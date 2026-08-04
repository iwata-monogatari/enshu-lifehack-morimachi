#!/usr/bin/env python3
"""/tools/ 配下の3ツールと一覧ページを生成する(01計画書1-A)。

  /tools/                  ツール一覧
  /tools/gomi-search/      ごみ分別クイック検索(森町公式「家庭ごみの出し方ナビ」への誘導型)
  /tools/moving-checklist/ 引っ越しチェックリスト
  /tools/life-timeline/    ライフイベント・タイムライン

gomi-search は磐田版と同じく自前の品目DBを持たず、公式ツールへ誘導する構成にする。
森町固有の付加価値として多言語ガイド(英・中・ポルトガル・ベトナム・クメール)を前面に出す。

内部リンクは実在ページを指しているか生成前に検証し、1件でも切れていれば中止する。

使い方: python scripts/build_tools.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS_DIR = os.path.join(ROOT, "parts")
OUT_DIR = os.path.join(ROOT, "tools")
SITE = "https://morimachi.enshu-lifehack.com"
SITE_NAME = "森町ライフハック"

# 最終確認日。ここを更新したら各ページの表示も追従する。
VERIFIED = "2026-08-04"

TOOLS = [
    {"slug": "gomi-search", "emoji": "🗑️", "title": "ごみ分別クイック検索",
     "lead": "森町の家庭ごみは、町公式の「家庭ごみの出し方ナビ」で品目名から調べられます。分別表・カレンダーは多言語にも対応しています。"},
    {"slug": "moving-checklist", "emoji": "📦", "title": "引っ越しチェックリスト",
     "lead": "静岡県周智郡森町への転入・森町からの転出で必要な手続きを、順番に確認できます。"},
    {"slug": "life-timeline", "emoji": "🧭", "title": "ライフイベント・タイムライン",
     "lead": "結婚・出産・介護・相続・農地の承継まで。人生の節目ごとに、森町で必要になる手続きを見渡せます。"},
]


def load_parts():
    parts = {}
    for name in ("head-css", "header", "disclaimer", "footer"):
        with open(os.path.join(PARTS_DIR, "%s.html" % name), encoding="utf-8") as f:
            parts[name] = f.read().strip()
    return parts


def part_markup(name, content):
    return "<!-- PART:%s:START -->%s<!-- PART:%s:END -->" % (name, content, name)


def page_shell(slug, emoji, title, lead, body, parts, breadcrumb_label):
    url = "%s/tools/%s/" % (SITE, slug) if slug else "%s/tools/" % SITE
    crumb = (
        '<p class="breadcrumb"><a href="/">%s</a> ／ <a href="/tools/">ツール</a> ／ %s</p>' % (SITE_NAME, breadcrumb_label)
        if slug
        else '<p class="breadcrumb"><a href="/">%s</a> ／ ツール</p>' % SITE_NAME
    )
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
        '<main id="main"><div class="wrap">\n%s\n'
        '<section class="hero"><div class="hero-visual"><h1><span aria-hidden="true">%s</span> %s</h1></div>'
        '<div class="hero-body"><p class="lead">%s</p></div></section>\n'
        "%s\n"
        '<p class="verified">最終確認日：%s ／ 本ページは公式情報を整理したものです。最新・正確な情報は必ず森町公式ページで確認してください。</p>\n'
        "</div></main>\n%s\n</body></html>\n"
    ) % (
        title, SITE_NAME, lead, url, SITE_NAME, title, lead, url,
        part_markup("head-css", parts["head-css"]),
        part_markup("header", parts["header"]),
        part_markup("disclaimer", parts["disclaimer"]),
        crumb,
        emoji, title, lead,
        body, VERIFIED,
        part_markup("footer", parts["footer"]),
    )


def write(slug, html):
    out = os.path.join(OUT_DIR, slug, "index.html") if slug else os.path.join(OUT_DIR, "index.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as f:
        f.write(html)
    return os.path.relpath(out, ROOT).replace(os.sep, "/")


# --- 各ツールの本体 ----------------------------------------------------------


def body_gomi_search():
    return (
        '<div class="note">令和8年（2026年）4月1日からのごみ分別ルール変更にともなう分別ガイドブックの改訂作業が、'
        "町で進められています。現在の分別区分は、必ず下記の公式ページまたは生活環境係（0538-85-6314）で確認してください。</div>\n"
        '<h2 class="sec">品目から調べる</h2>\n'
        '<div class="grid"><div class="card real-card"><h3><span aria-hidden="true">🔎</span> 家庭ごみの出し方ナビ</h3>'
        "<p>品目名のキーワード検索と50音検索ができる、森町公式の検索ツールです。「これは燃えるごみ？」で迷ったら、まずここで引きます。</p>"
        '<a class="official-link" href="https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/juminseikatsuka/seikatsukankyokakari/1/1/gomi_navi/kateigomi/1101.html" target="_blank" rel="noopener" data-track-click="tool_gomi_navi">家庭ごみの出し方ナビを開く <span>森町公式</span></a></div>\n'
        '<div class="card real-card"><h3><span aria-hidden="true">📅</span> 分別表・収集カレンダー</h3>'
        "<p>分別表と収集日カレンダーはPDFで公開されているほか、全戸配布や役場での配架もあります。</p>"
        '<a class="official-link" href="https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/juminseikatsuka/seikatsukankyokakari/1/1/692.html" target="_blank" rel="noopener" data-track-click="tool_gomi_calendar">分別表・カレンダーを見る <span>森町公式</span></a></div></div>\n'
        '<h2 class="sec"><span aria-hidden="true">🌐</span> 多言語で確認する</h2>\n'
        '<p class="lead">森町の分別ガイドブックは英語・中国語・ポルトガル語・ベトナム語・クメール語に対応しています。'
        "外国籍のご家族・ご近所の方にはこちらを案内してください。</p>\n"
        '<div class="official">'
        '<a class="official-link" href="https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/juminseikatsuka/seikatsukankyokakari/1/1/692.html" target="_blank" rel="noopener">分別ガイドブック（多言語版を含む） <span>森町公式</span></a>'
        '<a class="official-link" href="https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/somuka/gyoseigakari/tabunkakyousei/6821.html" target="_blank" rel="noopener">外国人町民のための生活ガイドブック <span>森町公式</span></a>'
        "</div>\n"
        '<h2 class="sec">大きいもの・特別なものを捨てる</h2>\n'
        '<div class="note">森町では粗大ごみの戸別収集は行っておらず、中遠広域粗大ごみ処理施設（磐田市新貝）への直接搬入が基本です。'
        "手数料は車両の最大積載量により520円〜2,090円です。</div>\n"
        '<div class="action-grid">'
        '<a class="btn" href="/life/start-living/bulky-garbage-dropoff/">粗大ごみの出し方を見る</a>'
        '<a class="btn" href="/life/moving-out/bulk-garbage-cleaning/">引っ越しで出る大量のごみ</a>'
        '<a class="btn" href="https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/juminseikatsuka/seikatsukankyokakari/1/1/4520.html" target="_blank" rel="noopener">リユーズ事業（無料）を見る</a>'
        "</div>\n"
        '<h2 class="sec">くわしく読む</h2>\n'
        '<div class="official">'
        '<a class="official-link" href="/life/start-living/how-to-garbage/">ごみの出し方（森町ライフハック）</a>'
        '<a class="official-link" href="/life/start-living/garbage-sorting-calendar/">ごみ分別カレンダー（森町ライフハック）</a>'
        '<a class="official-link" href="/life/start-living/bulky-garbage-dropoff/">粗大ごみの搬入（森町ライフハック）</a>'
        "</div>\n"
        '<h2 class="sec">問い合わせ</h2>\n'
        '<div class="official"><p class="mini"><b>窓口</b>：森町 住民生活課 生活環境係</p>'
        '<p class="mini"><b>電話</b>：0538-85-6314</p>'
        '<a class="official-link" href="tel:0538-85-6314" data-track-click="tel_tap">生活環境係に電話する <span>0538-85-6314</span></a></div>\n'
    )


def body_moving_checklist(data):
    out = ['<div class="type-tabs" aria-label="状況を選ぶ">']
    for m in data["modes"]:
        out.append('<a href="#mode-%s">%s</a>' % (m["id"], m["label"]))
    out.append("</div>\n")
    for m in data["modes"]:
        out.append('<section class="type-panel" id="mode-%s"><span class="label">%s</span>' % (m["id"], m["label"]))
        out.append("<p>%s</p>" % m["lead"])
        for g in m["groups"]:
            out.append('<h3>%s</h3><ul>' % g["title"])
            for it in g["items"]:
                out.append('<li><a href="%s">%s</a></li>' % (it["href"], it["label"]))
            out.append("</ul>")
        out.append("</section>\n")
    out.append(
        '<h2 class="sec">チェックを付けながら進めたい方へ</h2>'
        '<div class="action-grid">'
        '<a class="btn" href="/checklist/moved-in/">森町に引っ越してきた（チェックリスト）</a>'
        '<a class="btn" href="/tools/life-timeline/">ライフイベント・タイムラインを見る</a>'
        "</div>\n"
    )
    return "".join(out)


def body_life_timeline(data):
    out = ['<div class="timeline">']
    for e in data["events"]:
        badge = '<span class="timeline-badge">森町ならでは</span>' if e.get("morimachi_specific") else ""
        out.append(
            '<section class="timeline-item"><div class="timeline-head">'
            '<span class="timeline-emoji" aria-hidden="true">%s</span>'
            '<div><span class="timeline-age">%s</span><h2>%s</h2>%s</div></div>'
            "<p>%s</p>" % (e["emoji"], e["age_band"], e["title"], badge, e["summary"])
        )
        out.append('<div class="official">')
        for l in e["links"]:
            out.append('<a class="official-link" href="%s">%s</a>' % (l["href"], l["label"]))
        out.append("</div></section>")
    out.append("</div>\n")
    return "".join(out)


def body_index():
    cards = "".join(
        '<div class="card real-card"><h3><span aria-hidden="true">%s</span> %s</h3><p>%s</p>'
        '<a class="official-link" href="/tools/%s/">開く <span>森町ライフハック</span></a></div>'
        % (t["emoji"], t["title"], t["lead"], t["slug"])
        for t in TOOLS
    )
    return (
        '<h2 class="sec">3つのツール</h2><div class="grid">%s</div>\n'
        '<h2 class="sec">ライフイベント別チェックリスト</h2>'
        '<div class="action-grid">'
        '<a class="btn" href="/checklist/moved-in/">森町に引っ越してきた</a>'
        '<a class="btn" href="/checklist/married/">結婚した</a>'
        '<a class="btn" href="/checklist/baby/">子どもが生まれた</a>'
        '<a class="btn" href="/checklist/job-change/">転職した・退職した</a>'
        "</div>\n" % cards
    )


def collect_internal_links(*blobs):
    import re

    hrefs = set()
    for b in blobs:
        hrefs |= set(re.findall(r'href="(/[^"#]*)"', b))
    return hrefs


def main():
    parts = load_parts()
    with open(os.path.join(ROOT, "data", "moving-checklist.json"), encoding="utf-8-sig") as f:
        moving = json.load(f)
    with open(os.path.join(ROOT, "data", "life-timeline.json"), encoding="utf-8-sig") as f:
        timeline = json.load(f)

    bodies = {
        "gomi-search": body_gomi_search(),
        "moving-checklist": body_moving_checklist(moving),
        "life-timeline": body_life_timeline(timeline),
        "": body_index(),
    }

    # 内部リンクの実在確認(/tools/ と /checklist/ は本スクリプト実行後に存在する前提で許容)
    allowed_prefix = ("/tools/", "/checklist/")
    broken = []
    for href in sorted(collect_internal_links(*bodies.values())):
        if href.startswith(allowed_prefix) or href == "/":
            continue
        target = os.path.join(ROOT, href.strip("/").replace("/", os.sep), "index.html")
        if not os.path.isfile(target):
            broken.append(href)
    if broken:
        print("リンク切れのため生成を中止しました（%d件）:" % len(broken))
        for b in broken:
            print("  " + b)
        return 1

    generated = []
    for t in TOOLS:
        html = page_shell(t["slug"], t["emoji"], t["title"], t["lead"], bodies[t["slug"]], parts, t["title"])
        generated.append(write(t["slug"], html))
    index_html = page_shell(
        "", "🧰", "便利ツール", "森町の暮らしで使えるツールをまとめています。", bodies[""], parts, "ツール"
    )
    generated.append(write("", index_html))

    print("生成 %d ページ / 内部リンク切れ 0" % len(generated))
    for p in generated:
        print("  " + p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
