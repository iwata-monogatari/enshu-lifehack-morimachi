"""Read-only release audits, with saved observations for this approved batch."""
from pathlib import Path
import json,re,hashlib,sys,urllib.request,concurrent.futures,datetime,html,xml.etree.ElementTree as ET,contextlib,io
from bs4 import BeautifulSoup
from PIL import Image,ImageDraw,ImageFont
import fitz
from build_blog_20261103 import SOURCES,DETAILS
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'test-results/dedicated-publish';OUT.mkdir(parents=True,exist_ok=True)
DATA=json.loads((ROOT/'data/blog-batch-20261103.json').read_text(encoding='utf-8'));POSTS=DATA['articles']
def save(name,data):
 p=OUT/name;p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');assert json.loads(p.read_text(encoding='utf-8'))==data
def sources():
 previous=json.loads((OUT/'sources-http.json').read_text(encoding='utf-8')) if (OUT/'sources-http.json').exists() else []
 valid={x['key']:x for x in previous if x.get('status')==200 and x.get('url')==SOURCES.get(x['key'],('',None))[1]}
 def get(item):
  k,(name,url)=item
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; source-verification/1.0)'})
   with urllib.request.urlopen(req,timeout=35) as r: body=r.read();status=r.status;final=r.url;ctype=r.headers.get('Content-Type','')
   return {'key':k,'url':url,'final_url':final,'name':name,'status':status,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'content_type':ctype,'checked_at':datetime.datetime.now().isoformat()}
  except Exception as e:return {'key':k,'url':url,'error':str(e),'status':0}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:new=list(ex.map(get,[(k,v) for k,v in SOURCES.items() if k not in valid]))
 valid.update({x['key']:x for x in new});results=[valid[k] for k in SOURCES]
 save('sources-http.json',results);print(json.dumps({'sources':len(results),'failures':[x for x in results if x['status']!=200]},ensure_ascii=False));return all(x['status']==200 for x in results)
def article():
 import build_blog
 ledger=json.loads((ROOT/'data/blog-posts.json').read_text(encoding='utf-8'));rows=[x for x in ledger['posts'] if x['slug'] in {p['slug'] for p in POSTS}]
 with contextlib.redirect_stdout(io.StringIO()):problems=build_blog.audit(rows)
 reports=[]
 for p in POSTS:
  path=ROOT/'blog'/p['slug']/'index.html';raw=path.read_text(encoding='utf-8');soup=BeautifulSoup(raw,'html.parser');body=soup.select_one('.post-editorial-body');issues=[]
  types=[];graphs=[]
  for el in soup.select('script[type="application/ld+json"]'):
   obj=json.loads(el.string);graphs.extend(obj.get('@graph',[obj]))
  types=[x.get('@type') for x in graphs]
  if not all(t in types for t in ['BlogPosting','BreadcrumbList','FAQPage','Person']):issues.append('schema types')
  faq=next(x for x in graphs if x.get('@type')=='FAQPage')['mainEntity']
  if len(faq)!=3:issues.append('FAQ count')
  for q in faq:
   if q['name'] not in body.get_text() or q['acceptedAnswer']['text'] not in body.get_text():issues.append('FAQ mismatch')
  bp=next(x for x in graphs if x.get('@type')=='BlogPosting')
  if bp['datePublished']!='2026-11-03' or bp['dateModified']!='2026-11-03':issues.append('schema date')
  canonical=SITE+'/blog/'+p['slug']+'/'
  if soup.select_one('link[rel="canonical"]')['href']!=canonical:issues.append('canonical')
  if soup.h1.get_text()!=p['title']:issues.append('title')
  links=[a['href'] for a in body.select('a[href^="/blog/"]')]
  if len(links)<3 or len(links)>5:issues.append('internal link count')
  for link in links:
   if not (ROOT/link.strip('/')/'index.html').exists():issues.append('missing '+link)
  reverse=(ROOT/'blog'/p['reverse']/'index.html').read_text(encoding='utf-8')
  if '/blog/'+p['slug']+'/' not in reverse:issues.append('backlink')
  if not soup.select_one('.post-author img[src="/assets/author-oishi.jpg"]'):issues.append('author photo')
  if len(p['answer'])>200:issues.append('answer length')
  images=[]
  for im in soup.select('article img'):
   src=im['src'];f=ROOT/src.lstrip('/')
   if not f.exists():issues.append('image missing '+src)
   images.append({'source':src,'exists':f.exists(),'alt':im.get('alt','')})
  for n in (1,2):ET.parse(ROOT/'blog'/p['slug']/f'fig{n}.svg')
  count=len(re.sub(r'\s+','',body.get_text()));paragraphs=len(body.find_all('p'))
  reports.append({'title':p['title'],'slug':p['slug'],'characters':count,'paragraphs':paragraphs,'answer_characters':len(p['answer']),'faq_lengths':[len(x['acceptedAnswer']['text']) for x in faq],'links':links,'reverse':p['reverse'],'images':images,'issues':issues})
  problems.extend((p['slug'],x) for x in issues)
 save('article-check.json',{'articles':reports,'problems':problems});print(json.dumps({'articles':[{k:x[k] for k in ['slug','characters','paragraphs','issues']} for x in reports],'problems':problems},ensure_ascii=False));return not problems
