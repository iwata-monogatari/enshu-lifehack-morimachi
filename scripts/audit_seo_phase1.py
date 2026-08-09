#!/usr/bin/env python3
"""Quality gate for the reviewed phase-1 pages in the 200-page plan."""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from html import unescape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://morimachi.enshu-lifehack.com"
MIN_CHARS = 6000


def page_path(url: str) -> Path:
    return ROOT / url.strip("/") / "index.html"


def strip_html(fragment: str) -> str:
    fragment = re.sub(r"<!--.*?-->|<script\b.*?</script>|<style\b.*?</style>", "", fragment, flags=re.I | re.S)
    return re.sub(r"\s+", "", unescape(re.sub(r"<[^>]+>", "", fragment)))


def one(source: str, pattern: str) -> str:
    match = re.search(pattern, source, flags=re.I | re.S)
    return unescape(match.group(1)).strip() if match else ""


def main() -> int:
    manifest = json.loads((ROOT / "data" / "seo-phase1-publication.json").read_text(encoding="utf-8"))
    failures: list[str] = []
    titles: dict[str, str] = {}
    descriptions: dict[str, str] = {}
    passed = 0
    for item in manifest:
        url = item["url"]
        path = page_path(url)
        if not path.exists():
            failures.append(f"missing phase1 page: #{item['id']} {url}")
            continue
        source = path.read_text(encoding="utf-8")
        main_html = one(source, r"<main\b[^>]*>(.*?)</main>")
        chars = len(strip_html(main_html))
        title = one(source, r"<title>(.*?)</title>")
        description = one(source, r'<meta\s+name="description"\s+content="(.*?)">')
        h1s = re.findall(r"<h1\b[^>]*>(.*?)</h1>", source, flags=re.I | re.S)
        h2_count = len(re.findall(r"<h2\b", main_html, flags=re.I))
        internal = {href.split("#", 1)[0] for href in re.findall(r'href="(/[^"]+)', main_html) if href != url}
        official = set(re.findall(
            r'href="(https://(?:www\.)?(?:town\.morimachi\.shizuoka\.jp|hospital\.town\.morimachi\.shizuoka\.jp|mori-kanko\.jp|tenhama\.co\.jp|okunijinja\.or\.jp|pref\.shizuoka\.jp|bunka\.go\.jp|actymori\.jp)/[^"]+)',
            source,
            flags=re.I,
        ))
        faq_questions = max(
            len(re.findall(r'<(?:h3|summary)\b[^>]*>[\s\S]*?(?:\?|？)[\s\S]*?</(?:h3|summary)>', main_html, flags=re.I)),
            len(re.findall(r'"@type"\s*:\s*"Question"', source, flags=re.I)),
        )
        jsonld_text = " ".join(re.findall(r'<script\s+type="application/ld\+json">(.*?)</script>', source, flags=re.I | re.S))
        breadcrumb_count = len(re.findall(r'"@type"\s*:\s*"BreadcrumbList"', jsonld_text))
        visual_refs = set(re.findall(
            r'(?:src|href)="([^"]+\.(?:svg|png|jpe?g|webp))"', main_html, flags=re.I
        ))
        svg_refs = {ref for ref in visual_refs if ref.lower().endswith(".svg")}

        if chars < MIN_CHARS:
            failures.append(f"#{item['id']} chars {chars} < {MIN_CHARS}: {url}")
        if not (7 <= h2_count <= 12):
            failures.append(f"#{item['id']} h2 count {h2_count} outside 7..12: {url}")
        if len(h1s) != 1:
            failures.append(f"#{item['id']} h1 count {len(h1s)}: {url}")
        if not (80 <= len(description) <= 130):
            failures.append(f"#{item['id']} description length {len(description)} outside 80..130: {url}")
        if one(source, r'<link\s+rel="canonical"\s+href="(.*?)">') != SITE + url:
            failures.append(f"#{item['id']} canonical mismatch: {url}")
        if len(re.findall(r'<link\s+rel="canonical"', source, flags=re.I)) != 1:
            failures.append(f"#{item['id']} canonical count is not 1: {url}")
        for prop in ("og:title", "og:description", "og:url", "og:image"):
            if len(re.findall(rf'<meta\s+property="{re.escape(prop)}"', source, flags=re.I)) != 1:
                failures.append(f"#{item['id']} {prop} count is not 1: {url}")
        if len(internal) < 5:
            failures.append(f"#{item['id']} internal links {len(internal)} < 5: {url}")
        if len(official) < 2:
            failures.append(f"#{item['id']} official sources {len(official)} < 2: {url}")
        if faq_questions < 3:
            failures.append(f"#{item['id']} FAQ questions {faq_questions} < 3: {url}")
        has_page_type = "WebPage" in jsonld_text or "Article" in jsonld_text
        if not has_page_type or not all(value in jsonld_text for value in ("BreadcrumbList", "FAQPage")):
            failures.append(f"#{item['id']} missing required JSON-LD types: {url}")
        if breadcrumb_count != 1:
            failures.append(f"#{item['id']} BreadcrumbList count {breadcrumb_count} != 1: {url}")
        if len(visual_refs) < 3:
            failures.append(f"#{item['id']} figures {len(visual_refs)} < 3: {url}")
        for ref in svg_refs:
            svg_path = ROOT / ref.lstrip("/") if ref.startswith("/") else path.parent / ref
            if not svg_path.exists():
                failures.append(f"#{item['id']} missing SVG asset {ref}: {url}")
                continue
            svg = svg_path.read_text(encoding="utf-8")
            if 'data-illustration="mori-editorial"' not in svg:
                failures.append(f"#{item['id']} missing illustration marker {ref}: {url}")
            try:
                ET.fromstring(svg)
            except ET.ParseError as exc:
                failures.append(f"#{item['id']} invalid SVG {ref}: {exc}")
        if title in titles:
            failures.append(f"duplicate phase1 title: {url} and {titles[title]}")
        if description in descriptions:
            failures.append(f"duplicate phase1 description: {url} and {descriptions[description]}")
        titles[title] = url
        descriptions[description] = url
        passed += 1
        print(f"CHECK #{item['id']:03d} chars={chars} h2={h2_count} figures={len(visual_refs)} internal={len(internal)} official={len(official)} {url}")

    print(f"SUMMARY checked={passed}/{len(manifest)} failures={len(failures)}")
    for failure in failures:
        print(f"FAIL {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
