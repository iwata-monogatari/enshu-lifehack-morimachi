"""町外読者の3入口と既存記事の早見案内。本文・事実確認日は保持する。"""
import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATE = '2026-10-26'
CSS = '<link rel="stylesheet" href="/assets/outside-routes.css?v=20261026a">'

ROUTES = [
    ('visit', '🍵', '遊び・買い物に行く', '旬の直売所、参拝、交通から、森町で過ごす半日を組み立てる。'),
    ('family', '🏡', '森町に実家・親がいる', '帰省前の準備、親の相談、空き家の管理を、今の用事から選ぶ。'),
    ('move', '🌿', '移住・暮らしを考える', '通勤、買い物、学校、住まいを、家族の一週間に合わせて確かめる。'),
]

def link(href, title, note='', event='outside_article_click'):
    return (f'<a class="outside-card" href="{escape(href, quote=True)}" data-track-click="{event}">'
            f'<strong>{escape(title)}</strong><span>{escape(note)}</span><small aria-hidden="true">詳しく見る →</small></a>')

def home_section():
    cards = ''.join(link('/for/' + slug + '/', title, note, 'outside_' + slug + '_click')
                    .replace('<strong>', f'<strong><span aria-hidden="true">{icon}</span> ', 1)
                    for slug, icon, title, note in ROUTES)
    return ('<section class="outside-entry" aria-labelledby="outside-title"><p class="outside-kicker">町外から森町を調べている方へ</p>'
            '<h2 id="outside-title">森町で、何をしたいですか？</h2><div class="outside-grid">' + cards + '</div></section>')

def cards(items):
    return '<div class="outside-grid">' + ''.join(link(*item) for item in items) + '</div>'

def checklist(title, items):
    return '<section class="outside-check"><h2>' + title + '</h2><ul>' + ''.join('<li>' + x + '</li>' for x in items) + '</ul></section>'

