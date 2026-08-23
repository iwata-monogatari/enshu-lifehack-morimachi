#!/usr/bin/env python3
"""重点SEO URLと検索意図の代表URLが公開可能な状態か検査する。"""
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def page_path(url: str) -> Path:
    if url == "/":
        return ROOT / "index.html"
    return ROOT / url.strip("/") / "index.html"


def main() -> None:
    priority = json.loads((ROOT / "data" / "seo-priority-urls.json").read_text(encoding="utf-8"))
    ownership = json.loads((ROOT / "data" / "seo-topic-ownership.json").read_text(encoding="utf-8"))
    urls = priority["urls"]
    failures: list[str] = []

    if not 20 <= len(urls) <= 30:
        failures.append(f"重点URLは20〜30件にする: {len(urls)}件")
    if len(urls) != len(set(urls)):
        failures.append("重点URLに重複があります")

    for url in urls:
        path = page_path(url)
        if not path.exists():
            failures.append(f"重点URLのHTMLがありません: {url}")
            continue
        source = path.read_text(encoding="utf-8")
        if re.search(r'<meta\s+name="robots"\s+content="[^"]*noindex', source, re.I):
            failures.append(f"重点URLがnoindexです: {url}")
        canonical = f'https://morimachi.enshu-lifehack.com{url}'
        if f'<link rel="canonical" href="{canonical}">' not in source:
            failures.append(f"重点URLのcanonicalが不一致です: {url}")

    for topic in ownership["topics"]:
        url = topic["primary_url"]
        if url not in urls:
            failures.append(f"代表URLが重点URLにありません: {topic['topic']} {url}")

    if failures:
        raise SystemExit("\n".join(failures))
    print(f"SEO重点URL: {len(urls)}件 / 代表テーマ: {len(ownership['topics'])}件 / errors=0")


if __name__ == "__main__":
    main()
