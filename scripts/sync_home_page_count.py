#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sitemapの公開URL件数をトップページの確認状況へ同期する。"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    sitemap = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
    count = len(re.findall(r'<loc>', sitemap))
    path = ROOT / 'index.html'
    html = path.read_text(encoding='utf-8')
    updated, replacements = re.subn(
        r'サイト全体の公開ページは\s*\d+\s*件です。',
        f'サイト全体の公開ページは {count} 件です。', html, count=1
    )
    if replacements != 1:
        raise RuntimeError('トップページの公開件数表示を特定できません')
    path.write_text(updated, encoding='utf-8', newline='\n')
    print(f'トップページ公開件数を同期: {count}件')


if __name__ == '__main__':
    main()
