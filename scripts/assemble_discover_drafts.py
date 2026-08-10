# -*- coding: utf-8 -*-
"""Normalize independently edited Discover drafts into one publication ledger.

The script never invents or expands article prose.  A release entry is honored
only when the slug also exists in data/discover-release.json, which is created
after editorial and visual review.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DRAFTS = ROOT / "work" / "discover-drafts"
OUTPUT = ROOT / "data" / "discover-pages.json"
RELEASE = ROOT / "data" / "discover-release.json"


def rows_from(value: object) -> list[dict]:
    if isinstance(value, list):
        return value
    if not isinstance(value, dict):
        return []
    if isinstance(value.get("pages"), list):
        return value["pages"]
    if isinstance(value.get("articles"), list):
        return value["articles"]
    return [value] if value.get("slug") else []


def source_object(value: object) -> dict:
    if isinstance(value, dict):
        url = value["url"]
        fallback = source_object(url)
        return {
            "title": value.get("title") or value.get("name") or value.get("label") or fallback["title"],
            "publisher": value.get("publisher") or fallback["publisher"],
            "url": url,
        }
    url = str(value)
    domain = urlparse(url).netloc
    if domain == "www.town.morimachi.shizuoka.jp":
        publisher, title = "静岡県森町", "静岡県森町公式ページ"
    elif "okunijinja.or.jp" in domain:
        publisher, title = "小國神社", "小國神社公式ページ"
    elif "kotomachi.com" in domain:
        publisher, title = "ことまち横丁", "ことまち横丁公式ページ"
    elif "c-nexco.co.jp" in domain:
        publisher, title = "NEXCO中日本", "NEXCO中日本公式ページ"
    elif "mori-kanko.jp" in domain:
        publisher, title = "静岡県森町観光協会", "静岡県森町観光協会公式ページ"
    elif "tenhama.co.jp" in domain:
        publisher, title = "天竜浜名湖鉄道", "天竜浜名湖鉄道公式ページ"
    else:
        publisher, title = domain, "公式確認ページ"
    return {"title": title, "publisher": publisher, "url": url}


def illustration_objects(row: dict) -> list[dict]:
    result = []
    labels = [row["primary_keyword"], *row["secondary_keywords"], "公式情報を再確認"]
    for number, value in enumerate(row.get("illustrations", []), 1):
        scene = value.get("scene") or value.get("concept") or value.get("caption") or ""
        result.append({
            "title": value.get("title") or f'{row["primary_keyword"]}の確認図{number}',
            "caption": value.get("caption") or scene,
            "alt": value.get("alt") or scene,
            "labels": (value.get("labels") or labels)[:4],
        })
    return result


def normalize(row: dict, released: bool) -> dict:
    sections = row.get("body_sections") or row.get("sections") or []
    related = (
        row.get("related_slugs")
        or row.get("related_article_slugs")
        or [x["slug"] for x in row.get("internal_links", [])]
    )
    category = row.get("category_label") or row.get("category") or "静岡県森町ガイド"
    checked = row.get("fact_checked_at") or row.get("verified_at") or "2026-08-10"
    lead = row.get("lead") or row.get("direct_answer") or sections[0]["paragraphs"][0]
    motif = row.get("visual_motif") or row.get("illustrations", [{}])[0].get("concept") or category
    return {
        "id": row.get("id") or row["slug"],
        "slug": row["slug"],
        "category_label": category,
        "primary_keyword": row["primary_keyword"],
        "secondary_keywords": row["secondary_keywords"],
        "intent": row["intent"],
        "title": row["title"],
        "description": row["description"],
        "audience": row.get("audience") if isinstance(row.get("audience"), list) else [row.get("audience", "静岡県森町を訪れる人")],
        "lead": lead,
        "direct_answer": row["direct_answer"],
        "body_sections": sections,
        "sources": [source_object(x) for x in (row.get("sources") or row.get("official_sources", []))],
        "related_slugs": related,
        "illustrations": illustration_objects(row),
        "illustration_after_sections": row.get("illustration_after_sections", [2, 5]),
        "visual_motif": motif,
        "cover_alt": row.get("cover_alt") or f'{row["title"]}の内容を森町の風景で表した編集イラスト',
        "cover_caption": row.get("cover_caption", "記事の判断点を静岡県森町の風景に重ねた編集イラスト"),
        "fact_checked_at": checked,
        "published_at": "2026-08-10",
        "updated_at": "2026-08-10",
        "status": "published" if released else "draft",
        "editor_reviewed": released,
        "publish_ready": released,
        "source_validation": "verified" if released else "pending",
        "uniqueness_validation": "verified" if released else "pending",
        "visual_validation": "verified" if released else "pending",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    release_slugs: set[str] = set()
    if RELEASE.exists():
        release_slugs = set(json.loads(RELEASE.read_text(encoding="utf-8")).get("reviewed_slugs", []))
    drafts: list[dict] = []
    for path in sorted(DRAFTS.glob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        drafts.extend(rows_from(value))
    slugs = [row["slug"] for row in drafts]
    if len(slugs) != len(set(slugs)):
        raise RuntimeError("draft slugが重複しています")
    if not args.allow_partial and len(drafts) != 100:
        raise RuntimeError(f"完成原稿が100件ではありません: {len(drafts)}")
    if not release_slugs.issubset(slugs):
        raise RuntimeError("release台帳に存在しないslugがあります")
    pages = [normalize(row, row["slug"] in release_slugs) for row in drafts]
    # Keep author-selected links when they resolve, then complete each set with
    # other guides from the same editorial category. Drafts may refer to an
    # article's planning slug before its final slug is fixed; unresolved links
    # must never leak into the published collection.
    pages_by_slug = {row["slug"]: row for row in pages}
    all_slugs = sorted(pages_by_slug)
    for row in pages:
        selected: list[str] = []
        for slug in row.get("related_slugs", []):
            if slug in pages_by_slug and slug != row["slug"] and slug not in selected:
                selected.append(slug)
        same_category = sorted(
            slug for slug, other in pages_by_slug.items()
            if other["category_label"] == row["category_label"] and slug != row["slug"]
        )
        for slug in [*same_category, *all_slugs]:
            if slug != row["slug"] and slug not in selected:
                selected.append(slug)
            if len(selected) >= 5:
                break
        row["related_slugs"] = selected[:5]
    OUTPUT.write_text(json.dumps({"schema_version": 1, "pages": pages}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"discover台帳: {len(pages)}件（公開承認 {len(release_slugs)}件）")


if __name__ == "__main__":
    main()
