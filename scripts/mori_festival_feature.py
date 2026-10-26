"""The festival feature reuses the existing, indexed Discover guide URL."""
from html import escape as e
import json

URL = 'https://morimachi.enshu-lifehack.com/discover/mori-festival/'
NOTICE = 'https://www.mori-kanko.jp/newsdetail/morinomaturipanfuposuta2026.html'
STATION = 'https://www.tenhama.co.jp/about/station/enshumori/'
IDS = ['intro', 'dates', 'highlights', 'train', 'parking', 'family', 'weather',
       'plan', 'culture', 'information', 'before-you-go', 'perspective', 'summary']


def lantern(x, y, scale=1):
    return f'<g transform="translate({x} {y}) scale({scale})"><path d="M0 -16V0" stroke="#e8be6b" stroke-width="2"/><ellipse cy="23" rx="15" ry="22" fill="#f3bd67"/><path d="M-10 7H10M-14 17H14M-14 28H14M-10 39H10" stroke="#b77d3d" stroke-width="1.5"/><path d="M-7 1H7M-7 45H7" stroke="#18373c" stroke-width="4"/></g>'


def float_art(x=0,y=0,s=1):
    # Editorial illustration; not a replica of any of the fourteen floats.
    wheels=''.join(f'<g transform="translate({cx} 310)"><circle r="47" fill="#402d26" stroke="#bb8548" stroke-width="8"/>'+''.join(f'<path d="M0 -41V41" transform="rotate({a})" stroke="#ce9a5c" stroke-width="4"/>' for a in (0,30,60,90,120,150))+'<circle r="10" fill="#d6b26f"/></g>' for cx in (62,238))
    return f'''<g transform="translate({x} {y}) scale({s})"><path d="M-36 273H354" stroke="#91613b" stroke-width="15"/>{wheels}<path d="M32 110V278H266V110" fill="#895b39" stroke="#d6a464" stroke-width="8"/><path d="M52 150H247V245H52Z" fill="#233d3b"/><path d="M68 160V240M110 160V240M155 160V240M199 160V240M234 160V240" stroke="#be8950" stroke-width="8"/><path d="M15 125Q150 -5 285 125L252 135Q150 65 47 135Z" fill="#1b2d31" stroke="#ba8c51" stroke-width="8"/><path d="M0 121Q44 122 66 101M300 121Q259 122 236 101" fill="none" stroke="#d8b875" stroke-width="7"/><path d="M17 259H283V280H17Z" fill="#b4834c"/><path d="M30 224H270" stroke="#deb675" stroke-width="7"/><path d="M35 218V257M67 218V257M233 218V257M265 218V257" stroke="#d9b573" stroke-width="5"/>{lantern(36,137,.85)}{lantern(265,137,.85)}<path d="M120 128H184V150H120Z" fill="#a23e33"/><circle cx="150" cy="140" r="7" fill="#f0cc8c"/></g>'''


def people(x,y,s=1):
    return f'<g transform="translate({x} {y}) scale({s})"><circle cx="0" cy="0" r="12" fill="#dca77b"/><path d="M-13 17H12L19 64H-19Z" fill="#254f54"/><path d="M-10 62L-14 96M11 62L15 96" stroke="#233a40" stroke-width="9"/><circle cx="41" cy="33" r="9" fill="#dca77b"/><path d="M31 45H51L54 77H28Z" fill="#ae4b3b"/><path d="M34 76L30 98M47 76L51 98M13 25L31 52" stroke="#543f34" stroke-width="6"/></g>'


def houses():
    return ''.join(f'<g transform="translate({x} {y})"><path d="M0 55L75 12L150 55Z" fill="#294a48"/><path d="M10 55H140V164H10Z" fill="{c}"/><path d="M34 75H112V152H34Z" fill="#335452"/><path d="M46 75V152M62 75V152M78 75V152M94 75V152" stroke="#bdac89" stroke-width="4"/><path d="M5 55H145" stroke="#b79568" stroke-width="6"/></g>' for x,y,c in [(10,280,'#bdab89'),(160,250,'#c7b999'),(755,270,'#c9b48e'),(910,300,'#b9a481')])


