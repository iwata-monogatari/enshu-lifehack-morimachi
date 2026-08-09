#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""topics_master.json + aux-pages.json + 質問台帳からsitemap.xmlを生成する。

topics_master.json は「調査済みの中項目155件」の台帳(出典・検証状態つき)。
/tools/ と /checklist/ は既存ページへの導線をまとめた集約ページで、
固有の出典を持たないため topics_master には入れず、data/aux-pages.json で管理する。

出力前に実ファイルの存在を確認し、無いURLはsitemapに載せない。

実行: python3 scripts/build_sitemap.py
"""
import datetime
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://morimachi.enshu-lifehack.com'
PUBLISHABLE_STATUSES = ('ai-checked', 'machine-verified', 'human-verified', 'published')


def iso_date_or_none(value):
    """sitemap の lastmod に使える YYYY-MM-DD だけを返す。"""
    if not value:
        return None
    try:
        return datetime.date.fromisoformat(value).isoformat()
    except (TypeError, ValueError):
        return None


def page_path(href):
    if href == '/':
        return ROOT / 'index.html'
    return ROOT / href.strip('/') / 'index.html'


def page_exists(href):
    return page_path(href).is_file()


# これ以上のHTMLファイルを一度に触るコミットは、フッター差し替えや計測タグ追加など
# サイト共通部品の機械的変更とみなし、lastmod の根拠にしない。
# （全289ページが同じ lastmod になると Google は lastmod を信頼しなくなる）
MASS_COMMIT_THRESHOLD = 100


def git_lastmod_map():
    """各ファイルが最後に「内容として」変わった日を git から取る（修正指示書15）。

    lastmod にビルド日時を入れると、中身が変わっていなくても毎回更新扱いになり、
    検索エンジンに対して嘘の更新シグナルを出すことになる。
    さらに、共通フッター差し替えのような全ページ一括コミットを含めると
    全URLが同一日付になり lastmod が無意味になるため、
    MASS_COMMIT_THRESHOLD 以上のHTMLを触ったコミットは除外する。
    """
    try:
        out = subprocess.run(
            ['git', 'log', '--name-status', '--pretty=format:@@%cs', '--', '*.html'],
            cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=120).stdout
    except Exception:
        return {}
    # コミット単位で (日付, 触ったHTML一覧) を集める
    commits = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('@@'):
            commits.append((line[2:], []))
        elif commits:
            parts = line.split('\t')
            if len(parts) >= 2 and parts[-1].endswith('.html'):
                commits[-1][1].append((parts[0], parts[-1]))
    dates = {}
    for date, entries in commits:  # git log は新しい順
        # 大規模コミットでも新規ページの公開日は意味がある。既存ページの
        # 一括部品差し替えだけを除外し、追加(A)はlastmodに採用する。
        files = [path for status, path in entries
                 if len(entries) < MASS_COMMIT_THRESHOLD or status.startswith('A')]
        for f in files:
            dates.setdefault(f, date)  # 最初に出た＝最新の実質的変更
    return dates


def dirty_html_files():
    """未コミットの変更があるHTMLの一覧。

    毎朝のブログ公開は「ビルド→コミット」の順で走るため、ビルド時点の
    git log には当日の変更が現れず、トップや /blog/ の lastmod が
    1日古いままデプロイされていた（2026-08-06 実測）。
    未コミットの変更は当日デプロイされる内容なので、今日の日付を使う。
    一括変更（MASS_COMMIT_THRESHOLD 以上）は git 日付と同じ理由で除外。
    """
    try:
        out = subprocess.run(
            ['git', 'status', '--porcelain', '--untracked-files=all', '--', '*.html'],
            cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=60).stdout
    except Exception:
        return set()
    files = set()
    for line in out.splitlines():
        status = line[:2]
        path = line[3:].split(' -> ')[-1].strip().strip('"')
        if not path.endswith('.html'):
            continue
        # 既存のCRLFファイルを生成スクリプトが開いただけで、内容が同じでも
        # Windowsではstatusに出る場合がある。空白だけの差をlastmodにしない。
        if status == '??':
            files.add(path)
            continue
        unstaged = subprocess.run(
            ['git', 'diff', '--ignore-all-space', '--quiet', '--', path],
            cwd=ROOT, timeout=30).returncode
        staged = subprocess.run(
            ['git', 'diff', '--cached', '--ignore-all-space', '--quiet', '--', path],
            cwd=ROOT, timeout=30).returncode
        if unstaged or staged:
            files.add(path)
    if len(files) >= MASS_COMMIT_THRESHOLD:
        return set()
    return files


def main():
    ledger = json.loads((ROOT / 'data/topics_master.json').read_text(encoding='utf-8'))
    published = [t for t in ledger if t.get('status') in PUBLISHABLE_STATUSES]
    aux = json.loads((ROOT / 'data/aux-pages.json').read_text(encoding='utf-8'))
    blog = json.loads((ROOT / 'data/blog-posts.json').read_text(encoding='utf-8'))['posts']
    questions = json.loads((ROOT / 'data/questions.json').read_text(encoding='utf-8'))
    expansion = json.loads((ROOT / 'data/search-expansion-pages.json').read_text(encoding='utf-8'))
    phase1_path = ROOT / 'data/seo-phase1-publication.json'
    phase1 = json.loads(phase1_path.read_text(encoding='utf-8')) if phase1_path.exists() else []

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
                  + [q['href'] for q in questions]
                  + [p['href'] for p in expansion]
                  + [p['url'] for p in phase1]
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
    dirty = dirty_html_files()
    today = datetime.date.today().isoformat()

    # git 以外の「内容の日付」: 台帳の内容更新日・最終確認日と、ブログ記事の公開日。
    # 全ページ一括コミットを除外すると git 日付を持たないページが出るため、
    # ページ単位で管理している実データの日付で補完し、両方あれば新しい方を使う。
    verified = {t['href']: t['verified_date'] for t in published
                if t.get('verified_date')}
    content_updated = {t['href']: t['content_updated'] for t in published
                       if t.get('content_updated')}
    blog_dates = {f"/blog/{p['slug']}/": p['date'] for p in blog if p.get('date')}
    question_dates = {q['href']: q['verified_date'] for q in questions if q.get('verified_date')}
    expansion_dates = {p['href']: '2026-08-09' for p in expansion}
    phase1_dates = {p['url']: p.get('fact_checked_at') for p in phase1}

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    dated = 0
    for u in urls:
        rel = page_path(u).relative_to(ROOT).as_posix()
        candidates = [d for d in (
            iso_date_or_none(lastmods.get(rel)),
            iso_date_or_none(content_updated.get(u)),
            iso_date_or_none(verified.get(u)),
            iso_date_or_none(blog_dates.get(u)),
            iso_date_or_none(question_dates.get(u)),
            iso_date_or_none(expansion_dates.get(u)),
            iso_date_or_none(phase1_dates.get(u)),
            today if rel in dirty else None,
        ) if d]
        lastmod = max(candidates) if candidates else None  # YYYY-MM-DD は辞書順=時系列順
        if lastmod:
            dated += 1
            lines.append(f'<url><loc>{SITE}{u}</loc><lastmod>{lastmod}</lastmod></url>')
        else:
            lines.append(f'<url><loc>{SITE}{u}</loc></url>')
    lines.append('</urlset>')
    out = ROOT / 'sitemap.xml'
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    print(f'  lastmod を付けたURL: {dated} / {len(urls)}')
    print(f'生成完了: {out}（{len(urls)}件 / 質問{len(questions)}件 / ブログ記事{len(blog)}件）')
    if missing:
        print(f'実ファイルが無いため除外 {len(missing)}件: {missing}')

if __name__ == '__main__':
    main()
