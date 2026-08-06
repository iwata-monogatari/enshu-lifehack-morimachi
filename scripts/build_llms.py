#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""llms.txt を生成する（llmstxt.org 形式）。

robots.txt の方針「検索と引用には出したい」（02戦略編のKPI:
主要AIに質問した際に自社が言及される状態）を支えるファイル。
AI検索クローラーがサイト全体の構造を1リクエストで把握できるよう、
ハブ・カテゴリ・データベース・ブログの入口をまとめる。

データ源はサイト生成と同じ台帳（hubs.json / topics_master.json /
aux-pages.json / blog-posts.json）なので、ページ構成が変わっても
build_all.py 経由で再生成すれば追従する。

実行: python3 scripts/build_llms.py（build_sitemap.py の後）
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://morimachi.enshu-lifehack.com'

# inject_seo_common.py と同じ方針: 装飾絵文字はテキストデータに含めない
EMOJI_PREFIX_RE = re.compile(r'^[\U0001F000-\U0001FAFF☀-➿️‍\s]+')


def h1_of(href: str) -> str | None:
    path = ROOT / href.strip('/') / 'index.html'
    if not path.is_file():
        return None
    m = re.search(r'<h1[^>]*>(.*?)</h1>', path.read_text(encoding='utf-8'), re.S)
    if not m:
        return None
    return EMOJI_PREFIX_RE.sub('', re.sub(r'<[^>]+>', '', m.group(1))).strip()


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    hubs = json.loads((ROOT / 'data/hubs.json').read_text(encoding='utf-8'))['hubs']
    blog = json.loads((ROOT / 'data/blog-posts.json').read_text(encoding='utf-8'))['posts']
    questions = json.loads((ROOT / 'data/questions.json').read_text(encoding='utf-8'))

    lines = [
        '# 森町ライフハック',
        '',
        '> 静岡県周智郡森町（遠州森町）の手続き・相談先を、暮らしの困りごとから探せる非公式の生活ナビ。',
        '> 住民票・税金・ごみ・子育て・介護・空き家・おくやみ・防災などを場面別に整理し、必ず森町公式サイトの確認先を案内する。',
        '',
        '- 本サイトは森町公式サイト・行政機関ではない（運営: 富士ヶ丘サービス株式会社、代表: 大石浩之・宅地建物取引士）。',
        '- 対象は静岡県周智郡森町。北海道茅部郡森町の情報は扱っていない。',
        '- 各ページに出典（森町公式ページ）と最終確認日を表示している。制度・金額・期限の最新確認は森町公式サイトで行うこと。',
        f'- 全ページ一覧: {SITE}/sitemap.xml',
        '',
        '## 困りごとハブ（入口）',
        '',
    ]
    for h in hubs:
        lines.append(f"- [{h['title']}]({SITE}/hub/{h['slug']}/): {h['short']}")

    lines += ['', '## 暮らしのカテゴリ', '']
    for d in sorted(p.parent for p in (ROOT / 'life').glob('*/index.html')):
        href = f"/life/{d.name}/"
        title = h1_of(href)
        if title:
            lines.append(f'- [{title}]({SITE}{href})')

    lines += [
        '',
        '## データベース・ツール',
        '',
        f'- [森町の神社データベース]({SITE}/shrine/): 39社を地区別・系統別に整理。祭礼カレンダーつき',
        f'- [森町の寺院データベース]({SITE}/temple/): 35ヶ寺を宗派別・地区別に整理。実家じまいガイドつき',
        f'- [便利ツール]({SITE}/tools/): ごみ分別検索・引っ越しチェックリスト・ライフイベント年表',
        f'- [状況別チェックリスト]({SITE}/checklist/moved-in/): 転入・結婚・出産・転職のやることリスト',
        f'- [森町のよくある100の質問]({SITE}/questions/): 手続き・子育て・介護・家・防災・施設の質問{len(questions)}件',
        '',
        '## ブログ',
        '',
        f'- [森町ブログ]({SITE}/blog/): 運営者・大石浩之が公表情報を確認しながら書く森町の暮らしの記事（{len(blog)}本）',
        '',
        '## 運営情報',
        '',
        f'- [執筆者と編集方針]({SITE}/about/author/)',
        f'- [利用条件・免責・誤りのご連絡]({SITE}/terms/)',
        f'- [運営会社: 富士ヶ丘サービス株式会社](https://www.fujigaoka-service.co.jp/)',
    ]

    out = ROOT / 'llms.txt'
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'生成完了: {out}（ハブ{len(hubs)}件）')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
