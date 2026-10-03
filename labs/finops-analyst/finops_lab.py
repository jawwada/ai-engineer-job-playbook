#!/usr/bin/env python3
"""
finops_lab.py -- a hands-on FinOps analyst lab (Python 3.10+, standard library only)

The lab generates 18 months (April 2025 to September 2026) of synthetic,
FOCUS-like daily cost data for a fictional business unit that runs on AWS,
Microsoft Azure and Google Cloud, and then runs the analyses a multi-cloud
FinOps analyst is hired to do:

  generate     write the data set: cost rows, business drivers, budget, tag
               standard, account map, planned-change calendar, commitment
               inventory, initiative register and the ground truth for the
               injected events and the true savings
  forecast     12-month forecast: a seasonal-naive weekday profile with a
               robust level and a damped trend per series (storage on a
               constant-month basis), driver adjustments (migration, Savings
               Plan pool, renewal, known one-time items, probability-weighted
               savings) and a rolling-origin backtest with MAPE and WAPE
  variance     budget vs forecast vs actual for one month, with a
               volume / mix / rate / one-time bridge
  anomalies    robust z-score detection (median and MAD of same-weekday
               baselines, percentage and dollar thresholds), triage rules,
               unit-cost detection, and precision/recall against the
               injected ground truth
  allocation   tag compliance, unallocated cost and a shared-cost split
  commitments  coverage, utilization, waste, effective savings rate (three
               definitions) and a sizing recommendation with break-even
  savings      projected vs realized savings for implemented initiatives,
               scored against the true savings, plus the probability-weighted
               pipeline
  summary      a one-page Markdown executive summary

Every number is deterministic for a given --seed. All names and events are
fictional. Unit prices are illustrative, except the NAT gateway and public IPv4
prices, which match AWS's published us-east-1 prices in October 2026.

Example:
  python3 finops_lab.py generate --out data
  python3 finops_lab.py summary --data data --month 2026-09
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import signal
import statistics
import sys
from collections import defaultdict
from datetime import date, timedelta

# ===========================================================================
# 0. Small utilities
# ===========================================================================

DAYS_PER_MONTH = 30.4375


def d2s(d: date) -> str:
    return d.isoformat()


def s2d(s: str) -> date:
    return date.fromisoformat(s[:10])


def daterange(a: date, b: date):
    """Yield every date from a to b inclusive."""
    for i in range((b - a).days + 1):
        yield a + timedelta(days=i)


def ym(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def ym_parse(s: str) -> tuple[int, int]:
    y, m = s.split("-")
    return int(y), int(m)


def add_months(y: int, m: int, k: int) -> tuple[int, int]:
    idx = y * 12 + (m - 1) + k
    return idx // 12, idx % 12 + 1


def month_end(y: int, m: int) -> date:
    ny, nm = add_months(y, m, 1)
    return date(ny, nm, 1) - timedelta(days=1)


def days_in_month(y: int, m: int) -> int:
    return month_end(y, m).day


def month_bounds(month: str) -> tuple[date, date]:
    y, m = ym_parse(month)
    return date(y, m, 1), month_end(y, m)


def month_list(a: str, b: str) -> list[str]:
    """Inclusive list of YYYY-MM strings from a to b."""
    y, m = ym_parse(a)
    out = []
    while f"{y:04d}-{m:02d}" <= b:
        out.append(f"{y:04d}-{m:02d}")
        y, m = add_months(y, m, 1)
    return out


def median(xs) -> float:
    xs = list(xs)
    return statistics.median(xs) if xs else 0.0


def percentile(xs, p: float) -> float:
    """Linear-interpolated percentile, p in [0, 100]."""
    s = sorted(xs)
    if not s:
        return 0.0
    k = (len(s) - 1) * p / 100.0
    f = math.floor(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


def money(x: float, decimals: int = 0) -> str:
    sign = "-" if x < 0 else ""
    return f"{sign}${abs(x):,.{decimals}f}"


def smoney(x: float) -> str:
    """Signed money: +$1,234 or -$1,234."""
    return ("+" if x >= 0 else "-") + f"${abs(x):,.0f}"


def kmoney(x: float) -> str:
    """Compact money for summaries: $1.23M or $456k."""
    sign = "-" if x <= -0.5 else ""
    a = abs(x)
    if a >= 1e6:
        return f"{sign}${a / 1e6:.2f}M"
    if a >= 1e3:
        return f"{sign}${a / 1e3:.0f}k"
    return f"{sign}${a:.0f}"


def skmoney(x: float) -> str:
    """Signed compact money: +$125k."""
    return ("+" if x >= 0 else "-") + kmoney(abs(x))


def dtxt(d) -> str:
    """Prose date: 31 August 2026."""
    d = s2d(d) if isinstance(d, str) else d
    return f"{d.day} {d.strftime('%B %Y')}"


def pct(x: float, decimals: int = 1) -> str:
    return f"{x * 100:.{decimals}f}%"


def spct(x: float, decimals: int = 1) -> str:
    return ("+" if x >= 0 else "") + f"{x * 100:.{decimals}f}%"


def print_table(headers, rows, align=None, title=None):
    """Print a plain-text table. align is a string of 'l'/'r' per column."""
    cols = len(headers)
    align = align or ("l" + "r" * (cols - 1))
    srows = [[str(c) for c in r] for r in rows]
    widths = [len(h) for h in headers]
    for r in srows:
        for i, c in enumerate(r):
            widths[i] = max(widths[i], len(c))

    def fmt(r):
        return "  ".join(c.ljust(widths[i]) if align[i] == "l" else c.rjust(widths[i])
                         for i, c in enumerate(r)).rstrip()

    if title:
        print(title)
    print(fmt(headers))
    print("  ".join("-" * w for w in widths))
    for r in srows:
        print(fmt(r))
    print()


def md_table(headers, rows, align=None) -> str:
    """Return a Markdown table."""
    align = align or ("l" + "r" * (len(headers) - 1))
    sep = ["---" if a == "l" else "---:" for a in align]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(sep) + " |"]
    for r in rows:
        lines.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(lines)


def section(title: str):
    print("=" * len(title))
    print(title)
    print("=" * len(title))
    print()


# ===========================================================================
# 1. The synthetic world (every name, price and event is fictional)
# ===========================================================================

START = date(2025, 4, 1)
END = date(2026, 9, 30)           # last day of data; "today" is early October 2026

PROVIDERS = {
    "AWS": {"billing_account_id": "111100000000", "billing_account_name": "aws-payer-org",
            "subaccount_type": "AWS Account", "region": "us-east-1", "negotiated": 0.06},
    "Microsoft": {"billing_account_id": "mca-7700-1180", "billing_account_name": "mca-business-unit",
                  "subaccount_type": "Subscription", "region": "eastus", "negotiated": 0.0},
    "Google Cloud": {"billing_account_id": "01A2B3-C4D5E6-F7A8B9", "billing_account_name": "gcp-business-unit",
                     "subaccount_type": "Project", "region": "us-central1", "negotiated": 0.04},
}
PROVIDER_ORDER = ["AWS", "Microsoft", "Google Cloud"]

# Typical delay (days) before a day's cost is visible in the provider's data.
LATENCY_DAYS = {"AWS": 1, "Microsoft": 2, "Google Cloud": 1}

# Sub-accounts: AWS accounts, Azure subscriptions, Google Cloud projects.
SUBACCOUNTS = {
    "aws-management": ("AWS", "111100000001"),
    "aws-payments-prod": ("AWS", "111100000002"),
    "aws-payments-nonprod": ("AWS", "111100000003"),
    "aws-data-platform-prod": ("AWS", "111100000004"),
    "aws-shared-network": ("AWS", "111100000005"),
    "aws-ml-sandbox": ("AWS", "111100000006"),
    "az-crm-prod": ("Microsoft", "0b5c2f4e-0001-4c1a-9a51-000000000001"),
    "az-crm-dev": ("Microsoft", "0b5c2f4e-0002-4c1a-9a51-000000000002"),
    "az-security-shared": ("Microsoft", "0b5c2f4e-0003-4c1a-9a51-000000000003"),
    "az-ai-assistant-prod": ("Microsoft", "0b5c2f4e-0004-4c1a-9a51-000000000004"),
    "gcp-analytics-prod": ("Google Cloud", "gcp-analytics-prod"),
    "gcp-analytics-dev": ("Google Cloud", "gcp-analytics-dev"),
    "gcp-docai-prod": ("Google Cloud", "gcp-docai-prod"),
}

# The allocation hierarchy comes first: what each sub-account is for.
# kind: single = one application owns it; multi = several teams share it (tags decide);
# shared = a shared-cost pool (network, security, commitments and governance).
ACCOUNT_MAP = {
    "aws-management": dict(kind="shared", pool="commitments-and-governance", budget_line="shared-platform",
                           environment="shared", owner="team-platform"),
    "aws-payments-prod": dict(kind="single", application="payments-api", environment="prod",
                              cost_center="cc-1001", owner="team-payments", budget_line="payments-api"),
    "aws-payments-nonprod": dict(kind="single", application="payments-api", environment="dev",
                                 cost_center="cc-1001", owner="team-payments", budget_line="payments-api"),
    "aws-data-platform-prod": dict(kind="multi", environment="prod", owner="team-claims-data",
                                   budget_line="claims-analytics"),
    "aws-shared-network": dict(kind="shared", pool="network", budget_line="shared-platform",
                               environment="shared", owner="team-platform"),
    "aws-ml-sandbox": dict(kind="multi", environment="sandbox", owner="team-ml", budget_line="ml-research"),
    "az-crm-prod": dict(kind="single", application="customer-portal", environment="prod",
                        cost_center="cc-1003", owner="team-crm", budget_line="customer-portal"),
    "az-crm-dev": dict(kind="single", application="customer-portal", environment="dev",
                       cost_center="cc-1003", owner="team-crm", budget_line="customer-portal"),
    "az-security-shared": dict(kind="shared", pool="security", budget_line="shared-platform",
                               environment="shared", owner="team-security"),
    "az-ai-assistant-prod": dict(kind="single", application="ai-assistant", environment="prod",
                                 cost_center="cc-1005", owner="team-ai", budget_line="ai-assistant"),
    "gcp-analytics-prod": dict(kind="single", application="claims-analytics", environment="prod",
                               cost_center="cc-1002", owner="team-claims-data", budget_line="claims-analytics"),
    "gcp-analytics-dev": dict(kind="single", application="claims-analytics", environment="dev",
                              cost_center="cc-1002", owner="team-claims-data", budget_line="claims-analytics"),
    "gcp-docai-prod": dict(kind="single", application="doc-intelligence", environment="prod",
                           cost_center="cc-1006", owner="team-ai", budget_line="doc-intelligence"),
}

# The tagging standard. Lowercase keys and values, because Google Cloud labels
# accept only lowercase; one standard has to work on all three clouds.
TAG_STANDARD = {
    "required_keys": ["application", "environment", "cost-center", "owner"],
    "allowed_values": {
        "application": ["payments-api", "claims-analytics", "customer-portal", "ai-assistant",
                        "doc-intelligence", "ml-research", "shared-platform"],
        "environment": ["prod", "staging", "dev", "sandbox", "shared"],
        "cost-center": ["cc-1001", "cc-1002", "cc-1003", "cc-1004", "cc-1005", "cc-1006", "cc-1999"],
        "owner": ["team-payments", "team-claims-data", "team-crm", "team-ai", "team-ml",
                  "team-platform", "team-security"],
    },
    "case_rule": "keys and values are lowercase kebab-case",
    "sources_of_truth": {"cost-center": "finance chart of accounts", "owner": "team directory",
                         "application": "service catalog"},
    "key_aliases": {"Application": "application", "Environment": "environment", "costcenter": "cost-center",
                    "CostCenter": "cost-center", "Owner": "owner"},
    "value_aliases": {"payments": "payments-api"},
}

# Tag sets used by the series; several are deliberately non-compliant.
T_PAY_PROD = {"application": "payments-api", "environment": "prod", "cost-center": "cc-1001", "owner": "team-payments"}
T_PAY_NONPROD = {"application": "payments", "environment": "dev", "cost-center": "cc-1001", "owner": "team-payments"}
T_DP_PARTIAL = {"application": "claims-analytics", "environment": "prod", "cost-center": "cc-1002"}
T_DP_FULL = dict(T_DP_PARTIAL, owner="team-claims-data")
T_ML = {"application": "ml-research", "environment": "sandbox", "cost-center": "cc-1004", "owner": "team-ml"}
T_CRM_PROD_LEGACY = {"Application": "customer-portal", "Environment": "Prod", "cost-center": "CC-1003", "owner": "team-crm"}
T_CRM_PROD = {"application": "customer-portal", "environment": "prod", "cost-center": "cc-1003", "owner": "team-crm"}
T_CRM_DEV_PARTIAL = {"application": "customer-portal", "environment": "dev"}
T_CRM_DEV = dict(T_CRM_DEV_PARTIAL, **{"cost-center": "cc-1003", "owner": "team-crm"})
T_SEC = {"application": "shared-platform", "environment": "shared", "cost-center": "cc-1999", "owner": "team-security"}
T_AI = {"application": "ai-assistant", "environment": "prod", "cost-center": "cc-1005", "owner": "team-ai"}
T_GCP_PROD = {"application": "claims-analytics", "environment": "prod", "cost-center": "cc-1002", "owner": "team-claims-data"}
T_GCP_DEV = {"application": "claims-analytics", "environment": "dev", "costcenter": "cc-1002", "owner": "team-claims-data"}
T_DOCAI = {"application": "doc-intelligence", "environment": "prod", "cost-center": "cc-1006", "owner": "team-ai"}

# Weekday profiles (Monday..Sunday), normalized to a mean of 1 below.
DOW = {
    "flat": [1, 1, 1, 1, 1, 1, 1],
    "prod": [1.02, 1.03, 1.03, 1.02, 1.00, 0.86, 0.84],
    "prod_db": [1.01, 1.01, 1.01, 1.01, 1.00, 0.96, 0.95],
    "nonprod": [1.00, 1.00, 1.00, 1.00, 0.95, 0.40, 0.38],
    "batch": [1.12, 1.12, 1.12, 1.12, 1.10, 0.72, 0.70],
    "research": [1.15, 1.20, 1.20, 1.15, 1.05, 0.55, 0.50],
    "business": [1.06, 1.07, 1.07, 1.06, 1.00, 0.78, 0.76],
}
DOW_N = {k: [x / (sum(v) / 7) for x in v] for k, v in DOW.items()}

# Yearly seasonality by calendar month (payments peaks in November and December).
SEASON = {"none": {}, "retail": {11: 1.10, 12: 1.18, 1: 0.96}, "retail_db": {11: 1.05, 12: 1.08}}


def series_spec(**kw):
    """A series definition with defaults (one sub-account x service x meter)."""
    base = dict(season="none", noise=0.03, growth=0.0, dow="flat", storage=False, sp=False, ri=False,
                cud=False, start=None, tags=[(START, None)], desc="")
    base.update(kw)
    return base


# Each series is one (sub-account, service, meter) with a daily usage model.
# qty is the base daily quantity in April 2025 (for storage: GB stored).
SERIES = [
    # ---- AWS (negotiated private-pricing discount 6%) ----
    series_spec(id="aws-pay-ec2", sub="aws-payments-prod", service="Amazon EC2", cat="Compute", unit="Hours", price=0.20,
      qty=20000, growth=0.020, dow="prod", season="retail", noise=0.03, sp=True, tags=[(START, T_PAY_PROD)],
      desc="EC2 instance usage"),
    series_spec(id="aws-pay-rds", sub="aws-payments-prod", service="Amazon RDS", cat="Databases", unit="Hours", price=1.00,
      qty=2400, growth=0.015, dow="prod_db", season="retail_db", noise=0.02, tags=[(START, T_PAY_PROD)],
      desc="RDS instance usage"),
    series_spec(id="aws-pay-s3", sub="aws-payments-prod", service="Amazon S3", cat="Storage", unit="GB-Mo", price=0.023,
      qty=1_200_000, growth=0.025, noise=0.004, storage=True, tags=[(START, T_PAY_PROD)], desc="S3 storage"),
    series_spec(id="aws-pay-cw", sub="aws-payments-prod", service="Amazon CloudWatch", cat="Management and Governance",
      unit="GB", price=0.50, qty=1000, growth=0.020, dow="prod", season="retail", noise=0.04,
      tags=[(START, T_PAY_PROD)], desc="Log ingestion"),
    series_spec(id="aws-pay-dt", sub="aws-payments-prod", service="AWS Data Transfer", cat="Networking", unit="GB",
      price=0.09, qty=6000, growth=0.020, dow="prod", season="retail", noise=0.04, tags=[(START, T_PAY_PROD)],
      desc="Data transfer out to the internet"),
    series_spec(id="aws-nonprod-ec2", sub="aws-payments-nonprod", service="Amazon EC2", cat="Compute", unit="Hours",
      price=0.20, qty=15000, growth=0.010, dow="nonprod", noise=0.04, sp=True, tags=[(START, T_PAY_NONPROD)],
      desc="EC2 instance usage"),
    series_spec(id="aws-nonprod-rds", sub="aws-payments-nonprod", service="Amazon RDS", cat="Databases", unit="Hours",
      price=0.50, qty=600, growth=0.005, noise=0.02, tags=[(START, T_PAY_NONPROD)], desc="RDS instance usage"),
    series_spec(id="aws-dp-emr", sub="aws-data-platform-prod", service="Amazon EMR", cat="Analytics", unit="Hours",
      price=0.10, qty=8000, growth=0.003, dow="batch", noise=0.05,
      tags=[(START, None), (date(2026, 3, 15), T_DP_FULL)], desc="EMR service fee"),
    series_spec(id="aws-dp-ec2", sub="aws-data-platform-prod", service="Amazon EC2", cat="Compute", unit="Hours",
      price=0.20, qty=22000, growth=0.003, dow="batch", noise=0.05, sp=True,
      tags=[(START, T_DP_PARTIAL), (date(2026, 3, 15), T_DP_FULL)], desc="EC2 instances for EMR clusters"),
    series_spec(id="aws-dp-s3", sub="aws-data-platform-prod", service="Amazon S3", cat="Storage", unit="GB-Mo",
      price=0.023, qty=2_000_000, growth=0.010, noise=0.004, storage=True,
      tags=[(START, T_DP_PARTIAL), (date(2026, 3, 15), T_DP_FULL)], desc="S3 storage (claims data lake)"),
    series_spec(id="aws-net-natgb", sub="aws-shared-network", service="Amazon VPC", cat="Networking", unit="GB",
      price=0.045, qty=18000, growth=0.015, dow="prod", noise=0.04, desc="NAT Gateway data processed"),
    series_spec(id="aws-net-nathr", sub="aws-shared-network", service="Amazon VPC", cat="Networking", unit="Hours",
      price=0.045, qty=288, noise=0.0, desc="NAT Gateway hours"),
    series_spec(id="aws-net-ipv4", sub="aws-shared-network", service="Amazon VPC", cat="Networking", unit="Hours",
      price=0.005, qty=9600, growth=0.005, noise=0.0, desc="Public IPv4 address hours"),
    series_spec(id="aws-net-tgw", sub="aws-shared-network", service="AWS Transit Gateway", cat="Networking", unit="GB",
      price=0.02, qty=30000, growth=0.015, dow="prod", noise=0.04, desc="Transit Gateway data processed"),
    series_spec(id="aws-ml-ec2", sub="aws-ml-sandbox", service="Amazon EC2", cat="Compute", unit="Hours", price=4.00,
      qty=100, growth=0.030, dow="research", noise=0.10, sp=True,
      tags=[(START, None), (date(2026, 1, 15), T_ML)], desc="GPU instance usage"),
    series_spec(id="aws-ml-sm", sub="aws-ml-sandbox", service="Amazon SageMaker AI", cat="AI and Machine Learning",
      unit="Hours", price=1.25, qty=200, growth=0.030, dow="research", noise=0.08,
      tags=[(START, None), (date(2026, 1, 15), T_ML)], desc="Notebook and training instances"),
    series_spec(id="aws-ml-bedrock", sub="aws-ml-sandbox", service="Amazon Bedrock", cat="AI and Machine Learning",
      unit="1M Tokens", price=3.00, qty=100, dow="research", noise=0.10, start=date(2026, 8, 1),
      desc="Model inference (experiments)"),
    series_spec(id="aws-mgmt-config", sub="aws-management", service="AWS Config", cat="Management and Governance",
      unit="Items", price=0.003, qty=40000, growth=0.005, noise=0.03, desc="Configuration items recorded"),
    # ---- Microsoft Azure (no negotiated discount modeled) ----
    series_spec(id="az-crm-vm", sub="az-crm-prod", service="Virtual Machines", cat="Compute", unit="Hours", price=0.40,
      qty=6000, growth=0.005, dow="prod", noise=0.02, ri=True,
      tags=[(START, T_CRM_PROD_LEGACY), (date(2026, 6, 1), T_CRM_PROD)], desc="D-series VM compute"),
    series_spec(id="az-crm-vmlic", sub="az-crm-prod", service="Virtual Machines Licenses", cat="Compute", unit="Hours",
      price=0.09, qty=0, tags=[(START, T_CRM_PROD_LEGACY), (date(2026, 6, 1), T_CRM_PROD)],
      desc="Windows Server license"),
    series_spec(id="az-crm-sql", sub="az-crm-prod", service="Azure SQL Database", cat="Databases", unit="vCore Hours",
      price=0.50, qty=1200, growth=0.010, dow="prod_db", noise=0.02,
      tags=[(START, T_CRM_PROD_LEGACY), (date(2026, 6, 1), T_CRM_PROD)], desc="vCore usage"),
    series_spec(id="az-crm-sto", sub="az-crm-prod", service="Storage", cat="Storage", unit="GB-Mo", price=0.020,
      qty=450_000, growth=0.015, noise=0.004, storage=True, desc="Blob storage (storage accounts never tagged)"),
    series_spec(id="az-crm-la", sub="az-crm-prod", service="Log Analytics", cat="Management and Governance", unit="GB",
      price=2.30, qty=400, growth=0.010, dow="prod", noise=0.04,
      tags=[(START, T_CRM_PROD_LEGACY), (date(2026, 6, 1), T_CRM_PROD)], desc="Log data ingestion"),
    series_spec(id="az-crm-app", sub="az-crm-prod", service="Azure App Service", cat="Compute", unit="Hours", price=0.25,
      qty=2000, growth=0.005, dow="prod", noise=0.02,
      tags=[(START, T_CRM_PROD_LEGACY), (date(2026, 6, 1), T_CRM_PROD)], desc="App Service plan hours"),
    series_spec(id="az-dev-vm", sub="az-crm-dev", service="Virtual Machines", cat="Compute", unit="Hours", price=0.40,
      qty=2000, growth=0.005, dow="nonprod", noise=0.04,
      tags=[(START, T_CRM_DEV_PARTIAL), (date(2026, 5, 1), T_CRM_DEV)], desc="Dev/test VM compute"),
    series_spec(id="az-dev-sql", sub="az-crm-dev", service="Azure SQL Database", cat="Databases", unit="vCore Hours",
      price=0.50, qty=300, growth=0.005, noise=0.02,
      tags=[(START, T_CRM_DEV_PARTIAL), (date(2026, 5, 1), T_CRM_DEV)], desc="vCore usage"),
    series_spec(id="az-sec-def", sub="az-security-shared", service="Microsoft Defender for Cloud", cat="Security",
      unit="Hours", price=0.02, qty=35000, growth=0.010, noise=0.01, tags=[(START, T_SEC)],
      desc="Protected resource hours"),
    series_spec(id="az-sec-sent", sub="az-security-shared", service="Microsoft Sentinel", cat="Security", unit="GB",
      price=2.00, qty=450, growth=0.015, dow="prod", noise=0.04, tags=[(START, T_SEC)], desc="Analyzed log data"),
    series_spec(id="az-sec-kv", sub="az-security-shared", service="Key Vault", cat="Security", unit="10K Operations",
      price=0.03, qty=1333, growth=0.005, dow="prod", noise=0.03, tags=[(START, T_SEC)], desc="Key operations"),
    series_spec(id="az-ai-oai", sub="az-ai-assistant-prod", service="Azure OpenAI", cat="AI and Machine Learning",
      unit="1M Tokens", price=3.00, qty=0, tags=[(START, T_AI)], desc="Model inference tokens"),
    series_spec(id="az-ai-search", sub="az-ai-assistant-prod", service="Azure AI Search", cat="AI and Machine Learning",
      unit="Hours", price=1.00, qty=150, growth=0.020, noise=0.01, tags=[(START, T_AI)], desc="Search units"),
    series_spec(id="az-ai-app", sub="az-ai-assistant-prod", service="Azure App Service", cat="Compute", unit="Hours",
      price=0.25, qty=480, growth=0.030, dow="business", noise=0.03, tags=[(START, T_AI)],
      desc="App Service plan hours"),
    # ---- Google Cloud (negotiated discount 4%) ----
    series_spec(id="gcp-prod-bq", sub="gcp-analytics-prod", service="BigQuery", cat="Analytics", unit="TiB", price=6.25,
      qty=96, growth=0.010, dow="batch", noise=0.06, tags=[(START, T_GCP_PROD)], desc="Analysis (on-demand)"),
    series_spec(id="gcp-prod-gce", sub="gcp-analytics-prod", service="Compute Engine", cat="Compute", unit="Hours",
      price=0.20, qty=2500, growth=0.005, dow="prod", noise=0.02, cud=True, tags=[(START, T_GCP_PROD)],
      desc="N2 instance core and memory"),
    series_spec(id="gcp-prod-gcs", sub="gcp-analytics-prod", service="Cloud Storage", cat="Storage", unit="GB-Mo",
      price=0.020, qty=300_000, growth=0.010, noise=0.004, storage=True, desc="Standard storage (buckets unlabeled)"),
    series_spec(id="gcp-prod-dataproc", sub="gcp-analytics-prod", service="Dataproc", cat="Analytics", unit="vCPU Hours",
      price=0.06, qty=0, dow="batch", noise=0.05, start=date(2026, 7, 1), tags=[(START, T_GCP_PROD)],
      desc="Cluster vCPU hours"),
    series_spec(id="gcp-dev-bq", sub="gcp-analytics-dev", service="BigQuery", cat="Analytics", unit="TiB", price=6.25,
      qty=40, growth=0.010, dow="batch", noise=0.08, tags=[(START, T_GCP_DEV)], desc="Analysis (on-demand)"),
    series_spec(id="gcp-dev-gcs", sub="gcp-analytics-dev", service="Cloud Storage", cat="Storage", unit="GB-Mo",
      price=0.020, qty=91_000, growth=0.010, noise=0.004, storage=True, tags=[(START, T_GCP_DEV)],
      desc="Standard storage"),
    series_spec(id="gcp-docai-gem", sub="gcp-docai-prod", service="Gemini API", cat="AI and Machine Learning",
      unit="1M Tokens", price=1.25, qty=400, growth=0.040, dow="business", noise=0.04, tags=[(START, T_DOCAI)],
      desc="Model inference tokens"),
    series_spec(id="gcp-docai-run", sub="gcp-docai-prod", service="Cloud Run", cat="Compute", unit="vCPU Hours",
      price=0.0864, qty=1736, growth=0.030, dow="business", noise=0.04, tags=[(START, T_DOCAI)],
      desc="Container vCPU time"),
    series_spec(id="gcp-docai-log", sub="gcp-docai-prod", service="Cloud Logging", cat="Management and Governance",
      unit="GiB", price=0.50, qty=160, growth=0.030, dow="business", noise=0.04, tags=[(START, T_DOCAI)],
      desc="Log ingestion"),
]
SERIES_BY_ID = {s["id"]: s for s in SERIES}

# Business drivers (unit-economics denominators): application -> metric and model.
DRIVERS = {
    "payments-api": dict(metric="transactions", base=1_800_000, growth=0.020, dow="prod", season="retail", noise=0.02),
    "ai-assistant": dict(metric="conversations", base=20_000, growth=0.060, dow="business", season="none", noise=0.03),
    "customer-portal": dict(metric="sessions", base=250_000, growth=0.005, dow="prod", season="none", noise=0.02),
    "claims-analytics": dict(metric="claims_processed", base=40_000, growth=0.010, dow="business", season="none", noise=0.03),
    "doc-intelligence": dict(metric="documents", base=60_000, growth=0.040, dow="business", season="none", noise=0.03),
}

# The planned migration: AWS data platform to Google Cloud, with double-running.
MIGRATION = {
    "name": "Claims analytics platform: AWS (EMR, EC2, S3) to Google Cloud (BigQuery, Dataproc, Cloud Storage)",
    "source_sub": "aws-data-platform-prod",
    "source_compute_services": ["Amazon EMR", "Amazon EC2"],
    "source_storage_services": ["Amazon S3"],
    "target_sub": "gcp-analytics-prod",
    "target_increments_list_per_day": {"BigQuery": 2800.0, "Dataproc": 1100.0, "Cloud Storage": 600.0},
    "organic_growth": 0.01,
    "approved_on": "2026-02-20",
    "actual": {"ramp_start": "2026-07-01", "ramp_end": "2026-09-15",
               "decommission_compute": "2026-11-01", "decommission_storage": "2026-12-01"},
    "budget_plan": {"ramp_start": "2026-09-01", "ramp_end": "2026-11-15",
                    "decommission_compute": "2026-12-01", "decommission_storage": "2027-01-01"},
    "credits": {"2026-07": -12000.0, "2026-08": -12000.0, "2026-09": -12000.0},
}

# Commitment inventory. Discounts are illustrative.
COMMITMENTS = [
    {"id": "sp-0a1b2c3d4e5f", "provider": "AWS", "sub": "aws-management", "service": "AWS Savings Plans",
     "type": "Savings Plan", "category": "Spend", "name": "Compute Savings Plan, 3-year, no upfront",
     "start": "2024-02-01", "end": "2027-01-31", "hourly_commitment": 220.0, "discount": 0.30,
     "eligible": "Amazon EC2 in all accounts (shared across the organization)"},
    {"id": "ri-crm-vm-2024", "provider": "Microsoft", "sub": "az-crm-prod", "service": "Virtual Machines",
     "type": "Reservation", "category": "Usage", "name": "Reserved VM instances, 200 x D-series, 1-year, monthly payment",
     "start": "2024-09-01", "end": "2025-08-31", "hours_per_day": 4800.0, "discount": 0.40,
     "eligible": "Virtual Machines in az-crm-prod (single subscription scope)"},
    {"id": "ri-crm-vm-2025", "provider": "Microsoft", "sub": "az-crm-prod", "service": "Virtual Machines",
     "type": "Reservation", "category": "Usage", "name": "Reserved VM instances, 200 x D-series, 1-year, monthly payment",
     "start": "2025-09-01", "end": "2026-08-31", "hours_per_day": 4800.0, "discount": 0.40,
     "eligible": "Virtual Machines in az-crm-prod (single subscription scope)"},
    {"id": "cud-gce-analytics", "provider": "Google Cloud", "sub": "gcp-analytics-prod", "service": "Compute Engine",
     "type": "Committed Use Discount", "category": "Usage", "name": "Resource-based CUD, 3-year",
     "start": "2024-06-01", "end": "2027-05-31", "hours_per_day": 2000.0, "discount": 0.37,
     "eligible": "Compute Engine in gcp-analytics-prod"},
]
COMMIT_BY_ID = {c["id"]: c for c in COMMITMENTS}
SP = COMMIT_BY_ID["sp-0a1b2c3d4e5f"]
SP_SERIES = [s["id"] for s in SERIES if s["sp"]]
SP_KEYS = [(SERIES_BY_ID[i]["sub"], SERIES_BY_ID[i]["service"]) for i in SP_SERIES]

# Optimization initiatives already implemented (tracked for realized savings).
INITIATIVES = [
    {"id": "INIT-01", "name": "Rightsize payments RDS instances", "series": ["aws-pay-rds"], "start": "2026-03-01",
     "projected_monthly": 14000.0, "method": "unit", "driver": "payments-api", "owner": "team-payments",
     "type": "cost reduction"},
    {"id": "INIT-02", "name": "Schedule non-production compute (nights, weekends)",
     "series": ["aws-nonprod-ec2", "az-dev-vm"], "start": "2026-04-15", "projected_monthly": 40000.0,
     "method": "trend", "owner": "team-payments, team-crm", "type": "cost reduction"},
    {"id": "INIT-03", "name": "S3 Intelligent-Tiering for payments log and archive data", "series": ["aws-pay-s3"],
     "start": "2026-02-01", "projected_monthly": 8000.0, "method": "rate", "owner": "team-payments",
     "type": "cost reduction"},
    {"id": "INIT-04", "name": "Azure Hybrid Benefit for Windows Server on CRM VMs", "series": ["az-crm-vmlic"],
     "start": "2026-05-01", "projected_monthly": 11500.0, "method": "ratio", "ratio_of": "az-crm-vm",
     "owner": "team-crm", "type": "cost reduction"},
]

# Opportunities not yet implemented: they enter the forecast probability-weighted.
PIPELINE = [
    {"id": "OPP-01", "name": "Buy a new 1-year VM reservation (240 VMs) for az-crm-prod", "start": "2026-10-15",
     "monthly": 27000.0, "probability": 0.9, "owner": "team-crm + FinOps", "type": "rate", "registered_on": "2026-09-20"},
    {"id": "OPP-02", "name": "Restore non-production schedules (opt-outs since July)", "start": "2026-10-15",
     "monthly": 12000.0, "probability": 0.8, "owner": "team-payments", "type": "usage", "registered_on": "2026-09-20"},
    {"id": "OPP-03", "name": "Log Analytics retention and sampling for CRM", "start": "2026-11-01",
     "monthly": 6000.0, "probability": 0.7, "owner": "team-crm", "type": "usage", "registered_on": "2026-09-20"},
    {"id": "OPP-04", "name": "Move payments EC2 to Graviton instances", "start": "2026-12-01",
     "monthly": 9000.0, "probability": 0.5, "owner": "team-payments", "type": "usage", "registered_on": "2026-09-20"},
    {"id": "OPP-05", "name": "Release idle public IPv4 addresses and old snapshots", "start": "2026-10-15",
     "monthly": 1500.0, "probability": 0.9, "owner": "team-platform", "type": "usage", "registered_on": "2026-09-20"},
]

# The planned-change calendar the FinOps analyst keeps with Cloud Engineering.
CALENDAR = [
    {"id": "PC-01", "start": "2025-11-18", "end": "2025-11-20", "sub": "aws-payments-nonprod", "service": "Amazon EC2",
     "type": "planned-spike", "amount": 1600.0, "recurrence": "", "owner": "team-payments",
     "description": "Peak-season load test (expected about $1,600/day extra)", "added_on": "2025-11-03"},
    {"id": "PC-02", "start": "2026-07-01", "end": "2026-10-31", "sub": "gcp-analytics-prod", "service": "*",
     "type": "migration", "amount": 4300.0, "recurrence": "", "owner": "team-claims-data",
     "description": "Claims analytics migration: Google Cloud build-out and double-running", "added_on": "2026-02-20"},
    {"id": "PC-03", "start": "2026-09-15", "end": "2026-09-15", "sub": "aws-management", "service": "AWS Marketplace*",
     "type": "one-time", "amount": 48000.0, "recurrence": "annual", "owner": "team-security",
     "description": "Annual SIEM subscription renewal through AWS Marketplace", "added_on": "2026-09-10"},
    {"id": "PC-04", "start": "2026-11-01", "end": "", "sub": "aws-data-platform-prod", "service": "Amazon EMR;Amazon EC2",
     "type": "decommission", "amount": 0.0, "recurrence": "", "owner": "team-claims-data",
     "description": "Decommission EMR clusters after cut-over", "added_on": "2026-02-20"},
    {"id": "PC-05", "start": "2026-12-01", "end": "", "sub": "aws-data-platform-prod", "service": "Amazon S3",
     "type": "decommission", "amount": 0.0, "recurrence": "", "owner": "team-claims-data",
     "description": "Delete migrated S3 data after a 30-day validation window", "added_on": "2026-02-20"},
    {"id": "PC-06", "start": "2027-01-31", "end": "", "sub": "aws-management", "service": "AWS Savings Plans",
     "type": "commitment-expiry", "amount": 0.0, "recurrence": "", "owner": "FinOps",
     "description": "Compute Savings Plan sp-0a1b2c3d4e5f expires; renewal decision due", "added_on": "2024-02-01"},
]

# Injected events (ground truth). "target" says which control should catch it.
INJECTED = [
    {"id": "A1", "series": "aws-net-natgb", "start": "2026-02-10", "end": "2026-02-15", "add_list_per_day": 2385.0,
     "kind": "usage", "target": "detector", "title": "NAT gateway data-processing spike",
     "cause": "A new nightly sync to a partner endpoint went through the NAT gateway instead of a VPC endpoint"},
    {"id": "A3", "series": "gcp-dev-bq", "start": "2026-04-22", "end": "2026-04-22", "add_list_per_day": 4000.0,
     "kind": "usage", "target": "detector", "title": "Runaway BigQuery query in development",
     "cause": "An unfiltered join scanned about 640 TiB in one day"},
    {"id": "A4", "series": "aws-ml-ec2", "start": "2026-05-18", "end": "2026-05-29", "add_list_per_day": 3104.0,
     "kind": "usage", "target": "detector", "title": "Forgotten GPU cluster",
     "cause": "An 8-node GPU training cluster was left running after an experiment"},
    {"id": "A5", "series": "az-crm-la", "start": "2026-07-07", "end": "2026-07-11", "add_list_per_day": 1794.0,
     "kind": "usage", "target": "detector", "title": "Logging explosion",
     "cause": "A release shipped with debug-level logging enabled"},
    {"id": "A6", "series": "aws-nonprod-ec2", "start": "2026-07-01", "end": "2026-09-30",
     "kind": "usage", "target": "savings-tracker", "title": "Non-production schedules disabled (savings decay)",
     "cause": "About half the fleet was opted out of the schedule during a release crunch and never re-enrolled"},
    {"id": "A7", "series": "az-ai-oai", "start": "2026-08-03", "end": "2026-08-11",
     "kind": "unit-cost", "target": "detector", "title": "Prompt change raised tokens per conversation by 80%",
     "cause": "A prompt release added retrieved context to every turn; conversations did not change"},
    {"id": "A8", "series": "az-crm-vm", "start": "2026-09-01", "end": "2026-09-30",
     "kind": "rate", "target": "detector", "title": "Reservation expired: rates rose, usage did not",
     "cause": "The 1-year VM reservation ended on 31 August 2026 and was not renewed"},
]
DATA_ARTIFACT = {"id": "A2", "series": "aws-pay-ec2", "drop_day": "2026-03-03", "spike_day": "2026-03-04",
                 "moved_share": 0.65, "title": "Late-arriving billing rows (data lag)",
                 "expected": "data artifact"}
IMMATERIAL = {"id": "A9", "series": "gcp-dev-gcs", "start": "2026-06-09", "end": "2026-06-12",
              "add_list_per_day": 120.0, "title": "Small storage increase below the dollar threshold",
              "expected": "not flagged"}
ONE_TIME = [
    {"date": "2026-09-15", "sub": "aws-management", "service": "AWS Marketplace: SIEM subscription",
     "category": "Security", "amount": 48000.0, "description": "Annual subscription (one-time charge)",
     "end": "2027-09-15"},
]
OTHER_CREDITS = [
    {"date": "2026-06-10", "sub": "aws-payments-prod", "service": "Amazon EC2", "category": "Compute",
     "amount": -3000.0, "description": "Service credit"},
]

# Budget assumptions (the annual plan approved in late 2025 for calendar 2026).
BUDGET_ASSUMPTIONS = {
    "built_on": "2025-10-31",
    "migration_plan": "budget_plan",
    "ai_growth_cap_per_month": 0.03,
    "efficiency_target": 0.03,
    "efficiency_from": "2026-04-01",
    "notes": ["Statistical forecast from data through 31 October 2025",
              "Migration assumed to start 1 September 2026 (approved plan at the time)",
              "AI assistant growth capped at 3% a month by Business Planning",
              "3% efficiency target from April 2026",
              "Commitments assumed renewed on expiry (rates unchanged)"],
}


# ===========================================================================
# 2. Generator
# ===========================================================================

COLUMNS = ["BillingAccountId", "BillingAccountName", "BillingPeriodStart", "BillingPeriodEnd",
           "ChargePeriodStart", "ChargePeriodEnd", "ServiceProviderName", "SubAccountId", "SubAccountName",
           "SubAccountType", "RegionId", "ServiceName", "ServiceCategory", "ChargeCategory", "ChargeClass",
           "ChargeFrequency", "ChargeDescription", "PricingUnit", "PricingQuantity", "ListUnitPrice",
           "ContractedUnitPrice", "ListCost", "ContractedCost", "EffectiveCost", "BilledCost", "BillingCurrency",
           "CommitmentDiscountId", "CommitmentDiscountType", "CommitmentDiscountCategory",
           "CommitmentDiscountStatus", "Tags"]
NUMERIC = ["PricingQuantity", "ListUnitPrice", "ContractedUnitPrice", "ListCost", "ContractedCost",
           "EffectiveCost", "BilledCost"]
SCALED = ["PricingQuantity", "ListCost", "ContractedCost", "EffectiveCost", "BilledCost"]


def growth_factor(g: float, d: date) -> float:
    """Compound monthly growth from the start of the data."""
    return (1 + g) ** ((d - START).days / DAYS_PER_MONTH)


def ramp(d: date, start: date, end: date) -> float:
    """0 before start, 1 after end, linear in between."""
    if d < start:
        return 0.0
    if d >= end:
        return 1.0
    return (d - start).days / max(1, (end - start).days)


def tags_for(s: dict, d: date):
    current = None
    for since, tags in s["tags"]:
        if d >= since:
            current = tags
    return current


def initiative_multiplier(sid: str, d: date, off=frozenset()) -> float:
    """Usage changes from implemented initiatives (and the savings decay). `off` switches initiatives
    off, which is how generate computes the true savings for scoring."""
    weekday = d.weekday() < 5
    if sid == "aws-pay-rds" and d >= date(2026, 3, 1) and "INIT-01" not in off:
        return 0.82                                      # INIT-01 rightsizing
    if sid in ("aws-nonprod-ec2", "az-dev-vm") and d >= date(2026, 4, 15) and "INIT-02" not in off:
        if sid == "aws-nonprod-ec2" and d >= date(2026, 7, 1):
            return 0.92 if weekday else 0.70             # A6: part of the fleet opted out of the schedule
        return 0.80 if weekday else 0.35                 # INIT-02 scheduling
    return 1.0


def price_multiplier(sid: str, d: date, off=frozenset()) -> float:
    """Rate changes: INIT-03 moves objects to cheaper tiers after 30 days without access."""
    if sid == "aws-pay-s3" and d >= date(2026, 2, 1) and "INIT-03" not in off:
        days = (d - date(2026, 2, 1)).days
        return 1.0 - 0.22 * min(1.0, max(0.0, (days - 30) / 30))
    return 1.0


def additive_list_usd(sid: str, d: date) -> float:
    """Injected anomalies and planned spikes, in list dollars per day."""
    add = 0.0
    for a in INJECTED:
        if a["series"] == sid and "add_list_per_day" in a and s2d(a["start"]) <= d <= s2d(a["end"]):
            add += a["add_list_per_day"]
    if sid == IMMATERIAL["series"] and s2d(IMMATERIAL["start"]) <= d <= s2d(IMMATERIAL["end"]):
        add += IMMATERIAL["add_list_per_day"]
    if sid == "aws-nonprod-ec2" and date(2025, 11, 18) <= d <= date(2025, 11, 20):
        add += 2000.0                                    # PC-01 planned load test
    return add


def simulate_drivers(seed: int) -> dict:
    """Daily business volumes per application (the unit-economics denominators)."""
    out = {}
    for app, cfg in DRIVERS.items():
        rng = random.Random(f"{seed}:driver:{app}")
        for d in daterange(START, END):
            v = (cfg["base"] * growth_factor(cfg["growth"], d) * DOW_N[cfg["dow"]][d.weekday()]
                 * SEASON[cfg["season"]].get(d.month, 1.0) * max(0.5, 1 + rng.gauss(0, cfg["noise"])))
            out[(app, d)] = float(round(v))
    return out


def make_row(sub, service, category, charge_category, frequency, description, unit, qty, list_unit,
             contracted_unit, list_cost, contracted_cost, effective, billed, period_start, period_end,
             tags=None, commitment=None, status=""):
    prov = SUBACCOUNTS[sub][0]
    p = PROVIDERS[prov]
    ny, nm = add_months(period_start.year, period_start.month, 1)
    return {
        "BillingAccountId": p["billing_account_id"], "BillingAccountName": p["billing_account_name"],
        "BillingPeriodStart": d2s(date(period_start.year, period_start.month, 1)),
        "BillingPeriodEnd": d2s(date(ny, nm, 1)),
        "ChargePeriodStart": d2s(period_start), "ChargePeriodEnd": d2s(period_end),
        "ServiceProviderName": prov, "SubAccountId": SUBACCOUNTS[sub][1], "SubAccountName": sub,
        "SubAccountType": p["subaccount_type"], "RegionId": p["region"], "ServiceName": service,
        "ServiceCategory": category, "ChargeCategory": charge_category, "ChargeClass": "",
        "ChargeFrequency": frequency, "ChargeDescription": description, "PricingUnit": unit,
        "PricingQuantity": round(qty, 4), "ListUnitPrice": round(list_unit, 6),
        "ContractedUnitPrice": round(contracted_unit, 6), "ListCost": round(list_cost, 4),
        "ContractedCost": round(contracted_cost, 4), "EffectiveCost": round(effective, 4),
        "BilledCost": round(billed, 4), "BillingCurrency": "USD",
        "CommitmentDiscountId": commitment["id"] if commitment else "",
        "CommitmentDiscountType": commitment["type"] if commitment else "",
        "CommitmentDiscountCategory": commitment["category"] if commitment else "",
        "CommitmentDiscountStatus": status,
        "Tags": json.dumps(tags, sort_keys=True) if tags else "{}",
    }


def generate_rows(seed: int, off=frozenset()) -> tuple[list, dict]:
    """Simulate every day and return (cost rows, business drivers); `off` = initiatives switched off."""
    drivers = simulate_drivers(seed)
    rng = {s["id"]: random.Random(f"{seed}:series:{s['id']}") for s in SERIES}
    mig_rng = {s["id"]: random.Random(f"{seed}:migration:{s['id']}") for s in SERIES}
    plan = MIGRATION["actual"]
    rs, re_ = s2d(plan["ramp_start"]), s2d(plan["ramp_end"])
    rows = []
    for d in daterange(START, END):
        dim = days_in_month(d.year, d.month)
        nd = d + timedelta(days=1)
        qty, usage = {}, {}
        # 1. Usage quantity per series: base x growth x weekday x season x noise x initiatives + events
        for s in SERIES:
            sid = s["id"]
            unit_day_price = s["price"] / dim if s["storage"] else s["price"]
            if s["start"] and d < s["start"]:
                q = 0.0
            elif sid == "az-crm-vmlic":
                # Windows license meter follows VM hours; INIT-04 (Hybrid Benefit) removes 70% of it
                q = qty["az-crm-vm"] * (0.30 if d >= date(2026, 5, 1) and "INIT-04" not in off else 1.0)
            elif sid == "az-ai-oai":
                # tokens = conversations x tokens per conversation (A7: prompt change for nine days)
                tokens_per_conv = 27000 if date(2026, 8, 3) <= d <= date(2026, 8, 11) else 15000
                q = drivers[("ai-assistant", d)] * tokens_per_conv / 1e6
            else:
                q = (s["qty"] * growth_factor(s["growth"], d) * DOW_N[s["dow"]][d.weekday()]
                     * SEASON[s["season"]].get(d.month, 1.0))
                if s["noise"] > 0:
                    q *= max(0.5, 1 + rng[sid].gauss(0, s["noise"]))
                q *= initiative_multiplier(sid, d, off)
            add = additive_list_usd(sid, d)
            if add:
                q += add / unit_day_price
            if s["sub"] == MIGRATION["target_sub"] and s["service"] in MIGRATION["target_increments_list_per_day"]:
                r = ramp(d, rs, re_)
                if r > 0:
                    inc = (MIGRATION["target_increments_list_per_day"][s["service"]] * r
                           * DOW_N[s["dow"]][d.weekday()] * max(0.5, 1 + mig_rng[sid].gauss(0, 0.05)))
                    q += inc / unit_day_price
            qty[sid] = q
            pq = q / dim if s["storage"] else q          # storage: GB stored -> GB-months for this day
            lu = s["price"] * price_multiplier(sid, d, off)
            neg = PROVIDERS[SUBACCOUNTS[s["sub"]][0]]["negotiated"]
            usage[sid] = {"pq": pq, "lu": lu, "cu": lu * (1 - neg)}

        # 2. Commitments: which share of each eligible series is covered today
        cover, extra = {}, []
        if s2d(SP["start"]) <= d <= s2d(SP["end"]):
            # Spend-based plan: $/hour at Savings Plan rates, applied across eligible EC2 usage.
            # (AWS applies it to the highest savings percentage first; the discounts are equal here,
            # so a pro-rata split is used.)
            C = SP["hourly_commitment"] * 24
            disc = SP["discount"]
            elig = [sid for sid in SP_SERIES if usage[sid]["pq"] > 0]
            tot = sum(usage[sid]["pq"] * usage[sid]["cu"] for sid in elig)
            covered = min(tot, C / (1 - disc))           # contracted (on-demand equivalent) dollars covered
            for sid in elig:
                cover[sid] = (covered / tot if tot else 0.0, SP)
            unused = C - covered * (1 - disc)
            if unused > 0.01:
                extra.append(make_row("aws-management", "AWS Savings Plans", "Compute", "Usage", "Usage-Based",
                                      "Unused Savings Plan commitment", "USD", unused, 1.0, 1.0, 0.0, 0.0,
                                      unused, 0.0, d, nd, None, SP, "Unused"))
        for c in COMMITMENTS:
            if c["type"] == "Savings Plan" or not (s2d(c["start"]) <= d <= s2d(c["end"])):
                continue
            sid = "az-crm-vm" if c["type"] == "Reservation" else "gcp-prod-gce"
            u = usage[sid]
            cov_h = min(u["pq"], c["hours_per_day"])
            cover[sid] = (cov_h / u["pq"] if u["pq"] else 0.0, c)
            unused_h = c["hours_per_day"] - cov_h
            if unused_h > 0.001:
                rate = u["cu"] * (1 - c["discount"])
                extra.append(make_row(c["sub"], c["service"], "Compute", "Usage", "Usage-Based",
                                      "Unused commitment hours", "Hours", unused_h, u["lu"], u["cu"], 0.0, 0.0,
                                      unused_h * rate, 0.0, d, nd, None, c, "Unused"))

        # 3. Usage rows: a covered row (EffectiveCost amortized, BilledCost 0) and an on-demand row
        for s in SERIES:
            sid = s["id"]
            u = usage[sid]
            if u["pq"] <= 0:
                continue
            tags = tags_for(s, d)
            share, cm = cover.get(sid, (0.0, None))
            pq_c = u["pq"] * share
            pq_o = u["pq"] - pq_c
            if pq_c > 1e-9:
                lc, cc = pq_c * u["lu"], pq_c * u["cu"]
                rows.append(make_row(s["sub"], s["service"], s["cat"], "Usage", "Usage-Based", s["desc"], s["unit"],
                                     pq_c, u["lu"], u["cu"], lc, cc, cc * (1 - cm["discount"]), 0.0, d, nd,
                                     tags, cm, "Used"))
            if pq_o > 1e-9:
                lc, cc = pq_o * u["lu"], pq_o * u["cu"]
                rows.append(make_row(s["sub"], s["service"], s["cat"], "Usage", "Usage-Based", s["desc"], s["unit"],
                                     pq_o, u["lu"], u["cu"], lc, cc, cc, cc, d, nd, tags))
        rows.extend(extra)

        # 4. Monthly commitment fees: Purchase rows (BilledCost = fee, EffectiveCost = 0 because the
        #    fee is already spread over the covered and unused rows above)
        if d.day == 1:
            ny, nm = add_months(d.year, d.month, 1)
            for c in COMMITMENTS:
                if not (s2d(c["start"]) <= d <= s2d(c["end"])):
                    continue
                if c["type"] == "Savings Plan":
                    q = 24.0 * dim
                    unit_price = c["hourly_commitment"]
                elif c["type"] == "Reservation":
                    unit_price = SERIES_BY_ID["az-crm-vm"]["price"] * (1 - c["discount"])
                    q = c["hours_per_day"] * 365 / 12            # equal monthly installments
                else:
                    unit_price = (SERIES_BY_ID["gcp-prod-gce"]["price"] * (1 - PROVIDERS["Google Cloud"]["negotiated"])
                                  * (1 - c["discount"]))
                    q = c["hours_per_day"] * dim
                fee = q * unit_price
                rows.append(make_row(c["sub"], c["service"], "Compute", "Purchase", "Recurring",
                                     f"{c['name']} (monthly fee)", "Hours", q, unit_price, unit_price, fee, fee,
                                     0.0, fee, d, date(ny, nm, 1), None, c, ""))

    # 5. Credits and one-time charges
    for mo, amt in MIGRATION["credits"].items():
        y, m = ym_parse(mo)
        ny, nm = add_months(y, m, 1)
        rows.append(make_row(MIGRATION["target_sub"], "Google Cloud credits", "Other", "Credit", "One-Time",
                             "Migration promotional credit", "", 0, 0, 0, 0, 0, amt, amt, date(y, m, 1),
                             date(ny, nm, 1)))
    for c in OTHER_CREDITS:
        d = s2d(c["date"])
        rows.append(make_row(c["sub"], c["service"], c["category"], "Credit", "One-Time", c["description"], "",
                             0, 0, 0, 0, 0, c["amount"], c["amount"], d, d + timedelta(days=1)))
    for o in ONE_TIME:
        d = s2d(o["date"])
        rows.append(make_row(o["sub"], o["service"], o["category"], "Purchase", "One-Time", o["description"],
                             "Units", 1, o["amount"], o["amount"], o["amount"], o["amount"], o["amount"],
                             o["amount"], d, s2d(o["end"])))

    # 6. Data artifact (A2): 65% of one day's EC2 rows arrive late and are stamped with the next day
    art = DATA_ARTIFACT
    s = SERIES_BY_ID[art["series"]]
    moved = []
    for r in rows:
        if (r["SubAccountName"] == s["sub"] and r["ServiceName"] == s["service"]
                and r["ChargePeriodStart"] == art["drop_day"] and r["ChargeCategory"] == "Usage"):
            c = dict(r)
            c["ChargePeriodStart"] = art["spike_day"]
            c["ChargePeriodEnd"] = d2s(s2d(art["spike_day"]) + timedelta(days=1))
            for f in SCALED:
                c[f] = round(r[f] * art["moved_share"], 4)
                r[f] = round(r[f] * (1 - art["moved_share"]), 4)
            moved.append(c)
    rows.extend(moved)
    rows.sort(key=lambda r: (r["ChargePeriodStart"], PROVIDER_ORDER.index(r["ServiceProviderName"]),
                             r["SubAccountName"], r["ServiceName"], r["ChargeCategory"], r["CommitmentDiscountStatus"]))
    return rows, drivers


def write_csv(path: str, header: list, rows: list):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def true_savings(seed: int, rows: list) -> dict:
    """Ground truth for the savings tracker: regenerate the data with each initiative switched off
    (same random draws) and difference the monthly totals. Company-level, so it includes the
    Savings Plan coverage that moves to other accounts when a covered workload shrinks."""
    def monthly(rs):
        t = defaultdict(float)
        for r in rs:
            t[r["ChargePeriodStart"][:7]] += r["EffectiveCost"]
        return t
    base = monthly(rows)
    out = {}
    for ini in INITIATIVES:
        alt = monthly(generate_rows(seed, frozenset([ini["id"]]))[0])
        out[ini["id"]] = {mo: round(alt[mo] - base[mo], 2) for mo in sorted(base) if mo >= ini["start"][:7]}
    return out


def generate(out_dir: str, seed: int):
    os.makedirs(out_dir, exist_ok=True)
    rows, drivers = generate_rows(seed)
    with open(os.path.join(out_dir, "focus_costs.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    write_csv(os.path.join(out_dir, "business_metrics.csv"), ["Date", "Application", "Metric", "Value"],
              [[d2s(d), app, DRIVERS[app]["metric"], int(v)] for (app, d), v in sorted(drivers.items(),
                                                                                      key=lambda x: (x[0][1], x[0][0]))])
    write_csv(os.path.join(out_dir, "account_map.csv"),
              ["SubAccountName", "ServiceProviderName", "SubAccountId", "Kind", "Application", "Environment",
               "CostCenter", "Owner", "BudgetLine", "SharedPool"],
              [[n, SUBACCOUNTS[n][0], SUBACCOUNTS[n][1], m["kind"], m.get("application", ""),
                m.get("environment", ""), m.get("cost_center", ""), m.get("owner", ""), m["budget_line"],
                m.get("pool", "")] for n, m in ACCOUNT_MAP.items()])
    write_csv(os.path.join(out_dir, "planned_changes.csv"),
              ["Id", "Start", "End", "SubAccountName", "ServiceName", "Type", "Amount", "Recurrence", "Owner",
               "Description", "AddedOn"],
              [[c["id"], c["start"], c["end"], c["sub"], c["service"], c["type"], c["amount"], c["recurrence"],
                c["owner"], c["description"], c["added_on"]] for c in CALENDAR])
    with open(os.path.join(out_dir, "tag_standard.json"), "w") as f:
        json.dump(TAG_STANDARD, f, indent=2)
    with open(os.path.join(out_dir, "commitments.json"), "w") as f:
        json.dump(COMMITMENTS, f, indent=2)
    with open(os.path.join(out_dir, "initiatives.json"), "w") as f:
        json.dump({"implemented": INITIATIVES, "pipeline": PIPELINE}, f, indent=2)
    truth = {"anomalies": INJECTED, "data_artifact": DATA_ARTIFACT, "below_threshold": IMMATERIAL,
             "planned": [c for c in CALENDAR if c["type"] in ("planned-spike", "migration", "one-time")],
             "migration": MIGRATION, "budget_assumptions": BUDGET_ASSUMPTIONS,
             "initiative_savings": true_savings(seed, rows),
             "note": "Ground truth for scoring. A real analyst does not have this file."}
    with open(os.path.join(out_dir, "ground_truth.json"), "w") as f:
        json.dump(truth, f, indent=2)
    # The budget is built the way a planning team would: a forecast from the data available in
    # late 2025, with the plan assumptions of that time.
    data = Data(out_dir)
    budget_rows = build_budget(data)
    write_csv(os.path.join(out_dir, "budget.csv"), ["Month", "ServiceProviderName", "BudgetLine", "Budget"],
              budget_rows)
    n_usage = sum(1 for r in rows if r["ChargeCategory"] == "Usage")
    print(f"Wrote {len(rows):,} cost rows ({n_usage:,} usage rows) for {START} to {END} into {out_dir}/")
    print("Files: focus_costs.csv, business_metrics.csv, budget.csv, account_map.csv, tag_standard.json,")
    print("       planned_changes.csv, commitments.json, initiatives.json, ground_truth.json")
    totals = defaultdict(float)
    for r in rows:
        totals[r["BillingPeriodStart"][:7]] += r["EffectiveCost"]
    print()
    print_table(["Month", "EffectiveCost (amortized)"],
                [[m, money(totals[m])] for m in sorted(totals)], title="Monthly totals (all providers):")


# ===========================================================================
# 3. Loading the data set
# ===========================================================================

class Data:
    """Everything the analyses need, loaded from the generated files."""

    def __init__(self, path: str):
        self.path = path
        self.rows = []
        with open(os.path.join(path, "focus_costs.csv"), newline="") as f:
            for r in csv.DictReader(f):
                for k in NUMERIC:
                    r[k] = float(r[k]) if r[k] else 0.0
                r["_date"] = s2d(r["ChargePeriodStart"])
                r["_tags"] = json.loads(r["Tags"]) if r["Tags"] else {}
                self.rows.append(r)
        # Daily series history for the modeled scope: ChargeCategory = Usage (including unused-
        # commitment rows). Purchases, credits and one-time charges are handled as separate items.
        self.E = defaultdict(lambda: defaultdict(float))
        self.L = defaultdict(lambda: defaultdict(float))
        self.C = defaultdict(lambda: defaultdict(float))
        self.Q = defaultdict(lambda: defaultdict(float))
        self.items = defaultdict(lambda: defaultdict(float))     # month -> item -> amount
        self.OT = defaultdict(lambda: defaultdict(float))        # one-time purchases by series and day
        self.provider_of = {}
        self.per_month = set()       # series priced per GB-month: their daily cost depends on month length
        self.first = min(r["_date"] for r in self.rows)
        self.last = max(r["_date"] for r in self.rows if r["ChargeCategory"] == "Usage")
        for r in self.rows:
            k = (r["SubAccountName"], r["ServiceName"])
            self.provider_of[k] = r["ServiceProviderName"]
            if r["PricingUnit"] == "GB-Mo":
                self.per_month.add(k)
            mo = ym(r["_date"])
            self.items[mo]["billed"] += r["BilledCost"]
            self.items[mo]["effective"] += r["EffectiveCost"]
            if r["ChargeCategory"] == "Usage":
                d = r["_date"]
                self.E[k][d] += r["EffectiveCost"]
                self.L[k][d] += r["ListCost"]
                self.C[k][d] += r["ContractedCost"]
                if r["CommitmentDiscountStatus"] != "Unused":     # unused hours are not consumption
                    self.Q[k][d] += r["PricingQuantity"]
                self.items[mo]["usage"] += r["EffectiveCost"]
            elif r["ChargeCategory"] == "Credit":
                self.items[mo]["credits"] += r["EffectiveCost"]
            elif r["ChargeCategory"] == "Purchase" and r["CommitmentDiscountId"]:
                self.items[mo]["commitment_purchases"] += r["BilledCost"]
            elif r["ChargeCategory"] == "Purchase":
                self.items[mo]["one_time"] += r["EffectiveCost"]
                self.OT[k][r["_date"]] += r["EffectiveCost"]
        self.keys = sorted(self.E.keys(), key=lambda k: (PROVIDER_ORDER.index(self.provider_of[k]), k))
        self.drivers = {}
        p = os.path.join(path, "business_metrics.csv")
        if os.path.exists(p):
            with open(p, newline="") as f:
                for r in csv.DictReader(f):
                    self.drivers[(r["Application"], s2d(r["Date"]))] = float(r["Value"])
        self.budget = defaultdict(float)
        p = os.path.join(path, "budget.csv")
        if os.path.exists(p):
            with open(p, newline="") as f:
                for r in csv.DictReader(f):
                    self.budget[(r["Month"], r["ServiceProviderName"], r["BudgetLine"])] += float(r["Budget"])
        self.true_savings = {}       # scoring only, like the anomalies' ground truth
        p = os.path.join(path, "ground_truth.json")
        if os.path.exists(p):
            with open(p) as f:
                self.true_savings = json.load(f).get("initiative_savings", {})

    def month_total(self, month: str) -> float:
        """Total EffectiveCost (amortized) for a month: usage + one-time + credits."""
        it = self.items[month]
        return it["usage"] + it["one_time"] + it["credits"]

    def usage_total(self, month: str) -> float:
        return self.items[month]["usage"]

    def rows_in(self, month: str):
        return [r for r in self.rows if ym(r["_date"]) == month]


def budget_line_of(key) -> str:
    return ACCOUNT_MAP[key[0]]["budget_line"]


# ===========================================================================
# 4. Forecasting: seasonal-naive weekday profile + robust level + damped trend, plus drivers
# ===========================================================================

def monthly_levels(vals: dict, as_of: date, first: date) -> list:
    """Weekday-balanced robust level of each complete month up to as_of.

    For each weekday take the median of that weekday's values in the month, then average the
    seven medians. This removes the weekday mix of the month and resists short anomalies."""
    out = []
    y, m = first.year, first.month
    if first.day != 1:
        y, m = add_months(y, m, 1)
    while True:
        me = month_end(y, m)
        if me > as_of:
            break
        by_wd = [[] for _ in range(7)]
        for dd in daterange(date(y, m, 1), me):
            by_wd[dd.weekday()].append(vals.get(dd, 0.0))
        out.append((f"{y:04d}-{m:02d}", sum(median(b) for b in by_wd) / 7))
        y, m = add_months(y, m, 1)
    return out


def fit_series(vals: dict, as_of: date, first: date = START, g_override=None, level_days: int = 28,
               per_month: bool = False):
    """Fit the model to one daily series using only days <= as_of. None if no recent cost.

    w      weekday profile: seasonal-naive over the last 12 weeks (median ratio to the week's mean)
    level  median of the weekday-adjusted values of the last `level_days` days
    g      monthly growth: median month-over-month change of the last six monthly levels, clipped
           to [-4%, +8%] so one step change cannot become a trend
    S      yearly seasonal index by calendar month from a 2x12 centered moving average; only
           estimable with 13+ months of history, and only kept when it differs from 1 by 4%+
    per_month  for meters priced per GB-month (storage): the same GB costs 1/28 of the month's price
           per day in February and 1/31 in January, so the series is fitted on a constant-month
           basis (daily cost x days in month / 30.4375) and predict() converts back."""
    if per_month:
        vals = {d: v * days_in_month(d.year, d.month) / DAYS_PER_MONTH for d, v in vals.items()}
    window = [as_of - timedelta(days=i) for i in range(83, -1, -1)]
    x = [vals.get(dd, 0.0) for dd in window]
    if sum(x[-level_days:]) <= 0:
        return None
    ratios = [[] for _ in range(7)]
    for b in range(12):
        block = window[b * 7:(b + 1) * 7]
        v = x[b * 7:(b + 1) * 7]
        mean = sum(v) / 7
        if mean > 0:
            for dd, vv in zip(block, v):
                ratios[dd.weekday()].append(vv / mean)
    w = [median(r) if r else 1.0 for r in ratios]
    mw = sum(w) / 7
    w = [v / mw for v in w] if mw > 0 else [1.0] * 7
    recent = window[-level_days:]
    des = [vals.get(dd, 0.0) / w[dd.weekday()] for dd in recent if w[dd.weekday()] > 0.05]
    level = median(des)
    M = monthly_levels(vals, as_of, first)
    if g_override is not None:
        g = g_override
    else:
        last = M[-7:]
        rates = [b / a - 1 for (_, a), (_, b) in zip(last, last[1:]) if a > 0 and b > 0]
        g = median(rates) if len(rates) >= 3 else 0.0
        g = max(-0.04, min(0.08, g))
    S = {}
    if len(M) >= 13:
        lv = [v for _, v in M]
        for i in range(6, len(M) - 6):
            cma = (0.5 * lv[i - 6] + sum(lv[i - 5:i + 6]) + 0.5 * lv[i + 6]) / 12
            if cma > 0 and lv[i] > 0 and abs(lv[i] / cma - 1) >= 0.04:
                S[int(M[i][0][5:7])] = lv[i] / cma
    center = as_of - timedelta(days=level_days // 2)
    level /= S.get(center.month, 1.0)
    return {"w": w, "level": level, "g": g, "S": S, "center": center, "per_month": per_month}


def growth_multiplier(g: float, h: float, phi: float = 0.97) -> float:
    """Damped trend: the monthly growth rate fades by phi each month, so long horizons do not run away."""
    if h <= 0 or phi >= 1:
        return (1 + g) ** h                  # phi = 1 means no damping
    return (1 + g) ** (phi * (1 - phi ** h) / (1 - phi))


def predict(fit: dict, dd: date) -> float:
    h = (dd - fit["center"]).days / DAYS_PER_MONTH
    v = fit["level"] * growth_multiplier(fit["g"], h) * fit["w"][dd.weekday()] * fit["S"].get(dd.month, 1.0)
    return v * DAYS_PER_MONTH / days_in_month(dd.year, dd.month) if fit["per_month"] else v


def plan_dates(plan_key: str) -> dict:
    return {k: s2d(v) for k, v in MIGRATION[plan_key].items()}


def sp_pool_cost(contracted: float, commit_per_day: float, disc: float) -> float:
    """Amortized daily cost of eligible usage under a spend-based commitment.

    The commitment (in Savings Plan dollars) covers contracted usage worth commit / (1 - disc);
    anything above that is paid on demand; anything below it is unused but still paid."""
    if commit_per_day <= 0:
        return contracted
    return commit_per_day + max(0.0, contracted - commit_per_day / (1 - disc))


def forecast_engine(D: Data, as_of: date, end: date, plan_key: str = "actual", use_drivers: bool = True,
                    include_items: bool = True, growth_overrides: dict | None = None,
                    renewal_hourly: float | None = None) -> dict:
    """Forecast EffectiveCost (amortized) from the day after as_of to end.

    Components per month:
      statistical  per-series weekday profile x level x damped trend x yearly index
      migration    driver adjustment: the Google Cloud build-out replaces the statistical extrapolation
                   of the target project, the AWS source is switched off at decommission, and the
                   Savings Plan pool is recomputed without the source EC2 (where unused commitment appears)
      renewal      Savings Plan renewed at `renewal_hourly` once the current plan expires
      known_items  one-time charges on the planned-change calendar and contracted credits
      savings      pipeline opportunities weighted by probability (negative)"""
    growth_overrides = growth_overrides or {}
    plan = plan_dates(plan_key)
    horizon = list(daterange(as_of + timedelta(days=1), end))
    stat, fits = {}, {}
    for k in D.keys:
        fit = fit_series(D.E[k], as_of, D.first, growth_overrides.get(k), per_month=k in D.per_month)
        if fit:
            fits[k] = fit
            stat[k] = {dd: predict(fit, dd) for dd in horizon}
    comp = defaultdict(lambda: defaultdict(float))
    series_month = defaultdict(lambda: defaultdict(float))
    for k, daily in stat.items():
        for dd, v in daily.items():
            comp[ym(dd)]["statistical"] += v
            series_month[k][ym(dd)] += v

    def add(component, k, dd, v):
        comp[ym(dd)][component] += v
        series_month[k][ym(dd)] += v

    if use_drivers:
        src, tgt = MIGRATION["source_sub"], MIGRATION["target_sub"]
        rs, re_ = plan["ramp_start"], plan["ramp_end"]
        # (a) Target project: pre-migration baseline with organic growth + increment x ramp.
        for svc, inc_list in MIGRATION["target_increments_list_per_day"].items():
            k = (tgt, svc)
            neg = PROVIDERS[SUBACCOUNTS[tgt][0]]["negotiated"]
            vals = D.E.get(k, {})
            pre_end = min(as_of, rs - timedelta(days=1))
            base_fit = (fit_series(vals, pre_end, D.first, MIGRATION["organic_growth"], per_month=k in D.per_month)
                        if vals else None)
            full_fit = fits.get(k)
            if full_fit and as_of >= rs + timedelta(days=28):
                w = full_fit["w"]
            elif base_fit:
                w = base_fit["w"]
            else:
                w = DOW_N["flat"] if svc == "Cloud Storage" else DOW_N["batch"]
            inc = inc_list * (1 - neg)
            if as_of >= re_ + timedelta(days=14):
                # The ramp is finished: replace the plan's increment with the observed one.
                recent = [vals.get(as_of - timedelta(days=i), 0.0) / max(0.05, w[(as_of - timedelta(days=i)).weekday()])
                          for i in range(14)]
                base_now = 0.0
                if base_fit:   # the pre-migration base today, without its weekday factor
                    base_now = predict(base_fit, as_of) / max(0.05, base_fit["w"][as_of.weekday()])
                inc = max(0.0, median(recent) - base_now)
            for dd in horizon:
                base = predict(base_fit, dd) if base_fit else 0.0
                new = base + inc * ramp(dd, rs, re_) * w[dd.weekday()]
                add("migration", k, dd, new - stat.get(k, {}).get(dd, 0.0))
        # (b) Source account: EMR stops at decommission, S3 data is deleted later.
        for k in list(stat):
            if k[0] != src:
                continue
            for dd in horizon:
                stop_storage = k[1] in MIGRATION["source_storage_services"] and dd >= plan["decommission_storage"]
                stop_compute = (k[1] in MIGRATION["source_compute_services"] and k[1] != "Amazon EC2"
                                and dd >= plan["decommission_compute"])
                if stop_storage or stop_compute:
                    add("migration", k, dd, -stat[k][dd])
        # (c) Savings Plan pool: remove the source EC2 at decommission and let the commitment re-apply
        #     to what is left (unused commitment appears on low days); then the renewal assumption.
        statC = {}
        for k in SP_KEYS:
            fitc = fit_series(D.C.get(k, {}), as_of, D.first, growth_overrides.get(k))
            statC[k] = {dd: (predict(fitc, dd) if fitc else 0.0) for dd in horizon}
        src_key = (src, "Amazon EC2")
        disc, c_old, sp_end = SP["discount"], SP["hourly_commitment"] * 24, s2d(SP["end"])
        for dd in horizon:
            tot = sum(statC[k][dd] for k in SP_KEYS)
            changed = tot - (statC[src_key][dd] if dd >= plan["decommission_compute"] else 0.0)
            mig = sp_pool_cost(changed, c_old, disc) - sp_pool_cost(tot, c_old, disc)
            if mig:
                add("migration", src_key, dd, mig)
            if dd > sp_end and renewal_hourly is not None:
                add("renewal", src_key, dd,
                    sp_pool_cost(changed, renewal_hourly * 24, disc) - sp_pool_cost(changed, c_old, disc))

    if include_items:
        for c in CALENDAR:
            if c["type"] != "one-time" or s2d(c["added_on"]) > as_of:
                continue
            occ = s2d(c["start"])
            while occ <= end:
                if occ > as_of:
                    comp[ym(occ)]["known_one_time"] += c["amount"]
                if c["recurrence"] != "annual":
                    break
                occ = date(occ.year + 1, occ.month, occ.day)
        if plan_key == "actual" and s2d(MIGRATION["approved_on"]) <= as_of:
            for mo, amt in MIGRATION["credits"].items():
                ms, _ = month_bounds(mo)
                if as_of < ms <= end:
                    comp[mo]["known_credits"] += amt
        for p in PIPELINE:
            if s2d(p["registered_on"]) > as_of:
                continue
            for dd in horizon:
                if dd >= s2d(p["start"]):
                    comp[ym(dd)]["savings"] -= p["monthly"] * p["probability"] / days_in_month(dd.year, dd.month)

    months = sorted({ym(dd) for dd in horizon})
    scope = [k for k in series_month if k[0] == MIGRATION["source_sub"] or
             (k[0] == MIGRATION["target_sub"] and k[1] in MIGRATION["target_increments_list_per_day"])]
    for mo in months:
        c = comp[mo]
        c["known_items"] = c["known_one_time"] + c["known_credits"]
        c["modeled"] = c["statistical"] + c["migration"] + c["renewal"]
        c["final"] = c["modeled"] + c["known_items"] + c["savings"]
        # Presentation split: workloads in the migration scope are forecast from the plan (drivers);
        # everything else is the run-rate business forecast statistically.
        c["migration_scope"] = sum(series_month[k].get(mo, 0.0) for k in scope) - c["renewal"]
        c["run_rate"] = c["modeled"] - c["migration_scope"] - c["renewal"]
    return {"as_of": as_of, "end": end, "months": months, "comp": comp, "series_month": series_month,
            "fits": fits}


def build_budget(D: Data) -> list:
    """The 2026 budget as a planning team would have built it in late 2025 (see BUDGET_ASSUMPTIONS)."""
    a = BUDGET_ASSUMPTIONS
    ai_keys = [k for k in D.keys if k[0] == "az-ai-assistant-prod"]
    fc = forecast_engine(D, s2d(a["built_on"]), date(2026, 12, 31), plan_key=a["migration_plan"],
                         include_items=False, growth_overrides={k: a["ai_growth_cap_per_month"] for k in ai_keys})
    cells = defaultdict(float)
    for k, months in fc["series_month"].items():
        for mo, v in months.items():
            if not mo.startswith("2026"):
                continue
            if mo >= a["efficiency_from"][:7]:
                v *= 1 - a["efficiency_target"]
            cells[(mo, D.provider_of[k], budget_line_of(k))] += v
    out = []
    for (mo, prov, line), v in sorted(cells.items(), key=lambda x: (x[0][0], PROVIDER_ORDER.index(x[0][1]), x[0][2])):
        out.append([mo, prov, line, int(round(v / 100.0)) * 100])
    return out


def backtest(D: Data, origins: list, horizons=(1, 3)) -> list:
    """Rolling-origin backtest on the modeled scope (usage EffectiveCost, excluding one-time items)."""
    out = []
    for o in origins:
        hmax = max(horizons)
        y, m = add_months(o.year, o.month, hmax)
        end = min(month_end(y, m), D.last)
        fs = forecast_engine(D, o, end, use_drivers=False, include_items=False)
        fd = forecast_engine(D, o, end, use_drivers=True, include_items=False)
        for h in horizons:
            y, m = add_months(o.year, o.month, h)
            if month_end(y, m) > D.last:
                continue
            mo = f"{y:04d}-{m:02d}"
            actual = D.usage_total(mo)
            naive = D.usage_total(ym(o)) / days_in_month(o.year, o.month) * days_in_month(y, m)
            out.append({"origin": o, "month": mo, "h": h, "actual": actual, "naive": naive,
                        "stat": fs["comp"][mo]["modeled"], "drivers": fd["comp"][mo]["modeled"]})
    return out


def context_notes(k, month: str) -> str:
    """What the analyst's own records say about a series in a month (calendar, commitments, register)."""
    ms, me = month_bounds(month)
    notes = []
    for c in COMMITMENTS:
        end = s2d(c["end"])
        if c["sub"] == k[0] and c["service"] == k[1] and ms - timedelta(days=1) <= end <= me:
            notes.append(f"commitment {c['id']} ended {c['end']}")
    if k in SP_KEYS:
        notes.append("Savings Plan coverage shifts between accounts")
    for c in CALENDAR:
        if c["sub"] != k[0] or not service_match(c["service"], k[1]):
            continue
        cs = s2d(c["start"])
        ce = s2d(c["end"]) if c["end"] else cs
        if cs <= me and ce >= ms:
            notes.append(f"{c['id']}: {c['description']}")
    for ini in INITIATIVES:
        for sid in ini["series"]:
            s = SERIES_BY_ID[sid]
            if (s["sub"], s["service"]) == k and s2d(ini["start"]) <= me:
                notes.append(f"{ini['id']}: {ini['name']}")
    if k[0] == MIGRATION["source_sub"] and "migration" not in " ".join(notes):
        notes.append("migration source")
    return "; ".join(notes) if notes else "investigate"


def service_match(pattern: str, service: str) -> bool:
    if pattern == "*":
        return True
    if pattern.endswith("*"):
        return service.startswith(pattern[:-1])
    return service in pattern.split(";")


def error_stats(results: list, field: str, h: int) -> tuple[float, float, float]:
    """MAPE = mean(|A-F|/A); WAPE = sum|A-F| / sum A; bias = sum(F-A) / sum A."""
    rs = [r for r in results if r["h"] == h]
    if not rs:
        return 0.0, 0.0, 0.0
    mape = sum(abs(r["actual"] - r[field]) / r["actual"] for r in rs) / len(rs)
    wape = sum(abs(r["actual"] - r[field]) for r in rs) / sum(r["actual"] for r in rs)
    bias = sum(r[field] - r["actual"] for r in rs) / sum(r["actual"] for r in rs)
    return mape, wape, bias


def rms_pct_error(results: list, field: str, h: int) -> float:
    rs = [r for r in results if r["h"] == h]
    if not rs:
        return 0.0
    return math.sqrt(sum(((r[field] - r["actual"]) / r["actual"]) ** 2 for r in rs) / len(rs))


# ===========================================================================
# 5. forecast
# ===========================================================================

BACKTEST_ORIGINS = [date(2026, 3, 31), date(2026, 4, 30), date(2026, 5, 31), date(2026, 6, 30),
                    date(2026, 7, 31), date(2026, 8, 31)]


def compute_forecast(D: Data, as_of: date | None = None, months: int = 12) -> dict:
    as_of = as_of or D.last
    y, m = add_months(as_of.year, as_of.month, months)
    end = month_end(y, m)
    sizing = sp_sizing(D, as_of)
    fc = forecast_engine(D, as_of, end, renewal_hourly=sizing["recommended_hourly"])
    bt = backtest(D, [o for o in BACKTEST_ORIGINS if o < as_of])
    s1, s3 = rms_pct_error(bt, "drivers", 1), rms_pct_error(bt, "drivers", 3)
    ranges = {}
    for i, mo in enumerate(fc["months"], start=1):
        sig = max(s1 * math.sqrt(i), s3 * math.sqrt(i / 3))
        f = fc["comp"][mo]["final"]
        ranges[mo] = (f * (1 - 1.28 * sig), f * (1 + 1.28 * sig))
    by_provider = defaultdict(lambda: defaultdict(float))
    for k, months_ in fc["series_month"].items():
        for mo, v in months_.items():
            by_provider[mo][D.provider_of[k]] += v
    year = str(as_of.year)
    fy_actual = sum(D.month_total(mo) for mo in month_list(f"{year}-01", ym(as_of)))
    fy_fc = sum(fc["comp"][mo]["final"] for mo in fc["months"] if mo.startswith(year))
    fy_budget = sum(v for (mo, _, _), v in D.budget.items() if mo.startswith(year))
    return {"as_of": as_of, "fc": fc, "backtest": bt, "ranges": ranges, "by_provider": by_provider,
            "sizing": sizing, "fy": {"year": year, "actual": fy_actual, "forecast": fy_fc,
                                     "outlook": fy_actual + fy_fc, "budget": fy_budget},
            "sigma": (s1, s3)}


def cmd_forecast(D: Data, args):
    R = compute_forecast(D)
    fc, bt = R["fc"], R["backtest"]
    section(f"Forecast as of {R['as_of']}: next 12 months of EffectiveCost (amortized, USD)")
    print("Method: per series (sub-account x service), a seasonal-naive weekday profile from the last 12 weeks,")
    print("a robust level (median of the last 28 weekday-adjusted days), a damped monthly trend (median")
    print("month-over-month change of the last six months, clipped to -4%..+8%, damped 0.97 a month) and a yearly")
    print("index where 13+ months of history allow it. Storage, priced per GB-month, is fitted on a constant-month")
    print("basis. Driver adjustments: the migration (Google Cloud build-out, AWS decommission, Savings Plan pool")
    print("recomputed), the Savings Plan renewal, known one-time items and credits, and pipeline savings weighted")
    print("by probability.")
    print()
    rows = []
    for r in bt:
        rows.append([str(r["origin"]), r["month"], r["h"], money(r["actual"]), money(r["naive"]), money(r["stat"]),
                     money(r["drivers"]), pct(abs(r["naive"] / r["actual"] - 1)),
                     pct(abs(r["stat"] / r["actual"] - 1)), pct(abs(r["drivers"] / r["actual"] - 1))])
    print_table(["Origin", "Month", "h", "Actual", "Naive", "Statistical", "Stat+drivers", "APE naive", "APE stat",
                 "APE drivers"], rows, "llr" + "r" * 7,
                title="Backtest (rolling origin; recurring usage only, one-time items excluded):")
    rows = []
    for field, name in (("naive", "Naive (last month's daily rate)"), ("stat", "Statistical"),
                        ("drivers", "Statistical + drivers")):
        m1, w1, b1 = error_stats(bt, field, 1)
        m3, w3, b3 = error_stats(bt, field, 3)
        rows.append([name, pct(m1), pct(w1), spct(b1), pct(m3), pct(w3), spct(b3)])
    print_table(["Model", "MAPE h=1", "WAPE h=1", "Bias h=1", "MAPE h=3", "WAPE h=3", "Bias h=3"], rows,
                title="Accuracy (MAPE = mean |A-F|/A; WAPE = sum |A-F| / sum A; bias = sum (F-A) / sum A):")
    rows = []
    for mo in fc["months"]:
        c = fc["comp"][mo]
        lo, hi = R["ranges"][mo]
        rows.append([mo, money(c["run_rate"]), money(c["migration_scope"]), smoney(c["renewal"]),
                     smoney(c["known_items"]), smoney(c["savings"]), money(c["final"]),
                     f"{kmoney(lo)} - {kmoney(hi)}"])
    tot = {f: sum(fc["comp"][mo][f] for mo in fc["months"])
           for f in ("run_rate", "migration_scope", "renewal", "known_items", "savings", "final")}
    rows.append(["Total", money(tot["run_rate"]), money(tot["migration_scope"]), smoney(tot["renewal"]),
                 smoney(tot["known_items"]), smoney(tot["savings"]), money(tot["final"]), ""])
    print("Run-rate = all other workloads, forecast statistically. Migration scope = the AWS data platform and the")
    print("Google Cloud services replacing it, forecast from the plan (ramp, decommission dates, Savings Plan pool).")
    print()
    print_table(["Month", "Run-rate", "Migration scope", "SP renewal", "Known items", "Exp. savings", "Forecast",
                 "~80% range"], rows,
                title=f"12-month forecast (renewal assumed at ${R['sizing']['recommended_hourly']:.0f}/hour; "
                      f"range from backtest errors, sigma h1 {pct(R['sigma'][0])}, h3 {pct(R['sigma'][1])}):")
    rows = []
    for mo in fc["months"]:
        bp = R["by_provider"][mo]
        c = fc["comp"][mo]
        rows.append([mo] + [money(bp[p]) for p in PROVIDER_ORDER]
                    + [smoney(c["known_items"] + c["savings"]), money(c["final"])])
    print_table(["Month"] + PROVIDER_ORDER + ["Items+savings", "Total"], rows,
                title="By provider (renewal and SP effects sit with AWS; items and savings are not split):")
    fy = R["fy"]
    print(f"Full-year {fy['year']} outlook: actual Jan-{R['as_of'].strftime('%b')} {money(fy['actual'])} + forecast "
          f"{money(fy['forecast'])} = {money(fy['outlook'])} vs budget {money(fy['budget'])} "
          f"({smoney(fy['outlook'] - fy['budget'])}, {spct(fy['outlook'] / fy['budget'] - 1)}).")
    sz = R["sizing"]
    print(f"Savings Plan after the AWS decommission ({MIGRATION['actual']['decommission_compute']}): projected "
          f"utilization {pct(sz['post_decom_util'])}, about {money(sz['post_decom_waste_month'])}/month unused until "
          f"expiry on {SP['end']}.")
    ai = [k for k in fc["fits"] if k[0] == "az-ai-assistant-prod" and k[1] == "Azure OpenAI"]
    if ai:
        print(f"AI assistant model spend trend: {spct(fc['fits'][ai[0]]['g'])} a month (damped in the forecast).")
    print()


# ===========================================================================
# 6. variance
# ===========================================================================

def compute_variance(D: Data, month: str) -> dict:
    """Budget vs forecast (made the day before the month) vs actual, with a volume/mix/rate bridge.

    For each series: L = usage at list prices (the volume measure), e = EffectiveCost / ListCost
    (the effective rate per list dollar). Forecast rate eF = e over the 28 days before the month;
    forecast volume LF = EF / eF.
      volume = (sum LA - sum LF) x eF_avg          more or less usage, at the forecast average rate
      mix    = sum(LA x eF) - sum(LA) x eF_avg     usage moved between services with different rates
      rate   = sum(LA x (eA - eF))                 the price paid per unit changed
    volume + mix + rate = actual usage cost - forecast usage cost exactly."""
    ms, me = month_bounds(month)
    as_of = ms - timedelta(days=1)
    fc = forecast_engine(D, as_of, me)
    c = fc["comp"][month]
    series = []
    for k in D.keys:
        EF = fc["series_month"].get(k, {}).get(month, 0.0)
        EA = sum(D.E[k].get(dd, 0.0) for dd in daterange(ms, me))
        LA = sum(D.L[k].get(dd, 0.0) for dd in daterange(ms, me))
        l28 = sum(D.L[k].get(as_of - timedelta(days=i), 0.0) for i in range(28))
        e28 = sum(D.E[k].get(as_of - timedelta(days=i), 0.0) for i in range(28))
        if abs(EF) < 0.01 and abs(EA) < 0.01:
            continue
        if l28 <= 0 and LA <= 0:
            series.append({"key": k, "kind": "commitment", "EF": EF, "EA": EA, "LF": 0.0, "LA": 0.0,
                           "usage": EA - EF, "rate": 0.0})
            continue
        eA = EA / LA if LA > 0 else None
        eF = e28 / l28 if l28 > 0 else eA
        LF = EF / eF if eF else 0.0
        series.append({"key": k, "kind": "usage", "EF": EF, "EA": EA, "LF": LF, "LA": LA, "eF": eF, "eA": eA,
                       "usage": (LA - LF) * eF, "rate": LA * (eA - eF) if eA is not None else 0.0})
    us = [s for s in series if s["kind"] == "usage"]
    LF_tot, LA_tot = sum(s["LF"] for s in us), sum(s["LA"] for s in us)
    EF_tot = sum(s["EF"] for s in us)
    eF_avg = EF_tot / LF_tot if LF_tot else 0.0
    volume = (LA_tot - LF_tot) * eF_avg
    mix = sum(s["LA"] * s["eF"] for s in us) - LA_tot * eF_avg
    rate = sum(s["rate"] for s in us)
    commit = sum(s["usage"] for s in series if s["kind"] == "commitment")
    it = D.items[month]
    A_one, A_cred = it["one_time"], it["credits"]
    F_one, F_cred, F_sav = c["known_one_time"], c["known_credits"], c["savings"]
    forecast = c["final"]
    actual = D.month_total(month)
    budget_by_line = defaultdict(float)
    for (mo, _, line), v in D.budget.items():
        if mo == month:
            budget_by_line[line] += v
    budget = sum(budget_by_line.values())
    f_line, a_line = defaultdict(float), defaultdict(float)
    for s in series:
        f_line[budget_line_of(s["key"])] += s["EF"]
    for cal in CALENDAR:
        if cal["type"] == "one-time" and ms <= s2d(cal["start"]) <= me and s2d(cal["added_on"]) <= as_of:
            f_line[ACCOUNT_MAP[cal["sub"]]["budget_line"]] += cal["amount"]
    f_line[ACCOUNT_MAP[MIGRATION["target_sub"]]["budget_line"]] += F_cred
    if F_sav:
        f_line["(pipeline savings)"] += F_sav
    for r in D.rows_in(month):
        a_line[ACCOUNT_MAP[r["SubAccountName"]]["budget_line"]] += r["EffectiveCost"]
    bridge = [("Volume (usage at forecast rates)", volume), ("Mix (between services)", mix),
              ("Rate (price per unit)", rate), ("Unused commitment", commit),
              ("One-time charges", A_one - F_one), ("Credits", A_cred - F_cred)]
    if F_sav:
        bridge.append(("Expected savings not yet realized", -F_sav))
    residual = actual - forecast - sum(v for _, v in bridge)
    return {"month": month, "as_of": as_of, "budget": budget, "forecast": forecast, "actual": actual,
            "series": series, "bridge": bridge, "residual": residual, "budget_by_line": budget_by_line,
            "f_line": f_line, "a_line": a_line, "one_time": (A_one, F_one), "credits": (A_cred, F_cred)}


def cmd_variance(D: Data, args):
    V = compute_variance(D, args.month)
    B, F, A = V["budget"], V["forecast"], V["actual"]
    section(f"Variance for {V['month']}: budget vs forecast vs actual (EffectiveCost, amortized)")
    print_table(["Measure", "Amount", "Actual minus", "%"],
                [["Budget (approved late 2025)", money(B), smoney(A - B), spct(A / B - 1)],
                 [f"Forecast (made {V['as_of']})", money(F), smoney(A - F), spct(A / F - 1)],
                 ["Actual", money(A), "", ""]])
    fa = (F - A) / F
    print(f"Forecast accuracy (FinOps Foundation: (forecast - actual) / forecast) = {spct(fa)}")
    bv = abs(A / B - 1)
    level = "within Run (12%)" if bv <= 0.12 else "within Walk (15%)" if bv <= 0.15 else \
        "within Crawl (20%)" if bv <= 0.20 else "outside even the Crawl threshold (20%)"
    print(f"Budget variance {pct(bv)}: {level} of the FinOps Foundation budgeting thresholds.")
    print()
    lines = sorted(set(V["budget_by_line"]) | set(V["f_line"]) | set(V["a_line"]))
    rows = []
    for ln in lines:
        b, f, a = V["budget_by_line"].get(ln, 0.0), V["f_line"].get(ln, 0.0), V["a_line"].get(ln, 0.0)
        flag = "explain" if abs(a - f) >= max(10000, 0.05 * abs(f)) or abs(a - b) >= max(10000, 0.05 * abs(b)) else ""
        rows.append([ln, money(b), money(f), money(a), smoney(a - b), smoney(a - f), flag])
    rows.append(["Total", money(B), money(F), money(A), smoney(A - B), smoney(A - F), ""])
    print_table(["Budget line", "Budget", "Forecast", "Actual", "Act - Bud", "Act - Fcst", "Materiality"], rows,
                title="By budget line (materiality: |difference| >= max($10,000, 5%)):")
    rows = [["Budget", "", money(B)]]
    run = B
    for ln in lines:
        d = V["f_line"].get(ln, 0.0) - V["budget_by_line"].get(ln, 0.0)
        if abs(d) >= 1000:
            run += d
            rows.append([f"  plan change: {ln}", smoney(d), money(run)])
    other = F - run
    if abs(other) >= 1:
        run += other
        rows.append(["  plan change: other lines", smoney(other), money(run)])
    rows.append(["Forecast", "", money(F)])
    for name, v in V["bridge"]:
        run += v
        rows.append([f"  {name}", smoney(v), money(run)])
    rows.append(["Actual", "", money(A)])
    print_table(["Step", "Change", "Running total"], rows, "lrr",
                title="Bridge: budget -> forecast -> actual:")
    if abs(V["residual"]) > 1:
        print(f"(Residual not explained by the bridge: {smoney(V['residual'])})\n")
    drivers = []
    for s in V["series"]:
        drivers.append((s["usage"] + s["rate"], s))
    drivers.sort(key=lambda x: -abs(x[0]))
    rows = []
    for tot, s in drivers[:10]:
        rows.append([f"{s['key'][0]} / {s['key'][1]}", smoney(s["usage"]), smoney(s["rate"]), smoney(tot),
                     context_notes(s["key"], V["month"])[:70]])
    A_one, F_one = V["one_time"]
    if A_one - F_one:
        rows.append(["(one-time charges)", smoney(A_one - F_one), "+$0", smoney(A_one - F_one),
                     "not in the forecast: added to the calendar after it was made"])
    print_table(["Series", "Usage (vol+mix)", "Rate", "Total", "Context from calendar, commitments, register"],
                rows, "lrrrl", title="Top drivers, forecast -> actual:")


# ===========================================================================
# 7. anomalies
# ===========================================================================

DEFAULT_RULE = {"name": "default", "weeks": 6, "z": 4.0, "pct": 0.25, "usd": 500.0}
SWEEP_RULES = [
    {"name": "loose", "weeks": 6, "z": 3.0, "pct": 0.15, "usd": 250.0},
    {"name": "medium", "weeks": 6, "z": 3.5, "pct": 0.20, "usd": 400.0},
    DEFAULT_RULE,
    {"name": "strict", "weeks": 6, "z": 5.0, "pct": 0.40, "usd": 1000.0},
]
UNIT_SCOPES = {"ai-assistant": ["az-ai-assistant-prod"], "payments-api": ["aws-payments-prod"]}


def robust_baseline(vals: dict, d: date, weeks: int, floor: float = 1.0) -> tuple[float, float]:
    """Median of the same weekday over the previous `weeks` weeks, and a robust sigma (1.4826 x MAD),
    floored at 5% of the median (and at `floor` dollars) so flat series do not produce infinite z-scores."""
    hist = [vals.get(d - timedelta(weeks=i), 0.0) for i in range(1, weeks + 1)]
    med = median(hist)
    mad = median(abs(v - med) for v in hist)
    return med, max(1.4826 * mad, 0.05 * med, floor)


def detect_series(vals: dict, start: date, end: date, rule: dict) -> list:
    """Flag a day when z >= rule z AND the increase is >= rule pct AND >= rule usd (all three)."""
    flags = []
    for d in daterange(start, end):
        med, sigma = robust_baseline(vals, d, rule["weeks"])
        x = vals.get(d, 0.0)
        excess = x - med
        if excess <= 0:
            continue
        z = excess / sigma
        rel = excess / med if med > 0 else float("inf")
        if z >= rule["z"] and rel >= rule["pct"] and excess >= rule["usd"]:
            flags.append({"date": d, "value": x, "baseline": med, "excess": excess, "z": z, "rel": rel})
    return flags


def group_events(flags: list, gap_days: int = 2) -> list:
    """Merge flagged days into events; gaps of up to two days (a weekend) do not split an event."""
    events = []
    for f in flags:
        if events and (f["date"] - events[-1]["end"]).days <= gap_days + 1:
            events[-1]["end"] = f["date"]
            events[-1]["flags"].append(f)
        else:
            events.append({"start": f["date"], "end": f["date"], "flags": [f]})
    return events


def attribute_event(D: Data, k, ev: dict, weeks: int) -> tuple[float, float, str]:
    """Split the excess into usage (volume at list prices) and rate (effective price per list dollar)."""
    usage = rate = 0.0
    for f in ev["flags"]:
        d = f["date"]
        L, E = D.L[k].get(d, 0.0), D.E[k].get(d, 0.0)
        hist = [d - timedelta(weeks=i) for i in range(1, weeks + 1)]
        L0 = median(D.L[k].get(h, 0.0) for h in hist)
        ratios = [D.E[k].get(h, 0.0) / D.L[k].get(h, 0.0) for h in hist if D.L[k].get(h, 0.0) > 0]
        e0 = median(ratios) if ratios else (E / L if L > 0 else 1.0)
        if L <= 0:
            usage += f["excess"]
            continue
        u, r = (L - L0) * e0, L * (E / L - e0)
        if abs(u + r) > 1e-9:
            usage += f["excess"] * u / (u + r)
            rate += f["excess"] * r / (u + r)
        else:
            usage += f["excess"]
    tot = usage + rate
    share = rate / tot if tot else 0.0
    return usage, rate, ("rate" if share >= 0.6 else "usage" if share <= 0.4 else "mixed")


def truth_of(k, start: date, end: date) -> str:
    """Which injected event (if any) an event overlaps. Only used for scoring."""
    def overlaps(a, b):
        return start <= b + timedelta(days=1) and end >= a - timedelta(days=1)
    for a in INJECTED:
        s = SERIES_BY_ID[a["series"]]
        if (s["sub"], s["service"]) == k and overlaps(s2d(a["start"]), s2d(a["end"])):
            return a["id"]
    s = SERIES_BY_ID[DATA_ARTIFACT["series"]]
    if (s["sub"], s["service"]) == k and overlaps(s2d(DATA_ARTIFACT["spike_day"]), s2d(DATA_ARTIFACT["spike_day"])):
        return DATA_ARTIFACT["id"]
    s = SERIES_BY_ID[IMMATERIAL["series"]]
    if (s["sub"], s["service"]) == k and overlaps(s2d(IMMATERIAL["start"]), s2d(IMMATERIAL["end"])):
        return IMMATERIAL["id"]
    for c in CALENDAR:
        if c["type"] in ("planned-spike", "migration", "one-time") and c["sub"] == k[0] and \
                service_match(c["service"], k[1]):
            cs = s2d(c["start"])
            ce = s2d(c["end"]) if c["end"] else cs
            if overlaps(cs, ce):
                return c["id"]
    return "noise"


def triage(D: Data, k, ev: dict) -> tuple[str, str]:
    """Rules a FinOps analyst applies before paging an owner."""
    prov = D.provider_of[k]
    detected_on = ev["start"] + timedelta(days=LATENCY_DAYS[prov])
    for c in CALENDAR:            # 1. expected: on the planned-change calendar before detection
        if c["type"] not in ("planned-spike", "migration", "one-time"):
            continue
        if c["sub"] == k[0] and service_match(c["service"], k[1]):
            cs = s2d(c["start"])
            ce = s2d(c["end"]) if c["end"] else cs
            if ev["start"] <= ce and ev["end"] >= cs and s2d(c["added_on"]) <= detected_on:
                return "planned", c["id"]
    if len(ev["flags"]) == 1:     # 2. data artifact: a one-day spike right after a drop, two-day sum normal
        f = ev["flags"][0]
        prev = f["date"] - timedelta(days=1)
        x_prev = D.E[k].get(prev, 0.0)
        base_prev, _ = robust_baseline(D.E[k], prev, DEFAULT_RULE["weeks"])
        both = base_prev + f["baseline"]
        if base_prev > 0 and x_prev < 0.6 * base_prev and abs(x_prev + f["value"] - both) <= 0.2 * both:
            return "data artifact", "late rows"
    if ev["start"] > D.last - timedelta(days=LATENCY_DAYS[prov]):   # 3. too fresh to judge
        return "provisional", ""
    return "anomaly", ""


def detector_view(D: Data) -> dict:
    """What the detector watches: daily usage cost plus one-time purchases (marketplace and similar).
    Credits and commitment fees are excluded; commitment fees are already amortized into usage."""
    view = {}
    for k in set(D.keys) | set(D.OT.keys()):
        vals = defaultdict(float)
        for d, v in D.E.get(k, {}).items():
            vals[d] += v
        for d, v in D.OT.get(k, {}).items():
            vals[d] += v
        view[k] = vals
    return view


def compute_anomalies(D: Data, rule: dict = DEFAULT_RULE) -> dict:
    start = D.first + timedelta(weeks=8)
    events = []
    view = detector_view(D)
    for k in sorted(view, key=lambda k: (PROVIDER_ORDER.index(D.provider_of[k]), k)):
        for ev in group_events(detect_series(view[k], start, D.last, rule)):
            prov = D.provider_of[k]
            excess = sum(f["excess"] for f in ev["flags"])
            usage, rate, driver = attribute_event(D, k, ev, rule["weeks"])
            if any(D.OT.get(k, {}).get(f["date"], 0.0) for f in ev["flags"]):
                driver = "one-time"
            label, ref = triage(D, k, ev)
            ongoing = ev["end"] >= D.last - timedelta(days=2)
            impact = excess + (30 * ev["flags"][-1]["excess"] if ongoing else 0.0)
            sev = "Sev1" if impact >= 25000 else "Sev2" if impact >= 5000 else "Sev3"
            acct = ACCOUNT_MAP[k[0]]
            events.append({"key": k, "provider": prov, "start": ev["start"], "end": ev["end"],
                           "days": len(ev["flags"]), "excess": excess, "z": max(f["z"] for f in ev["flags"]),
                           "rel": max(f["rel"] for f in ev["flags"]), "driver": driver, "usage": usage,
                           "rate": rate, "label": label, "ref": ref, "ongoing": ongoing, "impact": impact,
                           "detected_on": ev["start"] + timedelta(days=LATENCY_DAYS[prov]), "severity": sev,
                           "owner": acct.get("owner", ""), "truth": truth_of(k, ev["start"], ev["end"]),
                           "flags": ev["flags"]})
    events.sort(key=lambda e: e["start"])
    real = {a["id"]: a for a in INJECTED}
    targets = [a for a in INJECTED if a["target"] == "detector"]
    labeled = [e for e in events if e["label"] == "anomaly"]
    tp = [e for e in labeled if e["truth"] in real]
    found = {e["truth"] for e in tp}
    raw_tp = [e for e in events if e["truth"] in real]
    mttd = {}
    for a in INJECTED:
        hits = [e for e in tp if e["truth"] == a["id"]]
        if hits:
            mttd[a["id"]] = (min(e["detected_on"] for e in hits) - s2d(a["start"])).days
    score = {"events": len(events), "labeled": len(labeled), "tp": len(tp), "fp": len(labeled) - len(tp),
             "raw_precision": len(raw_tp) / len(events) if events else 0.0,
             "precision": len(tp) / len(labeled) if labeled else 0.0,
             "recall": sum(1 for a in targets if a["id"] in found) / len(targets),
             "missed": [a["id"] for a in targets if a["id"] not in found],
             "found_other": [a["id"] for a in INJECTED if a["target"] != "detector" and a["id"] in found],
             "mttd": mttd}
    return {"rule": rule, "events": events, "score": score}


def compute_unit_cost_anomalies(D: Data, rule: dict = DEFAULT_RULE) -> list:
    """Same detector on cost per business unit (per conversation, per 1,000 transactions)."""
    out = []
    start = D.first + timedelta(weeks=8)
    for app, subs in UNIT_SCOPES.items():
        keys = [k for k in D.keys if k[0] in subs]
        unit, vol = {}, {}
        for d in daterange(D.first, D.last):
            v = D.drivers.get((app, d), 0.0)
            if v > 0:
                vol[d] = v
                unit[d] = sum(D.E[k].get(d, 0.0) for k in keys) / v
        flags = []
        for d in daterange(start, D.last):
            if d not in unit:
                continue
            med, sigma = robust_baseline(unit, d, rule["weeks"], floor=1e-9)
            ex = unit[d] - med
            if ex <= 0 or med <= 0:
                continue
            impact = ex * vol[d]
            if ex / sigma >= rule["z"] and ex / med >= rule["pct"] and impact >= rule["usd"]:
                flags.append({"date": d, "value": unit[d], "baseline": med, "excess": impact,
                              "z": ex / sigma, "rel": ex / med})
        for ev in group_events(flags):
            top = max(ev["flags"], key=lambda f: f["rel"])    # report one day consistently
            out.append({"app": app, "metric": DRIVERS[app]["metric"], "start": ev["start"], "end": ev["end"],
                        "days": len(ev["flags"]), "impact": sum(f["excess"] for f in ev["flags"]),
                        "baseline": top["baseline"], "peak": top["value"], "rel": top["rel"]})
    return out


def anomaly_cost_share(D: Data, events: list, month: str) -> tuple[float, float]:
    cost = sum(f["excess"] for e in events if e["label"] == "anomaly" for f in e["flags"] if ym(f["date"]) == month)
    total = D.month_total(month)
    return cost, cost / total if total else 0.0


def cmd_anomalies(D: Data, args):
    R = compute_anomalies(D)
    rule, sc = R["rule"], R["score"]
    section("Anomaly detection: daily EffectiveCost per sub-account x service")
    print(f"Rule: baseline = median of the same weekday over the previous {rule['weeks']} weeks; sigma = 1.4826 x MAD")
    print(f"(floored at 5% of the median). Flag a day when z >= {rule['z']}, the increase is >= {pct(rule['pct'], 0)} "
          f"AND >= {money(rule['usd'])}. Days merge into events across gaps of up to 2 days.")
    print("Triage: (1) planned if on the change calendar before detection; (2) data artifact if a one-day spike")
    print("follows a drop and the two days sum to normal; (3) provisional if newer than the provider's data latency.")
    print()
    rows = []
    for i, e in enumerate(R["events"], start=1):
        rows.append([i, f"{e['key'][0]} / {e['key'][1]}", str(e["start"]), str(e["end"]), e["days"],
                     money(e["excess"]), f"{min(e['z'], 999):.1f}",
                     "new" if e["rel"] == float("inf") else spct(e["rel"], 0), e["driver"],
                     e["label"] + (f" ({e['ref']})" if e["ref"] else ""), str(e["detected_on"]), e["severity"],
                     e["truth"]])
    print_table(["#", "Series", "Start", "End", "Days", "Excess", "Max z", "Max %", "Driver", "Triage",
                 "Detected", "Sev", "Truth"], rows, "rllllrrrlllll",
                title="Events (Truth = the injected ground truth, for scoring only):")
    print(f"Events flagged: {sc['events']}. Raw precision (before triage): {pct(sc['raw_precision'])}.")
    print(f"After triage: {sc['labeled']} labeled anomaly, {sc['tp']} true, {sc['fp']} false -> precision "
          f"{pct(sc['precision'])}.")
    print(f"Recall on detector-targeted anomalies: {pct(sc['recall'])}" +
          (f" (missed: {', '.join(sc['missed'])})" if sc["missed"] else "") + ".")
    others = [a for a in INJECTED if a["target"] != "detector"]
    for a in others:
        status = "also caught by the detector" if a["id"] in sc["found_other"] else "not caught by the detector"
        print(f"{a['id']} ({a['title']}) is meant for the {a['target']}: {status}.")
    print()
    rows = []
    for a in INJECTED:
        if a["id"] in sc["mttd"]:
            hit = [e for e in R["events"] if e["truth"] == a["id"] and e["label"] == "anomaly"][0]
            rows.append([a["id"], a["title"], a["start"], str(hit["detected_on"]), sc["mttd"][a["id"]],
                         money(sum(e["excess"] for e in R["events"] if e["truth"] == a["id"])), hit["driver"],
                         hit["owner"]])
    print_table(["Id", "Anomaly", "Started", "Detected", "Days", "Excess cost", "Driver", "Route to"], rows,
                "llllrrll", title="Time to detect (start of the anomaly to data available + flagged):")
    ue = compute_unit_cost_anomalies(D)
    rows = [[u["app"], f"cost per {u['metric'][:-1] if u['metric'].endswith('s') else u['metric']}",
             str(u["start"]), str(u["end"]), u["days"], f"{u['baseline']:.4f}", f"{u['peak']:.4f}",
             spct(u["rel"], 0), money(u["impact"])] for u in ue]
    print_table(["Application", "Unit cost", "Start", "End", "Days", "Baseline", "Peak", "Peak %", "Impact"], rows,
                "llllrrrrr", title="Unit-cost anomalies (cost per business unit; baseline and peak on the day of the "
                                   "largest increase; impact = excess x volume):")
    rows = []
    for rl in SWEEP_RULES:
        s = compute_anomalies(D, rl)["score"]
        rows.append([rl["name"], f"z>={rl['z']}, >={pct(rl['pct'], 0)}, >={money(rl['usd'])}", s["events"],
                     s["labeled"], s["tp"], s["fp"], pct(s["precision"]), pct(s["recall"]),
                     ", ".join(s["missed"]) or "-"])
    print_table(["Rule", "Thresholds", "Events", "Labeled", "TP", "FP", "Precision", "Recall", "Missed"], rows,
                "llrrrrrrl", title="Threshold sweep (precision and recall after triage):")
    rows = []
    for mo in month_list("2026-04", ym(D.last)):
        cost, share = anomaly_cost_share(D, R["events"], mo)
        band = "green" if share < 0.02 else "yellow" if share <= 0.07 else "red"
        rows.append([mo, money(cost), pct(share, 2), band])
    print_table(["Month", "Anomaly cost", "Anomaly cost %", "Band"], rows,
                title="Anomaly cost % = anomaly excess / total spend (FinOps Foundation bands <2% / 2-7% / >7%):")


# ===========================================================================
# 8. allocation
# ===========================================================================

APPS = TAG_STANDARD["allowed_values"]["application"]
# A fixed split agreed with the owning teams (used only to compare methods).
FIXED_SPLIT = {"payments-api": 0.40, "claims-analytics": 0.25, "customer-portal": 0.15, "ai-assistant": 0.10,
               "doc-intelligence": 0.05, "ml-research": 0.05}


def normalize_tags(tags: dict) -> dict:
    """Apply the alias table and the lowercase rule (used for allocation, not for compliance)."""
    out = {}
    for k, v in tags.items():
        k2 = TAG_STANDARD["key_aliases"].get(k, k).lower()
        v2 = str(v).lower()
        out[k2] = TAG_STANDARD["value_aliases"].get(v2, v2)
    return out


def tag_issues(tags: dict) -> list:
    """Violations of the tagging standard: missing keys, misspelled keys, wrong case, unknown values."""
    issues = []
    allowed = TAG_STANDARD["allowed_values"]
    for key in TAG_STANDARD["required_keys"]:
        if key in tags:
            v = tags[key]
            if v not in allowed[key]:
                issues.append(f"value case {key}={v}" if v.lower() in allowed[key]
                              else f"value not in dictionary {key}={v}")
        else:
            near = [t for t in tags if TAG_STANDARD["key_aliases"].get(t, t.lower()) == key]
            issues.append(f"key spelled '{near[0]}'" if near else f"missing {key}")
    return issues


def is_taggable(r) -> bool:
    """Usage charges on resources. Unused commitment, purchases, credits are not taggable."""
    return r["ChargeCategory"] == "Usage" and r["CommitmentDiscountStatus"] != "Unused"


def allocate_row(r):
    """(method, application, shared pool): hierarchy first, then tags, then the account default."""
    acct = ACCOUNT_MAP[r["SubAccountName"]]
    if acct["kind"] == "shared":
        return "shared", None, acct["pool"]
    if r["ChargeCategory"] == "Credit" and acct["kind"] == "single":
        return "credit", acct["application"], None          # credits follow the account that earned them
    app = normalize_tags(r["_tags"]).get("application")
    if app in APPS:
        return "tag", app, None
    if acct["kind"] == "single":
        return "account", acct["application"], None
    return "unallocated", None, None


def allocation_month(D: Data, month: str) -> dict:
    rows = D.rows_in(month)
    res = {"total": 0.0, "taggable": 0.0, "compliant": 0.0, "by_provider": defaultdict(lambda: [0.0, 0.0]),
           "issues": defaultdict(float), "method": defaultdict(float), "direct": defaultdict(float),
           "pools": defaultdict(float), "unallocated": defaultdict(float), "proxy": defaultdict(float)}
    for r in rows:
        c = r["EffectiveCost"]
        res["total"] += c
        if is_taggable(r):
            res["taggable"] += c
            res["by_provider"][r["ServiceProviderName"]][0] += c
            iss = tag_issues(r["_tags"])
            if not iss:
                res["compliant"] += c
                res["by_provider"][r["ServiceProviderName"]][1] += c
            else:
                label = "untagged (all required keys missing)" if not r["_tags"] else "; ".join(iss)
                res["issues"][(r["SubAccountName"], label)] += c
        method, app, pool = allocate_row(r)
        res["method"][method] += c
        if app:
            res["direct"][app] += c
            if r["ServiceCategory"] in ("Compute", "Networking"):
                res["proxy"][app] += r["ListCost"]
        if pool:
            res["pools"][pool] += c
        if method == "unallocated":
            res["unallocated"][(r["SubAccountName"], r["ServiceName"])] += c
    return res


def split_pool(amount: float, method: str, direct: dict, proxy: dict) -> dict:
    """Shared-cost split methods: even, proportional (to direct cost), fixed (agreed %), usage-driven."""
    apps = [a for a in direct if direct[a] > 0]
    if method == "even":
        return {a: amount / len(apps) for a in apps}
    if method == "proportional":
        tot = sum(direct[a] for a in apps)
        return {a: amount * direct[a] / tot for a in apps}
    if method == "fixed":
        tot = sum(FIXED_SPLIT.get(a, 0.0) for a in apps)
        return {a: amount * FIXED_SPLIT.get(a, 0.0) / tot for a in apps}
    tot = sum(proxy.get(a, 0.0) for a in apps)            # usage-driven: compute + network footprint
    return {a: amount * proxy.get(a, 0.0) / tot for a in apps}


def compute_allocation(D: Data, month: str) -> dict:
    res = allocation_month(D, month)
    trend = []
    for mo in month_list("2025-10", month):
        r = allocation_month(D, mo)
        unalloc = sum(r["unallocated"].values())
        trend.append((mo, r["compliant"] / r["taggable"], unalloc / r["total"], 1 - unalloc / r["total"]))
    res["trend"] = trend
    return res


def cmd_allocation(D: Data, args):
    R = compute_allocation(D, args.month)
    T = R["total"]
    section(f"Allocation for {args.month}: tags, hierarchy and shared costs (EffectiveCost)")
    comp = R["compliant"] / R["taggable"]
    unalloc = sum(R["unallocated"].values())
    print(f"Tagging Policy Compliance = compliant cost / taggable cost = {money(R['compliant'])} / "
          f"{money(R['taggable'])} = {pct(comp)} (first target > 90%)")
    print(f"Unallocated cost % = {money(unalloc)} / {money(T)} = {pct(unalloc / T, 2)}; allocated "
          f"{pct(1 - unalloc / T)} (FinOps Foundation maturity examples: >=70% Crawl, >=85% Walk, >90% Run)")
    print()
    rows = [[p, money(v[0]), money(v[1]), pct(v[1] / v[0]) if v[0] else "-"]
            for p, v in sorted(R["by_provider"].items(), key=lambda x: PROVIDER_ORDER.index(x[0]))]
    print_table(["Provider", "Taggable cost", "Compliant cost", "Compliance"], rows,
                title="Tag compliance by provider (strict: exact keys, lowercase, dictionary values):")
    rows = [[s, i, money(v), pct(v / R["taggable"])]
            for (s, i), v in sorted(R["issues"].items(), key=lambda x: -x[1])[:10]]
    print_table(["Sub-account", "Violation", "Cost affected", "% of taggable"], rows, "llrr",
                title="Top tag violations by cost (fix the expensive ones first):")
    labels = {"tag": "Direct: tag (after normalization)", "account": "Direct: account default (hierarchy)",
              "credit": "Credits (to the account's owner)", "shared": "Shared pools (split below)",
              "unallocated": "Unallocated"}
    rows = [[labels[m], money(R["method"][m]), pct(R["method"][m] / T)]
            for m in ("tag", "account", "credit", "shared", "unallocated") if R["method"].get(m)]
    print_table(["How the cost was allocated", "Cost", "Share"], rows, "lrr",
                title="Allocation waterfall (hierarchy first, then tags, then account defaults):")
    rows = [[f"{s} / {svc}", money(v), "multi-team account, no valid application tag"]
            for (s, svc), v in sorted(R["unallocated"].items(), key=lambda x: -x[1])]
    if rows:
        print_table(["Unallocated series", "Cost", "Why"], rows, "lrl", title="What is unallocated:")
    direct, proxy = R["direct"], R["proxy"]
    net = R["pools"].get("network", 0.0)
    methods = ["even", "proportional", "fixed", "usage-driven"]
    splits = {m: split_pool(net, m, direct, proxy) for m in methods}
    apps = sorted(direct, key=lambda a: -direct[a])
    rows = [[a, money(direct[a])] + [money(splits[m][a]) for m in methods] for a in apps]
    print_table(["Application", "Direct cost"] + [f"Network: {m}" for m in methods], rows,
                title=f"Network pool ({money(net)}) under four split methods:")
    final = {a: {"direct": direct[a]} for a in apps}
    pool_names = sorted(R["pools"])
    for p in pool_names:
        sp = split_pool(R["pools"][p], "proportional", direct, proxy)
        for a in apps:
            final[a][p] = sp[a]
    rows = []
    for a in apps:
        loaded = sum(final[a].values())
        rows.append([a, money(final[a]["direct"])] + [money(final[a][p]) for p in pool_names]
                    + [money(loaded), pct(loaded / T)])
    rows.append(["unallocated", money(unalloc)] + ["" for _ in pool_names] + [money(unalloc), pct(unalloc / T)])
    print_table(["Application", "Direct"] + [f"+ {p}" for p in pool_names] + ["Fully loaded", "% of total"], rows,
                title="Showback with shared pools split proportionally to direct cost:")
    rows = [[mo, pct(c), pct(u, 2), pct(a)] for mo, c, u, a in R["trend"]]
    print_table(["Month", "Tag compliance", "Unallocated", "Allocated"], rows,
                title="Trend (tag remediation: ml-sandbox Jan 15, data platform Mar 15, CRM dev May 1, CRM prod Jun 1):")


# ===========================================================================
# 9. commitments
# ===========================================================================

def sp_sizing(D: Data, as_of: date) -> dict:
    """Size the Savings Plan renewal from the projected usage floor after the decommission.

    Eligible usage is measured in Savings Plan dollars (contracted cost x (1 - discount)). A commitment
    of X per day costs X whether used or not, and saves disc/(1-disc) per covered dollar. The marginal
    dollar of commitment pays off only if usage exceeds it at least (1 - disc) of the time, so the
    break-even utilization is 1 - disc and the expected-value optimum is the disc-quantile of daily
    usage. Daily data hides hourly troughs; with hourly data the same method gives a lower number."""
    disc = SP["discount"]
    plan = plan_dates("actual")
    src_key = (MIGRATION["source_sub"], "Amazon EC2")
    hist = [sum(D.C[k].get(as_of - timedelta(days=i), 0.0) for k in SP_KEYS) * (1 - disc) for i in range(60)]
    sp_end = s2d(SP["end"])
    fits = {k: fit_series(D.C.get(k, {}), as_of, D.first) for k in SP_KEYS}

    def eligible(dd, without_source=True):
        tot = 0.0
        for k, f in fits.items():
            if not f or (without_source and k == src_key and dd >= plan["decommission_compute"]):
                continue
            tot += predict(f, dd)
        return tot * (1 - disc)

    renewal_year = list(daterange(sp_end + timedelta(days=1), sp_end + timedelta(days=365)))
    proj = [eligible(dd) for dd in renewal_year]
    post_days = list(daterange(max(plan["decommission_compute"], as_of + timedelta(days=1)), sp_end))
    post = [eligible(dd) for dd in post_days]
    C = SP["hourly_commitment"] * 24
    used = sum(min(v, C) for v in post)
    post_util = used / (C * len(post)) if post else 1.0
    post_waste_month = (C * len(post) - used) / len(post) * DAYS_PER_MONTH if post else 0.0

    def evaluate(hourly: float) -> dict:
        X = hourly * 24
        covered = sum(min(v, X) for v in proj)
        commit = X * len(proj)
        gross = covered * disc / (1 - disc)
        return {"hourly": hourly, "util": covered / commit, "coverage": covered / sum(proj), "gross": gross,
                "waste": commit - covered, "net": gross - (commit - covered)}

    grid = [evaluate(h) for h in range(100, 405, 5)]
    best = max(grid, key=lambda g: g["net"])
    # The net-savings curve is flat near the optimum, so take the smallest commitment that earns at
    # least 95% of the best net savings: almost the same value, much less exposure to usage falling.
    plateau = min((g for g in grid if g["net"] >= 0.95 * best["net"]), key=lambda g: g["hourly"])
    p_floor = percentile(proj, 5) / 24
    p_break = percentile(proj, disc * 100) / 24
    conservative = math.floor(p_floor / 5) * 5
    options = [("Floor: P5 of daily usage", evaluate(conservative)),
               ("Recommended: 95% of best net, least exposure", plateau),
               ("Expected-value optimum on the $5 grid", best),
               ("Renew as is", evaluate(SP["hourly_commitment"])),
               ("Oversized: 120% of the optimum", evaluate(5 * round(best["hourly"] * 1.2 / 5)))]
    return {"hist_min": min(hist) / 24, "hist_p5": percentile(hist, 5) / 24, "hist_median": median(hist) / 24,
            "proj_p5": p_floor, "proj_p30": p_break, "proj_median": median(proj) / 24,
            "recommended_hourly": float(plateau["hourly"]), "optimum_hourly": float(best["hourly"]),
            "conservative_hourly": float(conservative), "recommended": plateau, "optimum": best,
            "options": options, "post_decom_util": post_util, "post_decom_waste_month": post_waste_month,
            "breakeven_util": 1 - disc, "disc": disc}


def ri_sizing(D: Data, as_of: date) -> dict:
    """Size a new VM reservation from the floor of concurrent VMs (P10 of daily VM-hours / 24)."""
    k = ("az-crm-prod", "Virtual Machines")
    hours = [D.Q[k].get(as_of - timedelta(days=i), 0.0) for i in range(30)]
    p10 = percentile([h / 24 for h in hours], 10)
    qty = int(p10 // 10 * 10)
    price = SERIES_BY_ID["az-crm-vm"]["price"]
    disc = COMMIT_BY_ID["ri-crm-vm-2025"]["discount"]
    covered = sum(min(h, qty * 24) for h in hours)
    unused = qty * 24 * len(hours) - covered
    util = covered / (qty * 24 * len(hours)) if qty else 0.0
    # net of the hours paid for and not used (at the reserved rate)
    monthly = (covered * price * disc - unused * price * (1 - disc)) / len(hours) * DAYS_PER_MONTH
    return {"instances_p10": p10, "qty": qty, "util": util, "monthly_saving": monthly, "disc": disc,
            "breakeven_util": 1 - disc}


def compute_commitments(D: Data, month: str) -> dict:
    ms, me = month_bounds(month)
    rows = D.rows_in(month)
    out = []
    for c in COMMITMENTS:
        if s2d(c["end"]) < ms - timedelta(days=31) or s2d(c["start"]) > me:
            continue
        cid = c["id"]
        used = sum(r["EffectiveCost"] for r in rows if r["CommitmentDiscountId"] == cid
                   and r["CommitmentDiscountStatus"] == "Used")
        unused = sum(r["EffectiveCost"] for r in rows if r["CommitmentDiscountId"] == cid
                     and r["CommitmentDiscountStatus"] == "Unused")
        cov_contracted = sum(r["ContractedCost"] for r in rows if r["CommitmentDiscountId"] == cid
                             and r["CommitmentDiscountStatus"] == "Used")
        fee = sum(r["BilledCost"] for r in rows if r["CommitmentDiscountId"] == cid and r["ChargeCategory"] == "Purchase")
        if c["type"] == "Savings Plan":
            elig = sum(r["ContractedCost"] for r in rows if r["ChargeCategory"] == "Usage"
                       and (r["SubAccountName"], r["ServiceName"]) in SP_KEYS)
            coverage = cov_contracted / elig if elig else 0.0
            lost = 0.0
        else:
            key = (c["sub"], c["service"])
            usage_rows = [r for r in rows if (r["SubAccountName"], r["ServiceName"]) == key
                          and r["ChargeCategory"] == "Usage" and r["CommitmentDiscountStatus"] != "Unused"]
            hrs = sum(r["PricingQuantity"] for r in usage_rows)
            cov_h = sum(r["PricingQuantity"] for r in usage_rows if r["CommitmentDiscountId"] == cid)
            coverage = cov_h / hrs if hrs else 0.0
            elig = sum(r["ContractedCost"] for r in usage_rows)
            lost = 0.0
            if s2d(c["end"]) < ms:
                price = sum(r["ContractedCost"] for r in usage_rows) / hrs if hrs else 0.0
                for dd in daterange(ms, me):
                    lost += min(D.Q[key].get(dd, 0.0), c["hours_per_day"]) * price * c["discount"]
        commit_cost = used + unused
        out.append({"c": c, "used": used, "unused": unused, "commit_cost": commit_cost, "fee": fee,
                    "util": used / commit_cost if commit_cost else 0.0, "coverage": coverage,
                    "waste": unused / commit_cost if commit_cost else 0.0, "savings": cov_contracted - used,
                    "eligible": elig, "lost": lost,
                    "status": "active" if s2d(c["end"]) >= me else f"expired {c['end']}"})
    esr = {}
    for prov in PROVIDER_ORDER + ["All"]:
        us = [r for r in rows if r["ChargeCategory"] == "Usage" and (prov == "All" or r["ServiceProviderName"] == prov)]
        L = sum(r["ListCost"] for r in us)
        Cc = sum(r["ContractedCost"] for r in us)
        E = sum(r["EffectiveCost"] for r in us)
        cov_sav = sum(r["ContractedCost"] - r["EffectiveCost"] for r in us if r["CommitmentDiscountStatus"] == "Used")
        unused = sum(r["EffectiveCost"] for r in us if r["CommitmentDiscountStatus"] == "Unused")
        esr[prov] = {"L": L, "C": Cc, "E": E, "focus": (Cc - E) / Cc if Cc else 0.0,
                     "foundation": (cov_sav - unused) / L if L else 0.0, "vendor": (L - E) / L if L else 0.0}
    pool = [r for r in rows if r["ChargeCategory"] == "Usage" and ((r["SubAccountName"], r["ServiceName"]) in SP_KEYS
            or r["CommitmentDiscountId"] == SP["id"])]
    pc = sum(r["ContractedCost"] for r in pool)
    pe = sum(r["EffectiveCost"] for r in pool)
    return {"month": month, "items": out, "esr": esr, "sp_pool_esr": (pc - pe) / pc if pc else 0.0,
            "sizing": sp_sizing(D, me), "ri": ri_sizing(D, me)}


def cmd_commitments(D: Data, args):
    R = compute_commitments(D, args.month)
    section(f"Commitments for {args.month}: coverage, utilization, waste, ESR and the renewal decisions")
    rows = []
    for it in R["items"]:
        c = it["c"]
        live = it["commit_cost"] > 0          # an expired commitment has no utilization or coverage
        rows.append([c["id"], c["provider"], f"{c['type']} ({c['category']})", f"{c['start']}..{c['end']}",
                     money(it["fee"]), money(it["commit_cost"]), money(it["used"]), money(it["unused"]),
                     pct(it["util"]) if live else "n/a", pct(it["coverage"]) if live else "n/a",
                     pct(it["waste"]) if live else "n/a", money(it["savings"]), it["status"]])
    print_table(["Commitment", "Provider", "Type", "Term", "Billed fee", "Amortized", "Used", "Unused",
                 "Utilization", "Coverage", "Waste %", "Savings", "Status"], rows, "llll" + "r" * 8 + "l",
                title="Inventory and month metrics (utilization = used / amortized commitment; coverage = covered / "
                      "eligible usage):")
    for it in R["items"]:
        if it["lost"]:
            print(f"{it['c']['id']} expired on {it['c']['end']}: the same hours at on-demand rates cost "
                  f"{money(it['lost'])} more in {args.month} (rate, not usage).")
    print()
    rows = []
    for prov, e in R["esr"].items():
        rows.append([prov, money(e["L"]), money(e["C"]), money(e["E"]), pct(e["focus"]), pct(e["foundation"]),
                     pct(e["vendor"])])
    print_table(["Provider", "ListCost", "ContractedCost", "EffectiveCost", "ESR (FOCUS)", "Option 1 at list",
                 "Option 2 at list"], rows,
                title="Effective savings rate, three definitions (usage rows incl. unused commitment):")
    print("  ESR (FOCUS)      = (ContractedCost - EffectiveCost) / ContractedCost: commitment savings net of waste,")
    print("                     against contracted prices, so negotiated discounts are left out.")
    print("  Option 1 at list = FinOps Foundation option 1, (commitment savings - unused commitment) / on-demand")
    print("                     equivalent, with the on-demand equivalent at list prices.")
    print("  Option 2 at list = FinOps Foundation option 2, 1 - EffectiveCost / ListCost: negotiated and commitment")
    print("                     discounts together.")
    print(f"  AWS Savings Plan pool (eligible EC2 + unused): ESR {pct(R['sp_pool_esr'])}.")
    print()
    sz = R["sizing"]
    print(f"Savings Plan renewal ({SP['id']}, ${SP['hourly_commitment']:.0f}/hour, expires {SP['end']}):")
    print(f"  Eligible usage in SP dollars, last 60 days: min ${sz['hist_min']:.0f}/h, P5 ${sz['hist_p5']:.0f}/h, "
          f"median ${sz['hist_median']:.0f}/h (includes the data platform).")
    print(f"  Projected for the renewal year without the data platform: P5 ${sz['proj_p5']:.0f}/h, "
          f"P30 ${sz['proj_p30']:.0f}/h, median ${sz['proj_median']:.0f}/h.")
    print(f"  Current plan after the decommission on {MIGRATION['actual']['decommission_compute']}: utilization "
          f"{pct(sz['post_decom_util'])}, about {money(sz['post_decom_waste_month'])}/month unused until expiry.")
    print(f"  Break-even utilization = 1 - discount = {pct(sz['breakeven_util'], 0)}.")
    print()
    rows = [[name, f"${o['hourly']:.0f}", pct(o["util"]), pct(o["coverage"]), money(o["gross"]), money(o["waste"]),
             money(o["net"])] for name, o in sz["options"]]
    print_table(["Option", "Hourly", "Utilization", "Coverage", "Gross savings/yr", "Unused/yr", "Net savings/yr"],
                rows, "lrrrrrr", title="Sensitivity for the renewal year (1-year view, discount "
                                       f"{pct(sz['disc'], 0)}):")
    ri = R["ri"]
    print(f"Azure VM reservation (expired): P10 of concurrent VMs over 30 days = {ri['instances_p10']:.0f}; "
          f"recommend {ri['qty']} instances, expected utilization {pct(ri['util'])}, net saving about "
          f"{money(ri['monthly_saving'])}/month at {pct(ri['disc'], 0)} (break-even utilization "
          f"{pct(ri['breakeven_util'], 0)}).")
    print()


# ===========================================================================
# 10. savings
# ===========================================================================

def counterfactual(D: Data, ini: dict, method: str, k, vals: dict, days: list) -> dict:
    """What series k would have cost each day without the initiative, from the 28 days before it."""
    start = s2d(ini["start"])
    pre = [start - timedelta(days=i) for i in range(1, 29)]
    if method == "unit":         # pre-change cost per business unit x actual volume
        unit = sum(vals.get(d, 0.0) for d in pre) / sum(D.drivers[(ini["driver"], d)] for d in pre)
        return {d: unit * D.drivers[(ini["driver"], d)] for d in days}
    if method == "trend":        # the pre-change model projected forward
        fit = fit_series(vals, start - timedelta(days=1), D.first, per_month=k in D.per_month)
        return {d: predict(fit, d) for d in days}
    qk = k
    if method == "ratio":        # license cost per VM hour x actual VM hours
        b = SERIES_BY_ID[ini["ratio_of"]]
        qk = (b["sub"], b["service"])
    r0 = sum(vals.get(d, 0.0) for d in pre) / sum(D.Q[qk].get(d, 0.0) for d in pre)
    return {d: r0 * D.Q[qk].get(d, 0.0) for d in days}   # rate: pre-change cost per unit x quantity


def realized_by_day(D: Data, ini: dict, method: str, days: list) -> dict:
    """Realized saving per day for the whole company.

    Series on the shared Savings Plan are valued through the plan: while it is fully used, removing a
    dollar of covered usage saves a dollar at contracted (on-demand) rates, because the plan's
    coverage moves to other accounts; once usage falls below the plan, removing usage saves nothing.
    So those series are measured on ContractedCost through sp_pool_cost, not on their own amortized
    cost, which would miss the coverage that moved. Other series are measured on EffectiveCost."""
    keys = [(SERIES_BY_ID[s]["sub"], SERIES_BY_ID[s]["service"]) for s in ini["series"]]
    out = {d: 0.0 for d in days}
    sp_cf, sp_act = defaultdict(float), defaultdict(float)
    for k in keys:
        on_sp = k in SP_KEYS
        vals = D.C[k] if on_sp else D.E[k]
        cf = counterfactual(D, ini, method, k, vals, days)
        for d in days:
            if on_sp:
                sp_cf[d] += cf[d]
                sp_act[d] += vals.get(d, 0.0)
            else:
                out[d] += cf[d] - vals.get(d, 0.0)
    if sp_act:
        disc, sp_start, sp_end = SP["discount"], s2d(SP["start"]), s2d(SP["end"])
        for d in days:
            commit = SP["hourly_commitment"] * 24 if sp_start <= d <= sp_end else 0.0
            other = sum(D.C[k].get(d, 0.0) for k in SP_KEYS) - sp_act[d]
            out[d] += (sp_pool_cost(other + sp_cf[d], commit, disc)
                       - sp_pool_cost(other + sp_act[d], commit, disc))
    return out


def compute_savings(D: Data, last_month: str) -> dict:
    """Realized savings = counterfactual (what it would have cost) - actual, per initiative and month,
    with the method registered before the change, a trend-method cross-check, and (for scoring only)
    the true saving from ground_truth.json."""
    out = []
    _, last_day = month_bounds(last_month)
    last_day = min(last_day, D.last)
    for ini in INITIATIVES:
        start = s2d(ini["start"])
        all_days = list(daterange(start, last_day))
        main = realized_by_day(D, ini, ini["method"], all_days)
        trend = main if ini["method"] == "trend" else realized_by_day(D, ini, "trend", all_days)
        truth = D.true_savings.get(ini["id"], {})
        months = []
        for mo in month_list(ym(start), ym(last_day)):
            ms, me = month_bounds(mo)
            days = list(daterange(max(ms, start), min(me, last_day)))
            projected = ini["projected_monthly"] * len(days) / days_in_month(ms.year, ms.month)
            months.append({"month": mo, "days": len(days), "projected": projected,
                           "realized": sum(main[d] for d in days), "realized_trend": sum(trend[d] for d in days),
                           "truth": truth.get(mo)})
        proj = sum(m["projected"] for m in months)
        real = sum(m["realized"] for m in months)
        real_trend = sum(m["realized_trend"] for m in months)
        true_total = (sum(m["truth"] for m in months)
                      if months and all(m["truth"] is not None for m in months) else None)
        full = [m for m in months if m["days"] == days_in_month(*ym_parse(m["month"]))]
        peak = max((m["realized"] for m in full), default=0.0)
        last = full[-1]["realized"] if full else 0.0
        rate = real / proj if proj else 0.0
        status = "on track" if rate >= 0.9 else "partial" if rate >= 0.6 else "at risk"
        decaying = bool(full) and peak > 0 and last < 0.75 * peak
        out.append({"ini": ini, "months": months, "projected": proj, "realized": real, "rate": rate,
                    "realized_trend": real_trend, "truth": true_total,
                    "status": status + (", decaying" if decaying else ""), "run_rate": last,
                    "decaying": decaying, "peak": peak})
    year = last_month[:4]
    ytd_proj = sum(m["projected"] for o in out for m in o["months"] if m["month"].startswith(year))
    ytd_real = sum(m["realized"] for o in out for m in o["months"] if m["month"].startswith(year))
    pipeline = [{"p": p, "expected": p["monthly"] * p["probability"]} for p in PIPELINE]
    return {"items": out, "ytd_projected": ytd_proj, "ytd_realized": ytd_real,
            "run_rate": sum(o["run_rate"] for o in out), "pipeline": pipeline,
            "pipeline_monthly": sum(p["p"]["monthly"] for p in pipeline),
            "pipeline_expected": sum(p["expected"] for p in pipeline)}


def cmd_savings(D: Data, args):
    R = compute_savings(D, args.month)
    section(f"Savings tracker through {args.month}: projected vs realized, for the whole company")
    rows = []
    has_truth = all(o["truth"] is not None for o in R["items"])
    for o in R["items"]:
        i = o["ini"]
        rows.append([i["id"], i["name"][:56], i["start"], i["method"], money(o["projected"]), money(o["realized"]),
                     pct(o["rate"], 0), money(o["realized_trend"]), money(o["run_rate"]), o["status"]]
                    + ([money(o["truth"])] if has_truth else []))
    rows.append(["Total", "", "", "", money(sum(o["projected"] for o in R["items"])),
                 money(sum(o["realized"] for o in R["items"])),
                 pct(sum(o["realized"] for o in R["items"]) / sum(o["projected"] for o in R["items"]), 0),
                 money(sum(o["realized_trend"] for o in R["items"])), money(R["run_rate"]), ""]
                + ([money(sum(o["truth"] for o in R["items"]))] if has_truth else []))
    print_table(["Id", "Initiative", "Start", "Method", "Projected", "Realized", "Rate", "Trend check", "Last month",
                 "Status"] + (["Truth"] if has_truth else []), rows, "llllrrrrrlr",
                title="Implemented initiatives (since each start date; 'Trend check' = realized by the trend method; "
                      "Truth = from the ground truth, for scoring only):")
    months = month_list("2026-02", args.month)
    rows = []
    for o in R["items"]:
        mm = {m["month"]: m for m in o["months"]}
        rows.append([o["ini"]["id"]] + [f"{kmoney(mm[mo]['realized'])}/{kmoney(mm[mo]['projected'])}" if mo in mm
                                        else "" for mo in months])
    print_table(["Id"] + months, rows, title="Realized / projected by month (watch for decay):")
    print(f"Year to date {args.month[:4]}: realized {money(R['ytd_realized'])} of {money(R['ytd_projected'])} projected "
          f"({pct(R['ytd_realized'] / R['ytd_projected'], 0)}). Current monthly run-rate {money(R['run_rate'])}.")
    print("INIT-02's EC2 is on the shared Savings Plan, so it is valued at contracted rates through the plan: the")
    print("coverage it frees moves to other accounts. INIT-04 is measured on the license meter (license cost per")
    print("VM hour), so the reservation expiry on the compute meter in September does not contaminate it.")
    print()
    rows = [[x["p"]["id"], x["p"]["name"][:60], x["p"]["start"], money(x["p"]["monthly"]),
             pct(x["p"]["probability"], 0), money(x["expected"]), x["p"]["owner"]] for x in R["pipeline"]]
    rows.append(["Total", "", "", money(R["pipeline_monthly"]), "", money(R["pipeline_expected"]), ""])
    print_table(["Id", "Opportunity", "Start", "Monthly", "Probability", "Expected", "Owner"], rows, "lllrrrl",
                title="Pipeline (enters the forecast at monthly x probability from its start date):")


# ===========================================================================
# 11. summary
# ===========================================================================

def cmd_summary(D: Data, args):
    month = args.month
    V = compute_variance(D, month)
    F = compute_forecast(D)
    sav = compute_savings(D, month)
    A = compute_anomalies(D)
    AL = compute_allocation(D, month)
    CM = compute_commitments(D, month)
    B, Fc, Ac = V["budget"], V["forecast"], V["actual"]
    y, m = ym_parse(month)
    mname = date(y, m, 1).strftime("%B %Y")
    one_time = V["one_time"][0]
    credits = V["credits"][0]
    line = lambda ln: V["a_line"].get(ln, 0.0) - V["budget_by_line"].get(ln, 0.0)
    claims_gap = line("claims-analytics") - credits
    ai_gap = line("ai-assistant")
    expired = [it for it in CM["items"] if it["lost"]]
    expiry_cost = sum(it["lost"] for it in expired)
    other_gap = (Ac - B) - one_time - credits - claims_gap - ai_gap - expiry_cost
    fy = F["fy"]
    fcm = F["fc"]
    sz = F["sizing"]
    ri = CM["ri"]
    next3 = fcm["months"][:3]
    m1, w1, _ = error_stats(F["backtest"], "drivers", 1)
    run_rate = sav["run_rate"]
    decaying = [o for o in sav["items"] if o["decaying"]]
    billed = D.items[month]["billed"]
    purchases = D.items[month]["commitment_purchases"]
    unalloc = sum(AL["unallocated"].values())
    anomalies = [e for e in A["events"] if e["label"] == "anomaly" and e["start"] >= month_bounds(month)[0] - timedelta(days=45)]
    print(f"# Cloud cost summary: {mname}")
    print()
    print(f"*Business-unit cloud spend on AWS, Microsoft Azure and Google Cloud. Amortized cost (FOCUS EffectiveCost) "
          f"by charge date; data through {D.last}. All figures USD.*")
    print()
    print("## The three numbers")
    print()
    bt_sep = [r for r in F["backtest"] if r["h"] == 1 and r["month"] == month]
    dec = s2d(MIGRATION["actual"]["decommission_compute"])
    dec_txt = f"{dec.day} {dec.strftime('%B')}"
    offs = [f"the claims-analytics migration started two months earlier than the budget assumed "
            f"({skmoney(claims_gap)} until AWS is switched off on {dec_txt})"]
    if one_time:
        offs.append(f"a one-time marketplace renewal ({skmoney(one_time)})")
    if expired:
        offs.append(f"a VM reservation that lapsed on {dtxt(expired[0]['c']['end'])} ({skmoney(expiry_cost)})")
    offs_txt = offs[0] if len(offs) == 1 else ", ".join(offs[:-1]) + " and " + offs[-1]
    print(f"1. **{date(y, m, 1).strftime('%B')} cost {kmoney(Ac)}: {kmoney(Ac - B)} ({spct(Ac / B - 1, 0)}) over budget "
          f"and {kmoney(Ac - Fc)} ({spct(Ac / Fc - 1)}) over our forecast.** Most of the budget gap is timing and "
          f"one-offs: {offs_txt}. The recurring overrun is AI assistant growth ({skmoney(ai_gap)}).")
    miss_txt = "."
    if bt_sep:
        miss = bt_sep[0]["actual"] - bt_sep[0]["drivers"]
        miss_txt = (f"; in {date(y, m, 1).strftime('%B')} it missed by {pct(abs(miss) / bt_sep[0]['actual'])} "
                    f"({skmoney(miss)})")
        if expiry_cost:
            miss_txt += f", of which the lapsed reservation was {kmoney(expiry_cost)}"
        if one_time:
            miss_txt += f", and the {kmoney(one_time)} one-time renewal came on top"
        miss_txt += ("." if not (expiry_cost or one_time) else
                     ". Neither was on the change calendar." if expiry_cost and one_time else
                     ". It was not on the change calendar.")
    print(f"2. **Full-year {fy['year']} outlook {kmoney(fy['outlook'])} against a {kmoney(fy['budget'])} budget: "
          f"{skmoney(fy['outlook'] - fy['budget'])} ({spct(fy['outlook'] / fy['budget'] - 1)}).** The outlook includes "
          f"the AWS decommission on {dec_txt}, the end of the migration credits and the savings pipeline at its "
          f"probability. One month ahead, the forecast of recurring usage has been within {pct(m1)} on average "
          f"over six months (WAPE {pct(w1)})" + miss_txt)
    print(f"3. **Savings now run at {kmoney(run_rate)} a month; {kmoney(sav['ytd_realized'])} realized this year "
          f"({pct(sav['ytd_realized'] / sav['ytd_projected'], 0)} of plan).** Another "
          f"{kmoney(sav['pipeline_monthly'])} a month is identified ({kmoney(sav['pipeline_expected'])} "
          f"probability-weighted); two decisions this month unlock {kmoney(ri['monthly_saving'] + PIPELINE[1]['monthly'])} "
          f"of it.")
    print()
    print("## What drove the gap to budget")
    print()
    rows = [["Claims-analytics migration ahead of plan (timing)", claims_gap,
             "Google Cloud build-out began 1 July, not 1 September; both sides run until " + dec_txt],
            ["One-time marketplace renewal", one_time, "Annual SIEM subscription; not in the forecast"],
            ["Azure VM reservation lapsed", expiry_cost, "Same VM hours at on-demand rates (rate, not usage)"],
            ["AI assistant growth", ai_gap, "Conversations up about 6% a month; budget assumed 3%"],
            ["Migration credits", credits, "Google Cloud migration credits"],
            ["Other (net)", other_gap, "Organic growth net of savings above the 3% target"]]
    rows = [[n, smoney(v), t] for n, v, t in rows if abs(v) >= 0.5]
    rows.append(["**Total**", f"**{smoney(Ac - B)}**", f"Budget {money(B)}; actual {money(Ac)}"])
    print(md_table(["Driver", "vs budget", "Explanation"], rows, "lrl"))
    print()
    print("## Outlook")
    print()
    rows = [[mo, money(fcm["comp"][mo]["final"]), f"{kmoney(F['ranges'][mo][0])} to {kmoney(F['ranges'][mo][1])}",
             money(sum(v for (bm, _, _), v in D.budget.items() if bm == mo)) if mo.startswith(fy["year"]) else "n/a"]
            for mo in next3]
    print(md_table(["Month", "Forecast", "~80% range", "Budget"], rows, "lrrr"))
    print()
    print("## Risks")
    print()
    print(f"- **Savings Plan after the AWS decommission.** From {dec_txt} until the plan expires on {dtxt(SP['end'])}, "
          f"utilization falls to about {pct(sz['post_decom_util'], 0)} (about {kmoney(sz['post_decom_waste_month'])} "
          f"a month unused). The renewal must be sized to usage without the data platform.")
    ai_fit = fcm["fits"].get(("az-ai-assistant-prod", "Azure OpenAI"))
    if ai_fit:
        print(f"- **AI assistant spend grows about {pct(ai_fit['g'], 0)} a month.** A prompt change in August raised "
              f"cost per conversation by about 70% for nine days before it was reverted; there is no unit-cost "
              f"guardrail yet.")
    if decaying:
        print(f"- **Savings decay.** The non-production schedule ({decaying[0]['ini']['id']}) saves "
              f"{kmoney(decaying[0]['run_rate'])} a month against {kmoney(decaying[0]['peak'])} at its peak: instances "
              f"opted out in July were never re-enrolled.")
    if credits and month == max(MIGRATION["credits"]):
        print(f"- **Credits end.** The {kmoney(-credits)} monthly Google Cloud migration credit stopped after "
              f"{date(y, m, 1).strftime('%B')}.")
    print()
    print("## Decisions and actions requested")
    print()
    rec = sz["recommended"]
    rows = [[f"Approve a 1-year reservation for {ri['qty']} CRM VMs", kmoney(ri["monthly_saving"]) + "/month",
             f"breaks even at {pct(ri['breakeven_util'], 0)} utilization; expected {pct(ri['util'], 0)}",
             "team-crm, FinOps", "this week"],
            ["Re-enroll non-production instances in the schedule", kmoney(PIPELINE[1]["monthly"]) + "/month",
             "opt-outs since July", "team-payments", "15 October"],
            [f"Renew the Compute Savings Plan at about ${rec['hourly']:.0f}/hour (today ${SP['hourly_commitment']:.0f})",
             kmoney(rec["net"]) + "/year net vs on-demand",
             f"usage without the data platform; {pct(rec['util'], 0)} expected utilization", "FinOps, Finance",
             "before " + s2d(SP["end"]).strftime("%d %B %Y").lstrip("0")],
            ["Set a cost-per-conversation guardrail and alert for the AI assistant", "risk control",
             "unit-cost anomaly in August", "team-ai", "next review"]]
    print(md_table(["Decision or action", "Value", "Basis", "Owner", "By"], rows, "lrlll"))
    print()
    print("## Method and reconciliation")
    print()
    amort_commit = sum(r["EffectiveCost"] for r in D.rows_in(month)
                       if r["ChargeCategory"] == "Usage" and r["CommitmentDiscountId"])
    print("- Amortized cost (EffectiveCost) by charge date: usage, one-time purchases and credits. Budget lines map "
          "accounts to owning teams. Forecast: per-series weekday profile, robust level and damped trend, plus "
          "drivers (migration, commitments, known items, probability-weighted savings).")
    print(f"- Reconciliation with the central IT FinOps report, which uses invoice (billed) cost: amortized "
          f"{money(Ac)} - commitment cost amortized into usage {money(amort_commit)} + commitment fees billed "
          f"{money(purchases)} = billed {money(billed)}."
          + (f" If Finance books the {kmoney(one_time)} annual subscription as a prepaid expense, the ledger shows "
             f"{kmoney(one_time / 12)} a month instead." if one_time else "")
          + " Any other difference should come from scope (which accounts) or cut-off (charge period vs billing "
            "period); both are agreed in writing with the central team.")
    print(f"- Data quality: tag compliance {pct(AL['compliant'] / AL['taggable'], 0)}; unallocated "
          f"{pct(unalloc / AL['total'], 1)} of cost; {len(anomalies)} anomalies opened in the last 45 days, "
          f"each routed to its owner.")


# ===========================================================================
# 12. Command line
# ===========================================================================

def main(argv=None):
    p = argparse.ArgumentParser(description="FinOps analyst lab: synthetic multi-cloud FOCUS-like data and analyses.")
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate", help="write the synthetic data set")
    g.add_argument("--out", default="data", help="output directory (default: data)")
    g.add_argument("--seed", type=int, default=42, help="random seed (default: 42)")
    for name, helptext in [("forecast", "12-month forecast with backtest"),
                           ("variance", "budget vs forecast vs actual with a bridge"),
                           ("anomalies", "anomaly detection scored against ground truth"),
                           ("allocation", "tag compliance, unallocated cost, shared-cost split"),
                           ("commitments", "coverage, utilization, ESR, sizing"),
                           ("savings", "projected vs realized savings"),
                           ("summary", "one-page Markdown executive summary")]:
        sp = sub.add_parser(name, help=helptext)
        sp.add_argument("--data", default="data", help="data directory written by generate (default: data)")
        sp.add_argument("--month", default="2026-09", help="month to analyze, YYYY-MM (default: 2026-09)")
    args = p.parse_args(argv)
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)   # exit quietly when piped into head or less
    if args.cmd == "generate":
        generate(args.out, args.seed)
        return
    if not os.path.exists(os.path.join(args.data, "focus_costs.csv")):
        sys.exit(f"No data in {args.data}/. Run: python3 finops_lab.py generate --out {args.data}")
    D = Data(args.data)
    {"forecast": cmd_forecast, "variance": cmd_variance, "anomalies": cmd_anomalies, "allocation": cmd_allocation,
     "commitments": cmd_commitments, "savings": cmd_savings, "summary": cmd_summary}[args.cmd](D, args)


if __name__ == "__main__":
    main()
