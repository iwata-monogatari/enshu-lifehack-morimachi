#!/usr/bin/env python3
"""Build the phase-1 publication manifest from reviewed renovation decisions."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def page_path(url: str) -> Path:
    return ROOT / url.strip("/") / "index.html"


def main() -> int:
    ledger = json.loads((ROOT / "data" / "seo-renovation-200.json").read_text(encoding="utf-8"))
    selected = []
    for row in ledger:
        if not row["priority_20"] or row["decision"] not in {"CREATE", "EXPAND_EXISTING"}:
            continue
        selected.append(
            {
                "id": row["id"],
                "primary_keyword": row["primary_keyword"],
                "decision": row["decision"],
                "url": row["final_url"],
                "proposed_title_h1": row["proposed_title_h1"],
                "cta_level": row["cta_level"],
                "exists": page_path(row["final_url"]).is_file(),
                "fact_checked_at": "2026-08-09",
            }
        )
    output = ROOT / "data" / "seo-phase1-publication.json"
    output.write_text(json.dumps(selected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"phase1_publishable={len(selected)} existing_files={sum(row['exists'] for row in selected)} output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
