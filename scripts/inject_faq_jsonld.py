#!/usr/bin/env python3
"""各ページの Q&A ブロックから schema.org/FAQPage JSON-LD を生成し <head> へ注入する。

磐田版(enshu-lifehack-iwata)は categories.json の item.faq を出典にしているが、
森町版の categories.json は {id,label,url} のみの薄い台帳で faq を持たない。
一方 data/content/*.json の qa は 147件どまり(全155ページ中8ページが未収録)。

そこで森町版は「ページ本文の <details><summary>質問</summary>回答</details>」を出典とする。
- 全155ページを対象にできる
- 構造化データが必ず画面上の可視テキストと一致する(Googleの FAQPage 要件)

<!-- FAQ-JSONLD:START -->...<!-- FAQ-JSONLD:END --> マーカーで冪等に管理する。

使い方: python scripts/inject_faq_jsonld.py [--check]
  --check ... 書き込まず、差分が出るページ数だけ報告する(CI/検証用)
"""
import argparse
import glob
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

START = "<!-- FAQ-JSONLD:START -->"
END = "<!-- FAQ-JSONLD:END -->"
MARKER_RE = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)

# <details> 一塊を取る。summary と、それ以降(回答本体)に分ける。
DETAILS_RE = re.compile(r"<details\b[^>]*>(.*?)</details>", re.S | re.I)
SUMMARY_RE = re.compile(r"<summary\b[^>]*>(.*?)</summary>(.*)", re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def to_text(fragment):
    """HTML断片を、画面上の可視テキストと同じ素のテキストに落とす。"""
    # <br> や </p> は空白扱いにしてから他のタグを除去する
    frag = re.sub(r"<br\s*/?>", " ", fragment, flags=re.I)
    frag = re.sub(r"</(p|li|div)>", " ", frag, flags=re.I)
    text = TAG_RE.sub("", frag)
    text = html.unescape(text)
    return WS_RE.sub(" ", text).strip()


def extract_faq(html_src):
    """ページ本文の Q&A を [(question, answer), ...] で返す。"""
    faq = []
    for block in DETAILS_RE.findall(html_src):
        m = SUMMARY_RE.search(block)
        if not m:
            continue
        q = to_text(m.group(1))
        a = to_text(m.group(2))
        if q and a:
            faq.append((q, a))
    return faq


def build_jsonld(faq):
    data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in faq
        ],
    }
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="書き込まずに差分の有無だけ報告する")
    args = ap.parse_args()

    targets = sorted(glob.glob(os.path.join(ROOT, "life", "**", "index.html"), recursive=True))

    changed, no_faq, no_head = [], [], []
    total_q = 0

    for filepath in targets:
        rel = os.path.relpath(filepath, ROOT).replace(os.sep, "/")
        with open(filepath, encoding="utf-8") as f:
            src = f.read()

        faq = extract_faq(src)
        if not faq:
            no_faq.append(rel)
            continue
        total_q += len(faq)

        block = START + '<script type="application/ld+json">%s</script>' % build_jsonld(faq) + END

        if MARKER_RE.search(src):
            new = MARKER_RE.sub(lambda m: block, src, count=1)
        else:
            idx = src.find("</head>")
            if idx == -1:
                no_head.append(rel)
                continue
            new = src[:idx] + block + src[idx:]

        if new != src:
            changed.append(rel)
            if not args.check:
                with open(filepath, "w", encoding="utf-8", newline="") as f:
                    f.write(new)

    verb = "要更新" if args.check else "更新"
    print("対象 %d ページ / %s %d ページ / 設問 %d 件" % (len(targets), verb, len(changed), total_q))
    if no_faq:
        print("Q&A未検出でスキップ %d 件: %s" % (len(no_faq), no_faq[:10]))
    if no_head:
        print("</head>未検出でスキップ %d 件: %s" % (len(no_head), no_head))
    return 1 if no_head else 0


if __name__ == "__main__":
    sys.exit(main())
