#!/usr/bin/env python3
"""Validate independent Phase 4 enrichment records for topic IDs 101-200."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "seo-phase4-enrichment-101-200.json"
REQUIRED_KEYS = {
    "id", "verified_facts", "morimachi_conditions", "section_headings", "faqs", "sources"
}
FORBIDDEN = "\u653f\u7b56"
RISK_IDS = set(range(131, 186))
RISK_WORDS = ("\u5fc5\u305a\u8a31\u53ef", "\u5fc5\u305a\u975e\u8ab2\u7a0e", "\u5fc5\u305a\u767b\u8a18\u3067\u304d", "\u5fc5\u305a\u8ee2\u7528\u3067\u304d")


def main() -> int:
    rows = json.loads(DATA.read_text(encoding="utf-8"))
    errors: list[str] = []
    if not isinstance(rows, list):
        errors.append("top level must be an array")
        rows = []
    ids = [row.get("id") for row in rows if isinstance(row, dict)]
    expected = list(range(101, 201))
    if ids != expected:
        errors.append("IDs must be exactly 101..200 in order")

    source_counter: Counter[str] = Counter()
    for row in rows:
        ident = row.get("id", "?")
        missing = REQUIRED_KEYS - set(row)
        if missing:
            errors.append(f"{ident}: missing keys {sorted(missing)}")
            continue
        facts = row["verified_facts"]
        conditions = row["morimachi_conditions"]
        headings = row["section_headings"]
        faqs = row["faqs"]
        sources = row["sources"]
        if len(facts) < 6 or len({f.get('statement') for f in facts}) != len(facts):
            errors.append(f"{ident}: needs 6 unique verified facts")
        if len(conditions) < 3 or len(set(conditions)) != len(conditions):
            errors.append(f"{ident}: needs 3 unique Mori conditions")
        if len(headings) < 12 or len(set(headings)) != len(headings):
            errors.append(f"{ident}: needs 12 unique headings")
        if len(faqs) < 4 or len({f.get('question') for f in faqs}) != len(faqs):
            errors.append(f"{ident}: needs 4 unique FAQs")
        urls = [source.get("url", "") for source in sources]
        mori = [url for url in urls if urlparse(url).hostname == "www.town.morimachi.shizuoka.jp"]
        external = [url for url in urls if urlparse(url).hostname != "www.town.morimachi.shizuoka.jp"]
        if len(set(mori)) < 2 or len(set(external)) < 1:
            errors.append(f"{ident}: needs 2 Mori URLs and 1 external authority URL")
        for source in sources:
            source_counter[source.get("url", "")] += 1
            if not all(source.get(key) for key in ("url", "role", "title", "status")):
                errors.append(f"{ident}: incomplete source metadata")
            if not source.get("status", "").startswith("verified_200_"):
                errors.append(f"{ident}: source is not live-verified: {source.get('url')}")
        for fact in facts:
            if fact.get("source_url") not in urls:
                errors.append(f"{ident}: fact source is absent from sources")
        serialized = json.dumps(row, ensure_ascii=False)
        if FORBIDDEN in serialized:
            errors.append(f"{ident}: forbidden term found")
        if ident in RISK_IDS:
            for token in ("\u671f\u9650", "\u5bfe\u8c61", "\u7a93\u53e3", "\u65ad\u5b9a"):
                if token not in serialized:
                    errors.append(f"{ident}: legal/tax/agriculture/forest guardrail lacks {token}")
            if any(word in serialized for word in RISK_WORDS):
                errors.append(f"{ident}: prohibited categorical legal conclusion")

    report = {
        "status": "PASS" if not errors else "FAIL",
        "records": len(rows),
        "id_min": min(ids) if ids else None,
        "id_max": max(ids) if ids else None,
        "facts": sum(len(r.get("verified_facts", [])) for r in rows),
        "conditions": sum(len(r.get("morimachi_conditions", [])) for r in rows),
        "headings": sum(len(r.get("section_headings", [])) for r in rows),
        "faqs": sum(len(r.get("faqs", [])) for r in rows),
        "source_references": sum(source_counter.values()),
        "unique_source_urls": len(source_counter),
        "errors": errors,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
