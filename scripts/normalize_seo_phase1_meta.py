#!/usr/bin/env python3
"""Normalize canonical and social metadata on the reviewed phase-1 pages."""
from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://morimachi.enshu-lifehack.com"
START, END = "<!-- PHASE1-SEO-META:START -->", "<!-- PHASE1-SEO-META:END -->"


def page_path(url: str) -> Path:
    return ROOT / url.strip("/") / "index.html"


def esc(value: str) -> str:
    return value.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def fit_description(value: str) -> str:
    if len(value) <= 130:
        return value
    candidates = [match.end() for match in re.finditer("。", value[:131]) if match.end() >= 80]
    if candidates:
        return value[: candidates[-1]]
    return value[:129].rstrip("、。 ") + "。"


def image_for(url: str, source: str) -> str:
    parts = url.strip("/").split("/")
    if parts and parts[0] == "life":
        category = parts[1]
        slug = "-".join(parts[2:]) if len(parts) > 2 else "index"
        candidate = ROOT / "assets" / "ogp" / category / f"{slug}.png"
        if candidate.exists():
            return f"{SITE}/assets/ogp/{category}/{slug}.png"
    cover = re.search(r'<img\b[^>]+src="([^"]+\.(?:png|jpe?g|webp))"', source, re.I)
    if cover:
        ref = cover.group(1)
        if ref.startswith("http"):
            return ref
        if ref.startswith("/"):
            return SITE + ref
        return SITE + url + ref
    return SITE + "/assets/ogp/site-default.png"


def main() -> None:
    manifest = json.loads((ROOT / "data" / "seo-phase1-publication.json").read_text(encoding="utf-8"))
    changed = 0
    for row in manifest:
        url = row["url"]
        path = page_path(url)
        source = original = path.read_text(encoding="utf-8")
        preferred_title = row.get("proposed_title_h1", "").strip()
        if preferred_title:
            source = re.sub(
                r"<title>.*?</title>",
                f"<title>{esc(preferred_title)} | 森町ライフハック</title>",
                source,
                count=1,
                flags=re.S | re.I,
            )
            def replace_h1(match: re.Match[str]) -> str:
                inner = match.group(2)
                icon = re.match(r"\s*(<span\b[^>]*aria-hidden=\"true\"[^>]*>.*?</span>)", inner, re.S | re.I)
                prefix = icon.group(1) + " " if icon else ""
                return match.group(1) + prefix + esc(preferred_title) + match.group(3)
            source = re.sub(r"(<h1\b[^>]*>)(.*?)(</h1>)", replace_h1, source, count=1, flags=re.S | re.I)
        title_m = re.search(r"<title>(.*?)</title>", source, re.S | re.I)
        desc_m = re.search(r'<meta\s+name="description"\s+content="(.*?)">', source, re.S | re.I)
        title = unescape(re.sub(r"<[^>]+>", "", title_m.group(1))).split(" | ")[0].strip()
        desc = fit_description(unescape(desc_m.group(1)).strip())
        source = re.sub(
            r'(<meta\s+name="description"\s+content=").*?(\">)',
            lambda m: m.group(1) + esc(desc) + m.group(2),
            source,
            count=1,
            flags=re.S | re.I,
        )
        image = image_for(url, source)

        source = re.sub(re.escape(START) + r".*?" + re.escape(END), "", source, flags=re.S)
        source = re.sub(r"<!-- OGP-META:START -->.*?<!-- OGP-META:END -->", "", source, flags=re.S)
        source = re.sub(r'<meta\s+(?:property="og:[^"]+"|name="twitter:[^"]+")[^>]*>', "", source, flags=re.I)
        source = re.sub(r'<link\s+rel="canonical"[^>]*>', "", source, flags=re.I)
        block = START + "".join([
            '<meta property="og:type" content="website">',
            '<meta property="og:site_name" content="森町ライフハック">',
            '<meta property="og:locale" content="ja_JP">',
            f'<meta property="og:title" content="{esc(title)}">',
            f'<meta property="og:description" content="{esc(desc)}">',
            f'<meta property="og:url" content="{SITE}{url}">',
            f'<meta property="og:image" content="{image}">',
            '<meta name="twitter:card" content="summary_large_image">',
            f'<meta name="twitter:title" content="{esc(title)}">',
            f'<meta name="twitter:description" content="{esc(desc)}">',
            f'<meta name="twitter:image" content="{image}">',
            f'<link rel="canonical" href="{SITE}{url}">',
        ]) + END
        source = source.replace("</head>", block + "</head>", 1)
        if source != original:
            path.write_text(source, encoding="utf-8")
            changed += 1
    print(f"phase1 canonical/OGP normalized: {changed}/{len(manifest)}")


if __name__ == "__main__":
    main()
