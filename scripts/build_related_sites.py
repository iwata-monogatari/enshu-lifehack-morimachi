# -*- coding: utf-8 -*-
"""関連サイト一覧ページ /about/related-sites/ を生成する（修正指示書20）。

共通フッターに音楽・お笑い等の関連サイトを大量に並べると、
住民票や夜間診療を調べている利用者にとって不要で、生活情報サイトとしての
主題がぼやける。フッターからは「関連サイト一覧」1リンクだけにし、
実際の一覧はこのページへ集約する。
"""
from __future__ import annotations

import json
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

CITY = json.loads((ROOT / "data" / "city.json").read_text(encoding="utf-8"))
SITE = CITY["site_url"].rstrip("/")
SITE_NAME = CITY["site_name"]
URL = SITE + "/about/related-sites/"

PARTS = {n: (ROOT / "parts" / f"{n}.html").read_text(encoding="utf-8").strip()
         for n in ("header", "footer", "head-css", "disclaimer")}

GROUPS = [
    ("森町の相談窓口", "森町ライフハックの運営会社が実際に相談を受けている窓口です。", [
        ("https://fudosan.atawi.link/areas/mori/", "森町の実家・空き家相談（ふじがおか実家カルテ）",
         "相続した実家や空き家を、売る前に整理するための相談窓口"),
        ("https://www.fujigaoka-service.info/", "富士ヶ丘サービス（介護）",
         "高齢者向け住宅と、介護と住まいの相談"),
    ]),
    ("遠州ライフハック", "同じ方針で、遠州の各市町を扱っています。", [
        ("https://enshu-lifehack.com/", "遠州ライフハック", "地域を選ぶ入口"),
        ("https://iwata.enshu-lifehack.com/", "磐田ライフハック", ""),
        ("https://fukuroi.enshu-lifehack.com/", "袋井ライフハック", ""),
        ("https://kakegawa.enshu-lifehack.com/", "掛川ライフハック", ""),
        ("https://kikugawa.enshu-lifehack.com/", "菊川ライフハック", ""),
        ("https://omaezaki.enshu-lifehack.com/", "御前崎ライフハック", ""),
        ("https://kosai.enshu-lifehack.com/", "湖西ライフハック", ""),
        ("https://hamamatsu.enshu-lifehack.com/", "浜松ライフハック", ""),
    ]),
    ("大石ひろゆきの他のサイト", "森町の手続きとは直接関係のない、個人の制作物です。", [
        ("https://oishi-hiroyuki.org/", "大石ひろゆき公式サイト", ""),
        ("https://iwata-monogatari.net/", "磐田物語", "磐田の歴史・地域史"),
        ("https://atawimusic.link/", "ATAWI MUSIC", "音楽"),
        ("https://atawicomedy.link/", "ATAWI COMEDY", "お笑い"),
    ]),
]


def esc(s: str) -> str:
    return escape(str(s or ""), quote=True)


def main() -> None:
    sections = []
    for heading, lead, links in GROUPS:
        items = "".join(
            f'<li><a class="official-link" href="{esc(u)}" target="_blank" rel="noopener">'
            f"{esc(label)}" + (f' <span>{esc(note)}</span>' if note else "") + "</a></li>"
            for u, label, note in links)
        sections.append(f'<h2 class="sec">{esc(heading)}</h2>'
                        f'<p class="lead">{esc(lead)}</p>'
                        f'<ul class="related-list">{items}</ul>')

    desc = ("静岡県周智郡森町の森町ライフハックと、同じ運営者による関連サイトの一覧です。"
            "森町の相談窓口、遠州ライフハックの各市町版、個人制作のサイトに分けて掲載しています。")
    title = f"関連サイト一覧 | 静岡県{SITE_NAME}"
    breadcrumb = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": f"静岡県{SITE_NAME}", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "関連サイト一覧", "item": URL},
        ],
    }

    html = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:type" content="website"><meta property="og:site_name" content="{esc(SITE_NAME)}">
<meta property="og:locale" content="ja_JP"><meta property="og:title" content="関連サイト一覧">
<meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{URL}">
<meta property="og:image" content="{SITE}/assets/ogp/site-default.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="関連サイト一覧">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{SITE}/assets/ogp/site-default.png">
<link rel="canonical" href="{URL}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<!-- PART:head-css:START -->{PARTS['head-css']}<!-- PART:head-css:END -->
<script type="application/ld+json">{json.dumps(breadcrumb, ensure_ascii=False, separators=(',', ':'))}</script>
</head>
<body class="hub">
<!-- PART:header:START -->{PARTS['header']}<!-- PART:header:END -->
<!-- PART:disclaimer:START -->{PARTS['disclaimer']}<!-- PART:disclaimer:END -->
<main><div class="wrap">
<p class="breadcrumb"><a href="/">静岡県{esc(SITE_NAME)}</a> ／ 関連サイト一覧</p>
<section class="hero">
<h1>関連サイト一覧</h1>
<p class="lead">森町ライフハックと同じ運営者がつくっているサイトです。
森町の手続きと直接関係のないものも含むため、各ページのフッターには並べず、このページにまとめています。</p>
</section>
{"".join(sections)}
<p class="verified">最終確認日：2026-08-05 ／ 運営：富士ヶ丘サービス株式会社（代表 大石浩之）</p>
</div></main>
<!-- PART:footer:START -->{PARTS['footer']}<!-- PART:footer:END -->
</body></html>
"""
    out = ROOT / "about" / "related-sites"
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(html, encoding="utf-8")
    total = sum(len(links) for _, _, links in GROUPS)
    print(f"/about/related-sites/ を生成しました（{len(GROUPS)}分類 / {total}サイト）")


if __name__ == "__main__":
    main()
