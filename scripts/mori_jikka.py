"""遠方家族の入口。既存URLと共通部品を維持して生成する。"""
from html import escape
from urllib.parse import urlencode

HUB = '/life/housing/close-parents-house/'
CAMPAIGN = 'mori_jikka_20261018'

def url(entry, intent='organize', sample=False):
    query = urlencode(dict(area='森町', intent=intent, utm_source='morimachi_lifehack',
                           utm_medium='referral', utm_campaign=CAMPAIGN, utm_content=entry))
    return 'https://fudosan.atawi.link/karte/' + ('sample/' if sample else '') + '?' + query + ('' if sample else '#apply')

def link(entry, label, intent='organize', sample=False, secondary=False):
    kind = 'sample' if sample else intent
    return f'<a class="mj-button{" mj-secondary" if secondary else ""}" href="{escape(url(entry, intent, sample), quote=True)}" data-track-click="mori_jikka_{kind}_click">{label}</a>'

def disclosure():
    return '<p class="mj-note">富士ヶ丘サービス株式会社の民間サービスです。森町役場の窓口ではありません。申込みだけで売却依頼・媒介契約にはなりません。</p>'

def home_entry():
    return f'''<section class="mj-home" aria-labelledby="mj-home-title"><p class="mj-eyebrow"><span aria-hidden="true">🏡</span> 森町に実家がある、町外のご家族へ</p><h2 id="mj-home-title">遠くにある実家。帰省前から、次の一歩を整理できます。</h2><p>家財が残っている・相続がまだ・農地もある。今の状況から進め方を確認できます。</p><div class="mj-actions"><a class="mj-button" href="{HUB}" data-track-click="mori_jikka_hub_click">実家じまいの進め方を見る</a>{link('home_sale', '売却を相談したい方はこちら', 'sale', secondary=True)}</div><p class="mj-note">相談対応：富士ヶ丘サービス株式会社（磐田市見付・森町へ出張対応）</p></section>'''

def sale_entry():
    return f'''<section class="mj-panel" aria-labelledby="mj-sale-title"><p class="mj-eyebrow">森町の家・土地を売りたい方へ</p><h2 id="mj-sale-title">売却相談・現地確認の希望を、そのまま担当者へ。</h2><p>家財あり・相続登記前・遠方在住でも相談できます。まず町名と連絡先で受け付け、現地確認の方法や日程は初回連絡で相談します。</p><div class="mj-actions">{link('sell_top', '森町の実家・土地の売却を相談する', 'sale')}<a class="mj-button mj-secondary" href="tel:0538313308" data-track-click="mori_jikka_phone_click">電話で相談する</a></div><p class="mj-note">受付9〜18時（水曜・日曜は予約制）／仲介専門・自社買取なし</p>{disclosure()}</section>'''

