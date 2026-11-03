"""Render the approved follow-up batch; public release is owned by the fixed runner."""
from pathlib import Path
import json,re,html,sys,hashlib,subprocess,zipfile
import fitz
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'test-results/dedicated-publish/4a37ba6f'
SITE='https://morimachi.enshu-lifehack.com'
DATE='2026-11-03'
TOWN='https://www.town.morimachi.shizuoka.jp/'
SOURCES={
 'cold':['浜松市：水道管の凍結にご注意ください','https://www.city.hamamatsu.shizuoka.jp/service/suidou/mame/touketu.html'],
 'leak':['森町：漏水のみつけ方と水道料金の減免について',TOWN+'gyosei/machinososhiki/jogesuidoka/josuidokanrigakari/1/1/669.html'],
 'bank':['森町：空き家・空き地バンク',TOWN+'gyosei/machinososhiki/teijusuishinka/ijukoryugakari/2/2/379.html'],
 'seminar':['森町：我が家の終活セミナー開催',TOWN+'gyosei/machinososhiki/teijusuishinka/ijukoryugakari/2/7028.html'],
 'mail':['日本郵便：死亡した受取人あての郵便物等の転送','https://www.post.japanpost.jp/question/107.html'],
 'court':['裁判所：遺言書の検認','https://www.courts.go.jp/saiban/syurui/syurui_kazi/kazi_06_17/index.html'],
 'qa':['国土交通省：建物状況調査に関するQ＆A（令和6年4月1日現在）','https://www.mlit.go.jp/tochi_fudousan_kensetsugyo/const/content/001735111.pdf']}
