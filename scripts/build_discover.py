# -*- coding: utf-8 -*-
"""Render the reviewed Mori Town discover guides from an editorial ledger.

This renderer deliberately does not write prose.  Every paragraph, source and
illustration caption must already be present in data/discover-pages.json.
Unreviewed rows remain reachable for local QA, but receive noindex and are not
eligible for search/sitemap registration.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "discover-pages.json"
OUT = ROOT / "discover"
VERIFIED = "verified"


def e(value: object) -> str:
    return html.escape(str(value), quote=True)


def released(row: dict) -> bool:
    return (
        row.get("status") == "published"
        and row.get("editor_reviewed") is True
        and row.get("publish_ready") is True
        and row.get("source_validation") == VERIFIED
        and row.get("uniqueness_validation") == VERIFIED
        and row.get("visual_validation") == VERIFIED
    )


def visible_text(row: dict) -> str:
    return "".join(
        paragraph
        for section in row.get("body_sections", [])
        for paragraph in section.get("paragraphs", [])
    )


def palette(seed: str) -> tuple[str, str, str, str]:
    palettes = [
        ("#183f35", "#dcebdd", "#f4b942", "#fffaf0"),
        ("#29465b", "#dceaf1", "#e87d4c", "#fff9f2"),
        ("#4a3428", "#efe3ce", "#77966d", "#fffaf2"),
        ("#3d315b", "#e7e0f2", "#d6a84b", "#fffaf0"),
        ("#24504a", "#d7eee7", "#d9654f", "#fff8f0"),
    ]
    return palettes[int(hashlib.sha256(seed.encode()).hexdigest(), 16) % len(palettes)]


def motif_art(row: dict, dark: str, accent: str) -> str:
    """Draw a subject-shaped foreground mark instead of a generic text card."""
    haystack = row["title"] + row.get("category_label", "") + row.get("visual_motif", "")
    if any(word in haystack for word in ("神社", "御朱印", "紅葉")):
        return f'<g transform="translate(935 290)" stroke="{accent}" stroke-width="18" fill="none"><path d="M20 12h185M48 48h130M66 48v170M160 48v170M48 118h130"/><path d="M18 218h190" stroke="{dark}"/></g>'
    if any(word in haystack for word in ("PA", "交通", "駅", "IC", "バス")):
        return f'<g transform="translate(920 300)"><path d="M15 230Q100 25 210 230" fill="none" stroke="{dark}" stroke-width="70"/><path d="M15 230Q100 25 210 230" fill="none" stroke="{accent}" stroke-width="8" stroke-dasharray="24 18"/><rect x="52" y="18" width="104" height="64" rx="10" fill="{accent}"/><path d="M104 82v54" stroke="{accent}" stroke-width="12"/></g>'
    if any(word in haystack for word in ("ランチ", "カフェ", "食", "茶", "土産")):
        return f'<g transform="translate(930 330)" stroke="{dark}" stroke-width="13" fill="{accent}"><path d="M18 40h155v118a58 58 0 0 1-58 58H76a58 58 0 0 1-58-58Z"/><path d="M173 72h26a48 48 0 0 1 0 96h-26" fill="none"/><path d="M62 0q-22-34 0-62M112 0q-22-34 0-62" fill="none" stroke="{accent}"/></g>'
    if any(word in haystack for word in ("アクティ", "陶芸", "体験")):
        return f'<g transform="translate(920 315)"><path d="M30 0h170q-8 66-36 95 36 64 34 142H32q-2-78 34-142Q38 66 30 0Z" fill="{accent}" stroke="{dark}" stroke-width="12"/><ellipse cx="115" cy="18" rx="84" ry="20" fill="none" stroke="{dark}" stroke-width="12"/><path d="M55 138h120" stroke="{dark}" stroke-width="10"/></g>'
    if any(word in haystack for word in ("花", "桜", "萩", "あじさい", "ききょう")):
        petals = ''.join(f'<ellipse cx="{110 + 62 * (i % 3)}" cy="{62 + 66 * (i // 3)}" rx="48" ry="72" transform="rotate({i * 55} {110 + 62 * (i % 3)} {62 + 66 * (i // 3)})" fill="{accent}" opacity=".9"/>' for i in range(6))
        return f'<g transform="translate(880 310)">{petals}<circle cx="170" cy="130" r="34" fill="{dark}"/></g>'
    return f'<g transform="translate(930 330)" fill="{accent}" stroke="{dark}" stroke-width="12"><path d="M18 208V84L112 12l94 72v124Z"/><path d="M86 208v-72h52v72M18 84h188" fill="none"/></g>'


def cover_svg(row: dict) -> str:
    dark, pale, accent, paper = palette(row["slug"])
    title = e(row["title"])
    category = e(row["category_label"])
    motif = e(row.get("visual_motif", "森町の山並みと道しるべ"))
    art = motif_art(row, dark, accent)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-labelledby="title desc">
<title id="title">{title}の表紙</title><desc id="desc">{motif}を、遠州森町の山並みと川を背景に描いた編集イラスト。</desc>
<rect width="1200" height="630" fill="{paper}"/><path d="M0 330Q180 190 350 305T700 270T1200 300V630H0Z" fill="{pale}"/>
<path d="M0 430Q210 330 410 420T820 385T1200 420V630H0Z" fill="{dark}" opacity=".92"/>
<path d="M0 525Q260 465 520 520T900 495T1200 520" fill="none" stroke="{accent}" stroke-width="18" opacity=".9"/>
<circle cx="1035" cy="122" r="63" fill="{accent}"/><path d="M88 86h710" stroke="{dark}" stroke-width="4"/>
{art}
<text x="88" y="70" font-family="sans-serif" font-size="28" fill="{dark}" letter-spacing="3">静岡県周智郡森町｜{category}</text>
<foreignObject x="82" y="112" width="875" height="245"><div xmlns="http://www.w3.org/1999/xhtml" style="font:700 54px/1.38 sans-serif;color:{dark};">{title}</div></foreignObject>
<text x="88" y="592" font-family="sans-serif" font-size="25" fill="#fff">森町ライフハック　現地判断ガイド</text>
</svg>'''


def diagram_svg(row: dict, number: int) -> str:
    dark, pale, accent, paper = palette(row["slug"] + str(number))
    item = row["illustrations"][number - 1]
    title = e(item["title"])
    caption = e(item["caption"])
    labels = [e(x) for x in item.get("labels", [])[:4]]
    while len(labels) < 4:
        labels.append("確認")
    if number == 1:
        shapes = ''.join(
            f'<g><circle cx="{160+i*220}" cy="250" r="68" fill="{pale}" stroke="{dark}" stroke-width="5"/><text x="{160+i*220}" y="257" text-anchor="middle" font-family="sans-serif" font-size="22" fill="{dark}">{label}</text>{"<path d=\"M230 250h82\" stroke=\"" + accent + "\" stroke-width=\"10\" marker-end=\"url(#a)\"/>" if i < 3 else ""}</g>'
            for i, label in enumerate(labels)
        )
    else:
        shapes = ''.join(
            f'<g><rect x="{80+(i%2)*470}" y="{175+(i//2)*155}" width="400" height="110" rx="18" fill="{pale}" stroke="{dark}" stroke-width="4"/><text x="{280+(i%2)*470}" y="240" text-anchor="middle" font-family="sans-serif" font-size="24" fill="{dark}">{label}</text></g>'
            for i, label in enumerate(labels)
        )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" data-illustration="mori-editorial" width="960" height="560" viewBox="0 0 960 560" role="img" aria-labelledby="title desc"><title id="title">{title}</title><desc id="desc">{caption}</desc><defs><marker id="a" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0 0L9 3L0 6Z" fill="{accent}"/></marker></defs><rect width="960" height="560" rx="24" fill="{paper}"/><text x="480" y="72" text-anchor="middle" font-family="sans-serif" font-size="34" font-weight="700" fill="{dark}">{title}</text>{shapes}<text x="480" y="520" text-anchor="middle" font-family="sans-serif" font-size="19" fill="{dark}">静岡県森町で確認する順番を整理した編集図解</text></svg>'''


def source_list(row: dict) -> str:
    items = []
    for source in row["sources"]:
        items.append(f'<li><a href="{e(source["url"])}" target="_blank" rel="noopener noreferrer">{e(source["title"])}</a><span>（{e(source["publisher"])}、{e(row["fact_checked_at"])}確認）</span></li>')
    return "".join(items)


def hero_media(row: dict, *, card: bool = False) -> tuple[str, str]:
    photo = row.get("hero_photo", "")
    if photo:
        src = photo
        alt = row.get("cover_alt", row["title"])
        kind = "写真"
    else:
        src = f'/discover/{row["slug"]}/cover.svg' if card else "cover.svg"
        alt = row.get("cover_alt", f'{row["title"]}の編集イラスト')
        kind = "編集イラスト"
    return src, f'<img src="{e(src)}" width="1200" height="630"{ " loading=\"lazy\"" if card else "" } alt="{e(alt)}"><span class="media-kind">{kind}</span>'


def article_html(row: dict, rows_by_slug: dict[str, dict], published_count: int) -> str:
    canonical = f'https://morimachi.enshu-lifehack.com/discover/{row["slug"]}/'
    robots = '' if released(row) else '<meta name="robots" content="noindex,nofollow" data-discover-pending>'
    keywords = "、".join([row["primary_keyword"], *row["secondary_keywords"]])
    body = []
    ill_no = 0
    for i, section in enumerate(row["body_sections"]):
        paragraphs = "".join(f'<p>{e(p)}</p>' for p in section["paragraphs"])
        body.append(f'<section class="editorial-section"><h2>{e(section["heading"])}</h2>{paragraphs}</section>')
        if i in row.get("illustration_after_sections", [2, 5]) and ill_no < 2:
            ill_no += 1
            item = row["illustrations"][ill_no - 1]
            body.append(f'<figure class="article-figure"><img src="fig{ill_no}.svg" width="960" height="560" loading="lazy" alt="{e(item["alt"])}"><figcaption>{e(item["caption"])}</figcaption></figure>')
    related = []
    for slug in row.get("related_slugs", [])[:5]:
        other = rows_by_slug.get(slug)
        if other:
            related.append(f'<li><a href="/discover/{e(slug)}/">{e(other["title"])}</a></li>')
    schema = {
        "@context": "https://schema.org", "@graph": [
            {"@type": "Article", "headline": row["title"], "description": row["description"], "mainEntityOfPage": canonical, "datePublished": row["published_at"], "dateModified": row["updated_at"], "author": {"@type": "Person", "name": "大石浩之"}, "publisher": {"@type": "Organization", "name": "森町ライフハック"}, "image": canonical + "cover.svg", "keywords": keywords},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "静岡県森町ライフハック", "item": "https://morimachi.enshu-lifehack.com/"},
                {"@type": "ListItem", "position": 2, "name": "静岡県森町100ガイド", "item": "https://morimachi.enshu-lifehack.com/discover/"},
                {"@type": "ListItem", "position": 3, "name": row["title"], "item": canonical},
            ]},
        ]
    }
    _, hero = hero_media(row)
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{robots}<title>{e(row["title"])}</title><meta name="description" content="{e(row["description"])}"><link rel="canonical" href="{canonical}"><meta property="og:type" content="article"><meta property="og:title" content="{e(row["title"])}"><meta property="og:description" content="{e(row["description"])}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{canonical}cover.svg"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/site.css?v=20260810"><link rel="stylesheet" href="/assets/discover.css?v=20260810"><script type="application/ld+json">{json.dumps(schema, ensure_ascii=False, separators=(',', ':'))}</script></head><body class="discover-article"><!-- PART:header:START --><!-- PART:header:END --><!-- PART:disclaimer:START --><!-- PART:disclaimer:END --><main><article class="wrap editorial"><nav class="breadcrumb" aria-label="パンくず"><a href="/">静岡県森町ライフハック</a> ／ <a href="/discover/">静岡県森町{published_count}ガイド</a> ／ {e(row["category_label"])}</nav><header class="article-header"><p class="eyebrow">{e(row["category_label"])}｜最終確認 {e(row["fact_checked_at"])}</p><h1>{e(row["title"])}</h1><p class="lead">{e(row["lead"])}</p><figure class="hero-media">{hero}<figcaption>{e(row.get("cover_caption", "記事内容を整理した編集イラスト"))}</figcaption></figure><aside class="answer-box"><h2>先に結論</h2><p>{e(row["direct_answer"])}</p></aside></header>{''.join(body)}<section class="official-sources"><h2>公式情報・確認先</h2><p>掲載内容は次の一次情報を基礎に整理しました。営業、料金、催し、交通は変わるため、出発前または手続き前にリンク先で最新情報を確認してください。</p><ul>{source_list(row)}</ul></section><section class="related-guides"><h2>静岡県森町の関連ガイド</h2><ul>{''.join(related)}</ul><p><a class="btn" href="/discover/">{published_count}ガイドの検索・分類へ戻る</a></p></section></article></main><!-- PART:footer:START --><!-- PART:footer:END --></body></html>'''


def index_html(rows: list[dict]) -> str:
    published = [row for row in rows if released(row)]
    published_count = len(published)
    keyword_count = published_count * 3
    groups: dict[str, list[dict]] = {}
    for row in published:
        groups.setdefault(row.get("broad_category", row["category_label"]), []).append(row)
    category_counts = Counter(row.get("broad_category", row["category_label"]) for row in published)
    chips = ['<button class="filter-chip is-active" type="button" data-category="all" aria-pressed="true">すべて <span>' + str(len(published)) + '</span></button>']
    for category, count in sorted(category_counts.items(), key=lambda item: (-item[1], item[0])):
        chips.append(f'<button class="filter-chip" type="button" data-category="{e(category)}" aria-pressed="false">{e(category)} <span>{count}</span></button>')
    sections = []
    for category, items in sorted(groups.items()):
        cards = []
        for x in sorted(items, key=lambda row: row["title"]):
            _, media = hero_media(x, card=True)
            search_text = " ".join([x["title"], x["description"], x["primary_keyword"], *x["secondary_keywords"], *x.get("audience", [])])
            cards.append(f'<li class="discover-card" data-category="{e(category)}" data-search="{e(search_text.lower())}"><a href="/discover/{e(x["slug"])}/"><span class="card-media">{media}</span><span class="card-copy"><small>{e(x["category_label"])}</small><strong>{e(x["title"])}</strong><span>{e(x["description"])}</span><em>{e(x["primary_keyword"])}</em></span></a></li>')
        sections.append(f'<section class="discover-section" data-section-category="{e(category)}"><h2>{e(category)} <span>{len(items)}本</span></h2><ul class="discover-grid">{"".join(cards)}</ul></section>')
    collection = {"@type": "CollectionPage", "name": f"静岡県森町を深く知る{published_count}ガイド", "url": "https://morimachi.enshu-lifehack.com/discover/", "mainEntity": {"@type": "ItemList", "numberOfItems": published_count, "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f'https://morimachi.enshu-lifehack.com/discover/{x["slug"]}/', "name": x["title"]} for i, x in enumerate(published)]}}
    breadcrumb = {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "静岡県森町ライフハック", "item": "https://morimachi.enshu-lifehack.com/"},
        {"@type": "ListItem", "position": 2, "name": f"静岡県森町{published_count}ガイド", "item": "https://morimachi.enshu-lifehack.com/discover/"},
    ]}
    schema = {"@context": "https://schema.org", "@graph": [collection, breadcrumb]}
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>静岡県森町を深く知る{published_count}ガイド｜検索・分類対応</title><meta name="description" content="静岡県周智郡森町の観光、食、交通、子育て、健康、防災、行政手続、住まいを検索・分類から探せる{published_count}本の長文ガイドです。{keyword_count}の固有キーワードを一次情報と判断順に沿って解説します。"><link rel="canonical" href="https://morimachi.enshu-lifehack.com/discover/"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/site.css?v=20260810"><link rel="stylesheet" href="/assets/discover.css?v=20260810"><script defer src="/assets/discover.js?v=20260810"></script><script type="application/ld+json">{json.dumps(schema, ensure_ascii=False, separators=(',', ':'))}</script></head><body class="discover-index"><!-- PART:header:START --><!-- PART:header:END --><!-- PART:disclaimer:START --><!-- PART:disclaimer:END --><main><div class="wrap"><nav class="breadcrumb"><a href="/">静岡県森町ライフハック</a> ／ {published_count}ガイド</nav><header class="hero"><p class="eyebrow">100の質問とは別の、読み応えある編集ガイド</p><h1>静岡県森町を深く知る{published_count}ガイド</h1><p class="lead">観光・食・交通から、子育て・健康・防災・行政手続・住まいまで、公式情報、良い点、注文したい点、代案を一つの記事で読み切れる形にしました。検索欄と分類ボタンから目的の記事を絞れます。</p><p class="publication-count">現在公開中：<strong>{published_count}本</strong>／固有キーワード <strong>{keyword_count}語</strong></p></header><section class="discover-tools" aria-labelledby="guide-search-title"><h2 id="guide-search-title">目的のガイドを探す</h2><label for="discover-search">キーワード検索</label><div class="search-row"><input id="discover-search" type="search" autocomplete="off" placeholder="例：小國神社、保育料、バス、防災"><button id="discover-clear" type="button">クリア</button></div><div class="filter-chips" aria-label="分類で絞り込む">{''.join(chips)}</div><p id="discover-result" class="result-count" aria-live="polite">{published_count}件を表示中</p></section><div id="discover-empty" class="discover-empty" hidden><h2>該当するガイドがありません</h2><p>言葉を短くするか、「すべて」を選んで再検索してください。</p></div><div id="discover-results">{''.join(sections)}</div></div></main><!-- PART:footer:START --><!-- PART:footer:END --></body></html>'''


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    rows = data["pages"]
    by_slug = {row["slug"]: row for row in rows}
    OUT.mkdir(exist_ok=True)
    expected = set(by_slug)
    orphaned = sorted(path.name for path in OUT.iterdir() if path.is_dir() and path.name not in expected)
    if orphaned:
        raise RuntimeError(f"台帳にないdiscoverディレクトリがあります: {orphaned[:10]}")
    (OUT / "index.html").write_text(index_html(rows), encoding="utf-8", newline="\n")
    for row in rows:
        dest = OUT / row["slug"]
        dest.mkdir(parents=True, exist_ok=True)
        page_html = article_html(row, by_slug, sum(1 for item in rows if released(item)))
        (dest / "index.html").write_text(page_html, encoding="utf-8", newline="\n")
        (dest / "cover.svg").write_text(cover_svg(row), encoding="utf-8", newline="\n")
        for number in (1, 2):
            (dest / f"fig{number}.svg").write_text(diagram_svg(row, number), encoding="utf-8", newline="\n")
    print(f"discover生成: {len(rows)}件（公開 {sum(released(x) for x in rows)}件）")


if __name__ == "__main__":
    main()
