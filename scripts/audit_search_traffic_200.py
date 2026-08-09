#!/usr/bin/env python3
"""Audit the 200-query search expansion against the generated static site."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from html import unescape
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://morimachi.enshu-lifehack.com"
DECISIONS = ROOT / "data" / "search-intent-200-decisions.json"
SITEMAP = ROOT / "sitemap.xml"


def html_path(url: str) -> Path:
    path = urlparse(url).path if url.startswith("http") else url
    return ROOT / path.strip("/") / "index.html"


def text_content(source: str) -> str:
    source = re.sub(r"<script\b.*?</script>|<style\b.*?</style>", " ", source, flags=re.I | re.S)
    source = re.sub(r"<[^>]+>", " ", source)
    return re.sub(r"\s+", " ", unescape(source)).strip()


def one(source: str, pattern: str) -> str:
    match = re.search(pattern, source, flags=re.I | re.S)
    return unescape(match.group(1)).strip() if match else ""


def internal_links(source: str) -> set[str]:
    result: set[str] = set()
    for href in re.findall(r'<a\b[^>]*href=["\']([^"\']+)', source, flags=re.I):
        if href.startswith(ORIGIN):
            href = urlparse(href).path
        if href.startswith("/") and not href.startswith("//"):
            path = href.split("#", 1)[0].split("?", 1)[0]
            if path.endswith("/"):
                result.add(path)
    return result


def main() -> int:
    failures: list[str] = []
    decisions = json.loads(DECISIONS.read_text(encoding="utf-8"))
    if len(decisions) != 200:
        failures.append(f"decision count: expected 200, got {len(decisions)}")
    if {item["number"] for item in decisions} != set(range(1, 201)):
        failures.append("candidate numbers are not exactly 1..200")

    counts = Counter(item["action"] for item in decisions)
    target_urls = sorted({item["final_url"] for item in decisions})
    sitemap_urls = set(re.findall(r"<loc>(.*?)</loc>", SITEMAP.read_text(encoding="utf-8")))
    page_sources: dict[str, str] = {}

    for url in target_urls:
        page = html_path(url)
        if not page.exists():
            failures.append(f"missing target page: {url}")
            continue
        source = page.read_text(encoding="utf-8")
        page_sources[url] = source
        title = one(source, r"<title>(.*?)</title>")
        description = one(source, r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']')
        canonical = one(source, r'<link\s+rel=["\']canonical["\']\s+href=["\'](.*?)["\']')
        h1s = re.findall(r"<h1\b[^>]*>(.*?)</h1>", source, flags=re.I | re.S)
        if not title:
            failures.append(f"missing title: {url}")
        if url.startswith("/life/") and not (90 <= len(description) <= 130):
            failures.append(f"description length {len(description)} (expected 90..130): {url}")
        if canonical != ORIGIN + url:
            failures.append(f"canonical mismatch: {url} -> {canonical}")
        if len(h1s) != 1 or not text_content(h1s[0]):
            failures.append(f"expected one non-empty h1: {url}")
        if re.search(r'<meta\s+name=["\']robots["\'][^>]*noindex', source, flags=re.I):
            failures.append(f"noindex target: {url}")
        if ORIGIN + url not in sitemap_urls:
            failures.append(f"target missing from sitemap: {url}")

    # Every candidate phrase (minus the location prefix) must be visibly represented.
    for item in decisions:
        url = item["final_url"]
        if url not in page_sources:
            continue
        expected = item["target_query"].removeprefix("森町 ").strip()
        visible = text_content(page_sources[url])
        tokens = [token for token in expected.split() if token]
        if not all(token in visible for token in tokens):
            failures.append(f"query #{item['number']} not visible on {url}: {expected}")

    # New pages must provide at least three useful outgoing links and receive three entrances.
    create_urls = {item["final_url"] for item in decisions if item["action"] == "CREATE"}
    all_html = list(ROOT.rglob("index.html"))
    incoming: defaultdict[str, set[str]] = defaultdict(set)
    for page in all_html:
        try:
            source = page.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = page.parent.relative_to(ROOT).as_posix()
        source_url = "/" if rel == "." else f"/{rel}/"
        for target in internal_links(source):
            incoming[target].add(source_url)
    for url in sorted(create_urls):
        outgoing = internal_links(page_sources.get(url, "")) - {url}
        sources = incoming[url] - {url}
        if len(outgoing) < 3:
            failures.append(f"new page has {len(outgoing)} outgoing links: {url}")
        if len(sources) < 3:
            failures.append(f"new page has {len(sources)} incoming links: {url}")

    duplicate_titles: defaultdict[str, list[str]] = defaultdict(list)
    for url, source in page_sources.items():
        duplicate_titles[one(source, r"<title>(.*?)</title>")].append(url)
    for title, urls in duplicate_titles.items():
        if title and len(urls) > 1:
            failures.append(f"duplicate target title: {title} ({', '.join(urls)})")

    print(f"decisions={len(decisions)} actions={dict(sorted(counts.items()))}")
    print(f"target_urls={len(target_urls)} create_urls={len(create_urls)} sitemap_urls={len(sitemap_urls)}")
    if failures:
        print(f"FAIL ({len(failures)})")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("PASS: all 200 decisions resolve to valid, indexable, internally linked pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
