"""相談導線を生成後に反映。再実行時はマーカーを置換する。"""
import re
from html import escape
from pathlib import Path
from mori_jikka import HUB, sale_entry, url

ROOT = Path(__file__).resolve().parent.parent
PAGES = ['hub/property/', 'inheritance/', 'vacant-house/', 'temple/guide/',
         'life/housing/clean-parents-house/', 'life/housing/vacant-house/',
         'life/end-of-life/inherited-house/', 'life/housing/sell-house/']

def replace_block(src, name, body, anchor, after=False):
    start, end = f'<!-- {name}:START -->', f'<!-- {name}:END -->'
    block = start + body + end
    pattern = re.escape(start) + '.*?' + re.escape(end)
    if re.search(pattern, src, re.S):
        return re.sub(pattern, lambda _: block, src, count=1, flags=re.S)
    assert anchor in src, (name, anchor)
    return src.replace(anchor, anchor + block if after else block + anchor, 1)

def styles(src):
    return replace_block(src, 'MORI-JIKKA-CSS', '<link rel="stylesheet" href="/assets/mori-jikka.css?v=20261018">', '</head>')

def main():
    for slug in PAGES:
        path = ROOT / slug / 'index.html'
        src = path.read_text(encoding='utf-8')
        body = f'<div class="wrap"><aside class="mj-inbound"><p>森町に実家がある遠方のご家族へ</p><a href="{HUB}" data-track-click="mori_jikka_hub_click">帰省前の準備・実家じまい・売却相談をまとめて確認する →</a></aside></div>'
        # A common main wrapper exists on both the hub and life guides.
        src = replace_block(styles(src), 'MORI-JIKKA-INBOUND', body, '</main>')
        path.write_text(src, encoding='utf-8', newline='\n')
    path = ROOT / 'fudosan/sell/index.html'
    src = path.read_text(encoding='utf-8')
    src = replace_block(styles(src), 'MORI-JIKKA-SALE', sale_entry(), '<div class="fx-hero">')
    # Keep one direct intake destination at the bottom as well.
    src = re.sub(r'https://fudosan\.atawi\.link/areas/mori/\?[^"<>]+', escape(url('sell_bottom', 'sale'), quote=True), src)
    src = re.sub(r'https://fudosan\.atawi\.link/karte/\?[^"<>]+', lambda m: m[0] if 'intent=sale' in m[0] else escape(url('sell_bottom_organize'), quote=True), src)
    src = src.replace('9:00〜18:00、水曜定休。予約があれば時間外も対応', '9:00〜18:00、水曜・日曜は予約制。時間外は事前にご相談')
    path.write_text(src, encoding='utf-8', newline='\n')
    print('森町実家じまい導線: 9ページ反映')

if __name__ == '__main__':
    main()
