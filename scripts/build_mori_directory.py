#!/usr/bin/env python3
"""森町の施設・店舗・地域情報を、検索できる一覧ページへ生成する。"""

from __future__ import annotations

import html
import json
import os
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PARTS_DIR = ROOT / "parts"
OUT = ROOT / "mori-directory" / "index.html"
SITE = "https://morimachi.enshu-lifehack.com"


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return "、".join(str(item).strip() for item in value if str(item).strip())
    return str(value).strip()


def first(row: dict, *keys: str) -> str:
    for key in keys:
        value = text(row.get(key))
        if value:
            return value
    return ""


def clean_url(value: object) -> str:
    raw_url = text(value)
    match = re.match(r"https?://[^\s<>\"'（）]+", raw_url, re.I)
    if not match:
        return ""
    url = match.group(0)
    parsed = urlparse(url)
    return url if parsed.scheme in {"http", "https"} and parsed.netloc else ""


def load_json(path: Path, required: bool = True):
    if not path.exists():
        if required:
            raise FileNotFoundError("入力ファイルがありません: %s" % path)
        return {}
    with path.open(encoding="utf-8-sig") as stream:
        return json.load(stream)


def records_from(payload) -> list[dict]:
    rows = payload if isinstance(payload, list) else payload.get("records", [])
    return [row for row in rows if isinstance(row, dict)]


def key_name(value: object) -> str:
    value = unicodedata.normalize("NFKC", text(value)).casefold()
    return re.sub(r"[\s\-‐‑‒–—―・･\.。()（）【】\[\]]+", "", value)


def merge_values(base, added):
    if base in (None, "", [], {}):
        return added
    if added in (None, "", [], {}):
        return base
    if isinstance(base, dict) and isinstance(added, dict):
        result = dict(base)
        for key, value in added.items():
            result[key] = merge_values(result.get(key), value)
        return result
    if isinstance(base, list) or isinstance(added, list):
        items = base if isinstance(base, list) else [base]
        items += added if isinstance(added, list) else [added]
        result = []
        seen = set()
        for item in items:
            marker = json.dumps(item, ensure_ascii=False, sort_keys=True) if isinstance(item, dict) else text(item)
            if marker and marker not in seen:
                seen.add(marker)
                result.append(item)
        return result
    return base


def merge_records(main_rows: list[dict], extra_rows: list[dict]) -> list[dict]:
    merged: dict[str, dict] = {}
    order: list[str] = []
    for index, row in enumerate(main_rows + extra_rows):
        name = first(row, "name", "title", "facility_name", "spot_name")
        marker = key_name(name) or "unnamed-%d" % index
        if marker not in merged:
            merged[marker] = dict(row)
            order.append(marker)
        else:
            current = merged[marker]
            combined = merge_values(current, row)
            references = []
            for candidate in (current, row):
                raw_sources = candidate.get("sources", [])
                if isinstance(raw_sources, dict):
                    raw_sources = [raw_sources]
                if isinstance(raw_sources, list):
                    references.extend(raw_sources)
                source_url = clean_url(first(candidate, "source_url", "url"))
                if source_url:
                    references.append({
                        "url": source_url,
                        "name": first(candidate, "source_name") or "情報源",
                        "checked_at": first(candidate, "checked_at", "verified_at"),
                    })
            if references:
                combined["sources"] = merge_values([], references)
            merged[marker] = combined
    return [merged[marker] for marker in order]


def categories_of(row: dict) -> list[str]:
    raw = row.get("categories")
    values = raw if isinstance(raw, list) else []
    direct = first(row, "category_label", "category", "type", "genre")
    if direct:
        values = [direct] + values
    result = []
    for value in values:
        value = text(value)
        if value and value not in result:
            result.append(value)
    return result or ["その他"]


def category_of(row: dict) -> str:
    return categories_of(row)[0]


def source_links(row: dict) -> list[dict]:
    found = []
    raw = row.get("sources", [])
    if isinstance(raw, dict):
        raw = [raw]
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, str):
                url, label, checked = clean_url(item), "情報源", ""
            elif isinstance(item, dict):
                url = clean_url(first(item, "url", "source_url", "href"))
                label = first(item, "name", "label", "source_name", "title") or "情報源"
                checked = first(item, "checked_at", "verified_at", "accessed_at")
            else:
                continue
            if url:
                found.append({"url": url, "label": label, "checked_at": checked})
    direct_url = clean_url(first(row, "source_url", "url"))
    if direct_url:
        found.append({
            "url": direct_url,
            "label": first(row, "source_name", "website_name") or "公式・確認先",
            "checked_at": first(row, "checked_at", "verified_at", "accessed_at"),
        })
    official_url = clean_url(first(row, "official_url", "official_homepage", "website"))
    if official_url:
        found.append({"url": official_url, "label": "当事者の公式サイト", "checked_at": ""})
    unique = []
    seen = set()
    for item in found:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique.append(item)
    return unique


