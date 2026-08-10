# -*- coding: utf-8 -*-
"""Report the human-rewrite state of the second 100 Discover articles."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRAFTS = ROOT / "work" / "discover-expansion-drafts"
STOCK_PHRASES = (
    "を確認する人へ",
    "を進める場合",
    "について家族で共有する際は",
    "一枚につなぐための実用ガイド",
    "同じ答えで済ませず",
)
REQUIRED = ("良い点", "注文したい点", "代案・結論", "大石の視点")


def compact(value: str) -> str:
    return re.sub(r"\s+", "", value)


def main() -> None:
    files = sorted(DRAFTS.glob("*.json"))
    if len(files) != 100:
        raise SystemExit(f"expansion draft count must be 100: {len(files)}")
    complete: list[str] = []
    incomplete: list[str] = []
    errors: list[str] = []
    paragraph_owners: dict[str, set[str]] = defaultdict(set)
    prefix_owners: dict[str, set[str]] = defaultdict(set)
    all_keywords: list[str] = []
    for path in files:
        row = json.loads(path.read_text(encoding="utf-8"))
        slug = row["slug"]
        keywords = [row.get("primary_keyword", ""), *row.get("secondary_keywords", [])]
        all_keywords.extend(keywords)
        rewritten = row.get("publication", {}).get("editorial_rewrite_complete") is True
        (complete if rewritten else incomplete).append(slug)
        if not rewritten:
            continue
        sections = row.get("body_sections", [])
        paragraphs = [compact(p) for s in sections for p in s.get("paragraphs", []) if compact(p)]
        body = "".join(paragraphs)
        for paragraph in paragraphs:
            if len(paragraph) >= 35:
                paragraph_owners[paragraph].add(slug)
                prefix_owners[paragraph[:28]].add(slug)
        headings = [s.get("heading", "") for s in sections]
        description_length = len(compact(row.get("description", "")))
        town_sources = {
            s.get("url") for s in row.get("sources", [])
            if "www.town.morimachi.shizuoka.jp" in s.get("url", "")
        }
        source_urls = [s.get("url", "") for s in row.get("sources", [])]
        publication = row.get("publication", {})
        if len(body) < 5000:
            errors.append(f"{slug}: {len(body)} chars")
        if not 70 <= description_length <= 135:
            errors.append(f"{slug}: description {description_length} chars")
        if len(paragraphs) < 35:
            errors.append(f"{slug}: {len(paragraphs)} paragraphs")
        for required in REQUIRED:
            if not any(required in h for h in headings):
                errors.append(f"{slug}: missing heading {required}")
        if len(town_sources) < 2:
            errors.append(f"{slug}: town sources {len(town_sources)}")
        if len(source_urls) != len(set(source_urls)):
            errors.append(f"{slug}: duplicate source URLs")
        if len(row.get("illustrations", [])) != 2:
            errors.append(f"{slug}: illustrations must be 2")
        # The assembler expands same-category links to five; source drafts may
        # deliberately name only the three strongest editorial relationships.
        if len(row.get("related_slugs", [])) < 3:
            errors.append(f"{slug}: related slugs must be 3+")
        if len(keywords) != 3 or any(not keyword for keyword in keywords):
            errors.append(f"{slug}: keywords must be primary 1 + secondary 2")
        if "政策" in json.dumps(row, ensure_ascii=False):
            errors.append(f"{slug}: banned word 政策")
        for flag in ("published", "publish_ready", "editor_reviewed"):
            if publication.get(flag) is not False:
                errors.append(f"{slug}: source draft {flag} must stay false")
        for gate in ("source_validation", "uniqueness_validation", "visual_validation"):
            if publication.get(gate) != "pending":
                errors.append(f"{slug}: source draft {gate} must stay pending")
        for phrase in STOCK_PHRASES:
            if phrase in json.dumps(row, ensure_ascii=False):
                errors.append(f"{slug}: stock phrase {phrase}")
    duplicate_paragraphs = [owners for owners in paragraph_owners.values() if len(owners) > 1]
    if duplicate_paragraphs:
        errors.append(f"completed articles share {len(duplicate_paragraphs)} exact paragraphs")
    repeated_prefixes = [owners for owners in prefix_owners.values() if len(owners) >= 3]
    if repeated_prefixes:
        errors.append(f"completed articles share {len(repeated_prefixes)} prefixes across 3+ articles")
    if len(all_keywords) != 300:
        errors.append(f"expansion keywords must total 300: {len(all_keywords)}")
    duplicate_keywords = [keyword for keyword, count in Counter(all_keywords).items() if count > 1]
    if duplicate_keywords:
        errors.append(f"expansion keywords are duplicated: {duplicate_keywords[:8]}")
    print(f"rewrite progress: {len(complete)}/100 complete, {len(incomplete)} remaining")
    for slug in complete:
        print(f"  PASS {slug}")
    if errors:
        print("rewrite errors:")
        for error in errors:
            print(f"  FAIL {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
