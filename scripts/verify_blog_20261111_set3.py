"""Durable article, source, illustration and distribution checks for this batch.

Adapted from verify_blog_20261108.py for the November 10 additional batch.
The banned-word baseline comparison uses git show when a .git directory is
available (PC flow) and falls back to the pristine tree next to this working
copy (VM flow), because this working copy was unpacked from an archive.
"""
import json,re,sys,hashlib,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
from build_blog_20261111_set3 import ROOT,OUT,POSTS,SOURCES,save
DATE='2026-11-11'
def baseline(filename):
 gitdir=ROOT/'.git'
 if gitdir.exists():
  return subprocess.check_output(['git','show','HEAD:'+filename],cwd=ROOT).decode('utf8')
 pristine=ROOT.parent/'pristine'/filename
 if pristine.exists():return pristine.read_text(encoding='utf8')
 return None
def check(local=False):
 issues=[];reports=[]
 ledger=json.loads((ROOT/'data/blog-posts.json').read_text(encoding='utf8'))['posts']
 sitemap=ET.parse(ROOT/'sitemap.xml');ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
 feed=ET.parse(ROOT/'feed.xml');search=json.loads((ROOT/'search-index.json').read_text(encoding='utf8'))
 for p in POSTS:
  slug=p['slug'];url='https://morimachi.enshu-lifehack.com/blog/'+slug+'/'
  raw=(ROOT/'blog'/slug/'index.html').read_text(encoding='utf8');s=BeautifulSoup(raw,'html.parser');body=s.select_one('.post-editorial-body');errors=[]
  count=len(re.sub(r'\s+','',body.get_text()));paragraphs=len(body.find_all('p'))
  if count<5000 or paragraphs<35:errors.append('length')
  if s.h1.get_text()!=p['title'] or s.select_one('link[rel="canonical"]')['href']!=url:errors.append('title/canonical')
  if len(p['title'])>32:errors.append('title length')
  gs=[]
  for el in s.select('script[type="application/ld+json"]'):
   obj=json.loads(el.string);gs+=obj.get('@graph',[obj])
  for t in ['BlogPosting','Person','BreadcrumbList','FAQPage']:
   if not any(g.get('@type')==t for g in gs):errors.append('schema '+t)
  bp=next(g for g in gs if g.get('@type')=='BlogPosting');person=next(g for g in gs if g.get('@type')=='Person')
  if bp['datePublished']!=DATE or bp['dateModified']!=DATE:errors.append('schema dates')
  if len(p['answer'])>200:errors.append('answer')
  faqs=next(g for g in gs if g.get('@type')=='FAQPage')['mainEntity']
  if len(faqs)!=3:errors.append('faq number')
  for q in faqs:
   if q['name'] not in body.get_text() or q['acceptedAnswer']['text'] not in body.get_text():errors.append('faq mismatch')
  if not s.select_one('img[src="/assets/author-oishi.jpg"]') or not s.select_one('.post-author a[href="https://oishi-hiroyuki.org/profile"]'):errors.append('author')
  if not person.get('sameAs') or not person.get('image'):errors.append('person identity')
  for h in body.find_all('h2'):
   n=h.find_next_sibling()
   if not n or n.name!='p' or re.match(r'^(これ|その|それ|上記)',n.get_text()):errors.append('h2 independence '+h.get_text())
  links=[a['href'] for a in body.select('a[href^="/blog/"]')]
  if not 3<=len(links)<=5:errors.append('links')
  for a in links:
   if not (ROOT/a.strip('/')/'index.html').exists():errors.append('broken '+a)
  if '/blog/'+slug+'/' not in (ROOT/'blog'/p['reverse']/'index.html').read_text(encoding='utf8'):errors.append('backlink')
  if len({k for k in p['source_keys'] if SOURCES[k][1].startswith('https://www.town.morimachi.shizuoka.jp/')})<2:errors.append('town sources')
  pictures=[]
  for im in s.select('article img'):
   f=ROOT/im['src'].lstrip('/')
   if not f.exists():errors.append('missing '+im['src'])
   if f.suffix=='.jpg':Image.open(f).verify()
   if len(im.get('alt',''))<15:errors.append('alt')
   if 'author-oishi' not in im['src']:pictures.append(dict(source=im['src'],local_path=f.relative_to(ROOT).as_posix(),local_exists=f.exists(),page_reference=True))
  for n in (1,2):
   f=ROOT/'blog'/slug/f'fig{n}.svg';ET.parse(f)
   if 'data-illustration="mori-editorial"' not in f.read_text(encoding='utf8'):errors.append('svg marker')
  if len(pictures)!=3:errors.append('3 illustrations')
  for phrase in ['いかがでしたか','と言えるでしょう','ではないでしょうか','重要です','ポイントは3つです','まとめると','していきましょう','ぜひ〜してみてください','近年、','注目されています','求められています']:
   if phrase in body.get_text():errors.append('phrase '+phrase)
  for phrase in ['一言メモ','体験ストック','体験素材','制作ルール','制作入力欄']:
   if phrase in body.get_text():errors.append('editorial process note '+phrase)
  for word in ['昨年','最近']:
   if word in body.get_text():errors.append('relative '+word)
  for word in ['また','さらに','そして']:
   if len(re.findall(r'(?:^|[。！？])'+word,body.get_text()))>=3:errors.append('connective '+word)
  row=next(x for x in ledger if x['slug']==slug)
  if row['date']!=DATE or row['modified']!=DATE:errors.append('ledger date')
  if not local:
   searchrow=next((x for x in search if x.get('href')=='/blog/'+slug+'/'),None)
   if searchrow is None or searchrow.get('date')!=DATE:errors.append('search publication date')
   entry=next((e for e in sitemap.findall('s:url',ns) if e.findtext('s:loc',namespaces=ns)==url),None)
   if entry is None or not entry.findtext('s:lastmod',namespaces=ns).startswith(DATE):errors.append('sitemap date')
   item=next((x for x in feed.findall('./channel/item') if x.findtext('link')==url),None)
   if item is None or '11 Nov 2026' not in item.findtext('pubDate'):errors.append('feed date')
   if slug not in json.dumps(search,ensure_ascii=False):errors.append('search index')
   for f in ['llms.txt','llms-full.txt','blog/index.html']:
    if slug not in (ROOT/f).read_text(encoding='utf8'):errors.append(f+' missing')
  reports.append(dict(slug=slug,title=p['title'],requested_title=p['title'],html_title=s.title.get_text(),url=url,characters=count,paragraphs=paragraphs,answer_length=len(p['answer']),faq_lengths=[len(q['acceptedAnswer']['text']) for q in faqs],links=links,reverse=p['reverse'],images=pictures,issues=errors))
  issues.extend((slug,e) for e in errors)
 save(OUT/'article-checks.json',dict(status='pass' if not issues else 'fail',articles=reports,issues=issues))
 sources=json.loads((OUT/'sources-http.json').read_text(encoding='utf8'))
 used=set(k for p in POSTS for k in p['source_keys'])
 if not all(any(x['key']==k and x['status']==200 for x in sources) for k in used):issues.append(('sources','HTTP'))
 print(json.dumps(dict(status='pass' if not issues else 'fail',articles=[{k:r[k] for k in ['slug','characters','paragraphs','issues']} for r in reports],issues=issues),ensure_ascii=False))
 return not issues

