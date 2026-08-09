#!/usr/bin/env python3
"""Parse the 200-page renovation plan and attach existing-URL candidates.

The similarity result is only a review aid.  ``decision`` and ``final_url``
remain blank until a human has checked search intent and cannibalization.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRIORITY_20 = {1, 2, 11, 12, 15, 16, 19, 26, 27, 28, 32, 41, 46, 48, 81, 96, 145, 181, 186, 197}
ROW = re.compile(
    r"\|\s*(\d{1,3})\s*\|\s*(.*?)\s*\|\s*`([^`]+)`\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(L\d)\s*\|"
)


def tokens(value: str) -> set[str]:
    value = re.sub(r"[｜|・／/、。！？?（）()【】「」『』：:]+", " ", value)
    return {part.lower() for part in value.split() if len(part) >= 2 and part not in {"静岡県", "森町"}}


def phase(number: int) -> str:
    if number in PRIORITY_20:
        return "phase1"
    if 96 <= number <= 145 or 161 <= number <= 170:
        return "phase2"
    if 1 <= number <= 65:
        return "phase3"
    return "phase4"


def cluster(url: str) -> str:
    return url.strip("/").split("/", 1)[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "seo-renovation-200.json")
    args = parser.parse_args()

    plan_text = args.plan.read_text(encoding="utf-8")
    existing = json.loads((ROOT / "data" / "url-ledger.json").read_text(encoding="utf-8"))
    rows: list[dict] = []
    for line in plan_text.splitlines():
        match = ROW.match(line)
        if not match:
            continue
        number = int(match.group(1))
        keyword, proposed_url, title, related, cta = match.groups()[1:]
        query_tokens = tokens(keyword + " " + title)
        ranked = []
        for page in existing:
            if page.get("redirect") or not page.get("url"):
                continue
            haystack = " ".join(str(page.get(key, "")) for key in ("title", "h1", "keyword", "intent", "description"))
            overlap = query_tokens & tokens(haystack)
            if overlap:
                score = len(overlap) / max(1, len(query_tokens))
                ranked.append((score, len(overlap), page["url"], page.get("title", "")))
        ranked.sort(reverse=True)
        suggestions = [
            {"url": url, "title": existing_title, "score": round(score, 3)}
            for score, _, url, existing_title in ranked[:5]
        ]
        rows.append(
            {
                "id": number,
                "phase": phase(number),
                "priority_20": number in PRIORITY_20,
                "cluster": cluster(proposed_url),
                "primary_keyword": keyword,
                "proposed_url": proposed_url,
                "proposed_title_h1": title,
                "related_ids": [int(value) for value in re.findall(r"\d+", related)],
                "cta_level": cta,
                "existing_candidates": suggestions,
                "decision": "",
                "final_url": "",
                "decision_reason": "",
                "unique_angle": "",
                "source_urls": [],
                "status": "review",
            }
        )

    if {row["id"] for row in rows} != set(range(1, 201)):
        raise SystemExit(f"expected IDs 1..200, parsed {len(rows)} rows")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"parsed={len(rows)} phase1={sum(row['priority_20'] for row in rows)} output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
