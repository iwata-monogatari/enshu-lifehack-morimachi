# -*- coding: utf-8 -*-
"""6つの生活場面ハブページ /hub/<id>/ を生成する（抜本改修指示書 4.1 / 4.2 / 7）。

親ページ（page_type=parent）を「状況を選ぶ分岐カード」に、
詳細ページ（page_type=detail）を旧13カテゴリごとの一覧に並べる。
統合（action=merge）のページは出力しない。

実行: python scripts/build_hubs.py
"""
from __future__ import annotations

import json
import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

CITY = json.loads((ROOT / "data" / "city.json").read_text(encoding="utf-8"))
HUBS = json.loads((ROOT / "data" / "hubs.json").read_text(encoding="utf-8"))
TOPICS = json.loads((ROOT / "data" / "topics_master.json").read_text(encoding="utf-8"))
SITE = CITY["site_url"].rstrip("/")
SITE_NAME = CITY["site_name"]
TODAY = "2026-08-04"

PARTS = {
    name: (ROOT / "parts" / f"{name}.html").read_text(encoding="utf-8").strip()
    for name in ("header", "footer", "head-css", "disclaimer", "cta-disclosure")
}

CTA_BLOCKS = {
    "care": (
        '<div class="company-strip cta-middle"><h2 class="sec" style="margin-top:0">'
        "介護と住まいを一緒に相談する</h2>"
        '<div class="company-grid"><div class="company-card">'
        "<p>公的な介護の窓口で相談したうえで、住まいをどうするかも一緒に考えたいときの選択肢です。"
        "相談は任意で、公的サービスの利用に影響しません。</p>"
        '<a class="official-link" href="https://fudosan.atawi.link/areas/mori/'
        '?utm_source=morimachi_lifehack&amp;utm_medium=referral&amp;utm_campaign=morimachi_support&amp;utm_content=hub_care" '
        'target="_blank" rel="noopener" style="margin-top:8px" data-track-click="cta_care">'
        "森町の相談窓口を見る <span>富士ヶ丘サービス</span></a></div></div>"
        + PARTS["cta-disclosure"] + "</div>"
    ),
    "real_estate": (
        '<div class="company-strip cta-middle"><h2 class="sec" style="margin-top:0">'
        "親の家を今後どうするか整理する</h2>"
        '<div class="company-grid"><div class="company-card">'
        "<p>売る・貸す・残すを決める前に、権利関係と費用の見通しを整理したいときの選択肢です。"
        "町の制度の確認が先で、相談は任意です。</p>"
        '<a class="official-link" href="https://fudosan.atawi.link/areas/mori/'
        '?utm_source=morimachi_lifehack&amp;utm_medium=referral&amp;utm_campaign=morimachi_support&amp;utm_content=hub_property" '
        'target="_blank" rel="noopener" style="margin-top:8px" data-track-click="cta_real_estate">'
        "森町の相談窓口を見る <span>富士ヶ丘サービス</span></a></div></div>"
        + PARTS["cta-disclosure"] + "</div>"
    ),
    "none": "",
}

CATEGORY_ORDER = [
    "暮らし始めた", "新しい場所へ", "これから暮らす", "働く・暮らす",
    "家族が増える", "学ぶ・育つ", "親のこと", "家・住まい", "人生の終わり",
    "もしもの時", "健康・医療", "困った・相談したい", "遊ぶ・使う・出かける",
]


def esc(s: str) -> str:
    return escape(str(s or ""), quote=True)


def strip_emoji(s: str) -> str:
    return re.sub(r"^[\U0001F000-\U0001FAFF☀-➿️‍\s]+", "", s or "").strip()


def pages_for(hub_id: str) -> list[dict]:
    return [t for t in TOPICS
            if t.get("hub") == hub_id and t.get("action") != "merge"]