def content(slug):
    if slug == 'visit':
        return ('<section><h2>まず、今回の目的を一つ選ぶ</h2>' + cards([
            ('/blog/20261001-morimachi-jirogaki-chokubaijo/', '秋の次郎柿を買う', '直売所3件の比較、店頭受取予約、地方発送の違いを確認。'),
            ('/discover/morimachi-autumn-leaves-townwide-guide/', '紅葉・参拝に出かける', '小國神社・大洞院の候補を比べ、撮影日付きの色づき情報へ。'),
            ('/discover/mori-festival/', '森のまつりを見に行く', '当年の開催案内、交通、子どもと見学するときの準備へ。'),
        ]) + '</section><section><h2>半日なら、主な目的地＋もう一か所</h2>' + cards([
            ('/discover/kotomachi-yokocho-complete-guide/', '参拝と食べ歩き', '小國神社とことまち横丁。徒歩でつなぐ範囲を先に決めます。'),
            ('/discover/morimachi-souvenir-guide/', '帰りにお土産を選ぶ', 'お茶・和菓子・農産物を、荷物と持ち帰り時間から選びます。'),
            ('/guide/access/', '車・電車・バスを選ぶ', '目的地ごとの最終区間と、帰りの便を先に確認します。'),
        ]) + '</section>' + checklist('出発前の4つの確認', [
            '買い物：販売日・必要な量・受取方法を確認。売切れ時の候補も一つ決める。',
            '車：目的地の駐車場と当日の交通規制を確認。通常時の所要時間に駐車待ちは含めない。',
            '電車・バス：訪問日の運行と帰りの便を確認。駅から目的地までの移動も予定に入れる。',
            '子ども・親と一緒：歩ける距離、休憩、トイレ、雨の場合の変更先を同行者と決める。',
        ]) + '<p class="outside-note">販売日・在庫・紅葉・運行状況は当日情報ではありません。各記事の確認日と、リンク先の最新案内をご覧ください。</p>')
    if slug == 'family':
        return ('<section><h2>今いちばん気になることから</h2>' + cards([
            ('/life/parents-care/community-support-center/', '親の暮らし・介護が心配', '森町の公的な相談窓口へ。困っている状況をメモして相談します。'),
            ('/vacant-house/management-cost/', '留守の家を管理したい', '草木、郵便、鍵、巡回、費用と緊急時の連絡先を整理。'),
            ('/inheritance/property-checklist/', '家・土地を引き継いだ', '家、農地、山林、名義、家財の確認順序を整理。'),
        ]) + '</section>' + checklist('帰省前に家族で共有するメモ', [
            '親の用事：本人の希望、今困っていること、普段の支援者と連絡先。',
            '家の用事：住所、所有者、鍵を持つ人、手元の課税明細・登記資料。分からない欄は空欄で構いません。',
            '今回の帰省：訪問先の予約、家族の立会い、持ち帰る書類、現地で確認する場所。',
            '帰省後：写真やメモを共有する相手、次の連絡日、急な不具合があった場合の連絡先。',
        ]) + '<section><h2>売るかどうかは、整理してから</h2><p>使う・貸す・保有する・売るという選択肢を、家族の希望と管理の負担から比べます。片付けや解体を発注する前に、残す資料と必要な確認を整理しましょう。</p>' + cards([
            ('/life/housing/clean-parents-house/', '片付けの前に確認する', '残す書類、家族の持ち物、処分する範囲を分けます。'),
            ('/life/housing/vacant-house/', '町の空き家バンクを調べる', '制度の対象、利用の流れ、町の窓口を確認。'),
            ('/life/housing/close-parents-house/', '実家の今後を具体的に考える', '帰省前の準備と、運営会社による任意の実家・売却相談の案内。'),
        ]) + '<p class="outside-note">実家じまいページの個別相談は富士ヶ丘サービス株式会社の民間サービスです。町の相談窓口とは別で、利用は任意です。</p></section>')
    return ('<section><h2>家探しの前に、一週間の暮らしを描く</h2>' + cards([
        ('/transport/commuting/', '毎日の通勤を確かめる', '磐田・袋井・掛川・浜松方面へ、平日の往復と代替手段を検討。'),
        ('/transport/car-free-life/', '車を使わない日の生活', '買い物・通院・送迎を、曜日と帰路まで含めて確認。'),
        ('/housing/districts/', '地区ごとの条件を比べる', '地区名だけで決めず、候補の住所から生活動線を確認。'),
    ]) + '</section><section><h2>候補の家が見つかったら</h2>' + cards([
        ('/life/education/school-zones/', '学校と通学を確認する', '住所から学区を確認し、通学路や送迎を検討。'),
        ('/housing/land-selection/', '土地・建物の確認項目', '道路、上下水道、改修と維持費を整理。'),
        ('/life/emergency/evacuation-hazard-map/', 'ハザードマップを確認する', '候補地と周囲の道路、避難先を重ねて確認。'),
    ]) + '</section>' + checklist('内見の日に持っていく確認メモ', [
        '通勤・通学：出発時刻、帰宅時刻、送迎の分担。平日の利用時間帯にも確かめる。',
        '生活：食料品の買い物、通院、車を使えない日の代わりの移動。',
        '住まい：購入費や家賃に加え、修繕、設備、庭や敷地を管理する負担。',
        '地域：自治会・地域行事の内容や負担を、候補地の窓口や関係者に聞く。',
    ]) + '<section><h2>制度と住まいの情報へ進む</h2>' + cards([
        ('/life/living-soon/about-morimachi/', '移住前の基本情報', '生活環境と、森町の移住相談の確認先。'),
        ('/life/housing/vacant-house/', '空き家バンクの利用', '希望する物件の状況と利用条件を確認。'),
        ('/fudosan/', '森町の住まいを探す', '運営会社の不動産情報。募集状況と個別条件を確認。'),
    ]) + '<p class="outside-note">不動産情報は富士ヶ丘サービス株式会社による民間の案内です。移住制度の利用に相談申込みは必要ありません。</p></section>')

