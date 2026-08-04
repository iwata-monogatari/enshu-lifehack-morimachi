#!/usr/bin/env python3
"""data/channels.json をもとに、<h1> 直後へチャネルバッジを注入する。

表示するのは**根拠が確認できたチャネルだけ**。
「オンライン不可」のような否定は一切描画しない（derive_channel_fields.py の設計判断を参照）。
非表示チャネルについて誤解が生じないよう、
バッジ群には「確認できた手続き方法」という肯定形のラベルを付け、
補足文はインスタントヘッダー側に表示する。

<!-- CHANNEL-BADGES:START/END --> マーカーで冪等に管理する。

使い方: python scripts/inject_channel_badges.py [--check]
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHANNELS = os.path.join(ROOT, "data", "channels.json")

START = "<!-- CHANNEL-BADGES:START -->"
END = "<!-- CHANNEL-BADGES:END -->"
MARKER_RE = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
H1_RE = re.compile(r"(<h1[^>]*>.*?</h1>)", re.S)

# AGENTS.md: 絵文字は装飾。必ず aria-hidden="true" を付けて読み上げ対象外にする。
LABELS = {
    "counter": ("🏛️", "窓口"),
    "phone": ("📞", "電話"),
    "online": ("🌐", "オンライン"),
    "konbini": ("🏪", "コンビニ"),
}
ORDER = ["counter", "phone", "online", "konbini"]


def build(channels):
    parts = [
        '<span class="channel-badge channel-%s"><span class="emoji" aria-hidden="true">%s</span>%s</span>'
        % (ch, LABELS[ch][0], LABELS[ch][1])
        for ch in ORDER
        if ch in channels
    ]
    if not parts:
        return ""
    return (
        '<div class="channel-badges" aria-label="確認できた手続き方法">'
        '<span class="channel-badges-label">確認できた手続き方法</span>%s</div>' % "".join(parts)
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    with open(CHANNELS, encoding="utf-8-sig") as f:
        records = json.load(f)

    changed, no_h1, missing, empty = [], [], [], 0
    for rec in records:
        filepath = os.path.join(ROOT, rec["url"].strip("/").replace("/", os.sep), "index.html")
        if not os.path.isfile(filepath):
            missing.append(rec["url"])
            continue
        src = open(filepath, encoding="utf-8").read()

        block = build(rec["channels"])
        if not block:
            empty += 1
        marker_block = START + block + END

        if MARKER_RE.search(src):
            new = MARKER_RE.sub(lambda m: marker_block, src, count=1)
        else:
            m = H1_RE.search(src)
            if not m:
                no_h1.append(rec["url"])
                continue
            new = src[: m.end()] + marker_block + src[m.end() :]

        if new != src:
            changed.append(rec["url"])
            if not args.check:
                with open(filepath, "w", encoding="utf-8", newline="") as f:
                    f.write(new)

    verb = "要更新" if args.check else "更新"
    print("対象 %d ページ / %s %d ページ / バッジ無し %d ページ" % (len(records), verb, len(changed), empty))
    if no_h1:
        print("<h1>未検出 %d 件: %s" % (len(no_h1), no_h1[:5]))
    if missing:
        print("ファイル未検出 %d 件: %s" % (len(missing), missing[:5]))
    return 1 if (no_h1 or missing) else 0


if __name__ == "__main__":
    sys.exit(main())
