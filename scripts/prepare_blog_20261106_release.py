"""Keep this release scoped; seal executed evidence for the fixed runner."""
import json,re,subprocess,hashlib,zipfile,sys,os
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from bs4 import BeautifulSoup
from build_blog_20261106 import ROOT,OUT,POSTS,SOURCES,save
PREFIX='test-results/dedicated-publish/'
COMMON=['data/blog-posts.json','data/url-ledger.json','data/article-ledger.json','reports/url-ledger.csv','feed.xml','index.html','blog/index.html','llms-full.txt','llms.txt','search-index.json','sitemap.xml']
REVERSE=['blog/'+p['reverse']+'/index.html' for p in POSTS]
NEW=['data/blog-batch-20261106.json','scripts/build_blog_20261106.py','scripts/illustrate_blog_20261106.py','scripts/verify_blog_20261106.py','scripts/prepare_blog_20261106_release.py']+['data/content/blog-20261106-'+p['key']+'.html' for p in POSTS]+['blog/'+p['slug']+'/'+n for p in POSTS for n in ['index.html','cover.jpg','fig1.svg','fig2.svg']]
def scope():
 keep=set(COMMON+REVERSE+NEW);restored=[]
 files=subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,stderr=subprocess.DEVNULL).decode().splitlines()
 with zipfile.ZipFile(OUT/'unrelated-build-drift.zip','w',zipfile.ZIP_DEFLATED) as z:
  for name in files:
   if name in keep:continue
   f=ROOT/name;old=subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT)
   z.write(f,name);f.write_bytes(old);restored.append(name)
 save(OUT/'build-scope.json',dict(initial_head='aad1ee2bf713330aaeccf0dc65e8e7ea11bbe3b9',initial_worktree_clean=True,restored=restored,archive=PREFIX+'unrelated-build-drift.zip',scope='Only this batch plus four contextual backlinks and required shared outputs retained'))
 print('Restored unrelated build drift:',len(restored))

