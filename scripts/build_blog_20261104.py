"""Assemble the November 4 Mori culture features and their four contextual backlinks."""
from pathlib import Path
from html import escape
import json,re
from bs4 import BeautifulSoup
from illustrate_blog_20261104 import draw

ROOT=Path(__file__).resolve().parents[1]
DATE='2026-11-04'
SITE='https://morimachi.enshu-lifehack.com'
META=ROOT/'data/blog-batch-20261104.json'
POSTS=json.loads(META.read_text(encoding='utf8'))
SOURCES=json.loads((ROOT/'data/blog-20261104-sources.json').read_text(encoding='utf8'))
def read(path):return (ROOT/path).read_text(encoding='utf8')
def save(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def page(p,folder,sources_by_key=None):
    if sources_by_key is None:
        sources_by_key = SOURCES
    template=read('blog/20261101-morimachi-ikuji-nenkin/index.html')
    style=re.search(r'<style>(.*?)</style>',template,re.S)[1]+'.post-editorial-body table{width:100%;border-collapse:collapse;font-size:.94em}.post-editorial-body th,.post-editorial-body td{border:1px solid #b6c2b9;padding:.35em;overflow-wrap:anywhere}.post-editorial-body th{background:#e9efe9}'
    author=re.search(r'<aside class="post-author.*?</aside>',template,re.S)[0]
    def part(n):return '<!-- PART:'+n+':START -->'+read('parts/'+n+'.html')+'<!-- PART:'+n+':END -->'
    slug=p['slug']; title=p['title']; url=SITE+'/blog/'+slug+'/';desc=p['description']
    body=read('data/content/blog-20261104-'+p['key']+'.html')
    soup=BeautifulSoup(body,'html.parser');faq=[]
    for h in soup.find_all('h3'):
        if h.find_previous('h2')==soup.find_all('h2')[-1]:
            faq.append({'@type':'Question','name':h.get_text(strip=True),'acceptedAnswer':{'@type':'Answer','text':h.find_next_sibling('p').get_text(strip=True)}})
    assert len(faq)==3
    person={'@type':'Person','@id':'https://oishi-hiroyuki.org/#person','name':'大石浩之','image':SITE+'/assets/author-oishi.jpg','url':'https://oishi-hiroyuki.org/profile','sameAs':['https://oishi-hiroyuki.org/profile','https://fudosan.atawi.link/']}
    graph=[{'@type':'BlogPosting','headline':title,'datePublished':DATE,'dateModified':DATE,'image':url+'cover.jpg','mainEntityOfPage':url,'author':{'@id':person['@id']},'description':desc},person,{'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':i,'item':u,'name':name} for i,(u,name) in enumerate([(SITE+'/','森町ライフハック'),(SITE+'/blog/','ブログ'),(url,title)],1)]},{'@type':'FAQPage','mainEntity':faq}]
    def fig(file,motif,caption):
        return f'<figure><img src="/blog/{slug}/{file}" width="1000" height="560" alt="{motif}。森町の地形と記事の資料を主題にした概念イラスト。"><figcaption>{caption}</figcaption></figure>'
    for n,idx,motif,caption in [(2,7,p['method'],p['method']+'。調べた事実と自分の覚え書きを区別する手順を描いた。'),(1,3,p['scene'],p['scene']+'。実物の形状・配置を復元した図ではない。')]:
        pos=list(re.finditer(r'<h2(?:\s|>)',body))[idx].start()
        body=body[:pos]+fig(f'fig{n}.svg',motif,caption)+body[pos:]
    sources=''.join(f'<li><a href="{sources_by_key[k][1]}">{sources_by_key[k][0]}</a>（2026年11月4日確認）</li>' for k in p['sources'])
    html=f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}｜森町ライフハック</title><meta name="description" content="{desc}"><link rel="canonical" href="{url}"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="alternate" type="application/rss+xml" href="/feed.xml" title="森町ライフハック ブログ"><meta property="og:type" content="article"><meta property="og:title" content="{title}"><meta property="og:description" content="{desc}"><meta property="og:url" content="{url}"><meta property="og:image" content="{url}cover.jpg"><meta name="twitter:card" content="summary_large_image"><script type="application/ld+json">{json.dumps({"@context":"https://schema.org","@graph":graph},ensure_ascii=False)}</script>{part('head-css')}<style>{style}</style></head><body>{part('header')}<main><article class="post"><nav aria-label="パンくず"><a href="/">ホーム</a> / <a href="/blog/">ブログ</a></nav><h1>{title}</h1><p class="post-meta"><time datetime="{DATE}">2026年11月4日</time> ／ 大石浩之（磐田市／不動産業）</p>{fig('cover.jpg',p['scene'],'記事の内容をもとに描いたイメージ。')}<section class="post-answer" aria-label="結論"><p><strong>Q. {p['question']}</strong></p><p>A. {p['answer']}</p></section><div class="post-editorial-body">{body}</div><div class="action-grid"><a href="/life/housing/close-parents-house/">実家の所在地や家族への引継ぎを整理する</a></div>{author}<h2>出典・確認日</h2><p>2026年11月4日確認。史資料の記述と、家族での調べ方についての筆者の提案を分けて掲載しました。</p><ul class="post-sources">{sources}</ul><p class="post-disclaimer">公開状況や案内は変わる場合があります。現地を訪れる前に管理者の最新案内をご確認ください。土地や権利に関する個別の判断は、関係窓口や専門家にご相談ください。</p></article></main>{part('footer')}</body></html>'''
    (folder/'index.html').write_text(html,encoding='utf8')

def main():
    ledger=ROOT/'data/blog-posts.json'; data=json.loads(ledger.read_text(encoding='utf8'))
    for p in POSTS:
        folder=ROOT/'blog'/p['slug'];folder.mkdir(exist_ok=True)
        draw(p,folder);page(p,folder)
        rev=ROOT/'blog'/p['reverse']/'index.html';old=rev.read_text(encoding='utf8'); link='/blog/'+p['slug']+'/'
        if link not in old:
            start=old.index('<div class="post-editorial-body">')
            paragraphs=list(re.finditer(r'<p(?:\s[^>]*)?>.*?</p>',old[start:],re.S))
            anchor={'yama':3,'waniguchi':8,'toyohei':4,'school':3}[p['key']]
            at=start+paragraphs[anchor].end()
            old=old[:at]+f'<p>{p["lead"]}、<a href="{link}">{p["title"]}</a>をご覧ください。</p>'+old[at:]
            old=re.sub(r'("dateModified"\s*:\s*")[^"]+',r'\g<1>'+DATE,old)
            rev.write_text(old,encoding='utf8')
        next(r for r in data['posts'] if r['slug']==p['reverse'])['modified']=DATE
        row={k:p[k] for k in ['slug','title','description','query']}
        row.update(date=DATE,modified=DATE,axis='wed',home_description=p['description'],cta='official',primary_source='・'.join(SOURCES[k][0] for k in p['sources'])+'（2026-11-04確認）',cover_alt=p['scene']+'を描いた概念図',search_index=True)
        existing=next((r for r in data['posts'] if r['slug']==p['slug']),None)
        if existing:existing.update(row)
        else:data['posts'].append(row)
    save(ledger,data)
if __name__=='__main__':main()
