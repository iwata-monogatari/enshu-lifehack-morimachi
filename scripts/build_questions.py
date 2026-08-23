#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""調査済みコンテンツから「森町のよくある100の質問」を生成する。

同じ親ページからは1問だけを選び、回答だけでなく、前提・確認順序・
森町公式の確認先・詳しい既存ガイドを付ける。質問の選定結果は
data/questions.json に書き出し、検索索引・sitemap・ハブから共用する。

実行: python scripts/build_questions.py
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
from html import escape, unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "data" / "content"
QUESTIONS_DIR = ROOT / "questions"
SITE = "https://morimachi.enshu-lifehack.com"
SITE_NAME = "静岡県森町ライフハック"
QUESTION_PUBLISHED = "2026-08-06"
sys.stdout.reconfigure(encoding="utf-8")

PARTS = {
    name: (ROOT / "parts" / f"{name}.html").read_text(encoding="utf-8").strip()
    for name in ("header", "footer", "head-css", "disclaimer")
}

HUBS = {
    "procedures": {"label": "手続き", "emoji": "📄", "quota": 28},
    "property": {"label": "家・土地", "emoji": "🏠", "quota": 20},
    "trouble": {"label": "困った・緊急", "emoji": "🆘", "quota": 18},
    "family": {"label": "子ども・家族", "emoji": "👶", "quota": 17},
    "care": {"label": "親・介護", "emoji": "👵", "quota": 9},
    "enjoy": {"label": "暮らしを楽しむ", "emoji": "🌳", "quota": 8},
}
PRIORITY = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
TAG_RE = re.compile(r"<[^>]+>")
GENERIC_QUESTIONS = {
    "何から手をつければいいですか",
    "何から手を付ければいいですか",
    "まず何から確認すればいいですか",
    "何を最初に確認すればよいですか",
    "どこに相談すればいいですか",
}


def load_redirects() -> dict[str, str]:
    """_redirects の完全一致301を、生成ページ内の古い内部URL補正に使う。"""
    redirects: dict[str, str] = {}
    for raw in (ROOT / "_redirects").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 3 and parts[0].startswith("/") and parts[1].startswith("/") and parts[2] == "301":
            redirects[parts[0]] = parts[1]
    return redirects


REDIRECTS = load_redirects()
SEARCH_PRIORITY = json.loads(
    (ROOT / "data" / "search-priority-pages.json").read_text(encoding="utf-8"))


def esc(value: object) -> str:
    return escape(str(value or ""), quote=True)


def plain(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(TAG_RE.sub("", value or ""))).strip()


def search_topic(row: dict) -> str:
    """台帳の検索語を、タイトルで読める日本語に整える。"""
    keyword = plain(row.get("keyword", ""))
    if not keyword:
        return plain(row.get("context", ""))
    parts = keyword.split()
    if parts and parts[0] == "森町":
        return "森町の" + "・".join(parts[1:])
    return "・".join(parts)


def description_for(answer: str, limit: int = 132) -> str:
    """検索結果の説明文を、途中で句点を足して壊さずに短くする。"""
    value = plain(answer)
    if len(value) <= limit:
        return value if value.endswith(("。", "！", "？")) else value + "。"
    return value[:limit].rstrip("、。！？ ") + "…"


def normalize_internal_links(value: str) -> str:
    for source, target in REDIRECTS.items():
        value = value.replace(f'href="{source}"', f'href="{target}"')
    return value


def page_path(href: str) -> Path:
    return ROOT / href.strip("/") / "index.html"


def load_content() -> dict[str, dict]:
    result: dict[str, dict] = {}
    for path in sorted(CONTENT_DIR.glob("*.json")):
        if path.stem.startswith("_"):
            continue
        for item in json.loads(path.read_text(encoding="utf-8")):
            if item.get("href"):
                result[item["href"]] = item
    return result


def question_rank(item: dict, index: int) -> tuple[int, int, int]:
    question = plain(item.get("question", ""))
    answer_length = len(plain(item.get("answer", "")))
    generic = 1 if question in GENERIC_QUESTIONS or question.startswith("まず何") else 0
    return generic, index, -answer_length


def slug_for(parent_href: str) -> str:
    parts = [part for part in parent_href.strip("/").split("/") if part]
    tail = parts[1:] if parts and parts[0] == "life" else parts
    if len(tail) == 1:
        tail.append("overview")
    return "-".join(tail[-2:])


