# -*- coding: utf-8 -*-
"""森町の紅葉（町全体INDEX）の特集ページ専用レンダラー。

通常の discover 記事は段落の羅列になるため、このページだけは
build_discover.article_html から委譲され、台帳の文面（lead /
direct_answer / body_sections / illustrations / sources）をそのまま使い、
スポットカード・チップ・チェックリスト・ステップ図などの構造で組む。
文面の正は台帳（data/discover-pages.json と discover-overrides.json）。
画像は hero_photo と fig1.svg / fig2.svg（写真）を使う。
"""
from __future__ import annotations

import html
import json


def e(text: object) -> str:
    return html.escape(str(text), quote=True)


SLUG = "morimachi-autumn-leaves-townwide-guide"
URL = f"https://morimachi.enshu-lifehack.com/discover/{SLUG}/"


def _section(row: dict, idx: int, extra_class: str = "") -> str:
    sec = row["body_sections"][idx]
    ps = "".join(f"<p>{e(p)}</p>" for p in sec["paragraphs"])
    cls = f"editorial-section al-sec {extra_class}".strip()
    return f'<section class="{cls}"><h3>{e(sec["heading"])}</h3>{ps}</section>'


def _group(gid: str, kicker: str, title: str, inner: str) -> str:
    return (
        f'<section class="al-group" id="{gid}">'
        f'<div class="al-group-head"><p class="al-kicker">{e(kicker)}</p>'
        f'<h2>{e(title)}</h2></div>{inner}</section>'
    )


def _figure(row: dict, number: int) -> str:
    item = row["illustrations"][number - 1]
    return (
        f'<figure class="al-photo"><img src="fig{number}.svg" width="960" height="560" '
        f'loading="lazy" alt="{e(item["alt"])}"><figcaption>{e(item["caption"])}</figcaption></figure>'
    )


def _chips(items: list[tuple[str, str]]) -> str:
    lis = "".join(
        f'<li><strong>{e(head)}</strong><span>{e(desc)}</span></li>' for head, desc in items
    )
    return f'<ul class="al-chips">{lis}</ul>'


FAQS = [
    ("森町の紅葉の見頃はいつですか？",
     "年によって変わるため、固定日では案内していません。小國神社・大洞院とも11月下旬の名所ですが、その年の色づきは、町公式の地点別写真に付いた「撮影日」と、神社・寺院の公式発信で確認してください。"),
    ("小國神社と大洞院は、どちらがおすすめですか？",
     "参拝と宮川沿いの散策、ことまち横丁での食事まで楽しみたいなら小國神社。静かな禅寺の境内と「森の石松」の伝承に触れたいなら大洞院です。初めてなら、一日一地点に絞るのがおすすめです。"),
    ("車がなくても行けますか？",
     "行けますが、二地点の周遊より一地点の往復が現実的です。帰りのバスや列車の時刻と、駅からの徒歩区間、タクシーの手配を先に確認してください。"),
    ("紅葉祭やライトアップはありますか？",
     "当年の公式告知がある年だけ計画してください。過去の写真や記事から今年の実施を推測せず、寺社や主催者の当年の案内を確認しましょう。"),
    ("雨の日でも楽しめますか？",
     "葉の色は濃く見えますが、石や苔、落ち葉で足元が滑りやすくなります。無理をせず、参拝を中心に短く切り上げるのがおすすめです。"),
]


