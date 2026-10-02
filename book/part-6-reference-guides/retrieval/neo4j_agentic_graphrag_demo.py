#!/usr/bin/env python3
"""Agentic GraphRAG demo using Python and Neo4j.

This version is intentionally more "agentic" than a single Cypher query:

1. It plans from the user question.
2. It selects graph tools dynamically.
3. It gathers evidence step by step for each candidate vendor.
4. It stops when it has enough support to answer.

The planning layer is rule-based so the demo runs locally without an API key,
but the control flow mirrors the tool-using agent pattern used in production.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Any

try:
    from neo4j import GraphDatabase
except ImportError as exc:  # pragma: no cover - import error path
    raise SystemExit(
        "Missing dependency: install the Neo4j driver with `pip install neo4j`."
    ) from exc


DEFAULT_QUESTION = (
    "Which owner is responsible for vendors storing customer billing data "
    "without a current DPA?"
)


SEED_VENDORS = [
    {
        "name": "Stripe",
        "vendor_doc": "Vendor Inventory 2025",
        "owner": {
            "name": "Finance Engineering",
            "doc": "Engineering Ownership Map",
        },
        "data_types": [
            {
                "name": "Billing Email",
                "category": "billing",
                "doc": "Data Inventory 2025",
            },
            {
                "name": "Payment Metadata",
                "category": "payment",
                "doc": "Data Inventory 2025",
            },
        ],
        "compliance": {
            "kind": "DPA",
            "year": 2025,
            "status": "missing",
            "doc": "Legal Tracker 2025",
        },
    },
    {
        "name": "Twilio",
        "vendor_doc": "Vendor Inventory 2025",
        "owner": {
            "name": "Growth Platform",
            "doc": "Engineering Ownership Map",
        },
        "data_types": [
            {
                "name": "Phone Number",
                "category": "contact",
                "doc": "Data Inventory 2025",
            }
        ],
        "compliance": {
            "kind": "DPA",
            "year": 2025,
            "status": "current",
            "doc": "Legal Tracker 2025",
        },
    },
    {
        "name": "Zendesk",
        "vendor_doc": "Vendor Inventory 2025",
        "owner": {
            "name": "Support Systems",
            "doc": "Engineering Ownership Map",
        },
        "data_types": [
            {
                "name": "Support Ticket Content",
                "category": "support",
                "doc": "Data Inventory 2025",
            },
            {
                "name": "Customer Email",
                "category": "contact",
                "doc": "Data Inventory 2025",
            },
        ],
        "compliance": {
            "kind": "DPA",
            "year": 2025,
            "status": "current",
            "doc": "Legal Tracker 2025",
        },
    },
]


CONSTRAINTS = [
    "CREATE CONSTRAINT vendor_name IF NOT EXISTS FOR (v:Vendor) REQUIRE v.name IS UNIQUE",
    "CREATE CONSTRAINT team_name IF NOT EXISTS FOR (t:Team) REQUIRE t.name IS UNIQUE",
    "CREATE CONSTRAINT data_type_name IF NOT EXISTS FOR (d:DataType) REQUIRE d.name IS UNIQUE",
    "CREATE CONSTRAINT document_title IF NOT EXISTS FOR (d:Document) REQUIRE d.title IS UNIQUE",
    (
        "CREATE CONSTRAINT compliance_id IF NOT EXISTS "
        "FOR (c:ComplianceRecord) REQUIRE c.id IS UNIQUE"
    ),
]


SEED_QUERY = """
MERGE (vendor:Vendor {name: $vendor_name})

MERGE (vendor_doc:Document {title: $vendor_doc})
MERGE (vendor_doc)-[:MENTIONS]->(vendor)

MERGE (owner:Team {name: $owner_name})
MERGE (owner_doc:Document {title: $owner_doc})
MERGE (vendor)-[:OWNED_BY]->(owner)
MERGE (owner_doc)-[:MENTIONS]->(owner)

WITH vendor
UNWIND $data_types AS item
MERGE (data_type:DataType {name: item.name})
SET data_type.category = item.category
MERGE (data_doc:Document {title: item.doc})
MERGE (vendor)-[:STORES]->(data_type)
MERGE (data_doc)-[:MENTIONS]->(data_type)

