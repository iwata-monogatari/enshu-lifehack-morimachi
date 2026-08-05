# -*- coding: utf-8 -*-
"""リンクのラベルと補足で同じ番号・語が二重に出る表示を直す（修正指示書 P0-4）。

公式リンクは `<a>ラベル <span>補足</span></a>` の形で描画している。
ラベル側にすでに電話番号が入っていると「こども救急電話相談 #8000 #8000」のように見える。
補足がラベルに含まれている場合は補足を出さない。

データ側（data/content/*.json の actions[].label / source）も直し、再生成で戻らないようにする。冪等。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

LINK_RE = re.compile(r'(<a class="official-link"[^>]*>)([^<]*?)\s*<span>([^<]*)</span>(</a>)')


def normalize(s: str) -> str:
    """全角＃・♯と半角#、全角数字の差を無視して比べる。"""
    return (s.replace("＃", "#").replace("♯", "#")
             .replace("－", "-").replace("ー", "-")
             .translate(str.maketrans("０１２３４５６７８９", "0123456789"))
             .strip())


def dedupe_html(html: str) -> tuple[str, int]:
    count = 0

    def repl(m: re.Match) -> str:
        nonlocal count
        head, label, suffix, tail = m.groups()
        if suffix.strip() and normalize(suffix) in normalize(label):
            count += 1
            return head + label.strip() + tail
        return m.group(0)

    return LINK_RE.sub(repl, html), count


def dedupe_data() -> int:
    """actions[].label に source と同じ番号が入っているものを整える。"""
    fixed = 0
    for path in sorted((ROOT / "data" / "content").glob("*.json")):
        items = json.loads(path.read_text(encoding="utf-8"))
        changed = False
        for item in items:
            for tab in item.get("tabs") or []:
                for action in tab.get("actions") or []:
                    label = action.get("label", "")
                    source = action.get("source", "")
                    if source and normalize(source) in normalize(label):
                        # ラベルに番号が入っているので、補足は空にする
                        action["source"] = ""
                        changed = True
                        fixed += 1
        if changed:
            path.write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n",
                            encoding="utf-8")
    return fixed


def main() -> None:
    total = files = 0
    for path in sorted(ROOT.rglob("*.html")):
        if {".git", "_cache", "node_modules", "reports", "data"} & set(
                path.relative_to(ROOT).parts):
            continue
        html = path.read_text(encoding="utf-8")
        new, n = dedupe_html(html)
        if n:
            path.write_text(new, encoding="utf-8")
            files += 1
            total += n
            print(f"  {path.relative_to(ROOT)}: {n} 箇所")
    print(f"HTML: {files} ファイル / {total} 箇所の重複表示を解消")
    print(f"データ: {dedupe_data()} 箇所の補足を整理")

    # 検算：リンク内で同じ語が連続していないか
    leftovers = []
    for path in sorted(ROOT.rglob("*.html")):
        if {".git", "_cache", "node_modules", "reports", "data"} & set(
                path.relative_to(ROOT).parts):
            continue
        for m in re.finditer(r"<a [^>]*>(.*?)</a>", path.read_text(encoding="utf-8"), re.S):
            text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(1))).strip()
            words = text.split()
            for i in range(len(words) - 1):
                if words[i] == words[i + 1] and len(words[i]) > 2:
                    leftovers.append((str(path.relative_to(ROOT)), text))
    if leftovers:
        print(f"[!!] まだ重複しているリンク {len(leftovers)} 件:")
        for f, t in leftovers[:8]:
            print(f"   {f}: {t}")
    else:
        print("リンク内の重複表示は残っていません。")


if __name__ == "__main__":
    main()
