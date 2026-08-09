#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""検索意図台帳でCREATEになった生活ガイドを生成し、入口を既存ページへ追加する。"""
from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "search-expansion-pages.json"
DECISIONS = ROOT / "data" / "search-intent-200-decisions.json"
SITE = "https://morimachi.enshu-lifehack.com"
VERIFIED = "2026-08-09"
START = "<!-- SEARCH-EXPANSION-LINKS:START -->"
END = "<!-- SEARCH-EXPANSION-LINKS:END -->"
INTENT_START = "<!-- SEARCH-INTENT-COVERAGE:START -->"
INTENT_END = "<!-- SEARCH-INTENT-COVERAGE:END -->"


def e(value: object) -> str:
    return escape(str(value), quote=True)


def list_html(values: list[str]) -> str:
    return "".join(f"<li>{e(value)}</li>" for value in values)


def render(item: dict) -> str:
    href = item["href"]
    if href.startswith("/life/housing/"):
        hub_href, hub_label = "/hub/property/", "家・土地"
    elif href.startswith(("/life/start-living/", "/life/living-soon/")):
        hub_href, hub_label = "/hub/procedures/", "手続き・暮らし"
    else:
        hub_href, hub_label = "/hub/trouble/", "困った・緊急"
    sources = "".join(
        f'<a class="official-link" href="{e(source["url"])}" target="_blank" rel="noopener">'
        f'{e(source["label"])} <span>公式情報</span></a>'
        for source in item["sources"]
    )
    related = "".join(
        f'<a class="official-link" href="{e(url)}">関連ガイドを確認する <span>{e(url)}</span></a>'
        for url in item["related"]
    )
    faq = "".join(
        f'<details><summary>{e(row["q"])}</summary><p>{e(row["a"])}</p></details>'
        for row in item["faq"]
    )
    return f'''<!doctype html><html lang="ja"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(item["title"])} | 森町ライフハック</title>
<meta name="description" content="{e(item["description"])}">
<link rel="canonical" href="{SITE}{e(href)}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<!-- PART:head-css:START --><link rel="stylesheet" href="/assets/site.css?v=20260702"><!-- PART:head-css:END -->
</head><body>
<!-- PART:header:START --><header class="site"><div class="wrap"><a class="logo" href="/">森町ライフハック</a></div></header><!-- PART:header:END -->
<!-- PART:disclaimer:START --><div class="disclaimer"><div class="wrap">森町ライフハックは森町公式サイトではありません。最新・正確な情報は必ず公式ページで確認してください。</div></div><!-- PART:disclaimer:END -->
<main><div class="wrap">
<p class="breadcrumb"><a href="/">森町ライフハック</a> ／ <a href="{hub_href}">{hub_label}</a> ／ {e(item["title"])}</p>
<section class="hero"><div class="hero-visual"><span aria-hidden="true">🧭</span><h1>{e(item["title"])}</h1></div><div class="hero-body"><p class="lead">{e(item["conclusion"])}</p></div></section>
<section><h2 class="sec">対象になる人</h2><p>{e(item["audience"])}</p></section>
<section><h2 class="sec">最初にすること</h2><ol>{list_html(item["steps"])}</ol></section>
<section><h2 class="sec">用意しておくもの</h2><ul>{list_html(item["documents"])}</ul></section>
<section><h2 class="sec">費用と期限</h2><div class="grid"><div class="card"><h3>費用</h3><p>{e(item["fee"])}</p></div><div class="card"><h3>期限・急ぐ目安</h3><p>{e(item["deadline"])}</p></div></div></section>
<section><h2 class="sec">森町の窓口・連絡先</h2><div class="official"><p><strong>{e(item["window"])}</strong></p><p>{e(item["tel"])}</p></div></section>
<section><h2 class="sec">注意したいこと</h2><ul>{list_html(item["cautions"])}</ul></section>
<section><h2 class="sec">よくある質問</h2><div class="qa">{faq}</div></section>
<section><h2 class="sec">関連ページ</h2><div class="official">{related}</div></section>
<section><h2 class="sec">公式情報・出典</h2><div class="official">{sources}</div></section>
<section class="feedback-box" id="feedback"><h2 class="sec">これで解決しそうですか？</h2><p class="mini">いただいた反応はページ改善のためだけに使い、お名前や連絡先は取得しません。</p><div class="fb-actions"><button type="button" class="fb-btn" data-feedback="solved">解決しそう</button><button type="button" class="fb-btn" data-feedback="still_worried">まだ不安</button><button type="button" class="fb-btn" data-feedback="could_not_find">探している情報がなかった</button></div><p class="fb-thanks">ありがとうございました。今後のページ改善に役立てます。</p></section>
<p class="verified">最終確認日：{VERIFIED} ／ 本ページは公式情報を整理したものです。最新・正確な情報は必ず公式ページで確認してください。</p>
</div></main><!-- PART:footer:START --><!-- PART:footer:END -->
</body></html>
'''


