#!/usr/bin/env python3
"""LINEシェア＋URLコピーのシェアボックスを feedback-box の直後へ注入する。

磐田版は categories.json の item.label を使うが、森町版の categories.json は
136件しか無いため、各ページの <title> 先頭セグメントを見出しに使って全155ページへ入れる。

プリセット文は「静岡県周智郡森町の<ページ名>、ここ見ると早いよ」。
02戦略編3の表記ルール(北海道茅部郡森町との混同回避)に従い「静岡県周智郡森町」と明示する。
シェアされた文面がそのままSNS上の表記になるため、ここは略さない。

<!-- SHARE-BOX:START/END --> マーカーで冪等に管理する。

使い方: python scripts/inject_share_box.py [--check]
"""
import argparse
import glob
import html
import os
import re
import sys
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_ORIGIN = "https://morimachi.enshu-lifehack.com"

START = "<!-- SHARE-BOX:START -->"
END = "<!-- SHARE-BOX:END -->"
MARKER_RE = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
FEEDBACK_RE = re.compile(r'<section class="feedback-box"[^>]*>.*?</section>', re.S)

TITLE_RE = re.compile(r"<title>(.*?)\s*\|")
TITLE_ANY_RE = re.compile(r"<title>(.*?)</title>", re.S)


# タイトル側にすでに地名が入っている場合、文頭の地名と重ならないようにする。
# （例：「静岡県周智郡森町の森町の放課後児童クラブ…」になってしまうのを防ぐ）
LEADING_PLACE_RE = re.compile(r"^(静岡県周智郡森町の|静岡県森町の|遠州森町の|森町の|森町)")


def build_share_box(label, page_url):
    body = LEADING_PLACE_RE.sub("", label).strip() or label
    line_text = "静岡県周智郡森町の%s、ここ見ると早いよ" % body
    line_href = "https://social-plugins.line.me/lineit/share?url=%s&text=%s" % (
        urllib.parse.quote(page_url, safe=""),
        urllib.parse.quote(line_text, safe=""),
    )
    esc_url = html.escape(page_url, quote=True)
    return (
        '<section class="share-box" aria-label="このページをシェア">'
        '<h2 class="sec" style="margin-top:0">友人・家族に送る</h2>'
        '<div class="share-actions">'
        '<a class="share-btn share-line" href="%s" target="_blank" rel="noopener" data-track-click="share_line">LINEで送る</a>'
        '<button type="button" class="share-btn share-copy" data-share-url="%s" data-track-click="share_copy">リンクをコピー</button>'
        "</div>"
        '<p class="share-copied" hidden>コピーしました</p>'
        "</section>"
        "<script>(function(){"
        "var box=document.currentScript.previousElementSibling;"
        "var btn=box&&box.querySelector('.share-copy');"
        "if(!btn){return;}"
        "btn.addEventListener('click',function(){"
        "var url=btn.getAttribute('data-share-url');"
        "var done=function(){var msg=box.querySelector('.share-copied');if(msg){msg.hidden=false;setTimeout(function(){msg.hidden=true;},2500);}};"
        "var fallback=function(){var ta=document.createElement('textarea');ta.value=url;ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);ta.select();try{document.execCommand('copy');}catch(e){}document.body.removeChild(ta);done();};"
        "if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(url).then(done).catch(fallback);}"
        "else{fallback();}"
        "});"
        "})();</script>"
    ) % (line_href, esc_url)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    targets = sorted(glob.glob(os.path.join(ROOT, "life", "**", "index.html"), recursive=True))
    changed, skipped = [], []

    for filepath in targets:
        rel = os.path.relpath(filepath, ROOT).replace(os.sep, "/")
        page_url = SITE_ORIGIN + "/" + rel[: -len("index.html")]
        with open(filepath, encoding="utf-8") as f:
            src = f.read()

        m = TITLE_RE.search(src) or TITLE_ANY_RE.search(src)
        label = html.unescape(m.group(1).strip()) if m else rel

        block = START + build_share_box(label, page_url) + END

        if MARKER_RE.search(src):
            new = MARKER_RE.sub(lambda mm: block, src, count=1)
        else:
            fm = FEEDBACK_RE.search(src)
            if not fm:
                skipped.append(rel)
                continue
            new = src[: fm.end()] + block + src[fm.end() :]

        if new != src:
            changed.append(rel)
            if not args.check:
                with open(filepath, "w", encoding="utf-8", newline="") as f:
                    f.write(new)

    verb = "要更新" if args.check else "更新"
    print("対象 %d ページ / %s %d ページ" % (len(targets), verb, len(changed)))
    if skipped:
        print("feedback-box未検出でスキップ %d 件: %s" % (len(skipped), skipped[:10]))
    return 1 if skipped else 0


if __name__ == "__main__":
    sys.exit(main())
