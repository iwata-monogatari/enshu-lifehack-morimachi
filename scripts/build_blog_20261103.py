"""Render the four approved 2026-11-03 articles from their editorial source.
No publish operation. Shared site indexes are owned by build_all.py.
"""
from pathlib import Path
import json, re, html
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
SITE='https://morimachi.enshu-lifehack.com'
DATE='2026-11-03'
META=ROOT/'data/blog-batch-20261103.json'
TOWN='https://www.town.morimachi.shizuoka.jp/'
SOURCES={
 'seminar':('森町：我が家の終活セミナー開催',TOWN+'gyosei/machinososhiki/teijusuishinka/ijukoryugakari/2/7028.html'),
 'bank':('森町：空き家・空き地バンク',TOWN+'gyosei/machinososhiki/teijusuishinka/ijukoryugakari/2/2/379.html'),
 'rights':('日本司法書士会連合会：権利証を紛失した場合','https://www.shiho-shoshi.or.jp/consulting/muniments/case_muniments02/'),
 'reins':('国土交通省：レインズのステータス管理機能','https://www.mlit.go.jp/totikensangyo/const/content/001854004.pdf'),
 'contract':('国土交通省：専属専任媒介契約制度の施行等について','https://www.mlit.go.jp/notice/noticedata/sgml/016/74000466/74000466.html'),
 'standard':('国土交通省：標準専属専任媒介契約約款','https://www.mlit.go.jp/common/001180502.pdf'),
 'fire':('志太消防本部：2026年秋の全国火災予防運動','https://www.shida119.jp/whatsnew/whatsnew-20784/'),
 'insurance':('日本損害保険協会：火災保険の告知・通知事項','https://soudanguide.sonpo.or.jp/home/q059.html?vm=r'),
 'alarm':('森町：住宅用火災警報器の交換',TOWN+'gyosei/bosai_anzen/syoubou/3984.html'),
 'support':('森町：住宅用火災警報器の取り付け支援',TOWN+'gyosei/bosai_anzen/syoubou/3983.html'),
 'guide':('森町：家庭ごみ分別表・収集日カレンダーの案内',TOWN+'gyosei/machinososhiki/juminseikatsuka/seikatsukankyokakari/1/1/692.html'),
 'sorting':('森町：令和8年度家庭ごみ分別表',TOWN+'material/files/group/6/kateigomibunnbetu2026.pdf'),
 'recycle':('消火器リサイクル推進センター：処分の手順','https://www.ferpc.jp/disposal/help/')}
