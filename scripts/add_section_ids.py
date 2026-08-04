# -*- coding: utf-8 -*-
"""記事内の定型見出しに安定したid を付ける。

ページ内リンク（分岐カードの「詳しくはこの節」）が確実に着地するようにする。
見出し文言は生成テンプレートで固定されているため、文言→id の対応表で足りる。
冪等：すでに id がある見出しは触らない。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

SECTION_IDS = {
    "先に知っておきたいこと": "points",
    "不安を先につぶすQ&amp;A": "qa",
    "タイプ別・最初の一歩": "types",
    "行動のステップ": "steps",
    "今日動けること": "actions",
    "公式窓口・確認先": "official",
}


def main() -> None:
    files = added = 0
    for path in sorted((ROOT / "life").rglob("index.html")):
        html = original = path.read_text(encoding="utf-8")
        for text, sid in SECTION_IDS.items():
            pattern = re.compile(r'<h2 class="sec">' + re.escape(text) + r"</h2>")
            html, n = pattern.subn(f'<h2 class="sec" id="{sid}">{text}</h2>', html)
            added += n
        if html != original:
            path.write_text(html, encoding="utf-8")
            files += 1
    print(f"見出しid を付与: {files} ファイル / {added} 見出し")


if __name__ == "__main__":
    main()
