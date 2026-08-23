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
VERIFIED = "2026-08-10"

from sacred_research import research_figure, shrine_research  # noqa: E402

DEEP_RESEARCH_EXCLUDED = {"s4410001", "s4410002", "s4410003"}

SHRINE_PHOTO_SHOWCASE = '''<section class="sacred-showcase" aria-labelledby="shrine-photo-showcase-title"><h2 class="sec" id="shrine-photo-showcase-title">写真で見る森町の神社</h2><p class="sacred-showcase-intro">提供写真のある神社を、詳細ページとは別の境内写真で紹介します。写真を選ぶと各神社の所在地、祭神、参拝前の確認事項を読めます。</p><div class="sacred-showcase-grid">
<article class="sacred-showcase-card"><a href="/shrine/shrines/s4410001/"><span class="sacred-showcase-photos"><img src="/shrine/shrines/s4410001/oguni-showcase-precinct-1200.webp" srcset="/shrine/shrines/s4410001/oguni-showcase-precinct-480.webp 480w, /shrine/shrines/s4410001/oguni-showcase-precinct-800.webp 800w, /shrine/shrines/s4410001/oguni-showcase-precinct-1200.webp 1200w" sizes="(max-width:720px) 50vw, 440px" alt="小國神社の境内と拝殿を参道脇から望む写真" width="1200" height="900" loading="lazy" decoding="async"><img src="/shrine/shrines/s4410001/oguni-showcase-bridge-1200.webp" srcset="/shrine/shrines/s4410001/oguni-showcase-bridge-480.webp 480w, /shrine/shrines/s4410001/oguni-showcase-bridge-800.webp 800w, /shrine/shrines/s4410001/oguni-showcase-bridge-1200.webp 1200w" sizes="(max-width:720px) 50vw, 440px" alt="小國神社の事待池に架かる朱色の橋" width="1200" height="900" loading="lazy" decoding="async"></span><span class="sacred-showcase-copy"><span class="sacred-showcase-area">一宮</span><strong>小國神社</strong><span>鎮守の森に囲まれた境内と、事待池の橋の風景から紹介します。</span></span></a></article>
<article class="sacred-showcase-card"><a href="/shrine/shrines/s4410002/"><span class="sacred-showcase-photos"><img src="/shrine/shrines/s4410002/amenomiya-showcase-tree-1200.webp" srcset="/shrine/shrines/s4410002/amenomiya-showcase-tree-480.webp 480w, /shrine/shrines/s4410002/amenomiya-showcase-tree-800.webp 800w, /shrine/shrines/s4410002/amenomiya-showcase-tree-1200.webp 1200w" sizes="(max-width:720px) 50vw, 440px" alt="天宮神社の境内に立つ大きな御神木と赤い鳥居" width="1200" height="900" loading="lazy" decoding="async"><img src="/shrine/shrines/s4410002/amenomiya-showcase-chozuya-1200.webp" srcset="/shrine/shrines/s4410002/amenomiya-showcase-chozuya-480.webp 480w, /shrine/shrines/s4410002/amenomiya-showcase-chozuya-800.webp 800w, /shrine/shrines/s4410002/amenomiya-showcase-chozuya-1200.webp 1200w" sizes="(max-width:720px) 50vw, 440px" alt="天宮神社境内の手水舎" width="1200" height="900" loading="lazy" decoding="async"></span><span class="sacred-showcase-copy"><span class="sacred-showcase-area">天宮</span><strong>天宮神社</strong><span>御神木のある境内と手水舎を、参拝の動線に沿う写真で紹介します。</span></span></a></article>
<article class="sacred-showcase-card"><a href="/shrine/shrines/s4410003/"><span class="sacred-showcase-photos"><img src="/shrine/shrines/s4410003/yamana-showcase-precinct-1200.webp" srcset="/shrine/shrines/s4410003/yamana-showcase-precinct-480.webp 480w, /shrine/shrines/s4410003/yamana-showcase-precinct-800.webp 800w, /shrine/shrines/s4410003/yamana-showcase-precinct-1200.webp 1200w" sizes="(max-width:720px) 50vw, 440px" alt="山名神社の社殿と境内を広く望む写真" width="1200" height="900" loading="lazy" decoding="async"><img src="/shrine/shrines/s4410003/yamana-showcase-stage-1200.webp" srcset="/shrine/shrines/s4410003/yamana-showcase-stage-480.webp 480w, /shrine/shrines/s4410003/yamana-showcase-stage-800.webp 800w, /shrine/shrines/s4410003/yamana-showcase-stage-1200.webp 1200w" sizes="(max-width:720px) 50vw, 440px" alt="山名神社の舞楽が奉納される舞殿" width="1200" height="900" loading="lazy" decoding="async"></span><span class="sacred-showcase-copy"><span class="sacred-showcase-area">飯田</span><strong>山名神社</strong><span>社殿を囲む境内と舞殿を、異なる位置から見た写真で紹介します。</span></span></a></article>
<article class="sacred-showcase-card"><a href="/shrine/shrines/s4410008/"><span class="sacred-showcase-photos"><img src="/shrine/shrines/s4410008/kine-showcase-torii-view-1200.webp" srcset="/shrine/shrines/s4410008/kine-showcase-torii-view-480.webp 480w, /shrine/shrines/s4410008/kine-showcase-torii-view-800.webp 800w, /shrine/shrines/s4410008/kine-showcase-torii-view-1200.webp 1200w" sizes="(max-width:720px) 50vw, 440px" alt="許禰神社の社殿側から鳥居と参道を望む写真" width="1200" height="900" loading="lazy" decoding="async"><img src="/shrine/shrines/s4410008/kine-showcase-village-entrance-1200.webp" srcset="/shrine/shrines/s4410008/kine-showcase-village-entrance-480.webp 480w, /shrine/shrines/s4410008/kine-showcase-village-entrance-800.webp 800w, /shrine/shrines/s4410008/kine-showcase-village-entrance-1200.webp 1200w" sizes="(max-width:720px) 50vw, 440px" alt="三倉の集落に面した許禰神社入口と社号標" width="1200" height="900" loading="lazy" decoding="async"></span><span class="sacred-showcase-copy"><span class="sacred-showcase-area">三倉</span><strong>許禰神社</strong><span>社殿から望む参道と、三倉の集落に面した入口を紹介します。</span></span></a></article>
</div></section>'''