def inject_inbound(items: list[dict]) -> int:
    by_source: dict[str, list[dict]] = {}
    for item in items:
        for source in item["inbound_from"]:
            by_source.setdefault(source, []).append(item)
    changed = 0
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    for source, targets in sorted(by_source.items()):
        path = ROOT / source.strip("/") / "index.html"
        if not path.is_file():
            raise FileNotFoundError(f"内部リンク元がありません: {source}")
        html = original = path.read_text(encoding="utf-8")
        links = "".join(
            f'<a class="official-link" href="{e(item["href"])}">{e(item["title"])}</a>'
            for item in sorted(targets, key=lambda row: row["href"])
        )
        block = f'{START}<section class="search-expansion-links"><h2 class="sec">関連する新しい確認ガイド</h2><div class="official">{links}</div></section>{END}'
        if pattern.search(html):
            html = pattern.sub(block, html)
        elif '<p class="verified">' in html:
            html = html.replace('<p class="verified">', block + '\n<p class="verified">', 1)
        else:
            html = html.replace("</main>", block + "\n</main>", 1)
        if html != original:
            path.write_text(html, encoding="utf-8", newline="\n")
            changed += 1
    return changed


def inject_intent_coverage() -> int:
    decisions = json.loads(DECISIONS.read_text(encoding="utf-8"))
    by_target: dict[str, list[dict]] = {}
    for row in decisions:
        if row["action"] != "CREATE":
            by_target.setdefault(row["final_url"], []).append(row)
    pattern = re.compile(re.escape(INTENT_START) + r".*?" + re.escape(INTENT_END), re.S)
    changed = 0
    for target, rows in sorted(by_target.items()):
        path = ROOT / target.strip("/") / "index.html"
        if not path.is_file():
            raise FileNotFoundError(f"検索意図の統合先がありません: {target}")
        html = original = path.read_text(encoding="utf-8")
        items = "".join(
            f'<li>{e(row["target_query"].removeprefix("森町").strip())}</li>'
            for row in sorted(rows, key=lambda value: value["number"])
        )
        block = (
            f'{INTENT_START}<section class="search-intent-coverage">'
            '<h2 class="sec">このページでまとめて確認する項目</h2>'
            '<p>同じ手続きや確認順序で解決できる質問を、ページを分けずにまとめています。</p>'
            f'<ul>{items}</ul></section>{INTENT_END}'
        )
        if pattern.search(html):
            html = pattern.sub(block, html)
        elif '<p class="verified">' in html:
            html = html.replace('<p class="verified">', block + '\n<p class="verified">', 1)
        else:
            html = html.replace("</main>", block + "\n</main>", 1)
        if html != original:
            path.write_text(html, encoding="utf-8", newline="\n")
            changed += 1
    return changed


def main() -> None:
    items = json.loads(DATA.read_text(encoding="utf-8"))
    if len(items) != 14:
        raise RuntimeError(f"CREATE判定14件と一致しません: {len(items)}")
    for item in items:
        path = ROOT / item["href"].strip("/") / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render(item), encoding="utf-8", newline="\n")
    changed = inject_inbound(items)
    covered = inject_intent_coverage()
    print(f"検索拡張ページ生成: {len(items)}件 / 入口更新: {changed}ページ / 意図統合: {covered}ページ")


if __name__ == "__main__":
    main()
