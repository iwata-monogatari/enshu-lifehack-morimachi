#!/usr/bin/env python3
"""Validate the official-source research catalog and report duplicate bodies."""

from __future__ import annotations

import argparse
import json
import urllib.parse
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "data" / "official-source-catalog.json"
OFFICIAL_HOST = "www.town.morimachi.shizuoka.jp"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("catalog", nargs="?", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--require-fetched", type=int, default=0)
    args = parser.parse_args()

    document = json.loads(args.catalog.read_text(encoding="utf-8"))
    rows = document.get("sources")
    if not isinstance(rows, list):
        raise SystemExit("sources配列がありません")
    errors: list[str] = []
    urls = [str(row.get("url", "")) for row in rows]
    if len(urls) != len(set(urls)):
        errors.append("URLが重複しています")
    if document.get("total_urls") != len(rows):
        errors.append("total_urlsとsources件数が一致しません")
    for index, row in enumerate(rows, start=1):
        url = str(row.get("url", ""))
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "https" or parsed.netloc != OFFICIAL_HOST:
            errors.append(f"{index}: 森町公式HTTPS URLではありません: {url}")
        status = str(row.get("status", ""))
        if status == "http-200":
            for field in ("checked_at", "content_type", "final_url", "payload_sha256"):
                if not row.get(field):
                    errors.append(f"{index}: 取得済み行に{field}がありません")
            if row.get("content_type") in {"text/html", "application/xhtml+xml"}:
                for field in ("title", "headings", "visible_chars", "visible_sha256"):
                    if not row.get(field):
                        errors.append(f"{index}: HTML行に{field}がありません")

    fetched = [row for row in rows if row.get("status") == "http-200"]
    if len(fetched) < args.require_fetched:
        errors.append(f"取得済み件数が不足: {len(fetched)} < {args.require_fetched}")
    html_rows = [row for row in fetched if row.get("visible_sha256")]
    body_counts = Counter(str(row["visible_sha256"]) for row in html_rows)
    duplicate_groups = sum(1 for count in body_counts.values() if count > 1)
    duplicate_pages = sum(count for count in body_counts.values() if count > 1)
    status_counts = Counter(str(row.get("status", "pending")) for row in rows)

    print(f"official source catalog: {len(rows)} URLs")
    print(f"fetched: {len(fetched)} / pending: {status_counts.get('pending', 0)}")
    print(f"HTML unique bodies: {len(body_counts)} / duplicate groups: {duplicate_groups} ({duplicate_pages} pages)")
    if errors:
        for error in errors[:30]:
            print(f"ERROR: {error}")
        raise SystemExit(f"監査失敗: {len(errors)}件")
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
