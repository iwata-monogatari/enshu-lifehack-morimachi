#!/usr/bin/env python3
"""/temple/ 配下を静的生成する（01計画書②）。

  /temple/                  トップ
  /temple/temples/          全寺院一覧
  /temple/temples/<slug>/   個別（35ページ）
  /temple/areas/<district>/ 地区別（6ページ・神社DBと共通の区分）
  /temple/sects/<slug>/     宗派別（5ページ）
  /temple/guide/            法要・帰省・実家じまいのガイド
  /temple/about/            出典・編集方針・免責・修正依頼

01計画書2-5の「意図的な簡素化」に従い、軸は地区別・宗派別の2つだけにする。
34ヶ寺で磐田版（118件・6軸）を真似ると中身のない空箱になるため。
掲示板・写真投稿・admin などの Functions 系は作らない。

使い方: python scripts/generate_temple_pages.py
"""
import html
import json
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS_DIR = os.path.join(ROOT, "parts")
OUT = os.path.join(ROOT, "temple")
SITE = "https://morimachi.enshu-lifehack.com"
SITE_NAME = "森町ライフハック"
VERIFIED = "2026-08-04"

SECT_SLUG = {"曹洞宗": "soto", "日蓮宗": "nichiren", "真言宗": "shingon", "天台宗": "tendai", "浄土宗": "jodo"}
SECT_DESC = {
    "曹洞宗": "森町の寺院の8割近くを占める。中山間地の集落ごとに末寺が置かれた歴史を映している。",
    "日蓮宗": "向天方と飯田に1ヶ寺ずつ。",
    "真言宗": "御室派と智山派が1ヶ寺ずつ。金剛院の山門は町の文化財に指定されている。",
    "天台宗": "森と一宮に1ヶ寺ずつ。",
    "浄土宗": "一宮に1ヶ寺。",
}


def esc(s):
    return html.escape(str(s), quote=True)


def load_parts():
    p = {}
    for n in ("head-css", "header", "disclaimer", "footer"):
        with open(os.path.join(PARTS_DIR, "%s.html" % n), encoding="utf-8") as f:
            p[n] = f.read().strip()
    return p


def part(name, content):
    return "<!-- PART:%s:START -->%s<!-- PART:%s:END -->" % (name, content, name)


def shell(path, emoji, title, lead, body, parts, crumbs):
    url = SITE + path
    return (
        '<!doctype html><html lang="ja"><head>\n'
        '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
        "<title>%s | %s</title>\n"
        '<meta name="description" content="%s">\n'
        '<link rel="canonical" href="%s">\n'
        '<meta property="og:type" content="website"><meta property="og:site_name" content="%s">'
        '<meta property="og:title" content="%s"><meta property="og:description" content="%s">'
        '<meta property="og:url" content="%s"><meta name="twitter:card" content="summary">\n'
        '<link rel="icon" href="/favicon.svg" type="image/svg+xml">\n'
        "%s\n</head><body>\n%s\n%s\n"
        '<main id="main"><div class="wrap">\n'
        '<p class="breadcrumb">%s</p>\n'
        '<section class="hero"><div class="hero-visual"><h1><span aria-hidden="true">%s</span> %s</h1></div>'
        '<div class="hero-body"><p class="lead">%s</p></div></section>\n%s\n'
        '<p class="verified">最終確認日：%s ／ 本ページは公表情報を整理したものです。'
        "各寺院の公式サイトではありません。記載の誤りは"
        '<a href="/temple/about/">修正依頼</a>からお知らせください。</p>\n'
        "</div></main>\n%s\n</body></html>\n"
    ) % (
        esc(title), SITE_NAME, esc(lead), url, SITE_NAME, esc(title), esc(lead), url,
        part("head-css", parts["head-css"]), part("header", parts["header"]),
        part("disclaimer", parts["disclaimer"]),
        " ／ ".join(crumbs), emoji, esc(title), esc(lead), body, VERIFIED,
        part("footer", parts["footer"]),
    )


def write(rel, content):
    p = os.path.join(OUT, rel, "index.html") if rel else os.path.join(OUT, "index.html")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def card(t):
    bits = [esc(t["sect"])]
    if t.get("area"):
        bits.append(esc(t["area"]))
    if t.get("cultural_property"):
        bits.append("町指定文化財")
    return (
        '<a class="shrine-item" href="/temple/temples/%s/">'
        '<span class="shrine-name">%s</span>'
        '<span class="shrine-meta">%s</span></a>' % (t["slug"], esc(t["name"]), " ／ ".join(bits))
    )