WITH vendor
MERGE (compliance:ComplianceRecord {id: $compliance_id})
SET compliance.kind = $compliance_kind,
    compliance.year = $compliance_year,
    compliance.status = $compliance_status
MERGE (compliance_doc:Document {title: $compliance_doc})
MERGE (vendor)-[:HAS_COMPLIANCE_RECORD]->(compliance)
MERGE (compliance_doc)-[:MENTIONS]->(compliance)
"""


CANDIDATE_VENDOR_QUERY = """
MATCH (vendor:Vendor)-[:HAS_COMPLIANCE_RECORD]->(compliance:ComplianceRecord {
    kind: "DPA",
    year: $year
})
MATCH (vendor)-[:STORES]->(data_type:DataType)
WHERE compliance.status <> "current"
  AND data_type.category IN $categories
RETURN DISTINCT vendor.name AS vendor
ORDER BY vendor
"""


OWNER_QUERY = """
MATCH (vendor:Vendor {name: $vendor})-[:OWNED_BY]->(owner:Team)
OPTIONAL MATCH (owner_doc:Document)-[:MENTIONS]->(owner)
RETURN owner.name AS owner,
       collect(DISTINCT owner_doc.title) AS docs
"""


DATA_QUERY = """
MATCH (vendor:Vendor {name: $vendor})-[:STORES]->(data_type:DataType)
WHERE data_type.category IN $categories
OPTIONAL MATCH (data_doc:Document)-[:MENTIONS]->(data_type)
RETURN collect(DISTINCT data_type.name) AS data_types,
       collect(DISTINCT data_doc.title) AS docs
"""


COMPLIANCE_QUERY = """
MATCH (vendor:Vendor {name: $vendor})-[:HAS_COMPLIANCE_RECORD]->(
    compliance:ComplianceRecord {
        kind: "DPA",
        year: $year
    }
)
OPTIONAL MATCH (compliance_doc:Document)-[:MENTIONS]->(compliance)
RETURN compliance.status AS status,
       compliance.year AS year,
       collect(DISTINCT compliance_doc.title) AS docs
"""


VENDOR_DOC_QUERY = """
MATCH (vendor_doc:Document)-[:MENTIONS]->(vendor:Vendor {name: $vendor})
RETURN collect(DISTINCT vendor_doc.title) AS docs
"""


NEIGHBOR_QUERY = """
MATCH (vendor:Vendor {name: $vendor})-[rel]-(neighbor)
RETURN type(rel) AS relation,
       labels(neighbor) AS neighbor_labels,
       properties(neighbor) AS neighbor_properties
