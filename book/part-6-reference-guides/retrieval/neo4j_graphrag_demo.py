#!/usr/bin/env python3
"""Small Python + Neo4j GraphRAG demo for a Stripe vendor-risk question.

This demo keeps the "RAG" pieces intentionally small:

1. Build a graph index in Neo4j with vendors, teams, data types, compliance
   records, and source documents.
2. Retrieve a relevant evidence subgraph with Cypher.
3. Generate a grounded answer from only the retrieved graph facts.

It is designed for interview prep, so the graph schema and query are simple
enough to explain on a whiteboard.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
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


RISK_QUERY = """
MATCH (vendor:Vendor)-[:STORES]->(data_type:DataType)
MATCH (vendor)-[:OWNED_BY]->(owner:Team)
MATCH (vendor)-[:HAS_COMPLIANCE_RECORD]->(compliance:ComplianceRecord {
    kind: "DPA",
    year: $year
})
WHERE compliance.status <> "current"
  AND data_type.category IN $categories
OPTIONAL MATCH (vendor_doc:Document)-[:MENTIONS]->(vendor)
OPTIONAL MATCH (owner_doc:Document)-[:MENTIONS]->(owner)
OPTIONAL MATCH (data_doc:Document)-[:MENTIONS]->(data_type)
OPTIONAL MATCH (compliance_doc:Document)-[:MENTIONS]->(compliance)
RETURN vendor.name AS vendor,
       owner.name AS owner,
       compliance.status AS dpa_status,
       compliance.year AS dpa_year,
       collect(DISTINCT data_type.name) AS data_types,
       collect(DISTINCT vendor_doc.title) AS vendor_docs,
       collect(DISTINCT owner_doc.title) AS owner_docs,
       collect(DISTINCT data_doc.title) AS data_docs,
       collect(DISTINCT compliance_doc.title) AS compliance_docs
ORDER BY vendor
"""


@dataclass
class DemoConfig:
    uri: str
    username: str
    password: str
    database: str


def get_config() -> DemoConfig:
    return DemoConfig(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        username=os.getenv("NEO4J_USERNAME", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password"),
        database=os.getenv("NEO4J_DATABASE", "neo4j"),
    )


class Neo4jGraphRAGDemo:
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

    def retrieve_vendor_dpa_risk(
        self,
        year: int = 2025,
        categories: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        categories = categories or ["billing", "payment"]
        with self._driver.session(database=self._database) as session:
            result = session.run(RISK_QUERY, year=year, categories=categories)
            return [record.data() for record in result]


def unique_nonempty(items: list[str]) -> list[str]:
    seen = set()
    output: list[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output


def render_answer(question: str, rows: list[dict[str, Any]]) -> str:
    if not rows:
        return (
            f"Question: {question}\n\n"
            "Answer: No vendors matched the requested risk pattern."
        )

    lines = [f"Question: {question}", "", "Answer:"]
    for row in rows:
        data_types = ", ".join(unique_nonempty(row["data_types"]))
        lines.append(
            f"- {row['owner']} is responsible for {row['vendor']}. "
            f"{row['vendor']} stores {data_types} and its {row['dpa_year']} "
            f"DPA status is {row['dpa_status']}."
        )

    lines.extend(["", "Evidence Paths:"])
    for row in rows:
        data_types = ", ".join(unique_nonempty(row["data_types"]))
        lines.append(
            f"- ({row['vendor']})-[:OWNED_BY]->({row['owner']}) "
            f"[source: {', '.join(unique_nonempty(row['owner_docs']))}]"
        )
        lines.append(
            f"- ({row['vendor']})-[:STORES]->({data_types}) "
            f"[source: {', '.join(unique_nonempty(row['data_docs']))}]"
        )
        lines.append(
            f"- ({row['vendor']})-[:HAS_COMPLIANCE_RECORD]->"
            f"(DPA {row['dpa_year']} = {row['dpa_status']}) "
            f"[source: {', '.join(unique_nonempty(row['compliance_docs']))}]"
        )
        vendor_docs = unique_nonempty(row["vendor_docs"])
        if vendor_docs:
            lines.append(
                f"- ({row['vendor']}) is cataloged in "
                f"{', '.join(vendor_docs)}."
            )

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Small GraphRAG demo using Python and Neo4j."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("seed", help="Create constraints and seed demo data.")

    ask_parser = subparsers.add_parser(
        "ask",
        help="Run the vendor-risk GraphRAG query and print a grounded answer.",
    )
    ask_parser.add_argument(
        "question",
        nargs="?",
        default=DEFAULT_QUESTION,
        help="Question to answer. The demo routes this to the vendor-risk query.",
    )
    ask_parser.add_argument(
        "--year",
        type=int,
        default=2025,
        help="Compliance year to inspect.",
    )
    ask_parser.add_argument(
        "--categories",
        nargs="+",
        default=["billing", "payment"],
        help="Data categories treated as sensitive for this query.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    demo = Neo4jGraphRAGDemo(get_config())

    try:
        demo.verify_connectivity()
        if args.command == "seed":
            demo.seed()
            print("Seeded Neo4j with the Stripe GraphRAG demo data.")
            return 0

        rows = demo.retrieve_vendor_dpa_risk(
            year=args.year,
            categories=args.categories,
        )
        print(render_answer(args.question, rows))
        return 0
    except Exception as exc:  # pragma: no cover - runtime environment issues
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        demo.close()


if __name__ == "__main__":
    raise SystemExit(main())
