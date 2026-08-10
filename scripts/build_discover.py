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

LISTING_TABS = [
    ("parenting", "子育て・学び", ("妊娠・子育て手続", "学校・就学・家庭記録", "子育て・教育")),
    ("tourism", "観光・レジャー", ("小國神社・ことまち横丁", "アクティ森・自然体験", "花・祭り・文化", "森町観光・暮らし")),
    ("transport", "交通・おでかけ", ("交通・宿泊・行程", "交通・外出・生活動線")),
    ("admin", "行政・税金", ("行政手続・証明書", "行政手続・暮らし", "税金・不動産", "税金・納付")),
    ("disaster", "防災・安全", ("防災・家族の備え", "防災・安全")),
    ("health", "健康・医療", ("健康・医療・保険", "健康・医療")),
    ("food", "食・買い物", ("食・お茶・買い物",)),
    ("housing", "住まい・移住", ("住まい・土地・移住",)),
]
TAB_BY_CATEGORY = {category: (key, label) for key, label, categories in LISTING_TABS for category in categories}

PICKUP_SLUGS = [
    "oguni-shrine-autumn-leaves",
    "morimachi-lunch-complete-guide",
    "acty-mori-complete-guide",
    "kotomachi-yokocho-complete-guide",
    "enshu-morimachi-pa-up",
    "morimachi-childcare-support",
    "morimachi-disaster-map",
    "morimachi-moving-in-procedures",
]

POPULAR_SLUGS = [
    "oguni-shrine-autumn-leaves",
    "morimachi-lunch-complete-guide",
    "acty-mori-complete-guide",
    "kotomachi-yokocho-complete-guide",
    "morimachi-disaster-map",
]

POPULAR_KEYWORDS = ["小國神社", "子育て", "防災", "アクティ森", "移住", "お茶", "マイナンバー", "交通"]


def e(value: object) -> str:
    return html.escape(str(value), quote=True)


def listing_tab(row: dict) -> tuple[str, str]:
    category = row.get("broad_category", "")
    if category not in TAB_BY_CATEGORY:
        raise ValueError(f"一覧8分類へ未割当のカテゴリです: {category} ({row.get('slug')})")
    return TAB_BY_CATEGORY[category]