POSTS=[
 dict(key='freeze',slug='20261103-morimachi-akiya-suido-toketsu',title='空き家の水道凍結｜森町の実家で冬前に確認',query='空き家 水道 凍結防止',principle=1,intent='do',reverse='20261027-morimachi-akiya-kanri-itaku',sources=['cold','leak','bank'],
 description='空き家の水道凍結は、冬前に屋外配管と止水栓を確かめる準備から始めます。保温材の状態、給湯器の説明書、漏水時の連絡担当を整理。森町の漏水減免には露出配管などの除外条件があります。通う家族の移動負担を増やさず、次の訪問で写真を残す順番を紹介します。',
 question='森町の空き家の水道は、冬前に何を見ればいい？',answer='屋外配管の露出や保温材の状態、止水栓の位置を、安全に見える範囲で確認します。写真と連絡担当を残し、水抜きや給湯器の扱いは設備の説明書や工事事業者へ確認してください。森町の漏水減免には対象外の条件があり、凍結後に必ず適用されるわけではありません。',
 faq=[['保温材を巻けば、空き家の凍結を必ず防げますか？','必ず防げるとは言えません。浜松市は、風の強い戸外や日陰、露出配管への注意と、保温材を濡らさない方法を案内しています。家ごとの配管や給湯器の状態は別に確認してください。写真に点検日を付け、分からない設備は説明書や工事事業者へ相談します。家族が危険な場所へ入ってまで点検する必要はありません。'],['水が出ないとき、熱湯をかけてもよいですか？','熱湯は避けてください。浜松市の案内は、自然に解けるのを待つか、布をかぶせてぬるま湯でゆっくり解かす方法を示しています。水が出ない原因を凍結と決めつけず、設備の扱いが不明なら工事事業者へ相談します。漏水が疑われる場合に備え、止水栓の場所と連絡先を先に記録しておくと引継ぎに使えます。'],['凍結による漏水なら水道料金は減免されますか？','森町では個別の条件確認が必要です。町の案内は、露出配管や給湯器等の故障による漏水などを対象外に挙げています。凍結という原因だけで減免を約束できません。修理前後の写真や工事事業者の説明を残し、申請の要否と必要書類を上下水道課へ確認してください。修理費と水道料金の扱いも分けて相談します。']]),
 dict(key='postmail',slug='20261103-morimachi-oyano-yubin',title='亡くなった親の郵便転送｜森町の実家整理',query='亡くなった親 郵便 転送',principle=1,intent='know',reverse='20260817-heir-representative-tax-notice',sources=['mail','seminar','bank'],
 description='亡くなった親宛ての郵便物は、家族からの申出でも転送できないと日本郵便が案内しています。森町の実家を整理する家族へ、差出人の一覧、届出の確認、原本の保管を分ける順番を紹介。固定資産税の通知やオンライン契約も別に確かめ、今日の封筒一通から連絡先を整理します。',
 question='亡くなった親の郵便を、家族の家へ転送できる？',answer='日本郵便は、死亡した本人宛ての郵便物等は家族からの申出でも転送できず、差出人へ返還されると案内しています。転送を前提にせず、差出人ごとに死亡後の届出と今後の連絡方法を確認してください。郵便の扱いと、契約・相続の判断は分けます。',
 faq=[['家族が転居届を出せば、亡くなった親の郵便を受け取れますか？','日本郵便の公式FAQでは、死亡した本人宛ての郵便物等は、ご家族からの申出でも転送できず差出人へ返還されるとされています。親の名前で転居届を出せば済むとは考えないでください。差出人の正式名称を控え、死亡後の届出方法、申請できる人、必要書類、今後の連絡先をそれぞれの公式窓口へ確認します。'],['役所へ死亡届を出したら、契約先への連絡も終わりますか？','役所の届出と、契約先や差出人ごとの手続きを同じものとは扱わないでください。必要な連絡や書類は窓口ごとに確認します。差出人、連絡日、必要書類、回答待ちか完了かを表に残すと、家族の引継ぎに使えます。固定資産税の通知先についても町の担当窓口へ確認し、相続登記や契約の判断とは区別します。'],['実家で見つけた請求書は、すぐ払うべきですか？','本稿では個別の支払義務を判定できません。差出人、契約内容、期限を確認し、相続の方針も含めて専門家や担当窓口へ相談してください。相続放棄などを検討している場合も、家族だけで処分や支払いを決めないようにします。原本を保管し、問い合わせた事実と回答内容を残してから、次の対応を確かめてください。']]),
 dict(key='kennin',slug='20261103-morimachi-yuigon-kennin',title='遺言書の検認は必要？森町の実家で発見したら',query='遺言書 検認 必要',principle=5,intent='compare',reverse='20260714-clean-parents-house',sources=['court','seminar','bank'],
 description='遺言書の検認は、書類の種類と保管方法を分けて確認します。公正証書遺言と法務局保管の自筆証書遺言に関する遺言書情報証明書は検認不要です。森町の実家で書類を見つけた家族へ、封と保管場所の記録、原本の扱い、相談前の準備を整理。家の結論を急がず次の確認につなげます。',
 question='実家で遺言書が見つかったら、必ず検認が必要？',answer='遺言書は種類と保管方法によって検認の要否が異なります。裁判所の案内では、公正証書遺言と法務局保管の自筆証書遺言に関する遺言書情報証明書は検認不要です。封のある書類は開封前に扱いを確認してください。検認は遺言の有効・無効を判断する手続きではありません。',
 faq=[['自宅で見つけた封のある遺言書は、家族で開けてよいですか？','開封する前に、家庭裁判所や専門家へ扱いを確認してください。封のある書類を片付けの勢いで開けたり、原本へ書き込んだりしないことを勧めます。発見日、発見場所、保管している人を別紙に記録します。すでに開けた場合も、家族だけで有効性を決めず、開封した事実を伝えて以後の手続きを相談してください。'],['検認が済めば、遺言書が有効だと確定しますか？','確定する手続きではありません。裁判所は、検認を遺言書の形状や訂正、日付、署名などを明確にし、偽造・変造を防ぐ手続きと説明しています。遺言の有効・無効や、家を誰が継ぐかの個別判断とは分けてください。検認後の登記や契約で必要な資料、家族間の確認については、担当する専門家へ相談します。'],['法務局に預けた自筆証書遺言も検認が必要ですか？','裁判所の案内では、法務局で保管されている自筆証書遺言に関して交付される遺言書情報証明書は検認不要です。公正証書遺言も検認不要とされています。ただし、手元の紙がどの書類か分からない場合は自己判断しないでください。保管に関する通知や書類名を確認し、法務局や専門家へ必要な手続きを尋ねます。']]),
 dict(key='defects',slug='20261103-morimachi-keiyaku-menseki',title='契約不適合責任の免責｜森町の実家売却前に',query='中古住宅 売却 契約不適合責任 免責',principle=5,intent='know',reverse='20260922-morimachi-jikka-tatemono-chosa',sources=['qa','seminar','bank'],
 description='契約不適合責任の免責は、不具合の説明を省くための約束ではありません。森町の実家を売る家族へ、知っている症状、修理の資料、未確認の場所を分ける準備を紹介します。建物状況調査と契約条件の違いも整理。今日の不具合一件を記録し、個別の条項は専門家へ確認します。',
 question='古い実家は免責で売れば、不具合を説明しなくていい？',answer='免責の特約があっても、知りながら告げなかった事実について責任を逃れられない旨を国土交通省が案内しています。古い家だから説明不要とは考えず、既知の症状、修理資料、未確認部分を整理してください。個別の免責条項の効力や責任の範囲は専門家へ確認します。',
 faq=[['免責の特約があれば、雨漏りを伝えなくてもよいですか？','そうとは考えないでください。国土交通省のQ＆Aは、責任を負わない特約があっても、知りながら告げなかった事実について責任を逃れられない旨を示しています。雨漏りなど知っている症状は記録し、仲介会社へ伝えます。告知書や契約案への記載、個別の条項の効力と責任の範囲は、専門家へ確認してください。'],['相続した家で、親が行った修理の内容が分からない場合は？','分からないことを推測で埋めないでください。家族が見た症状と、工事書類に記載された内容、未確認の範囲を分けます。依頼先の記憶があれば照会の材料として残し、書類の有無も仲介会社へ伝えます。修理した記憶だけで現在も不具合がないとは説明せず、追加調査の範囲や必要な資料を担当者へ相談します。'],['建物状況調査をすれば、売主の説明や責任はなくなりますか？','調査の実施と、契約で何を約束するかは別に確認します。調査を頼んだから既知の不具合の説明が不要になるとは考えません。手元の修理資料や症状の記録を調査担当者と仲介会社へ渡し、結果と契約案を照合してください。調査で分からなかった部分や、個別の責任の範囲については専門家へ相談します。']])]

