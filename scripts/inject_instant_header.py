#!/usr/bin/env python3
"""インスタントヘッダー（要点先出し）を hero セクションの直後へ注入する。

「このページで結局どこに行けばいいのか」を、本文を読む前に1画面で分かるようにする。
表示するのは data/channels.json に根拠がある項目だけ（窓口・電話・受付時間・期限）。
値が無い項目は行ごと出さない。推測で埋めない。

チャネルバッジ側で『確認できた手続き方法』しか出していないため、
非表示チャネルが「不可」と誤解されないよう、注記をここに1文置く。

<!-- INSTANT-HEADER:START/END --> マーカーで冪等に管理する。

使い方: python scripts/inject_instant_header.py [--check]
"""
import argparse
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHANNELS = os.path.join(ROOT, "data", "channels.json")

START = "<!-- INSTANT-HEADER:START -->"
END = "<!-- INSTANT-HEADER:END -->"
MARKER_RE = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
HERO_RE = re.compile(r"<section class=\"hero\">.*?</section>", re.S)

TEL_NUM_RE = re.compile(r"0\d{1,3}-\d{2,4}-\d{3,4}")


def esc(s):
    return html.escape(str(s), quote=True)


def build(rec):
    rows = []
    if rec.get("window"):
        rows.append(
            '<div class="ih-row"><span class="ih-key"><span aria-hidden="true">🏛️</span> 窓口</span>'
            '<span class="ih-val">%s</span></div>' % esc(rec["window"])
        )
    if rec.get("tel"):
        tel_text = esc(rec["tel"])
        nums = TEL_NUM_RE.findall(rec["tel"])
        if nums:
            # 先頭の番号だけ発信リンクにする（複数窓口がある場合は本文で選んでもらう）
            link = '<a href="tel:%s" data-track-click="tel_tap">%s</a>' % (nums[0], tel_text)
        else:
            link = tel_text
        rows.append(
            '<div class="ih-row"><span class="ih-key"><span aria-hidden="true">📞</span> 電話</span>'
            '<span class="ih-val">%s</span></div>' % link
        )
    if rec.get("hours"):
        rows.append(
            '<div class="ih-row"><span class="ih-key"><span aria-hidden="true">🕘</span> 受付時間</span>'
            '<span class="ih-val">%s</span></div>' % esc(rec["hours"])
        )
    if rec.get("deadline"):
        rows.append(
            '<div class="ih-row"><span class="ih-key"><span aria-hidden="true">⏳</span> 期限</span>'
            '<span class="ih-val">%s</span></div>' % esc(rec["deadline"])
        )

    if not rows:
        return ""

    note = (
        '<p class="ih-note">上の「確認できた手続き方法」は、公表資料で確認できたものだけを表示しています。'
        "表示が無い方法が使えないという意味ではありません。最新の取り扱いは窓口にご確認ください。</p>"
    )
    checked = (
        '<p class="ih-checked">最終確認日：%s</p>' % esc(rec["last_checked"]) if rec.get("last_checked") else ""
    )
    return (
        '<aside class="instant-header" aria-label="このページの要点">'
        '<p class="ih-title">先に結論</p>%s%s%s</aside>' % ("".join(rows), note, checked)
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    with open(CHANNELS, encoding="utf-8-sig") as f:
        records = json.load(f)

    changed, no_hero, missing, empty = [], [], [], 0
    for rec in records:
        filepath = os.path.join(ROOT, rec["url"].strip("/").replace("/", os.sep), "index.html")
        if not os.path.isfile(filepath):
            missing.append(rec["url"])
            continue
        src = open(filepath, encoding="utf-8").read()

        block = build(rec)
        if not block:
            empty += 1
        marker_block = START + block + END

        if MARKER_RE.search(src):
            new = MARKER_RE.sub(lambda m: marker_block, src, count=1)
        else:
            m = HERO_RE.search(src)
            if not m:
                no_hero.append(rec["url"])
                continue
            new = src[: m.end()] + marker_block + src[m.end() :]

        if new != src:
            changed.append(rec["url"])
            if not args.check:
                with open(filepath, "w", encoding="utf-8", newline="") as f:
                    f.write(new)

    verb = "要更新" if args.check else "更新"
    print("対象 %d ページ / %s %d ページ / 要点なし %d ページ" % (len(records), verb, len(changed), empty))
    if no_hero:
        print("heroセクション未検出 %d 件: %s" % (len(no_hero), no_hero[:5]))
    if missing:
        print("ファイル未検出 %d 件: %s" % (len(missing), missing[:5]))
    return 1 if (no_hero or missing) else 0


if __name__ == "__main__":
    sys.exit(main())