DETAILS=[
 ('kenrisho',['seminar','bank','rights'],'権利証がなくても、本人確認の方法を相談して売却準備を進められます。再発行できない書類と代わりの手続き、森町の空き家バンクとの役割の違いを整理。書類の所在、名義、費用と日程を確かめ、家族が売却を急がず判断するための準備を紹介します。',[
 '権利証や登記識別情報は、紛失を理由に再発行できません。日本司法書士会連合会は、司法書士による本人確認情報、法務局の事前通知、公証人の認証などを案内しています。どの方法を使えるかは個別に確認します。再発行の申請先を探し続けるより、対象物件と所有者の状況を整理して司法書士へ相談してください。',
 '権利証をなくしたことだけで、直ちに所有権を失うわけではありません。ただし、ほかの本人確認書類もなくした場合や、不正利用が心配な場合は早めに専門家へ相談します。安全だと家族だけで決めず、なくした書類と時期を整理してください。登記の状態や必要な対応は、法務局や司法書士へ個別に確かめます。',
 '家族の説明だけで、所有者本人の確認がすべて済むとは考えないでください。誰がどの資料を準備し、どの方法で本人確認を受けるかは担当する司法書士に聞きます。本人が移動しにくい事情があれば、売買の日程を決める前に相談します。家族の連絡担当を決めることと、本人の意思や権限の確認は別の作業です。']),
 ('baikai',['bank','seminar','reins','contract','standard'],'媒介契約は、依頼先の数、自分で見つけた買主との契約、業務報告の扱いで選びます。一般・専任・専属専任の違いと、レインズの売主画面を整理。森町の実家へ通う家族が、鍵の管理と報告方法まで確かめて、無理なく売却を依頼する段取りを紹介します。',[
 '一般媒介は複数の不動産会社へ依頼できます。ただし、ほかの依頼先を明示する方式など、契約案の条件を確認してください。会社数を増やせば、価格変更や内見日程をそろえる家族の作業も増えます。何社なら管理できるかを考え、各社への連絡担当を決めます。一般媒介という名称だけで、連絡や契約上の義務がないとは判断しません。',
 '専任媒介では、自分で見つけた相手と直接契約できます。専属専任媒介では、その場合も依頼した会社を通します。業務報告の最低頻度も専任は二週間に一回以上、専属専任は一週間に一回以上と異なります。知人から購入の話が出る可能性があるなら、署名前に伝え、契約案で具体的な扱いを確認してください。',
 'レインズへの登録は、売却の成立や価格を保証するものではありません。不動産会社間で物件情報を共有する仕組みです。専任・専属専任では登録証明書を受け取り、売主専用画面と業務報告を照合します。申込みがある表示になっても、契約成立とは区別してください。実際の条件や進行状況は依頼した会社へ確認します。']),
 ('hoken',['fire','insurance','alarm','support'],'住まなくなった実家の火災保険は、契約先へ利用状況を伝えて確認します。告知と通知、建物と家財、受付と変更完了を区別。森町の防火案内も参照し、保険証券と居住状況のメモをそろえ、家族が自己判断で解約する前に確かめる順序を紹介します。',[
 '空き家になったという呼び方だけで、必ず無効になるとも、そのまま補償されるとも断定できません。現在の利用状況と契約内容によって取扱いを確認します。住まなくなった時期、宿泊の実態、家財の移動を契約先へ伝えてください。通知や変更が必要かを聞き、自己判断で解約したり、連絡を省いたりしないことを勧めます。',
 '週末に通っていることだけで通知不要とは判断できません。見回りだけか、宿泊しているか、今後の利用予定はどうかを正確に伝えます。商品の約款などで通知が求められる事項を契約先に確認してください。家族が実家と呼んでいることと、保険会社が判断する建物の用法は分けて考え、回答の前提も記録しておきます。',
 '保険料の支払いが続いているだけでは、現在の建物の使い方が契約内容に合っていると確認できません。日本損害保険協会は契約後の通知事項を案内しています。証券番号と利用状況をそろえ、契約先へ確認してください。個別の事故に保険金が支払われるかは本稿では判定せず、契約内容と事故の事実に基づいて照会します。']),
 ('shokaki',['fire','guide','sorting','recycle'],'消火器は、中身がなくても森町のごみ収集に出せません。実家で見つけた古い一本は、種類と表示を確かめて専用の回収窓口へ相談します。スプレー式との違い、シールと運搬費、引取りと持込みの確認順を整理し、片付けを担う家族の無理を減らします。',[
 '森町の分別表では、中身のない消火器も通常の収集に出せないものに含まれます。金属の容器だからという理由で金属類へ混ぜないでください。空かどうかを確かめるために分解や試し噴射をせず、表示と状態を回収窓口へ伝えます。製品の種類に応じた引取先と受入条件を確認し、案内された方法で処分を進めます。',
 'スプレー式消火具は、消火器リサイクル推進センターの回収システムの対象外です。製造元や販売元へ中身の扱いを尋ね、自治体の分別ルールを確認します。普通の消火器と一緒に持ち込めるとは判断しないでください。製品名が読めない場合も推測で分けず、分からないことを伝えて処分方法を相談します。',
 '処分料金は、本稿では一律の金額を確認していません。リサイクルシールの費用のほか、引取りの収集運搬費や、持込み先での保管費などがかかる場合があります。メーカー、種類、本数、状態、引取り場所を伝えて総額を聞いてください。シールが貼られていることだけで、すべて無料になるとは判断できません。'])]

