#!/usr/bin/env python3
"""Application tracker for the job-search workspace (job-agent-kit).

Python 3.10+, standard library only. One CSV row per posting; this file is the
single source of pipeline state. Run from ~/job-search:

  .venv/bin/python scripts/tracker.py add --id li-4012345678 --platform linkedin \
      --company "Example AI" --role "Forward Deployed Engineer" \
      --url https://www.linkedin.com/jobs/view/4012345678/ --fit-score 82 --status screened
  .venv/bin/python scripts/tracker.py update li-4012345678 --status submitted --notes "Easy Apply; seen in Applied list"
  .venv/bin/python scripts/tracker.py list --status queued,tailored
  .venv/bin/python scripts/tracker.py list --since 7d
  .venv/bin/python scripts/tracker.py due
  .venv/bin/python scripts/tracker.py stats [--since 28d] [--json]
  .venv/bin/python scripts/tracker.py dupe-check --url https://www.dice.com/job-detail/<uuid>
  .venv/bin/python scripts/tracker.py remove setup-test        # test rows only
  .venv/bin/python scripts/tracker.py pause                    # random 20-60 s between applications

Default CSV: ~/job-search/tracker/applications.csv (override with --csv PATH,
before or after the subcommand).

Exit codes: 0 ok; 1 refused or duplicate found; 2 error (bad input, unknown id).
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import random
import re
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit

COLUMNS = [
    "id", "platform", "company", "role", "url", "apply_url", "location", "employment",
    "rate_or_salary", "fit_score", "status", "date_found", "date_applied", "resume_file",
    "cover_file", "follow_up_on", "notes",
]
STATUSES = [
    "found", "screened", "queued", "tailored", "ready", "submitted", "skipped",
    "replied", "interview", "rejected", "offer", "needs-check",
]
REPLY_STATUSES = {"replied", "interview", "rejected", "offer"}
APPLIED_STATUSES = {"submitted"} | REPLY_STATUSES
INTERVIEW_STATUSES = {"interview", "offer"}
FOLLOW_UP_DAYS = 7
DATE_FIELDS = {"date_found", "date_applied", "follow_up_on"}
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$")
TRACKING_PARAMS = {
    "refid", "trackingid", "trk", "trkinfo", "lipi", "midtoken", "midsig", "eid", "otptoken",
    "ebp", "src", "source", "ref", "referrer", "lever-source", "lever-origin", "from", "tk",
    "fbclid", "gclid", "mc_cid", "mc_eid", "alid", "position", "pagenum", "searchid",
}


class TrackerError(Exception):
    """A problem the user should see as a one-line message (exit code 2)."""


# ----------------------------------------------------------------- helpers

def today() -> dt.date:
    return dt.date.today()


def parse_date(value: str, field: str = "date") -> dt.date:
    """Accept YYYY-MM-DD, 'today', 'yesterday' or 'Nd' (N days ago)."""
    v = (value or "").strip().lower()
    if v == "today":
        return today()
    if v == "yesterday":
        return today() - dt.timedelta(days=1)
    m = re.fullmatch(r"(\d+)d", v)
    if m:
        return today() - dt.timedelta(days=int(m.group(1)))
    try:
        return dt.date.fromisoformat(v)
    except ValueError:
        raise TrackerError(f"{field}: expected YYYY-MM-DD, 'today' or 'Nd', got {value!r}") from None


def as_date(value: str) -> dt.date | None:
    try:
        return dt.date.fromisoformat(value.strip()) if value and value.strip() else None
    except ValueError:
        return None


def clean(value: str) -> str:
    """Keep every row on one physical line."""
    return " ".join(str(value).split()) if value is not None else ""


def _is_tracking(key: str) -> bool:
    k = key.lower()
    return k.startswith("utm_") or k in TRACKING_PARAMS


def normalize_url(url: str) -> str:
    """Canonical form used for duplicate detection (not for display)."""
    u = (url or "").strip()
    if not u:
        return ""
    if "://" not in u:
        u = "https://" + u
    parts = urlsplit(u)
    host = (parts.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = re.sub(r"/+$", "", parts.path) or ""
    query = parse_qsl(parts.query, keep_blank_values=False)
    qd = {k: v for k, v in query}

    if host.endswith("linkedin.com"):
        m = re.search(r"/jobs/view/(?:[^/]*?-)?(\d{6,})", path)
        job_id = m.group(1) if m else qd.get("currentJobId")
        if job_id:
            return f"linkedin.com/jobs/view/{job_id}"
    if host.endswith("dice.com"):
        m = re.search(r"/job-detail/([0-9A-Fa-f-]{8,})", path)
        if m:
            return f"dice.com/job-detail/{m.group(1).lower()}"
    if host.endswith("indeed.com"):
        jk = qd.get("jk") or qd.get("vjk")
        if jk:
            return f"indeed.com/viewjob?jk={jk}"
    if host.endswith("greenhouse.io"):
        m = re.search(r"^/([^/]+)/jobs/(\d+)", path)
        if m:
            return f"greenhouse.io/{m.group(1).lower()}/jobs/{m.group(2)}"
    if host == "jobs.lever.co":
        path = re.sub(r"/apply$", "", path)
    if host == "jobs.ashbyhq.com":
        path = re.sub(r"/application$", "", path)

    keep = sorted((k, v) for k, v in query if not _is_tracking(k))
    q = urlencode(keep)
    return f"{host}{path}" + (f"?{q}" if q else "")


def norm_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def title_family(role: str) -> str:
    r = (role or "").lower()
    if "forward deployed" in r or "forward-deployed" in r or re.search(r"\bfde\b", r):
        return "Forward Deployed"
    if "solution" in r and ("engineer" in r or "architect" in r):
        return "Solutions"
    if "architect" in r:
        return "Architect"
    if re.search(r"\bai\b|applied ai|genai|gen ai|generative|\bllm|agent", r):
        return "AI Engineer"
    if "machine learning" in r or re.search(r"\bml\b|mlops", r):
        return "ML Engineer"
    if "data scien" in r:
        return "Data Scientist"
    if "data" in r:
        return "Data Engineer"
    return "Other"


# ----------------------------------------------------------------- storage

def default_csv() -> Path:
    return Path.home() / "job-search" / "tracker" / "applications.csv"


def load(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return list(COLUMNS), []
    with path.open("r", newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        header = reader.fieldnames or []
        rows = [{k: (v or "") for k, v in row.items() if k is not None} for row in reader]
    fields = list(COLUMNS) + [h for h in header if h and h not in COLUMNS]
    for row in rows:
        for f in fields:
            row.setdefault(f, "")
    return fields, rows


def save(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".applications.", suffix=".tmp", dir=str(path.parent))
    try:
        if path.exists():  # keep the file's permissions (mkstemp creates 0600)
            os.chmod(tmp, path.stat().st_mode & 0o777)
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({f: clean(row.get(f, "")) for f in fields})
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def find(rows: list[dict[str, str]], row_id: str) -> dict[str, str] | None:
    return next((r for r in rows if r.get("id") == row_id), None)


def url_matches(rows: list[dict[str, str]], url: str) -> list[dict[str, str]]:
    target = normalize_url(url)
    if not target:
        return []
    return [r for r in rows if target in {normalize_url(r.get("url", "")), normalize_url(r.get("apply_url", ""))} - {""}]


# ----------------------------------------------------------------- validation

def validate_field(field: str, value: str) -> str:
    value = clean(value)
    if field == "status" and value and value not in STATUSES:
        raise TrackerError(f"status must be one of: {', '.join(STATUSES)} (got {value!r})")
    if field in DATE_FIELDS and value:
        value = parse_date(value, field).isoformat()
    if field == "fit_score" and value:
        try:
            score = float(value)
        except ValueError:
            raise TrackerError(f"fit_score must be a number 0-100 (got {value!r})") from None
        if not 0 <= score <= 100:
            raise TrackerError(f"fit_score must be between 0 and 100 (got {value})")
        value = str(int(score)) if score.is_integer() else str(score)
    if field == "platform":
        value = value.lower()
    return value


def mark_submitted(row: dict[str, str], explicit: dict[str, str]) -> None:
    """Set date_applied (if new) and follow_up_on = date_applied + 7 days."""
    if explicit.get("date_applied"):
        row["date_applied"] = explicit["date_applied"]
    newly_applied = not row.get("date_applied")
    if newly_applied:
        row["date_applied"] = today().isoformat()
    if explicit.get("follow_up_on"):
        row["follow_up_on"] = explicit["follow_up_on"]
    elif newly_applied or explicit.get("date_applied") or not row.get("follow_up_on"):
        applied = as_date(row["date_applied"]) or today()
        row["follow_up_on"] = (applied + dt.timedelta(days=FOLLOW_UP_DAYS)).isoformat()


def collect_fields(args: argparse.Namespace, skip: set[str]) -> dict[str, str]:
    out = {}
    for col in COLUMNS:
        if col in skip:
            continue
        value = getattr(args, col, None)
        if value is not None:
            out[col] = validate_field(col, value)
    return out


# ----------------------------------------------------------------- output

def table(rows: list[dict[str, str]], cols: list[tuple[str, str, int]]) -> str:
    if not rows:
        return "(no rows)"
    widths = []
    for key, title, cap in cols:
        w = max([len(title)] + [len(r.get(key, "")) for r in rows])
        widths.append(min(w, cap))
    def cut(text: str, w: int) -> str:
        return text if len(text) <= w else text[: max(w - 1, 1)] + "~"
    lines = ["  ".join(title.ljust(w) for (_, title, _), w in zip(cols, widths))]
    lines.append("  ".join("-" * w for w in widths))
    for r in rows:
        lines.append("  ".join(cut(r.get(k, ""), w).ljust(w) for (k, _, _), w in zip(cols, widths)).rstrip())
    return "\n".join(lines)


LIST_COLS = [
    ("id", "id", 30), ("status", "status", 11), ("platform", "platform", 9),
    ("company", "company", 24), ("role", "role", 36), ("fit_score", "fit", 4),
    ("date_found", "found", 10), ("date_applied", "applied", 10), ("follow_up_on", "follow_up", 10),
]


# ----------------------------------------------------------------- commands

def cmd_add(args: argparse.Namespace, path: Path) -> int:
    fields, rows = load(path)
    row_id = clean(args.id or "")
    if not ID_RE.match(row_id):
        raise TrackerError("--id is required: letters, digits, '.', '_' or '-' (e.g. li-4012345678, ats-acme-ai-engineer)")
    values = collect_fields(args, skip={"id"})
    for req in ("platform", "company", "role"):
        if not values.get(req):
            raise TrackerError(f"--{req} is required for add")
    if find(rows, row_id):
        print(f"REFUSED duplicate id {row_id}", file=sys.stderr)
        return 1
    # Same platform + URL is a duplicate; so is a URL already tracked as any row's posting or apply URL.
    for field in ("url", "apply_url"):
        if values.get(field):
            for r in url_matches(rows, values[field]):
                print(f"REFUSED {field} already tracked as {r['id']} ({r['platform']}, {r['status']})", file=sys.stderr)
                return 1
    row = {f: "" for f in fields}
    row.update(values)
    row["id"] = row_id
    row["status"] = row.get("status") or "found"
    row["date_found"] = row.get("date_found") or today().isoformat()
    if row["status"] == "submitted":
        mark_submitted(row, values)
    rows.append(row)
    save(path, fields, rows)
    print(f"added {row_id} [{row['status']}] {row['company']} - {row['role']}")
    return 0


def cmd_update(args: argparse.Namespace, path: Path) -> int:
    fields, rows = load(path)
    row = find(rows, args.row_id)
    if row is None:
        raise TrackerError(f"unknown id {args.row_id!r}")
    values = collect_fields(args, skip={"id", "notes"})
    if not values and args.notes is None:
        raise TrackerError("nothing to update: pass --status, --notes or another --field value")
    old_status = row.get("status", "")
    row.update(values)
    if args.notes is not None and clean(args.notes):
        note = clean(args.notes)
        if args.replace_notes:
            row["notes"] = note
        else:
            stamped = f"{today().isoformat()}: {note}"
            row["notes"] = f"{row['notes']} | {stamped}" if row.get("notes") else stamped
    if values.get("status") == "submitted":
        mark_submitted(row, values)
    save(path, fields, rows)
    change = f"{old_status} -> {row['status']}" if values.get("status") and values["status"] != old_status else row["status"]
    extra = f" applied {row['date_applied']}, follow up {row['follow_up_on']}" if row["status"] == "submitted" else ""
    print(f"updated {row['id']} [{change}]{extra}")
    return 0


def filter_rows(rows, statuses=None, platform=None, since=None):
    out = []
    for r in rows:
        if statuses and r.get("status") not in statuses:
            continue
        if platform and r.get("platform") != platform.lower():
            continue
        if since:
            dates = [d for d in (as_date(r.get("date_found", "")), as_date(r.get("date_applied", ""))) if d]
            if not any(d >= since for d in dates):
                continue
        out.append(r)
    return out


def parse_statuses(value: str | None) -> set[str] | None:
    if not value:
        return None
    statuses = {s.strip() for s in value.split(",") if s.strip()}
    bad = statuses - set(STATUSES)
    if bad:
        raise TrackerError(f"unknown status {', '.join(sorted(bad))}; use: {', '.join(STATUSES)}")
    return statuses


def cmd_list(args: argparse.Namespace, path: Path) -> int:
    _, rows = load(path)
    since = parse_date(args.since, "--since") if args.since else None
    rows = filter_rows(rows, parse_statuses(args.status), args.platform, since)
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        print(table(rows, LIST_COLS))
        print(f"\n{len(rows)} row(s)")
    return 0


def cmd_due(args: argparse.Namespace, path: Path) -> int:
    _, rows = load(path)
    ref = parse_date(args.today, "--today") if args.today else today()
    due = [r for r in rows if r.get("status") == "submitted" and as_date(r.get("follow_up_on", "")) and as_date(r["follow_up_on"]) <= ref]
    due.sort(key=lambda r: r["follow_up_on"])
    if args.json:
        print(json.dumps(due, indent=2))
    else:
        print(table(due, LIST_COLS + [("url", "url", 60)]))
        print(f"\n{len(due)} follow-up(s) due on or before {ref.isoformat()}")
    return 0


def _rate(part: int, whole: int) -> float:
    return round(100.0 * part / whole, 1) if whole else 0.0


def _group(rows, key_fn):
    groups: dict[str, dict[str, int]] = {}
    for r in rows:
        g = groups.setdefault(key_fn(r), {"applied": 0, "replied": 0, "interviews": 0})
        g["applied"] += 1
        g["replied"] += r["status"] in REPLY_STATUSES
        g["interviews"] += r["status"] in INTERVIEW_STATUSES
    for g in groups.values():
        g["reply_rate_pct"] = _rate(g["replied"], g["applied"])
        g["interview_rate_pct"] = _rate(g["interviews"], g["applied"])
    return dict(sorted(groups.items()))


def _week(r) -> str:
    d = as_date(r.get("date_applied", ""))
    if not d:
        return "unknown"
    year, week, _ = d.isocalendar()
    return f"{year}-W{week:02d}"


def cmd_stats(args: argparse.Namespace, path: Path) -> int:
    _, rows = load(path)
    ref = parse_date(args.today, "--today") if args.today else today()
    since = parse_date(args.since, "--since") if args.since else None
    scoped = filter_rows(rows, since=since) if since else rows
    by_status = {s: 0 for s in STATUSES}
    by_platform: dict[str, dict[str, int]] = {}
    for r in scoped:
        by_status[r.get("status") or "found"] = by_status.get(r.get("status") or "found", 0) + 1
        p = by_platform.setdefault(r.get("platform") or "unknown", {})
        p[r.get("status") or "found"] = p.get(r.get("status") or "found", 0) + 1
    applied = [r for r in scoped if r.get("status") in APPLIED_STATUSES]
    replied = [r for r in applied if r["status"] in REPLY_STATUSES]
    today_rows = [r for r in rows if r.get("date_applied") == ref.isoformat() and r.get("status") in APPLIED_STATUSES]
    today_by_platform: dict[str, int] = {}
    for r in today_rows:
        today_by_platform[r["platform"]] = today_by_platform.get(r["platform"], 0) + 1
    result = {
        "total_rows": len(scoped),
        "since": since.isoformat() if since else None,
        "by_status": {k: v for k, v in by_status.items() if v},
        "by_platform": dict(sorted(by_platform.items())),
        "applied": len(applied),
        "replied": len(replied),
        "reply_rate_pct": _rate(len(replied), len(applied)),
        "interview_rate_pct": _rate(sum(r["status"] in INTERVIEW_STATUSES for r in applied), len(applied)),
        "reply_rate_by_platform": _group(applied, lambda r: r.get("platform") or "unknown"),
        "reply_rate_by_title": _group(applied, lambda r: title_family(r.get("role", ""))),
        "reply_rate_by_week": _group(applied, _week),
        "submitted_today": len(today_rows),
        "submitted_today_by_platform": today_by_platform,
        "today": ref.isoformat(),
    }
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    print(f"Rows: {result['total_rows']}" + (f" (found or applied since {result['since']})" if since else ""))
    print("By status:   " + (", ".join(f"{k} {v}" for k, v in result["by_status"].items()) or "none"))
    for plat, counts in result["by_platform"].items():
        print(f"  {plat:<10} " + ", ".join(f"{k} {v}" for k, v in counts.items()))
    print(f"Applied: {result['applied']}  replied: {result['replied']}  reply rate: {result['reply_rate_pct']}%"
          f"  interview rate: {result['interview_rate_pct']}%  (reply = replied, interview, rejected or offer)")
    for title, key in (("By platform", "reply_rate_by_platform"), ("By title", "reply_rate_by_title"), ("By week applied", "reply_rate_by_week")):
        print(f"{title}:")
        if not result[key]:
            print("  (no applications yet)")
        for name, g in result[key].items():
            print(f"  {name:<18} applied {g['applied']:>3}  replied {g['replied']:>3}  reply {g['reply_rate_pct']:>5}%  interview {g['interview_rate_pct']:>5}%")
    per = ", ".join(f"{k} {v}" for k, v in sorted(today_by_platform.items()))
    print(f"Submitted today ({result['today']}): {result['submitted_today']}" + (f" ({per})" if per else ""))
    return 0


def cmd_dupe_check(args: argparse.Namespace, path: Path) -> int:
    _, rows = load(path)
    if not (args.url or args.id or (args.company and args.role)):
        raise TrackerError("pass --url URL (repeatable), --id ID, or --company C --role R")
    results, found = [], False
    for url in args.url or []:
        hits = url_matches(rows, url)
        found |= bool(hits)
        results.append({"check": "url", "value": url, "normalized": normalize_url(url),
                        "duplicates": [{"id": h["id"], "status": h["status"], "platform": h["platform"]} for h in hits]})
    if args.id:
        hit = find(rows, args.id)
        found |= hit is not None
        results.append({"check": "id", "value": args.id,
                        "duplicates": [{"id": hit["id"], "status": hit["status"], "platform": hit["platform"]}] if hit else []})
    if args.company and args.role:
        key = (norm_text(args.company), norm_text(args.role))
        hits = [r for r in rows if (norm_text(r.get("company", "")), norm_text(r.get("role", ""))) == key]
        found |= bool(hits)
        results.append({"check": "company+role", "value": f"{args.company} | {args.role}",
                        "duplicates": [{"id": h["id"], "status": h["status"], "platform": h["platform"]} for h in hits]})
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for res in results:
            if res["duplicates"]:
                ids = ", ".join(f"{d['id']} ({d['platform']}, {d['status']})" for d in res["duplicates"])
                print(f"DUPLICATE {res['check']} {res['value']} -> {ids}")
            else:
                print(f"NEW {res['check']} {res['value']}")
    return 1 if found else 0


def cmd_remove(args: argparse.Namespace, path: Path) -> int:
    fields, rows = load(path)
    row = find(rows, args.row_id)
    if row is None:
        raise TrackerError(f"unknown id {args.row_id!r}")
    if row.get("status") in APPLIED_STATUSES and not args.force:
        print(f"REFUSED {row['id']} is {row['status']}; history rows are kept (use --force only to undo a mistake)", file=sys.stderr)
        return 1
    rows.remove(row)
    save(path, fields, rows)
    print(f"removed {row['id']} [{row['status']}] {row['company']} - {row['role']}")
    return 0


def cmd_pause(args: argparse.Namespace, path: Path) -> int:
    low, high = sorted((max(args.min, 0.0), max(args.max, 0.0)))
    seconds = random.uniform(low, high)
    time.sleep(seconds)
    print(f"paused {seconds:.0f} s")
    return 0


# ----------------------------------------------------------------- CLI

def add_field_options(parser: argparse.ArgumentParser, skip: set[str]) -> None:
    for col in COLUMNS:
        if col in skip:
            continue
        flags = [f"--{col.replace('_', '-')}"]
        if "_" in col:
            flags.append(f"--{col}")
        parser.add_argument(*flags, dest=col, metavar=col.upper(), default=None)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Job-search application tracker (CSV).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Statuses: " + ", ".join(STATUSES),
    )
    parser.add_argument("--csv", default=None, help=f"tracker CSV (default {default_csv()})")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--csv", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("add", parents=[common], help="add a posting (refuses duplicates)")
    add_field_options(p, skip=set())
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("update", parents=[common], help="update a row by id")
    p.add_argument("row_id", metavar="ID")
    add_field_options(p, skip={"id"})
    p.add_argument("--replace-notes", action="store_true", help="overwrite notes instead of appending")
    p.set_defaults(func=cmd_update)

    p = sub.add_parser("list", parents=[common], help="list rows")
    p.add_argument("--status", help="status or comma-separated statuses")
    p.add_argument("--platform")
    p.add_argument("--since", help="YYYY-MM-DD, today or Nd: rows found or applied on/after this date")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("due", parents=[common], help="follow-ups due today or earlier")
    p.add_argument("--today", help=argparse.SUPPRESS)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_due)

    p = sub.add_parser("stats", parents=[common], help="counts and reply rates")
    p.add_argument("--since", help="limit to rows found or applied since YYYY-MM-DD or Nd")
    p.add_argument("--today", help=argparse.SUPPRESS)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("dupe-check", parents=[common], help="is this posting already tracked?")
    p.add_argument("--url", action="append", help="posting or apply URL (repeatable)")
    p.add_argument("--id")
    p.add_argument("--company")
    p.add_argument("--role")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_dupe_check)

    p = sub.add_parser("remove", parents=[common], help="remove a test row by id")
    p.add_argument("row_id", metavar="ID")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_remove)

    p = sub.add_parser("pause", parents=[common], help="sleep a random 20-60 s (pacing)")
    p.add_argument("--min", type=float, default=20.0)
    p.add_argument("--max", type=float, default=60.0)
    p.set_defaults(func=cmd_pause)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    path = Path(os.path.expanduser(args.csv)) if args.csv else default_csv()
    try:
        return args.func(args, path)
    except TrackerError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
