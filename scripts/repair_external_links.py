"""Apply individually reviewed source-link repairs after every generator.

An unavailable old document is never represented as the current replacement.
The original URL remains in data-retired-url and the reviewed JSON ledger.
"""
import json
import re
from html import escape, unescape
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r'<a\b[^>]*>.*?</a>', re.S | re.I)
HREF = re.compile(r'\bhref=(\x22|\x27)(.*?)\1', re.S | re.I)
ARCHIVED = re.compile(r'<span class="retired-source" data-retired-url="([^"]+)">(.*?)</span>\s*<span class="source-replacement">.*?</a></span>',re.S)
NOTICE = '<!-- SOURCE-AVAILABILITY:20261111 -->'
TOURISM_NOTICE = (
    NOTICE + '<aside class="note source-availability" aria-label="外部の観光案内の接続状況">'
    '<p><strong>観光協会サイトの一時停止について</strong>：町公式は2026年10月23日に公開一時停止・復旧時期未定を案内しています。'
    '11月11日の接続確認でも観光協会のページを開けませんでした。'
    '<a href="https://www.town.morimachi.shizuoka.jp/gyosei/kanko_bunka/kanko/7109.html" target="_blank" rel="noopener">町公式の停止案内</a>と、'
    '<a href="https://www.town.morimachi.shizuoka.jp/gyosei/kanko_bunka/index.html" target="_blank" rel="noopener">現在使える町公式の観光案内</a>を確認してください。'
    '施設の営業や催しの実施は、それぞれの公式窓口で確認してください。</p></aside>'
)


def after_intro(html, block):
    main=re.search(r'<main\b[^>]*>',html)
    if not main:
        return html
    end=html.find('</main>',main.end())
    end=len(html) if end<0 else end
    heading=re.search(r'<h2\b',html[main.end():end])
    pos=main.end()+heading.start() if heading else end
    return html[:pos]+block+html[pos:]


def repair(html, rules, availability=(), tourism_already_explained=False):
    counts = {}
    def restore_reviewed(m):
        old=unescape(m[1])
        if old not in rules:
            return m[0]
        label=re.split(r'（(?:旧リンク：|2026年11月11日接続未確認|2026年11月11日確認：)',m[2],maxsplit=1)[0]
        anchor=LINK.search(m[0])
        if not anchor:
            return m[0]
        opening=anchor[0][:anchor[0].index('>')+1]
        opening=HREF.sub(lambda h:'href='+h[1]+escape(old,quote=True)+h[1],opening,count=1)
        return opening+label+'</a>'
    # Refresh the reviewed annotation if its evidence/alternative changes, while
    # preserving all content outside this narrowly marked source citation.
    html=ARCHIVED.sub(restore_reviewed,html)
    def change(m):
        tag = m.group(0)
        href = HREF.search(tag)
        if not href:
            return tag
        old = unescape(href[2])
        e = rules.get(old)
        if not e:
            return tag
        counts[old] = counts.get(old, 0) + 1
        attrs = tag[:tag.index('>')+1]
        attrs = HREF.sub(lambda h: 'href='+h[1]+escape(e['replacement_url'], quote=True)+h[1], attrs, count=1)
        if e['replacement_url'].startswith('tel:'):
            attrs=re.sub(r'\s+target=(\x22|\x27).*?\1','',attrs,flags=re.I)
        link = attrs + escape(e['label']) + '</a>'
        if e['mode'] == 'archive':
            text = unescape(re.sub('<[^>]+>', '', tag[tag.index('>')+1:tag.rindex('</a>')])).strip()
            status = {
                'connection_unconfirmed':'2026年11月11日接続未確認。営業・掲載終了の確認ではありません',
                'redirects_to_home':'2026年11月11日確認：元の記事ではなく公式トップへ転送',
            }.get(e.get('reason'),'旧リンク：2026年11月11日到達できず')
            return (f'<span class="retired-source" data-retired-url="{escape(old, quote=True)}">'
                    f'{escape(text)}（{status}）</span> '
                    f'<span class="source-replacement">別の現行案内（リンク先のみ2026年11月11日確認）：{link}</span>')
        return link
    html = LINK.sub(change, html)
    html=re.sub(re.escape(NOTICE)+r'<aside\b[^>]*>.*?</aside>','',html,flags=re.S)
    if (re.search(r'href=[\x22\x27]https?://(?:www\.)?mori-kanko\.jp', html)
            and 'kanko/7109.html' not in html and not tourism_already_explained):
        html=after_intro(html,TOURISM_NOTICE)
    for note in availability:
        marker = '<!-- SOURCE-STATUS:'+note['id']+' -->'
        html=re.sub(re.escape(marker)+r'<aside\b[^>]*>.*?</aside>','',html,flags=re.S)
        if note.get('already_explained') in html:
            continue
        if not any('href="'+u+'"' in html for u in note['urls']):
            continue
        block=(marker+'<aside class="note" aria-label="外部の案内先の状況"><p>'
               +escape(note['message'])+'</p><p><a href="'+escape(note['url'],quote=True)+'" target="_blank" rel="noopener">'
               +escape(note['label'])+'</a></p></aside>')
        html=after_intro(html,block)
    return html, counts


def main():
    doc = json.loads((ROOT/'data/external-link-repairs.json').read_text(encoding='utf-8'))
    rules = doc['repairs']
    prior_notices=json.loads((ROOT/'data/verified-source-notices.json').read_text(encoding='utf-8'))
    tourism_explained={x['path'] for x in prior_notices if x['source'].endswith('/7109.html')}
    ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
    changed=0; replaced=0
    for loc in ET.parse(ROOT/'sitemap.xml').findall('.//s:loc',ns):
        href=loc.text.split('morimachi.enshu-lifehack.com',1)[1]
        path=ROOT/href.strip('/')/'index.html'
        before=path.read_bytes()
        after, counts=repair(before.decode('utf-8'),rules,doc.get('availability_notes',()),href in tourism_explained)
        if after.encode('utf-8') != before:
            path.write_bytes(after.encode('utf-8')); changed+=1
        replaced+=sum(counts.values())
    print(f'Reviewed external links: {changed} pages updated, {replaced} old links repaired')


if __name__ == '__main__':main()