def illustration(number):
    if number == 2:
        scene = '''<rect width="1200" height="630" fill="#f1ecdf"/><path d="M50 500Q260 365 440 477T800 451T1160 486" fill="none" stroke="#cbaa70" stroke-width="12" stroke-dasharray="8 16"/><path d="M40 280L155 187L269 280" fill="#35615b"/><path d="M65 281H245V422H65Z" fill="#d3b98b"/><path d="M92 308H160V352H92Z" fill="#fff9e8"/><path d="M180 313V420" stroke="#8e6747" stroke-width="24"/><rect x="348" y="254" width="240" height="139" rx="17" fill="#416c61"/><path d="M363 285H572V345H363Z" fill="#d6e5d9"/><path d="M427 285V345M506 285V345" stroke="#416c61" stroke-width="9"/><path d="M350 361H585" stroke="#d8ae68" stroke-width="8"/><circle cx="396" cy="405" r="18" fill="#294348"/><circle cx="543" cy="405" r="18" fill="#294348"/><circle cx="1040" cy="284" r="69" fill="#fffcf2" stroke="#385b55" stroke-width="10"/><path d="M1040 236V284L1074 306" fill="none" stroke="#ad4d3c" stroke-width="9"/>'''+float_art(667,210,.54)+people(878,381,.7)+people(139,380,.65)+'''<g fill="#244740" font-family="sans-serif" text-anchor="middle"><text x="155" y="115" font-size="27">案内を読む</text><text x="465" y="115" font-size="27">往復を決める</text><text x="785" y="115" font-size="27">余白を持って見る</text><text x="1040" y="115" font-size="27">帰る時刻を確認</text><text x="600" y="580" font-size="22">行程のイメージです。地図・屋台の運行経路ではありません。</text></g>'''
    else:
        sky='#18383e' if number == 0 else '#e0e9df'
        scene=f'<rect width="1200" height="630" fill="{sky}"/><circle cx="1014" cy="99" r="45" fill="#efd69b"/><path d="M0 265L167 123L290 218L430 101L630 262L819 172L1030 275L1200 152V500H0Z" fill="#315a55"/><path d="M0 350L230 226L420 306L675 179L955 327L1200 255V531H0Z" fill="#497568"/>'+houses()+'<path d="M0 470Q600 380 1200 485V630H0Z" fill="#b1aa8e"/><path d="M430 630L545 401H665L842 630Z" fill="#d5c6a5"/>'+float_art(436,129,1.1)+people(160,425,1.15)+people(939,439,.9)
        scene+=''.join(lantern(x,98+(x%3)*13,.75) for x in (60,190,320,900,1110))
        scene+='<path d="M0 62Q600 132 1200 62" fill="none" stroke="#ba9864" stroke-width="3"/>'
        if number == 1:
            scene+='<path d="M600 0H1200V630H600Z" fill="#18383e" opacity=".18"/><g font-family="sans-serif" font-size="26" fill="#fff9e8"><rect x="30" y="25" width="260" height="48" rx="24" fill="#244740"/><text x="58" y="58">昼の造形、夜の灯り</text></g>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" data-illustration="mori-editorial"><title>森のまつりの編集イラスト</title><desc>実在の屋台・場所・運行経路を再現したものではありません。</desc>{scene}</svg>'



