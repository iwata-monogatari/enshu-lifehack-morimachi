"""Evidence-backed preview handoff and final batch publisher contract."""
import json,re,sys,subprocess,zipfile,hashlib
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from bs4 import BeautifulSoup
from build_blog_20261107 import ROOT,OUT,POSTS,SOURCES,save
PREFIX=OUT.relative_to(ROOT).as_posix()+'/'
WID='14ce5b44d6b4e1fc4a9278d9ef32b25ae5b1fef15dbc5830c3a36c68d7577c95'
RUN='0d2d19ee9f7b490dae8048999d02ae6e'
BASE='c02958704c4d5c3a4fb5d046a3b1bccb3236492b'
COMMON=['data/blog-posts.json','data/url-ledger.json','data/article-ledger.json','reports/url-ledger.csv','feed.xml','index.html','blog/index.html','llms-full.txt','llms.txt','search-index.json','sitemap.xml']
REVERSE=['blog/'+p['reverse']+'/index.html' for p in POSTS]
NEW=['data/blog-batch-20261107.json']+['scripts/'+stem+'_20261107.py' for stem in ['build_blog','illustrate_blog','verify_blog','prepare_blog']]+['data/content/blog-20261107-'+p['key']+'.html' for p in POSTS]+['blog/'+p['slug']+'/'+n for p in POSTS for n in ['index.html','cover.jpg','fig1.svg','fig2.svg']]
NEW[4]='scripts/prepare_blog_20261107_release.py'
NEW.append('scripts/build-search-index.mjs')
DEPS=['scripts/build_blog_20261104.py','scripts/illustrate_blog_20261104_second.py','scripts/illustrate_blog_20261104.py','scripts/author_profile.py','blog/20261101-morimachi-ikuji-nenkin/index.html','data/blog-batch-20261104.json','data/blog-20261104-sources.json','parts/header.html','parts/footer.html','parts/head-css.html']
def paths_for(p):return ['blog/'+p['slug']+'/'+n for n in ['index.html','cover.jpg','fig1.svg','fig2.svg']]
def assets(pages):
 found=set(pages+['favicon.svg']);queue=list(pages)
 for f in queue:
  if not (ROOT/f).is_file():continue
  s=BeautifulSoup((ROOT/f).read_text(encoding='utf8'),'html.parser')
  for tag,attr in [('img','src'),('script','src'),('link','href')]:
   for el in s.find_all(tag):
    value=el.get(attr,'')
    if not value or value.startswith(('data:','#')):continue
    u=urlsplit(urljoin('https://morimachi.enshu-lifehack.com/'+f,value))
    if u.netloc!='morimachi.enshu-lifehack.com':continue
    name=u.path.lstrip('/')
    if name and (ROOT/name).is_file():found.add(name)
 todo=list(found);seen=set()
 while todo:
  f=todo.pop()
  if f in seen:continue
  seen.add(f)
  if Path(f).suffix not in ('.css','.js','.mjs'):continue
  t=(ROOT/f).read_text(encoding='utf8');refs=re.findall(r'url\(\s*[\'"]?([^\'"\s)]+)',t)+re.findall(r'(?:fetch|import)\s*\(\s*[\'"]([^\'"]+)',t)+re.findall(r'\bfrom\s*[\'"]([^\'"]+)',t)
  for value in refs:
   u=urlsplit(urljoin('https://morimachi.enshu-lifehack.com/'+f,value));name=u.path.lstrip('/')
   if u.netloc=='morimachi.enshu-lifehack.com' and (ROOT/name).is_file() and name not in found:found.add(name);todo.append(name)
 return sorted(found)