def candidates() -> list[dict]:
    topics = json.loads((ROOT / "data" / "topics_master.json").read_text(encoding="utf-8"))
    content = load_content()
    rows: list[dict] = []
    for topic in topics:
        href = topic.get("href", "")
        hub = topic.get("hub", "")
        body = content.get(href)
        if (hub not in HUBS or topic.get("action") == "merge" or not body
                or not page_path(href).is_file() or not topic.get("sources_morimachi")):
            continue
        valid = [
            (idx, item) for idx, item in enumerate(body.get("qa", []))
            if len(plain(item.get("question", ""))) >= 5
            and len(plain(item.get("answer", ""))) >= 45
        ]
        if not valid:
            continue
        qa_index, qa = min(valid, key=lambda pair: question_rank(pair[1], pair[0]))
        context = topic.get("intent") or plain(topic.get("title", ""))
        rows.append({
            "parent_href": href,
            "slug": slug_for(href),
            "hub": hub,
            "hub_label": HUBS[hub]["label"],
            "icon": topic.get("icon") or HUBS[hub]["emoji"],
            "category": topic.get("category", ""),
            "priority": topic.get("priority", "P3"),
            "context": context,
            "parent_title": plain(topic.get("title", "")),
            "question": plain(qa.get("question", "")),
            "answer_html": normalize_internal_links(qa.get("answer", "")),
            "answer": plain(qa.get("answer", "")),
            "qa_index": qa_index,
            "lead": plain(body.get("lead", "")),
            "note": plain(body.get("note", "")),
            "real_cards": body.get("real_cards", [])[:3],
            "steps": body.get("steps", {}),
            "sources": topic.get("sources_morimachi", [])[:3],
            "verified_date": topic.get("verified_date") or topic.get("ai_checked_date") or "確認中",
            "keyword": topic.get("primary_keyword", ""),
            "needs": topic.get("needs", []),
            "audience": topic.get("audience", []),
        })
    return rows


def select_questions() -> list[dict]:
    rows = candidates()
    selected: list[dict] = []
    for hub, meta in HUBS.items():
        pool = [row for row in rows if row["hub"] == hub]
        pool.sort(key=lambda row: (
            PRIORITY.get(row["priority"], 9),
            1 if row["question"] in GENERIC_QUESTIONS else 0,
            1 if row.get("parent_href", "").count("/") <= 3 else 0,
            -len(row["sources"]),
            row["parent_href"],
        ))
        if len(pool) < meta["quota"]:
            raise RuntimeError(f"{hub} の質問候補が不足: {len(pool)} < {meta['quota']}")
        selected.extend(pool[:meta["quota"]])

    if len(selected) != 100:
        raise RuntimeError(f"質問数が100件ではありません: {len(selected)}")
    slugs = [row["slug"] for row in selected]
    if len(slugs) != len(set(slugs)):
        raise RuntimeError("質問URLのslugが重複しています")

    for number, row in enumerate(selected, 1):
        row["number"] = number
        row["href"] = f'/questions/{row["slug"]}/'
        row["search_topic"] = search_topic(row)
        row["title"] = f'{row["search_topic"]}｜{row["question"]}'
        row["description"] = description_for(row["answer"])
    return selected


def official_links(row: dict) -> str:
    links = []
    seen = set()
    for source in row["sources"]:
        url = source.get("url", "")
        if not url or url in seen:
            continue
        seen.add(url)
        links.append(
            f'<a class="official-link" href="{esc(url)}" target="_blank" rel="noopener" '
            f'data-track-click="question_official">{esc(source.get("label", "森町公式ページ"))} '
            '<span>森町公式</span></a>'
        )
    return "".join(links)


def cards_html(row: dict) -> str:
    cards = []
    for card in row["real_cards"]:
        cards.append(
            '<div class="question-point">'
            f'<h3><span aria-hidden="true">{esc(card.get("icon", "✓"))}</span> '
            f'{esc(card.get("title", "確認事項"))}</h3>'
            f'<p>{esc(card.get("body", ""))}</p></div>'
        )
    if not cards:
        return ""
    return '<h2 class="sec">先に確認したいこと</h2><div class="question-points">' + "".join(cards) + "</div>"


def steps_html(row: dict) -> str:
    labels = (("today", "今日確認する"), ("this_week", "次に進める"), ("outside", "家族・関係先と確認する"))
    items = []
    for key, label in labels:
        for value in row["steps"].get(key, []):
            items.append(f'<li><b>{esc(label)}</b><span>{esc(value)}</span></li>')
            if len(items) >= 6:
                break
        if len(items) >= 6:
            break
    if not items:
        return ""
    return '<h2 class="sec">確認の順番</h2><ol class="question-steps">' + "".join(items) + "</ol>"


