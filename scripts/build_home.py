# -*- coding: utf-8 -*-
"""トップページを生成する（抜本改修指示書 6 / 12.1 / 12.2 / 12.3）。

表示順は指示書 6.1 のとおり:
  1 サイト名と非公式表示  2 検索窓  3 緊急導線
  4 6つの生活場面  5 よく使われる手続き8件  6 状況別チェックリスト
  7 森町独自データベース  8 最新確認情報  9 運営者・編集方針
  10 必要な場合のみ事業相談導線

守ること:
  - 本文中のリンクは60以下（13カテゴリ全項目の展開表示をやめる）
  - 非公式である旨はファーストビュー内に1回だけ
  - 緊急導線には営業CTAを置かない

実行: python scripts/build_home.py
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
TODAY = "2026-08-05"
MORI_LP = "https://fudosan.atawi.link/areas/mori/"

PARTS = {
    name: (ROOT / "parts" / f"{name}.html").read_text(encoding="utf-8").strip()
    for name in ("header", "footer", "head-css")
}

DESCRIPTION = (
    "静岡県周智郡森町の住民票、税金、ごみ、子育て、介護、空き家、おくやみ、防災などを、"
    "暮らしの場面から探せる非公式生活ナビ。手続きの順番と森町公式の確認先を案内します。"
)

CHECKLISTS = [
    ("/checklist/moved-in/", "🏡", "森町に引っ越してきた", "転入届から水道・ごみ・犬の登録まで"),
    ("/checklist/married/", "💍", "結婚した", "婚姻届のあとに続く名義と住所の手続き"),
    ("/checklist/baby/", "👶", "子どもが生まれた", "出生届・児童手当・健診・保育園"),
    ("/checklist/job-change/", "💴", "転職した・退職した", "国民健康保険・国民年金・住民税"),
]

def esc(s: str) -> str:
    return escape(str(s or ""), quote=True)


def emergency_section() -> str:
    cards = "".join(
        f'<a class="urgent-card" href="{esc(e["href"])}">'
        f'<span class="urgent-icon" aria-hidden="true">{e["emoji"]}</span>'
        f'<span class="urgent-text"><span class="urgent-label">{esc(e["label"])}</span>'
        f'<span class="urgent-note">{esc(e["note"])}</span></span></a>'
        for e in HUBS["emergency_links"])
    return (
        '<section class="urgent" aria-labelledby="urgent-title">'
        '<h2 id="urgent-title">急いでいるとき</h2>'
        f'<div class="urgent-grid">{cards}</div>'
        '<p class="mini">命に関わるときは119番。この欄には広告・営業のご案内を表示しません。</p>'
        "</section>")


def hub_section() -> str:
    cards = "".join(
        f'<a class="hub-card" href="/hub/{h["slug"]}/">'
        f'<span class="hub-emoji" aria-hidden="true">{h["emoji"]}</span>'
        f'<span class="hub-text"><span class="hub-title">{esc(h["title"])}</span>'
        f'<span class="hub-desc">{esc(h["short"])}</span></span></a>'
        for h in HUBS["hubs"])
    return (
        '<section class="hubs" aria-labelledby="hubs-title">'
        '<h2 id="hubs-title">どの場面のことですか</h2>'
        '<p class="lead">近い場面を選ぶと、そこから必要な手続きのページへ進めます。</p>'
        f'<div class="hub-grid">{cards}</div></section>')


def frequent_section() -> str:
    items = "".join(
        f'<li><a href="{esc(f["href"])}">'
        f'<span class="freq-icon" aria-hidden="true">{f["emoji"]}</span>'
        f'{esc(f["label"])}</a></li>' for f in HUBS["frequent"])
    return ('<section class="frequent" aria-labelledby="freq-title">'
            '<h2 id="freq-title">よく使われる手続き</h2>'
            f'<ul class="freq-list">{items}</ul></section>')


def checklist_section() -> str:
    cards = "".join(
        f'<a class="section-card" href="{href}">'
        f'<span class="section-emoji" aria-hidden="true">{emoji}</span>'
        f'<span class="section-body"><span class="section-title">{esc(label)}</span>'
        f'<span class="section-desc">{esc(note)}</span></span></a>'
        for href, emoji, label, note in CHECKLISTS)
    return ('<section aria-labelledby="checklist-title">'
            '<h2 id="checklist-title">状況別チェックリスト</h2>'
            '<p class="lead">やることを順番に確認して、済んだものから消していけます。</p>'
            f'<div class="section-grid">{cards}</div></section>')


def database_section() -> str:
    cards = "".join(
        f'<a class="section-card" href="{esc(d["href"])}">'
        f'<span class="section-emoji" aria-hidden="true">{d["emoji"]}</span>'
        f'<span class="section-body"><span class="section-title">{esc(d["label"])}</span>'
        f'<span class="section-desc">{esc(d["note"])}</span></span></a>'
        for d in HUBS["databases"])
    return ('<section aria-labelledby="db-title">'
            '<h2 id="db-title">森町を知る・調べる</h2>'
            '<p class="lead">手続きではなく、森町そのものを調べるための資料とツールです。</p>'
            f'<div class="section-grid">{cards}</div></section>')


def freshness_section(stats: dict) -> str:
    extra = ""
    if stats["partial"]:
        extra += (f'<li><b>一部確認中：{stats["partial"]}件</b>'
                  "－ 国の制度と森町公式ページの記載に差があるなど、"
                  "追加の確認が必要なページです。該当ページに理由を書いています。</li>")
    if stats["needs_review"]:
        extra += (f'<li><b>再確認が必要：{stats["needs_review"]}件</b>'
                  "－ 確認日または公式出典が記録できていないページです。"
                  "確認済みとしては数えていません。</li>")
    return (
        '<section class="freshness" aria-labelledby="fresh-title">'
        '<h2 id="fresh-title">情報の確認状況</h2>'
        f'<p>暮らしのページは {stats["pages"]} 件です。'
        f'このうち {stats["verified"]} 件は、窓口名・電話番号・受付時間・費用・期限・必要書類・'
        f'公式リンクを確認したうえで最終確認日を表示しています'
        f'（{stats["oldest"]}〜{stats["latest"]}）。</p>'
        + (f"<ul>{extra}</ul>" if extra else "")
        + "<p>電話番号・受付時間・金額・期限は変わることがあります。"
        "各ページの公式リンクで最終確認してください。</p>"
        '<a class="btn" href="https://www.town.morimachi.shizuoka.jp/" target="_blank" '
        'rel="noopener" data-track-click="official_link_click">森町公式サイトの新着を見る</a>'
        "</section>")


def publisher_section() -> str:
    return (
        '<section class="publisher" aria-labelledby="pub-title">'
        '<h2 id="pub-title">運営者と編集方針</h2>'
        f"<p>{esc(SITE_NAME)}は、富士ヶ丘サービス株式会社（代表 大石浩之・宅地建物取引士）が運営する"
        "非公式の案内サイトです。行政機関ではありません。公式資料をもとに整理し、"
        "各ページに出典と最終確認日を表示しています。医療・法律・税務の専門判断は行いません。</p>"
        '<div class="pub-links">'
        '<a class="btn" href="/about/author/">執筆者と編集方針を見る</a>'
        '<a class="btn" href="/terms/">利用条件・免責・誤りのご連絡</a>'
        "</div></section>")


def consult_section() -> str:
    """事業相談導線（指示書 6.1-10 / 11.1 / 修正指示書21）。

    到達先は森町専用の相談ページ1つに統一する。複数サイトへ分散させない。
    """
    return (
        '<section class="company-strip cta-weak" aria-labelledby="consult-title">'
        '<h2 id="consult-title">森町の空き家・親の家を、売る前に整理したい方へ</h2>'
        "<p>まずは各ページの森町公式窓口をご確認ください。そのうえで、相続した実家や空き家、"
        "介護と住まいが同時に動く場合に、状況を整理するところから相談できます。"
        "富士ヶ丘サービス株式会社が磐田本社から森町へ出張対応します。</p>"
        '<div class="pub-links">'
        '<a class="btn btn-main" href="'
        + MORI_LP
        + "?utm_source=morimachi_lifehack&amp;utm_medium=referral"
        + '&amp;utm_campaign=morimachi_support&amp;utm_content=home" '
        + 'target="_blank" rel="noopener" data-track-click="cta_real_estate">'
        "森町の相談窓口を見る</a>"
        "</div>"
        '<p class="cta-disclosure">※このご案内は、本サイト運営会社（富士ヶ丘サービス株式会社）の'
        "民間サービスです。ご利用は任意で、森町の制度利用には影響しません。"
        "森町役場とは関係ありません。</p></section>")


def stats() -> dict:
    """記事台帳から集計する（修正指示書22）。件数をHTMLに直接書かない。

    「確認済み」に数えるのは review_status が verified のものだけ。
    partial（電話確認待ち・国と自治体で記載が食い違う）は別に数える。
    """
    ledger = json.loads((ROOT / "data" / "article-ledger.json").read_text(encoding="utf-8"))
    verified = [r for r in ledger if r["review_status"] == "verified"]
    partial = [r for r in ledger if r["review_status"] == "partial"]
    needs = [r for r in ledger if r["review_status"] == "needs_review"]
    dates = sorted(r["last_verified_at"] for r in verified if r["last_verified_at"])
    return {
        "pages": len(ledger),
        "verified": len(verified),
        "partial": len(partial),
        "needs_review": len(needs),
        "latest": dates[-1] if dates else TODAY,
        "oldest": dates[0] if dates else TODAY,
    }


def build() -> str:
    st = stats()
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>静岡県森町ライフハック｜手続き・介護・空き家を困りごとから探す</title>
<meta name="description" content="{esc(DESCRIPTION)}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<!-- PART:head-css:START -->{PARTS['head-css']}<!-- PART:head-css:END -->
<link rel="stylesheet" href="/assets/home-blog.css?v=20260805a">
</head>
<body class="hub home">
<!-- PART:header:START -->{PARTS['header']}<!-- PART:header:END -->
<main><div class="wrap">
<section class="hero">
<figure class="hero-visual">
<picture>
<source srcset="/assets/img/hero-morimachi.svg" type="image/svg+xml">
<img src="/assets/img/hero-morimachi.svg" width="1600" height="460" fetchpriority="high" decoding="async"
 alt="静岡県周智郡森町の里山のイラスト。奥に山並み、中景に鎮守の森と鳥居、手前に太田川と茶畑の畝。">
</picture>
<figcaption>静岡県周智郡森町（遠州森町）／イラスト</figcaption>
</figure>
<p class="eyebrow">森町の暮らしと手続きが、すぐわかる</p>
<h1>静岡県森町の手続き・相談先を、困りごとから探せます</h1>
<p class="lead">住民票、税金、ごみ、子育て、介護、空き家、おくやみ、防災。
森町ライフハックは、<b>静岡県周智郡森町（遠州森町）</b>の暮らしと手続きを整理する案内サイトです。
<b>森町公式サイトではありません</b>。公式情報を整理し、最後は必ず公式ページへご案内します。</p>
<div class="home-shortcuts" aria-label="読み物とよくある質問">
<a class="home-blog-shortcut" href="/blog/">
<span class="home-blog-shortcut-icon" aria-hidden="true">✍️</span>
<span><strong>森町ブログ</strong><small>大石浩之が書く、森町の暮らしの記事</small></span>
<span class="home-blog-shortcut-arrow" aria-hidden="true">→</span>
</a>
<a class="home-blog-shortcut home-question-shortcut" href="/questions/">
<span class="home-blog-shortcut-icon" aria-hidden="true">💬</span>
<span><strong>森町の100の質問</strong><small>疑問から、答えと公式確認先を探す</small></span>
<span class="home-blog-shortcut-arrow" aria-hidden="true">→</span>
</a>
</div>
</section>

<section class="site-search" aria-labelledby="search-title">
<label id="search-title" for="site-search-input">調べたい言葉を入力してください</label>
<form class="search-row" role="search" action="/" method="get" onsubmit="return siteSearch(event)">
<input id="site-search-input" name="q" type="search" list="search-examples" autocomplete="off"
 placeholder="例：住民票、親が認知症、税金が払えない、空き家を相続した">
<button type="submit">探す</button>
</form>
<datalist id="search-examples"><option value="住民票"><option value="親が認知症"><option value="税金が払えない"><option value="空き家を相続した"><option value="ごみの日"><option value="夜に熱が出た"><option value="家族が亡くなった"></datalist>
<p class="mini">制度の正式名称でなくても、困っている状況の言葉で探せます。</p>
<div class="search-results" id="search-results" aria-live="polite"></div>
</section>

{emergency_section()}
{hub_section()}
{frequent_section()}
{checklist_section()}
{database_section()}
{freshness_section(st)}
{publisher_section()}
{consult_section()}
</div></main>
<script type="module" src="/assets/search-app.js"></script>
<!-- PART:footer:START -->{PARTS['footer']}<!-- PART:footer:END -->
</body></html>
"""


def main() -> None:
    html = build()
    (ROOT / "index.html").write_text(html, encoding="utf-8")
    body = html[html.index("<main>"):html.index("<!-- PART:footer:START -->")]
    body_links = len(re.findall(r"<a ", body))
    total_links = len(re.findall(r"<a ", html))
    print("index.html を生成しました")
    print(f"  本文リンク数: {body_links}（目安60以下）")
    print(f"  ページ全体のリンク数（フッター含む）: {total_links}")
    if body_links > 60:
        print("  [warn] 本文リンクが60を超えています")


if __name__ == "__main__":
    main()