SITE='https://morimachi.enshu-lifehack.com'
def banned():
 bad='政'+'策';phrases=['いかがでしたか','と言えるでしょう','ではないでしょうか','重要です','ポイントは3つです','まとめると','していきましょう','ぜひ','近年、','が求められています'];issues=[]
 files=[]
 for p in POSTS:files.extend((ROOT/'blog'/p['slug']).glob('*'))
 for f in files:
  if f.suffix not in ['.html','.svg','.json']:continue
  text=f.read_text(encoding='utf-8')
  for token in [bad]+phrases:
   if token in text:issues.append({'file':str(f.relative_to(ROOT)),'token':token})
 ledger=json.loads((ROOT/'data/blog-posts.json').read_text(encoding='utf-8'))
 new=[p for p in ledger['posts'] if p['slug'] in {p['slug'] for p in POSTS}]
 if bad in json.dumps(new,ensure_ascii=False):issues.append({'file':'data/blog-posts.json','token':bad})
 # Isolate the batch records in shared outputs; preserve unrelated preexisting content.
 for name in ['feed.xml','sitemap.xml','search-index.json','llms.txt','llms-full.txt']:
  p=ROOT/name
  if not p.exists():continue
  text=p.read_text(encoding='utf-8')
  if name.endswith('.json'):
   data=json.loads(text)
   def walk(x):
    if isinstance(x,dict):
     if any(sl['slug'] in str(x.get(k,'')) for sl in POSTS for k in ['url','path','href','slug']):
      if bad in json.dumps(x,ensure_ascii=False):issues.append({'file':name,'token':bad})
     else:
      for v in x.values():walk(v)
    elif isinstance(x,list):
     for v in x:walk(v)
   walk(data)
  elif name.endswith('.xml'):
   tree=ET.fromstring(text)
   for el in tree.iter():
    if el.tag.split('}')[-1] in ['item','url']:
     content=ET.tostring(el,encoding='unicode')
     if any(p['slug'] in content for p in POSTS) and bad in content:issues.append({'file':name,'token':bad})
  else:
   for line in text.splitlines():
    if any(p['slug'] in line for p in POSTS) and bad in line:issues.append({'file':name,'token':bad})
 save('banned-check.json',{'scope':'new articles SVG HTML, new ledger/search records and matching distribution entries','issues':issues});print(json.dumps({'banned_and_phrases':issues},ensure_ascii=False));return not issues
def montage():
 sheet=Image.new('RGB',(1200,1000),'white');draw=ImageDraw.Draw(sheet);font=ImageFont.truetype('C:/Windows/Fonts/YuGothM.ttc',17);records=[]
 for i,p in enumerate(POSTS):
  for j,name in enumerate(['cover.jpg','fig1.svg','fig2.svg']):
   path=ROOT/'blog'/p['slug']/name
   if name.endswith('.svg'):
    doc=fitz.open(path);pdf=fitz.open('pdf',doc.convert_to_pdf());pix=pdf[0].get_pixmap();im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
   else: im=Image.open(path).convert('RGB')
   im.thumbnail((390,220));sheet.paste(im,(j*400,i*250+25));draw.text((j*400+5,i*250),str(i+1)+' '+name,font=font,fill='black')
   records.append({'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'decoded':True})
 sheet.save(OUT/'image-contact-sheet.jpg',quality=90);save('images-decoded.json',records);print('12 images decoded; image-contact-sheet.jpg saved');return True
if __name__=='__main__':
 fn={'sources':sources,'article':article,'banned':banned,'montage':montage}[sys.argv[1]];sys.exit(0 if fn() else 1)