def share_box(row: dict) -> str:
    page_url = SITE + row["href"]
    text = f'静岡県森町の質問「{row["question"]}」への回答'
    line_url = "https://social-plugins.line.me/lineit/share?url=%s&text=%s" % (
        urllib.parse.quote(page_url, safe=""), urllib.parse.quote(text, safe=""))
    return (
        '<section class="share-box" aria-label="このページをシェア">'
        '<h2 class="sec" style="margin-top:0">家族に送る</h2><div class="share-actions">'
        f'<a class="share-btn share-line" href="{esc(line_url)}" target="_blank" rel="noopener" '
        'data-track-click="share_line">LINEで送る</a>'
        f'<button type="button" class="share-btn share-copy" data-share-url="{esc(page_url)}" '
        'data-track-click="share_copy">リンクをコピー</button></div>'
        '<p class="share-copied" hidden>コピーしました</p></section>'
        '<script>(function(){var box=document.currentScript.previousElementSibling;'
        'var btn=box&&box.querySelector(".share-copy");if(!btn){return;}'
        'btn.addEventListener("click",function(){var url=btn.getAttribute("data-share-url");'
        'var done=function(){var msg=box.querySelector(".share-copied");if(msg){msg.hidden=false;'
        'setTimeout(function(){msg.hidden=true;},2500);}};if(navigator.clipboard&&navigator.clipboard.writeText)'
        '{navigator.clipboard.writeText(url).then(done);}else{done();}});})();</script>'
    )


def related_questions_html(row: dict, rows: list[dict]) -> str:
    """同じ生活場面を優先して、検索エンジンと読者に話題のまとまりを示す。"""
    candidates = [item for item in rows if item["href"] != row["href"]]
    candidates.sort(key=lambda item: (
        0 if item["category"] == row["category"] else 1,
        0 if item["hub"] == row["hub"] else 1,
        PRIORITY.get(item["priority"], 9),
        abs(item["number"] - row["number"]),
    ))
    links = []
    for item in candidates[:4]:
        links.append(
            f'<li><a href="{esc(item["href"])}" data-track-click="question_related">'
            f'<span>Q{item["number"]}</span><strong>{esc(item["question"])}</strong></a></li>'
        )
    return (
        '<section class="question-related" aria-labelledby="question-related-title">'
        '<h2 class="sec" id="question-related-title">同じ分野の質問</h2>'
        '<ul>' + "".join(links) + '</ul></section>'
    )


def cornerstone_links_html(row: dict) -> str:
    """質問から重要11ガイドへ文脈の合う内部リンクを返す。"""
    matching = [item for item in SEARCH_PRIORITY if row["hub"] in item["question_hubs"]]
    if not matching:
        return ""
    exact = [item for item in matching if item["href"] == row["parent_href"]]
    others = [item for item in matching if item["href"] != row["parent_href"]]
    if others:
        offset = row["number"] % len(others)
        others = others[offset:] + others[:offset]
    selected = (exact + others)[:3]
    links = "".join(
        f'<li><a href="{esc(item["href"])}" data-track-click="question_cornerstone">'
        f'{item["emoji"]} <strong>{esc(item["label"])}</strong> — '
        f'{esc(item["description"])}</a></li>'
        for item in selected
    )
    return (
        '<section class="question-cornerstones" aria-labelledby="question-cornerstones-title">'
        '<h2 class="sec" id="question-cornerstones-title">この分野の重要ガイド</h2>'
        f'<ul>{links}</ul></section>'
    )


def page_schema(row: dict) -> str:
    page = {
        "@type": "WebPage",
        "name": row["question"],
        "description": row["description"],
        "url": SITE + row["href"],
        "inLanguage": "ja",
        "datePublished": QUESTION_PUBLISHED,
        "author": {
            "@type": "Person",
            "name": "大石浩之",
            "url": SITE + "/about/author/",
        },
        "about": {
            "@type": "Thing",
            "name": row["search_topic"],
        },
        "mainEntity": {
            "@type": "Question",
            "name": row["question"],
            "acceptedAnswer": {
                "@type": "Answer",
                "text": row["answer"],
                "url": SITE + row["href"],
            },
        },
    }
    if iso_date := re.fullmatch(r"\d{4}-\d{2}-\d{2}", row.get("verified_date", "")):
        page["dateModified"] = iso_date.group(0)
    breadcrumb = {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": SITE_NAME, "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "森町のよくある100の質問", "item": SITE + "/questions/"},
            {"@type": "ListItem", "position": 3, "name": row["question"], "item": SITE + row["href"]},
        ],
    }
    data = {"@context": "https://schema.org", "@graph": [page, breadcrumb]}
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + '</script>'


