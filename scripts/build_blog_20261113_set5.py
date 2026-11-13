"""Source capture and assembly for the November 10 Tuesday set-2 batch.

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
OUT=ROOT/'work-records/browser-proof/20261113-set5'
DATE='2026-11-13'
META=ROOT/'data/blog-batch-20261113-set5.json'
POSTS=json.loads(META.read_text(encoding='utf8')) if META.exists() else []
TOWN='https://www.town.morimachi.shizuoka.jp/'
SOURCES={
'suido-todoke':['森町「水道の開始・廃止・名義変更等の届出について」',TOWN+'gyosei/kurashi_tetsuzuki/jogesuido/1405.html'],
'kenshin-ryokin':['森町「上水道・簡易水道の検針・料金等について」',TOWN+'gyosei/kurashi_tetsuzuki/jogesuido/josuido/1402.html'],
'gomi-dasikata':['森町「ごみの出し方」',TOWN+'gyosei/kurashi_tetsuzuki/gomi_risaikuru/gomi/1138.html'],
'sodai-shisetsu':['森町「中遠広域粗大ごみ処理施設」',TOWN+'gyosei/machinososhiki/juminseikatsuka/seikatsukankyokakari/1/1/6837.html'],
'inkan-toroku':['森町「印鑑登録」',TOWN+'gyosei/machinososhiki/juminseikatsuka/juminkakari/2/1/565.html'],
'shinsei-yoshiki':['森町「申請書（委任状・住民票・印鑑証明・戸籍）」',TOWN+'gyosei/choseijoho/shinsei_todokede_gyoseiservice/2612.html'],
'entai':['森町「町税の滞納と延滞金」',TOWN+'gyosei/kurashi_tetsuzuki/zeikin/nofu/1375.html'],
'kotei-nofu':['森町「固定資産税・都市計画税の納付について」',TOWN+'gyosei/machinososhiki/zeimuka/shisanzeigakari/1/koteitosikeizenpan/539.html']}

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
  row.update(date=DATE,modified=DATE,axis='fri',home_description=p['description'],cta='official',primary_source='・'.join(SOURCES[k][0] for k in p['source_keys'])+'（2026年11月13日確認）',cover_alt=p['scene'],search_index=True)
  existing=next((r for r in data['posts'] if r['slug']==p['slug']),None)
  if existing:existing.update(row)
  else:data['posts'].append(row)
 save(ledger,data)
if __name__=='__main__':
 import sys
 if '--sources' in sys.argv:raise SystemExit(0 if fetch_sources() else 1)
 assemble()
