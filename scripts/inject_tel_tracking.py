#!/usr/bin/env python3
"""tel: リンクに data-track-click 属性を付与し、電話タップを計測対象にする。

04修正指示書 A-5 により「磐田では未適用」から「森町では適用する」に変更された項目。
フッターで読み込んでいる富士ヶ丘アナリティクスのトラッカー
(fujigaoka-analytics-worker.../tracker.js) は
  target.matches("[data-track-click]") -> POST /api/click {event_name: 属性値}
という実装なので、属性を足すだけで計測が始まる。

森町は電話が主要導線(役場0538-85-xxxx)であり、フォームを新設しない方針
(04 A-1「問い合わせフォームは新設しない」)のため、電話タップが実質的なCV計測点になる。

使い方: python scripts/inject_tel_tracking.py [--check]
"""
import argparse
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCLUDE_TOP = {"parts", "reports", "output", "scratchpad", "node_modules", ".git", ".wrangler", "docs", "_staging"}

TEL_RE = re.compile(r'<a\s+[^>]*href="tel:[^"]+"[^>]*>')


def add_track_attr(tag):
    if "data-track-click" in tag:
        return tag
    return tag[:-1] + ' data-track-click="tel_tap">'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    changed, total_links = [], 0
    for path in sorted(glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True)):
        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        if rel.split("/")[0] in EXCLUDE_TOP:
            continue
        with open(path, encoding="utf-8") as f:
            src = f.read()
        total_links += len(TEL_RE.findall(src))
        new = TEL_RE.sub(lambda m: add_track_attr(m.group(0)), src)
        if new != src:
            changed.append(rel)
            if not args.check:
                with open(path, "w", encoding="utf-8", newline="") as f:
                    f.write(new)

    verb = "要更新" if args.check else "更新"
    print("tel:リンク %d 本 / %s %d ファイル" % (total_links, verb, len(changed)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