def render_question(row: dict, previous: dict, following: dict, rows: list[dict]) -> str:
    premise = f'<p>{esc(row["lead"])}</p>' if row["lead"] else ""
    note = f'<div class="note">{esc(row["note"])}</div>' if row["note"] else ""
    return f"""<!doctype html>
<html lang="ja"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(row['title'])} | 森町ライフハック</title>
<meta name="description" content="{esc(row['description'])}">
<link rel="canonical" href="{SITE}{esc(row['href'])}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<!-- PART:head-css:START -->{PARTS['head-css']}<!-- PART:head-css:END -->
<link rel="stylesheet" href="/assets/questions.css?v=20260823a">
<link rel="stylesheet" href="/assets/search-tools.css?v=20260806a">
{page_schema(row)}
</head><body class="question-page">
<!-- PART:header:START -->{PARTS['header']}<!-- PART:header:END -->
<!-- PART:disclaimer:START -->{PARTS['disclaimer']}<!-- PART:disclaimer:END -->
<main><div class="wrap">
<p class="breadcrumb"><a href="/">{SITE_NAME}</a> ／ <a href="/questions/">森町のよくある100の質問</a> ／ 質問{row['number']}</p>
<article>
<section class="hero question-hero"><p class="eyebrow"><span aria-hidden="true">{esc(row['icon'])}</span> {esc(row['context'])}</p>
<h1>{esc(row['question'])}</h1><p class="lead">静岡県周智郡森町で「{esc(row['context'])}」ときの答えです。{esc(row['search_topic'])}について、確認する順番と公式窓口をまとめました。</p></section>
<section class="question-answer" aria-labelledby="answer-title"><p class="question-answer-kicker">先に結論</p>
<h2 id="answer-title">回答</h2><div>{row['answer_html']}</div></section>
<h2 class="sec">この回答の前提</h2>{premise}{note}
{cards_html(row)}
{steps_html(row)}
<h2 class="sec">森町公式の確認先</h2><div class="official"><p>制度・受付・対象条件は変更されることがあります。手続き前に公式ページまたは担当窓口で確認してください。</p>
{official_links(row)}</div>
<h2 class="sec">詳しい案内を読む</h2><a class="question-parent-link" href="{esc(row['parent_href'])}" data-track-click="question_parent">
<span>この質問の詳しいガイド</span><strong>{esc(row['parent_title'])}</strong><span aria-hidden="true">→</span></a>
{cornerstone_links_html(row)}
{related_questions_html(row, rows)}
<aside class="content-provenance" aria-label="執筆と確認情報"><h2>執筆・確認情報</h2><dl>
<div><dt>執筆者</dt><dd><a href="/about/author/">大石浩之（宅地建物取引士）</a></dd></div>
<div><dt>初回公開</dt><dd><time datetime="{QUESTION_PUBLISHED}">{QUESTION_PUBLISHED}</time></dd></div>
<div><dt>最終確認</dt><dd><time datetime="{esc(row['verified_date'])}">{esc(row['verified_date'])}</time></dd></div>
</dl><p>森町や関係機関の一次情報を基礎に、対象条件・日付・金額・連絡先を執筆者が確認しています。文章整理にAIを利用する場合も、出典と表現は執筆者が確認します。現地訪問・撮影を行った内容は、本文または写真説明に記載します。</p></aside>
{share_box(row)}
<nav class="question-pager" aria-label="前後の質問"><a href="{esc(previous['href'])}">← 質問{previous['number']}</a><a href="/questions/">100問の一覧</a><a href="{esc(following['href'])}">質問{following['number']} →</a></nav>
<p class="verified">最終確認日：{esc(row['verified_date'])} ／ このページは公表情報を整理した非公式案内です。</p>
</article></div></main>
<!-- PART:footer:START -->{PARTS['footer']}<!-- PART:footer:END -->
</body></html>
"""


