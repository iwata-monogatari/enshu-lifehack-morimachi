#!/usr/bin/env python3
"""Publish reviewed updates without advancing whole-article verification dates."""
import json
import re
from html import escape as esc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START, END = '<!-- OFFICIAL-UPDATES:START -->', '<!-- OFFICIAL-UPDATES:END -->'
STYLE = '<link rel="stylesheet" href="/assets/official-updates.css?v=20261008">'


def item(e, related=False):
    more = f'<p><a href="{esc(e["pages"][0])}">関連ガイドで手順を確認する →</a></p>' if related and e['pages'] else ''
    heading = f'<h3>{esc(e["title"])}</h3>' if related else f'<p class="official-update-label"><strong>{esc(e["title"])}</strong></p>'
    return (f'<section class="official-update-item" id="update-{esc(e["id"])}">'
            f'{heading}<p>{esc(e["summary"])}</p>'
            f'<p class="mini">公式更新日：<time datetime="{e["source_updated"]}">{e["source_updated"]}</time> ／ '
            f'<a href="{esc(e["source_url"])}" target="_blank" rel="noopener" data-track-click="official_link_click">森町公式の案内を確認</a></p>{more}</section>')


def main():
    doc = json.loads((ROOT/'data/official-updates.json').read_text(encoding='utf-8'))
    date, entries = doc['checked_at'], doc['entries']
    targets = {}
    for e in entries:
        for href in e['pages']:
            targets.setdefault(href, []).append(e)
    for href, rows in targets.items():
        path = ROOT / href.strip('/') / 'index.html'
        html = path.read_text(encoding='utf-8')
        block = (START + '<section class="official-updates" aria-labelledby="official-update-title">'
                 f'<p id="official-update-title" class="official-update-heading"><strong>公式情報の更新を確認しました（{date}）</strong></p>'
                 '<p class="mini">以下は今回確認した更新事項です。ページ末尾の最終確認日は、既存情報全体を確認した日を示しています。</p>'
                 + ''.join(item(e) for e in rows)
                 + '<p><a href="/updates/">今回確認した更新情報の一覧 →</a></p></section>' + END)
        if START in html:
            html = re.sub(re.escape(START)+'.*?'+re.escape(END), lambda _: block, html, flags=re.S)
        else:
            pos = html.index('</section>', html.index('<main')) + len('</section>')
            html = html[:pos] + block + html[pos:]
        if STYLE not in html: html = html.replace('</head>', STYLE+'</head>')
        path.write_text(html, encoding='utf-8')
    parts = {k:(ROOT/'parts'/f'{k}.html').read_text(encoding='utf-8') for k in ['head-css','header','footer']}
    desc = '静岡県森町公式サイトの更新を確認し、保育所・幼稚園・学童の申込み、公共施設予約、文化会館の申請期限、予防接種助成など暮らしに関わる変更を出典付きで整理します。'
    cards = ''.join(item(e, True) for e in entries)
    html = f'''<!doctype html><html lang="ja"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>森町公式情報の更新まとめ｜2026年10月確認 | 森町ライフハック</title>
<meta name="description" content="{desc}"><link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="canonical" href="https://morimachi.enshu-lifehack.com/updates/">
<!-- PART:head-css:START -->{parts['head-css']}<!-- PART:head-css:END -->{STYLE}</head>
<body class="hub"><!-- PART:header:START -->{parts['header']}<!-- PART:header:END -->
<main><div class="wrap"><p class="breadcrumb"><a href="/">森町ライフハック</a> ／ 公式情報の更新まとめ</p>
<section class="hero"><h1>森町公式情報の更新まとめ</h1>
<p class="lead">2026年10月8日に確認した、暮らしと手続きに関わる{len(entries)}件の更新情報です。</p>
<p>森町公式サイトを出典とする非公式の案内です。対象年度・申込期限・利用条件は、各項目の公式ページで最終確認してください。</p>
<p>確認日：<time datetime="{date}">{date}</time> ／ 終了した募集や催しも、確認時点の記録として掲載しています。</p></section>
<section aria-labelledby="reviewed-updates"><h2 id="reviewed-updates">今回確認した変更と新しい案内</h2><div class="official-update-list">{cards}</div></section>
<section><h2>確認の範囲</h2><p>公式サイトのサイトマップと前回の取得台帳を比較し、新しいページや更新候補から掲載内容に関わる情報を読み直しました。上の{len(entries)}項目を今回の掲載更新に反映しています。全公式ページの制度内容を一括して確認済みにしたものではありません。</p>
<p>同じ案内が複数のURLに掲載される場合があります。公開日・更新日と申込期間は別のものなので、期限は本文の記載を確認してください。</p></section>
</div></main><!-- PART:footer:START -->{parts['footer']}<!-- PART:footer:END --></body></html>'''
    (ROOT/'updates').mkdir(exist_ok=True)
    (ROOT/'updates/index.html').write_text(html, encoding='utf-8')
    print(f'Official updates: {len(entries)} entries, {len(targets)} existing pages')


if __name__ == '__main__': main()