def render(item):
    title = '森町の実家じまい｜遠方の家族の片付け・相続・売却相談'
    desc = '静岡県森町に実家がある遠方のご家族へ。帰省前にできる準備、家財・名義・農地の確認、家族で決める順序を案内。売却未定の実家カルテと、売却・現地確認の相談を状況に合わせて選べます。'
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} | 森町ライフハック</title><meta name="description" content="{desc}"><link rel="canonical" href="https://morimachi.enshu-lifehack.com{HUB}"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><!-- PART:head-css:START --><link rel="stylesheet" href="/assets/site.css?v=20260702"><!-- PART:head-css:END --><link rel="stylesheet" href="/assets/mori-jikka.css?v=20261018"></head><body>
<!-- PART:header:START --><!-- PART:header:END --><!-- PART:disclaimer:START --><!-- PART:disclaimer:END -->
<main class="mj-guide"><div class="wrap"><p class="breadcrumb"><a href="/">森町ライフハック</a> ／ <a href="/hub/property/">家・土地</a> ／ 実家じまい</p>
<section class="mj-hero"><p class="mj-eyebrow"><span aria-hidden="true">🏡</span> 静岡県周智郡森町に実家があるご家族へ</p><h1>森町の実家じまい。<br>遠くにいても、相談は今の状況から。</h1><p class="mj-lead">家財が残っている。名義が分からない。農地や山林もある。<br>帰省前にできることと、現地で確認することを一緒に整理します。</p><div class="mj-actions">{link('hub_top', '無料で実家カルテを依頼する')}{link('hub_sample', '届くカルテの見本を見る', sample=True, secondary=True)}</div><p class="mj-note">価格の目安・確認点・次にすることをまとめた資料です。売るか迷っている段階でも依頼できます。</p>{disclosure()}</section>
<nav class="mj-toc" aria-label="実家じまいの案内"><a href="#choose">今の状況から選ぶ</a><a href="#prepare">帰省前の準備</a><a href="#support">任せられること</a><a href="#after">申込み後の流れ</a><a href="#official">町の制度・窓口</a></nav>
<section id="choose"><h2 class="sec">今の状況に近い方から進めます</h2><div class="mj-grid"><article class="mj-card"><span class="mj-step">01 ／ まだ迷っている</span><h3>家族で判断する材料をそろえたい</h3><p>使う・貸す・売る・保有する場合の確認点を整理します。まずは分かる範囲で構いません。</p>{link('hub_organize', '無料で実家カルテを依頼する')}</article><article class="mj-card mj-sale"><span class="mj-step">02 ／ 売却を考えている</span><h3>価格や現地確認を相談したい</h3><p>売却相談として受け付けます。物件の状況、ご希望の時期、現地確認の進め方を伺います。</p>{link('hub_sale', '森町の実家の売却を相談する', 'sale')}<p class="mj-note"><a href="/fudosan/sell/">仲介の流れ・費用を詳しく見る</a></p></article></div></section>
<section id="prepare"><h2 class="sec">帰省前に、分かるところから3つだけ</h2><ol class="mj-steps"><li><h3>家と土地を特定する</h3><p>住所・町名、固定資産税の課税明細、手元の登記資料を確認。家と一緒に田畑・山林がないかも見ます。書類がそろわなくても相談できます。</p></li><li><h3>家族の希望と、分からないことを分ける</h3><p>所有者は誰か、使う人がいるか、誰が連絡窓口になるかをメモします。家族で結論が出ていなくても、その状況をお伝えください。</p></li><li><h3>片付けや解体の発注前に、進め方を確認する</h3><p>残す資料や思い出の品、家財処分の範囲、補助の条件を確認。売り方を比べてから、必要な費用と手順を考えます。</p></li></ol><div class="mj-reading"><a href="/life/housing/clean-parents-house/">家財の片付け</a><a href="/life/end-of-life/inherited-house/">相続した家の選択肢</a><a href="/life/troubles-consult/farmland/inheritance/">農地も引き継ぐ場合</a><a href="/vacant-house/management-cost/">空き家の管理と維持費</a><a href="/temple/guide/">法要・帰省と実家の整理</a></div></section>
<section id="support"><h2 class="sec">遠方のご家族と、現地で進める役割</h2><div class="mj-grid"><article class="mj-card"><h3>富士ヶ丘サービスへ相談できること</h3><ul><li>価格の目安と、登記・道路・境界などの確認順序</li><li>森町への訪問、建物・敷地・家財の現地確認</li><li>現況のまま売るか、片付けてから売るかの比較</li><li>媒介契約後の買主募集、内覧対応、条件調整</li></ul></article><article class="mj-card"><h3>初回連絡で一緒に決めること</h3><ul><li>所有者との関係、家族の意向、ご希望の時期</li><li>鍵・立入りの許可、現地確認の日程と方法</li><li>必要な資料と、結果を家族で共有する方法</li><li>専門家へ確認する内容と、別途見積もる費用</li></ul></article></div><p>帰省や立会いが必要かどうかは、物件と手続きに応じて確認します。農地・山林、未登記建物、共有名義などは住宅だけで判断しません。</p><p>担当：大石浩之（代表取締役・宅地建物取引士）。富士ヶ丘サービス株式会社は磐田市見付から森町へ出張対応します。<a href="/about/author/">運営者・担当者について</a></p></section>
<section id="after"><h2 class="sec">申込み後に何が起きるか</h2><ol class="mj-steps"><li><h3>ご希望の方法で初回連絡</h3><p>メールか電話を選べます。原則2営業日以内に連絡し、住所・相談の希望・必要資料を確認します。水曜・日曜・臨時休業日は営業日に含みません。</p></li><li><h3>確認できたことと未確認点を整理</h3><p>カルテは必要な情報と送付先がそろった日の翌々日までに、メールまたはLINEでお送りします（土日も数えます）。価格の目安を出せない場合は、その理由を説明します。</p></li><li><h3>ご希望に応じて次の予定を決める</h3><p>売却相談の方は現地確認・価格提案へ。検討中の方は家族で共有し、次の連絡時期も相談して決めます。申込みだけで売却を依頼したことにはなりません。</p></li></ol><div class="mj-panel"><h3>無料の範囲と、別途費用</h3><p>実家カルテ、机上の価格目安、標準的な資料取得、カルテ作成に必要な現地確認・訪問査定・役所確認は無料です。登記・測量・家財処分など専門家の実務費は、事前見積もりを確認してから進めます。売却仲介の費用は媒介契約の前に説明します。</p><div class="mj-actions">{link('hub_bottom', '無料で実家カルテを依頼する')}{link('hub_bottom_sale', '売却・現地確認を相談する', 'sale', secondary=True)}</div>{disclosure()}</div></section>
<section id="official"><h2 class="sec">森町の制度・窓口も確認できます</h2><p>町の空き家・空き地バンクは物件情報を提供する制度です。町は交渉・契約の仲介や物件管理を行いません。登録の条件や補助の対象は、着手前に町へ確認してください。</p><p>森町役場 定住推進課 移住交流係：<a href="tel:0538856321">0538-85-6321</a></p><div class="mj-reading"><a href="https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/teijusuishinka/ijukoryugakari/2/2/379.html">森町空き家・空き地バンク（公式）</a><a href="https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/teijusuishinka/ijukoryugakari/2/2/3043akiyakazaisyobun.html">空き家の家財処分・改修に関する補助（公式）</a><a href="/life/housing/vacant-house/">空き家バンクの利用ガイド</a></div><p class="verified">最終確認日：2026-10-18 ／ 制度・申請の条件は公式窓口でご確認ください。</p></section>
<section><h2 class="sec">よくある質問</h2><details><summary>売ると決めていなくても相談できますか</summary><p>できます。実家カルテで価格の目安・確認点・次の対応を整理してから、家族でご検討ください。</p></details><details><summary>片付けや相続登記が終わっていません</summary><p>その状態から相談できます。先に確認する資料と、専門家へ依頼する内容を整理します。売却の手続きに必要な準備は個別に確認します。</p></details><details><summary>現地に一度も行かずに売れますか</summary><p>一律には約束できません。所有者の意思確認、本人確認、鍵や書類、契約・決済の方法などを確認し、帰省の負担を減らす進め方を相談します。</p></details></section>
<section class="feedback-box" id="feedback"><h2 class="sec">これで解決しそうですか？</h2><p class="mini">反応はページ改善のために使います。このボタンではお名前や連絡先を取得しません。</p><div class="fb-actions"><button type="button" class="fb-btn" data-feedback="solved">解決しそう</button><button type="button" class="fb-btn" data-feedback="still_worried">まだ不安</button><button type="button" class="fb-btn" data-feedback="could_not_find">探している情報がなかった</button></div><p class="fb-thanks">ありがとうございました。今後のページ改善に役立てます。</p></section>
</div></main><!-- PART:footer:START --><!-- PART:footer:END --></body></html>'''
