#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_redirects に「正規URLへの301」を自動生成する。

Cloudflare Workers (Static Assets) は
  /life/housing      -> /life/housing/      (末尾スラッシュ補完)
  /life/housing/index.html -> /life/housing/ (index.html 除去)
を 307 Temporary Redirect で返す。307 は「一時的」の意味なので、
評価統合の観点では 301 Moved Permanently が正しい。
プラットフォーム側のステータスは変更できないため、_redirects の
静的ルール（307 より先に評価される）で 301 を明示する。

sitemap.xml に載っている正規URLを入力とし、
  <path без slash>        -> <path>/ 301
  <path>/index.html       -> <path>/ 301
を AUTO-GENERATED マーカー区間へ書き込む。手書きルールは保持する。

実行: python3 scripts/build_redirects.py（build_sitemap.py の後に走らせる）
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://morimachi.enshu-lifehack.com'
START = '# AUTO-GENERATED:canonical-301 START （scripts/build_redirects.py が生成。手で編集しない）'
END = '# AUTO-GENERATED:canonical-301 END'

# Cloudflare の静的リダイレクトは1ファイル2000行まで。超えたら異常として止める。
STATIC_RULE_LIMIT = 2000


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    sitemap = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
    paths = [m[len(SITE):] for m in re.findall(r'<loc>([^<]+)</loc>', sitemap)]

    rules = ['/index.html / 301']
    for p in paths:
        if p == '/':
            continue
        if not p.endswith('/'):
            continue
        rules.append(f'{p.rstrip("/")} {p} 301')
        rules.append(f'{p}index.html {p} 301')

    block = '\n'.join([START] + rules + [END])

    redirects_path = ROOT / '_redirects'
    text = redirects_path.read_text(encoding='utf-8')
    pattern = re.compile(re.escape(START) + r'.*?' + re.escape(END), re.S)
    if pattern.search(text):
        new_text = pattern.sub(lambda m: block, text)
    else:
        new_text = text.rstrip('\n') + '\n\n' + block + '\n'

    total_rules = sum(1 for line in new_text.splitlines()
                      if line.strip() and not line.strip().startswith('#'))
    if total_rules > STATIC_RULE_LIMIT:
        print(f'エラー: 静的ルール {total_rules} 件が上限 {STATIC_RULE_LIMIT} を超えます', file=sys.stderr)
        return 1

    redirects_path.write_text(new_text, encoding='utf-8')
    print(f'生成完了: _redirects（正規URL301: {len(rules)}件 / 全静的ルール: {total_rules}件）')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