def protected_phase1_urls():
    """人手で全面改稿したフェーズ1ページをDB再生成から守る。"""
    manifest = os.path.join(ROOT, "data", "seo-phase1-publication.json")
    if not os.path.isfile(manifest):
        return set()
    with open(manifest, encoding="utf-8") as f:
        rows = json.load(f)
    return {
        row["url"] for row in rows
        if row.get("decision") == "EXPAND_EXISTING" and row.get("url", "").startswith("/shrine/")
    }


PROTECTED_PHASE1 = protected_phase1_urls()

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
    page_title = "静岡県森町の神社39社｜写真・所在地・祭神から探す" if path == "/shrine/shrines/" else "%s | %s" % (title, SITE_NAME)
    og_image = (SITE + "/shrine/shrines/s4410001/oguni-shrine-main-hall.jpg") if path == "/shrine/shrines/" else ""
    og_image_meta = '<meta property="og:image" content="%s">' % og_image if og_image else ""
    twitter_card = "summary_large_image" if og_image else "summary"
    return (
        '<!doctype html><html lang="ja"><head>\n'
        '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
        "<title>%s</title>\n"
        '<meta name="description" content="%s">\n'
        '<link rel="canonical" href="%s">\n'
        '<meta property="og:type" content="website"><meta property="og:site_name" content="%s">'
        '<meta property="og:title" content="%s"><meta property="og:description" content="%s">'
        '<meta property="og:url" content="%s">%s<meta name="twitter:card" content="%s">\n'
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
        esc(page_title), esc(lead), url, SITE_NAME, esc(page_title), esc(lead), url, og_image_meta, twitter_card,
        part("head-css", parts["head-css"]), part("header", parts["header"]),
        part("disclaimer", parts["disclaimer"]),
        crumb, emoji, esc(title), esc(lead), body, VERIFIED,
        part("footer", parts["footer"]),
    )


