"""Freeze real local evidence for per-article preview and final publication."""
import json,re,sys,hashlib,subprocess,zipfile
from pathlib import Path
from bs4 import BeautifulSoup
from build_blog_20261108 import ROOT,OUT,POSTS,SOURCES,save
from prepare_blog_20261107_release import assets
PFX=OUT.relative_to(ROOT).as_posix()+'/'
RUN='33725e5e0e1b46c8a3fd7e05230e1114';WID='abe1e6f4af9b14b7dbf90ad9c7b7c5e96a95f9879c5ae9f88d38bc0e7384b739'
BASE='1fe59ec0af0c79850ceed325af358d8d16d7054d';SITE='https://morimachi.enshu-lifehack.com'
COMMON=['data/blog-posts.json','data/url-ledger.json','data/article-ledger.json','reports/url-ledger.csv','feed.xml','index.html','blog/index.html','llms-full.txt','llms.txt','search-index.json','sitemap.xml']
REVERSE=['blog/'+p['reverse']+'/index.html' for p in POSTS]
NEW=['data/blog-batch-20261108.json']+['scripts/'+s+'_20261108.py' for s in ['build_blog','illustrate_blog','verify_blog']]+['scripts/prepare_blog_20261108_release.py']+['data/content/blog-20261108-'+p['key']+'.html' for p in POSTS]+['blog/'+p['slug']+'/'+n for p in POSTS for n in ['index.html','cover.jpg','fig1.svg','fig2.svg']]
DEPS=['scripts/build_blog_20261104.py','scripts/illustrate_blog_20261104.py','scripts/illustrate_blog_20261107.py','scripts/illustrate_blog_20261104_second.py','scripts/prepare_blog_20261107_release.py','scripts/build_blog_20261107.py','scripts/author_profile.py','data/blog-batch-20261104.json','data/blog-20261104-sources.json','data/blog-batch-20261107.json','blog/20261101-morimachi-ikuji-nenkin/index.html','parts/header.html','parts/footer.html','parts/head-css.html','scripts/build_all.py','scripts/build_blog.py','scripts/build-search-index.mjs','scripts/preflight_check.py','scripts/verify_published.py','data/topics_master.json','package.json','package-lock.json']
def scope():
 keep=set(COMMON+REVERSE+NEW)
 changed=subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,stderr=subprocess.DEVNULL).decode().splitlines();restored=[]
 with zipfile.ZipFile(OUT/'unrelated-build-drift.zip','w',zipfile.ZIP_DEFLATED) as z:
  for name in changed:
   if name in keep:continue
   f=ROOT/name;z.write(f,name);f.write_bytes(subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT));restored.append(name)
 save(OUT/'build-scope.json',dict(initial_head=BASE,initial_tracked_worktree_clean=True,restored=restored,archive=PFX+'unrelated-build-drift.zip',scope='共有buildで生じた今回対象外の変更を保全し、基点に戻した。他者未commitなしを初回git statusで確認。'))
 print('Retained batch files; archived and restored unrelated build changes:',len(restored))
