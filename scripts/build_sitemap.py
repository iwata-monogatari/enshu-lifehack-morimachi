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
    blog = json.loads((ROOT / 'data/blog-posts.json').read_text(encoding='utf-8'))['posts']

    # 寺社DBはページ数が多く台帳を二重管理したくないので、実ディレクトリを走査する
    section_urls = []
    for section in ('shrine', 'temple'):
        base = ROOT / section
        if not base.is_dir():
            continue
        for p in sorted(base.rglob('index.html')):
            section_urls.append('/' + p.relative_to(ROOT).as_posix()[: -len('index.html')])

    # 6つの生活場面ハブ（抜本改修指示書 4.1）
    hubs = json.loads((ROOT / 'data/hubs.json').read_text(encoding='utf-8'))['hubs']
    hub_urls = [f"/hub/{h['slug']}/" for h in hubs]

    # 統合（301）したページは sitemap に載せない（指示書 12.5）
    published = [t for t in published if t.get('action') != 'merge']

    candidates = (['/', '/terms/']
                  + hub_urls
                  + sorted(t['href'] for t in published)
                  + [a['href'] for a in aux]
                  + [f"/blog/{p['slug']}/" for p in sorted(blog, key=lambda x: x['date'], reverse=True)]
                  + section_urls)

    # /shrine/ と /temple/ は aux-pages とディレクトリ走査の両方に現れるため重複を除く。
    # 同じURLを2回載せた sitemap は不整合として扱われる（指示書12.5）。
    urls, missing, seen = [], [], set()
    for u in candidates:
        if u in seen:
            continue
        seen.add(u)
        (urls if page_exists(u) else missing).append(u)

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        lines.append(f'<url><loc>{SITE}{u}</loc></url>')
    lines.append('</urlset>')
    out = ROOT / 'sitemap.xml'
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'生成完了: {out}（{len(urls)}件 / 集約ページ{len(aux)}件 / ブログ記事{len(blog)}件）')
    if missing:
        print(f'実ファイルが無いため除外 {len(missing)}件: {missing}')

if __name__ == '__main__':
    main()
