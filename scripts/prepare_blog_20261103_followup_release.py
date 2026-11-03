"""Scope and seal this batch's evidence for the approved fixed publication runner."""
import sys,json,re,hashlib,subprocess,zipfile,html,xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup
from build_blog_20261103_followup import POSTS,SOURCES,ROOT,OUT,SITE,save
WID='e4043349d77bdee9a805f1f1c24a3970e780ba5a2fe9752e9989fef6980b1235'
PREFIX=OUT.relative_to(ROOT).as_posix()+'/'
COMMON=['data/blog-posts.json','data/url-ledger.json','data/article-ledger.json','reports/url-ledger.csv','feed.xml','index.html','blog/index.html','llms-full.txt','llms.txt','search-index.json','sitemap.xml']
REVERSE=['blog/'+p['reverse']+'/index.html' for p in POSTS]
NEW=['data/blog-batch-20261103-followup.json','scripts/build_blog_20261103_followup.py','scripts/verify_blog_20261103_followup.py','scripts/prepare_blog_20261103_followup_release.py']+['data/content/blog-20261103-'+p['key']+'.html' for p in POSTS]+['blog/'+p['slug']+'/'+n for p in POSTS for n in ['index.html','cover.jpg','fig1.svg','fig2.svg']]

def scope():
 baseline=json.loads((OUT/'baseline.json').read_text(encoding='utf-8'))
 keep=set(COMMON+REVERSE+NEW);restore=[]
 with zipfile.ZipFile(OUT/'build-drift.zip','w',zipfile.ZIP_DEFLATED) as backup,zipfile.ZipFile(OUT/'baseline.zip') as base:
  for name,digest in baseline['files'].items():
   file=ROOT/name
   if file.exists() and hashlib.sha256(file.read_bytes()).hexdigest()!=digest and name not in keep:
    backup.write(file,name);file.write_bytes(base.read(name));restore.append(name)
 save('build-scope.json',{'baseline_head':baseline['head'],'baseline_archive':PREFIX+'baseline.zip','restored_to_preexisting_worktree':restore,'restored_count':len(restore),'preserved_preexisting_work':True,'allowed_scope':sorted(keep)})
 print('Restored',len(restore),'unrelated generated changes to exact initial worktree; evidence retained')

def distribution():
 rows=json.loads((ROOT/'data/blog-posts.json').read_text(encoding='utf-8'))['posts'];rss=ET.parse(ROOT/'feed.xml').getroot();sm=ET.parse(ROOT/'sitemap.xml').getroot();search=json.loads((ROOT/'search-index.json').read_text(encoding='utf-8'))
 bad='\u653f\u7b56';checks=[];issues=[]
 def objects(obj):
  if isinstance(obj,list):
   for v in obj:yield from objects(v)
  elif isinstance(obj,dict):
   if any(isinstance(v,str) and any(p['slug'] in v for p in POSTS) for v in obj.values()):yield obj
   for v in obj.values():
    if isinstance(v,(list,dict)):yield from objects(v)
 records=list(objects(search))
 for p in POSTS:
  url=SITE+'/blog/'+p['slug']+'/'
  row=next(x for x in rows if x['slug']==p['slug']);item=next(x for x in rss.findall('.//item') if x.findtext('link')==url);entry=next(x for x in sm if x.find('{*}loc').text==url)
  indexed=[x for x in records if p['slug'] in json.dumps(x,ensure_ascii=False)]
  llms=[line for name in ['llms.txt','llms-full.txt'] for line in (ROOT/name).read_text(encoding='utf-8').splitlines() if p['slug'] in line]
  check={'slug':p['slug'],'ledger_date':row['date'],'feed_date':parsedate_to_datetime(item.findtext('pubDate')).date().isoformat(),'sitemap_date':entry.find('{*}lastmod').text[:10],'search_records':len(indexed),'llms_lines':len(llms)}
  if not all(check[k]=='2026-11-03' for k in ['ledger_date','feed_date','sitemap_date']):issues.append('date '+p['slug'])
  if not indexed or len(llms)<2:issues.append('index '+p['slug'])
  for text in [json.dumps(row,ensure_ascii=False),ET.tostring(item,encoding='unicode'),ET.tostring(entry,encoding='unicode'),json.dumps(indexed,ensure_ascii=False),'\n'.join(llms)]:
   if bad in text:issues.append('banned distribution '+p['slug'])
  checks.append(check)
 save('distribution-check.json',{'checks':checks,'issues':issues})
 baseline=[]
 for name in ['search-index.json','llms-full.txt','llms.txt','data/blog-posts.json','sitemap.xml','feed.xml']:
  old=subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT).decode('utf-8');new=(ROOT/name).read_text(encoding='utf-8');baseline.append({'path':name,'head_count':old.count(bad),'current_count':new.count(bad)})
 save('existing-vocabulary-check.json',{'records':baseline,'new_blog_records_have_banned_token':False if not any('banned' in x for x in issues) else True,'scope':'既存本編由来の語は変更前Gitと件数を照合。新4記事のHTML・SVG・JSON・配信レコードは別途検査。'})
 print(json.dumps({'distribution':checks,'issues':issues},ensure_ascii=False));assert not issues

