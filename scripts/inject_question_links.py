#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""選定した100問への入口を、対応する既存ガイドへ1件ずつ追加する。"""
from __future__ import annotations

import json
import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
START = "<!-- QUESTION-LINK:START -->"
END = "<!-- QUESTION-LINK:END -->"
MARKER_RE = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
sys.stdout.reconfigure(encoding="utf-8")


def block(row: dict) -> str:
    return (
        START
        + '<aside class="question-teaser" aria-label="この内容のよくある質問">'
        + '<p><span aria-hidden="true">💬</span> この内容のよくある質問</p>'
        + f'<a href="{escape(row["href"], quote=True)}" data-track-click="question_teaser">'
        + f'<strong>{escape(row["question"])}</strong><span>先に答えを確認する →</span></a>'
        + "</aside>"
        + END
    )


def main() -> int:
    rows = json.loads((ROOT / "data" / "questions.json").read_text(encoding="utf-8"))
    changed = 0
    for row in rows:
        path = ROOT / row["parent_href"].strip("/") / "index.html"
        html = path.read_text(encoding="utf-8")
        rendered = block(row)
        if MARKER_RE.search(html):
            updated = MARKER_RE.sub(lambda _: rendered, html, count=1)
        else:
            anchors = (
                '<h2 class="sec">あわせて確認したい',
                '<!-- CTA-BLOCK:START -->',
                '<section class="feedback-box"',
                '<p class="verified">',
            )
            pos = next((html.find(anchor) for anchor in anchors if html.find(anchor) >= 0), -1)
            if pos < 0:
                print(f"挿入位置が見つかりません: {row['parent_href']}")
                return 1
            updated = html[:pos] + rendered + html[pos:]
        if updated != html:
            path.write_text(updated, encoding="utf-8")
            changed += 1
    print(f"質問への入口を {len(rows)}ページで確認（更新 {changed}ページ）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