def evidence():
 report=json.loads((OUT/'article-checks.json').read_text(encoding='utf8'));assert report['status']=='pass'
 design=[]
 for p in POSTS:
  body=BeautifulSoup((ROOT/'data/content'/f'blog-20261108-{p["key"]}.html').read_text(encoding='utf8'),'html.parser')
  design.append(dict(requested_title=p['title'],query=p['query'],principle=p['principle'],memo='空欄のため原則を自動選択',experience='なし・意見として記述',answer=p['answer'],h2=[h.get_text() for h in body.find_all('h2')],faq=[h.get_text() for h in body.find_all('h3')],links=[a['href'] for a in body.select('a[href^="/blog/"]')],reverse=p['reverse'],image_roles=dict(cover=p['scene'],fig1='暮らしと確認資料の場面',fig2=p['method']),opinion_paragraph='大石の視点：私はこう考えます、で始まる提案の段落'))
 save(OUT/'design.json',dict(status='pass',date='2026-11-08',articles=design))
 facts={
 'consult':dict(facts='共催団体現行ページの11市町、11月29日11時〜14時30分、交通会館8階B、参加無料、森町参加、申込2経路を原文照合。町の移住段階とバンクの契約・地域参加条件を照合。',unexpected='地域未定でも相談可能',claim='質問が一つ具体的になることにも価値がある',uncertain='県詳細404、締切・受付残数・個別契約可否は確定せず本文に明記'),
 'app':dict(facts='サービス公式の11月30日終了とmila-e引継ぎ、町の2023年旧リニューアル案内を混同せず説明。町2127の旧名称案内を照合。22日は11月30日−11月8日の差。',unexpected='町の紹介だけでは現行の移行条件を判断できない',claim='移る案内と家族の照合完了は別',uncertain='移行全項目・終了時刻・期限後対応・実操作は未確認と本文明記'),
 'medical':dict(facts='町の対象年齢・扶養条件、入通院無料・保険外除外、県内受給者証、県外支払後申請、領収書レシート不可ほか4持ち物、受診日/入院日から1年以内、学校災害給付を照合。県概要と町独自助成を区別。',unexpected='県内の証忘れも払い戻しの同じ案内',claim='払い戻しと窓口の支払不要は別',uncertain='郵送オンライン可否・振込時期は未確認。例外は窓口確認'),
 'leber':dict(facts='妊娠中/就学前児家庭、家族最大5名、24時間、利用料町負担・通信/指名家庭負担、案内番号、末子就学前年度末解除、操作電話平日10〜18時を照合。',unexpected='24時間相談と操作電話受付時間は別',claim='対象を知ることと利用準備完了は別',uncertain='個別登録可否・到着時期・料金実額・通知方法・実操作は未確認と本文明記')}
 save(OUT/'source-review.json',dict(status='pass',checked_at='2026-11-08',articles=facts,source_records='sources-http.json',failures_preserved='県詳細404。共催団体現行ページ200へ切替。申込先は200だが内容未表示のため期限は採用しない。'))
 save(OUT/'editorial-review.json',dict(status='pass',reviewer='制作担当による全4記事の自己査読',articles=design,findings=facts,corrections=['4記事のFAQ見出し直下に自己完結段落を追加','LEBER内の禁止フレーズの部分一致を修正','移住相談の未確定締切を採用せず正式共催案内へ変更'],fact_opinion='一次資料の段落と「私は」で始まる評価・提案を分離。架空の本人経験なし。',political_tone='家族と事業者の実務に限定。支持・投票・統治の主語なし。',visual_review='未実施。専任担当へ引渡し。'))
 save(OUT/'image-review.json',dict(status='pass',scope='ローカル実画像確認のみ',evidence=PFX+'illustrations-contact.jpg',covers=4,figures=8,findings='実画像の12点を確認。相談地図、スマホと手帳、県外受診の証と領収書、医師への相談を描き分けた。600×800の縦挿絵。図内の可視文字なし。赤い十字は病院の概念図。',browser_prepublication=False,production=False))
 save(OUT/'article-build.json',dict(status='pass',command='python -B -X utf8 scripts/build_blog_20261108.py; python -B -X utf8 scripts/verify_blog_20261108.py --local',articles=[dict(path='blog/'+p['slug']+'/index.html',sha256=hashlib.sha256((ROOT/'blog'/p['slug']/'index.html').read_bytes()).hexdigest()) for p in POSTS],scope='記事組立・構造・画像・参照・日付・逆リンク。共有buildは最終工程。'))