def banned():
 word=chr(0x653f)+chr(0x7b56);violations=[];existing=[]
 paths=[ROOT/'data/blog-batch-20261111-set3.json']
 for p in POSTS:
  paths+=[ROOT/'data/content'/f'blog-20261111-{p["key"]}.html']+list((ROOT/'blog'/p['slug']).glob('*.html'))+list((ROOT/'blog'/p['slug']).glob('*.svg'))
 for f in paths:
  if word in f.read_text(encoding='utf8'):violations.append(f.relative_to(ROOT).as_posix())
 for filename in ['feed.xml','sitemap.xml','llms.txt','llms-full.txt','data/blog-posts.json','search-index.json']:
  f=ROOT/filename;new=f.read_text(encoding='utf8');old=baseline(filename)
  if old is None:continue
  if word in new:
   if new.count(word)>old.count(word):violations.append(filename+' increased')
   existing.append(dict(path=filename,before=old.count(word),after=new.count(word)))
  if filename=='search-index.json':
   obj=json.loads(new);rows=obj if isinstance(obj,list) else obj.get('pages',obj.get('items',[]))
   for row in rows:
    raw=json.dumps(row,ensure_ascii=False)
    if any(p['slug'] in raw for p in POSTS) and word in raw:violations.append('search batch record')
 save(OUT/'banned-check.json',dict(status='pass' if not violations else 'fail',batch_hits=violations,preexisting_shared_hits=existing))
 print(json.dumps(dict(status='pass' if not violations else 'fail',batch_hits=violations,preexisting_shared_hits=existing),ensure_ascii=False))
 return not violations
if __name__=='__main__':raise SystemExit(0 if (banned() if '--banned' in sys.argv else check(local='--local' in sys.argv)) else 1)
