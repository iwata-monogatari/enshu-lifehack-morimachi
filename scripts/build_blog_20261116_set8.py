"""Source capture and assembly for the November 16 set-8 batch.

Same flow as build_blog_20261109_additional.py:
- Source fetching uses the default opener (this VM reaches the web through
  the configured proxy).
- The cover reference is rewritten from cover.jpg to cover.svg after
  assembly, because the push route available here carries UTF-8 text only
  and cannot carry the binary JPEG. cover.svg holds the same vector artwork
  that the JPEG is rasterized from; the local cover.jpg is still generated
  by the illustrate step so every local gate runs unchanged.
"""
import json,re,datetime,hashlib,concurrent.futures,urllib.request
from pathlib import Path
from bs4 import BeautifulSoup
from build_blog_20261104 import page,save
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'work-records/browser-proof/20261116-set8'
DATE='2026-11-16'
META=ROOT/'data/blog-batch-20261116-set8.json'
POSTS=json.loads(META.read_text(encoding='utf8')) if META.exists() else []
TOWN='https://www.town.morimachi.shizuoka.jp/'
SOURCES={
'mynumber-kofu':['森町「マイナンバーカードの交付について」','https://www.town.morimachi.shizuoka.jp/gyosei/kurashi_tetsuzuki/mynumber/1284.html'],
'mynumber-card':['森町「【通知カード】【個人番号カード】とは」','https://www.town.morimachi.shizuoka.jp/gyosei/kurashi_tetsuzuki/mynumber/1280.html'],
'kokuho':['森町「国民健康保険」','https://www.town.morimachi.shizuoka.jp/gyosei/kurashi_tetsuzuki/nenkin_kenkohoken/kokuminkenkohoken/1146.html'],
'kokuho-myna':['森町「マイナンバーカードの健康保険証利用について」','https://www.town.morimachi.shizuoka.jp/gyosei/kurashi_tetsuzuki/nenkin_kenkohoken/kokuminkenkohoken/5811.html'],
'jido-teate':['森町「児童手当について」','https://www.town.morimachi.shizuoka.jp/gyosei/kosodate_kyoiku/teate_josei/jidoteateto/5316.html'],
'jido-denshi':['森町「ご自宅で児童手当の申請ができます」','https://www.town.morimachi.shizuoka.jp/gyosei/kosodate_kyoiku/teate_josei/jidoteateto/2538.html'],
'jido-kaisei':['森町「児童手当制度が変わります」','https://www.town.morimachi.shizuoka.jp/gyosei/kosodate_kyoiku/teate_josei/jidoteateto/5467.html'],
'choei':['森町「森町の町営住宅（公営住宅）」','https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/teijusuishinka/sumaishiengakari/4/412.html'],
'choei-amamiya':['森町「町営住宅天宮団地」','https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/teijusuishinka/sumaishiengakari/4/406.html'],
'choei-yazaki':['森町「町営住宅やざき団地」','https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/teijusuishinka/sumaishiengakari/4/411.html']}

def fetch_sources():
 OUT.mkdir(parents=True,exist_ok=True)
 def fetch(k):
  url=SOURCES[k][1]
  try:
   op=urllib.request.build_opener()
   with op.open(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=45) as r:data=r.read();status=r.status;final=r.url
   (OUT/f'source-{k}.bin').write_bytes(data)
   s=BeautifulSoup(data,'html.parser')
   for e in s.select('script,style'):e.decompose()
   (OUT/f'source-{k}.txt').write_text(s.get_text(' ',strip=True),encoding='utf8')
   return dict(key=k,url=url,status=status,final_url=final,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),checked_at=datetime.datetime.now().isoformat())
  except Exception as e:return dict(key=k,url=url,status=0,error=str(e))
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:rows=list(ex.map(fetch,SOURCES))
 save(OUT/'sources-http.json',rows)
 print(json.dumps([dict(key=r['key'],status=r['status'],error=r.get('error','')) for r in rows],ensure_ascii=False))
 return all(r['status']==200 for r in rows)

def assemble():
 ledger=ROOT/'data/blog-posts.json';data=json.loads(ledger.read_text(encoding='utf8'))
 for p in POSTS:
  folder=ROOT/'blog'/p['slug'];folder.mkdir(exist_ok=True)
  p['sources']=p['source_keys'];page(p,folder,SOURCES,date=DATE)
  f=folder/'index.html';raw=f.read_text(encoding='utf8')
  raw=re.sub(r'(src="/blog/[^\"]+/fig[12]\.svg") width="1000" height="560"',r'\1 width="600" height="800"',raw)
  raw=raw.replace('公開状況や案内は変わる場合があります。現地を訪れる前に管理者の最新案内をご確認ください。','サービスや手続きの案内は変わる場合があります。利用・申請前に公式の最新案内をご確認ください。')
  raw=raw.replace('/blog/'+p['slug']+'/cover.jpg','/blog/'+p['slug']+'/cover.svg')
  f.write_text(raw,encoding='utf8')
  rev=ROOT/'blog'/p['reverse']/'index.html';old=rev.read_text(encoding='utf8');href='/blog/'+p['slug']+'/'
  if href not in old:
   start=old.index('<div class="post-editorial-body">');paras=list(re.finditer(r'<p(?:\s[^>]*)?>.*?</p>',old[start:],re.S));pos=start+paras[4].end()
   old=old[:pos]+f'<p>{p["lead"]}<a href="{href}">{p["title"]}</a>で確認できます。</p>'+old[pos:]
   old=re.sub(r'("dateModified"\s*:\s*")[^\"]+',r'\g<1>'+DATE,old)
   old=old.replace('/assets/blog.css','/assets/site.css')
   rev.write_text(old,encoding='utf8')
  next(r for r in data['posts'] if r['slug']==p['reverse'])['modified']=DATE
  row={k:p[k] for k in ['slug','title','query','description']}
  row.update(date=DATE,modified=DATE,axis='sat',home_description=p['description'],cta='official',primary_source='・'.join(SOURCES[k][0] for k in p['source_keys'])+'（2026年11月16日確認）',cover_alt=p['scene'],search_index=True)
  existing=next((r for r in data['posts'] if r['slug']==p['slug']),None)
  if existing:existing.update(row)
  else:data['posts'].append(row)
 save(ledger,data)
if __name__=='__main__':
 import sys
 if '--sources' in sys.argv:raise SystemExit(0 if fetch_sources() else 1)
 assemble()