def main():
    parts = load_parts()
    with open(os.path.join(ROOT, "data", "temples.json"), encoding="utf-8-sig") as f:
        temples = json.load(f)["temples"]
    with open(os.path.join(ROOT, "data", "shrine-districts.json"), encoding="utf-8-sig") as f:
        districts = json.load(f)["districts"]
    dmeta = {d["district_id"]: d for d in districts}

    by_d, by_s = defaultdict(list), defaultdict(list)
    for t in temples:
        if t["district_id"]:
            by_d[t["district_id"]].append(t)
        by_s[t["sect"]].append(t)

    generated = []

    # ---- 個別 -------------------------------------------------------------
    for t in temples:
        rows = []
        rows.append('<div class="ih-row"><span class="ih-key">宗派</span><span class="ih-val"><a href="/temple/sects/%s/">%s</a>（%s）</span></div>'
                    % (SECT_SLUG.get(t["sect"], "other"), esc(t["sect"]), esc(t["sect_full"])))
        rows.append('<div class="ih-row"><span class="ih-key">所在地</span><span class="ih-val">%s</span></div>' % esc(t["address"]))
        if t["district_id"]:
            d = dmeta[t["district_id"]]
            rows.append('<div class="ih-row"><span class="ih-key">地区</span><span class="ih-val"><a href="/temple/areas/%s/">%s</a></span></div>' % (d["slug"], esc(d["name"])))
        rows.append('<div class="ih-row"><span class="ih-key">法人格</span><span class="ih-val">%s</span></div>' % esc(t["corporate_status"]))
        if t.get("cultural_property"):
            rows.append('<div class="ih-row"><span class="ih-key">文化財</span><span class="ih-val">%s</span></div>' % esc(t["cultural_property"]))
        rows.append('<div class="ih-row"><span class="ih-key">本尊</span><span class="ih-val">%s</span></div>' % esc(t["main_deity"]))
        rows.append('<div class="ih-row"><span class="ih-key">現地確認</span><span class="ih-val">%s</span></div>' % esc(t["visit_status"]))

        body = ['<aside class="instant-header" aria-label="基本情報"><p class="ih-title">基本情報</p>%s</aside>' % "".join(rows)]
        if t.get("history_summary"):
            body.append('<div class="note">%s</div>' % esc(t["history_summary"]))
        body.append('<p class="mini">本尊・御朱印・拝観の可否などは確認できていません。'
                    "推測で書かない方針のため「未確認」と表示しています。現地確認のうえ順次更新します。</p>")

        if t["district_id"]:
            same = [x for x in by_d[t["district_id"]] if x["slug"] != t["slug"]]
            if same:
                body.append('<h2 class="sec">%s地区のほかの寺院</h2><div class="shrine-list">%s</div>'
                            % (esc(dmeta[t["district_id"]]["name"]), "".join(card(x) for x in same[:12])))

        body.append('<h2 class="sec">出典</h2><ul class="post-sources">')
        for s in t["sources"]:
            body.append('<li><a href="%s" target="_blank" rel="noopener">%s</a>（%s）</li>' % (esc(s["url"]), esc(s["title"]), esc(s["note"])))
        body.append("</ul>")

        addr_short = (t.get("address") or "").replace("静岡県周智郡森町", "森町") or (
            "森町%s" % (t.get("area") or ""))
        lead = "%s（%s）は、%sにある%sの寺院です。" % (t["name"], t["sect"], addr_short, t["sect"])
        if t.get("oldest_building"):
            lead += "本堂は元禄9年（1696年）建立で、森町の寺院建築では最古の記録とされています。"
        generated.append(write("temples/%s" % t["slug"], shell(
            "/temple/temples/%s/" % t["slug"], "🛕", t["name"], lead, "".join(body), parts,
            ['<a href="/">%s</a>' % SITE_NAME, '<a href="/temple/">森町の寺院</a>',
             '<a href="/temple/temples/">寺院一覧</a>', esc(t["name"])])))

    # ---- 一覧 -------------------------------------------------------------
    generated.append(write("temples", shell(
        "/temple/temples/", "📜", "森町の寺院一覧",
        "静岡県周智郡森町（遠州森町）の寺院%dヶ寺の一覧です。宗教法人名簿と森町公式資料をもとにしています。" % len(temples),
        '<div class="shrine-list">%s</div>' % "".join(card(t) for t in temples), parts,
        ['<a href="/">%s</a>' % SITE_NAME, '<a href="/temple/">森町の寺院</a>', "寺院一覧"])))

    # ---- 地区別 -----------------------------------------------------------
    for d in districts:
        lst = by_d.get(d["district_id"], [])
        body = ['<div class="note">%s</div>' % esc(d["description"])]
        body.append('<p class="mini"><b>旧町村</b>：%s（%s）／<b>含まれる大字</b>：%s</p>' % (esc(d["former_village"]), esc(d["merged"]), esc("・".join(d["oaza"]))))
        body.append('<h2 class="sec">この地区の寺院（%dヶ寺）</h2><div class="shrine-list">%s</div>' % (len(lst), "".join(card(t) for t in lst)))
        body.append('<h2 class="sec">この地区の神社</h2><p class="mini"><a href="/shrine/areas/%s/">%s地区の神社を見る</a></p>' % (d["slug"], esc(d["name"])))
        body.append('<h2 class="sec">ほかの地区</h2><div class="action-grid">%s</div>'
                    % "".join('<a class="btn" href="/temple/areas/%s/">%s（%dヶ寺）</a>' % (o["slug"], esc(o["name"]), len(by_d.get(o["district_id"], []))) for o in districts if o["district_id"] != d["district_id"]))
        generated.append(write("areas/%s" % d["slug"], shell(
            "/temple/areas/%s/" % d["slug"], "🗺️", "%s地区の寺院" % d["name"],
            "静岡県周智郡森町%s地区（%s）の寺院%dヶ寺をまとめています。%s" % (d["name"], d["former_village"], len(lst), d["summary"]),
            "".join(body), parts,
            ['<a href="/">%s</a>' % SITE_NAME, '<a href="/temple/">森町の寺院</a>', "%s地区" % esc(d["name"])])))

    # ---- 宗派別 -----------------------------------------------------------
    for sect, slug in SECT_SLUG.items():
        lst = by_s.get(sect, [])
        if not lst:
            continue
        body = ['<div class="note">%s</div>' % esc(SECT_DESC.get(sect, ""))]
        body.append('<h2 class="sec">%sの寺院（%dヶ寺）</h2><div class="shrine-list">%s</div>' % (esc(sect), len(lst), "".join(card(t) for t in lst)))
        body.append('<h2 class="sec">ほかの宗派</h2><div class="action-grid">%s</div>'
                    % "".join('<a class="btn" href="/temple/sects/%s/">%s（%dヶ寺）</a>' % (SECT_SLUG[o], esc(o), len(by_s.get(o, []))) for o in SECT_SLUG if o != sect and by_s.get(o)))
        generated.append(write("sects/%s" % slug, shell(
            "/temple/sects/%s/" % slug, "🔖", "%sの寺院（森町）" % sect,
            "静岡県周智郡森町の%sの寺院%dヶ寺です。%s" % (sect, len(lst), SECT_DESC.get(sect, "")),
            "".join(body), parts,
            ['<a href="/">%s</a>' % SITE_NAME, '<a href="/temple/">森町の寺院</a>', esc(sect)])))

    # ---- ガイド -----------------------------------------------------------
    guide = (
        '<div class="note">お寺との関わりは、法事のときだけでなく「実家をどうするか」を考える場面でも出てきます。'
        "ここでは森町で実際に起きやすい順に整理しています。</div>"
        '<h2 class="sec">遠方に住んでいて、法要で年に一度帰る</h2>'
        "<p>菩提寺との付き合いは続いているが、実家は普段だれも住んでいない——森町でよくある形です。"
        "帰省のたびに家の傷みが進んでいると感じたら、次の帰省までにできることを決めておくと動きやすくなります。</p>"
        '<div class="action-grid">'
        '<a class="btn" href="/life/housing/vacant-house/">空き家の管理を確認する</a>'
        '<a class="btn" href="/life/end-of-life/inherited-house/">相続した家をどうするか</a></div>'
        '<h2 class="sec">実家じまいと墓じまいをどの順で考えるか</h2>'
        "<p>家と墓は別の話なので、片方だけ先に進めても構いません。"
        "ただし親族の合意はどちらも必要です。菩提寺への相談は早いほど選択肢が残ります。</p>"
        '<div class="action-grid">'
        '<a class="btn" href="/life/end-of-life/grave-memorial/">お墓・供養のこと</a>'
        '<a class="btn" href="/life/housing/clean-parents-house/">実家の片づけを進める</a></div>'
        '<h2 class="sec">農地や山林が一緒についてくる場合</h2>'
        "<p>森町では実家に農地や山林が付いていることが珍しくありません。"
        "宅地とは手続きが別で、農地は相続後の届出に期限があります。</p>"
        '<div class="action-grid">'
        '<a class="btn" href="/life/troubles-consult/farmland/inheritance/">農地の相続手続き</a>'
        '<a class="btn" href="/life/troubles-consult/farmland/sell-or-rent/">農地を売る・貸す</a></div>'
        '<h2 class="sec">お寺の建物を見に行くなら</h2>'
        "<p>森町の寺院建築では、三倉の栄泉寺本堂（元禄9年・1696年）が最も古い記録として町の資料に挙げられています。"
        "真言宗御室派の金剛院は山門が町の文化財に指定されています。"
        "いずれも信仰の場です。参拝の作法と、撮影の可否の確認をお願いします。</p>"
        '<div class="action-grid">'
        '<a class="btn" href="/temple/temples/">寺院一覧を見る</a>'
        '<a class="btn" href="/shrine/festivals/">神社の祭礼カレンダー</a></div>'
    )
    generated.append(write("guide", shell(
        "/temple/guide/", "🧭", "法要・帰省・実家じまいのガイド",
        "静岡県周智郡森町の菩提寺との関わりと、実家じまい・墓じまい・農地の承継をどの順に考えるかを整理しています。",
        guide, parts,
        ['<a href="/">%s</a>' % SITE_NAME, '<a href="/temple/">森町の寺院</a>', "ガイド"])))

    # ---- about ------------------------------------------------------------
    n_corp = sum(1 for t in temples if t["corporate_status"] == "宗教法人")
    about = (
        '<h2 class="sec">このデータベースについて</h2>'
        "<p>静岡県周智郡森町（遠州森町）の寺院を、公表されている資料から整理したものです。</p>"
        '<h2 class="sec">出典</h2><ul class="post-sources">'
        '<li><a href="https://www.pref.shizuoka.jp/_res/projects/default_project/_page_/001/083/677/meibo4.pdf" target="_blank" rel="noopener">静岡県知事所轄宗教法人名簿（令和5年3月31日現在）</a>'
        "／法人名・包括団体・所在地。各寺院のページに参照ページと行番号を記録しています。</li>"
        '<li><a href="https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/shakaikyoikuka/bunkashinkogakari/2/774.html" target="_blank" rel="noopener">森町教育委員会「46 森町の寺院建築」</a>'
        "／宗派内訳・建立年・文化財。</li></ul>"
        '<h2 class="sec">2つの資料の食い違いについて</h2>'
        "<p>宗教法人名簿に載る森町の仏教法人は<strong>%d件</strong>で、宗派の内訳"
        "（曹洞宗27・日蓮宗2・真言宗2・天台宗2・浄土宗1）は森町公式の記載と完全に一致しました。</p>"
        "<p>ただし森町公式の記事が名前を挙げている21ヶ寺のうち<strong>陽向院</strong>だけは、"
        "宗教法人名簿に該当する法人を確認できませんでした。逆に、法人名簿にある14ヶ寺は"
        "森町公式の記事（建立年の記録がある寺を扱うもの）には名前が出てきません。</p>"
        "<p>2つの資料は数えている対象が違うため、<strong>どちらかを消さずに両方を残し</strong>、"
        "陽向院は法人格「未確認」として掲載しています。現地確認のうえ更新します。</p>"
        '<h2 class="sec">編集方針</h2><ul class="post-summary">'
        "<li><strong>推測で埋めません。</strong>本尊・御朱印・拝観可否など確認できていない項目は「未確認」と表示します。</li>"
        "<li><strong>他サイトの文章を転載しません。</strong>説明文は公表された事実項目から自分で書いています。</li>"
        "<li><strong>出典に参照位置を残します。</strong>名簿PDFはページ・行番号まで記録しています。</li>"
        "<li><strong>写真は自前撮影または権利確認済みのものだけ</strong>を使います。</li></ul>"
        '<h2 class="sec">本サイトは公式ではありません</h2>'
        "<p>森町ライフハックは森町公式サイトではなく、<strong>各寺院の公式サイトでもありません</strong>。"
        "法要・墓地・拝観などのお問い合わせは各寺院へ直接お願いします。</p>"
        '<h2 class="sec">修正依頼・情報提供</h2>'
        "<p>記載内容の誤り、掲載の取り下げのご要望、情報のご提供は下記へご連絡ください。"
        "寺院関係者の方からのご指摘は最優先で対応します。</p>"
        '<div class="official"><p class="mini"><b>運営</b>：富士ヶ丘サービス株式会社（静岡県磐田市見付5789番地1）</p>'
        '<p class="mini"><b>電話</b>：0538-31-3308</p>'
        '<a class="official-link" href="tel:0538-31-3308" data-track-click="tel_tap">電話する <span>0538-31-3308</span></a>'
        '<a class="official-link" href="/about/author/">運営者・執筆者について</a></div>'
    ) % n_corp
    generated.append(write("about", shell(
        "/temple/about/", "📋", "このデータベースについて（森町の寺院）",
        "森町の寺院データベースの出典・2つの資料の食い違い・編集方針・修正依頼の窓口をまとめています。",
        about, parts,
        ['<a href="/">%s</a>' % SITE_NAME, '<a href="/temple/">森町の寺院</a>', "このデータベースについて"])))

    # ---- トップ -----------------------------------------------------------
    sc = Counter(t["sect"] for t in temples)
    dc = Counter(t["district_id"] for t in temples)
    top = ['<div class="note">森町の寺院は<strong>%dヶ寺</strong>です。'
           "宗教法人名簿の仏教法人34件に、町公式資料にのみ名前がある1ヶ寺を加えています。"
           "曹洞宗が全体の約8割を占めるのが森町の特徴です。</div>" % len(temples)]
    top.append('<div class="action-grid">'
               '<a class="btn" href="/temple/temples/">寺院一覧（%dヶ寺）</a>'
               '<a class="btn" href="/temple/guide/">法要・実家じまいのガイド</a>'
               '<a class="btn" href="/temple/about/">出典・編集方針</a></div>' % len(temples))
    top.append('<h2 class="sec">宗派から探す</h2><div class="action-grid">%s</div>'
               % "".join('<a class="btn" href="/temple/sects/%s/">%s（%dヶ寺）</a>' % (SECT_SLUG[s], esc(s), sc.get(s, 0)) for s in SECT_SLUG if sc.get(s)))
    top.append('<h2 class="sec">地区から探す</h2><div class="action-grid">%s</div>'
               % "".join('<a class="btn" href="/temple/areas/%s/">%s（%dヶ寺）</a>' % (d["slug"], esc(d["name"]), dc.get(d["district_id"], 0)) for d in districts))
    top.append('<h2 class="sec">森町の寺院の特徴</h2><div class="grid">'
               '<div class="card real-card"><h3><span aria-hidden="true">🏯</span> 町内最古は三倉・栄泉寺本堂</h3>'
               "<p>元禄9年（1696年）建立。森町の寺院建築で最も古い記録として町の資料に挙げられています。</p></div>"
               '<div class="card real-card"><h3><span aria-hidden="true">⛩️</span> 金剛院の山門は町指定文化財</h3>'
               "<p>三倉にある真言宗御室派の寺院。山門が町の文化財に指定されています。</p></div>"
               '<div class="card real-card"><h3><span aria-hidden="true">📿</span> 曹洞宗が約8割</h3>'
               "<p>34法人のうち27が曹洞宗。集落ごとに末寺が置かれた歴史が、いまの分布に残っています。</p></div></div>")
    top.append('<h2 class="sec">暮らしのページとあわせて</h2><div class="action-grid">'
               '<a class="btn" href="/life/end-of-life/">人生の終わり</a>'
               '<a class="btn" href="/life/housing/clean-parents-house/">実家を片づける</a>'
               '<a class="btn" href="/shrine/">森町の神社</a></div>')
    generated.append(write("", shell(
        "/temple/", "🛕", "森町の寺院",
        "静岡県周智郡森町（遠州森町）の寺院%dヶ寺を、宗派別・地区別に整理したデータベースです。出典は宗教法人名簿と森町公式資料。" % len(temples),
        "".join(top), parts,
        ['<a href="/">%s</a>' % SITE_NAME, "森町の寺院"])))

    print("生成 %d ページ" % len(generated))
    print("  寺院 %d / 宗派 %d / 地区 %d" % (len(temples), len([s for s in SECT_SLUG if by_s.get(s)]), len(districts)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
