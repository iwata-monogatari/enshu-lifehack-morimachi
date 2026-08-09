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
EXPANSION_DATA = ROOT / "data" / "search-expansion-pages.json"
DECISION_DATA = ROOT / "data" / "search-intent-200-decisions.json"
MIN_LENGTH = 90
MAX_LENGTH = 130


def plain_text(value: str) -> str:
    value = unescape(re.sub(r"<[^>]+>", "", value))
    return re.sub(r"\s+", " ", value).strip()


def shorten(value: str) -> str:
    if len(value) <= MAX_LENGTH:
        return value
    return value[: MAX_LENGTH - 1].rstrip("、。 ") + "。"


def fit_standard(value: str) -> str:
    """作業指示書の90〜130字へ収める。本文の説明を補う場合だけ定型を足す。"""
    value = value.rstrip("。 ") + "。"
    if len(value) < MIN_LENGTH:
        value += "対象、手順、必要書類、費用、期限、森町の窓口と注意点を、公式情報へのリンクとともに案内します。"
    return shorten(value)


def description_for(item: dict) -> str:
    explicit = plain_text(item.get("seo_description", ""))
    if explicit:
        return fit_standard(explicit)
    lead = plain_text(item.get("lead", ""))
    if not lead:
        return ""
    if "森町" not in lead[:30]:
        lead = "静岡県森町で、" + lead
    return fit_standard(lead)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    content: dict[str, dict] = {}
    phase1_path = ROOT / "data" / "seo-phase1-publication.json"
    phase1_urls = {
        row["url"] for row in json.loads(phase1_path.read_text(encoding="utf-8"))
    } if phase1_path.exists() else set()
    for source in sorted(CONTENT_DIR.glob("*.json")):
        if source.stem.startswith("_"):
            continue
        for item in json.loads(source.read_text(encoding="utf-8")):
            if item.get("href"):
                content[item["href"]] = item

    if EXPANSION_DATA.exists():
        for item in json.loads(EXPANSION_DATA.read_text(encoding="utf-8")):
            if item.get("href"):
                content[item["href"]] = {
                    "href": item["href"],
                    "seo_description": item.get("description", ""),
                    "lead": item.get("conclusion", ""),
                }

    # The decision ledger is the final authority for pages in this project.  Some
    # older generators do not have a data/content entry, so retain their written
    # description and only bring its length into the agreed range.
    if DECISION_DATA.exists():
        for decision in json.loads(DECISION_DATA.read_text(encoding="utf-8")):
            href = decision.get("final_url", "")
            if not href.startswith("/life/") or href in content:
                continue
            path = ROOT / href.strip("/") / "index.html"
            if not path.exists():
                continue
            current = path.read_text(encoding="utf-8")
            match = re.search(r'<meta name="description" content="(.*?)">', current, re.S)
            if match:
                content[href] = {"href": href, "seo_description": plain_text(match.group(1))}

    found = changed = skipped = 0
    for href, item in content.items():
        # 第1期の全面改稿ページは、執筆時に個別最適化した説明文を正とする。
        if href in phase1_urls:
            continue
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