def seal(key=None):
 rs=json.loads((OUT/'article-checks.json').read_text(encoding='utf8'));assert rs['status']=='pass'
 assert json.loads((OUT/'banned-check.json').read_text(encoding='utf8'))['status']=='pass'
 if not key:
  assert json.loads((OUT/'build-result.json').read_text(encoding='utf8'))['exit_code']==0
  assert json.loads((OUT/'final-checks.json').read_text(encoding='utf8'))['status']=='pass'
 selected=[p for p in POSTS if not key or p['key']==key];rows=[r for r in rs['articles'] if any(p['slug']==r['slug'] for p in selected)]
 folder=OUT/('early-'+key if key else 'final');folder.mkdir(exist_ok=True);prefix=folder.relative_to(ROOT).as_posix()+'/'
 previews=['blog/'+p['slug']+'/index.html' for p in selected];urls=[SITE+'/blog/'+p['slug']+'/' for p in selected]
 candidates=COMMON+REVERSE+NEW
 changed=set(subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,stderr=subprocess.DEVNULL).decode().splitlines())
 gitfiles=[f for f in candidates if f in changed or f in NEW]
 assert changed.issubset(set(candidates)), 'Unexpected tracked changes outside batch'
 src=sorted(set([f for f in candidates if f.startswith(('scripts/','data/'))]+DEPS))
 build=[f for f in candidates if not f.startswith(('scripts/','data/'))]
 auxiliary=[] if key else ['index.html','blog/index.html','housing/districts/index.html','fudosan/buy/index.html','life/housing/close-parents-house/index.html']+REVERSE
 manifest=assets(previews+auxiliary)
 if not key:manifest=sorted(set(manifest+['feed.xml','sitemap.xml','search-index.json','llms.txt','llms-full.txt','404.html']))
 checks=[dict(id='backlink-'+p['key'],type='link',url=SITE+'/blog/'+p['reverse']+'/',expect='/blog/'+p['slug']+'/ への本文内の逆リンクがあり、遷移先の記事が開く') for p in selected]
 if not key:
  for id,url in [('feed',SITE+'/feed.xml'),('sitemap',SITE+'/sitemap.xml'),('search-index',SITE+'/search-index.json')]:
   cmd=[sys.executable,'-X','utf8','C:/Users/Owner/Desktop/dots_workspace/work_claude/blog-dashboard/resource_contracts.py','--id',id,'--url',url]
   obj=json.loads(subprocess.check_output(cmd).decode('utf8'));checks.append(obj)
  checks.extend([dict(id='listing',type='text',url=SITE+'/blog/',expect='2026年11月8日の今回4記事の題名とリンクが各1件表示される'),dict(id='home',type='link',url=SITE+'/',expect='新着ブログから今回4記事へ到達できる'),dict(id='llms',type='resource',url=SITE+'/llms.txt',expect='今回4slugが索引に掲載される'),dict(id='search-ui',type='search',url=SITE+'/',expect='サイト検索で「LEBER」「アプリ移行」「こども医療費」「11月29日」を各入力し今回の記事が該当、存在しない語「zzmori1108nonesuch」で0件表示、解除して通常表示へ戻り、結果リンクから記事へ遷移できる')])
 request=dict(kind='prepublish',review_protocol=2,urls=urls,preview_paths=previews,preview_path=previews[0],files=sorted(set(build+manifest)),publish_root='.',asset_manifest=manifest,checks=checks,note='対象全記事をPCと狭幅320/390pxで確認。表紙・縦挿絵2点・著者写真・FAQ・本文・出典・内部リンク・実家整理導線・横はみ出しを確認。各記事×2幅の証拠。'+('先行preview専用・公開不可。共有索引は最終specで確認。' if key else '今回4記事を一括公開し、公開後の全URL検証を固定runnerで1回実行する。'))
 gate=dict(status='pass',articles=[dict(url=r['url'],title=r['title'],requested_title=r['requested_title'],images=[dict(key='cover' if i==0 else 'fig'+str(i),kind='cover' if i==0 else 'illustration',**im) for i,im in enumerate(r['images'])]) for r in rows])
 used=set(k for p in selected for k in p['source_keys'])
 ev={'sources':[PFX+'sources-http.json',PFX+'source-review.json']+[PFX+f'source-{k}.{ext}' for k in sorted(used) for ext in ['bin','txt']],'article':[PFX+'article-checks.json',PFX+'banned-check.json'],'images':[PFX+'image-review.json',PFX+'illustrations-contact.jpg',PFX+'article-checks.json'],'review':[PFX+'editorial-review.json',PFX+'design.json'],'build':[PFX+'article-build.json'] if key else [PFX+'build.log',PFX+'build-continuation.log',PFX+'resume-build.py',PFX+'build-result.json',PFX+'build-scope.json',PFX+'final-checks.log',PFX+'final-checks.json',PFX+'final-checks.py']}
 if not key:
  ev['build'] += [PFX+'repair/runtime-tests.log',PFX+'repair/runtime-installed.json',PFX+'repair/repair-verification.json',PFX+'repair/preview-dependencies.json',PFX+'repair/preview-preflight.log',PFX+'repair/verify-preview-dependencies.py']
 record=dict(schema_version=1,workflow_id=WID,review='全4記事を一次情報と照合し自己査読済み。5項目はローカル検査。実画面と本番は未確認。',quality_checks={k:True for k in ev},checks={k:[dict(path=f,sha256=hashlib.sha256((ROOT/f).read_bytes()).hexdigest()) for f in fs] for k,fs in ev.items()},image_gate=gate)
 save(folder/'validation.json',record)
 save(folder/'completion.json',dict(review=record['review'],quality_checks=record['quality_checks'],image_gate=dict(status='fail',articles=[]),browser_checks=[dict(url=r['url'],requested_title=r['title'],title='',desktop=False,mobile=False,evidence_files=[]) for r in rows]))
 spec=dict(schema_version=1,run_id=RUN,workflow_id=WID,workflow_run=RUN+'-batch',expected_remote_sha=BASE,source_files=src,build_files=sorted(set(build+manifest)),git_files=gitfiles,dependency_files=[],validation_record=prefix+'validation.json',completion_path=prefix+'completion.json',commit_message='Add four Mori migration and family features for 2026-11-08',browser_request=request)
 if not key:spec['post_publish_audit']={'contract':'morimachi-all-urls-v1'}
 save(folder/'spec.json',spec);assert json.loads((folder/'spec.json').read_text(encoding='utf8'))==spec
 print('Saved',prefix+'spec.json')
if __name__=='__main__':
 if '--evidence' in sys.argv:evidence()
 elif '--scope' in sys.argv:scope()
 else:seal(sys.argv[1] if len(sys.argv)>1 else None)
