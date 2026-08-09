#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本番サイトの検索改修前ベースラインを取得する。

サイトマップ掲載URLを実際に取得し、HTTP状態、title、H1、description、
canonical、noindex、内部リンク数を保存する。あわせて、作業指示書が対象と
する life/ 配下129ページのSEO台帳を出力する。

実行:
    python scripts/capture_search_baseline.py
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from html import unescape
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://morimachi.enshu-lifehack.com"
OUT = ROOT / "reports" / "search-traffic-baseline-20260809"
UA = "MorimachiSearchBaseline/1.0 (+https://morimachi.enshu-lifehack.com/)"
TIMEOUT = 25

TAG_RE = re.compile(r"<[^>]+>")
HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', re.I)


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(TAG_RE.sub("", value))).strip()


def first(pattern: str, html: str) -> str:
    match = re.search(pattern, html, re.I | re.S)
    return clean(match.group(1)) if match else ""


def request(url: str, attempts: int = 1) -> tuple[int, str, bytes, str]:
    for attempt in range(attempts):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                return response.status, response.geturl(), response.read(), ""
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt + 1 < attempts:
                time.sleep(1.0 * (attempt + 1))
                continue
            return exc.code, exc.geturl(), exc.read(), str(exc)
        except Exception as exc:  # ネットワーク障害も台帳に残す
            if attempt + 1 < attempts:
                time.sleep(1.0 * (attempt + 1))
                continue
            return 0, url, b"", f"{type(exc).__name__}: {exc}"
    raise AssertionError("unreachable")