def branch_cards(pages: list[dict]) -> str:
    parents = [p for p in pages if p.get("page_type") == "parent"]
    parents.sort(key=lambda p: ({"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(p.get("priority"), 9),
                                p["href"]))
    if not parents:
        return ""
    cards = []
    for p in parents:
        cards.append(
            f'<a class="branch-card" href="{esc(p["href"])}">'
            f'<span class="branch-icon" aria-hidden="true">{esc(p.get("icon", ""))}</span>'
            f'<span class="branch-text">'
            f'<span class="branch-need">{esc((p.get("needs") or [p.get("intent", "")])[0])}</span>'
            f'<span class="branch-title">{esc(p.get("intent", ""))}</span>'
            f'</span><span class="branch-arrow" aria-hidden="true">›</span></a>'
        )
    return ('<h2>あてはまる状況を選ぶ</h2>'
            '<p class="lead">近いものを選ぶと、そこから必要なページへ進めます。</p>'
            f'<div class="branch-grid">{"".join(cards)}</div>')


def detail_lists(pages: list[dict]) -> str:
    details = [p for p in pages if p.get("page_type") != "parent"]
    by_cat: dict[str, list[dict]] = {}
    for p in details:
        by_cat.setdefault(p.get("category", "その他"), []).append(p)
    if not by_cat:
        return ""
    blocks = []
    for cat in sorted(by_cat, key=lambda c: CATEGORY_ORDER.index(c)
                      if c in CATEGORY_ORDER else 99):
        items = sorted(by_cat[cat],
                       key=lambda p: ({"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(
                           p.get("priority"), 9), p["href"]))
        lis = "".join(
            f'<li><a href="{esc(p["href"])}">'
            f'<span class="item-title">{esc(p.get("intent") or strip_emoji(p["title"]))}</span>'
            f'<span class="item-note">{esc(strip_emoji(p["title"]))}</span></a></li>'
            for p in items)
        blocks.append(
            f'<section class="hub-cat"><h3>{esc(strip_emoji(cat))}</h3>'
            f'<ul class="hub-items">{lis}</ul></section>')
    return ('<h2>この場面のページ一覧</h2>'
            '<p class="lead">上段の見出しが「解決できること」、下段が実際のページ名です。</p>'
            f'<div class="hub-cats">{"".join(blocks)}</div>')


def other_hubs(current: str) -> str:
    cards = []
    for h in HUBS["hubs"]:
        if h["id"] == current:
            continue
        cards.append(
            f'<a class="link-card" href="/hub/{h["slug"]}/">'
            f'<span class="card-text"><span class="card-title">'
            f'<span class="topic-icon" aria-hidden="true">{h["emoji"]}</span>{esc(h["title"])}'
            f'</span><span class="card-desc">{esc(h["short"])}</span></span>'
            f'<span class="arrow" aria-hidden="true">›</span></a>')
    return ('<h2>ほかの場面から探す</h2>'
            f'<div class="procedure-grid">{"".join(cards)}</div>')


def build(hub: dict) -> str:
    hub_id = hub["id"]
    pages = pages_for(hub_id)
    url = f"{SITE}/hub/{hub['slug']}/"
    title = f"{hub['title']}｜森町の手続き・相談先｜{SITE_NAME}"
    desc = hub["lead"][:118]
    image = f"{SITE}/assets/ogp/hub-{hub_id}.png"

    breadcrumb = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": SITE_NAME, "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": hub["title"], "item": url},
        ],
    }
    learn = "".join(f"<li>{esc(x)}</li>" for x in hub["learn"])
    official = "".join(
        f'<a class="official-link" href="{esc(o["url"])}" target="_blank" rel="noopener">'
        f'{esc(o["label"])} <span>森町公式</span></a>' for o in hub["official"])

    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:type" content="website"><meta property="og:site_name" content="{esc(SITE_NAME)}">
<meta property="og:locale" content="ja_JP"><meta property="og:title" content="{esc(hub['title'])}">
<meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{url}">
<meta property="og:image" content="{image}"><meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(hub['title'])}"><meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{image}">
<link rel="canonical" href="{url}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<!-- PART:head-css:START -->{PARTS['head-css']}<!-- PART:head-css:END -->
<script type="application/ld+json">{json.dumps(breadcrumb, ensure_ascii=False, separators=(',', ':'))}</script>
</head>
<body class="hub">
<!-- PART:header:START -->{PARTS['header']}<!-- PART:header:END -->
<!-- PART:disclaimer:START -->{PARTS['disclaimer']}<!-- PART:disclaimer:END -->
<main><div class="wrap">
<p class="breadcrumb"><a href="/">{esc(SITE_NAME)}</a> ／ {esc(hub['title'])}</p>
<section class="hero">
<p class="eyebrow"><span aria-hidden="true">{hub['emoji']}</span> 暮らしの場面から探す</p>
<h1>{esc(hub['title'])}</h1>
<p class="lead">{esc(hub['lead'])}</p>
</section>
<section class="choose">
<h2 style="margin-top:0">このページで分かること</h2>
<ul>{learn}</ul>
</section>
{branch_cards(pages)}
{detail_lists(pages)}
<h2>森町公式の情報</h2>
<div class="official-box">
<p>制度の詳細・申請の可否・最新の受付時間は、森町公式ページと担当窓口で確認してください。</p>
{official}
<p class="mini">森町役場 {esc(CITY['official']['hall_tel'])}／{esc(CITY['official']['hall_address'])}</p>
</div>
{CTA_BLOCKS[hub['cta']]}
{other_hubs(hub_id)}
<p class="verified">最終確認日：{TODAY} ／ このページは{esc(SITE_NAME)}が公式情報を整理した案内です。最新・正確な情報は必ず森町公式ページで確認してください。</p>
</div></main>
<!-- PART:footer:START -->{PARTS['footer']}<!-- PART:footer:END -->
</body></html>
"""


def main() -> None:
    total = 0
    for hub in HUBS["hubs"]:
        out_dir = ROOT / "hub" / hub["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(build(hub), encoding="utf-8")
        n = len(pages_for(hub["id"]))
        total += n
        print(f"  /hub/{hub['slug']}/  掲載 {n} ページ")
    print(f"ハブ 6 ページを生成しました（延べ {total} ページを掲載）")

    covered = {t["href"] for t in TOPICS if t.get("action") != "merge" and t.get("hub")}
    orphan = [t["href"] for t in TOPICS
              if t.get("action") != "merge" and t["href"] not in covered]
    if orphan:
        print("【要確認】どのハブにも載らないページ:")
        for href in orphan:
            print("  " + href)


if __name__ == "__main__":
    main()