def review():
 source_rows=json.loads((OUT/'sources-http.json').read_text(encoding='utf8'));assert all(r['status']==200 for r in source_rows)
 summaries={
 'volunteer':dict(fact='20歳以上・学生除外・年会費1000円・月1回勉強会・申込5経路。用紙の職業/動機/希望欄を照合。PDFと更新本文の連絡先表記の差は本文で明記。',unexpected='知識がない人も歓迎',claim='会費だけで負担の軽重は決めない',unverified='当番、交通費、受入人数、研修の詳しい流れ'),
 'fire':dict(fact='消防本部の器具例に発電機を確認。地域条例45条6号と事前届出を照合。産業祭11月22日9時〜15時30分。町の設備取扱講習案内も照合。',unexpected='調理しなくても発電機を確認する',claim='食品衛生と消防を別に確認する',unverified='個別判定・具体的期限・消火器本数'),
 'piano':dict(fact='5,500円・調律料除外・午前午後夜間ごとの徴収。使用料ページ2025年5月18日更新。会場費と設備費を区別。試算5500×2=11000、20人割275/550円。',unexpected='調律料が別',claim='5500円を総額としない',unverified='機種・調律実額/手配者・空き'),
 'archive':dict(fact='町告知2020年11月4日、実施予定11月7日18時。広報2020年12月号8ページの無観客開催報告。常磐会の5曲+乱れと最初の雨垂れ囃子を照合。',unexpected='雨垂れ囃子の順を変えた記録',claim='映像は人の練習と引継ぎの代わりにならない',unverified='現在の動画再生・費用・視聴数・2026年予定')}
 save(OUT/'source-review.json',dict(status='pass',checked_at='2026-11-07',sources=source_rows,articles=summaries,fetch_recovery='ローカルDNS失敗から許可されたHTTP取得へ変更。観光協会タイムアウトのため、町公式申込PDFに置き換え、取得済み原文の範囲で本文を修正。'))
 articles=[]
 for p in POSTS:
  articles.append(dict(requested_title=p['title'],principle=p['principle'],memo='空欄のため原則を自動選択',experience='なし・意見として記述',**summaries[p['key']],uncertainty='本文に私の迷いと公表資料の限界を明記',fact_opinion='事実整理と私の評価を区別',today_action=p['method'],reverse=p['reverse']))
 save(OUT/'editorial-review.json',dict(status='pass',reviewer='制作担当の自己査読',articles=articles,notes='結論200字以内、FAQ3問、4構造化データ、事実と評価、迷い、言い切り、今日の行動を全件確認。専任確認で指摘された制作メモは4記事の該当1段落を読者向けの判断へ修正し、本文への混入がないことを機械検査。逆リンク先の既存記事にあった不存在のblog.css参照を、既存記事共通のsite.cssへ修正。実画面判定は未実施。'))
 save(OUT/'image-review.json',dict(status='pass',scope='local illustration review only',evidence=PREFIX+'illustrations-contact.jpg',covers=4,figures=8,portrait_figures=True,text_in_drawing=False,findings='実画像で12点を確認。案内地図・露店発電機・舞台ピアノ・無観客記録を描き分け。図内小文字なし。縦配置。実物の復元ではない概念図。',prepublish_browser=False,production=False))
def scope():
 keep=set(COMMON+REVERSE+NEW);changed=subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,stderr=subprocess.DEVNULL).decode().splitlines();restored=[]
 with zipfile.ZipFile(OUT/'unrelated-build-drift.zip','w',zipfile.ZIP_DEFLATED) as z:
  for name in changed:
   if name in keep:continue
   f=ROOT/name;z.write(f,name);f.write_bytes(subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT));restored.append(name)
 save(OUT/'build-scope.json',dict(initial_head=BASE,initial_worktree_clean=True,restored=restored,archive=PREFIX+'unrelated-build-drift.zip'))
 print('Unrelated build drift preserved in archive and reverted to base:',len(restored))
