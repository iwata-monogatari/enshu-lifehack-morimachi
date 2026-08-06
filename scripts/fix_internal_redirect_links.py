#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""サイト内リンクを _redirects の301統合先へ直接つなぎ直す。冪等。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REDIRECTS = ROOT / "_redirects"
SKIP_DIRS = {".git", "_cache", "node_modules", "reports", "data", "scripts"}


def load_redirects() -> dict[str, str]:
    mappings: dict[str, str] = {}
    for raw in REDIRECTS.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = re.split(r"\s+", line)
        if len(parts) >= 3 and parts[2] == "301" and parts[0].startswith("/"):
            mappings[parts[0]] = parts[1]
    return mappings


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    mappings = load_redirects()
    files = links = 0
    for path in sorted(ROOT.rglob("*.html")):
        if SKIP_DIRS & set(path.relative_to(ROOT).parts):
            continue
        html = original = path.read_text(encoding="utf-8")
        for source, target in mappings.items():
            pattern = re.compile(rf'(?P<prefix>href=["\']){re.escape(source)}(?P<suffix>#[^"\']*)?(?P<quote>["\'])')

            def replace(match: re.Match[str]) -> str:
                nonlocal links
                links += 1
                suffix = match.group("suffix") or ""
                return match.group("prefix") + target + suffix + match.group("quote")

            html = pattern.sub(replace, html)
        if html != original:
            path.write_text(html, encoding="utf-8")
            files += 1
    print(f"301経由の内部リンクを直結: {links}リンク / {files}ファイル")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
