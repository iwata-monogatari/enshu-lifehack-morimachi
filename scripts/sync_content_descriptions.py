#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""個別ガイドのmeta descriptionを執筆済み本文から同期する。冪等。"""
from __future__ import annotations

import json
import re
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "data" / "content"
MAX_LENGTH = 132


def plain_text(value: str) -> str:
    value = unescape(re.sub(r"<[^>]+>", "", value))
    return re.sub(r"\s+", " ", value).strip()


def shorten(value: str) -> str:
    if len(value) <= MAX_LENGTH:
        return value
    return value[: MAX_LENGTH - 1].rstrip("、。 ") + "。"


def description_for(item: dict) -> str:
    explicit = plain_text(item.get("seo_description", ""))
    if explicit:
        return shorten(explicit)
    lead = plain_text(item.get("lead", ""))
    if not lead:
        return ""
    if "森町" not in lead[:30]:
        lead = "静岡県森町で、" + lead
    return shorten(lead)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    content: dict[str, dict] = {}
    for source in sorted(CONTENT_DIR.glob("*.json")):
        if source.stem.startswith("_"):
            continue
        for item in json.loads(source.read_text(encoding="utf-8")):
            if item.get("href"):
                content[item["href"]] = item

    found = changed = skipped = 0
    for href, item in content.items():
        description = description_for(item)
        if not description:
            skipped += 1
            continue
        path = ROOT / href.strip("/") / "index.html"
        if not path.exists():
            skipped += 1
            continue
        html = original = path.read_text(encoding="utf-8")
        pattern = re.compile(r'(<meta name="description" content=").*?(">)', re.S)
        if not pattern.search(html):
            skipped += 1
            continue
        found += 1
        html = pattern.sub(
            lambda match: match.group(1) + description.replace('"', "&quot;") + match.group(2),
            html,
            count=1,
        )
        if html != original:
            path.write_text(html, encoding="utf-8")
            changed += 1
    print(f"個別description同期: 対象 {found} / 更新 {changed} / 対象外 {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
