"""Four source-bound Friday features; shared assembly runs once per batch."""
import json,re,hashlib,concurrent.futures,urllib.request,datetime
from pathlib import Path
from bs4 import BeautifulSoup
import fitz
from build_blog_20261104 import page,save
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'test-results/dedicated-publish/20261107'
DATE='2026-11-07'
POSTS=json.loads((ROOT/'data/blog-batch-20261107.json').read_text(encoding='utf8'))
SOURCES={
'recruit':['森町「森町観光ボランティアの募集について」','https://www.town.morimachi.shizuoka.jp/gyosei/kanko_bunka/kanko/1473.html'],
'guide':['森町「観光ボランティアガイド会員申込用紙」','https://www.town.morimachi.shizuoka.jp/material/files/group/8/moushikomisho.pdf'],
'town-tourism':['森町「観光」','https://www.town.morimachi.shizuoka.jp/gyosei/kanko_bunka/kanko/index.html'],
'fire':['袋井消防本部「イベント等における露店等の開設届出と消火器の準備について」','https://www.city.fukuroi.shizuoka.jp/soshiki/38/1/shobo/1422535067729.html'],
'ordinance':['袋井市森町広域行政組合火災予防条例','https://www.city.fukuroi.shizuoka.jp/section/d1w_reiki_kumiai/H346901030021/H346901030021_j.html'],
'festival':['森町「第39回森町産業祭」','https://www.town.morimachi.shizuoka.jp/gyosei/kanko_bunka/eventjoho/6981.html'],
'town-fire':['森町「袋井消防庁舎の見学、訓練指導、視察のご案内」','https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/kikikanrika/kikikanrikakari/2/3359.html'],
'fees':['森町「森町文化会館使用料」','https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/bunkakaikan/bunka/2733.html'],
'hall':['森町「森町文化会館施設紹介」','https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/bunkakaikan/bunka/912.html'],
'usage':['森町文化会館「ご利用案内」','https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/bunkakaikan/bunka/904.html'],
'archive':['森町「リモート祭り囃子ライブ配信について」2020年告知','https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/sangyoseisakuka/kankoshinkokakari/1/3611.html'],
'newsletter':['森町「広報もりまち2020年12月号」8ページ','https://www.town.morimachi.shizuoka.jp/material/files/group/4/202012kouhou.pdf'],
'tokiwa':['常磐会「記念行事・その他の行事」','https://www.morimachi-tokiwakai.com/annual-events/memorial/']}

def fetch_sources():
 OUT.mkdir(parents=True,exist_ok=True)
 def fetch(k):
  name,url=SOURCES[k]
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=45) as r: data=r.read();status=r.status;final=r.url
   (OUT/f'source-{k}.bin').write_bytes(data)
   if data.startswith(b'%PDF'):text='\n'.join(p.get_text() for p in fitz.open(stream=data,filetype='pdf'))
   else:text=BeautifulSoup(data,'html.parser').get_text(' ',strip=True)
   (OUT/f'source-{k}.txt').write_text(text,encoding='utf8')
   return dict(key=k,url=url,status=status,final_url=final,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),checked_at=datetime.datetime.now().isoformat(),text_record=f'test-results/dedicated-publish/source-{k}.txt')
  except Exception as e:return dict(key=k,url=url,status=0,error=str(e))
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:rows=list(ex.map(fetch,SOURCES))
 save(OUT/'sources-http.json',rows)
 print(json.dumps(rows,ensure_ascii=False))
 return all(r['status']==200 for r in rows)

def assemble():
 ledger=ROOT/'data/blog-posts.json';data=json.loads(ledger.read_text(encoding='utf8'))
 for p in POSTS:
  folder=ROOT/'blog'/p['slug'];folder.mkdir(exist_ok=True)
  p['sources']=p['source_keys'];page(p,folder,SOURCES,date=DATE)
  html=folder/'index.html';raw=html.read_text(encoding='utf8')
  raw=re.sub(r'(src="/blog/[^"]+/fig[12]\.svg") width="1000" height="560"',r'\1 width="600" height="800"',raw)
  html.write_text(raw,encoding='utf8')
  rev=ROOT/'blog'/p['reverse']/'index.html';old=rev.read_text(encoding='utf8');href='/blog/'+p['slug']+'/'
  if href not in old:
   start=old.index('<div class="post-editorial-body">');end=old.index('<div class="action-grid">',start)
   paras=list(re.finditer(r'<p(?:\s[^>]*)?>.*?</p>',old[start:end],re.S))
   pos=start+paras[min(5,len(paras)-1)].end()
   old=old[:pos]+f'<p>{p["lead"]}<a href="{href}">{p["title"]}</a>をご覧ください。</p>'+old[pos:]
   old=re.sub(r'("dateModified"\s*:\s*")[^"]+',r'\g<1>'+DATE,old)
   rev.write_text(old,encoding='utf8')
  next(r for r in data['posts'] if r['slug']==p['reverse'])['modified']=DATE
  row={k:p[k] for k in ['slug','title','query','description']}
  row.update(date=DATE,modified=DATE,axis='sat',home_description=p['description'],cta='official',primary_source='・'.join(SOURCES[k][0] for k in p['source_keys'])+'（2026年11月7日確認）',cover_alt=p['scene'],search_index=True)
  existing=next((r for r in data['posts'] if r['slug']==p['slug']),None)
  if existing:existing.update(row)
  else:data['posts'].append(row)
 save(ledger,data)
if __name__=='__main__':
 import sys
 if '--sources' in sys.argv:raise SystemExit(0 if fetch_sources() else 1)
 assemble()