def seal():
 checkpoint=Path('C:/Users/Owner/Desktop/dots_workspace/work_claude/blog-autopilot/.tmp/publication-progress/6f81b3103bd8d83e55bdccfaa4d0eb37b1629b384c7f057fcd4f4f5d86d6898b.json')
 cp=json.loads(checkpoint.read_text(encoding='utf8'));wid=cp['workflow_id'];run=cp['run']
 report=json.loads((OUT/'article-checks.json').read_text(encoding='utf8'))
 assert report['status']=='pass'
 assert json.loads((OUT/'banned-check.json').read_text(encoding='utf8'))['status']=='pass'
 assert all(r['status']==200 for r in json.loads((OUT/'sources-http.json').read_text(encoding='utf8')))
 review=dict(status='pass',reviewer='制作担当による公開前自己査読',checked_at='2026-11-06',scope='4 articles; editorial and local image review; browser and production not yet performed',articles=[],fixes=['ローカルネットワークのDNSエラーは許可された公式サイト読取りで復旧。8出典HTTP200と原文を保存。','全体build末尾の回遊テストで一時フォルダー権限エラー。指定.tmpで同テストを再実行し3件合格。','無関係なbuild生成差分を保存して初期の正確なバイト列へ戻し、今回の導線と共通索引だけを保持。'])
 unexpected=['同額のみかんきっぷは森町を含まない','同じ駅でも上下ホームで入口の条件が違う','対策箇所図には防犯上の非公表理由がある','予約しても混雑で輪行を断られる場合がある']
 unverified=['個別行程の普通運賃、購入時の年齢区分や精算条件','当日の介助体制、個別車種の利用可否、現地の最新状況','2026年度の個別箇所の整備進捗と現在の担当体制','現在の貸出実施、在庫、個別車種、保証料の最新運用']
 for i,p in enumerate(POSTS):
  review['articles'].append(dict(requested_title=p['title'],principle=p['principle'],memo='空欄のため原則を自動選択',experience='なし・意見として記述',unexpected_fact=unexpected[i],clear_claim=['券の価格より先に使う区間を選ぶ','5駅を一律に使えるとは言わない','地図がないことを未点検と決めつけない','無料より先に車種・有人駅・返却時刻を確認'][i],uncertainty='本文の「私は」に始まる段落で自分の迷いを明示',facts_vs_opinion='資料の記述と私の評価・提案を段落で分離',h2='最初の段落を前段から独立',reverse=p['reverse'],unverified=unverified[i],today_action=['乗降駅を一枚に書く','往復の駅と候補列車を揃える','一箇所を公開しない相談メモに書く','車種と帰りの列車を伝えて問い合わせる'][i]))
 save(OUT/'editorial-review.json',review)
 save(OUT/'image-review.json',dict(status='pass',scope='local only',visual_reviewed=True,evidence=PREFIX+'illustrations-contact.jpg',covers=4,figures=8,findings='8構図を実画像で確認。券と地図、車いすとスロープ、通学路と相談メモ、前輪と返却時計を描き分け。切れ・参照切れなし。現地設備の復元図ではない。',prepublish_browser=False,production=False))
 gitfiles=[]
 for name in COMMON+REVERSE+NEW:
  f=ROOT/name
  if not f.exists():continue
  r=subprocess.run(['git','show','HEAD:'+name],cwd=ROOT,capture_output=True)
  if r.returncode or r.stdout!=f.read_bytes():gitfiles.append(name)
 actual=subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,stderr=subprocess.DEVNULL).decode().splitlines()
 assert set(actual)<=set(gitfiles),(set(actual)-set(gitfiles))
 src=[f for f in gitfiles if f.startswith(('data/','scripts/','reports/'))]
 src+=['scripts/build_all.py','scripts/build_blog.py','scripts/build_blog_20261104.py','scripts/illustrate_blog_20261104_second.py','scripts/author_profile.py','scripts/build_sitemap.py','scripts/build_llms.py','scripts/build-search-index.mjs','scripts/preflight_check.py','scripts/verify_published.py','parts/header.html','parts/footer.html','parts/head-css.html','package.json','package-lock.json','wrangler.toml']
 build=[f for f in gitfiles if f not in src];urls=[r['url'] for r in report['articles']];previews=['blog/'+p['slug']+'/index.html' for p in POSTS]
 pages=previews+REVERSE+['index.html','blog/index.html','life/housing/close-parents-house/index.html']
 assets=set(pages+['feed.xml','sitemap.xml','llms.txt','llms-full.txt','search-index.json','favicon.svg'])
 queue=list(pages);seen=set()
 while queue:
  f=queue.pop()
  if f in seen:continue
  seen.add(f);s=BeautifulSoup((ROOT/f).read_text(encoding='utf8'),'html.parser')
  for tag,attr in [('img','src'),('script','src'),('link','href')]:
   for el in s.find_all(tag):
    value=el.get(attr,'')
    if not value or value.startswith(('data:','http:','https:','//','#')):continue
    path=urlsplit(urljoin('/'+f,value)).path.lstrip('/')
    if path and (ROOT/path).is_file():assets.add(path)
 # Include dependencies referenced by stylesheets/scripts, not only HTML tags.
 queue=list(assets);seen_assets=set()
 while queue:
  f=queue.pop()
  if f in seen_assets:continue
  seen_assets.add(f)
  if Path(f).suffix not in ('.css','.js','.mjs'):continue
  text=(ROOT/f).read_text(encoding='utf8')
  refs=re.findall(r'url\(\s*[\'"]?([^\'"\s)]+)',text)
  refs+=re.findall(r'(?:fetch|import)\s*\(\s*[\'"]([^\'"]+)',text)
  refs+=re.findall(r'\bfrom\s*[\'"]([^\'"]+)',text)
  for value in refs:
   u=urlsplit(urljoin('https://morimachi.enshu-lifehack.com/'+f,value))
   if u.netloc!='morimachi.enshu-lifehack.com':continue
   name=u.path.lstrip('/')
   if (ROOT/name).is_file() and name not in assets:assets.add(name);queue.append(name)
 manifest=sorted(assets)
 checks=[dict(id='blog-list',type='text',url='https://morimachi.enshu-lifehack.com/blog/',expect='新記事4件のタイトルと記事リンク。検索で「輪行」を入力すると該当記事、存在しない文字列「zz-no-match-1106」で0件、解除で全件表示。'),dict(id='home',type='text',url='https://morimachi.enshu-lifehack.com/',expect='新着ブログから2026年11月6日の記事へ進める'),dict(id='feed',type='resource',url='https://morimachi.enshu-lifehack.com/feed.xml',expect='4 slug: '+', '.join(p['slug'] for p in POSTS)),dict(id='sitemap',type='resource',url='https://morimachi.enshu-lifehack.com/sitemap.xml',expect='4記事の正規URLと2026-11-06のlastmod'),dict(id='llms',type='resource',url='https://morimachi.enshu-lifehack.com/llms.txt',expect='新記事4件のURLを含む'),dict(id='search',type='resource',url='https://morimachi.enshu-lifehack.com/search-index.json',expect='新記事4件のslugを含む')]
 for p in POSTS:checks.append(dict(id='backlink-'+p['key'],type='link',url='https://morimachi.enshu-lifehack.com/blog/'+p['reverse']+'/',expect='/blog/'+p['slug']+'/ への文脈付き逆リンク'))
 request=dict(kind='prepublish',review_protocol=2,urls=urls,preview_path=previews[0],preview_paths=previews,files=sorted(set(build+manifest)),publish_root='.',asset_manifest=manifest,checks=checks,note='4記事全件のPC・狭幅、本文、表紙とfig1/fig2と著者写真、横はみ出し、FAQ・出典・内部リンク・実家整理導線を確認。各記事×2幅の画像証拠を保存。非公開のtest-results/data/scriptsは配信しない。固定runnerは同一バッチを1回で公開し、全URL・301・404をscripts/verify_published.pyで1回検査し記録する。')
 gate=dict(status='pass',articles=[])
 for r in report['articles']:
  gate['articles'].append(dict(url=r['url'],title=r['title'],requested_title=r['requested_title'],images=[dict(key=('cover' if i==0 else 'fig'+str(i)),kind=('cover' if i==0 else 'illustration'),**im) for i,im in enumerate(r['images'])]))
 evidence={'sources':['sources-http.json','source-review.json']+[f'source-{k}.{ext}' for k in SOURCES for ext in ['bin','txt']],'article':['article-checks.json','banned-check.json'],'images':['image-review.json','article-checks.json','illustrations-contact.jpg'],'review':['editorial-review.json','design.json'],'build':['build.log','growth-test.log','build-continuation.log','build-scope.json']}
 record=dict(schema_version=1,workflow_id=wid,review='制作担当の自己査読合格。4記事とも事実と意見を分離し、意外な事実・言い切り・迷い・今日の行動を確認。体験なし。実ブラウザーと本番は専任担当へ引渡し、未実施を合格にしていない。',quality_checks={k:True for k in evidence},checks={k:[dict(path=PREFIX+f) for f in fs] for k,fs in evidence.items()},image_gate=gate)
 save(OUT/'validation.json',record)
 save(OUT/'completion.json',dict(review=record['review'],image_gate=dict(status='fail',articles=[]),quality_checks=record['quality_checks'],browser_checks=[dict(url=r['url'],requested_title=r['title'],title='',desktop=False,mobile=False,evidence_files=[]) for r in report['articles']]))
 spec=dict(schema_version=1,run_id='58f685727f50459aa85f3de7e511be92',workflow_id=wid,workflow_run=run,expected_remote_sha='aad1ee2bf713330aaeccf0dc65e8e7ea11bbe3b9',source_files=list(dict.fromkeys(src)),build_files=list(dict.fromkeys(build+manifest)),git_files=gitfiles,dependency_files=[],validation_record=PREFIX+'validation.json',completion_path=PREFIX+'completion.json',commit_message='Add four Mori Friday transport features for 2026-11-06',browser_request=request)
 save(OUT/'spec.json',spec)
 assert json.loads((OUT/'spec.json').read_text(encoding='utf8'))==spec
 print(json.dumps(dict(saved=True,articles=4,git_files=len(gitfiles),source_files=len(src),build_files=len(spec['build_files']),assets=len(manifest)),ensure_ascii=False))
if __name__=='__main__':scope() if '--scope' in sys.argv else seal()
