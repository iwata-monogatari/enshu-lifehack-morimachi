"""Build the second November 4 batch from its reviewed editorial HTML and metadata."""
import json
import re
from pathlib import Path
from build_blog_20261104 import ROOT, DATE, page, save
from illustrate_blog_20261104_second import draw

def load(name):
    return json.loads((ROOT/name).read_text(encoding='utf8'))

POSTS=load('data/blog-batch-20261104-second.json')
SOURCES=load('data/blog-20261104-second-sources.json')
backlinks={
    'ekijin':('十一月','収穫を感謝する新嘗祭の四日前には、疫病を鎮める祈りもあります。'),
    'lamp':('文化財','街道に残る灯りは、何を覆い、どの部分を直してきたかでも比べられます。'),
    'inn':('古着','古着商と旅籠屋の軒数は、文政十三年の森町村の生業表から読み取れます。'),
    'parking':('宮川','宮川まで親御さんと歩くなら、駐車場図の徒歩分数がどこまでかも確かめておけます。'),
}

def main():
    ledger_path=ROOT/'data/blog-posts.json'
    ledger=load('data/blog-posts.json')
    for post in POSTS:
        slug=post['slug']
        folder=ROOT/'blog'/slug
        folder.mkdir(exist_ok=True)
        draw(post,folder)
        page(post,folder,SOURCES)
        reverse=ROOT/'blog'/post['reverse']/'index.html'
        old=reverse.read_text(encoding='utf8')
        link=f'/blog/{slug}/'
        if link not in old:
            start=old.index('<div class="post-editorial-body">')
            end=old.index('<div class="action-grid">',start)
            term,lead=backlinks[post['key']]
            paragraphs=list(re.finditer(r'<p(?:\s[^>]*)?>.*?</p>',old[start:end],re.S))
            match=next((m for m in paragraphs if term in m.group() and '<a ' not in m.group()),paragraphs[1])
            pos=start+match.end()
            html=old[:pos]+f'<p>{lead}<a href="{link}">{post["title"]}</a>で詳しく紹介しています。</p>'+old[pos:]
            html=re.sub(r'("dateModified"\s*:\s*")[^"]+',r'\g<1>'+DATE,html)
            reverse.write_text(html,encoding='utf8')
        next(row for row in ledger['posts'] if row['slug']==post['reverse'])['modified']=DATE
        row={k:post[k] for k in ('title','slug','description','query')}
        row.update(date=DATE,modified=DATE,axis='wed',home_description=post['description'],cta='official',primary_source='・'.join(SOURCES[k][0] for k in post['sources'])+'（2026年11月4日確認）',cover_alt=post['scene'],search_index=True)
        existing=next((r for r in ledger['posts'] if r['slug']==slug),None)
        if existing is None:ledger['posts'].append(row)
        else:existing.update(row)
    save(ledger_path,ledger)

if __name__=='__main__':
    main()
