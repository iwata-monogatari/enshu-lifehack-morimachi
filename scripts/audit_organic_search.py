#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自然検索向け100問の生成物を監査する。"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://morimachi.enshu-lifehack.com"
sys.stdout.reconfigure(encoding="utf-8")


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)
    print("  x " + message)


def main() -> int:
    rows = json.loads((ROOT / "data" / "questions.json").read_text(encoding="utf-8"))
    errors: list[str] = []
    if len(rows) != 100:
        fail(f"質問台帳が100件ではありません: {len(rows)}", errors)

    for row in rows:
        path = ROOT / row["href"].strip("/") / "index.html"
        if not path.is_file():
            fail(f"質問ページがありません: {row['href']}", errors)
            continue
        html = path.read_text(encoding="utf-8")
        title = re.search(r"<title>(.*?)</title>", html, re.S)
        title_text = title.group(1) if title else ""
        keyword_parts = row.get("keyword", "").split()
        missing_terms = [part for part in keyword_parts if part not in title_text and part not in html]
        if missing_terms:
            fail(f"主要検索語が本文にありません: {row['href']} {missing_terms}", errors)
        if html.count('data-track-click="question_related"') != 4:
            fail(f"関連質問が4件ではありません: {row['href']}", errors)
        if '"@type": "WebPage"' not in html or '"@type": "Question"' not in html:
            fail(f"質問の構造化データがありません: {row['href']}", errors)
        if f'<link rel="canonical" href="{SITE}{row["href"]}">' not in html:
            fail(f"canonicalが一致しません: {row['href']}", errors)

    sitemap_path = ROOT / "sitemap.xml"
    if not sitemap_path.is_file():
        fail("sitemap.xml がありません", errors)
    else:
        sitemap = sitemap_path.read_text(encoding="utf-8")
        urls = set(re.findall(r"<loc>([^<]+)</loc>", sitemap))
        expected = {SITE + "/questions/", *(SITE + row["href"] for row in rows)}
        missing = expected - urls
        if missing:
            fail(f"メインサイトマップに質問URLが不足しています: {len(missing)}", errors)

    print(f"  質問ページ: {len(rows)} / sitemap掲載: 101 URL / エラー: {len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