FIELD_MAP = (
    (("address", "所在地"), ("address", "location")),
    (("phone", "電話"), ("phone", "telephone", "tel")),
    (("hours", "営業時間・利用時間"), ("hours", "opening_hours", "business_hours")),
    (("closed", "休業日"), ("closed", "closed_days", "holiday")),
    (("price", "料金"), ("price", "fee", "admission")),
    (("parking", "駐車場"), ("parking",)),
    (("access", "交通・行き方"), ("access", "transport")),
    (("season", "時期・季節"), ("season", "best_season")),
    (("reservation", "予約"), ("reservation", "booking")),
)


def fact_rows(row: dict) -> list[tuple[str, str]]:
    result = []
    used_labels = set()
    for (_, label), keys in FIELD_MAP:
        value = first(row, *keys)
        if value:
            result.append((label, value))
            used_labels.add(label)
    facts = row.get("facts", [])
    if isinstance(facts, dict):
        facts = [{"label": key, "value": value} for key, value in facts.items()]
    if isinstance(facts, list):
        for fact in facts:
            if not isinstance(fact, dict):
                continue
            label = first(fact, "label", "name")
            value = first(fact, "value", "text")
            as_of = first(fact, "as_of")
            if label and value and label not in used_labels:
                result.append((label, value + ("（%s時点）" % as_of if as_of else "")))
                used_labels.add(label)
    return result


def card(row: dict, index: int) -> str:
    name = first(row, "name", "title", "facility_name", "spot_name") or "名称未確認"
    categories = categories_of(row)
    category = categories[0]
    area = first(row, "area", "district", "neighborhood")
    reading = first(row, "reading", "kana", "furigana")
    aliases = first(row, "aliases", "alias")
    summary = first(row, "summary", "description", "overview", "lead")
    status = first(row, "status")
    checked = first(row, "checked_at", "verified_at", "updated_at")
    search_blob = " ".join([name, reading, aliases, " ".join(categories), area, summary] + [value for _, value in fact_rows(row)])
    metadata = []
    if area:
        metadata.append('<span><span aria-hidden="true">📍</span> %s</span>' % esc(area))
    if reading:
        metadata.append('<span>読み：%s</span>' % esc(reading))
    if status:
        metadata.append('<span>収録状況：%s</span>' % esc(status))
    facts = fact_rows(row)
    details = ""
    if facts:
        details = '<dl class="directory-facts">%s</dl>' % "".join(
            '<div><dt>%s</dt><dd>%s</dd></div>' % (esc(label), esc(value)) for label, value in facts
        )
    links = source_links(row)
    link_html = "".join(
        '<li><a href="%s" target="_blank" rel="noopener noreferrer">%s<span class="visually-hidden">（外部サイト）</span></a>%s</li>'
        % (esc(item["url"]), esc(item["label"]), '<small>確認 %s</small>' % esc(item["checked_at"]) if item["checked_at"] else "")
        for item in links
    )
    return (
        '<article class="directory-card" data-directory-card data-categories="%s" data-search="%s" id="record-%d">'
        '<div class="directory-card__head"><div class="category-badges">%s</div><h2>%s</h2></div>'
        '%s%s%s%s%s</article>'
    ) % (
        esc("｜".join(categories)), esc(search_blob), index,
        "".join('<span class="category-badge">%s</span>' % esc(item) for item in categories), esc(name),
        '<p class="directory-meta">%s</p>' % "".join(metadata) if metadata else "",
        '<p class="directory-summary">%s</p>' % esc(summary) if summary else "",
        details,
        '<div class="directory-sources"><h3>公式・確認先</h3><ul>%s</ul></div>' % link_html if link_html else "",
        '<p class="directory-checked">最終確認：%s</p>' % esc(checked) if checked else "",
    )


