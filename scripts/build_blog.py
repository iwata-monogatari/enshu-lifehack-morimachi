#!/usr/bin/env python3
"""data/blog-posts.json から /blog/ の一覧ページを生成し、記事の体裁を検証する。

記事の実体(blog/<slug>/index.html)は手書き。本スクリプトは
  1. 台帳と実ファイルの突き合わせ
  2. 品質ゲート(04指示書A-4)の機械チェック
  3. 一覧ページの生成
を担当する。

品質ゲート(機械で見られる範囲):
  - 出典セクション(post-sources)に外部リンクが1本以上あるか
    → 「一次情報を最低1つ含まない記事は公開しない」の最低限の担保
  - 著者表記(post-author)があるか(04決定8)
  - 表紙画像 cover.jpg があるか
  - タイトルの重複が無いか(02戦略編4-3の重複防止)
本文の内容が本当に一次情報かどうかは機械では判定できないため、最終判断は執筆者が行う。

使い方: python scripts/build_blog.py [--check]
"""
import argparse
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "data", "blog-posts.json")
PARTS_DIR = os.path.join(ROOT, "parts")
BLOG_DIR = os.path.join(ROOT, "blog")
SITE = "https://morimachi.enshu-lifehack.com"
SITE_NAME = "森町ライフハック"

AXIS_LABEL = {
    "mon": "手続き・制度",
    "tue": "空き家・実家・相続",
    "wed": "寺社・歴史",
    "thu": "農地・山林・茶畑",
    "fri": "地区めぐり",
    "sat": "祭礼・イベント",
    "sun": "移住・暮らし・データ",
}


def load_parts():
    parts = {}
    for name in ("head-css", "header", "disclaimer", "footer"):
        with open(os.path.join(PARTS_DIR, "%s.html" % name), encoding="utf-8") as f:
            parts[name] = f.read().strip()
    return parts


def part_markup(name, content):
    return "<!-- PART:%s:START -->%s<!-- PART:%s:END -->" % (name, content, name)


def audit(posts):
    """記事ごとの品質ゲート。問題があれば (slug, 理由) のリストを返す。"""
    problems = []
    seen_titles = {}
    for p in posts:
        slug = p["slug"]
        d = os.path.join(BLOG_DIR, slug)
        idx = os.path.join(d, "index.html")
        if not os.path.isfile(idx):
            problems.append((slug, "記事本体が無い: blog/%s/index.html" % slug))
            continue
        src = open(idx, encoding="utf-8").read()

        m = re.search(r'<ul class="post-sources">(.*?)</ul>', src, re.S)
        if not m or not re.search(r'href="https?://', m.group(1)):
            problems.append((slug, "出典(post-sources)に外部リンクが無い ← 品質ゲート未達"))
        if "post-author" not in src:
            problems.append((slug, "著者表記(post-author)が無い"))
        if not os.path.isfile(os.path.join(d, "cover.jpg")):
            problems.append((slug, "表紙 cover.jpg が無い"))
        if p["title"] in seen_titles:
            problems.append((slug, "タイトルが %s と重複" % seen_titles[p["title"]]))
        seen_titles[p["title"]] = slug
    return problems


def build_index(posts, parts):
    items = []
    for p in sorted(posts, key=lambda x: x["date"], reverse=True):
        axis = AXIS_LABEL.get(p.get("axis"), "")
        badge = '<span class="post-axis">%s</span>' % html.escape(axis) if axis else ""
        items.append(
            '<li class="post-item">'
            '<a class="post-item-link" href="/blog/%s/">'
            '<span class="post-item-date"><time datetime="%s">%s</time></span>'
            "%s"
            '<span class="post-item-title">%s</span>'
            '<span class="post-item-desc">%s</span>'
            "</a></li>"
            % (
                p["slug"],
                p["date"],
                p["date"].replace("-", "."),
                badge,
                html.escape(p["title"]),
                html.escape(p["description"]),
            )
        )

    lead = "静岡県周智郡森町（遠州森町）の暮らし・手続き・空き家・寺社について、公表情報を確認しながら書いています。"
    body = '<ul class="post-list">%s</ul>' % "".join(items) if items else '<p class="lead">記事はまだありません。</p>'

    return (
        '<!doctype html><html lang="ja"><head>\n'
        '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
        "<title>ブログ | %s</title>\n"
        '<meta name="description" content="%s">\n'
        '<link rel="canonical" href="%s/blog/">\n'
        '<meta property="og:type" content="website"><meta property="og:site_name" content="%s">'
        '<meta property="og:title" content="ブログ | %s"><meta property="og:description" content="%s">'
        '<meta property="og:url" content="%s/blog/"><meta name="twitter:card" content="summary">\n'
        '<link rel="icon" href="/favicon.svg" type="image/svg+xml">\n'
        "%s\n</head><body>\n%s\n%s\n"
        '<main id="main"><div class="wrap">\n'
        '<p class="breadcrumb"><a href="/">%s</a> ／ ブログ</p>\n'
        '<section class="hero"><div class="hero-visual"><h1><span aria-hidden="true">📝</span> ブログ</h1></div>'
        '<div class="hero-body"><p class="lead">%s</p></div></section>\n'
        "%s\n</div></main>\n%s\n</body></html>\n"
    ) % (
        SITE_NAME, lead, SITE, SITE_NAME, SITE_NAME, lead, SITE,
        part_markup("head-css", parts["head-css"]),
        part_markup("header", parts["header"]),
        part_markup("disclaimer", parts["disclaimer"]),
        SITE_NAME, lead, body,
        part_markup("footer", parts["footer"]),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    with open(LEDGER, encoding="utf-8-sig") as f:
        posts = json.load(f)["posts"]

    problems = audit(posts)
    if problems:
        print("品質ゲート未達 %d 件:" % len(problems))
        for slug, why in problems:
            print("  %s: %s" % (slug, why))
        print("→ 一覧は生成しません。記事を直してから再実行してください。")
        return 1

    parts = load_parts()
    html_out = build_index(posts, parts)
    out = os.path.join(BLOG_DIR, "index.html")
    os.makedirs(BLOG_DIR, exist_ok=True)
    if not args.check:
        with open(out, "w", encoding="utf-8", newline="") as f:
            f.write(html_out)
    print("記事 %d 件 / 品質ゲート未達 0 / 一覧: blog/index.html%s" % (len(posts), "（未書き込み:--check）" if args.check else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
