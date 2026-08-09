#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""空き家・相続・土地・農地・山林の判断ハブを生成する。"""
from __future__ import annotations

import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://morimachi.enshu-lifehack.com"

THEMES = {
    "property": ("森町の住宅・建物", "中古住宅、設備、接道、災害リスクなど、購入や改修前に読む記事を状況別に選べます。", "🏠"),
    "vacant-house": ("森町の空き家", "管理、空き家バンク、修繕、近隣対応のどこから確認するかを状況別に選べます。", "🏚️"),
    "inheritance": ("森町の相続と家", "相続人、登記、書類、家財、管理の順に、今の状況に合う確認記事を選べます。", "🗂️"),
    "land": ("森町の土地", "境界、道路、地目、災害リスク、土地利用を、判断する順番から探せます。", "🧭"),
    "farmland": ("森町の農地", "耕作、貸借、転用、水路、相続など、農地で最初に確かめる事項を選べます。", "🌾"),
    "forest": ("森町の山林", "境界、進入路、伐採、届出、災害リスク、家族への引継ぎを順に確認できます。", "🌲"),
    "business": ("森町で事業を始める", "開業場所、許認可、税、空き店舗、事業承継など、事業開始前の確認記事を選べます。", "🏪"),
    "work": ("森町で働く", "求人、通勤、農作業、働き方を、家族時間と移動条件から確認できます。", "💼"),
    "culture": ("森町の文化を調べる", "文化財、祭り、地域史を、資料の読み方と記録の残し方から探せます。", "🏛️"),
    "guide": ("森町の交通・訪問ガイド", "鉄道、バス、道路、徒歩、家族送迎など、往路と帰路を一緒に確認できます。", "🚉"),
    "records": ("森町の確認記録を作る", "行政、土地、家族、文化の情報を、次の担当へ渡せる記録様式から探せます。", "📚"),
    "agriculture": ("森町の農業・茶・森林", "農産物、茶畑、農道、農地、森林の確認記事を、現地と公的資料から選べます。", "🍵"),
}

STAGES = (
    ("まず状況を整理する", ("management", "inventory", "status", "records", "check", "consultation")),
    ("名義・境界・制度を確認する", ("registration", "boundary", "owner", "notice", "inquiry", "right", "tax")),
    ("現地・費用・管理方法を確認する", ("road", "repair", "cost", "maintenance", "utilities", "water", "vegetation", "risk")),
    ("家族や次の担当へ引き継ぐ", ("family", "archive", "log", "contact", "documents", "roles", "timeline")),
)


def e(value: object) -> str:
    return escape(str(value), quote=True)


def assign_stage(url: str, used: set[str]) -> str:
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    for label, words in STAGES:
        if any(word in slug for word in words):
            return label
    labels = [label for label, _ in STAGES]
    return labels[len(used) % len(labels)]


def build_hub(theme: str, items: list[dict]) -> str:
    title, description, emoji = THEMES[theme]
    groups = {label: [] for label, _ in STAGES}
    used: set[str] = set()
    for item in items:
        label = assign_stage(item["url"], used)
        groups[label].append(item)
        used.add(item["url"])
    # 空の段階をなくし、全記事が必ず一度だけ掲載されるよう均す。
    empty = [label for label, pages in groups.items() if not pages]
    for label in empty:
        donor = max(groups, key=lambda key: len(groups[key]))
        groups[label].append(groups[donor].pop())
    sections = []
    for number, (label, _) in enumerate(STAGES, 1):
        cards = "".join(
            f'<li><a href="{e(item["url"])}"><strong>{e(item["title"])}</strong>'
            f'<span>確認したい内容を先に答え、必要資料と公式確認先へ進みます。</span></a></li>'
            for item in groups[label]
        )
        sections.append(
            f'<section><p class="eyebrow">STEP {number}</p><h2>{e(label)}</h2>'
            f'<ul class="hub-list">{cards}</ul></section>'
        )
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}｜状況から読む記事を選ぶ | 森町ライフハック</title><meta name="description" content="{e(description)}"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/site.css?v=20260702"><style>.decision-flow{{display:grid;gap:1rem}}.hub-list{{display:grid;gap:.75rem;padding:0;list-style:none}}.hub-list a{{display:block;padding:1rem;border:1px solid #cad8d2;border-radius:12px;text-decoration:none}}.hub-list strong,.hub-list span{{display:block}}.hub-list span{{margin-top:.35rem;color:#4a5c55}}</style></head><body><!-- SEO-PHASE4-HUB --><!-- PART:header:START --><!-- PART:header:END --><!-- PART:disclaimer:START --><!-- PART:disclaimer:END --><main><div class="wrap"><p class="breadcrumb"><a href="/">静岡県森町ライフハック</a> ／ {e(title)}</p><section class="hero"><div class="hero-visual"><span aria-hidden="true">{emoji}</span><h1>{e(title)}｜どの記事から読むか</h1></div><div class="hero-body"><p class="lead">{e(description)}</p><p>記事を上から全部読む必要はありません。現在地に近い段階を選び、一つの記事で確認事項を整理してから次へ進んでください。</p></div></section><div class="decision-flow">{''.join(sections)}</div><section><h2>迷ったときの読み方</h2><p>住所や地番、名義、利用予定がまだ分からない場合は「まず状況を整理する」から始めます。申請、契約、工事、売却を決める前には、森町公式ページと担当窓口で対象条件を再確認してください。</p><p><a class="btn" href="/hub/property/">家・土地の総合案内へ戻る</a></p></section></div></main><!-- PART:footer:START --><!-- PART:footer:END --></body></html>'''


def main() -> None:
    publication = json.loads((ROOT / "data" / "seo-phase4-publication.json").read_text(encoding="utf-8"))
    counts = {}
    for theme in THEMES:
        prefix = f"/{theme}/"
        items = [item for item in publication if item["url"].startswith(prefix)]
        if not items:
            raise RuntimeError(f"判断ハブへ掲載する記事がありません: {theme}")
        out = ROOT / theme / "index.html"
        out.write_text(build_hub(theme, items), encoding="utf-8", newline="\n")
        counts[theme] = len(items)
    print("第4期判断ハブ生成: " + " / ".join(f"{key} {value}件" for key, value in counts.items()))


if __name__ == "__main__":
    main()
