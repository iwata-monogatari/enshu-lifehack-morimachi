"""Reader-first routes shared by the blog index and the final build pass."""
import re
from html import escape
from mori_jikka import url

LABELS = {'outings': '季節のお出かけ', 'living': '森町で暮らす', 'family': '親・実家・空き家'}
SAFE = re.compile(r'救急|避難|警報|熱中症|防火|防犯|生活困窮|納税.*困|患者|健診|医療|健康|予防接種|認知症|障害|就学援助')

def group(post):
    title = post['title']
    if re.search(r'次郎柿|治郎柿|とうもろこし|直売|紅葉|花火|桜|祭り|まつり', title):
        return 'outings'
    if re.search(r'実家|空き家|相続|売却|境界|接道|農地転用|山林を', title):
        return 'family'
    return {'wed': 'outings', 'sat': 'outings', 'tue': 'family', 'thu': 'living'}.get(post.get('axis'), 'living')

def link(href, label, event, primary=False):
    return f'<a class="mg-link{" mg-primary" if primary else ""}" href="{escape(href, quote=True)}" data-track-click="{event}">{escape(label)}</a>'

def owner_card(entry='growth_owner'):
    return ('<aside class="mg-next" data-mori-topic="family" aria-label="実家・空き家の次の確認">'
            '<p class="mg-kicker">実家・空き家のことを、もう少し具体的に</p>'
            '<h3>売るか決める前に、家族で判断する材料を。</h3>'
            '<p>道路・境界・名義など、確認できたことと次に調べることを実家カルテにまとめます。作成は無料。売却未定でも利用できます。</p>'
            '<div class="mg-actions">' + link(url(entry, sample=True), '届くカルテの見本を見る', 'mori_growth_sample_click', True)
            + link(url(entry), '自分の実家について相談する', 'mori_growth_apply_click') + '</div>'
            '<p class="mg-note">本サイト運営会社・富士ヶ丘サービス株式会社の民間サービスです。森町役場とは関係ありません。申込みだけで売却依頼にはなりません。</p></aside>')

def next_reading(post):
    kind, title = group(post), post['title']
    if SAFE.search(title):
        return ('<aside class="mg-next" data-mori-topic="living"><h3>必要な手続き・相談先を確認する</h3>'
                '<p>状況に近い項目から、公的な窓口と確認する順番を探せます。</p>'
                + link('/#search-title', '森町の手続き・窓口を探す', 'mori_growth_related_living', True) + '</aside>')
    if kind == 'family':
        return owner_card('growth_blog')
    if kind == 'outings':
        return ('<aside class="mg-next" data-mori-topic="outings"><h3>次のお出かけも、森町で。</h3>'
                '<p>季節の楽しみと、地区ごとの暮らしを続けて調べられます。</p><div class="mg-actions">'
                + link('/blog/#outings', '季節のお出かけ記事を探す', 'mori_growth_related_outings', True)
                + link('/housing/districts/', '六つの地区の暮らしを知る', 'mori_growth_related_living') + '</div></aside>')
    if re.search(r'移住|二地域|二拠点|住宅|住まい|家を買|通勤|駅|交通|バス|生活圏|地区', title):
        return ('<aside class="mg-next" data-mori-topic="living"><h3>森町で暮らす場所を、生活の動きから。</h3>'
                '<p>通勤・買い物・通院を地区ごとに確認してから、住宅の候補を見てみましょう。</p><div class="mg-actions">'
                + link('/housing/districts/', '地区ごとの暮らしを比べる', 'mori_growth_related_living', True)
                + link('/fudosan/buy/', '募集中の中古住宅を見る', 'mori_growth_buy_click') + '</div></aside>')
    return ('<aside class="mg-next" data-mori-topic="living"><h3>暮らしの疑問を、ひとつずつ。</h3>'
            + link('/blog/#living', '森町で暮らす記事を探す', 'mori_growth_related_living', True) + '</aside>')

def index_intro():
    cards = [
        ('outings', '🍊', '季節のお出かけ', '行く日・買う場所・移動を先に確認。', [
            ('/blog/20261001-morimachi-jirogaki-chokubaijo/', '次郎柿の直売所・予約・発送'),
            ('/discover/mori-festival/', '森のまつりの見学・交通'),
            ('/events/annual-calendar/', '森町の年間行事')]),
        ('living', '🌳', '森町で暮らす', '地区の生活環境から、住まい選びへ。', [
            ('/housing/districts/', '六つの地区の住宅事情'),
            ('/life/living-soon/about-morimachi/', '移住前に確認すること'),
            ('/fudosan/buy/', '募集中の中古住宅を見る')]),
        ('family', '🏡', '親・実家・空き家', '片付け・管理・相続を、決める前から整理。', [
            ('/life/housing/close-parents-house/', '遠方から進める実家じまい'),
            ('/life/housing/vacant-house/', '空き家バンクの利用と注意点'),
            ('/life/housing/clean-parents-house/', '片付ける前に残す資料')])]
    result = '<section class="mg-start" aria-labelledby="mg-start-title"><h2 id="mg-start-title">何を調べたいですか</h2><div class="mg-grid">'
    for key, icon, title, desc, links in cards:
        result += f'<section class="mg-topic"><h3><span aria-hidden="true">{icon}</span> {title}</h3><p>{desc}</p><ul>'
        for href, label in links:
            result += '<li>' + link(href, label, 'mori_growth_index_' + key) + '</li>'
        result += f'</ul><a href="#{key}" class="mg-filter-link">このテーマの記事を探す <span aria-hidden="true">↓</span></a></section>'
    return result + '</div></section><span id="outings"></span><span id="living"></span><span id="family"></span><span id="all"></span>'