ORDER BY relation
"""


@dataclass
class DemoConfig:
    uri: str
    username: str
    password: str
    database: str


@dataclass
class RetrievalPlan:
    question: str
    year: int
    categories: list[str]
    subgoals: list[str]


@dataclass
class AgentStep:
    thought: str
    action: str
    action_input: dict[str, Any]
    observation: str


@dataclass
class VendorEvidence:
    vendor: str
    owner: str | None = None
    data_types: list[str] = field(default_factory=list)
    dpa_status: str | None = None
    dpa_year: int | None = None
    vendor_docs: list[str] = field(default_factory=list)
    owner_docs: list[str] = field(default_factory=list)
    data_docs: list[str] = field(default_factory=list)
    compliance_docs: list[str] = field(default_factory=list)
    neighbor_snapshot: list[str] = field(default_factory=list)

    def is_complete(self) -> bool:
        return bool(self.owner and self.data_types and self.dpa_status)

    def matches_risk(self) -> bool:
        return self.is_complete() and self.dpa_status != "current"


@dataclass
class AgentResult:
    plan: RetrievalPlan
    evidence: list[VendorEvidence]
    trace: list[AgentStep]
    answer: str


def get_config() -> DemoConfig:
    return DemoConfig(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        username=os.getenv("NEO4J_USERNAME", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password"),
        database=os.getenv("NEO4J_DATABASE", "neo4j"),
    )


def unique_nonempty(items: list[str]) -> list[str]:
    seen = set()
    output: list[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output


class RuleBasedPlanner:
    CATEGORY_HINTS = {
        "billing": ["billing", "invoice", "subscription"],
        "payment": ["payment", "card", "checkout", "transaction"],
        "contact": ["contact", "email", "phone"],
        "support": ["support", "ticket"],
    }

    def build_plan(self, question: str) -> RetrievalPlan:
        question_lower = question.lower()
        year = self._extract_year(question_lower)
        categories = self._extract_categories(question_lower)
        subgoals = self._build_subgoals(question_lower)
        return RetrievalPlan(
            question=question,
            year=year,
            categories=categories,
            subgoals=subgoals,
        )

    def _extract_year(self, question: str) -> int:
        match = re.search(r"\b(20\d{2})\b", question)
        if match:
            return int(match.group(1))
        return 2025

    def _extract_categories(self, question: str) -> list[str]:
        categories: list[str] = []
        for category, keywords in self.CATEGORY_HINTS.items():
            if any(keyword in question for keyword in keywords):
                categories.append(category)

        if not categories:
            categories = ["billing", "payment"]

        return unique_nonempty(categories)

    def _build_subgoals(self, question: str) -> list[str]:
        wants_owner = "owner" in question or "responsible" in question
        wants_data = any(
            token in question
            for token in ["data", "billing", "payment", "email", "phone", "stores"]
        )
        wants_compliance = any(
            token in question
            for token in ["dpa", "compliance", "agreement", "current"]
        )

        subgoals: list[str] = []
        if wants_owner:
            subgoals.append("owner")
        if wants_data:
            subgoals.append("data")
        if wants_compliance:
            subgoals.append("compliance")

        for fallback_goal in ["owner", "data", "compliance"]:
            if fallback_goal not in subgoals:
                subgoals.append(fallback_goal)

        subgoals.append("documents")
        return subgoals


class GraphTools:
    def __init__(self, config: DemoConfig) -> None:
        self._database = config.database
        self._driver = GraphDatabase.driver(
            config.uri,
            auth=(config.username, config.password),
        )

    def close(self) -> None:
        self._driver.close()

    def verify_connectivity(self) -> None:
        self._driver.verify_connectivity()

    def seed(self) -> None:
        with self._driver.session(database=self._database) as session:
            for constraint in CONSTRAINTS:
                session.run(constraint).consume()

            for vendor in SEED_VENDORS:
                compliance = vendor["compliance"]
                session.run(
                    SEED_QUERY,
                    vendor_name=vendor["name"],
                    vendor_doc=vendor["vendor_doc"],
                    owner_name=vendor["owner"]["name"],
                    owner_doc=vendor["owner"]["doc"],
                    data_types=vendor["data_types"],
                    compliance_id=(
                        f"{vendor['name']}:{compliance['kind']}:{compliance['year']}"
                    ),
                    compliance_kind=compliance["kind"],
                    compliance_year=compliance["year"],
                    compliance_status=compliance["status"],
                    compliance_doc=compliance["doc"],
                ).consume()

    def find_candidate_vendors(
        self,
        year: int,
        categories: list[str],
    ) -> list[str]:
        with self._driver.session(database=self._database) as session:
            result = session.run(
                CANDIDATE_VENDOR_QUERY,
                year=year,
                categories=categories,
            )
            return [record["vendor"] for record in result]

    def get_vendor_owner(self, vendor: str) -> dict[str, Any]:
        with self._driver.session(database=self._database) as session:
            record = session.run(OWNER_QUERY, vendor=vendor).single()
            if not record:
                return {"owner": None, "docs": []}
            return {
                "owner": record["owner"],
                "docs": unique_nonempty(record["docs"]),
            }

    def get_vendor_data_types(
        self,
        vendor: str,
        categories: list[str],
    ) -> dict[str, Any]:
        with self._driver.session(database=self._database) as session:
            record = session.run(
                DATA_QUERY,
                vendor=vendor,
                categories=categories,
            ).single()
            if not record:
                return {"data_types": [], "docs": []}
            return {
                "data_types": unique_nonempty(record["data_types"]),
                "docs": unique_nonempty(record["docs"]),
            }

    def get_vendor_compliance(self, vendor: str, year: int) -> dict[str, Any]:
        with self._driver.session(database=self._database) as session:
            record = session.run(
                COMPLIANCE_QUERY,
                vendor=vendor,
                year=year,
            ).single()
            if not record:
                return {"status": None, "year": year, "docs": []}
            return {
                "status": record["status"],
                "year": record["year"],
                "docs": unique_nonempty(record["docs"]),
            }

    def get_vendor_documents(self, vendor: str) -> list[str]:
        with self._driver.session(database=self._database) as session:
            record = session.run(VENDOR_DOC_QUERY, vendor=vendor).single()
            if not record:
                return []
            return unique_nonempty(record["docs"])

    def expand_vendor_neighbors(self, vendor: str) -> list[str]:
        with self._driver.session(database=self._database) as session:
            result = session.run(NEIGHBOR_QUERY, vendor=vendor)
            snapshot: list[str] = []
            for record in result:
                labels = "/".join(record["neighbor_labels"])
                properties = record["neighbor_properties"]
                descriptor = properties.get("name") or properties.get("id") or str(
                    properties
                )
                snapshot.append(f"{record['relation']} -> {labels}:{descriptor}")
            return snapshot


class AgenticGraphRAG:
    def __init__(self, tools: GraphTools, planner: RuleBasedPlanner | None = None):
        self._tools = tools
        self._planner = planner or RuleBasedPlanner()

    def run(self, question: str) -> AgentResult:
        trace: list[AgentStep] = []
        plan = self._planner.build_plan(question)
        trace.append(
            AgentStep(
                thought="Break the question into retrieval constraints and subgoals.",
                action="plan",
                action_input={"question": question},
                observation=(
                    f"year={plan.year}, categories={plan.categories}, "
                    f"subgoals={plan.subgoals}"
                ),
            )
        )

        candidate_vendors = self._call_tool(
            trace=trace,
            thought=(
                "Start broad: find vendors that already match the risky "
                "billing/payment plus DPA pattern."
            ),
            action="find_candidate_vendors",
            year=plan.year,
            categories=plan.categories,
        )

        evidence: list[VendorEvidence] = []
        for vendor in candidate_vendors:
            case = VendorEvidence(vendor=vendor)
            trace.append(
                AgentStep(
                    thought=(
                        f"Investigate {vendor} step by step and stop when the "
                        "answer is fully supported."
                    ),
                    action="select_vendor",
                    action_input={"vendor": vendor},
                    observation="Vendor added to the active investigation queue.",
                )
            )

            for subgoal in plan.subgoals:
                if subgoal == "owner" and case.owner is None:
                    owner_result = self._call_tool(
                        trace=trace,
                        thought=f"I need the accountable team for {vendor}.",
                        action="get_vendor_owner",
                        vendor=vendor,
                    )
                    case.owner = owner_result["owner"]
                    case.owner_docs = owner_result["docs"]
                    continue

                if subgoal == "data" and not case.data_types:
                    data_result = self._call_tool(
                        trace=trace,
                        thought=(
                            f"I need to confirm what sensitive data {vendor} stores."
                        ),
                        action="get_vendor_data_types",
                        vendor=vendor,
                        categories=plan.categories,
                    )
                    case.data_types = data_result["data_types"]
                    case.data_docs = data_result["docs"]
                    continue

                if subgoal == "compliance" and case.dpa_status is None:
                    compliance_result = self._call_tool(
                        trace=trace,
                        thought=f"I need the DPA status for {vendor}.",
                        action="get_vendor_compliance",
                        vendor=vendor,
                        year=plan.year,
                    )
                    case.dpa_status = compliance_result["status"]
                    case.dpa_year = compliance_result["year"]
                    case.compliance_docs = compliance_result["docs"]
                    continue

                if subgoal == "documents" and not case.vendor_docs:
                    case.vendor_docs = self._call_tool(
                        trace=trace,
                        thought=(
                            f"I already have the graph facts for {vendor}; now gather "
                            "the source document that catalogs the vendor."
                        ),
                        action="get_vendor_documents",
                        vendor=vendor,
                    )

            if case.is_complete():
                case.neighbor_snapshot = self._call_tool(
                    trace=trace,
                    thought=(
                        f"I have enough to answer about {vendor}; capture a quick "
                        "neighbor snapshot for explainability."
                    ),
                    action="expand_vendor_neighbors",
                    vendor=vendor,
                )
                evidence.append(case)
            else:
                trace.append(
                    AgentStep(
                        thought=(
                            f"The evidence for {vendor} is incomplete, so I should "
                            "not include it in the final answer."
                        ),
                        action="skip_incomplete_vendor",
                        action_input={"vendor": vendor},
                        observation="Vendor omitted due to missing required support.",
                    )
                )

        answer = self._render_answer(plan, evidence, trace)
        return AgentResult(plan=plan, evidence=evidence, trace=trace, answer=answer)

    def _call_tool(
        self,
        trace: list[AgentStep],
        thought: str,
        action: str,
        **action_input: Any,
    ) -> Any:
        tool = getattr(self._tools, action)
        output = tool(**action_input)
        trace.append(
            AgentStep(
                thought=thought,
                action=action,
                action_input=action_input,
                observation=self._summarize_output(output),
            )
        )
        return output

    def _summarize_output(self, output: Any) -> str:
        if isinstance(output, list):
            if not output:
                return "No results."
            return f"Returned {len(output)} item(s): {output}"
        if isinstance(output, dict):
            return str(output)
        return str(output)

    def _render_answer(
        self,
        plan: RetrievalPlan,
        evidence: list[VendorEvidence],
        trace: list[AgentStep],
    ) -> str:
        lines = [f"Question: {plan.question}", ""]
        lines.append("Plan:")
        lines.append(f"- Year: {plan.year}")
        lines.append(f"- Categories: {', '.join(plan.categories)}")
        lines.append(f"- Subgoals: {', '.join(plan.subgoals)}")
        lines.append("")
        lines.append("Answer:")

        matched = [item for item in evidence if item.matches_risk()]
        if not matched:
            lines.append("- No vendors matched the requested risk pattern.")
        else:
            for item in matched:
                data_types = ", ".join(item.data_types)
                lines.append(
                    f"- {item.owner} is responsible for {item.vendor}. "
                    f"{item.vendor} stores {data_types} and its "
                    f"{item.dpa_year} DPA status is {item.dpa_status}."
                )

        lines.append("")
        lines.append("Evidence Paths:")
        if not matched:
            lines.append("- The agent did not gather enough evidence for a risk match.")
        else:
            for item in matched:
                lines.append(
                    f"- ({item.vendor})-[:OWNED_BY]->({item.owner}) "
                    f"[source: {', '.join(item.owner_docs)}]"
                )
                lines.append(
                    f"- ({item.vendor})-[:STORES]->({', '.join(item.data_types)}) "
                    f"[source: {', '.join(item.data_docs)}]"
                )
                lines.append(
                    f"- ({item.vendor})-[:HAS_COMPLIANCE_RECORD]->"
                    f"(DPA {item.dpa_year} = {item.dpa_status}) "
                    f"[source: {', '.join(item.compliance_docs)}]"
                )
                if item.vendor_docs:
                    lines.append(
                        f"- ({item.vendor}) is cataloged in "
                        f"{', '.join(item.vendor_docs)}."
                    )
                if item.neighbor_snapshot:
                    lines.append(
                        f"- Neighbor snapshot for {item.vendor}: "
                        f"{'; '.join(item.neighbor_snapshot)}"
                    )

        lines.append("")
        lines.append("Agent Trace:")
        for index, step in enumerate(trace, start=1):
            lines.append(f"{index}. Thought: {step.thought}")
            lines.append(
                f"   Action: {step.action}({step.action_input})"
            )
            lines.append(f"   Observation: {step.observation}")

        return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Agentic GraphRAG demo using Python and Neo4j."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("seed", help="Create constraints and seed demo data.")

    ask_parser = subparsers.add_parser(
        "ask",
        help="Run the agentic GraphRAG demo and print the answer plus trace.",
    )
    ask_parser.add_argument(
        "question",
        nargs="?",
        default=DEFAULT_QUESTION,
        help="Question to answer.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tools = GraphTools(get_config())

    try:
        tools.verify_connectivity()
        if args.command == "seed":
            tools.seed()
            print("Seeded Neo4j with the agentic GraphRAG demo data.")
            return 0

        agent = AgenticGraphRAG(tools)
        result = agent.run(args.question)
        print(result.answer)
        return 0
    except Exception as exc:  # pragma: no cover - runtime environment issues
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        tools.close()


if __name__ == "__main__":
    raise SystemExit(main())
