# -*- coding: utf-8 -*-
"""重要11ページ・5機能・100質問の検索発見基盤を検査する。"""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://morimachi.enshu-lifehack.com"
EXPECTED_DATE = "2026-08-06"
TOOLS = {
    "/life/start-living/how-to-garbage/": "data-garbage-tool",
    "/life/family-grow/nursery-school/": "data-nursery-tool",
    "/life/start-living/water-sewer/": "data-water-tool",
    "/life/education/school-zones/": "data-school-tool",
    "/life/work-life/subsidies/": "data-migration-tool",
}


def page(href: str) -> Path:
    return ROOT / href.strip("/") / "index.html"


def main() -> None:
    errors: list[str] = []
    priority = json.loads(
        (ROOT / "data" / "search-priority-pages.json").read_text(encoding="utf-8"))
    questions = json.loads((ROOT / "data" / "questions.json").read_text(encoding="utf-8"))
    topics = json.loads((ROOT / "data" / "topics_master.json").read_text(encoding="utf-8"))
    home = (ROOT / "index.html").read_text(encoding="utf-8")

    if len(priority) != 11:
        errors.append(f"重要ページ数が11ではない: {len(priority)}")
    for item in priority:
        href = item["href"]
        html = page(href).read_text(encoding="utf-8")
        if f'href="{href}"' not in home:
            errors.append(f"トップから直接リンクなし: {href}")
        if f"最終確認日：{EXPECTED_DATE}" not in html:
            errors.append(f"画面の最終確認日が不一致: {href}")
        if f'"dateModified":"{EXPECTED_DATE}"' not in html:
            errors.append(f"dateModifiedが不一致: {href}")
        cluster = re.search(
            r"<!-- PRIORITY-QUESTIONS:START -->(.*?)<!-- PRIORITY-QUESTIONS:END -->",
            html, re.S)
        if not cluster or len(re.findall(r'href="/questions/', cluster.group(1))) < 5:
            errors.append(f"関連質問が5件未満: {href}")

    for href, marker in TOOLS.items():
        html = page(href).read_text(encoding="utf-8")
        if marker not in html or "/assets/search-tools.mjs" not in html:
            errors.append(f"検索支援機能が未反映: {href}")

    if len(questions) != 100:
        errors.append(f"質問数が100ではない: {len(questions)}")
    pending = [row["href"] for row in questions if row.get("verified_date") == "確認中"]
    if pending:
        errors.append(f"確認中の質問が残存: {pending}")

    question_html = "".join(
        page(row["href"]).read_text(encoding="utf-8") for row in questions)
    for item in priority:
        inbound = question_html.count(f'href="{item["href"]}"')
        if inbound < 3:
            errors.append(f"質問からの重要ガイドリンクが3本未満: {item['href']} ({inbound})")

    root = ET.parse(ROOT / "sitemap.xml").getroot()
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap = {
        node.findtext("s:loc", namespaces=ns): node.findtext("s:lastmod", namespaces=ns)
        for node in root.findall("s:url", ns)
    }
    for item in priority:
        url = SITE + item["href"]
        if sitemap.get(url) != EXPECTED_DATE:
            errors.append(f"sitemap lastmodが不一致: {item['href']} ({sitemap.get(url)})")

    redirects = {
        tuple(line.split()[:3])
        for line in (ROOT / "_redirects").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#") and len(line.split()) >= 3
    }
    merge_rows = [row for row in topics if row.get("action") == "merge"]
    for row in merge_rows:
        href, target = row["href"], row.get("merge_target", "")
        if (href, target, "301") not in redirects:
            errors.append(f"統合ページの301不足: {href}")
        if SITE + href in sitemap:
            errors.append(f"301統合元がsitemapに残存: {href}")

    print(f"重要ページ: {len(priority)} / 検索支援機能: {len(TOOLS)} / 質問: {len(questions)}")
    print(f"既存の重複URL統合: {len(merge_rows)}件")
    if errors:
        for error in errors:
            print("[NG] " + error)
        sys.exit(1)
    print("検索発見基盤の監査: 合格")


if __name__ == "__main__":
    main()
