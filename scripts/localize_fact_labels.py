# -*- coding: utf-8 -*-
"""公式窓口ブロックの内部キーを日本語ラベルに置き換える（抜本改修指示書 8.4 / 19 P0）。

  <p class="mini"><b>window</b>：…</p>  →  <p class="mini"><b>相談窓口</b>：…</p>

あわせて、電話番号の値を発信リンクにする（14.2「電話リンクに番号を文字でも表示」）。
内部データのキー（facts）は変更しない。表示だけを日本語にする。
冪等：すでに日本語化済みのページは変更しない。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

LABELS = {
    k: v for k, v in
    json.loads((ROOT / "data" / "fact-labels.json").read_text(encoding="utf-8")).items()
    if not k.startswith("_")
}

KEY_RE = re.compile(r'(<p class="mini"><b>)([A-Za-z][A-Za-z0-9_]*)(</b>：)')
# 「0538-85-2111」形式。#7119 や 119 のような短縮番号は本文表現を壊さないため対象外。
TEL_RE = re.compile(r"(?<![\d\->])(0\d{1,3}-\d{2,4}-\d{4})(?![\d\-<])")

unknown: dict[str, int] = {}


def label_of(key: str) -> str:
    if key in LABELS:
        return LABELS[key]
    unknown[key] = unknown.get(key, 0) + 1
    return key


def linkify_tel(segment: str) -> str:
    """1件の <p class="mini"> の値部分だけを対象に電話番号をリンク化する。"""
    return TEL_RE.sub(
        r'<a href="tel:\1" data-track-click="tel_tap">\1</a>', segment)


def convert(html: str) -> tuple[str, int]:
    count = 0

    def replace_row(m: re.Match) -> str:
        nonlocal count
        count += 1
        return m.group(1) + label_of(m.group(2)) + m.group(3)

    out = KEY_RE.sub(replace_row, html)

    # 公式窓口ブロック内の電話番号のみリンク化する
    def tel_row(m: re.Match) -> str:
        head, body = m.group(1), m.group(2)
        if "<a " in body:
            return m.group(0)
        return head + linkify_tel(body)

    out = re.sub(r'(<p class="mini"><b>[^<]*電話番号</b>：)(.*?)(?=</p>)',
                 tel_row, out)
    return out, count


def main() -> None:
    changed = rows = 0
    for path in sorted(ROOT.rglob("*.html")):
        if {".git", "_cache", "node_modules", "reports"} & set(path.relative_to(ROOT).parts):
            continue
        html = path.read_text(encoding="utf-8")
        out, n = convert(html)
        if out != html:
            path.write_text(out, encoding="utf-8")
            changed += 1
            rows += n
    print(f"日本語ラベル化: {changed} ファイル / {rows} 行")
    if unknown:
        print("【要確認】data/fact-labels.json に未登録のキー:")
        for k, v in sorted(unknown.items(), key=lambda kv: -kv[1]):
            print(f"  {k} ({v})")
    else:
        print("未登録キーはありません。")


if __name__ == "__main__":
    main()