def house(x,y,s=1):
 return f'<g transform="translate({x} {y}) scale({s})"><path d="M-15 55L100-25 215 55Z" fill="#52685b"/><rect x="0" y="55" width="200" height="145" rx="5" fill="#f5e4bf"/><rect x="26" y="83" width="48" height="52" fill="#abc8c5"/><path d="M50 83v52M26 109h48" stroke="#fff" stroke-width="4"/><rect x="123" y="108" width="47" height="92" fill="#a77d5e"/></g>'
def person(x,y,color='#668979'):
 return f'<g transform="translate({x} {y})"><circle cy="-78" r="22" fill="#dfb38e"/><path d="M-22-91Q0-121 24-89" fill="#37483e"/><path d="M-33-45Q0-66 33-45L45 50H-45Z" fill="{color}"/><path d="M-20 50l-7 65m47-65 7 65" stroke="#40584b" stroke-width="16" stroke-linecap="round"/></g>'
def paper(x,y,w=100,h=130):
 return f'<g transform="translate({x} {y})"><rect width="{w}" height="{h}" rx="5" fill="#fffdf5" stroke="#8d9e8c" stroke-width="3"/><path d="M15 30h{w-30}m-{w-30} 22h{w-30}m-{w-30} 22h{w-45}" stroke="#a9b6a4" stroke-width="5"/><circle cx="{w-24}" cy="{h-25}" r="11" fill="#c68b63"/></g>'
def exting(x,y,s=1):
 return f'<g transform="translate({x} {y}) scale({s})"><rect x="-30" y="-60" width="60" height="120" rx="21" fill="#b95543"/><rect x="-19" y="-22" width="38" height="47" rx="3" fill="#fff3dc"/><path d="M0-60v-22h30m-30 0h-24m40 6q45 3 34 93" fill="none" stroke="#344b48" stroke-width="9"/><circle cy="-59" r="10" fill="#d7d8ba" stroke="#344b48" stroke-width="3"/><path d="M-25 60h50" stroke="#344b48" stroke-width="7"/></g>'
def svg(i,n):
 base='<rect width="1000" height="560" fill="#edf2e9"/><circle cx="839" cy="95" r="44" fill="#efd5a0"/><path d="M0 230L170 85 365 230 560 80 790 240 920 140 1000 220V560H0Z" fill="#bdcdb7"/><path d="M0 290Q190 200 370 285T1000 245V560H0Z" fill="#8eab89"/><path d="M0 390Q250 290 550 410T1000 350V560H0Z" fill="#cbd3a6"/><path d="M0 470Q230 360 480 460T1000 420" stroke="#eff0d7" stroke-width="28" fill="none"/>'
 if n==1:
  base+=house(650,230,.9)
  base+=person(250,350)+person(450,350,'#b88d68')
  base+='<path d="M100 415H590v28H100zm30 28v100m430-100v100" fill="#9e7958" stroke="#9e7958" stroke-width="12"/>'
  if i==0: base+=paper(310,280)+ '<path d="M130 345h130v66H130Z" fill="#ad9872"/><path d="M130 345l-35-35h130l35 35" fill="#d4c4a0"/>'+paper(151,316,70,70)
  elif i==1:
   base+=paper(320,282,100,130)
   for x in [620,755,890]:base+=f'<path d="M400 280Q{x} 170 {x} 130" stroke="#e9eed7" stroke-width="6" fill="none"/>'+paper(x-35,70,70,80)
  elif i==2:base+=paper(310,275)+ '<path d="M530 330l65-33 65 33v70q-65 65-130 0Z" fill="#527e80"/><path d="M559 366l24 24 45-50" fill="none" stroke="#f8f1d8" stroke-width="10"/>'
  else:base+=exting(350,349,.9)+ '<rect x="590" y="305" width="60" height="110" fill="#b8a482"/>'
 else:
  base+=house(80,235,.8)+person(390,345)+person(770,345,'#b88d68')
  base+='<path d="M290 475Q480 390 650 475" stroke="#f7efd8" stroke-width="38" fill="none"/><path d="M618 446l38 30-43 28" fill="none" stroke="#71927b" stroke-width="9"/>'
  base+='<rect x="475" y="330" width="110" height="125" rx="12" fill="#345654"/><rect x="485" y="344" width="90" height="85" fill="#edf2d9"/><circle cx="530" cy="442" r="6" fill="#edf2d9"/>'
  if i==0:base+=paper(300,390,80,100)+paper(840,300,85,110)
  elif i==1:base+=paper(310,375,90,110)+ '<rect x="610" y="273" width="125" height="90" rx="8" fill="#526e65"/><rect x="620" y="283" width="105" height="67" fill="#f3edd7"/><path d="M630 300h80m-80 18h62m-62 18h74" stroke="#92a991" stroke-width="6"/>'
  elif i==2:base+=paper(300,385,80,100)+ '<path d="M695 280q-20-25-35 0l-15 35q0 30 25 40" stroke="#345654" stroke-width="15" fill="none"/>'
  else:base+=exting(300,390,.75)+exting(845,412,.65)+ '<rect x="810" y="470" width="95" height="12" fill="#36524b"/><circle cx="830" cy="493" r="12" fill="#36524b"/><circle cx="890" cy="493" r="12" fill="#36524b"/>'
 return '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="560" viewBox="0 0 1000 560" data-illustration="mori-editorial" role="img"><title>森町の暮らしと実家整理の概念イラスト</title>'+base+'</svg>'