SUMMARIES = {
    '/guide/access/': ('visit', '目的地に合わせて、入口と帰路を選ぶ', [
        ('小國神社へ', 'JR袋井駅・遠州森駅からの開運線を候補に。訪問日の運行と帰りの便を確認。'),
        ('森地区の町歩きへ', '遠州森駅を起点に、歩く範囲と買い物の荷物量を決める。'),
        ('車で出かける', '目的地公式の経路・駐車場を確認。紅葉や祭りの日は交通規制も見る。'),
    ]),
    '/discover/morimachi-autumn-leaves-townwide-guide/': ('visit', '紅葉は「撮影日」と「帰り方」から選ぶ', [
        ('色づきを知りたい', '過去の見頃だけで決めず、公式の写真に付いた撮影日を確認。'),
        ('車で見に行く', '小國神社・大洞院それぞれの道路と駐車案内を確認してから選ぶ。'),
        ('車なしで見に行く', 'まず一か所の往復を計画。帰りの便と徒歩区間を先に確認。'),
    ]),
    '/life/housing/close-parents-house/': ('family', '帰省前にできること、現地で確かめること', [
        ('帰省前', '住所・手元の書類・家族の希望を整理。鍵と立入りの許可、訪問予約を確認。'),
        ('現地で', '建物と敷地の状態、残す家財を記録。無理な立入りや処分はせず確認を優先。'),
        ('帰省後', '写真と未確認事項を家族で共有。管理を続ける場合と活用・売却する場合を比較。'),
    ]),
    '/life/parents-care/community-support-center/': ('family', '離れて暮らす家族が、相談前にまとめること', [
        ('本人のこと', '親の住所、本人の希望、今困っていること。分かる範囲で整理。'),
        ('暮らしのこと', '食事・買い物・通院など、具体的に気になる場面をメモ。'),
        ('家族のこと', '普段の支援者と連絡先、家族が訪問できる日を整理して窓口へ。'),
    ]),
    '/life/living-soon/about-morimachi/': ('move', '移住前に、住所ごとの暮らしを確かめる', [
        ('平日の移動', '通勤・通学・送迎を往復で確認。休日の内見だけで判断しない。'),
        ('日々の買い物・通院', '車を使わない日や、家族が送迎できない日の手段も確認。'),
        ('家と地域', '修繕・維持費、道路、災害リスク、地域行事を候補地ごとに確認。'),
    ]),
}

