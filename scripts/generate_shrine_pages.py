#!/usr/bin/env python3
"""/shrine/ 配下を静的生成する（01計画書③）。

  /shrine/                    トップ（件数・地区/系統導線）
  /shrine/shrines/            全神社一覧
  /shrine/shrines/<slug>/     個別（39ページ）
  /shrine/areas/<district>/   地区別（6ページ）
  /shrine/systems/<system>/   系統別
  /shrine/festivals/          祭礼カレンダー（森町版の目玉）
  /shrine/about/              出典・編集方針・免責・修正依頼

Astroは持ち込まない（01計画書の最重要技術判断）。既存の静的生成方式で作る。
共通パーツは <!-- PART:xxx --> マーカーで埋め、inject_parts.py の対象にする。

由緒本文は転載しない。説明文はデータの事実項目から組み立てる。

使い方: python scripts/generate_shrine_pages.py
"""
import html
import json
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS_DIR = os.path.join(ROOT, "parts")
OUT = os.path.join(ROOT, "shrine")
SITE = "https://morimachi.enshu-lifehack.com"
SITE_NAME = "森町ライフハック"
VERIFIED = "2026-08-04"

MONTHS = ["", "1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]


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
    crumb = " ／ ".join(crumbs)
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
        "各神社の公式サイトではありません。記載の誤りは"
        '<a href="/shrine/about/">修正依頼</a>からお知らせください。</p>\n'
        "</div></main>\n%s\n</body></html>\n"
    ) % (
        esc(title), SITE_NAME, esc(lead), url, SITE_NAME, esc(title), esc(lead), url,
        part("head-css", parts["head-css"]), part("header", parts["header"]),
        part("disclaimer", parts["disclaimer"]),
        crumb, emoji, esc(title), esc(lead), body, VERIFIED,
        part("footer", parts["footer"]),
    )


def write(rel, content):
    p = os.path.join(OUT, rel, "index.html") if rel else os.path.join(OUT, "index.html")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def shrine_card(s):
    bits = []
    if s.get("area"):
        bits.append(esc(s["area"]))
    if s.get("saijin"):
        bits.append("御祭神：" + esc("・".join(s["saijin"][:3])))
    return (
        '<a class="shrine-item" href="/shrine/shrines/%s/">'
        '<span class="shrine-name">%s</span>'
        '<span class="shrine-kana">%s</span>'
        '<span class="shrine-meta">%s</span></a>'
        % (s["slug"], esc(s["name"]), esc(s["name_kana"]), " ／ ".join(bits))
    )