def coverage_source(source: dict, fallback_count: int) -> str:
    name = first(source, "name", "source_name") or "収録データ"
    url = clean_url(first(source, "url", "source_url", "directory_url"))
    scope = first(source, "scope")
    checked = first(source, "checked_at", "verified_at")
    expected = first(source, "expected_records", "expected", "total")
    indexed = first(source, "indexed_records", "imported_records", "indexed", "count") or str(fallback_count)
    notes = first(source, "notes", "note")
    title = '<a href="%s" target="_blank" rel="noopener noreferrer">%s<span class="visually-hidden">（外部サイト）</span></a>' % (esc(url), esc(name)) if url else esc(name)
    values = ['<p class="coverage-name">%s</p>' % title]
    if scope:
        values.append('<p>%s</p>' % esc(scope))
    counts = "収録 %s件" % esc(indexed)
    if expected:
        counts += " ／ 確認対象 %s件" % esc(expected)
    values.append('<p class="coverage-count">%s</p>' % counts)
    if checked:
        values.append('<p class="coverage-date">確認日：%s</p>' % esc(checked))
    if notes:
        values.append('<p class="coverage-note">%s</p>' % esc(notes))
    links = source.get("links", [])
    if isinstance(links, list):
        link_items = []
        for item in links:
            if not isinstance(item, dict):
                continue
            item_url, label = clean_url(first(item, "url", "href")), first(item, "label", "name")
            if item_url and label:
                link_items.append('<li><a href="%s" target="_blank" rel="noopener noreferrer">%s<span class="visually-hidden">（外部サイト）</span></a></li>' % (esc(item_url), esc(label)))
        if link_items:
            values.append('<ul class="coverage-links">%s</ul>' % "".join(link_items))
    facts = source.get("facts", [])
    if isinstance(facts, list) and facts:
        rows = []
        for fact in facts:
            if not isinstance(fact, dict):
                continue
            label, value = first(fact, "label", "name"), first(fact, "value", "text")
            as_of, status = first(fact, "as_of"), first(fact, "status")
            if label and value:
                suffix = "".join("（%s）" % esc(item) for item in (as_of, status) if item)
                rows.append('<div><dt>%s</dt><dd>%s%s</dd></div>' % (esc(label), esc(value), suffix))
        if rows:
            values.append('<dl class="coverage-facts">%s</dl>' % "".join(rows))
    return '<article class="coverage-card">%s</article>' % "".join(values)


def load_parts() -> dict[str, str]:
    result = {}
    for name in ("head-css", "header", "disclaimer", "footer"):
        result[name] = (PARTS_DIR / (name + ".html")).read_text(encoding="utf-8").strip()
    return result


def part(name: str, content: str) -> str:
    return "<!-- PART:%s:START -->%s<!-- PART:%s:END -->" % (name, content, name)


