#!/usr/bin/env python3
"""OGP(og:*)と Twitter Card のメタタグを <head> へ注入する。

既存の <title> 先頭セグメントと <meta name="description"> を流用し、
og:image は assets/ogp/<category>/<slug>.png (generate_ogp_images.py の出力)を指す。
対象は life/**/index.html の全155ページ(categories.json は136件しか無いため使わない)。

<!-- OGP-META:START -->...<!-- OGP-META:END --> マーカーで冪等に管理する。

使い方: python scripts/inject_ogp_meta.py [--check]
"""
import argparse
import glob
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_ORIGIN = "https://morimachi.enshu-lifehack.com"
SITE_NAME = "森町ライフハック"

START = "<!-- OGP-META:START -->"
END = "<!-- OGP-META:END -->"
MARKER_RE = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)


def page_key(relpath):
    parts = relpath.replace(os.sep, "/").split("/")[:-1]
    cat = parts[1]
    slug = "-".join(parts[2:]) if len(parts) > 2 else "index"
    return cat, slug


def build_meta(title, desc, image_url, page_url):
    t = html.escape(title, quote=True)
    d = html.escape(desc, quote=True)
    return "".join(
        [
            '<meta property="og:type" content="website">',
            '<meta property="og:site_name" content="%s">' % SITE_NAME,
            '<meta property="og:locale" content="ja_JP">',
            '<meta property="og:title" content="%s">' % t,
            '<meta property="og:description" content="%s">' % d,
            '<meta property="og:url" content="%s">' % page_url,
            '<meta property="og:image" content="%s">' % image_url,
            '<meta property="og:image:width" content="1200">',
            '<meta property="og:image:height" content="630">',
            '<meta name="twitter:card" content="summary_large_image">',
            '<meta name="twitter:title" content="%s">' % t,
            '<meta name="twitter:description" content="%s">' % d,
            '<meta name="twitter:image" content="%s">' % image_url,
            '<link rel="canonical" href="%s">' % page_url,
        ]
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    targets = sorted(glob.glob(os.path.join(ROOT, "life", "**", "index.html"), recursive=True))
    changed, no_desc, no_anchor, no_image = [], [], [], []

    for filepath in targets:
        rel = os.path.relpath(filepath, ROOT).replace(os.sep, "/")
        with open(filepath, encoding="utf-8") as f:
            src = f.read()

        cat, slug = page_key(rel)
        page_url = SITE_ORIGIN + "/" + rel[: -len("index.html")]
        image_rel = "assets/ogp/%s/%s.png" % (cat, slug)
        if not os.path.exists(os.path.join(ROOT, image_rel)):
            no_image.append(rel)
        image_url = "%s/%s" % (SITE_ORIGIN, image_rel)

        m = re.search(r"<title>(.*?)\s*\|", src) or re.search(r"<title>(.*?)</title>", src)
        title = html.unescape(m.group(1).strip()) if m else slug

        dm = re.search(r'<meta name="description" content="(.*?)">', src)
        if not dm:
            no_desc.append(rel)
            continue
        desc = html.unescape(dm.group(1))

        block = START + build_meta(title, desc, image_url, page_url) + END

        if MARKER_RE.search(src):
            new = MARKER_RE.sub(lambda mm: block, src, count=1)
        else:
            idx = src.find('<link rel="icon"')
            if idx == -1:
                idx = src.find("</head>")
            if idx == -1:
                no_anchor.append(rel)
                continue
            new = src[:idx] + block + src[idx:]

        if new != src:
            changed.append(rel)
            if not args.check:
                with open(filepath, "w", encoding="utf-8", newline="") as f:
                    f.write(new)

    verb = "要更新" if args.check else "更新"
    print("対象 %d ページ / %s %d ページ" % (len(targets), verb, len(changed)))
    if no_desc:
        print("description未検出でスキップ %d 件: %s" % (len(no_desc), no_desc[:10]))
    if no_anchor:
        print("挿入位置未検出 %d 件: %s" % (len(no_anchor), no_anchor))
    if no_image:
        print("OGP画像が未生成 %d 件(generate_ogp_images.py を先に実行): %s" % (len(no_image), no_image[:10]))
    return 1 if (no_desc or no_anchor) else 0


if __name__ == "__main__":
    sys.exit(main())
