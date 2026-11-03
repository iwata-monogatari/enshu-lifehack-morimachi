"""Batch-specific read-only quality checks with durable evidence."""
from pathlib import Path
import json,re,sys,contextlib,io,hashlib,urllib.request,concurrent.futures,datetime,xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from PIL import Image,ImageDraw
import fitz
from build_blog_20261103_followup import POSTS,SOURCES,ROOT,OUT,SITE,save

def sources():
 def get(item):
  k,(name,url)=item
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=45) as r:b=r.read();status=r.status;final=r.url
   if b.startswith(b'%PDF'):
    d=fitz.open(stream=b,filetype='pdf');text='\n'.join(p.get_text() for p in d)
   else:
    # These sources declare UTF-8; meta decoding avoids the platform default.
    text=BeautifulSoup(b,'html.parser').get_text(' ',strip=True)
   path=OUT/('source-'+k+'.txt');path.write_text(text,encoding='utf-8')
   return {'key':k,'url':url,'name':name,'status':status,'final_url':final,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'checked_at':datetime.datetime.now().isoformat(),'text_record':path.relative_to(ROOT).as_posix()}
  except Exception as e:return {'key':k,'url':url,'status':0,'error':str(e)}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:rows=list(ex.map(get,SOURCES.items()))
 save('sources-http.json',rows)
 print(json.dumps({'sources':len(rows),'failures':[x for x in rows if x['status']!=200]},ensure_ascii=False));return all(x['status']==200 for x in rows)

def article():
 import build_blog
 allposts=json.loads((ROOT/'data/blog-posts.json').read_text(encoding='utf-8'))['posts']
 with contextlib.redirect_stdout(io.StringIO()):problems=build_blog.audit(allposts)
 newslugs={p['slug'] for p in POSTS};problems=[x for x in problems if x[0] in newslugs]
 reports=[]
 for p in POSTS:
  f=ROOT/'blog'/p['slug']/'index.html';raw=f.read_text(encoding='utf-8');s=BeautifulSoup(raw,'html.parser');body=s.select_one('.post-editorial-body');issues=[]
  count=len(re.sub(r'\s+','',body.get_text()));paragraphs=len(body.find_all('p'))
  if count<5000 or paragraphs<35:issues.append('body length')
  gs=[]
  for el in s.select('script[type="application/ld+json"]'):
   obj=json.loads(el.string);gs+=obj.get('@graph',[obj])
  if not all(any(g.get('@type')==t for g in gs) for t in ['BlogPosting','Person','BreadcrumbList','FAQPage']):issues.append('schema')
  bp=next(g for g in gs if g.get('@type')=='BlogPosting');faq=next(g for g in gs if g.get('@type')=='FAQPage')['mainEntity']
  if len(faq)!=3:issues.append('faq')
  for q in faq:
   if q['name'] not in body.get_text() or q['acceptedAnswer']['text'] not in body.get_text():issues.append('faq schema mismatch')
  if bp['datePublished']!='2026-11-03' or bp['dateModified']!='2026-11-03':issues.append('date')
  url=SITE+'/blog/'+p['slug']+'/'
  if s.h1.get_text()!=p['title'] or s.select_one('link[rel="canonical"]')['href']!=url:issues.append('title/canonical')
  if len(p['answer'])>200:issues.append('answer >200')
  if not s.select_one('.post-author img[src="/assets/author-oishi.jpg"]'):issues.append('author')
  links=[a['href'] for a in body.select('a[href^="/blog/"]')]
  if not 3<=len(links)<=5:issues.append('internal links')
  for a in links:
   if not (ROOT/a.strip('/')/'index.html').exists():issues.append('broken '+a)
  rev=ROOT/'blog'/p['reverse']/'index.html'
  if '/blog/'+p['slug']+'/' not in rev.read_text(encoding='utf-8'):issues.append('backlink')
  for h in body.find_all('h2'):
   nxt=h.find_next_sibling()
   if not nxt or nxt.name!='p' or re.match(r'(これ|それ|その|上記)',nxt.get_text()):issues.append('h2 opening '+h.get_text())
  images=[]
  for im in s.select('article img'):
   file=ROOT/im['src'].lstrip('/')
   if not file.exists():issues.append('missing image')
   images.append({'source':im['src'],'local_exists':file.exists(),'page_reference':True,'alt':im.get('alt','')})
  for n in (1,2):ET.parse(ROOT/'blog'/p['slug']/f'fig{n}.svg')
  reports.append({'slug':p['slug'],'title':p['title'],'html_title':s.title.get_text(),'characters':count,'paragraphs':paragraphs,'faq_lengths':[len(a) for q,a in p['faq']],'answer_length':len(p['answer']),'links':links,'reverse':p['reverse'],'images':images,'issues':issues})
  problems.extend((p['slug'],x) for x in issues)
 save('article-check.json',{'articles':reports,'problems':problems});print(json.dumps({'articles':[{k:x[k] for k in ['slug','characters','paragraphs','issues']} for x in reports],'problems':problems},ensure_ascii=False));return not problems

def banned():
 token='\u653f\u7b56';phrases=['いかがでしたか','と言えるでしょう','ではないでしょうか','重要です','ポイントは3つです','まとめると','していきましょう','ぜひ','近年、','が求められています']
 hits=[];files=[]
 for p in POSTS:
  files += [ROOT/'data/content'/f'blog-20261103-{p["key"]}.html']+[ROOT/'blog'/p['slug']/name for name in ['index.html','fig1.svg','fig2.svg']]
 for f in files:
  text=f.read_text(encoding='utf-8')
  for word in [token]+phrases:
   if word in text:hits.append({'path':f.relative_to(ROOT).as_posix(),'word':word})
 save('banned-check.json',{'status':'pass' if not hits else 'fail','files':len(files),'hits':hits});print('Independent banned check:',len(hits),'hits');return not hits

def images():
 sheet=Image.new('RGB',(1200,4*250),'white');d=ImageDraw.Draw(sheet);rows=[]
 for i,p in enumerate(POSTS):
  for j,name in enumerate(['cover.jpg','fig1.svg','fig2.svg']):
   f=ROOT/'blog'/p['slug']/name
   if name.endswith('.svg'):
    doc=fitz.open(stream=f.read_bytes(),filetype='svg');pdf=fitz.open('pdf',doc.convert_to_pdf());px=pdf[0].get_pixmap();im=Image.frombytes('RGB',[px.width,px.height],px.samples)
   else:im=Image.open(f);im.load()
   dims=list(im.size);im.thumbnail((390,218));sheet.paste(im,(j*400,i*250+22));d.text((j*400+4,i*250+3),p['key']+' '+name,fill='black')
   rows.append({'path':f.relative_to(ROOT).as_posix(),'dimensions':dims,'decoded':True,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
 sheet.save(OUT/'contact-sheet.jpg',quality=90);save('images-decoded.json',rows);print('Decoded',len(rows),'article-specific images; contact sheet saved');return True

if __name__=='__main__':
 tasks={'sources':sources,'article':article,'banned':banned,'images':images}
 sys.exit(0 if tasks[sys.argv[1]]() else 1)