def cover(p,i):
 im=Image.new('RGB',(1200,675),'#edf2e9');d=ImageDraw.Draw(im)
 d.polygon([(0,400),(210,140),(460,350),(700,160),(1000,380),(1200,250),(1200,675),(0,675)],fill='#a6bea0')
 for y in range(410,675,42):d.arc((-120,y,950,y+250),180,350,fill='#6d9172',width=14)
 d.rectangle((780,350,1100,590),fill='#f2e1bd');d.polygon([(745,355),(930,230),(1135,355)],fill='#52685b');d.rectangle((980,440,1050,590),fill='#a47b59')
 d.rounded_rectangle((55,70,740,350),radius=25,fill='#faf6e9')
 f=ImageFont.truetype('C:/Windows/Fonts/YuGothB.ttc',45)
 for j,line in enumerate(p['title'].replace('｜','\n').split('\n')):d.text((85,100+j*75),line,font=f,fill='#294d42')
 small=ImageFont.truetype('C:/Windows/Fonts/YuGothM.ttc',25)
 d.text((87,284),'森町ライフハック  /  2026.11.03',font=small,fill='#547568')
 if i==3:
  d.rounded_rectangle((490,450,595,625),radius=35,fill='#b95543');d.rectangle((517,420,565,457),fill='#344b48');d.rectangle((515,497,570,555),fill='#fff3dc')
 else:
  d.rounded_rectangle((420,410,600,615),radius=8,fill='#fffaf0',outline='#52685b',width=3)
  for y in [450,480,510]:d.line((445,y,570,y),fill='#98b19b',width=6)
  if i==1:
   for x in [245,650]:d.rounded_rectangle((x,460,x+90,580),radius=5,fill='#fffaf0',outline='#52685b',width=3)
  if i==2:d.polygon([(650,445),(710,420),(770,445),(760,540),(710,580),(660,540)],fill='#527e80')
 im.save(ROOT/'blog'/p['slug']/'cover.jpg',quality=89,optimize=True)

