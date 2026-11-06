"""Four source-bound Friday features; shared assembly runs once per batch."""
import json,re,hashlib,concurrent.futures,urllib.request,datetime
from pathlib import Path
from bs4 import BeautifulSoup
import fitz
from build_blog_20261104 import page,save
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'test-results/dedicated-publish'
DATE='2026-11-06'
POSTS=json.loads((ROOT/'data/blog-batch-20261106.json').read_text(encoding='utf8'))
SOURCES={
 'ticket':['天竜浜名湖鉄道「お得な乗車券」','https://www.tenhama.co.jp/about/joshaken/'],
 'wheel':['天竜浜名湖鉄道「車椅子ご利用のお客様へ」','https://www.tenhama.co.jp/about/wheelchair/'],
 'cycle':['天竜浜名湖鉄道・2017年10月20日の輪行バッグ貸出告知','https://www.tenhama.co.jp/events/8980/'],
 'hospital':['公立森町病院「交通アクセス」','https://hospital.town.morimachi.shizuoka.jp/outline/access/'],
 'town-links':['森町「鉄道・民間路線バス・タクシー リンク集」','https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/seisakukikakuka/seisakukikakugakari/4/420.html'],
 'town-transport':['森町「森町の公共交通について」','https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/seisakukikakuka/seisakukikakugakari/4/422.html'],
 'school':['森町「子供の移動経路に関する交通安全プログラム」2022年2月','https://www.town.morimachi.shizuoka.jp/material/files/group/9/koutuuanzenpuroguramu2.pdf'],
 'childplan':['森町「森町こども計画」','https://www.town.morimachi.shizuoka.jp/material/files/group/27/localgovernmentchildplan.pdf']}

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
  row.update(date=DATE,modified=DATE,axis='fri',home_description=p['description'],cta='official',primary_source='・'.join(SOURCES[k][0] for k in p['source_keys'])+'（2026年11月6日確認）',cover_alt=p['scene'],search_index=True)
  existing=next((r for r in data['posts'] if r['slug']==p['slug']),None)
  if existing:existing.update(row)
  else:data['posts'].append(row)
 save(ledger,data)
if __name__=='__main__':
 import sys
 if '--sources' in sys.argv:raise SystemExit(0 if fetch_sources() else 1)
 assemble()