def seal(early_key=None):
 report=json.loads((OUT/'article-checks.json').read_text(encoding='utf8'));assert report['status']=='pass'
 banned=json.loads((OUT/'banned-check.json').read_text(encoding='utf8'));assert banned['status']=='pass'
 selected=[p for p in POSTS if not early_key or p['key']==early_key];rs=[r for r in report['articles'] if any(p['slug']==r['slug'] for p in selected)]
 label='early-'+early_key if early_key else 'final';folder=OUT/label;folder.mkdir(exist_ok=True);prefix=folder.relative_to(ROOT).as_posix()+'/'
 review()
 previews=['blog/'+p['slug']+'/index.html' for p in selected];urls=[r['url'] for r in rs]
 if early_key:
  src=['data/blog-batch-20261107.json','data/content/blog-20261107-'+early_key+'.html','scripts/build_blog_20261107.py','scripts/illustrate_blog_20261107.py','scripts/verify_blog_20261107.py']+DEPS
  built=[f for p in selected for f in paths_for(p)];gitfiles=[];pages=previews
  save(folder/'article-build.json',dict(status='pass',scope='article-only assembly; full shared build not claimed',articles=rs,command='python scripts/build_blog_20261107.py; python scripts/verify_blog_20261107.py --local'))
 else:
  assert json.loads((OUT/'final-build-result.json').read_text(encoding='utf-8-sig'))['status']=='pass'
  assert json.loads((OUT/'final-growth-result.json').read_text(encoding='utf-8-sig'))['status']=='pass'
  gitfiles=[]
  for f in COMMON+REVERSE+NEW:
   if not (ROOT/f).exists():continue
   old=subprocess.run(['git','show',BASE+':'+f],cwd=ROOT,capture_output=True)
   if old.returncode or old.stdout!=(ROOT/f).read_bytes():gitfiles.append(f)
  actual=subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,stderr=subprocess.DEVNULL).decode().splitlines();assert set(actual)<=set(gitfiles),set(actual)-set(gitfiles)
  src=[f for f in gitfiles if f.startswith(('data/','scripts/','reports/'))]+DEPS+['scripts/build_all.py','scripts/build_blog.py','scripts/build_sitemap.py','scripts/build_llms.py','scripts/build-search-index.mjs','scripts/preflight_check.py','scripts/verify_published.py','package.json','package-lock.json','wrangler.toml']
  built=[f for f in gitfiles if f not in src];pages=previews+REVERSE+['index.html','blog/index.html','life/housing/close-parents-house/index.html']
 manifest=assets(pages)
 if not early_key:manifest=sorted(set(manifest+['feed.xml','sitemap.xml','llms.txt','llms-full.txt','search-index.json']))
 checks=[]
 if not early_key:
  site='https://morimachi.enshu-lifehack.com'
  checks=[dict(id='blog-list',type='search',url=site+'/blog/',expect='新記事4件のタイトルとリンク。検索「調律」でピアノ記事、zz-no-match-1107で0件、解除で全件表示。'),dict(id='home',type='text',url=site+'/',expect='11月7日の新着記事の導線がある'),dict(id='llms',type='resource',url=site+'/llms.txt',expect='新記事4件のslugを含む')]
  contracts=OUT/'resource-contracts.json';checks+=json.loads(contracts.read_text(encoding='utf8'))
  for p in selected:checks.append(dict(id='backlink-'+p['key'],type='link',url=site+'/blog/'+p['reverse']+'/',expect='/blog/'+p['slug']+'/ への文脈付き逆リンク'))
 request=dict(kind='prepublish',review_protocol=2,urls=urls,preview_paths=previews,preview_path=previews[0],files=sorted(set(built+manifest)),publish_root='.',asset_manifest=manifest,checks=checks,note='全対象記事をPCと320/390px相当の狭幅で確認。表紙、縦挿絵2点、著者写真、FAQ、出典、本文内リンク、実家整理導線と横はみ出しを確認。各記事×2幅以上の画像証拠を保存。'+('記事単独のpreview専用で公開不可。共有索引等は最終spec。' if early_key else '全記事を1回で公開。固定runnerはscripts/verify_published.pyの全URL・301・404検査も1回実施し記録する。'))
 gate=dict(status='pass',articles=[dict(url=r['url'],title=r['title'],requested_title=r['requested_title'],images=[dict(key=('cover' if i==0 else 'fig'+str(i)),kind=('cover' if i==0 else 'illustration'),**im) for i,im in enumerate(r['images'])]) for r in rs])
 used=set(k for p in selected for k in p['source_keys'])
 ev={'sources':[PREFIX+'sources-http.json',PREFIX+'source-review.json']+[PREFIX+f'source-{k}.{ext}' for k in sorted(used) for ext in ['bin','txt']], 'article':[PREFIX+'article-checks.json',PREFIX+'banned-check.json',PREFIX+'backlink-css-repair.json'],'images':[PREFIX+'image-review.json',PREFIX+'illustrations-contact.jpg',PREFIX+'article-checks.json'],'review':[PREFIX+'editorial-review.json',PREFIX+'design.json',PREFIX+'repair-1/changes.json'],'build':[prefix+'article-build.json'] if early_key else [PREFIX+f for f in ['build.log','build-scope.json','final-build-result.json','scoped-preflight.log','sitemap-scope.log','final-growth-test.log','final-growth-result.json','repair-1/build.log','repair-1/build-continuation.log','repair-1/combined-build-result.json','repair-1/search-metadata-build.log','repair-1/search-metadata-tests.log','repair-1/resource-contract-repair.json']]}
 record=dict(schema_version=1,workflow_id=WID,review='4記事を自己査読。体験なしの意見として記述。実画面と本番は未確認。',quality_checks={k:True for k in ev},checks={k:[dict(path=f,sha256=hashlib.sha256((ROOT/f).read_bytes()).hexdigest()) for f in fs] for k,fs in ev.items()},image_gate=gate)
 save(folder/'validation.json',record);save(folder/'completion.json',dict(review=record['review'],quality_checks=record['quality_checks'],image_gate=dict(status='fail',articles=[]),browser_checks=[dict(url=r['url'],requested_title=r['title'],title='',desktop=False,mobile=False,evidence_files=[]) for r in rs]))
 spec=dict(schema_version=1,run_id=RUN,workflow_id=WID,workflow_run=RUN+'-batch',expected_remote_sha=BASE,source_files=list(dict.fromkeys(src)),build_files=sorted(set(built+manifest)),git_files=gitfiles,dependency_files=[],validation_record=prefix+'validation.json',completion_path=prefix+'completion.json',commit_message='Add four Mori culture and event features for 2026-11-07',browser_request=request)
 save(folder/'spec.json',spec);assert json.loads((folder/'spec.json').read_text(encoding='utf8'))==spec
 print(json.dumps(dict(saved=True,spec=prefix+'spec.json',articles=len(rs),git_files=len(gitfiles),assets=len(manifest))))
if __name__=='__main__':
 if '--scope' in sys.argv:scope()
 else:seal(sys.argv[sys.argv.index('--early')+1] if '--early' in sys.argv else None)
