# -*- coding: utf-8 -*-
"""統合先を「親ページ」に仕立てる（抜本改修指示書 5.3 / 7 / 8.1 / 8.2）。

  1. H1・title・description を、統合後の広い守備範囲に合わせて書き直す
  2. 「あなたはどのケースですか」の分岐カードを、先に結論のすぐ下に入れる
  3. パンくずの現在地表記・OGP・canonical・検索インデックスの表題を合わせる

分岐の内容は data/parent-pages.json が唯一の根拠。冪等（マーカーで管理）。
"""
from __future__ import annotations

import json
import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

SPEC = json.loads((ROOT / "data" / "parent-pages.json").read_text(encoding="utf-8"))
CITY = json.loads((ROOT / "data" / "city.json").read_text(encoding="utf-8"))
SITE = CITY["site_url"].rstrip("/")
SITE_NAME = CITY["site_name"]

START, END = "<!-- BRANCH-BLOCK:START -->", "<!-- BRANCH-BLOCK:END -->"


def esc(s: str) -> str:
    return escape(str(s or ""), quote=True)


def branch_html(spec: dict) -> str:
    cards = []
    for b in spec["branches"]:
        href = b["href"]
        is_tel = href.startswith("tel:")
        attrs = ' data-track-click="tel_tap"' if is_tel else ""
        cards.append(
            f'<a class="case-card" href="{esc(href)}"{attrs}>'
            f'<span class="case-icon" aria-hidden="true">{b["emoji"]}</span>'
            f'<span class="case-text">'
            f'<span class="case-when">{esc(b["case"])}</span>'
            f'<span class="case-do">{esc(b["action"])}</span>'
            f"</span></a>")
    return (
        START
        + f'<section class="case-branch" aria-labelledby="case-title">'
        + f'<h2 class="sec" id="case-title">{esc(spec["branch_title"])}</h2>'
        + f'<p class="lead">{esc(spec["branch_lead"])}</p>'
        + f'<div class="case-grid">{"".join(cards)}</div></section>'
        + END
    )


def apply(spec: dict) -> str:
    path = ROOT / spec["url"].strip("/") / "index.html"
    if not path.exists():
        return f"  [!!] ページがありません: {spec['url']}"
    html = path.read_text(encoding="utf-8")
    old_h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    old_h1_text = re.sub(r"<[^>]+>", "", old_h1.group(1)).strip() if old_h1 else ""

    h1, title, desc = spec["h1"], spec["title"], spec["description"]
    full_title = f"{title} | {SITE_NAME}"
    url = SITE + spec["url"]

    # H1
    html = re.sub(r"(<h1[^>]*>).*?(</h1>)", lambda m: m.group(1) + esc(h1) + m.group(2),
                  html, count=1, flags=re.S)
    # title / description
    html = re.sub(r"<title>.*?</title>", f"<title>{esc(full_title)}</title>",
                  html, count=1, flags=re.S)
    html = re.sub(r'(<meta name="description" content=").*?(">)',
                  lambda m: m.group(1) + esc(desc) + m.group(2), html, count=1, flags=re.S)
    # OGP / Twitter
    for prop, val in (("og:title", h1), ("og:description", desc)):
        html = re.sub(rf'(<meta property="{prop}" content=").*?(">)',
                      lambda m, v=val: m.group(1) + esc(v) + m.group(2), html, flags=re.S)
    for name, val in (("twitter:title", h1), ("twitter:description", desc)):
        html = re.sub(rf'(<meta name="{name}" content=").*?(">)',
                      lambda m, v=val: m.group(1) + esc(v) + m.group(2), html, flags=re.S)
    # パンくずの現在地とBreadcrumbList
    if old_h1_text:
        html = html.replace("／ " + old_h1_text + "</p>", "／ " + esc(h1) + "</p>")
        html = html.replace(json.dumps(old_h1_text, ensure_ascii=False)[1:-1],
                            json.dumps(h1, ensure_ascii=False)[1:-1])

    # 分岐カード（先に結論＝インスタントヘッダーの直後に置く）
    block = branch_html(spec)
    if START in html:
        html = re.sub(re.escape(START) + r".*?" + re.escape(END), block, html, flags=re.S)
    else:
        anchor = "<!-- INSTANT-HEADER:END -->"
        if anchor in html:
            html = html.replace(anchor, anchor + "\n" + block, 1)
        else:
            html = re.sub(r"(</section>)", r"\1" + block, html, count=1)

    path.write_text(html, encoding="utf-8")
    return f"  {spec['url']}  分岐 {len(spec['branches'])} 件"


def sync_topics(specs: list[dict]) -> int:
    """topics_master.json のタイトルも合わせる（検索インデックスの表題になる）。"""
    path = ROOT / "data" / "topics_master.json"
    topics = json.loads(path.read_text(encoding="utf-8"))
    by_href = {t["href"]: t for t in topics}
    n = 0
    for spec in specs:
        t = by_href.get(spec["url"])
        if t and t.get("title") != spec["h1"]:
            t["title"] = spec["h1"]
            t["page_type"] = "parent"
            n += 1
    path.write_text(json.dumps(topics, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return n


def main() -> None:
    print(f"親ページの仕立て直し: {len(SPEC['pages'])} ページ")
    for spec in SPEC["pages"]:
        print(apply(spec))
    print(f"topics_master.json のタイトルを {sync_topics(SPEC['pages'])} 件同期しました")


if __name__ == "__main__":
    main()
