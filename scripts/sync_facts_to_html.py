# -*- coding: utf-8 -*-
"""topics_master.json の facts を、公開HTMLの「公式窓口・確認先」に反映する。

窓口名・電話番号・補足は台帳（topics_master.json の facts）が唯一の根拠。
台帳を直しても公開HTMLが古いままだと、確認したはずの内容が画面に出ない。
このスクリプトで両者を一致させる。

置き換えるのは公式窓口ブロックの `<p class="mini"><b>ラベル</b>：値</p>` の行だけで、
本文・Q&A・タイプ別などの執筆済みコンテンツには触らない。冪等。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

LABELS = {k: v for k, v in
          json.loads((ROOT / "data" / "fact-labels.json").read_text(encoding="utf-8")).items()
          if not k.startswith("_")}

OFFICIAL_BLOCK_RE = re.compile(
    r'(<h2 class="sec"[^>]*>公式窓口・確認先</h2><div class="official">)(.*?)(</div>)', re.S)
MINI_ROW_RE = re.compile(r'<p class="mini"><b>[^<]*</b>：.*?</p>', re.S)
TEL_RE = re.compile(r"(?<![\d\->])(0\d{1,3}-\d{2,4}-\d{4})(?![\d\-<])")


def esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def rows_html(facts: dict) -> str:
    out = []
    for k, v in facts.items():
        label = LABELS.get(k, k)
        value = esc(v)
        if "電話番号" in label:
            value = TEL_RE.sub(r'<a href="tel:\1" data-track-click="tel_tap">\1</a>', value)
        out.append(f'<p class="mini"><b>{esc(label)}</b>：{value}</p>')
    return "".join(out)


def main() -> None:
    topics = json.loads((ROOT / "data" / "topics_master.json").read_text(encoding="utf-8"))
    changed = skipped = 0
    for t in topics:
        if t.get("action") == "merge":
            continue
        facts = t.get("facts") or {}
        if not facts:
            continue
        path = ROOT / t["href"].strip("/") / "index.html"
        if not path.exists():
            continue
        html = path.read_text(encoding="utf-8")
        m = OFFICIAL_BLOCK_RE.search(html)
        if not m:
            skipped += 1
            continue
        head, body, tail = m.group(1), m.group(2), m.group(3)
        # 既存の mini 行を取り除き、台帳から作り直した行を先頭に置く
        rest = MINI_ROW_RE.sub("", body)
        new_body = rows_html(facts) + rest
        if new_body == body:
            continue
        new_html = html[:m.start()] + head + new_body + tail + html[m.end():]
        path.write_text(new_html, encoding="utf-8")
        changed += 1
    print(f"公式窓口ブロックを台帳と一致させました: {changed} ページ更新")
    if skipped:
        print(f"  公式窓口ブロックが無く対象外: {skipped} ページ")


if __name__ == "__main__":
    main()
