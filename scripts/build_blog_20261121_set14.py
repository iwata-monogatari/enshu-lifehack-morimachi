"""Source capture and assembly for the November 21 set-14 batch (morimachi).
Adapted from build_blog_20261120_set13.py: same flow, cover.jpg -> cover.svg rewrite."""
import json,re,datetime,hashlib,concurrent.futures,urllib.request
from pathlib import Path
from bs4 import BeautifulSoup
from build_blog_20261104 import page,save
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'work-records/browser-proof/20261121-set14'
DATE='2026-11-21'
META=ROOT/'data/blog-batch-20261121-set14.json'
POSTS=json.loads(META.read_text(encoding='utf8')) if META.exists() else []
SOURCES={
'sango-menjo':['森町「産前産後の国民健康保険税の免除について」','https://www.town.morimachi.shizuoka.jp/gyosei/kurashi_tetsuzuki/zeikin/kokuminkenkohokenzei/5239.html'],
'kokuho-toha':['森町「国民健康保険税とは」','https://www.town.morimachi.shizuoka.jp/gyosei/kurashi_tetsuzuki/zeikin/kokuminkenkohokenzei/5164.html'],
'kokuho-faq':['森町「国民健康保険税のよくある質問」','https://www.town.morimachi.shizuoka.jp/gyosei/kurashi_tetsuzuki/zeikin/kokuminkenkohokenzei/5165.html'],
'zaitaku-fukushi':['森町「高齢者の在宅福祉サービスについて」','https://www.town.morimachi.shizuoka.jp/gyosei/kenko_fukushi/koreishashien/4004.html'],
'kinkyu-pdf':['森町「緊急通報システムのしくみ」','https://www.town.morimachi.shizuoka.jp/material/files/group/7/kinkyuutsuhou.pdf'],
'koreisha-sodan':['森町「高齢者のための相談窓口」','https://www.town.morimachi.shizuoka.jp/gyosei/kenko_fukushi/koreishashien/4003.html'],
'gomi-calendar':['森町「森町家庭ごみ分別表、収集日カレンダー、分別ガイドブック（保存版）」','https://www.town.morimachi.shizuoka.jp/gyosei/kurashi_tetsuzuki/gomi_risaikuru/gomi/1491.html'],
'gomi-dashikata':['森町「ごみの出し方」','https://www.town.morimachi.shizuoka.jp/gyosei/kurashi_tetsuzuki/gomi_risaikuru/gomi/1138.html'],
'gomi-index':['森町「ごみ」','https://www.town.morimachi.shizuoka.jp/gyosei/kurashi_tetsuzuki/gomi_risaikuru/gomi/index.html'],
'shinryojo-shien':['森町「森町診療所開設または事業承継支援事業のお知らせ」','https://www.town.morimachi.shizuoka.jp/gyosei/kenko_fukushi/kenkoukanri_kansennshou/4650.html'],
'byoin-annai':['森町「公立森町病院ホームページ」','https://www.town.morimachi.shizuoka.jp/gyosei/kenko_fukushi/morimachi_hospital/5810.html'],
'kenko-fukushi-index':['森町「健康・福祉」','https://www.town.morimachi.shizuoka.jp/gyosei/kenko_fukushi/index.html']}

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
  row.update(date=DATE,modified=DATE,axis='sat',home_description=p['description'],cta='official',primary_source='・'.join(SOURCES[k][0] for k in p['source_keys'])+'（2026年11月21日確認）',cover_alt=p['scene'],search_index=True)
  existing=next((r for r in data['posts'] if r['slug']==p['slug']),None)
  if existing:existing.update(row)
  else:data['posts'].append(row)
 save(ledger,data)
if __name__=='__main__':
 import sys
 if '--sources' in sys.argv:raise SystemExit(0 if fetch_sources() else 1)
 assemble()
