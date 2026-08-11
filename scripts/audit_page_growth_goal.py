#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""森町ページ拡充目標の日次指標を計測する。

ローカルの ``sitemap.xml`` を公開対象の正本として、ページ数、可視文字数、
noindex、欠損HTML、完全重複を検査する。森町役場のページ数は、再帰的な
サイトマップ取得または監査時に確認した数値を引数で渡す。

例:
    python scripts/audit_page_growth_goal.py --official-count 2758 --record
    python scripts/audit_page_growth_goal.py --fetch-official --record
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://morimachi.enshu-lifehack.com"
OFFICIAL_SITEMAP = "https://www.town.morimachi.shizuoka.jp/sitemap.xml"
# 2026-08-11の659ページを、このスクリプトの「画面本文のみ」の規則で
# 再計測した基準値。従来の約5,030字はmeta description等を含む集計だった
# ため、比較可能性を保つ目的で両方を記録する。
MEASURED_BASELINE_AVERAGE_CHARS = 4_883
REFERENCE_AVERAGE_CHARS = 5_030
REPORT = ROOT / "reports" / "page-growth" / "daily-metrics.json"
USER_AGENT = "MorimachiPageGrowthAudit/1.0 (+https://morimachi.enshu-lifehack.com/)"


class VisibleTextParser(HTMLParser):
    """検索利用者に表示される本文を、ビルド間で同じ規則により抽出する。"""

    SKIP = {"script", "style", "noscript", "template", "svg"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self.SKIP:
            self.skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self.SKIP and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)

    def text(self) -> str:
        return re.sub(r"\s+", "", "".join(self.parts))


def sitemap_locations(payload: bytes) -> tuple[str, list[str]]:
    root = ET.fromstring(payload)
    kind = root.tag.rsplit("}", 1)[-1]
    locations = [
        (node.text or "").strip()
        for node in root.iter()
        if node.tag.rsplit("}", 1)[-1] == "loc" and (node.text or "").strip()
    ]
    return kind, locations


def local_sitemap_urls() -> list[str]:
    kind, locations = sitemap_locations((ROOT / "sitemap.xml").read_bytes())
    if kind != "urlset":
        raise RuntimeError(f"ローカル sitemap.xml がurlsetではありません: {kind}")
    own_host = urllib.parse.urlsplit(SITE).netloc
    urls = []
    for url in locations:
        parsed = urllib.parse.urlsplit(url)
        if parsed.netloc != own_host:
            raise RuntimeError(f"サイトマップに外部URLがあります: {url}")
        urls.append(url)
    if len(urls) != len(set(urls)):
        raise RuntimeError("サイトマップに重複URLがあります")
    return urls


def local_path(url: str) -> Path:
    path = urllib.parse.unquote(urllib.parse.urlsplit(url).path)
    if path == "/":
        return ROOT / "index.html"
    relative = path.lstrip("/")
    if path.endswith("/"):
        return ROOT / relative / "index.html"
    return ROOT / relative


def visible_text(path: Path) -> tuple[str, bool]:
    html = path.read_text(encoding="utf-8")
    parser = VisibleTextParser()
    parser.feed(html)
    robots = re.findall(
        r'<meta\b[^>]*name=["\']robots["\'][^>]*content=["\']([^"\']*)',
        html,
        re.I,
    )
    return parser.text(), any("noindex" in value.lower() for value in robots)


def fetch_official_count() -> int:
    """同一ホストのサイトマップだけを再帰取得し、固有URL数を返す。"""
    official_host = urllib.parse.urlsplit(OFFICIAL_SITEMAP).netloc
    pending = [OFFICIAL_SITEMAP]
    visited: set[str] = set()
    page_urls: set[str] = set()
    def fetch(url: str) -> tuple[str, str, list[str]]:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=30) as response:
            kind, locations = sitemap_locations(response.read())
        return url, kind, locations

    with ThreadPoolExecutor(max_workers=8) as executor:
        while pending:
            batch = [url for url in dict.fromkeys(pending) if url not in visited]
            pending = []
            visited.update(batch)
            for url, kind, locations in executor.map(fetch, batch):
                if kind == "sitemapindex":
                    for child in locations:
                        if urllib.parse.urlsplit(child).netloc != official_host:
                            raise RuntimeError(f"役場サイトマップに外部子サイトマップ: {child}")
                        if child not in visited:
                            pending.append(child)
                elif kind == "urlset":
                    page_urls.update(locations)
                else:
                    raise RuntimeError(f"未知のサイトマップ形式: {kind} {url}")
    return len(page_urls)


def git_commit() -> str:
    return subprocess.check_output(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    ).strip()


def build_metrics(official_count: int) -> dict:
    urls = local_sitemap_urls()
    missing: list[str] = []
    noindex: list[str] = []
    char_counts: list[int] = []
    hashes: list[str] = []
    for url in urls:
        path = local_path(url)
        if not path.is_file():
            missing.append(url)
            continue
        text, is_noindex = visible_text(path)
        if is_noindex:
            noindex.append(url)
        char_counts.append(len(text))
        hashes.append(hashlib.sha256(text.encode("utf-8")).hexdigest())

    duplicate_groups = sum(1 for count in Counter(hashes).values() if count > 1)
    structural_errors = len(missing) + len(noindex) + duplicate_groups
    total_chars = sum(char_counts)
    average = total_chars // len(char_counts) if char_counts else 0
    target = official_count * 2
    return {
        "measured_at_jst": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "official_sitemap_pages": official_count,
        "target_pages": target,
        "site_sitemap_pages": len(urls),
        "page_gap": max(0, target - len(urls)),
        "goal_page_ratio": round(len(urls) / target, 6) if target else 0,
        "measured_html_pages": len(char_counts),
        "total_visible_chars": total_chars,
        "average_visible_chars": average,
        "measured_baseline_average_chars": MEASURED_BASELINE_AVERAGE_CHARS,
        "reference_average_chars": REFERENCE_AVERAGE_CHARS,
        "average_baseline_met": average >= MEASURED_BASELINE_AVERAGE_CHARS,
        "reference_average_met": average >= REFERENCE_AVERAGE_CHARS,
        "missing_html_count": len(missing),
        "noindex_in_sitemap_count": len(noindex),
        "exact_duplicate_text_groups": duplicate_groups,
        "structural_error_count": structural_errors,
        "quality_error_count": structural_errors + int(average < MEASURED_BASELINE_AVERAGE_CHARS),
        "missing_html_sample": missing[:10],
        "noindex_sample": noindex[:10],
    }


def record(metrics: dict) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    rows = json.loads(REPORT.read_text(encoding="utf-8")) if REPORT.is_file() else []
    day = metrics["measured_at_jst"][:10]
    rows = [row for row in rows if row.get("measured_at_jst", "")[:10] != day]
    rows.append(metrics)
    rows.sort(key=lambda row: row["measured_at_jst"])
    REPORT.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--official-count", type=int)
    source.add_argument("--fetch-official", action="store_true")
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()
    official_count = fetch_official_count() if args.fetch_official else args.official_count
    if not official_count or official_count < 1:
        parser.error("役場サイトマップ件数は1以上で指定してください")
    metrics = build_metrics(official_count)
    if args.record:
        record(metrics)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    if metrics["structural_error_count"]:
        print("[失敗] 公開対象に欠損、noindex、または完全重複があります", file=sys.stderr)
        return 1
    if not metrics["average_baseline_met"]:
        print(
            f"[失敗] 平均可視文字数が実測基準未満です: {metrics['average_visible_chars']} < {MEASURED_BASELINE_AVERAGE_CHARS}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
