#!/usr/bin/env python3
"""Approve an explicitly reviewed Phase 4 cohort without touching other rows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLICATION = ROOT / "data" / "seo-phase4-publication.json"


def parse_ids(raw: str) -> list[int]:
    result: set[int] = set()
    for part in raw.split(","):
        token = part.strip()
        if not token:
            continue
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start, end = int(start_text), int(end_text)
            if end < start:
                raise ValueError(f"ID範囲が逆です: {token}")
            result.update(range(start, end + 1))
        else:
            result.add(int(token))
    if not result:
        raise ValueError("--ids に公開確認済みIDを指定してください")
    if min(result) < 1 or max(result) > 300:
        raise ValueError("IDは1-300の範囲で指定してください")
    return sorted(result)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", required=True)
    parser.add_argument("--source-verified", action="store_true")
    parser.add_argument("--uniqueness-verified", action="store_true")
    parser.add_argument("--visual-verified", action="store_true")
    parser.add_argument("--human-reviewed", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    confirmations = {
        "source": args.source_verified,
        "uniqueness": args.uniqueness_verified,
        "visual": args.visual_verified,
        "human": args.human_reviewed,
    }
    missing = [name for name, confirmed in confirmations.items() if not confirmed]
    if missing:
        raise SystemExit("承認根拠が不足しています: " + ", ".join(missing))

    ids = parse_ids(args.ids)
    rows = json.loads(PUBLICATION.read_text(encoding="utf-8"))
    by_id = {int(row["id"]): row for row in rows}
    absent = [item_id for item_id in ids if item_id not in by_id]
    if absent:
        raise SystemExit(f"公開台帳にないIDです: {absent}")

    for item_id in ids:
        row = by_id[item_id]
        row["source_validation"] = "verified"
        row["uniqueness_validation"] = "verified"
        row["visual_validation"] = "verified"
        row["human_reviewed"] = True
        # audit_seo_phase4.py --release alone may turn this on after all gates pass.
        row["publish_ready"] = False

    if not args.check_only:
        PUBLICATION.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    mode = "確認" if args.check_only else "承認記録"
    print(f"Phase4 {mode}: {len(ids)}件 / IDs {','.join(map(str, ids))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
