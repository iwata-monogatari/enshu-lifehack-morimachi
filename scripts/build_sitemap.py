#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""topics_master.json + aux-pages.json + トップページ/利用規約からsitemap.xmlを生成する。

topics_master.json は「調査済みの中項目155件」の台帳(出典・検証状態つき)。
/tools/ と /checklist/ は既存ページへの導線をまとめた集約ページで、
固有の出典を持たないため topics_master には入れず、data/aux-pages.json で管理する。

出力前に実ファイルの存在を確認し、無いURLはsitemapに載せない。

実行: python3 scripts/build_sitemap.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://morimachi.enshu-lifehack.com'
PUBLISHABLE_STATUSES = ('ai-checked', 'machine-verified', 'human-verified', 'published')


def page_exists(href):
    if href == '/':
        return (ROOT / 'index.html').is_file()
    return (ROOT / href.strip('/') / 'index.html').is_file()


def main():
    ledger = json.loads((ROOT / 'data/topics_master.json').read_text(encoding='utf-8'))
    published = [t for t in ledger if t.get('status') in PUBLISHABLE_STATUSES]
    aux = json.loads((ROOT / 'data/aux-pages.json').read_text(encoding='utf-8'))

    candidates = ['/', '/terms/'] + sorted(t['href'] for t in published) + [a['href'] for a in aux]

    urls, missing = [], []
    for u in candidates:
        (urls if page_exists(u) else missing).append(u)

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        lines.append(f'<url><loc>{SITE}{u}</loc></url>')
    lines.append('</urlset>')
    out = ROOT / 'sitemap.xml'
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'生成完了: {out}（{len(urls)}件 / うち集約ページ{len(aux)}件）')
    if missing:
        print(f'実ファイルが無いため除外 {len(missing)}件: {missing}')

if __name__ == '__main__':
    main()
