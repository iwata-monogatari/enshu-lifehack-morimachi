"""Source capture and assembly for the November 17 set-9 batch.

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
OUT=ROOT/'work-records/browser-proof/20261117-set9'
DATE='2026-11-17'
META=ROOT/'data/blog-batch-20261117-set9.json'
POSTS=json.loads(META.read_text(encoding='utf8')) if META.exists() else []
TOWN='https://www.town.morimachi.shizuoka.jp/'
SOURCES={
'nenkin':['森町「国民年金」','https://www.town.morimachi.shizuoka.jp/gyosei/kurashi_tetsuzuki/nenkin_kenkohoken/kokuminnenkin/1148.html'],
'nenkin-index':['森町「保険・年金」','https://www.town.morimachi.shizuoka.jp/gyosei/kurashi_tetsuzuki/nenkin_kenkohoken/index.html'],
'tsuino-pdf':['日本年金機構「国民年金保険料の追納制度」','https://www.nenkin.go.jp/service/pamphlet/kokuminnenkin.files/tuino2.pdf'],
'ninpu':['森町「妊婦の健康診査」','https://www.town.morimachi.shizuoka.jp/gyosei/kosodate_kyoiku/ninshin_shussan/nimpunokenkoshinsa/index.html'],
'boshi':['森町「母子健康手帳」','https://www.town.morimachi.shizuoka.jp/gyosei/kosodate_kyoiku/ninshin_shussan/boshikenkotecho/index.html'],
'ninshin':['森町「妊娠したら（健診・訪問について）」','https://www.town.morimachi.shizuoka.jp/morikko/ninshin_shussan/4805.html'],
'kyoten':['森町「資源ごみの拠点回収について」','https://www.town.morimachi.shizuoka.jp/gyosei/kurashi_tetsuzuki/gomi_risaikuru/recycle/4252.html'],
'gomi-dashikata':['森町「ごみの出し方」','https://www.town.morimachi.shizuoka.jp/gyosei/kurashi_tetsuzuki/gomi_risaikuru/gomi/1138.html'],
'bunbetsu':['森町「家庭ごみ分別表、収集日カレンダー、分別ガイドブック」','https://www.town.morimachi.shizuoka.jp/gyosei/kurashi_tetsuzuki/gomi_risaikuru/gomi/1491.html'],
'hinanjo':['森町「町指定避難所等について」','https://www.town.morimachi.shizuoka.jp/gyosei/bosai_anzen/bosai/1195.html'],
'bichiku':['森町「防災倉庫備蓄資機材」','https://www.town.morimachi.shizuoka.jp/gyosei/bosai_anzen/bosai/1196.html'],
'bosai-info':['森町「防災情報」','https://www.town.morimachi.shizuoka.jp/gyosei/bosai_anzen/bosai/1129.html']}

def fetch_sources():
 OUT.mkdir(parents=True,exist_ok=True)
 def fetch(k):
  url=SOURCES[k][1]
  try:
   op=urllib.request.build_opener()
   with op.open(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=45) as r:data=r.read();status=r.status;final=r.url
   (OUT/f'source-{k}.bin').write_bytes(data)
   if url.endswith('.pdf'):
    import subprocess,os
    subprocess.run(['pdftotext','-layout',str(OUT/f'source-{k}.bin'),str(OUT/f'source-{k}.txt')],check=False)
    return dict(key=k,url=url,status=status,final_url=final,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),checked_at=datetime.datetime.now().isoformat())
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
  row.update(date=DATE,modified=DATE,axis='sat',home_description=p['description'],cta='official',primary_source='・'.join(SOURCES[k][0] for k in p['source_keys'])+'（2026年11月17日確認）',cover_alt=p['scene'],search_index=True)
  existing=next((r for r in data['posts'] if r['slug']==p['slug']),None)
  if existing:existing.update(row)
  else:data['posts'].append(row)
 save(ledger,data)
if __name__=='__main__':
 import sys
 if '--sources' in sys.argv:raise SystemExit(0 if fetch_sources() else 1)
 assemble()
