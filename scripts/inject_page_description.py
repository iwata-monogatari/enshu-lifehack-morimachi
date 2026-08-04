#!/usr/bin/env python3
"""<meta name="description"> をページ固有の本文リード文から作り直す。

改修前の森町版は description がカテゴリ単位の定型文しか無く、
155ページに対してユニークな description は13種類しか存在しなかった
(例:「困った・相談したい」カテゴリの19ページが全て同一文言)。
重複 description は検索結果のスニペット品質を落とし、
OGP/FAQ構造化データの投資効果も相殺してしまう。

各ページ冒頭の <p class="lead"> は既にページ固有の要約になっているため、
これを description(および OGP/Twitter の description)の出典にする。

先に本スクリプト → 次に inject_ogp_meta.py の順で実行すること
(OGP は description を読み取って複製するため)。

使い方: python scripts/inject_page_description.py [--check]
"""
import argparse
import glob
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_LEN = 120  # 日本語の検索スニペットは概ね全角120字前後で切られる

LEAD_RE = re.compile(r'<p class="lead">(.*?)</p>', re.S)
DESC_RE = re.compile(r'(<meta name="description" content=")(.*?)(">)')
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")

SUFFIX = "（森町ライフハック／非公式）"


def to_text(fragment):
    text = html.unescape(TAG_RE.sub("", fragment))
    return WS_RE.sub(" ", text).strip()


def truncate(text, limit):
    """句点で切れる位置があればそこで、無ければ字数で切る。"""
    if len(text) <= limit:
        return text
    head = text[:limit]
    cut = head.rfind("。")
    if cut >= limit * 0.5:
        return head[: cut + 1]
    return head.rstrip("、 ") + "…"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    targets = sorted(glob.glob(os.path.join(ROOT, "life", "**", "index.html"), recursive=True))
    changed, no_lead, no_desc = [], [], []
    seen = {}

    for filepath in targets:
        rel = os.path.relpath(filepath, ROOT).replace(os.sep, "/")
        with open(filepath, encoding="utf-8") as f:
            src = f.read()

        lm = LEAD_RE.search(src)
        if not lm or not to_text(lm.group(1)):
            no_lead.append(rel)
            continue
        if not DESC_RE.search(src):
            no_desc.append(rel)
            continue

        desc = truncate(to_text(lm.group(1)), MAX_LEN)
        seen.setdefault(desc, []).append(rel)
        escaped = html.escape(desc, quote=True)

        new = DESC_RE.sub(lambda m: m.group(1) + escaped + m.group(3), src, count=1)
        if new != src:
            changed.append(rel)
            if not args.check:
                with open(filepath, "w", encoding="utf-8", newline="") as f:
                    f.write(new)

    dupes = {d: v for d, v in seen.items() if len(v) > 1}
    verb = "要更新" if args.check else "更新"
    print("対象 %d ページ / %s %d ページ / ユニークdescription %d 種" % (len(targets), verb, len(changed), len(seen)))
    if dupes:
        print("重複description %d 種:" % len(dupes))
        for d, v in list(dupes.items())[:5]:
            print("   %d件 %s" % (len(v), d[:50]))
    if no_lead:
        print("lead未検出 %d 件: %s" % (len(no_lead), no_lead[:10]))
    if no_desc:
        print("descriptionタグ未検出 %d 件: %s" % (len(no_desc), no_desc[:10]))
    return 1 if (no_lead or no_desc) else 0


if __name__ == "__main__":
    sys.exit(main())
