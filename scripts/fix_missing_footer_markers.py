# -*- coding: utf-8 -*-
"""共通フッターのマーカーが無いページへ `<!-- PART:footer:START/END -->` を補う。

inject_parts.py はマーカーの無いページを対象外にするため、生成経路によっては
共通フッター（サイト内リンク＋計測タグ）が入らないページが残る。
このスクリプトはマーカーだけを置き、中身は後続の inject_parts.py が入れる。

  - すでにマーカーがあるページは無変更（冪等）
  - `</body>` 直前に簡易フッター（リンク1〜2本だけの `<footer class="site-footer">`）が
    ある場合は、その簡易フッターをマーカーへ置き換える（フッターの二重化を防ぐ）
  - それ以外は `</body>` 直前へマーカーを挿入する
  - CRLF / LF は元のまま保つ（読み書きとも newline=""）

実行: python scripts/fix_missing_footer_markers.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

# 共通部品の原本・作業用キャッシュ・スクリプト・レポートは対象外
EXCLUDE_TOP = {"parts", "_cache", "scripts", "reports", "node_modules",
               ".git", ".wrangler", "docs", "data"}
EXCLUDE_FILES = {"404.html"}

MARKERS = "<!-- PART:footer:START --><!-- PART:footer:END -->"
# 共通フッター化される前の簡易フッター（本文リンクを1〜2本だけ持つ）
STUB_FOOTER = re.compile(
    r'<footer class="site-footer">(?:(?!<footer).)*?</footer>\s*(?=</body>)',
    re.S,
)


def targets():
    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT)
        if EXCLUDE_TOP & set(rel.parts):
            continue
        if len(rel.parts) == 1 and rel.name in EXCLUDE_FILES:
            continue
        yield path, rel.as_posix()


def main() -> int:
    added, replaced, skipped_no_body = [], [], []
    for path, rel in targets():
        with open(path, encoding="utf-8", newline="") as f:
            html = f.read()
        if "PART:footer" in html:
            continue
        if "</body>" not in html:
            skipped_no_body.append(rel)
            continue
        new_html, n = STUB_FOOTER.subn(MARKERS, html, count=1)
        if n:
            replaced.append(rel)
        else:
            new_html = html.replace("</body>", MARKERS + "\n</body>", 1)
            added.append(rel)
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new_html)

    print("マーカー挿入 %d ページ / 簡易フッターを置換 %d ページ"
          % (len(added), len(replaced)))
    for rel in added + replaced:
        print("  " + rel)
    if skipped_no_body:
        print("</body> が無く対象外 %d ページ:" % len(skipped_no_body))
        for rel in skipped_no_body:
            print("  " + rel)
    if not added and not replaced:
        print("欠落なし（冪等OK）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