def write(rel, content):
    url = "/shrine/" + (rel.strip("/") + "/" if rel else "")
    if url in PROTECTED_PHASE1 and os.path.isfile(os.path.join(OUT, rel, "index.html")):
        return os.path.join("shrine", rel, "index.html").replace(os.sep, "/") + " (phase1 preserved)"
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
        if s.get("saijin"):
            rows.append('<div class="ih-row"><span class="ih-key">御祭神</span><span class="ih-val">%s</span></div>' % esc("・".join(s["saijin"])))
        if s.get("tel"):
            rows.append('<div class="ih-row"><span class="ih-key">電話</span><span class="ih-val"><a href="tel:%s" data-track-click="tel_tap">%s</a></span></div>' % (esc(s["tel"]), esc(s["tel"])))
        if s.get("official_url"):
            rows.append('<div class="ih-row"><span class="ih-key">公式サイト</span><span class="ih-val"><a href="%s" target="_blank" rel="noopener">%s</a></span></div>' % (esc(s["official_url"]), esc(s["official_url"])))

        body = ['<div class="sacred-place-guide" data-content-quality="human-readable">']
        body.append('<aside class="instant-header" aria-label="基本情報"><p class="ih-title">基本情報</p>%s</aside>' % "".join(rows))

        saijin_text = "・".join(s.get("saijin") or [])
        body.append('<section><h2 class="sec">%sについて</h2>' % esc(s["name"]))
        body.append('<p>%sは、%sに鎮座する神社です。読みは「%s」です。静岡県神社庁の公開情報で、社名と所在地を確認できます。</p>'
                    % (esc(s["name"]), esc(s["address"]), esc(s["name_kana"])))
        if saijin_text:
            body.append('<p>御祭神は、同じ公開情報に「%s」と記されています。神名の表記は資料によって異なることがあるため、このページでは出典の文字を尊重しています。</p>' % esc(saijin_text))
        else:
            body.append('<p>御祭神については、今回参照した公開情報から確かな表記を得られませんでした。神社名から祭神を推し量ることはせず、分かっている所在地と社名だけを掲載しています。</p>')
        if s.get("tsusho"):
            body.append('<p>「%s」という呼び名でも知られています。通称と正式な社名を並べておくと、案内を探すときや問い合わせるときの行き違いを減らせます。</p>' % esc(s["tsusho"]))
        body.append('</section>')

        research_sources = []
        if s["slug"] not in DEEP_RESEARCH_EXCLUDED:
            research_paragraphs, research_sources = shrine_research(s)
            body.append('<section class="deep-research" data-research-checked="2026-08-10">'
                        '<h2 class="sec">一次資料から読み解く%s</h2>' % esc(s["name"]))
            body.append(research_figure(s, "shrine"))
            split_at = min(5, len(research_paragraphs))
            for paragraph in research_paragraphs[:split_at]:
                body.append('<p>%s</p>' % esc(paragraph))
            body.append('</section>')
            body.append('<section class="deep-research-visit"><h2 class="sec">%sを訪ねる前の調べ方</h2>' % esc(s["name"]))
            for paragraph in research_paragraphs[split_at:]:
                body.append('<p>%s</p>' % esc(paragraph))
            body.append('</section>')

        fl = fest_by_shrine.get(s["slug"], [])
        if fl:
            body.append('<section><h2 class="sec">祭礼と地域行事</h2><div class="official">')
            for f_ in fl:
                tag = ""
                if f_.get("designation_id"):
                    dg = desig[f_["designation_id"]]
                    tag = '<span class="fest-badge">%s「%s」</span>' % (esc(dg["category"]), esc(dg["name"]))
                elif f_.get("designation_note"):
                    tag = '<span class="fest-badge">%s</span>' % esc(f_["designation_note"])
                body.append('<p class="mini"><b>%s</b>：%s %s<br>%s</p>' % (esc(f_["name"]), esc(f_["date_label"]), tag, esc(f_["summary"])))
            body.append('</div><p>ここに記した日付は参照資料の表記です。開催日時、奉納行事、観覧場所、交通規制は年によって変わることがあるため、訪問する年の主催者案内を優先してください。</p>'
                        '<p class="mini"><a href="/shrine/festivals/">森町の祭礼カレンダーを見る</a></p></section>')
        else:
            body.append('<section><h2 class="sec">祭礼の案内について</h2>'
                        '<p>%sについて、当サイトが参照した資料からは一般向けの祭礼予定を掲載できるだけの情報を得られませんでした。行事の有無や日程を、近隣神社の例や過去の暦から補うことはしていません。</p>'
                        '<p>祭礼日に訪ねたい場合は、静岡県神社庁の掲載ページや地域の最新案内をご覧ください。地域の行事は参拝者だけでなく、準備や交通を担う住民の暮らしの中で行われています。</p></section>'
                        % esc(s["name"]))

        if name_counts[s["name"]] > 1:
            body.append('<section><h2 class="sec">同名の神社と区別するには</h2>'
                        '<p>森町には「%s」という同名の神社が複数あります。このページが扱うのは、%sに鎮座する社です。検索結果や地図では、社名だけでなく住所まで照らし合わせてください。</p></section>'
                        % (esc(s["name"]), esc(s["address"])))
        else:
            body.append('<section><h2 class="sec">所在地を確かめて訪ねる</h2>'
                        '<p>所在地は%sです。駐車場、進入路、公共交通、境内設備については公開資料だけでは分からないため、道路や私有地を臨時の駐車場所として扱わないでください。</p></section>'
                        % esc(s["address"]))

        body.append('<section><h2 class="sec">参拝するときに大切にしたいこと</h2>'
                    '<p>%sは地域の信仰の場です。社殿や境内を静かに拝観し、祭礼準備、清掃、祈祷などが行われているときは現地の案内に従ってください。建物の内部や祭具は、許可なく撮影しないことが基本です。</p>'
                    '<p>このページは%sの開門時間、授与品、祈祷受付、駐車可否を保証するものではありません。目的がある参拝では、公式サイトや掲載先がある場合に最新情報を確かめてから出発すると安心です。</p></section>'
                    % (esc(s["name"]), esc(s["name"])))

        if d:
            body.append('<section><h2 class="sec">%s地区の中で見る</h2>'
                        '<p>%sは森町の%s地区にあります。地区ページでは、同じ地域に鎮座する神社をまとめて見られます。社ごとの由緒を一つにまとめず、所在地と出典を分けて読むための入口です。</p>'
                        '<p><a href="/shrine/areas/%s/">%s地区の神社を見る</a> ／ '
                        '<a href="/shrine/systems/%s/">御祭神から「%s」の神社を探す</a></p></section>'
                        % (esc(d["name"]), esc(s["name"]), esc(d["name"]), d["slug"], esc(d["name"]),
                           s["system"], esc(sys_meta[s["system"]]["label"])))

        same = [x for x in by_district[s["district_id"]] if x["slug"] != s["slug"]]
        if same:
            body.append('<section><h2 class="sec">%s地区のほかの神社</h2><div class="shrine-list">%s</div></section>'
                        % (esc(dmeta[s["district_id"]]["name"]), "".join(shrine_card(x) for x in same[:12])))

        body.append('<section><h2 class="sec">出典と更新日</h2><ul class="post-sources">')
        for src in s["sources"]:
            body.append('<li><a href="%s" target="_blank" rel="noopener">%s</a>（%s）</li>' % (esc(src["url"]), esc(src["title"]), esc(src.get("note", ""))))
        source_urls = {src["url"] for src in s["sources"]}
        for title, url, note in research_sources:
            if url not in source_urls:
                body.append('<li><a href="%s" target="_blank" rel="noopener">%s</a>（%s）</li>'
                            % (esc(url), esc(title), esc(note)))
                source_urls.add(url)
        body.append('<li><a href="https://www.town.morimachi.shizuoka.jp/gyosei/kanko_bunka/bunkazai/index.html" target="_blank" rel="noopener">森町 文化財情報</a>（町内の文化財に関する公式案内）</li>')
        body.append('</ul><p>基本情報の確認日は%sです。由緒本文の転載や、資料にない設備・行事の補完はしていません。神社または関係者から訂正の連絡をいただいた場合は、出典とともに更新します。</p></section></div>' % esc(s["last_verified_at"]))

        # 森町には同名の神社が複数ある（八幡神社5社・神明神社3社など）。
        # title と description が重複しないよう、鎮座地まで含めて区別する。
        addr_short = (s.get("address") or "").replace("静岡県周智郡森町", "森町")
        lead = "%s（%s）は、%sに鎮座する神社です。" % (s["name"], s["name_kana"], addr_short)
        if s.get("saijin"):
            lead += "御祭神は%s。" % "・".join(s["saijin"])
        lead += "所在地、祭礼の公開情報、地域との関わり、参拝時に守りたいことを一次資料に沿って整理します。"
        generated.append(write("shrines/%s" % s["slug"], shell(
            "/shrine/shrines/%s/" % s["slug"], "⛩️",
            ("%s（%s）｜%s" % (s["name"], s["name_kana"], addr_short)
             if name_counts[s["name"]] > 1 else "%s（%s）" % (s["name"], s["name_kana"])), lead,
            "".join(body), parts,
            ['<a href="/">%s</a>' % SITE_NAME, '<a href="/shrine/">森町の神社</a>',
             '<a href="/shrine/shrines/">神社一覧</a>', esc(s["name"])])))

    # ---- 一覧 -------------------------------------------------------------
    listing = [SHRINE_PHOTO_SHOWCASE, '<h2 class="sec">森町の神社39社</h2>', '<div class="shrine-list">%s</div>' % "".join(shrine_card(s) for s in shrines)]
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