def render(row: dict, parts: dict, count: int) -> str:
    canonical = URL
    keywords = row["primary_keyword"] + "、" + "、".join(row["secondary_keywords"])
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Article",
                "headline": row["title"],
                "description": row["description"],
                "mainEntityOfPage": canonical,
                "datePublished": row["published_at"],
                "dateModified": row["updated_at"],
                "author": {
                    "@type": "Person",
                    "name": "大石浩之",
                    "url": "https://morimachi.enshu-lifehack.com/about/author/",
                },
                "publisher": {"@type": "Organization", "name": "森町ライフハック"},
                "image": canonical + "cover.svg",
                "keywords": keywords,
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                    for q, a in FAQS
                ],
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "静岡県森町ライフハック",
                     "item": "https://morimachi.enshu-lifehack.com/"},
                    {"@type": "ListItem", "position": 2, "name": "静岡県森町100ガイド",
                     "item": "https://morimachi.enshu-lifehack.com/discover/"},
                    {"@type": "ListItem", "position": 3, "name": row["title"], "item": canonical},
                ],
            },
        ],
    }

    photo = row.get("hero_photo", "")
    if photo:
        hero_img = (
            f'<img src="{e(photo)}" width="1200" height="630" fetchpriority="high" '
            f'alt="{e(row.get("cover_alt", row["title"]))}"><span class="media-kind">写真</span>'
        )
    else:
        hero_img = (
            f'<img src="cover.svg" width="1200" height="630" fetchpriority="high" '
            f'alt="{e(row.get("cover_alt", row["title"]))}"><span class="media-kind">編集イラスト</span>'
        )

    provenance = f'''<aside class="content-provenance" aria-label="執筆と確認情報"><h2>執筆・確認情報</h2><dl><div><dt>執筆者</dt><dd><a href="/about/author/">大石浩之（宅地建物取引士）</a></dd></div><div><dt>初回公開</dt><dd><time datetime="{e(row["published_at"])}">{e(row["published_at"])}</time></dd></div><div><dt>最終更新</dt><dd><time datetime="{e(row["updated_at"])}">{e(row["updated_at"])}</time></dd></div><div><dt>一次情報確認</dt><dd><time datetime="{e(row["fact_checked_at"])}">{e(row["fact_checked_at"])}</time></dd></div></dl><p>公式情報を基礎に、対象条件・日付・金額・連絡先を執筆者が確認しています。文章整理にAIを利用する場合も、出典と表現は執筆者が確認します。現地訪問・撮影を行った内容は、本文または写真説明に記載します。</p></aside>'''

    sources = "".join(
        f'<li><a href="{e(s["url"])}" target="_blank" rel="noopener noreferrer">{e(s["title"])}</a>'
        f'<span>（{e(s["publisher"])}、{e(row["fact_checked_at"])}確認）</span></li>'
        for s in row["sources"]
    )

    checklist_items = [
        "両方の最近の写真と、その撮影日を見た",
        "参拝・駐車・道路の条件を確認した",
        "天気と日没の時刻を確認した",
        "帰りの便と、退出の時刻を決めた",
    ]
    checklist = "".join(
        f'<label><input type="checkbox"><span>{e(t)}</span></label>' for t in checklist_items
    )

    conclusion = f'''
<section class="al-conclusion" aria-label="まず結論">
<p class="al-kicker">まず結論</p>
<h2>どちらへ行く？ 二つの名所から選ぶ</h2>
<div class="al-spots">
<article class="al-spot">
<img src="fig1.svg" width="960" height="560" loading="lazy" alt="{e(row["illustrations"][0]["alt"])}">
<div class="al-spot-body"><h3>小國神社</h3>
<p class="al-spot-key">参拝 ＋ 宮川沿いの散策</p>
<p>遠江国一宮。参拝のあと、宮川沿いの散策と、ことまち横丁での食事まで、一度の訪問で楽しめます。</p>
<ul class="al-points"><li>朱色の橋と、川沿いのもみじ</li><li>ことまち横丁で食事・休憩</li><li>にぎやかな秋を楽しみたい人に</li></ul></div></article>
<article class="al-spot">
<div class="al-spot-banner" aria-hidden="true"><span>山あいの禅寺</span></div>
<div class="al-spot-body"><h3>大洞院</h3>
<p class="al-spot-key">禅寺参拝 ＋ 山あいの境内</p>
<p>曹洞宗の禅寺。山あいの静かな境内で、紅葉と「森の石松」の伝承に触れられます。</p>
<ul class="al-points"><li>静けさの中で過ごす秋</li><li>森の石松の伝承</li><li>食事・トイレは町なかで先に</li></ul></div></article>
</div>
<aside class="answer-box al-answer"><h2>先に結論</h2><p>{e(row["direct_answer"])}</p></aside>
</section>'''

    nav = '''<nav class="al-nav" aria-label="特集の目次">
<a href="#al-before">行く前に</a><a href="#al-spots">二つの名所</a><a href="#al-choose">選び方</a><a href="#al-access">行き方</a><a href="#al-manners">現地の過ごし方</a><a href="#al-seasons">季節の楽しみ</a><a href="#al-food">食と備え</a><a href="#al-record">記録</a><a href="#al-end">まとめ</a>
</nav>'''

    g1 = _group("al-before", "行く前に、これだけ", "見頃は「当てる」ものではなく、確かめるもの",
                _section(row, 0)
                + _chips([("撮影日", "その写真が撮られた日"), ("更新日", "ページが直された日"), ("訪問日", "あなたが行く日")])
                + _section(row, 1))

    g2 = _group("al-spots", "二つの名所を知る", "川沿いの神社と、山あいの禅寺",
                _section(row, 2) + _figure(row, 1) + _section(row, 3))

    g3 = _group("al-choose", "選び方のコツ", "欲張らず、一地点を深く",
                _section(row, 4) + _section(row, 5)
                + f'<section class="al-check"><h3>二地点に挑む日のチェック</h3>'
                  f'<p>二つ回るのは、この4つがそろった日だけにしましょう。</p>{checklist}</section>')

    photo_break = _figure(row, 2)

    g4 = _group("al-access", "行き方を組み立てる", "車でも、車なしでも",
                f'<div class="al-two-col"><div class="al-card">{_section(row, 6)}</div>'
                f'<div class="al-card">{_section(row, 7)}</div></div>')

    g5 = _group("al-manners", "現地での過ごし方", "混雑・マナー・雨の日",
                _chips([("人の混雑", "参道・橋・受付の前"), ("車の混雑", "駐車場の出入り"), ("撮影者の混雑", "構図待ちの列")])
                + _section(row, 8) + _section(row, 9) + _section(row, 10, "al-caution"))

    g6 = _group("al-seasons", "季節の移ろいを楽しむ", "青葉も、落葉も、秋のうち",
                _section(row, 11) + _section(row, 12) + _section(row, 13))

    g7 = _group("al-food", "食・休憩・備え", "無理のない一日を支えるもの",
                _section(row, 14) + _section(row, 15) + _section(row, 16))

    g8 = _group("al-record", "また来たくなる記録", "比べられるメモを残す",
                _chips([("訪問地点", "どちらの名所か"), ("確認日時", "いつの情報か"), ("色づきの範囲", "どこまで色づいたか"), ("落葉の状態", "どれくらい散ったか")])
                + _section(row, 17))

    g9 = (_section(row, 18, "al-panel-good") + _section(row, 19, "al-panel-note"))

    steps = (
        '<ol class="al-steps">'
        '<li><strong>町の公式</strong><span>地点ごとの写真の撮影日を比べる</span></li>'
        '<li><strong>寺社の公式</strong><span>参拝・駐車・催しを確認する</span></li>'
        '<li><strong>交通と天気</strong><span>帰りの便まで確かめて出発</span></li></ol>'
    )
    g10 = _group("al-end", "まとめ", "確認の順番は、シンプルに",
                 steps + _section(row, 20))

    author = row["body_sections"][21]
    author_ps = "".join(f"<p>{e(p)}</p>" for p in author["paragraphs"])
    author_sec = (
        f'<section class="al-author"><img src="/assets/img/oishi-hiroyuki.jpg" width="120" height="120" '
        f'loading="lazy" alt="大石浩之"><div><h2>{e(author["heading"])}</h2>{author_ps}</div></section>'
    )

    related = '''<section class="al-related"><h2>紅葉の森町を、もう少し</h2><div class="al-related-grid">
<a href="/discover/oguni-shrine-autumn-leaves/">小國神社の紅葉<span>宮川沿いの詳しい案内 →</span></a>
<a href="/discover/daitoin-autumn-ishimatsu/">大洞院の紅葉と石松<span>禅寺と伝承の案内 →</span></a>
<a href="/discover/enshu-mori-tea-guide/">森町のお茶<span>秋の町歩きのお供に →</span></a>
<a href="/discover/morimachi-wagashi-guide/">森町の和菓子<span>散策とお土産の楽しみ →</span></a>
</div></section>'''

    faq_items = "".join(
        f'<details><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in FAQS
    )
    faq_sec = (
        f'<section class="al-faq" id="al-faq"><p class="al-kicker">Q &amp; A</p>'
        f'<h2>よくある質問</h2>{faq_items}</section>'
    )

    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(row["title"])}</title><meta name="description" content="{e(row["description"])}"><link rel="canonical" href="{canonical}"><meta property="og:type" content="article"><meta property="og:title" content="{e(row["title"])}"><meta property="og:description" content="{e(row["description"])}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{canonical}cover.svg"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><!-- PART:head-css:START -->{parts['head-css']}<!-- PART:head-css:END --><link rel="stylesheet" href="/assets/discover.css?v=20260823a"><link rel="stylesheet" href="/assets/autumn-leaves.css?v=20261109c"><script type="application/ld+json">{json.dumps(schema, ensure_ascii=False, separators=(',', ':'))}</script></head><body class="discover-article"><!-- PART:header:START -->{parts['header']}<!-- PART:header:END --><!-- PART:disclaimer:START -->{parts['disclaimer']}<!-- PART:disclaimer:END --><main><article class="wrap editorial al-feature"><nav class="breadcrumb" aria-label="パンくず"><a href="/">静岡県森町ライフハック</a> ／ <a href="/discover/">静岡県森町{count}ガイド</a> ／ {e(row["category_label"])}</nav><header class="article-header"><p class="eyebrow">{e(row["category_label"])}｜最終確認 {e(row["fact_checked_at"])}</p><h1>{e(row["title"])}</h1><p class="lead">{e(row["lead"])}</p><figure class="hero-media">{hero_img}<figcaption>{e(row.get("cover_caption", ""))}</figcaption></figure></header>{conclusion}{nav}{provenance}{g1}{g2}{g3}{photo_break}{g4}{g5}{g6}{g7}{g8}{g9}{g10}{faq_sec}{author_sec}{related}<section class="official-sources"><h2>公式情報・確認先</h2><p>掲載内容は次の一次情報を基礎に整理しました。営業、料金、催し、交通は変わるため、出発前または手続き前にリンク先で最新情報を確認してください。</p><ul>{sources}</ul></section><section class="related-guides"><h2>静岡県森町の関連ガイド</h2><p><a class="btn" href="/discover/">{count}ガイドの検索・分類へ戻る</a></p></section></article></main><!-- PART:footer:START -->{parts['footer']}<!-- PART:footer:END --></body></html>'''