def url_path(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    path = parsed.path or "/"
    return path if path.endswith("/") or "." in path.rsplit("/", 1)[-1] else path + "/"


def normalize_internal(base: str, href: str) -> str:
    absolute = urllib.parse.urljoin(base, href)
    parsed = urllib.parse.urlsplit(absolute)
    if parsed.netloc != urllib.parse.urlsplit(SITE).netloc:
        return ""
    path = parsed.path or "/"
    if path.endswith("/index.html"):
        path = path[: -len("index.html")]
    return path


def fetch_page(url: str, attempts: int = 1) -> dict:
    status, final_url, payload, error = request(url, attempts=attempts)
    html = payload.decode("utf-8", errors="replace")
    h1s = re.findall(r"<h1\b[^>]*>(.*?)</h1>", html, re.I | re.S)
    links = {
        normalize_internal(final_url, href)
        for href in HREF_RE.findall(html)
        if not href.startswith(("mailto:", "tel:", "javascript:"))
    }
    links.discard("")
    canonical = first(
        r'<link\b[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', html
    ) or first(
        r'<link\b[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\']canonical["\']', html
    )
    robots = first(r'<meta\b[^>]*name=["\']robots["\'][^>]*content=["\']([^"\']+)', html)
    return {
        "url": url,
        "path": url_path(url),
        "http_status": status,
        "final_url": final_url,
        "redirected": final_url.rstrip("/") != url.rstrip("/"),
        "title": first(r"<title>(.*?)</title>", html),
        "h1": clean(h1s[0]) if h1s else "",
        "h1_count": len(h1s),
        "description": first(
            r'<meta\b[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)', html
        ),
        "canonical": canonical,
        "robots_meta": robots,
        "indexable": status == 200 and "noindex" not in robots.lower(),
        "outgoing_links": len(links),
        "outgoing_paths": sorted(links),
        "incoming_links": 0,
        "error": error,
        "bytes": len(payload),
    }


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in columns})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--retry-failed", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    captured_at = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(timespec="seconds")

    sitemap_status, sitemap_final, sitemap_bytes, sitemap_error = request(SITE + "/sitemap.xml")
    robots_status, robots_final, robots_bytes, robots_error = request(SITE + "/robots.txt")
    (OUT / "sitemap.xml").write_bytes(sitemap_bytes)
    (OUT / "robots.txt").write_bytes(robots_bytes)

    if sitemap_status != 200:
        print(f"[失敗] sitemap.xml: HTTP {sitemap_status} {sitemap_error}")
        return 1

    root = ET.fromstring(sitemap_bytes)
    namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = [node.text.strip() for node in root.findall("s:url/s:loc", namespace) if node.text]

    previous: dict[str, dict] = {}
    previous_path = OUT / "all-public-urls.json"
    if args.retry_failed and previous_path.is_file():
        previous = {row["url"]: row for row in json.loads(previous_path.read_text(encoding="utf-8"))}
    fetch_urls = [url for url in urls if not previous or previous.get(url, {}).get("http_status") != 200]
    rows: list[dict] = [row for url, row in previous.items() if row.get("http_status") == 200 and url in urls]
    workers = 1 if args.retry_failed else 8
    attempts = 5 if args.retry_failed else 1
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(fetch_page, url, attempts): url for url in fetch_urls}
        for number, future in enumerate(as_completed(futures), 1):
            rows.append(future.result())
            if args.retry_failed:
                time.sleep(0.15)
            if number % 25 == 0 or number == len(fetch_urls):
                print(f"今回取得 {number}/{len(fetch_urls)}（全体 {len(rows)}/{len(urls)}）")

    rows.sort(key=lambda row: row["path"])
    by_path = {row["path"]: row for row in rows}
    for source in rows:
        for target in set(source["outgoing_paths"]):
            if target in by_path:
                by_path[target]["incoming_links"] += 1

    columns = [
        "url", "path", "http_status", "final_url", "redirected", "title", "h1",
        "h1_count", "description", "canonical", "robots_meta", "indexable",
        "incoming_links", "outgoing_links", "error", "bytes",
    ]
    write_csv(OUT / "all-public-urls.csv", rows, columns)
    (OUT / "all-public-urls.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    topics = json.loads((ROOT / "data" / "topics_master.json").read_text(encoding="utf-8"))
    topics_by_path = {item["href"]: item for item in topics}
    life_rows = []
    for row in rows:
        if not row["path"].startswith("/life/") or row["path"].count("/") < 3:
            continue
        topic = topics_by_path.get(row["path"], {})
        life_rows.append({
            "existing_url": row["path"],
            "current_title": row["title"],
            "current_h1": row["h1"],
            "primary_intent": topic.get("intent", ""),
            "target_query": topic.get("primary_keyword", ""),
            "indexable": row["indexable"],
            "canonical": row["canonical"],
            "incoming_links": row["incoming_links"],
            "outgoing_links": row["outgoing_links"],
            "action": topic.get("action", "keep").upper(),
            "http_status": row["http_status"],
            "description_length": len(row["description"]),
            "official_source_count": len({s.get("url", "") for s in topic.get("sources_morimachi", []) if s.get("url")}),
            "verified_date": topic.get("verified_date", ""),
        })
    life_rows.sort(key=lambda row: row["existing_url"])
    life_columns = [
        "existing_url", "current_title", "current_h1", "primary_intent", "target_query",
        "indexable", "canonical", "incoming_links", "outgoing_links", "action",
        "http_status", "description_length", "official_source_count", "verified_date",
    ]
    write_csv(OUT / "existing-129-seo-ledger.csv", life_rows, life_columns)
    (OUT / "existing-129-seo-ledger.json").write_text(
        json.dumps(life_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    summary = {
        "captured_at_jst": captured_at,
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, encoding="utf-8"
        ).strip(),
        "sitemap_url": sitemap_final,
        "sitemap_status": sitemap_status,
        "robots_url": robots_final,
        "robots_status": robots_status,
        "robots_error": robots_error,
        "sitemap_url_count": len(urls),
        "fetched_url_count": len(rows),
        "http_200_count": sum(row["http_status"] == 200 for row in rows),
        "non_200_count": sum(row["http_status"] != 200 for row in rows),
        "indexable_count": sum(bool(row["indexable"]) for row in rows),
        "life_page_count": len(life_rows),
        "orphan_life_page_count": sum(row["incoming_links"] == 0 for row in life_rows),
        "life_pages_under_3_incoming": sum(row["incoming_links"] < 3 for row in life_rows),
        "life_pages_under_3_outgoing": sum(row["outgoing_links"] < 3 for row in life_rows),
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if len(life_rows) != 129:
        print(f"[失敗] lifeページが129件ではありません: {len(life_rows)}")
        return 1
    if summary["non_200_count"]:
        print(f"[注意] HTTP 200以外が{summary['non_200_count']}件あります")
    return 0


if __name__ == "__main__":
    sys.exit(main())
