# -*- coding: utf-8 -*-
"""title / description / パンくずに県名を入れ、北海道森町と区別する（修正指示書16）。

森町は静岡県周智郡と北海道茅部郡の2つある。「森町」だけで始まるタイトルが多いと、
検索エンジンからは地域の識別情報が不足して見える。

やること:
  - title の先頭に「静岡県森町」が分かる語を入れる（すでに入っていれば触らない）
  - description の冒頭を「静岡県周智郡森町の…」で始める
  - パンくずの先頭を「静岡県森町ライフハック」にする
  - 本文は書き換えない（不自然な繰り返しを避ける）

長さの目安は title 全角60字以内。超える場合はサイト名の付与をやめて内容を優先する。冪等。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

CITY = json.loads((ROOT / "data" / "city.json").read_text(encoding="utf-8"))
MUNI = CITY["municipality"]
SEO_NAME = MUNI["seo_name"]        # 静岡県森町
FULL_NAME = MUNI["full_name"]      # 静岡県周智郡森町
SITE_NAME = CITY["site_name"]      # 森町ライフハック

TITLE_MAX = 60


def has_prefecture(text: str) -> bool:
    return "静岡県" in text or "周智郡" in text


def fix_title(title: str) -> str:
    if has_prefecture(title):
        return title
    # 「森町の◯◯…」→「静岡県森町の◯◯…」。先頭以外の森町は触らない。
    if title.startswith("森町"):
        new = "静岡県" + title
    elif "森町" in title:
        new = re.sub("森町", SEO_NAME, title, count=1)
    else:
        new = f"{SEO_NAME}｜{title}"
    if len(new) > TITLE_MAX and f" | {SITE_NAME}" in new:
        new = new.replace(f" | {SITE_NAME}", "")
    return new


def fix_description(desc: str) -> str:
    if has_prefecture(desc):
        return desc
    if desc.startswith("森町"):
        return FULL_NAME + desc[len("森町"):]
    if "森町" in desc:
        return re.sub("森町", FULL_NAME, desc, count=1)
    return desc


def process(path: Path) -> dict[str, bool]:
    html = original = path.read_text(encoding="utf-8")
    flags = {"title": False, "desc": False, "crumb": False}

    m = re.search(r"<title>(.*?)</title>", html, re.S)
    if m:
        new = fix_title(m.group(1))
        if new != m.group(1):
            html = html[:m.start(1)] + new + html[m.end(1):]
            flags["title"] = True

    for attr, prop in (("name", "description"), ("property", "og:description"),
                       ("name", "twitter:description")):
        pattern = re.compile(rf'(<meta {attr}="{re.escape(prop)}" content=")(.*?)(">)', re.S)
        mm = pattern.search(html)
        if mm:
            new = fix_description(mm.group(2))
            if new != mm.group(2):
                html = pattern.sub(lambda x: x.group(1) + new + x.group(3), html, count=1)
                flags["desc"] = True

    # パンくずの先頭（サイト名）に県名を添える
    if f'<a href="/">{SITE_NAME}</a>' in html:
        html = html.replace(f'<a href="/">{SITE_NAME}</a>',
                            f'<a href="/">静岡県{SITE_NAME}</a>')
        flags["crumb"] = True
    # 構造化データの先頭要素も合わせる
    html = html.replace(f'"name":"{SITE_NAME}","item"', f'"name":"静岡県{SITE_NAME}","item"')

    if html != original:
        path.write_text(html, encoding="utf-8")
    return flags


def main() -> None:
    totals = {"title": 0, "desc": 0, "crumb": 0}
    long_titles = []
    for path in sorted(ROOT.rglob("*.html")):
        if {".git", "_cache", "node_modules", "reports", "parts", "data"} & set(
                path.relative_to(ROOT).parts):
            continue
        if path.name == "404.html":
            continue
        for k, v in process(path).items():
            totals[k] += 1 if v else 0
        m = re.search(r"<title>(.*?)</title>", path.read_text(encoding="utf-8"), re.S)
        if m and len(m.group(1)) > TITLE_MAX:
            long_titles.append((str(path.relative_to(ROOT)), len(m.group(1))))

    print(f"title に県名を追加      : {totals['title']} ページ")
    print(f"description に県名を追加: {totals['desc']} ページ")
    print(f"パンくずに県名を追加    : {totals['crumb']} ページ")
    if long_titles:
        print(f"[warn] title が{TITLE_MAX}字を超えるページ {len(long_titles)} 件（先頭で内容が分かるか要確認）")
        for f, n in long_titles[:8]:
            print(f"   {n}字 {f}")


if __name__ == "__main__":
    main()
