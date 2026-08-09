#!/usr/bin/env python3
"""Merge the three human-review reports into the 200-candidate ledger."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "seo-renovation-200.json"
REPORTS = [
    (ROOT / "work" / "agent-audit-tourism-food.md", "tourism"),
    (ROOT / "work" / "agent-audit-life-health.md", "life"),
    (ROOT / "work" / "agent-audit-areas-home.md", "areas"),
]
DECISIONS = {"CREATE", "MERGE", "EXPAND_EXISTING", "HOLD"}


def clean(value: str) -> str:
    return value.strip().replace("**", "").replace("`", "")


def parse_report(path: Path, kind: str) -> dict[int, dict[str, str]]:
    found: dict[int, dict[str, str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not re.match(r"^\|\d+\|", line):
            continue
        cols = [part.strip() for part in line.strip().strip("|").split("|")]
        number = int(cols[0])
        if kind == "tourism":
            decision = clean(cols[2])
            final_url = clean(cols[3])
            reason, angle, sources = clean(cols[4]), clean(cols[5]), clean(cols[6])
        elif kind == "life":
            combined = clean(cols[2])
            decision = next((value for value in DECISIONS if combined.startswith(value)), "")
            url_match = re.search(r"(/[A-Za-z0-9_./-]+/)", combined)
            final_url = url_match.group(1) if url_match else ""
            reason, angle, sources = clean(cols[3]), clean(cols[4]), clean(cols[5])
        else:
            decision = clean(cols[2])
            final_url = clean(cols[3]).split("（", 1)[0]
            reason, angle, sources = clean(cols[4]), "", clean(cols[5])
        if decision not in DECISIONS:
            raise ValueError(f"invalid decision in {path.name} #{number}: {decision}")
        found[number] = {
            "decision": decision,
            "final_url": final_url,
            "decision_reason": reason,
            "unique_angle": angle,
            "source_notes": sources,
        }
    return found


def main() -> int:
    rows = json.loads(LEDGER.read_text(encoding="utf-8"))
    audits: dict[int, dict[str, str]] = {}
    for path, kind in REPORTS:
        parsed = parse_report(path, kind)
        overlap = audits.keys() & parsed.keys()
        if overlap:
            raise SystemExit(f"duplicate audit IDs: {sorted(overlap)}")
        audits.update(parsed)
    if set(audits) != set(range(1, 201)):
        missing = sorted(set(range(1, 201)) - set(audits))
        raise SystemExit(f"audit coverage incomplete: {missing}")

    for row in rows:
        row.update(audits[row["id"]])
        row["status"] = "ready" if row["decision"] != "HOLD" else "blocked_on_fieldwork"
    LEDGER.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = ROOT / "reports" / "seo-renovation-200-decisions.csv"
    report.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "id", "phase", "priority_20", "cluster", "primary_keyword", "proposed_url",
        "decision", "final_url", "decision_reason", "unique_angle", "source_notes", "cta_level", "status",
    ]
    with report.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    counts = {value: sum(row["decision"] == value for row in rows) for value in sorted(DECISIONS)}
    priority = {value: sum(row["priority_20"] and row["decision"] == value for row in rows) for value in sorted(DECISIONS)}
    print(f"all={counts}")
    print(f"priority20={priority}")
    print(f"json={LEDGER} csv={report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
