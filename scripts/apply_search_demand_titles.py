#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""検索需要を確認した優先ガイドのtitle/H1を台帳から同期する。

手書きHTMLだけを直して台帳と乖離させないため、タイトルの唯一の根拠は
data/topics_master.json の title とする。冪等。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "data" / "topics_master.json"
SITE_NAME = "森町ライフハック"

PRIORITY_HREFS = {
    "/life/start-living/how-to-garbage/",
    "/life/family-grow/nursery-school/",
    "/life/family-grow/child-allowance/",
    "/life/education/school-zones/",
    "/life/living-soon/about-morimachi/",
    "/life/emergency/evacuation-hazard-map/",
    "/life/housing/vacant-house/",
    "/life/parents-care/long-term-care-insurance/",
    "/life/play-out/visit-library/",
    "/life/start-living/water-sewer/",
    "/life/work-life/subsidies/",
}


def sync_page(path: Path, title: str) -> bool:
    html = original = path.read_text(encoding="utf-8")
    html = re.sub(
        r"<title>.*?</title>",
        f"<title>{title} | {SITE_NAME}</title>",
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(
        r'(<section class="hero">.*?<h1>).*?(</h1>)',
        lambda match: match.group(1) + title + match.group(2),
        html,
        count=1,
        flags=re.S,
    )

    def breadcrumb(match: re.Match[str]) -> str:
        inner = match.group(1)
        if "／" not in inner:
            return match.group(0)
        prefix = inner.rsplit("／", 1)[0]
        return f'<p class="breadcrumb">{prefix}／ {title}</p>'

    html = re.sub(
        r'<p class="breadcrumb">(.*?)</p>',
        breadcrumb,
        html,
        count=1,
        flags=re.S,
    )
    if html != original:
        path.write_text(html, encoding="utf-8")
        return True
    return False


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    by_href = {item["href"]: item for item in ledger}
    missing = sorted(PRIORITY_HREFS - by_href.keys())
    if missing:
        print("[失敗] 台帳にない優先URL: " + ", ".join(missing))
        return 1

    changed = 0
    phase1_path = ROOT / "data" / "seo-phase1-publication.json"
    phase1_urls = {
        row["url"] for row in json.loads(phase1_path.read_text(encoding="utf-8"))
    } if phase1_path.exists() else set()
    for href in sorted(PRIORITY_HREFS):
        if href in phase1_urls:
            continue
        path = ROOT / href.strip("/") / "index.html"
        if not path.exists():
            print(f"[失敗] HTMLがない: {href}")
            return 1
        title = by_href[href].get("title", "").strip()
        if not title:
            print(f"[失敗] titleがない: {href}")
            return 1
        changed += int(sync_page(path, title))
    print(f"検索需要タイトル同期: {len(PRIORITY_HREFS)}ページ（更新 {changed}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