TRAFFIC_GUIDE = '''<section class="editorial-section" id="traffic-guide"><h2>当年の交通規制図を読む</h2>
<p><a href="https://www.mori-kanko.jp/newsdetail/maturi2026kisei.html" target="_blank" rel="noopener" data-track-click="mori_festival_official">観光協会の2026年交通規制・駐車場案内を開く</a>。10月21日公表、10月23日取得の保存資料を10月26日に確認しました。</p>
<p>下の一覧は、公式図のピンク色・水色の区間について、車両通行禁止の時間を抜粋したものです。規制区域はリンク先の地図で確認してください。その他の色・区間にも別の規制があり、この一覧だけで通行可否を判断できません。</p>
<dl><dt><b>11月6日（金）</b></dt><dd>ピンク色の区間：10:00〜22:00／水色の区間：17:00〜22:00</dd>
<dt><b>11月7日（土）</b></dt><dd>ピンク色の区間：8:00〜22:00／水色の区間：12:00〜22:00</dd>
<dt><b>11月8日（日）</b></dt><dd>ピンク色の区間：8:00〜22:30／水色の区間：11:00〜22:30</dd></dl>
<p>これは駐車場の開放時間や屋台の通過時刻ではありません。青いPは無料駐車場、丸数字は概算台数の表示です。無料でも空きは保証されません。利用する場所と入出庫条件、駐車後の徒歩経路を確かめてください。</p>
<h3>11月8日の舞児還しは、立入制限にも注意</h3>
<p>公式図では、三島神社下の黄色で示された指定区域について、17:00から19:30頃の最後の屋台が出終わるまで、正装以外の一般観客の立入りを遠慮するよう案内しています。舞児還し出発の18:00より前からの制限です。区域は拡大図で確認し、当日の誘導を優先してください。</p>
<p>送迎・駐車後の歩き方は<a href="/blog/20261023-mori-matsuri-kisei-car/">既存の交通規制確認記事</a>でも整理しています。<a href="#source-10">公式出典・確認時点</a></p></section>'''

def render(row, parts, count):
    links = ''.join(f'<li id="source-{n}"><a href="{e(s["url"])}" target="_blank" rel="noopener">{e(s["title"])}</a><small>{e(s["publisher"])}</small></li>' for n,s in enumerate(row['sources'],1))
    source_map={1:[1,8,9],2:[2,3,4],3:[5,6],4:[10],5:[2,5],8:[4],9:[10]}
    contents=[]
    for i,section in enumerate(row['body_sections']):
        ps=''.join(f'<p>{e(p)}</p>' for p in section['paragraphs'])
        refs=''.join(f'<a href="#source-{n}">出典 {n}</a> ' for n in source_map.get(i,[]))
        contents.append(f'<section class="editorial-section" id="{IDS[i]}"><span class="section-no" aria-hidden="true">{i+1:02}</span><h2>{e(section["heading"])}</h2>{ps}<div class="source-ref">{refs}</div></section>')
        if i == 4:
            contents.append(TRAFFIC_GUIDE)
        if i in (2,10):
            n=1 if i==2 else 2
            item=row['illustrations'][n-1]
            contents.append(f'<figure class="feature-figure"><img src="fig{n}.svg" width="1200" height="630" loading="lazy" alt="{e(item["alt"])}"><figcaption>{e(item["caption"])}</figcaption></figure>')
    checks=['2026年の公式案内で見たい日の進行を確認した','帰りの列車・接続、または当年の駐車条件を確認した','休憩・トイレ・家族の集合場所を決めた','天候と交通機関の運行情報を出発前に確認する']
    checklist=''.join(f'<label><input type="checkbox"><span>{e(t)}</span></label>' for t in checks)
    faqs=[('2026年はいつ開催？','11月6日（金）〜8日（日）です。森町観光協会の2026年10月1日のお知らせで確認しています。'),('見物心得帳はどこでもらえる？','観光協会は、森町役場や観光案内所での無料配布を案内しています。受取時間と在庫は問い合わせ先へ確認してください。'),('無料駐車場はある？','観光協会の2026年交通規制図には無料駐車場の位置が示されています。青いPと丸数字（概算台数）を公式図で確認してください。無料でも空きは保証されず、道路の規制時間は駐車場の開放時間ではありません。個別の入出庫条件と当日の案内も確認してください。'),('舞児還しは何時から？','神前で舞を奉納した舞児を家まで送る行事です。2026年11月8日（日）16時30分に舞児還し式、18時に三島神社から出発の予定です。式と出発は別の時刻です。変更は公式・現地案内で確認してください。'),('雨でも見学できる？','今年の雨天変更基準は本特集では未確認です。主催者側の案内と鉄道の運行情報を出発前に確認してください。')]
    faqhtml=''.join(f'<details><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q,a in faqs)
    schema={'@context':'https://schema.org','@type':'Article','headline':row['title'],'description':row['description'],'mainEntityOfPage':URL,'datePublished':row['published_at'],'dateModified':row['updated_at'],'author':{'@type':'Person','name':'大石浩之','url':'https://morimachi.enshu-lifehack.com/about/author/'},'publisher':{'@type':'Organization','name':'森町ライフハック'},'image':URL+'cover.svg'}
    schema = {'@context': 'https://schema.org', '@graph': [
        {k:v for k,v in schema.items() if k != '@context'},
        {'@type':'BreadcrumbList','itemListElement':[
            {'@type':'ListItem','position':1,'name':'森町ライフハック','item':'https://morimachi.enshu-lifehack.com/'},
            {'@type':'ListItem','position':2,'name':'森町のガイド','item':'https://morimachi.enshu-lifehack.com/discover/'},
            {'@type':'ListItem','position':3,'name':row['title'],'item':URL}
        ]}
    ]}
    return f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(row['title'])}</title><meta name="description" content="{e(row['description'])}"><link rel="canonical" href="{URL}">
