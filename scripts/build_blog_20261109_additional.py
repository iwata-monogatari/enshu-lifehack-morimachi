"""Source capture and assembly for the November 9 Monday additional batch.

Same flow as build_blog_20261108.py, with two environment adaptations:
- Source fetching uses the default opener (this VM reaches the web through
  the configured proxy; the dated script's direct opener cannot connect).
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
OUT=ROOT/'work-records/browser-proof/20261109-additional'
DATE='2026-11-09'
META=ROOT/'data/blog-batch-20261109-additional.json'
POSTS=json.loads(META.read_text(encoding='utf8')) if META.exists() else []
TOWN='https://www.town.morimachi.shizuoka.jp/'
SOURCES={
'nintei-flow':['森町「要介護（要支援）認定申請・サービス利用までの流れについて」',TOWN+'gyosei/machinososhiki/hokenfukushika/kaigohokengakari/4/1/403.html'],
'nintei-index':['森町「要介護認定申請・介護保険サービスの利用等について」',TOWN+'gyosei/kurashi_tetsuzuki/nenkin_kenkohoken/kaigohoken/4204.html'],
'careplan':['森町「ケアプランの作成について」',TOWN+'gyosei/machinososhiki/hokenfukushika/kaigohokengakari/4/1/4897.html'],
'furusato-flow':['総務省「ふるさと納税の流れ」','https://www.soumu.go.jp/main_sosiki/jichi_zeisei/czaisei/czaisei_seido/furusato/mechanism/procedure.html'],
'furusato-topics':['総務省「ふるさと納税ワンストップ特例制度について」','https://www.soumu.go.jp/main_sosiki/jichi_zeisei/czaisei/czaisei_seido/furusato/topics/20150401.html'],
'furusato-town':['森町「森町ふるさと納税」',TOWN+'gyosei/kurashi_tetsuzuki/furusatonozei/1230.html'],
'furusato-shinkoku':['森町「ふるさと納税をされた方のための確定申告書等について」',TOWN+'gyosei/kurashi_tetsuzuki/furusatonozei/1264.html'],
'nta-iryohi':['国税庁「医療費を支払ったとき（医療費控除）」','https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1120.htm'],
'shinkoku-yoyaku':['森町「確定申告（町民生活センター会場）事前予約についてのお知らせ」',TOWN+'gyosei/kurashi_tetsuzuki/zeikin/kakuteishinkoku/1350.html'],
'shinkoku-hitsuyo':['森町「確定申告（所得税）または町県民税申告が必要な方とは」',TOWN+'gyosei/kurashi_tetsuzuki/zeikin/kakuteishinkoku/3674.html'],
'jido-about':['森町「児童手当について」',TOWN+'gyosei/kosodate_kyoiku/teate_josei/jidoteateto/5316.html'],
'jido-online':['森町「ご自宅で児童手当の申請ができます」',TOWN+'gyosei/kosodate_kyoiku/teate_josei/jidoteateto/2538.html'],
'jido-change':['森町「児童手当制度が変わります」',TOWN+'gyosei/kosodate_kyoiku/teate_josei/jidoteateto/5467.html']}

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
  row.update(date=DATE,modified=DATE,axis='mon',home_description=p['description'],cta='official',primary_source='・'.join(SOURCES[k][0] for k in p['source_keys'])+'（2026年11月9日確認）',cover_alt=p['scene'],search_index=True)
  existing=next((r for r in data['posts'] if r['slug']==p['slug']),None)
  if existing:existing.update(row)
  else:data['posts'].append(row)
 save(ledger,data)
if __name__=='__main__':
 import sys
 if '--sources' in sys.argv:raise SystemExit(0 if fetch_sources() else 1)
 assemble()