def render_index(rows: list[dict]) -> str:
    groups = []
    for hub, meta in HUBS.items():
        cards = []
        for row in (item for item in rows if item["hub"] == hub):
            search_text = " ".join([row["question"], row["context"], row["keyword"], *row["needs"]])
            cards.append(
                f'<li class="question-card" data-question-card data-search="{esc(search_text.lower())}">'
                f'<a href="{esc(row["href"])}" data-track-click="question_index">'
                f'<span class="question-number">Q{row["number"]}</span>'
                f'<strong>{esc(row["question"])}</strong><span>{esc(row["context"])}</span></a></li>'
            )
        groups.append(
            f'<section class="question-group" id="questions-{hub}" data-question-group><h2><span aria-hidden="true">{meta["emoji"]}</span> '
            f'{esc(meta["label"])} <small>{len(cards)}問</small></h2><ul class="question-grid">{"".join(cards)}</ul></section>'
        )
    category_links = "".join(
        f'<a href="#questions-{hub}"><span aria-hidden="true">{meta["emoji"]}</span>{esc(meta["label"])}</a>'
        for hub, meta in HUBS.items()
    )
    return f"""<!doctype html>
<html lang="ja"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>森町のよくある100の質問｜手続き・介護・家・防災 | 森町ライフハック</title>
<meta name="description" content="静岡県周智郡森町の手続き、子育て、介護、家・土地、防災、施設について、よくある100の質問から答えと公式確認先を探せます。">
<link rel="canonical" href="{SITE}/questions/">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem","position":1,"name":"{SITE_NAME}","item":"{SITE}/"}},{{"@type":"ListItem","position":2,"name":"森町のよくある100の質問","item":"{SITE}/questions/"}}]}}</script>
<!-- PART:head-css:START -->{PARTS['head-css']}<!-- PART:head-css:END -->
<link rel="stylesheet" href="/assets/questions.css?v=20260823a">
</head><body class="hub questions-index">
<!-- PART:header:START -->{PARTS['header']}<!-- PART:header:END -->
<!-- PART:disclaimer:START -->{PARTS['disclaimer']}<!-- PART:disclaimer:END -->
<main><div class="wrap">
<p class="breadcrumb"><a href="/">{SITE_NAME}</a> ／ 森町のよくある100の質問</p>
<section class="hero"><p class="eyebrow"><span aria-hidden="true">💬</span> 困りごとを質問から探す</p>
<h1>森町のよくある100の質問</h1><p class="lead">制度名が分からなくても大丈夫です。今の疑問に近い質問を選ぶと、先に結論、確認する順番、森町公式の確認先が分かります。</p></section>
<nav class="question-category-nav" aria-label="質問の分野">{category_links}</nav>
<section class="question-filter" aria-labelledby="question-filter-title"><label id="question-filter-title" for="question-filter-input">質問を絞り込む</label>
<input id="question-filter-input" type="search" placeholder="例：住民票、介護、空き家、避難所"><p id="question-filter-count" aria-live="polite">100問を表示中</p></section>
{"".join(groups)}
<p class="verified">最終確認日：2026-08-06 ／ 回答は既存の調査済みガイドと森町公式ページをもとに整理しています。</p>
</div></main>
<script>(function(){{var input=document.getElementById('question-filter-input');var count=document.getElementById('question-filter-count');
if(!input){{return;}}input.addEventListener('input',function(){{var needle=input.value.trim().toLowerCase();var shown=0;
document.querySelectorAll('[data-question-card]').forEach(function(card){{var ok=!needle||card.getAttribute('data-search').indexOf(needle)!==-1;card.hidden=!ok;if(ok){{shown++;}}}});
document.querySelectorAll('[data-question-group]').forEach(function(group){{group.hidden=!group.querySelector('[data-question-card]:not([hidden])');}});
count.textContent=shown+'問を表示中';}});}})();</script>
<!-- PART:footer:START -->{PARTS['footer']}<!-- PART:footer:END -->
</body></html>
"""


def write_manifest(rows: list[dict]) -> None:
    public_rows = []
    for row in rows:
        public_rows.append({key: row[key] for key in (
            "number", "href", "slug", "parent_href", "parent_title", "title", "description",
            "question", "answer", "hub", "hub_label", "category", "icon", "priority", "context",
            "keyword", "needs", "audience", "sources", "verified_date")})
    (ROOT / "data" / "questions.json").write_text(
        json.dumps(public_rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main() -> int:
    rows = select_questions()
    QUESTIONS_DIR.mkdir(parents=True, exist_ok=True)
    for index, row in enumerate(rows):
        out_dir = QUESTIONS_DIR / row["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        previous = rows[index - 1] if index else rows[-1]
        following = rows[(index + 1) % len(rows)]
        (out_dir / "index.html").write_text(
            render_question(row, previous, following, rows), encoding="utf-8")
    (QUESTIONS_DIR / "index.html").write_text(render_index(rows), encoding="utf-8")
    write_manifest(rows)
    print(f"質問ページ {len(rows)}件 + 一覧1件を生成しました")
    for hub, meta in HUBS.items():
        print(f"  {meta['label']}: {sum(1 for row in rows if row['hub'] == hub)}件")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