def main():
 data=json.loads(META.read_text(encoding='utf-8'));posts=data['articles']
 template=(ROOT/'blog/20261101-morimachi-ikuji-nenkin/index.html').read_text(encoding='utf-8')
 css=re.search(r'<style>(.*?)</style>',template,re.S).group(1)
 author=re.search(r'<aside class="post-author.*?</aside>',template,re.S).group(0)
 parts={n:(ROOT/'parts'/f'{n}.html').read_text(encoding='utf-8') for n in ['header','footer','head-css']}
 ledger=json.loads((ROOT/'data/blog-posts.json').read_text(encoding='utf-8'))
 for i,(p,(key,sourcekeys,desc,answers)) in enumerate(zip(posts,DETAILS)):
  out=ROOT/'blog'/p['slug'];out.mkdir(exist_ok=True)
  body=(ROOT/'data/content'/f'blog-20261103-{key}.html').read_text(encoding='utf-8')
  alts=[f'森町を思わせる山並みと茶畑のある風景で、{v}を描いた概念イラスト。実際の人物や相談の記録ではなく、記事の確認手順を表す。' for v in p['images']]
  coveralt='森町を思わせる山並みと茶畑、家を背景に、'+['書類を表す紙を置いた表紙図案','三つの契約を表す紙を並べた表紙図案','契約書類と補償を表す盾を置いた表紙図案','古い消火器の処分を主題に赤い消火器を描いた表紙図案'][i]+'。実在する家の写真ではありません。'
  for n,after in [(1,3),(2,7)]:
   graphic=svg(i,n);(out/f'fig{n}.svg').write_text(graphic,encoding='utf-8')
   fig=f'<figure><img src="/blog/{p["slug"]}/fig{n}.svg" width="1000" height="560" loading="lazy" alt="{html.escape(alts[n-1],quote=True)}"><figcaption>記事の内容を図解した概念イラスト。{p["images"][n-1]}。</figcaption></figure>'
   hs=list(re.finditer('<h2>',body));pos=hs[after].start();body=body[:pos]+fig+body[pos:]
  faq=''.join(f'<h3>{q}</h3><p>{a}</p>' for q,a in zip(p['faq'],answers))
  body+='<h2>FAQ｜家族からの確認</h2><p>ここでは、この記事の主題に沿って、相談前に確認したい疑問を整理します。個別の条件は関係する窓口や専門家へ確認してください。</p>'+faq
  url=SITE+'/blog/'+p['slug']+'/'
  graph=[{'@type':'BlogPosting','headline':p['title'],'description':desc,'datePublished':DATE,'dateModified':DATE,'inLanguage':'ja','mainEntityOfPage':url,'image':url+'cover.jpg','author':{'@type':'Person','@id':'https://oishi-hiroyuki.org/#person','name':'大石浩之','url':'https://oishi-hiroyuki.org/profile'}},
   {'@type':'Person','@id':'https://oishi-hiroyuki.org/#person','name':'大石浩之','url':'https://oishi-hiroyuki.org/profile','image':SITE+'/assets/author-oishi.jpg','sameAs':['https://oishi-hiroyuki.org/profile','https://fudosan.atawi.link/']},
   {'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'森町ライフハック','item':SITE+'/'},{'@type':'ListItem','position':2,'name':'ブログ','item':SITE+'/blog/'},{'@type':'ListItem','position':3,'name':p['title'],'item':url}]},
   {'@type':'FAQPage','mainEntity':[{'@type':'Question','name':q,'acceptedAnswer':{'@type':'Answer','text':a}} for q,a in zip(p['faq'],answers)]}]
  srcs=''.join(f'<li><a href="{html.escape(SOURCES[k][1],quote=True)}" target="_blank" rel="noopener">{SOURCES[k][0]}</a>（2026年11月3日確認）</li>' for k in sourcekeys)
  t=html.escape(p['title']);descattr=html.escape(desc,quote=True)
  head=f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{t}｜森町ライフハック</title><meta name="description" content="{descattr}"><link rel="canonical" href="{url}"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="alternate" type="application/rss+xml" href="/feed.xml" title="森町ライフハック ブログ"><meta property="og:type" content="article"><meta property="og:title" content="{t}"><meta property="og:description" content="{descattr}"><meta property="og:url" content="{url}"><meta property="og:image" content="{url}cover.jpg"><meta name="twitter:card" content="summary_large_image"><script type="application/ld+json">'+json.dumps({'@context':'https://schema.org','@graph':graph},ensure_ascii=False)+'</script>'
  page=head+'<!-- PART:head-css:START -->'+parts['head-css']+'<!-- PART:head-css:END --><style>'+css+'</style></head><body><!-- PART:header:START -->'+parts['header']+'<!-- PART:header:END --><main><article class="post"><nav aria-label="パンくず"><a href="/">ホーム</a> / <a href="/blog/">ブログ</a></nav><h1>'+t+'</h1><p class="post-meta"><time datetime="'+DATE+'">2026年11月3日</time> ／ 大石浩之</p><figure><img class="post-cover" src="/blog/'+p['slug']+'/cover.jpg" width="1200" height="675" alt="'+html.escape(alts[0],quote=True)+'"><figcaption>記事の主題を図案化した表紙。実在する物件や相談の写真ではありません。</figcaption></figure><section class="post-answer" aria-label="結論"><p><strong>Q. '+p['question']+'</strong></p><p>A. '+p['answer']+'</p></section><div class="post-editorial-body">'+body+'</div><div class="action-grid"><a href="/life/housing/close-parents-house/">森町の実家・空き家の整理を確認する</a></div><h2>出典・確認日</h2><p>2026年11月確認。公的情報と業界団体の案内を参照し、評価と段取りの提案は大石浩之の意見として記述しました。</p><ul class="post-sources">'+srcs+'</ul><p class="post-disclaimer">制度・利用条件・費用・日程は変わる場合があります。実際に手続きをする前に最新情報を確認してください。個別の法律、契約、安全性などの判断は関係する専門家や担当窓口へご相談ください。</p>'+author+'</article></main><!-- PART:footer:START -->'+parts['footer']+'<!-- PART:footer:END --></body></html>'
  page=page.replace('alt="'+html.escape(alts[0],quote=True)+'"><figcaption>記事の主題', 'alt="'+html.escape(coveralt,quote=True)+'"><figcaption>記事の主題')
  (out/'index.html').write_text(page,encoding='utf-8');cover(p,i)
  row={'slug':p['slug'],'title':p['title'],'date':DATE,'modified':DATE,'axis':'tue','description':desc,'home_description':desc,'cta':'official','primary_source':' / '.join(sourcekeys)+'（2026-11-03確認）','cover_alt':alts[0],'search_index':True,'query':p['query']}
  row['cover_alt']=coveralt
  existing=next((x for x in ledger['posts'] if x['slug']==p['slug']),None)
  if existing:existing.update(row)
  else:ledger['posts'].append(row)
  rev=ROOT/'blog'/p['reverse']/'index.html';text=rev.read_text(encoding='utf-8')
  link=f'/blog/{p["slug"]}/'
  if link not in text:
   marker='</div><div class="action-grid">'
   if marker not in text: marker='</div>\n<div class="action-grid">'
   if marker not in text:
    m=re.search(r'</div>\s*<div class="action-grid">',text);assert m,p['reverse'];marker=m.group(0)
   additions=['登記の書類が見つからない場合は','売却を依頼する会社との約束は','住まなくなった後の契約確認は','古い消火器が出てきた場合は']
   sentence=f'<p>{additions[i]}、<a href="{link}">{t}</a>で、相談前にそろえる材料と確認の順番を整理しています。</p>'
   text=text.replace(marker,sentence+marker,1)
   # Preserve original publication date; record this real link addition.
   text=re.sub(r'("dateModified"\s*:\s*")[^"]+',r'\g<1>'+DATE,text)
   rev.write_text(text,encoding='utf-8')
   old=next(x for x in ledger['posts'] if x['slug']==p['reverse']);old['modified']=DATE
 (ROOT/'data/blog-posts.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Rendered 4 articles, 12 images, 4 contextual backlinks')
if __name__=='__main__':main()