def render(slug, icon, title, lead):
    parts = {n: (ROOT / 'parts' / (n + '.html')).read_text(encoding='utf-8').strip() for n in ['header', 'footer', 'head-css']}
    others = ''.join(link('/for/' + s + '/', t, d) for s, i, t, d in ROUTES if s != slug)
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>静岡県森町｜{title}方へ | 森町ライフハック</title><meta name="description" content="静岡県周智郡森町へ町外から関わる方の案内。{lead}目的に合う既存ガイドと公式確認先へ進めます。">
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="canonical" href="https://morimachi.enshu-lifehack.com/for/{slug}/">
<!-- PART:head-css:START -->{parts['head-css']}<!-- PART:head-css:END -->{CSS}</head><body class="hub">
<!-- PART:header:START -->{parts['header']}<!-- PART:header:END --><main><div class="wrap outside-page">
<p class="breadcrumb"><a href="/">森町ライフハック</a> ／ 町外からのご利用</p><header class="outside-hero"><p class="outside-kicker"><span aria-hidden="true">{icon}</span> 静岡県周智郡森町</p><h1>{title}</h1><p class="lead">{lead}</p><p>町外に住む方も、近くの方も。今の用事に合う案内からお進みください。</p></header>
{content(slug)}<section><h2>ほかの目的で森町を調べる</h2><div class="outside-grid">{others}</div></section>
<p class="outside-note">案内の編集：2026年10月26日。制度・販売・交通の確認日は各記事に掲載しています。森町公式サイトではありません。</p>
</div></main><!-- PART:footer:START -->{parts['footer']}<!-- PART:footer:END --></body></html>'''

def main():
    for slug, icon, title, lead in ROUTES:
        path = ROOT / 'for' / slug / 'index.html'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render(slug, icon, title, lead), encoding='utf-8')
    for route, (slug, title, rows) in SUMMARIES.items():
        path = ROOT / route.strip('/') / 'index.html'
        src = path.read_text(encoding='utf-8')
        src = re.sub(r'<!-- OUTSIDE-QUICK:START -->.*?<!-- OUTSIDE-QUICK:END -->', '', src, flags=re.S)
        body = '<aside class="outside-quick" aria-label="記事の早見案内"><p class="outside-summary-title"><strong>' + title + '</strong></p><dl>'
        body += ''.join('<div><dt>' + k + '</dt><dd>' + v + '</dd></div>' for k, v in rows)
        body += '</dl><a href="/for/' + slug + '/" data-track-click="outside_related_click">目的別のガイドも見る →</a><p class="outside-note">早見案内の編集：2026年10月26日。各情報の確認日・出典は本文をご覧ください。</p></aside>'
        heading_end = src.find('</h1>')
        if heading_end < 0:
            raise ValueError('Missing H1: ' + route)
        # Put the summary after the complete hero, outside its image/title grid.
        opening = list(re.finditer(r'<(section|header) class="(?:hero|mj-hero|article-header)"[^>]*>', src[:heading_end]))
        if not opening:
            raise ValueError('Missing article header: ' + route)
        outer = opening[-1]
        tag = outer.group(1)
        depth = 0
        insertion = None
        for match in re.finditer(r'</?' + tag + r'\b[^>]*>', src[outer.start():]):
            depth += -1 if match[0].startswith('</') else 1
            if depth == 0:
                insertion = outer.start() + match.end()
                break
        if insertion is None:
            raise ValueError('Unclosed article header: ' + route)
        src = src[:insertion] + '<!-- OUTSIDE-QUICK:START -->' + body + '<!-- OUTSIDE-QUICK:END -->' + src[insertion:]
        if CSS not in src:
            src = src.replace('</head>', CSS + '</head>', 1)
        path.write_text(src, encoding='utf-8')
    # The persimmon guide already has a verified comparison and detailed jump links.
    # Add a choice of buying methods without inventing fresh stock or opening data.
    path = ROOT / 'blog/20261001-morimachi-jirogaki-chokubaijo/index.html'
    src = re.sub(r'<!-- OUTSIDE-BUY:START -->.*?<!-- OUTSIDE-BUY:END -->', '', path.read_text(encoding='utf-8'), flags=re.S)
    block = '<!-- OUTSIDE-BUY:START --><section class="outside-quick"><h2>町外から買うなら、受け取り方を先に選ぶ</h2><div class="outside-grid">' + ''.join([
        link('#jiro-shops', '店頭で選びたい', '直売所3件の販売期・場所を比較。出発前に入荷を確認。'),
        link('#jiro-reservation', '取り置き・発送を頼みたい', '店頭受取と地方発送の受付条件を分けて確認。'),
        link('/for/visit/', '買い物と外出を組み合わせたい', '交通・参拝・お土産の案内から、半日の行程を考える。'),
    ]) + '</div><p class="outside-note">案内の編集：2026年10月26日。販売情報の確認日は下の比較表に記載しています。</p></section><!-- OUTSIDE-BUY:END -->'
    marker = '<h2 id="jiro-shops">'
    assert marker in src
    src = src.replace(marker, block + marker, 1)
    if CSS not in src:
        src = src.replace('</head>', CSS + '</head>', 1)
    path.write_text(src, encoding='utf-8')
    print('町外向け3入口・既存6記事の早見案内を生成')

if __name__ == '__main__':
    main()