<meta property="og:type" content="article"><meta property="og:title" content="{e(row['title'])}"><meta property="og:description" content="{e(row['description'])}"><meta property="og:url" content="{URL}"><meta property="og:image" content="{URL}cover.svg">
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><!-- PART:head-css:START -->{parts['head-css']}<!-- PART:head-css:END -->
<link rel="stylesheet" href="/assets/mori-festival.css?v=20261019a"><script type="application/ld+json">{json.dumps(schema,ensure_ascii=False)}</script></head>
<body class="festival-page"><!-- PART:header:START -->{parts['header']}<!-- PART:header:END -->
<main><article class="festival-wrap"><nav class="breadcrumb" aria-label="パンくず"><a href="/">森町ライフハック</a> ／ <a href="/discover/">森町のガイド</a> ／ 森のまつり</nav>
<header class="festival-hero"><div class="hero-copy"><p class="feature-kicker">遠州の秋、町が祭りになる。</p><h1>{e(row['title'])}</h1><p class="festival-date"><span>2026</span>11.6 <small>金</small> — 11.8 <small>日</small></p><p class="feature-lead">{e(row['lead'])}</p><a class="feature-button" href="#essentials">日程と訪問のポイントへ <span aria-hidden="true">↓</span></a><p class="feature-note">静岡県周智郡森町／非公式の見学特集<br>情報確認・特集更新：2026年10月26日</p></div><figure><img src="cover.svg" width="1200" height="630" fetchpriority="high" alt="{e(row['cover_alt'])}"><figcaption>{e(row['cover_caption'])}</figcaption></figure></header>
<nav class="feature-nav" aria-label="特集の目次"><a href="#essentials">日程・公式案内</a><a href="#schedule">行事予定</a><a href="#highlights">見どころ</a><a href="#train">電車</a><a href="#parking">駐車・規制</a><a href="#family">子連れ</a><a href="#plan">行程案</a><a href="#faq">よくある質問</a></nav>
<section id="essentials" class="feature-essentials"><p class="feature-kicker">まず押さえたいこと</p><h2>秋の3日間を、自分たちのペースで。</h2><div class="date-grid"><div><span>11月</span><strong>6 <small>金</small></strong><p>開催1日目</p></div><div><span>11月</span><strong>7 <small>土</small></strong><p>開催2日目</p></div><div><span>11月</span><strong>8 <small>日</small></strong><p>開催3日目</p></div></div><p class="date-source">日程の出典：<a href="{NOTICE}" target="_blank" rel="noopener" data-track-click="mori_festival_official">森町観光協会・2026年10月1日のお知らせ</a></p><div class="info-grid"><div class="confirmed"><span class="status-label">公式案内で確認済み</span><h3>無料の「見物心得帳」を手に入れる</h3><p>主な屋台の動きや見どころを載せた公式ガイド。森町役場・観光案内所で配布と案内されています。受取時間・在庫は事前にご確認ください。</p><a href="tel:0538856316">観光協会へ：0538-85-6316</a></div><div class="confirmed"><span class="status-label">当年の公式図を保存資料で確認</span><h3>駐車場・交通規制の確認先</h3><p>10月21日付の観光協会の図に、規制区域・時間と無料駐車場の位置があります。行事の出発時刻とは別です。10月23日取得資料を10月26日に照合。出発前に最新案内を確認してください。</p><a href="#traffic-guide">公式図の読み方・確認した注意事項へ →</a></div></div></section>
<section class="feature-essentials" id="schedule"><h2>2026年・主要行事の予定</h2><p>10月26日確認。観光協会の10月21日現在の案内と三島神社の当年行事表によります。時刻は変更される場合があります。</p><dl><dt><b>11月6日（金）</b></dt><dd>12:00 祭典開始宣言式・安全祈願祭（三島神社）／12:30頃 屋台清祓い</dd><dt><b>11月7日（土）</b></dt><dd>9:30 本祭／13:00 神幸祭／13:40 渡御出発（三島神社→金守神社）</dd><dt><b>11月8日（日）</b></dt><dd>12:00 還幸祭（金守神社）／12:30 還御出発／14:00頃 終祭／16:30 舞児還し式／18:00 舞児還し出発（三島神社）</dd></dl><p>到着目安は観光協会と神社で異なります。7日金守神社着は15:00／14:50頃、8日三島神社着は14:10／13:50頃。到着を確約する時刻ではありません。現地の進行を優先し、帰路に余裕を取ってください。</p><p>各屋台の経路・通過時刻や交通規制の時間割を示す表ではありません。<a href="#source-8">観光協会の予定</a>・<a href="#source-9">三島神社の詳細表</a>を出発前に確認してください。</p></section><div class="feature-reading"><div class="post-editorial-body">{''.join(contents)}</div>
<section class="visit-checklist" id="checklist"><p class="feature-kicker">出発前に、さっと確認</p><h2>家族で確認する4項目</h2><p>チェックはこの画面での確認用です。個人情報は入力しません。</p>{checklist}</section>
<section class="festival-faq" id="faq"><p class="feature-kicker">Q &amp; A</p><h2>よくある質問</h2>{faqhtml}</section>
<section class="feature-related"><h2>秋の森町を、もう少し楽しむ</h2><div class="related-grid"><a href="/blog/20261001-morimachi-jirogaki-chokubaijo/">次郎柿の直売所<span>販売時期・お店の探し方 →</span></a><a href="/discover/morimachi-wagashi-guide/">森町の和菓子<span>散策とお土産の楽しみ →</span></a><a href="/discover/enshu-mori-station/">遠州森駅のガイド<span>町へ入る交通の起点 →</span></a><a href="/events/annual-calendar/">森町の年間行事<span>ほかの季節にも出かける →</span></a></div></section>
<section class="official-sources" id="sources"><h2>公式情報・確認先</h2><p>2026年10月26日に確認。歴史資料は祭礼の説明に使用し、今年の日程には当年の案内を使用しています。本特集は主催者の公式サイトではありません。</p><ol>{links}</ol><p class="feature-note">編集：<a href="/about/author/">大石浩之</a>／初回ガイド公開：2026年8月10日／特集更新：2026年10月26日。公開情報の調査をもとに作成し、現地取材や2026年の開催風景を記録した記事ではありません。挿絵は編集用のイメージです。</p></section>
<aside class="festival-bottom-guide"><h2>帰省をきっかけに、実家のことも考えたら</h2><p>家族での情報共有や、家財・書類の整理から。まだ方針が決まっていない方も、確認する順番を調べられます。</p><a href="/life/housing/close-parents-house/" data-track-click="mori_festival_jikka">森町の実家を整理するガイド →</a><p class="feature-note">運営：富士ヶ丘サービス株式会社。相談サービスの案内はリンク先に掲載しています。</p></aside>
</div></article></main><!-- PART:footer:START -->{parts['footer']}<!-- PART:footer:END --></body></html>'''
