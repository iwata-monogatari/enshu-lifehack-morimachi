# -*- coding: utf-8 -*-
"""Fail closed quality audit for the 200 Discover guides."""
from __future__ import annotations

import json
import argparse
import re
import sys
from datetime import date
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "discover-pages.json"
BANNED = (
    "placeholder", "lorem ipsum", "架空の体験", "undefined",
    "本稿で扱う中心は", "これが本稿の結論です", "固有の角度から",
    # The second 100 planning drafts originally contained these mechanically
    # inflected stock phrases.  They are blocked even in --allow-pending mode
    # so a numerically complete but unreadable batch cannot pass again.
    "を確認する人へ", "を進める場合", "について家族で共有する際は",
    "一枚につなぐための実用ガイド", "同じ答えで済ませず",
)
TITLE_PREFIX = ("静岡県森町", "静岡県周智郡森町", "遠州森町")
MIN_CHARS = 5000
MIN_PARAGRAPHS = 35


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-pending", action="store_true", help="本文監査用。公開フラグとnoindexだけを許容する")
    args = parser.parse_args()
    data = json.loads(DATA.read_text(encoding="utf-8"))
    rows = data.get("pages", [])
    errors: list[str] = []
    if len(rows) != 200:
        fail(errors, f"台帳は200件必須です: {len(rows)}")
    slugs = [row.get("slug") for row in rows]
    if len(set(slugs)) != len(slugs):
        fail(errors, "slugが重複しています")
    all_keywords: list[str] = []
    paragraph_owners: dict[str, list[str]] = {}
    paragraph_prefixes: dict[str, set[str]] = {}
    title_starts = Counter()
    for row in rows:
        slug = row.get("slug", "(no-slug)")
        prefix = f"[{slug}]"
        title = row.get("title", "")
        if not title.startswith(TITLE_PREFIX):
            fail(errors, f"{prefix} titleは静岡県森町等で始めてください")
        title_starts[title[:18]] += 1
        description = compact(row.get("description", ""))
        if not 70 <= len(description) <= 135:
            fail(errors, f"{prefix} descriptionは70〜135字: {len(description)}")
        keywords = [row.get("primary_keyword", ""), *row.get("secondary_keywords", [])]
        if len(keywords) != 3 or any(not x for x in keywords):
            fail(errors, f"{prefix} キーワードは主1＋副2の3語必須")
        all_keywords.extend(keywords)
        if slug.startswith("guide-") and not args.allow_pending:
            if row.get("editorial_rewrite_complete") is not True:
                fail(errors, f"{prefix} 人手による全面改稿の完了記録がありません")
        if not args.allow_pending and (row.get("editor_reviewed") is not True or row.get("publish_ready") is not True):
            fail(errors, f"{prefix} 編集確認・公開可フラグが未完了")
        for gate in ("source_validation", "uniqueness_validation", "visual_validation"):
            if not args.allow_pending and row.get(gate) != "verified":
                fail(errors, f"{prefix} {gate}がverifiedではありません")
        sections = row.get("body_sections", [])
        headings = [x.get("heading", "") for x in sections]
        required_heading_groups = (
            ("良い点",), ("注文したい点",), ("代案・結論", "対案・結論"), ("大石の視点",),
        )
        for alternatives in required_heading_groups:
            if not any(any(required in h for required in alternatives) for h in headings):
                fail(errors, f"{prefix} 必須見出しがありません: {' / '.join(alternatives)}")
        paragraphs = [compact(p) for s in sections for p in s.get("paragraphs", []) if compact(p)]
        if len(paragraphs) < MIN_PARAGRAPHS:
            fail(errors, f"{prefix} 段落不足: {len(paragraphs)}")
        chars = sum(len(p) for p in paragraphs)
        if chars < MIN_CHARS:
            fail(errors, f"{prefix} 本文不足: {chars}字")
        for paragraph in paragraphs:
            if len(paragraph) >= 35:
                paragraph_owners.setdefault(paragraph, []).append(slug)
                paragraph_prefixes.setdefault(paragraph[:28], set()).add(slug)
        sources = row.get("sources", [])
        town_urls = {s.get("url") for s in sources if "www.town.morimachi.shizuoka.jp" in s.get("url", "")}
        if len(town_urls) < 2:
            fail(errors, f"{prefix} 内容の異なる森町公式URLが2件未満")
        if len({s.get("url") for s in sources}) != len(sources):
            fail(errors, f"{prefix} 出典URLが重複")
        if len(row.get("related_slugs", [])) < 5:
            fail(errors, f"{prefix} 関連記事は5件以上必須")
        if any(x == slug or x not in slugs for x in row.get("related_slugs", [])):
            fail(errors, f"{prefix} 関連slugに自己参照または不明値")
        if len(row.get("illustrations", [])) != 2:
            fail(errors, f"{prefix} 図解指定は2点必須")
        page = ROOT / "discover" / slug
        html_path = page / "index.html"
        if not html_path.exists():
            fail(errors, f"{prefix} index.htmlがありません")
            continue
        source = html_path.read_text(encoding="utf-8")
        if not args.allow_pending and ("data-discover-pending" in source or re.search(r'<meta[^>]+name="robots"[^>]+noindex', source, re.I)):
            fail(errors, f"{prefix} 公開記事にnoindexがあります")
        if len(re.findall(r"<h1[ >]", source)) != 1:
            fail(errors, f"{prefix} H1は1つ必須")
        if f'<h1>{title}</h1>' not in source:
            fail(errors, f"{prefix} H1と台帳titleが不一致")
        for filename in ("cover.svg", "fig1.svg", "fig2.svg"):
            asset = page / filename
            if not asset.exists():
                fail(errors, f"{prefix} {filename}がありません")
                continue
            try:
                ET.parse(asset)
            except ET.ParseError as exc:
                fail(errors, f"{prefix} {filename} XML不正: {exc}")
        for filename in ("fig1.svg", "fig2.svg"):
            asset = page / filename
            if asset.exists() and 'data-illustration="mori-editorial"' not in asset.read_text(encoding="utf-8"):
                fail(errors, f"{prefix} {filename} 固有図解markerなし")
        editorial_fields = {
            "title": row.get("title", ""),
            "description": row.get("description", ""),
            "lead": row.get("lead", ""),
            "direct_answer": row.get("direct_answer", ""),
            "category_label": row.get("category_label", ""),
            "cover_alt": row.get("cover_alt", ""),
            "body_sections": row.get("body_sections", []),
            "illustrations": row.get("illustrations", []),
            "source_titles": [s.get("title", "") for s in row.get("sources", [])],
        }
        # URL中の文字列（例: *todoke*）をTODOと誤判定しない。
        # JSON-LD and href/src values can legitimately contain strings such as
        # ``todoke``.  Audit only rendered prose, not script/style payloads.
        visible_source = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", source, flags=re.I | re.S)
        visible_source = re.sub(r"<[^>]+>", " ", visible_source)
        haystack = compact(json.dumps(editorial_fields, ensure_ascii=False)) + compact(visible_source)
        if re.search(r"(?<![A-Za-z0-9_])TODO(?![A-Za-z0-9_])", haystack):
            fail(errors, f"{prefix} 禁止語: TODO")
        for banned in BANNED:
            if banned.lower() in haystack.lower():
                fail(errors, f"{prefix} 禁止語: {banned}")
    if len(all_keywords) != 600:
        fail(errors, f"全キーワードは600語必須: {len(all_keywords)}")
    duplicate_keywords = [x for x, count in Counter(all_keywords).items() if count > 1]
    if duplicate_keywords:
        fail(errors, f"キーワード重複: {duplicate_keywords[:12]}")
    repeated = [(p, owners) for p, owners in paragraph_owners.items() if len(set(owners)) > 1]
    if repeated:
        fail(errors, f"記事間の同一長文段落: {[(x[:30], y) for x, y in repeated[:5]]}")
    repeated_prefixes = [(prefix, owners) for prefix, owners in paragraph_prefixes.items() if len(owners) >= 3]
    if repeated_prefixes:
        fail(errors, f"記事間の量産文頭（3記事以上）: {[(x, sorted(y)[:4]) for x, y in repeated_prefixes[:8]]}")
    if any(count > 2 for count in title_starts.values()):
        fail(errors, "タイトル先頭18字の反復が多すぎます")
    index_path = ROOT / "discover" / "index.html"
    if not index_path.exists():
        fail(errors, "/discover/index.htmlがありません")
    else:
        index = index_path.read_text(encoding="utf-8")
        required_index_slugs = slugs if not args.allow_pending else [row["slug"] for row in rows if row.get("publish_ready")]
        for slug in required_index_slugs:
            if f'/discover/{slug}/' not in index:
                fail(errors, f"親indexから未到達: {slug}")
        listing_match = re.search(r'<script id="discover-data" type="application/json">(.*?)</script>', index, re.S)
        if not listing_match:
            fail(errors, "親indexに遅延描画用discover-dataがありません")
        else:
            try:
                listing = json.loads(listing_match.group(1))
            except json.JSONDecodeError as exc:
                fail(errors, f"discover-dataのJSONが不正: {exc}")
                listing = []
            if len(listing) != 200 or len({item.get("slug") for item in listing}) != 200:
                fail(errors, f"一覧データは200固有記事必須: {len(listing)}")
            short_titles = [item.get("shortTitle", "") for item in listing]
            bad_short = [title for title in short_titles if not title or len(title) > 15]
            if bad_short:
                fail(errors, f"一覧短見出しは1〜15字必須: {bad_short[:8]}")
            if len(set(short_titles)) != len(short_titles):
                fail(errors, "一覧短見出しが重複しています")
            expected_tabs = {
                "parenting": 42, "tourism": 39, "transport": 28, "admin": 24,
                "disaster": 23, "health": 21, "food": 15, "housing": 8,
            }
            if Counter(item.get("tab") for item in listing) != Counter(expected_tabs):
                fail(errors, f"8分類の割当件数が不正: {Counter(item.get('tab') for item in listing)}")
        tab_buttons = re.findall(r'class="guide-tab(?: is-active)?"', index)
        if len(tab_buttons) != 9:
            fail(errors, f"分類タブは「すべて」＋8分類の9個必須: {len(tab_buttons)}")
        for required_id in ("discover-search", "discover-clear", "discover-list", "discover-more", "discover-empty", "discover-suggestions"):
            if f'id="{required_id}"' not in index:
                fail(errors, f"一覧UI要素がありません: {required_id}")
        if index.count('class="pickup-feature"') != 1 or index.count('class="pickup-list"') != 1:
            fail(errors, "今月のピックアップ構造が不正です")
        expected_seasonal = {
            1: "morimachi-events-calendar", 2: "morimachi-wagashi-guide",
            3: "morimachi-cherry-blossoms", 4: "morimachi-cherry-blossoms",
            5: "morimachi-flower-calendar", 6: "gokurakuji-hydrangeas",
            7: "acty-mori-river-play-summer", 8: "acty-mori-river-play-summer",
            9: "morimachi-events-calendar", 10: "mori-festival",
            11: "oguni-shrine-autumn-leaves", 12: "morimachi-souvenir-guide",
        }[date.today().month]
        pickup_match = re.search(r'class="pickup-feature" href="/discover/([^/]+)/"', index)
        if not pickup_match or pickup_match.group(1) != expected_seasonal:
            fail(errors, f"今月の主記事が季節不一致です: {pickup_match.group(1) if pickup_match else 'なし'}")
        if f'data-pickup-month="{date.today().month}"' not in index:
            fail(errors, "ピックアップ対象月の記録がありません")
        if len(re.findall(r'class="keyword-chip"', index)) not in range(6, 9):
            fail(errors, "人気キーワードは6〜8個必須です")
        if index.count('class="guide-list-item"') > 20:
            fail(errors, "初期HTMLの記事一覧は20件以下にしてください")
        if index.count('class="ranking-list"') != 1 or index.count('class="newest-list"') != 1:
            fail(errors, "人気TOP5または新着5件がありません")
    if errors:
        print("discover品質監査: 不合格")
        for message in errors[:120]:
            print(" - " + message)
        if len(errors) > 120:
            print(f" ...ほか{len(errors) - 120}件")
        sys.exit(1)
    print("discover品質監査: 合格（200ページ / 600固有キーワード）")


if __name__ == "__main__":
    main()