def main() -> int:
    main_payload = load_json(DATA_DIR / "mori-directory.json")
    supplement = load_json(DATA_DIR / "mori-directory-supplement.json", required=False)
    rows = merge_records(records_from(main_payload), records_from(supplement))
    if not rows:
        raise ValueError("収録データが0件です")
    rows.sort(key=lambda row: (category_of(row), key_name(first(row, "name", "title", "facility_name", "spot_name"))))
    categories = sorted({category for row in rows for category in categories_of(row)})
    sources = []
    if isinstance(main_payload, dict) and isinstance(main_payload.get("source"), dict):
        source = dict(main_payload["source"])
        source.setdefault("checked_at", first(main_payload, "checked_at", "generated_at"))
        source.setdefault("indexed_records", len(records_from(main_payload)))
        sources.append(source)
    if isinstance(main_payload, dict) and isinstance(main_payload.get("sources"), list):
        sources.extend(item for item in main_payload["sources"] if isinstance(item, dict))
    if isinstance(supplement, dict) and isinstance(supplement.get("sources"), list):
        sources.extend(item for item in supplement["sources"] if isinstance(item, dict))
    generated_at = first(main_payload if isinstance(main_payload, dict) else {}, "generated_at", "checked_at")
    parts = load_parts()
    chips = '<button type="button" class="category-chip is-active" data-category-filter="all" aria-pressed="true">すべて <span>%d</span></button>' % len(rows)
    for category in categories:
        count = sum(category in categories_of(row) for row in rows)
        chips += '<button type="button" class="category-chip" data-category-filter="%s" aria-pressed="false">%s <span>%d</span></button>' % (esc(category), esc(category), count)
    source_html = "".join(coverage_source(item, len(rows)) for item in sources)
    if not source_html:
        source_html = coverage_source({"name": "地域情報台帳", "indexed_records": len(rows), "checked_at": generated_at}, len(rows))
    cards = "".join(card(row, index + 1) for index, row in enumerate(rows))
    schema_items = []
    for position, row in enumerate(rows, 1):
        name = first(row, "name", "title", "facility_name", "spot_name") or "名称未確認"
        item = {"@type": "ListItem", "position": position, "name": name}
        url = clean_url(first(row, "official_url", "website", "source_url", "url"))
        if url:
            item["url"] = url
        schema_items.append(item)
    schema = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "静岡県周智郡森町 地域情報台帳",
        "description": "森町の施設、店舗、自然、文化、特産品などを情報源と確認日付きで整理した検索用台帳です。",
        "url": SITE + "/mori-directory/",
        "spatialCoverage": {"@type": "Place", "name": "静岡県周智郡森町"},
        "mainEntity": {"@type": "ItemList", "numberOfItems": len(rows), "itemListElement": schema_items},
    }
    title = "静岡県周智郡森町の地域情報台帳｜施設・店舗・文化・自然"
    description = "静岡県周智郡森町の施設、店舗、農園、史跡、自然、特産品など%d件を、分類とキーワードから探せる地域情報台帳です。" % len(rows)
    body = f'''<!doctype html><html lang="ja"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | 森町ライフハック</title><meta name="description" content="{esc(description)}">
<link rel="canonical" href="{SITE}/mori-directory/"><meta property="og:type" content="website"><meta property="og:site_name" content="森町ライフハック"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{SITE}/mori-directory/">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
{part("head-css", parts["head-css"])}<link rel="stylesheet" href="/assets/mori-directory.css?v=20260811">
<script defer src="/assets/mori-directory.js?v=20260811"></script><script type="application/ld+json">{json.dumps(schema, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')}</script>
</head><body class="mori-directory-page">{part("header", parts["header"])}{part("disclaimer", parts["disclaimer"])}
<main id="main"><div class="wrap"><nav class="breadcrumbs" aria-label="パンくず"><a href="/">静岡県森町ライフハック</a> ／ 地域情報台帳</nav>
<header class="directory-hero"><p class="eyebrow">名前から引ける、出典付きの地域索引</p><h1>静岡県周智郡森町の地域情報台帳</h1><p class="lead">施設、店舗、農園、史跡、自然、特産品などを、固有名詞と分類から探せます。紹介文の転載ではなく、所在地や営業情報などの事実を確認先とともに整理しています。</p><p class="directory-total"><strong>{len(rows)}件</strong>収録{(' ／ データ作成 ' + esc(generated_at)) if generated_at else ''}</p></header>
<section class="directory-controls" aria-labelledby="directory-search-title"><h2 id="directory-search-title">台帳を検索する</h2><label for="directory-search">名称・地区・内容・住所など</label><div class="search-row"><input id="directory-search" type="search" inputmode="search" autocomplete="off" placeholder="例：とうもろこし、一宮、駐車場" aria-describedby="search-help"><button type="button" id="search-clear">入力を消す</button></div><p id="search-help" class="search-help">複数の語を空白で区切ると、すべてを含む情報に絞れます。</p><div class="category-chips" aria-label="分類で絞り込む">{chips}</div><p id="result-count" class="result-count" aria-live="polite">{len(rows)}件を表示</p></section>
<div id="directory-list" class="directory-list">{cards}</div><p id="no-results" class="no-results" hidden>条件に合う情報がありません。検索語を短くするか、「すべて」を選んでください。</p>
<section id="coverage" class="coverage-section" aria-labelledby="coverage-title"><h2 id="coverage-title">情報源ごとの収録状況</h2><p>対象件数と収録件数を出典単位で表示します。件数は重複整理や公開範囲により、元ページの表示件数と一致しない場合があります。</p><div class="coverage-grid">{source_html}</div></section>
<aside class="directory-notice" aria-labelledby="notice-title"><h2 id="notice-title">利用前にご確認ください</h2><p>この台帳は森町公式サイトではありません。営業時間、料金、販売時期、催し、交通、予約条件などは変わる場合があります。訪問や申込みの直前に、各カードの公式・確認先で最新情報を確認してください。</p><p>誤りや閉店・移転などを見つけた場合は、<a href="/terms/">利用条件・免責・誤りのご連絡</a>からお知らせください。</p></aside>
</div></main>{part("footer", parts["footer"])}
</body></html>'''
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(body, encoding="utf-8", newline="")
    print("生成: %s (%d件・%d分類)" % (OUT.relative_to(ROOT).as_posix(), len(rows), len(categories)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("生成を中止しました: %s" % exc, file=sys.stderr)
        sys.exit(1)
