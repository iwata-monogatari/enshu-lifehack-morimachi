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
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://morimachi.enshu-lifehack.com'
PUBLISHABLE_STATUSES = ('ai-checked', 'machine-verified', 'human-verified', 'published')


def page_path(href):
    if href == '/':
        return ROOT / 'index.html'
    return ROOT / href.strip('/') / 'index.html'


def page_exists(href):
    return page_path(href).is_file()


def git_lastmod_map():
    """各ファイルが最後にコミットされた日を git から取る（修正指示書15）。

    lastmod にビルド日時を入れると、中身が変わっていなくても毎回更新扱いになり、
    検索エンジンに対して嘘の更新シグナルを出すことになる。
    実際に内容が変わった日＝最後のコミット日を使う。
    """
    try:
        out = subprocess.run(
            ['git', 'log', '--name-only', '--pretty=format:%cs', '--', '*.html'],
            cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=120).stdout
    except Exception:
        return {}
    dates = {}
    current = None
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        if len(line) == 10 and line[4] == '-' and line[7] == '-':
            current = line
        elif current and line.endswith('.html'):
            dates.setdefault(line, current)  # 最初に出た＝最新のコミット
    return dates


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

    lastmods = git_lastmod_map()
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    dated = 0
    for u in urls:
        rel = page_path(u).relative_to(ROOT).as_posix()
        lastmod = lastmods.get(rel)
        if lastmod:
            dated += 1
            lines.append(f'<url><loc>{SITE}{u}</loc><lastmod>{lastmod}</lastmod></url>')
        else:
            lines.append(f'<url><loc>{SITE}{u}</loc></url>')
    lines.append('</urlset>')
    out = ROOT / 'sitemap.xml'
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'  lastmod を付けたURL: {dated} / {len(urls)}')
    print(f'生成完了: {out}（{len(urls)}件 / 集約ページ{len(aux)}件 / ブログ記事{len(blog)}件）')
    if missing:
        print(f'実ファイルが無いため除外 {len(missing)}件: {missing}')

if __name__ == '__main__':
    main()