def short_title(row: dict) -> str:
    """Create a compact, readable listing label without changing the article H1."""
    text = row["title"].split("｜", 1)[0]
    text = re.sub(r"^静岡県周智郡森町[・のではへをから]*", "", text)
    text = re.sub(r"^静岡県森町[・のではへをから]*", "", text)
    text = re.sub(r"^遠州森町[・のではへをから]*", "", text)
    text = text.strip(" ・｜")
    replacements = (
        ("マイナンバーカード", "マイナカード"),
        ("国民健康保険", "国保"),
        ("確認する方法", "確認"),
        ("確認する", "確認"),
        ("ガイド", "案内"),
        ("チェックリスト", "確認表"),
        ("モデルコース", "コース"),
        ("インターネット", "ネット"),
        ("ハザードマップ", "防災地図"),
        ("子どもの", "子ども"),
        ("するとき", "時"),
        ("する前に", "前の"),
        ("したとき", "時"),
        ("について", ""),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    text = re.sub(r"[「」『』・／/ ]+", "", text)
    text = re.sub(r"(を|が|で|へ|から|まで|には)$", "", text)
    if len(text) < 5:
        text = row.get("primary_keyword", text)
        text = re.sub(r"静岡県|周智郡|森町|[「」『』・／/ 　]", "", text)
        for old, new in replacements:
            text = text.replace(old, new)
    if len(text) <= 15:
        return text

    # Prefer a complete phrase before a Japanese particle instead of cutting a word.
    for marker in ("を", "へ", "で", "から", "時", "前", "後", "と", "の"):
        prefix = text.split(marker, 1)[0]
        if 7 <= len(prefix) <= 15:
            return prefix
    return text[:14].rstrip("をがでへとの") + "…"


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
    by_slug = {row["slug"]: row for row in published}
    missing_categories = sorted({row.get("broad_category", "") for row in published} - set(TAB_BY_CATEGORY))
    if missing_categories:
        raise ValueError(f"一覧8分類へ未割当のカテゴリがあります: {missing_categories}")

    tab_counts = Counter(listing_tab(row)[0] for row in published)
    tabs = [f'<button class="guide-tab is-active" type="button" role="tab" aria-selected="true" data-tab="all">すべて<span>{published_count}</span></button>']
    for key, label, _ in LISTING_TABS:
        tabs.append(f'<button class="guide-tab" type="button" role="tab" aria-selected="false" data-tab="{key}">{e(label)}<span>{tab_counts[key]}</span></button>')

    listing_rows = []
    for row in sorted(published, key=lambda item: (item.get("published_at", ""), item["id"]), reverse=True):
        tab_key, tab_label = listing_tab(row)
        src, _ = hero_media(row, card=True)
        search_text = " ".join([
            row["title"], row["description"], row["primary_keyword"], *row["secondary_keywords"],
            *row.get("audience", []), row.get("category_label", ""), row.get("broad_category", ""), tab_label,
        ])
        listing_rows.append({
            "slug": row["slug"], "title": row["title"], "shortTitle": short_title(row),
            "description": row["description"], "category": row["category_label"],
            "tab": tab_key, "tabLabel": tab_label, "image": src,
            "imageAlt": row.get("cover_alt", row["title"]), "mediaType": "写真" if row.get("hero_photo") else "挿絵",
            "publishedAt": row.get("published_at", ""), "search": search_text,
        })
    listing_json = json.dumps(listing_rows, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    pickup_rows = [by_slug[slug] for slug in PICKUP_SLUGS if slug in by_slug]
    if len(pickup_rows) != 8:
        missing = sorted(set(PICKUP_SLUGS) - set(by_slug))
        raise ValueError(f"今日のピックアップが8件になりません: {missing}")
    pickup_main = pickup_rows[0]
    pickup_src, pickup_media = hero_media(pickup_main, card=True)
    pickup_hero = f'''<a class="pickup-feature" href="/discover/{e(pickup_main["slug"])}/">
        <span class="pickup-image">{pickup_media}</span><span class="pickup-copy"><small>今日の1本</small>
        <strong>{e(short_title(pickup_main))}</strong><span>{e(pickup_main["description"])}</span></span></a>'''
    pickup_links = "".join(
        f'<li><a href="/discover/{e(row["slug"])}/"><small>{e(listing_tab(row)[1])}</small><span>{e(short_title(row))}</span></a></li>'
        for row in pickup_rows[1:]
    )

    popular_rows = [by_slug[slug] for slug in POPULAR_SLUGS if slug in by_slug]
    if len(popular_rows) != 5:
        raise ValueError("人気ガイドは5件必要です")
    popular_links = "".join(
        f'<li><span>{index}</span><a href="/discover/{e(row["slug"])}/">{e(short_title(row))}</a></li>'
        for index, row in enumerate(popular_rows, 1)
    )
    newest_rows = sorted(published, key=lambda row: (row.get("published_at", ""), row["id"]), reverse=True)[:5]
    newest_links = "".join(
        f'<li><time datetime="{e(row.get("published_at", ""))}">{e(row.get("published_at", "").replace("-", "."))}</time><a href="/discover/{e(row["slug"])}/">{e(short_title(row))}</a></li>'
        for row in newest_rows
    )
    keyword_buttons = "".join(f'<button type="button" class="keyword-chip" data-keyword="{e(word)}">{e(word)}</button>' for word in POPULAR_KEYWORDS)
    noscript_links = "".join(f'<li><a href="/discover/{e(row["slug"])}/">{e(row["title"])}</a></li>' for row in published)
    collection = {"@type": "CollectionPage", "name": f"静岡県森町を深く知る{published_count}ガイド", "url": "https://morimachi.enshu-lifehack.com/discover/", "mainEntity": {"@type": "ItemList", "numberOfItems": published_count, "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f'https://morimachi.enshu-lifehack.com/discover/{x["slug"]}/', "name": x["title"]} for i, x in enumerate(published)]}}
    breadcrumb = {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "静岡県森町ライフハック", "item": "https://morimachi.enshu-lifehack.com/"},
        {"@type": "ListItem", "position": 2, "name": f"静岡県森町{published_count}ガイド", "item": "https://morimachi.enshu-lifehack.com/discover/"},
    ]}
    schema = {"@context": "https://schema.org", "@graph": [collection, breadcrumb]}
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>静岡県森町を深く知る{published_count}ガイド｜検索・8分類対応</title><meta name="description" content="静岡県周智郡森町の観光、食、交通、子育て、健康、防災、行政手続、住まいを検索と8分類から探せる{published_count}本の長文ガイドです。{keyword_count}の固有キーワードを一次情報と判断順に沿って解説します。"><link rel="canonical" href="https://morimachi.enshu-lifehack.com/discover/"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/site.css?v=20260810"><link rel="stylesheet" href="/assets/discover.css?v=20260810b"><script defer src="/assets/discover.js?v=20260810b"></script><script type="application/ld+json">{json.dumps(schema, ensure_ascii=False, separators=(',', ':'))}</script></head><body class="discover-index"><!-- PART:header:START --><!-- PART:header:END --><!-- PART:disclaimer:START --><!-- PART:disclaimer:END --><main><div class="wrap"><nav class="breadcrumb"><a href="/">静岡県森町ライフハック</a> ／ {published_count}ガイド</nav><header class="discover-hero"><p class="eyebrow">公式情報を、暮らしと訪問の判断順に</p><h1>静岡県森町の実用ガイド</h1><p>知りたいことを検索するか、8つの分類から選んでください。記事本文とURLはそのままに、{published_count}本を探しやすく整理しました。</p><p class="publication-count"><strong>{published_count}本</strong>公開中／固有キーワード <strong>{keyword_count}語</strong></p></header>
<section class="discover-tools" aria-labelledby="guide-search-title"><h2 id="guide-search-title">目的のガイドを探す</h2><label for="discover-search">キーワード検索</label><div class="search-row"><input id="discover-search" type="search" autocomplete="off" inputmode="search" placeholder="例：小國神社、保育料、バス、防災"><button id="discover-clear" type="button">クリア</button></div><div class="popular-keywords" aria-label="よく探されるキーワード"><span>人気の検索</span>{keyword_buttons}</div><div class="guide-tabs" role="tablist" aria-label="8分類で絞り込む">{''.join(tabs)}</div></section>
<section class="pickup" aria-labelledby="pickup-title"><div class="section-heading"><p>迷ったときの入口</p><h2 id="pickup-title">今日のピックアップ</h2></div><div class="pickup-grid">{pickup_hero}<ul class="pickup-list">{pickup_links}</ul></div></section>
<div class="discover-layout"><div class="discover-main"><div class="list-heading"><div><p id="discover-current-tab">すべての分類</p><h2>ガイド一覧</h2></div><p id="discover-result" class="result-count" aria-live="polite">{published_count}件中10件を表示</p></div><ul id="discover-list" class="guide-list" aria-live="polite"></ul><div id="discover-empty" class="discover-empty" hidden><h2>該当するガイドがありません</h2><p>別の言葉で探すか、下の候補から選んでください。</p><ul id="discover-suggestions"></ul><button id="discover-reset" type="button">すべてのガイドへ戻る</button></div><button id="discover-more" class="load-more" type="button">もっと見る <span>次の20件</span></button></div>
<aside class="discover-sidebar" aria-label="人気と新着のガイド"><section><h2>人気ガイド TOP5</h2><ol class="ranking-list">{popular_links}</ol></section><section><h2>新着ガイド</h2><ul class="newest-list">{newest_links}</ul></section><p class="sidebar-note">料金・日程・制度は更新されることがあります。各記事の公式確認先で最新情報をご確認ください。</p></aside></div>
<noscript><section class="noscript-guides"><h2>全{published_count}ガイド</h2><p>一覧の検索・絞り込みにはJavaScriptを使用します。無効の場合はこちらから選べます。</p><ul>{noscript_links}</ul></section></noscript><script id="discover-data" type="application/json">{listing_json}</script></div></main><!-- PART:footer:START --><!-- PART:footer:END --></body></html>'''


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