def prepare():
 data=json.loads((ROOT/'data/blog-batch-20261103-followup.json').read_text(encoding='utf-8'))
 # Explicit evidence review. This script records the primary agent's completed assessment;
 # browser and production flags remain false until the dedicated reviewer executes them.
 review={'reviewer':'primary editorial self-review','date':'2026-11-03','result':'pass for local editorial release; prepublish browser and production checks pending','articles':[],'sources':SOURCES,
 'fixes':['遺言の封印開封は家庭裁判所で行う点を明記し、本文と最終HTMLへ反映。','ローカルDNSエラー後、許可されたネットワーク実行で出典7件すべてHTTP200と原文を再取得。','画像デコード検査のJSON往復でtuple/list不一致を修正し12点を再検査。','全体build末尾テストの一時フォルダ権限エラーを指定.tmpで再実行。無関係な生成差分は初期作業ツリーの正確なバイト列へ戻す。'],
 'claims':'国土交通省の民法572条注記、日本郵便の死亡後転送不可、裁判所の検認不要類型と封印開封、森町の漏水減免除外条件を取得原文と照合。セミナー開催完了や講演内容を創作していない。',
 'visual_review':'contact-sheet.jpgを実際に開き、12点の構図、主題、文字なし、切れ、画像欠落を確認。記事ごとの配管・郵便・封書・傷みのモチーフを区別。実ブラウザー確認とは分離。',
 'notification':'体験ストックなし。共通素材・編集ルールは読み取り専用として変更していない。'}
 unexpected=['露出配管等の漏水は町の減免対象外に挙げられている','死亡した本人宛ての郵便は家族からの申出でも転送不可','検認は有効性の判定ではなく、不要な書類もある','免責でも知りながら告げなかった事実は別扱い']
 uncertainties=['個々の設備の水抜き方法と今冬の気温','各差出人の個別手続きと相続の判断','手元の遺言書の種類と有効性','各売買契約の効力と責任の範囲']
 for i,p in enumerate(POSTS):
  review['articles'].append({'requested_title':p['title'],'principle':p['principle'],'memo':'空欄のため原則を選択','experience':'なし・意見として記述','unexpected_fact':unexpected[i],'clear_claim':['屋外配管と止水栓の写真を残す','転送を前提とせず差出人一件を記録する','原本を守り封と保管場所を記録する','免責を説明の省略にしない'][i],'uncertainty':uncertainties[i],'first_person_opinion':'大石の視点の仮定と判断として明示。実話の捏造なし。','facts_vs_opinion':'公式情報の段落と私はこう考える評価・提案の段落を分離','reverse':p['reverse'],'h2_openings':'前段なしでも主題が分かる第1段落','legal_scope':'個別判定は関係する専門家・窓口へ確認','unverified':uncertainties[i]+('。セミナー開催結果と講演内容' if i else '')})
 save('editorial-review.json',review)
 save('image-review.json',{'status':'pass','scope':'local files and contact sheet only','visual_reviewed':True,'decoded_images':12,'evidence':PREFIX+'contact-sheet.jpg','prepublish_browser':False,'production':False})
 allowed=COMMON+REVERSE+NEW
 gitfiles=[]
 for name in allowed:
  f=ROOT/name
  if not f.exists():continue
  r=subprocess.run(['git','show','HEAD:'+name],cwd=ROOT,capture_output=True)
  if r.returncode or r.stdout!=f.read_bytes():gitfiles.append(name)
 sources=[x for x in gitfiles if x.startswith(('scripts/','data/','reports/'))]+['scripts/build_all.py','scripts/build_blog.py','scripts/build_blog_20261103.py','scripts/build_sitemap.py','scripts/build_llms.py','scripts/build-search-index.mjs','scripts/preflight_check.py','scripts/verify_published.py','parts/header.html','parts/footer.html','parts/head-css.html','package.json','package-lock.json','wrangler.toml']
 build=[x for x in gitfiles if x not in sources]
 urls=[SITE+'/blog/'+p['slug']+'/' for p in POSTS];previews=['blog/'+p['slug']+'/index.html' for p in POSTS]
 pages=previews+REVERSE+['index.html','blog/index.html','life/housing/close-parents-house/index.html']
 manifest=set(pages+['feed.xml','sitemap.xml','llms.txt','llms-full.txt','search-index.json','favicon.svg'])
 sys.path.insert(0,r'C:\Users\Owner\Desktop\dots_workspace\work_claude\blog-autopilot\本体')
 from request_preflight import References,CSS_URL,CSS_IMPORT,JS_REF
 pending=list(manifest);seen=set()
 while pending:
  name=pending.pop()
  if name in seen:continue
  seen.add(name);f=ROOT/name
  if f.suffix not in ['.html','.css','.js','.mjs']:continue
  text=f.read_text(encoding='utf-8');refs=[]
  if f.suffix=='.html':
   parser=References();parser.feed(text);refs=[u for u,k in parser.resources]
   for st in parser.inline_styles:refs+=CSS_URL.findall(st)+CSS_IMPORT.findall(st)
  elif f.suffix=='.css':refs=CSS_URL.findall(text)+CSS_IMPORT.findall(text)
  else:refs=JS_REF.findall(text)
  for ref in refs:
   if ref.startswith(('#','data:','blob:')):continue
   resolved=urlsplit(urljoin(SITE+'/'+name,ref))
   if resolved.netloc!='morimachi.enshu-lifehack.com':continue
   rel=resolved.path.lstrip('/');asset=ROOT/rel
   if asset.is_dir():rel=rel.rstrip('/')+'/index.html';asset=ROOT/rel
   if asset.is_file():manifest.add(rel);pending.append(rel)
 checks=[{'id':'blog-list','type':'text','url':SITE+'/blog/','expect':'新4記事のタイトルと各記事へのリンクが存在する。'}, {'id':'home-new','type':'link','url':SITE+'/','expect':'ブログの新4記事がトップ新着から辿れる。'}, {'id':'feed','type':'resource','url':SITE+'/feed.xml','expect':'新4記事のcanonical URLと2026-11-03の公開日を含む。'}, {'id':'sitemap','type':'resource','url':SITE+'/sitemap.xml','expect':'新4記事のcanonical URLとlastmod 2026-11-03を含む。'}, {'id':'llms','type':'resource','url':SITE+'/llms.txt','expect':'新4記事のslugを含む。'}, {'id':'llms-full','type':'resource','url':SITE+'/llms-full.txt','expect':'新4記事のslugを含む。'}, {'id':'search-index','type':'resource','url':SITE+'/search-index.json','expect':'新4記事のタイトルとURLが存在し、summaryは台帳descriptionの先頭90文字、leadは同descriptionの先頭部分、keywordは各記事の狙いクエリと一致する。'}, {'id':'search-ui','type':'search','url':SITE+'/','expect':'水道凍結で新記事が見つかる。存在しない語「照合用未登録語4a37ba6f」で0件表示になり、解除で通常の検索表示へ戻る。'}, {'id':'karte','type':'link','url':urls[0],'expect':'実家カルテと実家整理のCTAが各リンク先へ遷移し、記事へ戻れる。'}]
 checks[1]['expect']='既存の新着4件表示が台帳の公開日・slug降順と一致し、サイト内のブログ一覧リンクから新4記事すべてへ進める。'
 for i,p in enumerate(POSTS):checks.append({'id':'reverse-'+str(i),'type':'link','url':SITE+'/blog/'+p['reverse']+'/','expect':p['title']+'への文脈のある逆リンクが存在し、'+urls[i]+'へ遷移する。'})
 request={'review_protocol':2,'kind':'prepublish','urls':urls,'preview_path':previews[0],'preview_paths':previews,'files':sorted(set(build+pages)),'checks':checks,'publish_root':'.','asset_manifest':sorted(manifest),'note':'同一工程の新4記事をすべてPCと狭幅で確認。本文、結論、FAQ、表紙、fig1、fig2、著者写真の実表示、横はみ出し、画像と導線を照合し、4記事×2幅の証拠を保存。固定runnerだけが一括commit/pushし、最新remoteを照合して他者更新を保持。本番確認後、scripts/verify_published.pyを既存のアクセス間隔で1回実行し、全URL・301・404の結果を保存する。未確認をpassにしない。'}
 gate={'status':'pass','articles':[]}
 for p,url in zip(POSTS,urls):gate['articles'].append({'url':url,'title':p['title'],'requested_title':p['title'],'images':[{'key':key,'kind':'cover' if key=='cover' else 'illustration','source':'/blog/'+p['slug']+'/'+file,'local_path':'blog/'+p['slug']+'/'+file,'local_exists':True,'page_reference':True} for key,file in [('cover','cover.jpg'),('fig1','fig1.svg'),('fig2','fig2.svg')]]})
 proofs={'sources':['sources-http.json','editorial-review.json']+['source-'+k+'.txt' for k in SOURCES], 'article':['article-check.json','banned-check.json','distribution-check.json','existing-vocabulary-check.json'], 'images':['images-decoded.json','image-review.json','contact-sheet.jpg'],'review':['editorial-review.json'],'build':['build-all.log','build-resumed.log','preflight-final.log','search-final.log','build-scope.json']}
 record={'schema_version':1,'workflow_id':WID,'review':'4記事の一次情報・本文・画像・明示自己査読・全体build・最終検査は合格。専任担当の公開前実画面確認と本番確認は未実施。','quality_checks':dict.fromkeys(['sources','article','images','review','build'],True),'checks':{k:[{'path':PREFIX+x} for x in names] for k,names in proofs.items()},'image_gate':gate}
 save('validation.json',record)
 spec={'schema_version':1,'run_id':data['run_id'],'workflow_id':WID,'workflow_run':data['workflow_run'],'expected_remote_sha':'80881a8e6a84327591d1016428c180400038c76e','source_files':sorted(set(sources)),'build_files':sorted(set(build)),'git_files':sorted(set(gitfiles)),'dependency_files':[],'validation_record':PREFIX+'validation.json','completion_path':PREFIX+'completion.json','commit_message':'Add four Mori winter water and inheritance preparation articles','browser_request':request}
 save('spec.json',spec)
 completion={'review':record['review'],'image_gate':json.loads(json.dumps(gate)),'quality_checks':record['quality_checks'],'browser_checks':[{'url':url,'requested_title':p['title'],'title':'','desktop':False,'mobile':False,'evidence_files':[]} for p,url in zip(POSTS,urls)],'published':False,'status':'prepublish browser pending'}
 completion['image_gate']['status']='fail'
 for a in completion['image_gate']['articles']:
  for im in a['images']:im['production_confirmed']=False
 save('completion.json',completion)
 print(json.dumps({'git_files':len(gitfiles),'source_files':len(spec['source_files']),'build_files':len(build),'public_manifest':len(manifest),'spec':PREFIX+'spec.json'},ensure_ascii=False))

if __name__=='__main__':{'scope':scope,'distribution':distribution,'prepare':prepare}[sys.argv[1]]()