def save(name,obj):
 p=OUT/name;p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');assert json.loads(p.read_text(encoding='utf-8'))==obj

def snapshot():
 OUT.mkdir(parents=True,exist_ok=True)
 if (OUT/'baseline.zip').exists():return
 names=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
 records={}
 with zipfile.ZipFile(OUT/'baseline.zip','w',zipfile.ZIP_DEFLATED) as z:
  for name in names:
   p=ROOT/name
   if name and p.is_file():z.write(p,name);records[name]=hashlib.sha256(p.read_bytes()).hexdigest()
 save('baseline.json',{'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'files':records})
 print('Preserved baseline',len(records),'tracked files')

def figure(i,n):
 # Text-free original vector scenes. Distinct motifs per article and per scene.
 from build_blog_20261103 import house,person,paper
 bg='<rect width="1000" height="560" fill="#eef4ec"/><circle cx="850" cy="90" r="42" fill="#f2d8a2"/><path d="M0 270L170 95 340 255 550 100 770 250 920 155 1000 240V560H0Z" fill="#b2c6b3"/><path d="M0 345Q230 230 480 325T1000 285V560H0Z" fill="#8fae86"/><path d="M0 450Q240 350 490 445T1000 390V560H0Z" fill="#d0d9aa"/><path d="M0 488Q240 418 460 495T1000 455" stroke="#e9eedb" stroke-width="23" fill="none"/>'
 if n==1:bg+=house(640,240,.85)+person(395,355)
 else:bg+=house(80,240,.65)+person(790,355,'#6d8996')+'<path d="M350 450Q520 375 700 440" stroke="#f7ead2" stroke-width="60" fill="none"/>'
 if i==0:
  if n==1:
   bg+='<path d="M705 430v-85h-55" fill="none" stroke="#668d9e" stroke-width="19"/><path d="M704 417v-66" stroke="#ede0bb" stroke-width="30"/><path d="M684 367h40m-40 15h40m-40 15h40" stroke="#a99c7a" stroke-width="4"/><rect x="455" y="290" width="75" height="112" rx="12" fill="#365554"/><rect x="463" y="303" width="59" height="78" fill="#e2eee6"/>'
  else:
   bg+='<rect x="370" y="360" width="170" height="95" rx="12" fill="#718d88"/><ellipse cx="455" cy="395" rx="47" ry="24" fill="#e8f0de" stroke="#46665e" stroke-width="5"/><path d="M455 372v45m-23-23h46" stroke="#647e72" stroke-width="8"/>'+paper(565,275,120,155)
 elif i==1:
  if n==1:
   bg+='<rect x="515" y="325" width="100" height="105" rx="14" fill="#9b6754"/><path d="M526 342h76" stroke="#354d43" stroke-width="11"/><path d="M565 430v70" stroke="#765744" stroke-width="15"/><rect x="485" y="393" width="100" height="65" fill="#fcf4df" stroke="#b69270" stroke-width="3"/><path d="M485 393l50 34 50-34" fill="none" stroke="#b69270" stroke-width="3"/>'
  else:
   bg+=paper(375,290,110,145)+paper(550,275,135,170)+'<path d="M495 355h40m-13-11 13 11-13 11" fill="none" stroke="#587765" stroke-width="6"/>'
 elif i==2:
  if n==1:
   bg+='<rect x="465" y="365" width="165" height="100" rx="5" fill="#fcf4de" stroke="#ad957a" stroke-width="4"/><path d="M465 365l82 50 83-50" fill="none" stroke="#ad957a" stroke-width="4"/><circle cx="547" cy="405" r="14" fill="#b65c4b"/><path d="M425 467h260v18H425z" fill="#b19878"/>'
  else:
   bg+='<rect x="350" y="292" width="120" height="172" rx="9" fill="#f8ead0" stroke="#718575" stroke-width="4"/><rect x="527" y="260" width="150" height="200" rx="6" fill="#f7faf3" stroke="#718575" stroke-width="4"/><path d="M546 300h108m-108 25h108m-108 25h74" stroke="#a9b8a4" stroke-width="6"/><path d="M410 328l15 18-26 27" fill="none" stroke="#af755e" stroke-width="6"/>'
 else:
  if n==1:
   bg+='<path d="M708 320l-15 24 17 10-19 28" stroke="#986349" stroke-width="5" fill="none"/><rect x="475" y="333" width="105" height="80" rx="8" fill="#42655c"/><circle cx="529" cy="375" r="24" fill="#accbc1" stroke="#e4ece0" stroke-width="5"/><rect x="487" y="321" width="29" height="14" fill="#42655c"/>'
  else:
   bg+=paper(367,278,118,174)+paper(560,290,130,161)+'<path d="M381 329h87m-87 24h60" stroke="#b68d6d" stroke-width="6"/><path d="M510 400l14 15 27-33" fill="none" stroke="#607d65" stroke-width="8"/>'
 return '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="560" viewBox="0 0 1000 560" data-illustration="mori-editorial">'+bg+'</svg>'

def main():
 snapshot()
 old=json.loads((ROOT/'data/blog-posts.json').read_text(encoding='utf-8'))
 template=(ROOT/'blog/20261101-morimachi-ikuji-nenkin/index.html').read_text(encoding='utf-8')
 css=re.search(r'<style>(.*?)</style>',template,re.S).group(1)
 author=re.search(r'<aside class="post-author.*?</aside>',template,re.S).group(0)
 assert '/profile' in author and 'author-oishi.jpg' in author
 parts={n:(ROOT/'parts'/f'{n}.html').read_text(encoding='utf-8') for n in ['header','footer','head-css']}
 for i,p in enumerate(POSTS):
  target=ROOT/'blog'/p['slug'];target.mkdir(exist_ok=True)
  body=(ROOT/'data/content'/f'blog-20261103-{p["key"]}.html').read_text(encoding='utf-8')
  motifs=[['冬前の家の外で家族が保温材のある配管をスマートフォンで記録する様子','止水栓の位置を確かめて設備の書類と連絡先へ引き継ぐ道筋'],['実家の郵便受けと封筒を確認する家族の様子','差出人を控えた紙から担当者の連絡記録へ引き継ぐ道筋'],['家の前で封のある遺言書の保管を考える家族の様子','封筒と保管に関する書類を分けて相談へ進む道筋'],['家の壁の傷みと修理のための記録をカメラで残す家族の様子','症状の記録と工事書類を分け、確認先へ引き継ぐ道筋']][i]
  for n in (1,2):
   graphic=figure(i,n);(target/f'fig{n}.svg').write_text(graphic,encoding='utf-8')
  doc=fitz.open(stream=figure(i,1).encode(),filetype='svg');pdf=fitz.open('pdf',doc.convert_to_pdf());pix=pdf[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False);pix.save(str(target/'cover.jpg'))
  for n,after in [(2,7),(1,3)]:
   alt='森町を思わせる山並み、茶畑、住宅を背景に、'+motifs[n-1]+'を描く概念イラスト。実在の物件や相談の記録ではありません。'
   fig=f'<figure><img src="/blog/{p["slug"]}/fig{n}.svg" width="1000" height="560" loading="lazy" alt="{alt}"><figcaption>記事の内容を図解した概念イラスト。{motifs[n-1]}。</figcaption></figure>'
   headings=list(re.finditer('<h2>',body));pos=headings[after].start();body=body[:pos]+fig+body[pos:]
  body+='<h2>FAQ｜家族からの確認</h2><p>この記事で扱う手続きや準備について、一般的な案内と個別に相談する事項を分けて回答します。</p>'+''.join('<h3>'+q+'</h3><p>'+a+'</p>' for q,a in p['faq'])
  url=SITE+'/blog/'+p['slug']+'/'
  graph=[{'@type':'BlogPosting','headline':p['title'],'datePublished':DATE,'dateModified':DATE,'author':{'@id':'https://oishi-hiroyuki.org/#person'},'image':url+'cover.jpg','mainEntityOfPage':url,'description':p['description']}, {'@type':'Person','@id':'https://oishi-hiroyuki.org/#person','name':'大石浩之','url':'https://oishi-hiroyuki.org/profile','image':SITE+'/assets/author-oishi.jpg','sameAs':['https://oishi-hiroyuki.org/profile','https://fudosan.atawi.link/']}, {'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'森町ライフハック','item':SITE+'/'},{'@type':'ListItem','position':2,'name':'ブログ','item':SITE+'/blog/'},{'@type':'ListItem','position':3,'name':p['title'],'item':url}]}, {'@type':'FAQPage','mainEntity':[{'@type':'Question','name':q,'acceptedAnswer':{'@type':'Answer','text':a}} for q,a in p['faq']]}]
  t=html.escape(p['title']);desc=html.escape(p['description'],quote=True)
  page=f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{t}｜森町ライフハック</title><meta name="description" content="{desc}"><link rel="canonical" href="{url}"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="alternate" type="application/rss+xml" href="/feed.xml" title="森町ライフハック ブログ"><meta property="og:type" content="article"><meta property="og:title" content="{t}"><meta property="og:description" content="{desc}"><meta property="og:url" content="{url}"><meta property="og:image" content="{url}cover.jpg"><meta name="twitter:card" content="summary_large_image"><script type="application/ld+json">'+json.dumps({'@context':'https://schema.org','@graph':graph},ensure_ascii=False)+'</script><!-- PART:head-css:START -->'+parts['head-css']+'<!-- PART:head-css:END --><style>'+css+'</style></head><body><!-- PART:header:START -->'+parts['header']+'<!-- PART:header:END --><main><article class="post"><nav aria-label="パンくず"><a href="/">ホーム</a> / <a href="/blog/">ブログ</a></nav><h1>'+t+'</h1><p class="post-meta"><time datetime="'+DATE+'">2026年11月3日</time> ／ 大石浩之</p><figure><img class="post-cover" src="/blog/'+p['slug']+'/cover.jpg" width="1200" height="672" alt="森町を思わせる山並みと茶畑、住宅を背景に、'+motifs[0]+'を描いた記事専用の表紙。実在の物件や相談の写真ではありません。"><figcaption>記事内容をもとに制作した概念イラスト。実在の物件や相談の記録ではありません。</figcaption></figure><section class="post-answer" aria-label="結論"><p><strong>Q. '+p['question']+'</strong></p><p>A. '+p['answer']+'</p></section><div class="post-editorial-body">'+body+'</div><div class="action-grid"><a href="/life/housing/close-parents-house/">森町の実家・空き家の整理を確認する</a></div><h2>出典・確認日</h2><p>2026年11月確認。事実は以下の一次情報、段取りと評価は大石浩之の意見として記述しています。</p><ul class="post-sources">'+''.join('<li><a href="'+SOURCES[k][1]+'">'+SOURCES[k][0]+'</a>（2026年11月3日確認）</li>' for k in p['sources'])+'</ul><p class="post-disclaimer">制度・条件・費用・窓口は変わる場合があります。手続きの前に最新情報を確認してください。個別の法律・登記・契約・設備の判断は、担当窓口や専門家へご相談ください。</p>'+author+'</article></main><!-- PART:footer:START -->'+parts['footer']+'<!-- PART:footer:END --></body></html>'
  (target/'index.html').write_text(page,encoding='utf-8')
  row={'slug':p['slug'],'title':p['title'],'date':DATE,'modified':DATE,'axis':'tue','description':p['description'],'home_description':p['description'],'cta':'official','primary_source':' / '.join(p['sources'])+'（2026-11-03確認）','cover_alt':motifs[0]+'を描いた概念イラスト。','search_index':True,'query':p['query']}
  match=next((x for x in old['posts'] if x['slug']==p['slug']),None)
  if match:match.update(row)
  else:old['posts'].append(row)
  rev=ROOT/'blog'/p['reverse']/'index.html';text=rev.read_text(encoding='utf-8');link='/blog/'+p['slug']+'/'
  if link not in text:
   m=re.search(r'</div>\s*<div class="action-grid">',text);assert m,p['reverse']
   lead=['冬前の配管と止水栓の確認は','死亡後に届く通知の整理は','遺言書らしい書類を発見した場合は','売却時の免責と告知の関係は'][i]
   text=text[:m.start()]+'<p>'+lead+'、<a href="'+link+'">'+t+'</a>で、家族が今日残せる記録と相談の順番を整理しています。</p>'+text[m.start():]
   text=re.sub(r'("dateModified"\s*:\s*")[^"]+',r'\g<1>'+DATE,text);rev.write_text(text,encoding='utf-8')
   next(x for x in old['posts'] if x['slug']==p['reverse'])['modified']=DATE
 (ROOT/'data/blog-posts.json').write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 meta={'run_id':'4a37ba6f03504137a8a19f2a90bd0c52','workflow_id':'e4043349d77bdee9a805f1f1c24a3970e780ba5a2fe9752e9989fef6980b1235','workflow_run':'4a37ba6f03504137a8a19f2a90bd0c52-batch','date':DATE,'articles':POSTS}
 (ROOT/'data/blog-batch-20261103-followup.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 save('design.json',{'date':DATE,'memo':'全件空欄。記事ごとに原則1または5を使用','experience':'なし・意見として記述','articles':POSTS,'sources':SOURCES,'images':'各記事の表紙1点と情景・確認の道筋を示すSVG2点。文字だけのカードを使わない。'})
 print('Rendered 4 articles, 12 original images and 4 backlinks')
if __name__=='__main__':main()