def main():
    parts = load_parts()
    with open(os.path.join(ROOT, "data", "shrines.json"), encoding="utf-8-sig") as f:
        shrines = json.load(f)["shrines"]
    with open(os.path.join(ROOT, "data", "shrine-districts.json"), encoding="utf-8-sig") as f:
        districts = json.load(f)["districts"]
    with open(os.path.join(ROOT, "data", "festivals.json"), encoding="utf-8-sig") as f:
        fest = json.load(f)

    sys_meta = {}
    exec_globals = {}
    # 系統定義は build_shrines.py と重複させず、そこから読み込む
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    from build_shrines import SYSTEMS  # noqa: E402

    for s in SYSTEMS:
        sys_meta[s["id"]] = s

    by_district = defaultdict(list)
    by_system = defaultdict(list)
    for s in shrines:
        by_district[s["district_id"]].append(s)
        by_system[s["system"]].append(s)

    generated = []
    dmeta = {d["district_id"]: d for d in districts}

    # ---- 個別ページ -------------------------------------------------------
    fest_by_shrine = defaultdict(list)
    for f_ in fest["festivals"]:
        fest_by_shrine[f_["shrine_slug"]].append(f_)
    desig = {d["id"]: d for d in fest["designations"]}

    name_counts = Counter(x["name"] for x in shrines)

    for s in shrines:
        d = dmeta.get(s["district_id"])
        rows = []
        rows.append('<div class="ih-row"><span class="ih-key">よみ</span><span class="ih-val">%s</span></div>' % esc(s["name_kana"]))
        if s.get("tsusho"):
            rows.append('<div class="ih-row"><span class="ih-key">通称</span><span class="ih-val">%s</span></div>' % esc(s["tsusho"]))
        rows.append('<div class="ih-row"><span class="ih-key">鎮座地</span><span class="ih-val">%s</span></div>' % esc(s["address"]))
        if d:
            rows.append('<div class="ih-row"><span class="ih-key">地区</span><span class="ih-val"><a href="/shrine/areas/%s/">%s</a></span></div>' % (d["slug"], esc(d["name"])))
        rows.append('<div class="ih-row"><span class="ih-key">系統</span><span class="ih-val"><a href="/shrine/systems/%s/">%s</a></span></div>' % (s["system"], esc(sys_meta[s["system"]]["label"])))
        if s.get("saijin"):
            rows.append('<div class="ih-row"><span class="ih-key">御祭神</span><span class="ih-val">%s</span></div>' % esc("・".join(s["saijin"])))
        if s.get("tel"):
            rows.append('<div class="ih-row"><span class="ih-key">電話</span><span class="ih-val"><a href="tel:%s" data-track-click="tel_tap">%s</a></span></div>' % (esc(s["tel"]), esc(s["tel"])))
        if s.get("official_url"):
            rows.append('<div class="ih-row"><span class="ih-key">公式サイト</span><span class="ih-val"><a href="%s" target="_blank" rel="noopener">%s</a></span></div>' % (esc(s["official_url"]), esc(s["official_url"])))

        body = ['<aside class="instant-header" aria-label="基本情報"><p class="ih-title">基本情報</p>%s</aside>' % "".join(rows)]

        fl = fest_by_shrine.get(s["slug"], [])
        if fl:
            body.append('<h2 class="sec">祭礼</h2><div class="official">')
            for f_ in fl:
                tag = ""
                if f_.get("designation_id"):
                    dg = desig[f_["designation_id"]]
                    tag = '<span class="fest-badge">%s「%s」</span>' % (esc(dg["category"]), esc(dg["name"]))
                elif f_.get("designation_note"):
                    tag = '<span class="fest-badge">%s</span>' % esc(f_["designation_note"])
                body.append('<p class="mini"><b>%s</b>：%s %s<br>%s</p>' % (esc(f_["name"]), esc(f_["date_label"]), tag, esc(f_["summary"])))
            body.append('</div><p class="mini"><a href="/shrine/festivals/">森町の祭礼カレンダーを見る</a></p>')

        same = [x for x in by_district[s["district_id"]] if x["slug"] != s["slug"]]
        if same:
            body.append('<h2 class="sec">%s地区のほかの神社</h2><div class="shrine-list">%s</div>'
                        % (esc(dmeta[s["district_id"]]["name"]), "".join(shrine_card(x) for x in same[:12])))

        body.append('<h2 class="sec">出典</h2><ul class="post-sources">')
        for src in s["sources"]:
            body.append('<li><a href="%s" target="_blank" rel="noopener">%s</a>（%s）</li>' % (esc(src["url"]), esc(src["title"]), esc(src.get("note", ""))))
        body.append("</ul>")
        body.append('<p class="mini">本ページは静岡県神社庁の掲載情報から、社名・鎮座地・御祭神・祭礼日などの事実項目を整理したものです。由緒の本文は転載していません。</p>')

        # 森町には同名の神社が複数ある（八幡神社5社・神明神社3社など）。
        # title と description が重複しないよう、鎮座地まで含めて区別する。
        addr_short = (s.get("address") or "").replace("静岡県周智郡森町", "森町")
        lead = "%s（%s）は、%sに鎮座する神社です。" % (s["name"], s["name_kana"], addr_short)
        if s.get("saijin"):
            lead += "御祭神は%s。" % "・".join(s["saijin"])
        generated.append(write("shrines/%s" % s["slug"], shell(
            "/shrine/shrines/%s/" % s["slug"], "⛩️",
            ("%s（%s）｜%s" % (s["name"], s["name_kana"], addr_short)
             if name_counts[s["name"]] > 1 else "%s（%s）" % (s["name"], s["name_kana"])), lead,
            "".join(body), parts,
            ['<a href="/">%s</a>' % SITE_NAME, '<a href="/shrine/">森町の神社</a>',
             '<a href="/shrine/shrines/">神社一覧</a>', esc(s["name"])])))

    # ---- 一覧 -------------------------------------------------------------
    listing = ['<div class="shrine-list">%s</div>' % "".join(shrine_card(s) for s in shrines)]
    generated.append(write("shrines", shell(
        "/shrine/shrines/", "📜", "森町の神社一覧",
        "静岡県神社庁に掲載されている静岡県周智郡森町（遠州森町）の神社%d社の一覧です。読み仮名の五十音順に並べています。" % len(shrines),
        "".join(listing), parts,
        ['<a href="/">%s</a>' % SITE_NAME, '<a href="/shrine/">森町の神社</a>', "神社一覧"])))

    # ---- 地区別 -----------------------------------------------------------
    for d in districts:
        lst = by_district.get(d["district_id"], [])
        body = ['<div class="note">%s</div>' % esc(d["description"])]
        body.append('<p class="mini"><b>旧町村</b>：%s（%s）／<b>含まれる大字</b>：%s</p>' % (esc(d["former_village"]), esc(d["merged"]), esc("・".join(d["oaza"]))))
        body.append('<h2 class="sec">この地区の神社（%d社）</h2><div class="shrine-list">%s</div>' % (len(lst), "".join(shrine_card(s) for s in lst)))
        body.append('<h2 class="sec">ほかの地区</h2><div class="action-grid">%s</div>'
                    % "".join('<a class="btn" href="/shrine/areas/%s/">%s（%d社）</a>' % (o["slug"], esc(o["name"]), len(by_district.get(o["district_id"], []))) for o in districts if o["district_id"] != d["district_id"]))
        generated.append(write("areas/%s" % d["slug"], shell(
            "/shrine/areas/%s/" % d["slug"], "🗺️", "%s地区の神社" % d["name"],
            "静岡県周智郡森町%s地区（%s）の神社%d社をまとめています。%s" % (d["name"], d["former_village"], len(lst), d["summary"]),
            "".join(body), parts,
            ['<a href="/">%s</a>' % SITE_NAME, '<a href="/shrine/">森町の神社</a>', "%s地区" % esc(d["name"])])))

    # ---- 系統別 -----------------------------------------------------------
    for sy in SYSTEMS:
        lst = by_system.get(sy["id"], [])
        if not lst:
            continue
        body = ['<div class="note">%s</div>' % esc(sy["desc"])]
        body.append('<h2 class="sec">この系統の神社（%d社）</h2><div class="shrine-list">%s</div>' % (len(lst), "".join(shrine_card(s) for s in lst)))
        body.append('<p class="mini">系統は社名と御祭神から整理したものです。学術的な分類として確定したものではありません。</p>')
        body.append('<h2 class="sec">ほかの系統</h2><div class="action-grid">%s</div>'
                    % "".join('<a class="btn" href="/shrine/systems/%s/">%s（%d社）</a>' % (o["id"], esc(o["label"]), len(by_system.get(o["id"], []))) for o in SYSTEMS if o["id"] != sy["id"] and by_system.get(o["id"])))
        generated.append(write("systems/%s" % sy["id"], shell(
            "/shrine/systems/%s/" % sy["id"], "🔖", "%sの神社" % sy["label"],
            "静岡県周智郡森町の神社のうち、%sに分類した%d社です。%s" % (sy["label"], len(lst), sy["desc"]),
            "".join(body), parts,
            ['<a href="/">%s</a>' % SITE_NAME, '<a href="/shrine/">森町の神社</a>', esc(sy["label"])])))

    # ---- 祭礼カレンダー ---------------------------------------------------
    by_month = defaultdict(list)
    for f_ in fest["festivals"]:
        by_month[f_["month"]].append(f_)
    body = []
    dg = fest["designations"][0]
    body.append('<div class="note"><b>%s「%s」</b>（%s指定）<br>%s の舞楽が<strong>3社まとめて1件</strong>として指定されています。%s</div>'
                % (esc(dg["category"]), esc(dg["name"]), esc(dg["designated_on"]), esc("・".join(dg["shrines"])), esc(dg["note"])))
    body.append('<h2 class="sec">月別</h2><div class="timeline">')
    for m in range(1, 13):
        if not by_month.get(m):
            continue
        body.append('<section class="timeline-item"><div class="timeline-head"><span class="timeline-emoji" aria-hidden="true">🎏</span><div><span class="timeline-age">%s</span><h2>%s</h2></div></div>' % (MONTHS[m], MONTHS[m]))
        for f_ in by_month[m]:
            badge = ""
            if f_.get("designation_id"):
                badge = '<span class="fest-badge">%s</span>' % esc(desig[f_["designation_id"]]["category"])
            elif f_.get("designation_note"):
                badge = '<span class="fest-badge">%s</span>' % esc(f_["designation_note"])
            body.append('<p><b>%s</b>　%s %s<br>%s<br><a href="/shrine/shrines/%s/">%s のページ</a></p>'
                        % (esc(f_["name"]), esc(f_["date_label"]), badge, esc(f_["summary"]), f_["shrine_slug"], esc(f_["shrine_name"])))
        body.append("</section>")
    body.append("</div>")
    body.append('<h2 class="sec">見学するときに気をつけること</h2><ul class="post-summary">'
                "<li>祭礼は地域の方が担う神事です。撮影や立ち入りの可否は現地の案内に従ってください。</li>"
                "<li>日程は年によって変わります。出かける前に各神社・森町の公式情報で必ず確認してください。</li>"
                "<li>駐車場が用意されない祭礼もあります。近隣の生活道路をふさがないようご注意ください。</li></ul>")
    body.append('<h2 class="sec">出典</h2><ul class="post-sources">')
    seen = set()
    for f_ in fest["festivals"]:
        u = f_["source"]["url"]
        if u in seen:
            continue
        seen.add(u)
        body.append('<li><a href="%s" target="_blank" rel="noopener">%s</a>（%s確認）</li>' % (esc(u), esc(f_["source"]["title"]), esc(f_["source"]["checked"])))
    body.append('<li><a href="%s" target="_blank" rel="noopener">%s</a>（%s確認）</li>' % (esc(dg["source"]["url"]), esc(dg["source"]["title"]), esc(dg["source"]["checked"])))
    body.append("</ul>")
    generated.append(write("festivals", shell(
        "/shrine/festivals/", "🎏", "森町の祭礼カレンダー",
        "静岡県周智郡森町（遠州森町）の主な祭礼を月別にまとめています。小國神社・天宮神社・山名神社の舞楽は「遠江森町の舞楽」として国の重要無形民俗文化財に指定されています。",
        "".join(body), parts,
        ['<a href="/">%s</a>' % SITE_NAME, '<a href="/shrine/">森町の神社</a>', "祭礼カレンダー"])))

    # ---- about ------------------------------------------------------------
    about = (
        '<h2 class="sec">このデータベースについて</h2>'
        "<p>静岡県周智郡森町（遠州森町）の神社を、公表されている情報から整理したものです。"
        "静岡県神社庁の掲載社を出発点にしています。</p>"
        '<h2 class="sec">出典</h2><ul class="post-sources">'
        '<li><a href="http://www.shizuoka-jinjacho.or.jp/shokai/search.php?mode=city&amp;city=33" target="_blank" rel="noopener">静岡県神社庁 神社紹介 周智郡森町</a>（社名・鎮座地・御祭神・祭礼日）</li>'
        '<li><a href="https://online.bunka.go.jp/heritages/detail/199756" target="_blank" rel="noopener">遠江森町の舞楽／文化遺産オンライン（文化庁）</a>（文化財指定）</li>'
        '<li><a href="https://www.town.morimachi.shizuoka.jp/" target="_blank" rel="noopener">静岡県森町 公式サイト</a>（祭礼・地区）</li>'
        "</ul>"
        '<h2 class="sec">編集方針</h2><ul class="post-summary">'
        "<li><strong>由緒の本文は転載しません。</strong>神社庁や各神社の文章は著作物です。本サイトが載せるのは社名・鎮座地・御祭神・祭礼日などの事実項目で、説明文は自分で書いています。</li>"
        "<li><strong>確認できないことは書きません。</strong>文化財の指定は、文化庁・静岡県・森町の一次資料で裏を取れたものだけを「指定」と書いています。</li>"
        "<li><strong>系統分類は目安です。</strong>社名と御祭神から整理したもので、学術的に確定した分類ではありません。</li>"
        "<li><strong>写真は自前撮影または権利確認済みのものだけ</strong>を使います。</li>"
        "</ul>"
        '<h2 class="sec">本サイトは公式ではありません</h2>'
        "<p>森町ライフハックは森町公式サイトではなく、<strong>各神社の公式サイトでもありません</strong>。"
        "参拝・祭礼・御朱印などの最新の取り扱いは、各神社または森町公式にご確認ください。</p>"
        '<h2 class="sec">修正依頼・情報提供</h2>'
        "<p>記載内容の誤り、掲載の取り下げのご要望、情報のご提供は、下記へご連絡ください。"
        "神社関係者の方からのご指摘は最優先で対応します。</p>"
        '<div class="official"><p class="mini"><b>運営</b>：富士ヶ丘サービス株式会社（静岡県磐田市見付5789番地1）</p>'
        '<p class="mini"><b>電話</b>：0538-31-3308</p>'
        '<a class="official-link" href="tel:0538-31-3308" data-track-click="tel_tap">電話する <span>0538-31-3308</span></a>'
        '<a class="official-link" href="/about/author/">運営者・執筆者について</a></div>'
    )
    generated.append(write("about", shell(
        "/shrine/about/", "📋", "このデータベースについて（森町の神社）",
        "森町の神社データベースの出典・編集方針・免責・修正依頼の窓口をまとめています。",
        about, parts,
        ['<a href="/">%s</a>' % SITE_NAME, '<a href="/shrine/">森町の神社</a>', "このデータベースについて"])))

    # ---- トップ -----------------------------------------------------------
    dcount = Counter(s["district_id"] for s in shrines)
    scount = Counter(s["system"] for s in shrines)
    top = []
    top.append('<div class="note">静岡県神社庁に掲載されている森町の神社は<strong>%d社</strong>です。'
               "神社庁に加盟していない社や境内社は含まれていないため、町内の神社がこれで全部というわけではありません。</div>" % len(shrines))
    top.append('<div class="action-grid">'
               '<a class="btn" href="/shrine/shrines/">神社一覧（%d社）</a>'
               '<a class="btn" href="/shrine/festivals/">祭礼カレンダー</a>'
               '<a class="btn" href="/shrine/about/">出典・編集方針</a></div>' % len(shrines))
    top.append('<h2 class="sec">地区から探す</h2><div class="action-grid">%s</div>'
               % "".join('<a class="btn" href="/shrine/areas/%s/">%s（%d社）</a>' % (d["slug"], esc(d["name"]), dcount.get(d["district_id"], 0)) for d in districts))
    top.append('<h2 class="sec">系統から探す</h2><div class="action-grid">%s</div>'
               % "".join('<a class="btn" href="/shrine/systems/%s/">%s（%d社）</a>' % (sy["id"], esc(sy["label"]), scount.get(sy["id"], 0)) for sy in SYSTEMS if scount.get(sy["id"])))
    top.append('<h2 class="sec">森町の神社の特徴</h2><div class="grid">'
               '<div class="card real-card"><h3><span aria-hidden="true">⛩️</span> 遠江国一宮・小國神社</h3>'
               "<p>森町の神社を語るときの中心。例祭は4月18日で、十二段舞楽が奉奏されます。</p></div>"
               '<div class="card real-card"><h3><span aria-hidden="true">🎏</span> 国指定の舞楽が3社</h3>'
               "<p>小國神社・天宮神社・山名神社の舞楽は「遠江森町の舞楽」として、3社まとめて国の重要無形民俗文化財に指定されています。</p></div>"
               '<div class="card real-card"><h3><span aria-hidden="true">🏔️</span> 山あいに小社が点在</h3>'
               "<p>三倉・天方など中山間地には集落ごとに小さな社があります。八幡・神明が数のうえでは多数を占めます。</p></div></div>")
    top.append('<h2 class="sec">暮らしのページとあわせて</h2><div class="action-grid">'
               '<a class="btn" href="/life/play-out/">遊ぶ・使う・出かける</a>'
               '<a class="btn" href="/life/end-of-life/">人生の終わり</a>'
               '<a class="btn" href="/tools/life-timeline/">ライフイベント・タイムライン</a></div>')
    generated.append(write("", shell(
        "/shrine/", "⛩️", "森町の神社",
        "静岡県周智郡森町（遠州森町）の神社%d社を、地区別・系統別に整理したデータベースです。祭礼カレンダーもあります。" % len(shrines),
        "".join(top), parts,
        ['<a href="/">%s</a>' % SITE_NAME, "森町の神社"])))

    print("生成 %d ページ" % len(generated))
    print("  神社 %d / 地区 %d / 系統 %d / 祭礼 %d 件"
          % (len(shrines), len(districts), len([s for s in SYSTEMS if by_system.get(s["id"])]), len(fest["festivals"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
