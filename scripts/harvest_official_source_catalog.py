#!/usr/bin/env python3
"""Build a resumable metadata catalog of Mori Town's official sitemap pages.

The catalog intentionally stores discovery metadata rather than copied article
text.  It is a research queue: a page still needs source reading, purpose
screening, independent writing, and the normal publication gates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_SITEMAP = "https://www.town.morimachi.shizuoka.jp/sitemap.xml"
OFFICIAL_HOST = urllib.parse.urlsplit(OFFICIAL_SITEMAP).netloc
OUTPUT = ROOT / "data" / "official-source-catalog.json"
USER_AGENT = "MorimachiSourceCatalog/1.0 (+https://morimachi.enshu-lifehack.com/)"


def canonical_official_url(url: str) -> str:
    """Normalize legacy HTTP sitemap entries to the official HTTPS origin."""
    parsed = urllib.parse.urlsplit(url)
    if parsed.netloc != OFFICIAL_HOST:
        return url
    return urllib.parse.urlunsplit(("https", OFFICIAL_HOST, parsed.path, parsed.query, ""))


class PageMetadataParser(HTMLParser):
    SKIP = {"script", "style", "noscript", "template", "svg"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.title_depth = 0
        self.heading_depth = 0
        self.title_parts: list[str] = []
        self.heading_parts: list[str] = []
        self.headings: list[str] = []
        self.visible_parts: list[str] = []
        self.canonical = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        name = tag.lower()
        attr_map = {key.lower(): value or "" for key, value in attrs}
        if name in self.SKIP:
            self.skip_depth += 1
        if name == "title":
            self.title_depth += 1
        if name in {"h1", "h2", "h3"}:
            self.heading_depth += 1
            self.heading_parts = []
        if name == "link" and "canonical" in attr_map.get("rel", "").lower():
            self.canonical = attr_map.get("href", "").strip()

    def handle_endtag(self, tag: str) -> None:
        name = tag.lower()
        if name in self.SKIP and self.skip_depth:
            self.skip_depth -= 1
        if name == "title" and self.title_depth:
            self.title_depth -= 1
        if name in {"h1", "h2", "h3"} and self.heading_depth:
            heading = re.sub(r"\s+", " ", "".join(self.heading_parts)).strip()
            if heading and heading not in self.headings:
                self.headings.append(heading)
            self.heading_depth -= 1
            self.heading_parts = []

    def handle_data(self, data: str) -> None:
        if self.title_depth:
            self.title_parts.append(data)
        if self.heading_depth:
            self.heading_parts.append(data)
        if not self.skip_depth:
            self.visible_parts.append(data)

    def metadata(self) -> dict:
        visible = re.sub(r"\s+", "", "".join(self.visible_parts))
        return {
            "title": re.sub(r"\s+", " ", "".join(self.title_parts)).strip(),
            "headings": self.headings[:24],
            "canonical": self.canonical,
            "visible_chars": len(visible),
            "visible_sha256": hashlib.sha256(visible.encode("utf-8")).hexdigest(),
        }


def fetch_bytes(url: str, timeout: int = 30) -> tuple[bytes, str, int, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return (
            response.read(),
            response.headers.get_content_type(),
            int(response.status),
            response.geturl(),
        )


def sitemap_entries(payload: bytes) -> tuple[str, list[dict]]:
    root = ET.fromstring(payload)
    kind = root.tag.rsplit("}", 1)[-1]
    entries: list[dict] = []
    for node in list(root):
        values: dict[str, str] = {}
        for child in list(node):
            values[child.tag.rsplit("}", 1)[-1]] = (child.text or "").strip()
        if values.get("loc"):
            entries.append(values)
    return kind, entries


def discover_sitemap() -> dict[str, str]:
    pending = [OFFICIAL_SITEMAP]
    visited: set[str] = set()
    pages: dict[str, str] = {}
    while pending:
        url = pending.pop(0)
        if url in visited:
            continue
        visited.add(url)
        payload, _content_type, status, _final_url = fetch_bytes(url)
        if status != 200:
            raise RuntimeError(f"サイトマップ取得失敗: {status} {url}")
        kind, entries = sitemap_entries(payload)
        if kind == "sitemapindex":
            for entry in entries:
                child = canonical_official_url(entry["loc"])
                if urllib.parse.urlsplit(child).netloc != OFFICIAL_HOST:
                    raise RuntimeError(f"外部子サイトマップです: {child}")
                pending.append(child)
        elif kind == "urlset":
            for entry in entries:
                page_url = canonical_official_url(entry["loc"])
                if urllib.parse.urlsplit(page_url).netloc != OFFICIAL_HOST:
                    continue
                pages[page_url] = entry.get("lastmod", "")
        else:
            raise RuntimeError(f"未知のサイトマップ形式: {kind} {url}")
    return pages


def fetch_metadata(url: str) -> tuple[str, dict]:
    checked_at = datetime.now(ZoneInfo("Asia/Tokyo")).date().isoformat()
    try:
        payload, content_type, status, final_url = fetch_bytes(url)
        record: dict = {
            "status": f"http-{status}",
            "checked_at": checked_at,
            "content_type": content_type,
            "final_url": final_url,
            "payload_bytes": len(payload),
            "payload_sha256": hashlib.sha256(payload).hexdigest(),
        }
        if content_type in {"text/html", "application/xhtml+xml"}:
            parser = PageMetadataParser()
            parser.feed(payload.decode("utf-8", errors="replace"))
            record.update(parser.metadata())
        return url, record
    except Exception as exc:  # keep the queue resumable; failure stays explicit
        return url, {
            "status": "fetch-error",
            "checked_at": checked_at,
            "error": f"{type(exc).__name__}: {exc}",
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if args.limit < 1 or args.workers < 1 or args.workers > 12:
        raise SystemExit("--limit は1以上、--workers は1-12で指定してください")

    sitemap = discover_sitemap()
    existing: dict[str, dict] = {}
    if args.output.is_file():
        document = json.loads(args.output.read_text(encoding="utf-8"))
        existing = {
            canonical_official_url(row["url"]): {**row, "url": canonical_official_url(row["url"])}
            for row in document.get("sources", [])
        }

    rows: dict[str, dict] = {}
    for url, lastmod in sorted(sitemap.items()):
        previous = existing.get(url, {})
        rows[url] = {
            "url": url,
            "sitemap_lastmod": lastmod,
            "status": previous.get("status", "pending"),
            **{key: value for key, value in previous.items() if key not in {"url", "sitemap_lastmod", "status"}},
        }

    queue = [
        url for url, row in rows.items()
        if args.refresh or row.get("status") in {None, "", "pending", "fetch-error"}
    ][: args.limit]
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(fetch_metadata, url): url for url in queue}
        for future in as_completed(futures):
            url, metadata = future.result()
            rows[url].update(metadata)

    counts: dict[str, int] = {}
    for row in rows.values():
        status = str(row.get("status", "pending"))
        counts[status] = counts.get(status, 0) + 1
    document = {
        "generated_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(timespec="seconds"),
        "source_sitemap": OFFICIAL_SITEMAP,
        "total_urls": len(rows),
        "fetched_this_run": len(queue),
        "status_counts": dict(sorted(counts.items())),
        "sources": list(rows.values()),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: document[key] for key in ("total_urls", "fetched_this_run", "status_counts")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
