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
VERIFIED = "2026-08-10"

from sacred_research import research_figure, temple_research  # noqa: E402

DEEP_RESEARCH_EXCLUDED = {"t02"}

SECT_SLUG = {"曹洞宗": "soto", "日蓮宗": "nichiren", "真言宗": "shingon", "天台宗": "tendai", "浄土宗": "jodo"}
SECT_DESC = {
    "曹洞宗": "県名簿の27法人に、森町の寺院建築資料に載る陽向院を加えた一覧。資料ごとの差を分けて示している。",
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
    trailing_newline = "\n" if content.endswith("\n") else ""
    content = "\n".join(line.rstrip() for line in content.splitlines()) + trailing_newline
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


def area_research(d, temples):
    """Explain each district with its own source-grounded comparisons."""
    global SECT_EXTENSIONS
    expected_counts = {"mori": 8, "ichinomiya": 4, "amagata": 5, "sonoda": 5, "iida": 6, "mikura": 6}
    if len(temples) != expected_counts[d["district_id"]]:
        raise ValueError("寺院地区件数が固有解説と不一致: %s" % d["district_id"])
    sect_counts = Counter(t["sect"] for t in temples)
    distribution = "、".join("%s%dヶ寺" % (sect, count) for sect, count in sorted(sect_counts.items()))
    names = "、".join(t["name"] for t in sorted(temples, key=lambda item: item["name"]))
    town_names = "、".join(t["name"] for t in temples if t.get("in_town_article")) or "該当なし"
    registry_only = "、".join(t["name"] for t in temples if not t.get("in_town_article")) or "該当なし"
    facts = {
        "mori": [
            "%s地区は8ヶ寺で、内訳は%sです。寺院名は%s。森・向天方・橘・天宮という複数の大字にまたがり、同じ地区名でも所在地を寺院名と組にして読む必要があります。" % (d["name"], distribution, names),
            "天台宗の蓮華寺と日蓮宗の報恩寺が各1ヶ寺あり、残る6ヶ寺は曹洞宗です。曹洞宗6ヶ寺だけを見ると、森に梅林院・隨松寺・西光寺、向天方に宝太寺、橘に大洞院、天宮に萬松寺と分かれます。",
            "森町の寺院建築資料で個別名を確認できるのは%sです。一方、%sは県名簿で法人名・包括団体・所在地を確認した寺院であり、町資料に個別名がないことを不存在の根拠にはしていません。" % (town_names, registry_only),
            "地区集計は旧森町の範囲を使います。向天方と天宮は名称から天方地区へ移さず、地区台帳の大字対応どおり森地区に数えています。",
        ],
        "ichinomiya": [
            "一宮地区の4ヶ寺は、天台宗の蓮増院、浄土宗の安養院、曹洞宗の極楽寺と高雲寺です。4ヶ寺で3宗派に分かれるため、寺院数だけでなく宗派名まで確認すると候補を絞れます。",
            "所在地はいずれも大字一宮ですが、番地は322、3167、3903、5709と離れています。名称が似た施設を地図検索だけで選ばず、県名簿の法人名と番地を一組として照合する地区です。",
            "町の寺院建築資料に名が出るのは%sです。極楽寺は同資料の建築一覧には個別名がなくても、県名簿には一宮5709の曹洞宗寺院として掲載されています。" % town_names,
            "蓮増院と安養院は宗派が異なり、高雲寺と極楽寺は同じ曹洞宗です。一宮地区内で比較するときは、宗派による絞り込みと番地による照合を別々に行えます。",
        ],
        "amagata": [
            "天方地区の5ヶ寺はすべて曹洞宗で、藏雲院・自得院・萬福寺・福泉寺・古心庵です。宗派では区別できないため、大鳥居・鍛冶島・問詰・西俣・葛布の所在地を主な照合軸にします。",
            "5ヶ寺はそれぞれ別の大字に1ヶ寺ずつあります。旧天方村という集計単位と、現在の郵便住所に現れる大字を混同せず、寺院名の次に大字、最後に番地を確認する順が適します。",
            "町の寺院建築資料に個別名があるのは%sです。古心庵は県名簿の葛布288で確認でき、町資料が全寺院の所在地一覧ではないことも同時に示します。" % town_names,
            "陽向院は町資料で薄場と記載され、地区台帳では薄場が天方地区に含まれます。ただし県名簿で法人所在地を対応できていないため、この県名簿所在地による5ヶ寺の地区件数には加えていません。",
        ],
        "sonoda": [
            "園田地区で県名簿所在地を対応できる寺院は、香勝寺・雲林寺・地蔵寺・大福寺・全生寺の5ヶ寺です。5ヶ寺はいずれも曹洞宗なので、宗派別ページより所在地別の比較が有効です。",
            "中川には雲林寺と地蔵寺の2ヶ寺があり、草ヶ谷・牛飼・円田には各1ヶ寺です。同じ中川でも雲林寺は43-2、地蔵寺は1269であり、寺院名と番地の両方が識別情報になります。",
            "この5ヶ寺は町の寺院建築資料の建立年代表に個別名が並ぶ寺院ではありません。一方、県名簿では5件とも法人名、曹洞宗という包括団体、所在地を確認できます。",
            "園田地区という名称は旧園田村の大字対応による整理です。各寺院の檀家区域や現在の活動範囲を表す分類ではなく、公開された所在地を探すための索引として用います。",
        ],
        "iida": [
            "飯田地区の6ヶ寺は%sです。曹洞宗4ヶ寺に、真言宗智山派の遍照寺と日蓮宗の本立寺が1ヶ寺ずつ加わります。" % distribution,
            "大字飯田には遍照寺・崇信寺・本立寺、大字睦実には泉龍寺・玉泉寺・宗源寺があります。地区内を二つの大字に分けると、同宗派の曹洞宗4ヶ寺も所在地で比較できます。",
            "町の寺院建築資料に名があるのは%sです。玉泉寺は県名簿の睦実2325に掲載されますが、町資料の建立年代表に個別名がないため、二資料の収録目的を分けて扱います。" % town_names,
            "本立寺と遍照寺はともに大字飯田でも宗派が異なります。睦実の3ヶ寺はすべて曹洞宗なので、後者は名称と番地まで確認しないと地区・宗派だけでは一意になりません。",
        ],
        "mikura": [
            "三倉地区の6ヶ寺は、真言宗御室派の金剛院と、曹洞宗の全光寺・蔵泉寺・長月寺・太慶寺・榮泉寺です。全件の県名簿所在地は大字三倉で、番地が寺院を区別する重要な項目です。",
            "町資料では金剛院山門が町指定文化財として挙げられ、榮泉寺本堂は建立年代が判明する寺院建築のうち最古とされます。前者は山門の指定、後者は本堂の年代という異なる事実です。",
            "町の寺院建築資料に個別名があるのは%sです。全光寺は県名簿の三倉2257で確認でき、建築資料に名前がないことだけで寺院の有無は判断しません。" % town_names,
            "蔵泉寺は町資料の建立年代表では田能、県名簿では三倉4935と記載されます。太慶寺も町資料では大久保、県名簿では三倉4339であり、小地域名と法人所在地の表記差を残して照合します。",
        ],
    }
    SECT_EXTENSIONS = {
        "浄土宗": [
            "安養院を確認する入口は、浄土宗という宗派名、一宮322という県名簿所在地、安養院という法人名の三点です。一宮地区には蓮増院、極楽寺、高雲寺も載るため、大字一宮だけを検索条件にすると四寺が候補になります。浄土宗まで指定して初めて安養院一寺へ絞れる構造を、宗派別索引の利点として使えます。",
            "町の寺院建築資料が示す整形6間取りや前面の畳縁は、本堂についての建築説明です。県名簿の一宮322は法人所在地で、建物の位置、公開範囲、拝観条件を詳しく示す資料ではありません。建築形式を確認したいときは町資料、正式名称と宗派・所在地を確認したいときは県名簿へ戻り、一つの説明に混ぜません。",
            "一宮322という番地は、天台宗蓮増院の一宮3903、曹洞宗高雲寺の一宮3167、曹洞宗極楽寺の一宮5709と区別する鍵です。ただし番地の数字だけから寺院間の距離や道順は分かりません。訪問先を決める場合は安養院の公開住所を地図で再確認し、駐車や受付の有無は別に寺院へ問い合わせます。",
            "町資料が安養院を町内唯一の浄土宗寺院と説明し、県名簿でも今回の森町抽出は一法人です。この一致は件数確認に使えますが、檀家区域、法要の対応範囲、墓地利用まで一つだと示すものではありません。公開資料で答えられない質問を未確認欄へ送り、宗派別件数と個別の利用条件を分離します。",
            "大石の視点では、安養院を周辺土地の目印に用いるときも、寺院名だけで対象地の接道や境界を説明しません。家族の記録には安養院、浄土宗、一宮322、町建築資料の本堂項目、県名簿確認日を残します。法要や訪問に関する希望は事実欄へ混ぜず、寺院へ確認する内容と確認者を別欄に置きます。",
            "資料を読み直す際は、県名簿の一宮322を現住所欄、町建築資料の安養院本堂を建築欄へ転記し、出典ページも分けます。浄土宗一寺という集計は今回の森町抽出範囲に限り、近隣市町や寺院の関連施設まで含む数ではありません。修正情報を得た場合は、件数、住所、建築説明のどこが変わるかを個別に更新します。",
        ],
        "日蓮宗": [
            "日蓮宗二寺は、報恩寺―向天方1255-1―森地区と、本立寺―飯田1935-1―飯田地区の組で確認します。寺名も大字も異なるため、二寺を一つの所在地へまとめる必要はありません。宗派で二件に絞った後、地区、大字、番地の順に読めば、県名簿の法人所在地と地区台帳の分類を同時に追えます。",
            "向天方は名称に天方を含みますが、地区台帳では森地区に入ります。報恩寺を天方地区へ移すと、森地区と天方地区の寺院件数が変わります。本立寺の飯田地区との比較では、字面による推測を避け、報恩寺は森地区、本立寺は飯田地区という台帳区分を保持します。宗派資料だけでは地区は決まりません。",
            "町建築資料は本立寺本堂の奥行きや内陣両側室を扱います。報恩寺について同じ建築構成を示す根拠ではありません。一方、県名簿は両寺の日蓮宗法人名と所在地を確認する資料です。本立寺の建築説明、報恩寺と本立寺の法人所在地という二種類の情報を列で分け、二寺共通の特徴へ拡張しません。",
            "番地照合では枝番を省かず、報恩寺1255-1、本立寺1935-1と記します。どちらも末尾に枝番がありますが、同じ住所体系や近い場所を意味しません。地図検索では寺院名と完全な住所を一組にし、検索結果の外観写真だけで場所を確定しないようにします。訪問条件や連絡方法は各寺院へ個別に確かめます。",
            "大石の視点では、家族が覚える通称と県名簿の正式名が一致するかを先に確認します。記録票は宗派、寺院名、地区、大字番地、町資料の建築項目、確認日という順です。二寺のうち一方で確認した法要や墓地の条件を他方へ流用せず、未確認事項には報恩寺か本立寺か対象名を必ず添えます。",
            "二寺の比較表を更新するときは、報恩寺の向天方1255-1と本立寺の飯田1935-1を原表記で保存します。町資料に本立寺本堂の項目があること、報恩寺の建築詳細を同じ資料から補えないことも明記します。空欄は同じ形式ではないという意味にせず、今回参照した資料では確認できない状態として残します。",
        ],
        "真言宗": [
            "真言宗二寺は包括団体まで読むと、真言宗御室派の金剛院と真言宗智山派の遍照寺に分かれます。金剛院は三倉2308、遍照寺は飯田2130で、三倉地区と飯田地区に一寺ずつです。『真言宗』という上位名だけで一括せず、派名、寺院名、番地を続けて記すことが二件を識別する基本になります。",
            "町建築資料は両寺の本堂について、前方の外陣と奥の内陣・両脇間という構成を説明します。これは本堂形式に関する記載であり、二寺の沿革、現在の利用方法、受付条件が同じだという意味ではありません。共通する建築項目と、県名簿で異なる包括団体・所在地を別表にすれば、似ている点と異なる点を根拠付きで残せます。",
            "町指定文化財として資料に出るのは金剛院山門です。遍照寺本堂や金剛院の全建物が同じ指定を受けると読み替えません。金剛院を調べるときは三倉2308の法人所在地、山門の指定、本堂の建築説明を三行に分けます。遍照寺は飯田2130、真言宗智山派、本堂の建築項目という別の三行で扱います。",
            "地区別に見る場合、三倉には曹洞宗五寺もあり、飯田には曹洞宗四寺と日蓮宗一寺もあります。金剛院や遍照寺を地区名だけから探すと他宗派が候補に残ります。宗派別ページで派名を確認し、地区ページで同じ大字の寺院を比較し、最後に県名簿の番地へ戻る三段階が有効です。",
            "大石の視点では、山門の文化財情報を周辺土地の価値や利用制限へ直接結び付けません。土地・建物の相談では対象地番と寺院住所を別々に確認します。家族用メモには金剛院と遍照寺の派名、住所、町資料の対象建物、県名簿確認日を残し、訪問、法要、駐車の条件はそれぞれの寺院へ尋ねます。",
            "再確認では、金剛院を御室派・三倉2308、遍照寺を智山派・飯田2130として二行に固定します。町資料の共通する本堂構成は両行へ出典付きで置き、金剛院山門の指定だけは金剛院行へ加えます。この配置なら、派名の違い、所在地の違い、建物情報の共通点、文化財対象の相違を一つずつ検算できます。",
        ],
        "天台宗": [
            "天台宗二寺は蓮華寺と蓮増院で、寺名の先頭二字が共通します。蓮華寺は森2144・森地区、蓮増院は一宮3903・一宮地区です。一字違いの名称だけを記憶に頼らず、寺か院かという末尾、地区、大字番地を一組で照合します。県名簿では別法人なので、検索結果や家族メモでも表記を統一して残します。",
            "町建築資料は両寺の本堂を整形6間取りとして扱いますが、蓮華寺には観音堂移築の記載があります。この記載を蓮増院へ共有させず、蓮華寺の建築項目として保持します。県名簿が示すのは蓮華寺森2144、蓮増院一宮3903という所在地と天台宗法人であり、移築年代や建築形式の根拠は町資料へ戻ります。",
            "森地区で蓮華寺を探すと曹洞宗六寺と日蓮宗報恩寺も候補になり、一宮地区で蓮増院を探すと浄土宗安養院と曹洞宗二寺も候補になります。天台宗という条件を加えると各地区一寺へ絞れます。宗派別索引は地区横断の二寺比較、地区別索引は同じ地区内の別宗派比較に使い分けます。",
            "番地の2144と3903は寺院を区別する識別子ですが、数字から距離や道路条件は判断できません。現地確認では正式名と完全住所を地図へ入力し、写真の建物形状だけを手掛かりにしません。町資料の建築説明を現存状況の保証にせず、現在の外観や訪問可能範囲が必要なら寺院へ確認します。",
            "大石の視点では、蓮華寺と蓮増院の取り違えが土地説明や家族の予定表へ残らないよう、正式名、宗派、地区、住所、資料名、確認日を一行にします。観音堂の記載は蓮華寺だけに付けます。法要や墓地、駐車、受付時間は県名簿・建築資料の対象外なので、確認先と質問日を別欄へ置きます。",
            "表記確認では『蓮華寺』の華と寺、『蓮増院』の増と院を省略せず、森2144と一宮3903を並べます。町資料の整形6間取りという共通項目があっても、二寺を同じ建物として扱いません。資料の確認日が変わったときは、法人所在地、建築説明、観音堂の項目を別々に再読し、変更なしの場合も確認日を更新します。",
        ],
        "曹洞宗": [
            "曹洞宗ページは二つの母集団を持ちます。県名簿で法人所在地まで対応できる二十七寺と、町建築資料に曹洞宗寺院として出る陽向院を加えた二十八寺です。二十八という数字を県名簿の法人件数として使わず、二十七は所在地確認済み、陽向院は町資料由来で所在地詳細未対応、と注記します。",
            "所在地確認済み二十七寺は、森六、一宮二、天方五、園田五、飯田四、三倉五です。森の梅林院2345と隨松寺2318、中川の雲林寺43-2と地蔵寺1269のように同じ大字に複数寺院があるため、地区と宗派だけでは一意になりません。正式名、大字、番地の三項目を並べて初めて個別記録になります。",
            "陽向院について町資料は薄場と記し、地区台帳は薄場を天方地区に含めます。しかし県名簿の法人所在地へ対応できていないため、古心庵など天方五寺と同じ所在地確認済み一覧には入れません。薄場という町資料の表記、天方地区という台帳上の整理、県名簿所在地未対応という状態を三つとも残します。",
            "町建築資料の年代比較では榮泉寺本堂の元禄9年という記録を確認できます。県名簿は建立年代を掲載する資料ではないため、二十七寺全体の年代順を県名簿から作ることはできません。町資料に名のない寺院へ榮泉寺との新旧関係を当てはめず、年代が書かれた建物、寺院名、資料箇所を一組で転記します。",
            "地区ごとの読み方も異なります。天方と園田は所在地確認済み五寺がすべて曹洞宗、三倉は曹洞宗五寺に真言宗一寺、飯田は曹洞宗四寺に真言宗・日蓮宗各一寺です。曹洞宗だけを探す場合でも、大字が複数ある天方・園田、同じ大字三倉に五寺ある三倉、飯田と睦実に分かれる飯田では照合軸を変えます。",
            "実際の確認表では、県名簿二十七寺を地区、大字、番地で並べ、町建築資料掲載の有無を追加します。陽向院は別枠に置き、薄場、天方地区、所在地詳細未確認を記します。大石の視点では、宗派が同じことから檀家区域、行事、墓地、管理方法を共通化せず、個別寺院へ尋ねた回答だけを各行へ追記します。",
            "二十七行を点検する際は、まず地区別合計が六・二・五・五・四・五になるかを確認し、次に同じ大字内の寺名と番地を照合します。その後で町建築資料の個別記載を付け、陽向院を別枠へ戻します。合計値だけが合っていても寺院の入替えは発見できないため、寺名、所在地、宗派の三項目を行ごとに検算します。",
        ],
    }
    extensions = {
        "mori": [
            "森地区の照合表は、最初から八寺を一列に並べるより、森三寺、向天方一寺、橘一寺、天宮一寺に曹洞宗を分け、蓮華寺と報恩寺を別宗派として置く方が読みやすくなります。梅林院は森2345、隨松寺は森2318で番地が近く、西光寺は森473です。寺名だけを検索欄へ入れず、大字と番地を続けて確認すると、森という地区名と大字森の取り違えを減らせます。",
            "蓮華寺は森2144の天台宗、報恩寺は向天方1255-1の日蓮宗です。二寺は曹洞宗六寺とは宗派の欄で分けられますが、地区台帳ではいずれも森地区に収まります。向天方という字面を理由に天方地区へ数え直すと地区集計が変わるため、地区は台帳、宗派と法人所在地は県名簿、建物の説明は町資料という三本立てで読みます。",
            "町の寺院建築資料に出る寺名と県名簿の八法人は収録範囲が一致しません。蓮華寺、梅林院、報恩寺は町資料でも個別に追えますが、隨松寺、西光寺、宝太寺、萬松寺、大洞院は県名簿の法人所在地が主な確認箇所です。町資料に寺名が見当たらない五寺を『建物がない』と読まず、建築調査で個別掲載されたかどうかだけを示す差として保ちます。",
            "大字比較では、森の三寺を番地順に並べ、次に向天方、橘、天宮へ移る索引を作れます。これは参拝順や距離順を示すものではありません。現地へ行く場合は公開住所を地図で再確認し、境内への立入り、駐車、法要中の訪問可否を寺院へ尋ねます。県名簿の所在地公開は、境内の利用条件や日常の受付時間まで保証する情報ではありません。",
            "家族の記録へ残す順番は、寺院名、宗派、県名簿の所在地、地区台帳の区分、町資料にある建築項目、確認日の六欄です。たとえば萬松寺は天宮972と森地区、宝太寺は向天方1128と森地区を同時に記します。大石の視点では、近隣土地の説明に寺院名を使うときも、寺院との距離や関係を推測せず、公開住所から確かめた位置だけを事実欄へ置きます。",
            "八寺の再集計では、曹洞宗六、天台宗一、日蓮宗一を先に確認し、曹洞宗六寺を森三、向天方一、橘一、天宮一へ分けます。蓮華寺の森2144と報恩寺の向天方1255-1は別宗派の行として照合します。この順序なら、向天方を別地区へ動かした誤りや、森という大字と地区の混同を件数と住所の両面から見つけられます。",
        ],
        "ichinomiya": [
            "一宮地区は四寺だけですが、一宮322の安養院、一宮3167の高雲寺、一宮3903の蓮増院、一宮5709の極楽寺と番地の開きがあります。数字の大小を道路上の並びや移動距離だと解釈せず、地図上の位置は一寺ずつ再検索します。候補表では寺院名と番地を固定し、その後に浄土宗、曹洞宗、天台宗という宗派欄を付けると同名施設の混入を防げます。",
            "曹洞宗は高雲寺と極楽寺の二寺です。同じ大字、同じ宗派でも、高雲寺は3167、極楽寺は5709なので、宗派フィルターだけでは一寺に絞れません。蓮増院は天台宗で3903、安養院は浄土宗で322です。宗派内訳を二・一・一と読み、最後に番地へ戻る手順なら、一宮地区の四件を数え直す際にも根拠をたどれます。",
            "町建築資料で安養院、蓮増院、高雲寺の建築説明を確認できる一方、極楽寺は県名簿の法人所在地で数えています。この三対一の差は、極楽寺が寺院ではないことを意味しません。町資料は建築上の特徴や調査対象を扱い、県名簿は宗教法人名、包括団体、所在地を扱うため、四寺総覧を作るには二資料を同じ目的の一覧として重ねない注意が必要です。",
            "閲覧者が一宮の寺院を探すときは、まず宗派が分かるか、次に寺院名が分かるか、最後に番地を確認できるかを順に尋ねます。宗派不明なら四寺を残し、曹洞宗と分かれば高雲寺と極楽寺の二寺まで絞ります。番地が不明な段階で写真や地図の外観だけから決めず、県名簿の正式名称へ戻るのが安全です。",
            "大石の視点では、一宮という住所だけを周辺土地の説明に使わず、対象地番と寺院番地を別々に確認します。安養院322と蓮増院3903では同じ大字でも位置条件が異なります。家族用メモには、寺院名、宗派、番地、町建築資料の有無、県名簿確認日を残し、法要や墓地利用など公開資料にない事項は寺院への個別質問として分離します。",
            "四寺の更新確認は、安養院322、蓮増院3903、高雲寺3167、極楽寺5709という住所表から始めます。次に宗派内訳が浄土宗一、天台宗一、曹洞宗二になるかを検算し、最後に町建築資料の三寺と県名簿のみで数える極楽寺を分けます。件数、宗派、収録差を別々に確かめれば、一つの修正が他の列へ及ぼす範囲も分かります。",
        ],
        "amagata": [
            "天方地区の五寺は宗派欄がすべて曹洞宗になるため、藏雲院・自得院・萬福寺・福泉寺・古心庵という寺名と、大鳥居・鍛冶島・問詰・西俣・葛布という大字の対応が中心になります。一大字一寺という今回の県名簿集計を利用し、藏雲院―大鳥居540-1のように名称と番地を一対で写せば、宗派名だけの候補表より再確認しやすくなります。",
            "番地は自得院が鍛冶島522-1、萬福寺が問詰388、福泉寺が西俣50、古心庵が葛布288です。これらを数字順に並べても地理的な移動順にはなりません。天方地区という旧村由来の索引の下に現在の大字を置き、地図確認は各住所で別々に行います。住所の公開から駐車場所や参道の通行条件を推測しないことも必要です。",
            "町建築資料で個別名を追える藏雲院、自得院、萬福寺、福泉寺と、県名簿で葛布288を確認する古心庵には収録差があります。古心庵が町資料の建立年代表にないという事実は、年代や建物の状態が不明であることを示すだけです。県名簿が建築年代を扱わない以上、古心庵の建立年を他の四寺から類推して補いません。",
            "陽向院はこの地区を読むときの別枠です。町資料は薄場の曹洞宗寺院として名前を載せ、地区台帳では薄場が天方地区に入りますが、県名簿の法人所在地と結び付けられていません。そのため、所在地確認済み五寺の件数へ機械的に加えず、町資料由来の一寺として注記します。薄場と天方の関係、法人所在地の未対応という二点を同時に残します。",
            "確認票は、五寺について県名簿名、大字、番地、曹洞宗、町資料掲載の有無を一行ずつ記し、陽向院だけは町資料名、薄場、県名簿所在地未対応を別行にします。大石の視点では、住所未確認の寺院を土地案内の目印にせず、まず公開資料の範囲を説明します。現地情報が必要なら、寺院または資料所管へ照会した日と回答範囲を追加します。",
            "五寺表の検算は、大鳥居、鍛冶島、問詰、西俣、葛布が一回ずつ現れるかを確認してから寺名と番地を読みます。陽向院の薄場は六つ目の県名簿所在地として加えず、町資料欄だけに置きます。曹洞宗六寺という総覧と、所在地確認済み五寺という地区一覧の違いを注記すれば、資料母集団を保ったまま更新できます。",
        ],
        "sonoda": [
            "園田地区の五寺は曹洞宗で統一されますが、所在地は草ヶ谷、中川、牛飼、円田に分かれます。香勝寺は草ヶ谷968、大福寺は牛飼409、全生寺は円田1076-1です。宗派内訳が一種類でも、大字が四種類あるため、寺院名の次に大字を置く索引なら、地区名だけの一覧より現地確認の入口を明確にできます。",
            "中川には雲林寺43-2と地蔵寺1269の二寺があります。五寺のうち同じ大字を共有するのはこの二寺なので、中川という語だけでは候補が残ります。寺院名、番地、県名簿の法人名を照合し、地図の検索結果に出る写真や口コミは法人所在地の根拠にしません。枝番を含む43-2は省略せず、1269との識別欄にそのまま写します。",
            "園田の五寺は県名簿で法人名、曹洞宗、所在地を確認できますが、町の寺院建築資料の建立年代表では個別名が並びません。この差から建築年代、建物の価値、活動状況を判断することはできません。町資料に個別記載がないことと、県名簿に法人として収録されることを別々の列へ置くことで、資料の目的を越えた説明を避けます。",
            "読み分けは、園田地区の五件を開く、大字で四群に分ける、中川だけ二件を番地で分ける、県名簿確認日を付ける、町資料の個別記載なしを注記する、の順です。これは檀家区域や寺院同士の関係を示す分類ではありません。宗派が同じことから運営、行事、受付条件も同じだと考えず、必要事項は各寺院へ確認します。",
            "大石の視点では、草ヶ谷や中川の土地を家族で整理するとき、近隣寺院を位置確認の補助に使っても境界や接道の根拠にはしません。対象地番と寺院番地は別資料で扱います。家族メモには香勝寺、雲林寺、地蔵寺、大福寺、全生寺の正式名と住所を残し、墓地、駐車、訪問可否は未確認事項として切り離します。",
            "園田五寺を更新するときは、中川が二行、草ヶ谷・牛飼・円田が各一行になるかを先に数えます。中川二寺は43-2と1269を照合し、残る三寺も枝番を含む原住所を保持します。町建築資料の個別記載がない状態は一括注記にし、五寺それぞれの建立年や建物状態を同じ空欄から推定しないようにします。",
        ],
        "iida": [
            "飯田地区六寺は、大字飯田の遍照寺2130、崇信寺3052、本立寺1935-1と、大字睦実の泉龍寺1621、玉泉寺2325、宗源寺227に三寺ずつ分かれます。地区件数は同じ三対三でも、飯田側は真言宗・曹洞宗・日蓮宗、睦実側は曹洞宗三寺です。大字と宗派を二段階で読むと六寺の違いが見えます。",
            "曹洞宗四寺は崇信寺、泉龍寺、玉泉寺、宗源寺です。崇信寺だけが大字飯田で、残る三寺は睦実にあります。睦実の三寺を区別するときは、1621、2325、227という番地を寺名と組にします。番地の大小を道路順とみなさず、公開住所を一件ずつ地図へ入力して位置を確かめます。",
            "遍照寺は真言宗智山派、本立寺は日蓮宗で、いずれも大字飯田です。宗派名まで分かれば二寺は区別できますが、町建築資料の記述を県名簿の包括団体情報へ読み替えません。県名簿では法人名・宗派・所在地、町資料では本堂の構成や建立年表の対象を確認し、同じ寺院でも事実の種類を列で分けます。",
            "町資料に個別名のある寺院群と、県名簿の睦実2325で数える玉泉寺には収録差があります。玉泉寺が建立年表に出ないことを、建立年が新しい、建物が残らない、といった説明へ広げる根拠はありません。六寺一覧では町資料掲載の有無を補助欄に置き、所在地の確認は六寺すべて県名簿の記載へ戻します。",
            "大石の視点では、飯田と睦実のどちらかだけで候補を決めず、家族が覚える寺名、県名簿の正式名、番地を照合します。確認票の順は地区、大字、寺院名、宗派、番地、町資料項目、確認日です。法要日程や墓地の利用条件など名簿・建築資料が扱わない情報は、寺院へ尋ねる質問として別紙に残します。",
            "六寺の再確認では、大字飯田三行と睦実三行を分け、曹洞宗が飯田一・睦実三になるかを検算します。遍照寺と本立寺は飯田側の別宗派として残し、玉泉寺は県名簿所在地と町資料収録差を注記します。大字別件数、宗派別件数、町資料掲載数は同じ集計ではないため、それぞれ独立した合計欄を設けます。",
        ],
        "mikura": [
            "三倉地区六寺の県名簿住所はすべて大字三倉です。金剛院2308、全光寺2257、蔵泉寺4935、長月寺3196、太慶寺4339、榮泉寺707という番地を寺名に添えなければ、大字だけでは識別できません。真言宗御室派の金剛院一寺と曹洞宗五寺を先に分け、曹洞宗内は番地で確かめます。",
            "金剛院は町指定文化財として山門が挙げられます。榮泉寺は本堂の建立年代が町資料で比較され、元禄9年の記録があります。文化財指定の対象が山門であることと、建立年代の対象が本堂であることを分け、寺院全体が同じ指定・同じ年代だと要約しません。県名簿の所在地欄にも文化財や年代の情報は含まれません。",
            "町資料は蔵泉寺を田能、太慶寺を大久保という小地域名で記す一方、県名簿はそれぞれ三倉4935、三倉4339です。二つの表記をどちらかへ統一して消すより、町建築資料の場所表現と法人所在地を左右に並べます。田能・大久保から現在の番地対応をさらに判断する場合は、別の地図資料が必要です。",
            "全光寺は県名簿の三倉2257で確認しますが、町建築資料に個別名がないことから建物の状態や年代を断定しません。長月寺、蔵泉寺、太慶寺、榮泉寺、金剛院も、町資料に書かれた項目だけを転記します。六寺すべてに同じ建築説明を当てず、県名簿の共通事項は所在地と法人・宗派情報に限ります。",
            "家族用索引では、金剛院を真言宗御室派として最初に分け、曹洞宗五寺を寺名と番地順で確認します。大石の視点では、山間部の住所を見ただけで道路状況、駐車、管理負担を説明せず、対象土地と寺院の位置を現地・地図で別々に確かめます。寺院訪問が必要なら公開住所、連絡方法、確認日、未確認条件を残します。",
            "三倉六寺の更新表は、真言宗御室派一と曹洞宗五の合計を確認し、六つの番地が重複なく寺名へ対応するかを見ます。町資料の田能・大久保表記は蔵泉寺4935、太慶寺4339の県名簿住所へ上書きせず、別列に保存します。金剛院山門と榮泉寺本堂も対象建物が違うため、文化財欄と年代欄を分けて再確認します。",
        ],
    }
    parts = [
        '<section class="directory-research" data-source-scope="temple-registry">',
        '<h2 class="sec">%s地区の寺院資料を読む</h2>' % esc(d["name"]),
        *("<p>%s</p>" % esc(paragraph) for paragraph in facts[d["district_id"]] + extensions[d["district_id"]]),
    ]
    parts.append('</section>')
    return "".join(parts)


def sect_research(sect, temples, dmeta):
    """Explain each denomination with its own source-grounded comparisons."""
    expected_counts = {"浄土宗": 1, "日蓮宗": 2, "真言宗": 2, "天台宗": 2, "曹洞宗": 28}
    if len(temples) != expected_counts[sect]:
        raise ValueError("寺院宗派件数が固有解説と不一致: %s" % sect)
    located = [t for t in temples if t.get("district_id") in dmeta]
    district_counts = Counter(dmeta[t["district_id"]]["name"] for t in located)
    distribution = "、".join("%s地区%dヶ寺" % (name, count) for name, count in sorted(district_counts.items()))
    facts = {
        "浄土宗": [
            "森町の浄土宗寺院は安養院1ヶ寺で、県名簿では一宮322に所在する浄土宗法人として掲載されています。1ヶ寺のみなので、宗派内の件数比較ではなく名称と所在地の確認に使うページです。",
            "町の寺院建築資料も安養院を町内唯一の浄土宗寺院として説明し、本堂を整形6間取りの前面に畳縁を付けた形式としています。県名簿は法人所在地、町資料は建築形式を扱うという役割の違いがあります。",
            "同じ一宮地区には天台宗の蓮増院、曹洞宗の極楽寺・高雲寺もあります。地区名だけで安養院を選ばず、浄土宗と一宮322を合わせて照合できます。",
        ],
        "日蓮宗": [
            "日蓮宗は報恩寺と本立寺の2ヶ寺です。報恩寺は森地区の向天方1255-1、本立寺は飯田地区の飯田1935-1にあり、別地区に1ヶ寺ずつ分かれます。",
            "町の寺院建築資料は日蓮宗2ヶ寺を同じ二寺名で示し、本立寺本堂の奥行きと内陣両側室の特徴を記録しています。報恩寺の所在地確認は県名簿、本立寺の建築説明は町資料というように根拠を分けます。",
            "向天方は地区台帳では森地区に含まれます。報恩寺を地名の字面から天方地区へ移さず、本立寺の飯田地区との二地区比較を保っています。",
        ],
        "真言宗": [
            "真言宗は2ヶ寺ですが包括団体が異なります。金剛院は真言宗御室派で三倉2308、遍照寺は真言宗智山派で飯田2130です。",
            "町資料は両寺の本堂について、前半を一室の外陣、奥を内陣と両脇間にする構成を説明しています。また町指定文化財として挙げるのは金剛院山門であり、遍照寺について同じ指定を示す記載ではありません。",
            "地区分布は三倉と飯田に各1ヶ寺です。『真言宗』だけでまとめず、御室派・智山派という県名簿の包括団体名、寺院名、所在地の三項目で比較します。",
        ],
        "天台宗": [
            "天台宗は蓮華寺と蓮増院の2ヶ寺です。蓮華寺は森地区の森2144、蓮増院は一宮地区の一宮3903に所在します。",
            "町の寺院建築資料は両寺の本堂を整形6間取りと説明し、蓮華寺については観音堂の移築も記録しています。県名簿の所在地情報と、町資料の建物情報を同じ種類の事実として混ぜないことが重要です。",
            "寺名は一字違いですが、県名簿では蓮華寺と蓮増院という別法人です。森2144と一宮3903、森地区と一宮地区まで併記すれば取り違えを避けられます。",
        ],
        "曹洞宗": [
            "県名簿で所在地まで確認できる曹洞宗法人は27ヶ寺です。六地区の内訳は%sで、これとは別に町の寺院建築資料が曹洞宗寺院として陽向院を掲載しています。" % distribution,
            "陽向院は町資料の建立年代表で薄場の寺院と記載されます。地区台帳では薄場は天方地区の大字群に含まれますが、今回の県名簿には陽向院の法人所在地を対応できないため、県名簿所在地から作る六地区27ヶ寺の集計とは別枠にしています。",
            "県名簿所在地による比較では森地区6ヶ寺、三倉・天方・園田が各5ヶ寺、飯田4ヶ寺、一宮2ヶ寺です。町資料の陽向院を足した総覧は28ヶ寺ですが、資料の母集団が異なるため28をそのまま法人件数とは表現しません。",
            "建築年代が記録される寺院の中では、三倉の榮泉寺本堂が元禄9年（1696年）で最古です。一方、県名簿は建立年代を扱わないため、この年代比較は町資料に限った記述です。",
            "同名簿では同じ曹洞宗でも、たとえば中川の雲林寺43-2と地蔵寺1269、森の梅林院2345と隨松寺2318のように近い大字内に複数寺院があります。宗派名の次に寺院名と番地を照合します。",
        ],
    }
    parts = [
        '<section class="directory-research" data-source-scope="temple-registry">',
        '<h2 class="sec">森町の%s寺院を資料で照合する</h2>' % esc(sect),
        *("<p>%s</p>" % esc(paragraph) for paragraph in facts[sect] + SECT_EXTENSIONS[sect]),
    ]
    parts.append('</section>')
    return "".join(parts)


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
        address_is_public = "未確認" not in (t.get("address") or "")
        address_label = t["address"] if address_is_public else "静岡県周智郡森町内（町公式資料に寺院名を掲載）"
        rows = []
        rows.append('<div class="ih-row"><span class="ih-key">宗派</span><span class="ih-val"><a href="/temple/sects/%s/">%s</a>（%s）</span></div>'
                    % (SECT_SLUG.get(t["sect"], "other"), esc(t["sect"]), esc(t["sect_full"])))
        rows.append('<div class="ih-row"><span class="ih-key">所在地</span><span class="ih-val">%s</span></div>' % esc(address_label))
        if t["district_id"]:
            d = dmeta[t["district_id"]]
            rows.append('<div class="ih-row"><span class="ih-key">地区</span><span class="ih-val"><a href="/temple/areas/%s/">%s</a></span></div>' % (d["slug"], esc(d["name"])))
        if t.get("corporate_status") and t["corporate_status"] != "未確認":
            rows.append('<div class="ih-row"><span class="ih-key">法人格</span><span class="ih-val">%s</span></div>' % esc(t["corporate_status"]))
        if t.get("cultural_property"):
            rows.append('<div class="ih-row"><span class="ih-key">文化財</span><span class="ih-val">%s</span></div>' % esc(t["cultural_property"]))
        if t.get("main_deity") and t["main_deity"] != "未確認":
            rows.append('<div class="ih-row"><span class="ih-key">本尊</span><span class="ih-val">%s</span></div>' % esc(t["main_deity"]))

        body = ['<div class="sacred-place-guide" data-content-quality="human-readable">']
        body.append('<aside class="instant-header" aria-label="基本情報"><p class="ih-title">基本情報</p>%s</aside>' % "".join(rows))
        body.append('<section><h2 class="sec">%sについて</h2>' % esc(t["name"]))
        if address_is_public:
            body.append('<p>%sは、%sに所在する%sの寺院です。静岡県の宗教法人名簿で、名称、包括団体、所在地を確認できます。</p>'
                        % (esc(t["name"]), esc(address_label), esc(t["sect_full"])))
        else:
            body.append('<p>%sは、森町教育委員会の寺院建築資料に名前が記されている%sの寺院です。今回参照した公開資料では詳しい所在地を確定できないため、町内にあるという範囲で案内します。</p>'
                        % (esc(t["name"]), esc(t["sect_full"])))
        if t.get("aliases"):
            body.append('<p>公開資料には「%s」という別称も記録されています。名称が違う資料を読むときは、所在地と宗派を合わせて同じ寺院かを見分けます。</p>' % esc("・".join(t["aliases"])))
        if t.get("main_deity") and t["main_deity"] != "未確認":
            body.append('<p>本尊は、参照資料で「%s」と確認できました。寺院へ問い合わせる際は、資料名と表記をそのまま伝えると行き違いを減らせます。</p>' % esc(t["main_deity"]))
        else:
            body.append('<p>本尊については、今回参照した公開資料から確かな案内を得られませんでした。宗派や寺名から推し量らず、公開されている所在地と宗派だけを掲載しています。</p>')
        body.append('</section>')

        research_sources = []
        if t["slug"] not in DEEP_RESEARCH_EXCLUDED:
            research_paragraphs, research_sources = temple_research(t)
            body.append('<section class="deep-research" data-research-checked="2026-08-10">'
                        '<h2 class="sec">一次資料から読み解く%s</h2>' % esc(t["name"]))
            body.append(research_figure(t, "temple"))
            split_at = min(5, len(research_paragraphs))
            for paragraph in research_paragraphs[:split_at]:
                body.append('<p>%s</p>' % esc(paragraph))
            body.append('</section>')
            body.append('<section class="deep-research-visit"><h2 class="sec">%sを訪ねる前の調べ方</h2>' % esc(t["name"]))
            for paragraph in research_paragraphs[split_at:]:
                body.append('<p>%s</p>' % esc(paragraph))
            body.append('</section>')

        if t.get("history_summary"):
            body.append('<section><h2 class="sec">建物・文化財の記録</h2><div class="note">%s</div>'
                        '<p>文化財の指定は、建物すべての公開や自由な見学を意味しません。見学できる範囲と撮影の可否は、現地掲示や寺院の案内に従ってください。</p></section>' % esc(t["history_summary"]))
        else:
            body.append('<section><h2 class="sec">由緒や建物について</h2>'
                        '<p>%sについて今回参照した名簿は、法人名、宗派、所在地を確認するための資料です。創建年、建物の年代、由緒、文化財の有無を説明する資料ではないため、このページでは付け加えていません。</p>'
                        '<p>由緒を知りたいときは、境内の説明板、寺院自身の案内、森町や文化財担当機関の資料を優先してください。地域の言い伝えは、公的な指定や年代記録と分けて読む必要があります。</p></section>'
                        % esc(t["name"]))

        body.append('<section><h2 class="sec">参拝・御朱印・法要について</h2>'
                    '<p>%sは信仰と法要の場であり、常時公開の観光施設とは限りません。このページでは、拝観時間、御朱印、寺務所の常駐、駐車場、トイレの利用を案内できる公開情報を確認できませんでした。</p>'
                    '<p>御朱印、墓地、法要、建物見学など明確な目的がある場合は、連絡先が公開されている公式情報を探し、寺院の日常を妨げない日時に相談してください。連絡先が見つからない場合、無断で建物内へ入ることはできません。</p></section>'
                    % esc(t["name"]))

        if address_is_public:
            body.append('<section><h2 class="sec">所在地と訪問時の配慮</h2>'
                        '<p>所在地は%sです。公開資料から入口、駐車場所、接道状況までは分からないため、地図上の建物位置だけで車の進入可否を決めないでください。</p>'
                        '<p>%sの周辺にある生活道路、農道、民有地、墓参者用の区画を観光駐車場として扱わず、現地の標識と案内を優先します。撮影では、墓石の名、法要中の人、近隣住宅や車の番号が写り込まないよう配慮が必要です。</p></section>' % (esc(address_label), esc(t["name"])))
        else:
            body.append('<section><h2 class="sec">所在地を断定しない理由</h2>'
                        '<p>公開資料で確認できるのは森町内の寺院名と宗派までです。住所や地図上の地点を推測して案内すると、別の寺院や私有地へ誘導するおそれがあるため掲載していません。</p>'
                        '<p>陽向院を訪ねる必要がある場合は、森町教育委員会の資料を起点に、寺院または地域の正規の連絡先を確認してください。名称だけを頼りに生活道路へ入ることは避けます。</p></section>')

        if t["district_id"]:
            d = dmeta[t["district_id"]]
            body.append('<section><h2 class="sec">%s地区と%sの寺院</h2>'
                        '<p>%sは森町の%s地区にあります。地区ページでは近隣の寺院を、宗派ページでは町内の%s寺院を一覧できます。寺院ごとの歴史や運営を一括りにせず、所在地を確かめるための関連資料としてご利用ください。</p>'
                        '<p><a href="/temple/areas/%s/">%s地区の寺院を見る</a> ／ '
                        '<a href="/temple/sects/%s/">森町の%s寺院を見る</a></p></section>'
                        % (esc(d["name"]), esc(t["sect"]), esc(t["name"]), esc(d["name"]), esc(t["sect"]),
                           d["slug"], esc(d["name"]), SECT_SLUG.get(t["sect"], "other"), esc(t["sect"])))

        if t["district_id"]:
            same = [x for x in by_d[t["district_id"]] if x["slug"] != t["slug"]]
            if same:
                body.append('<section><h2 class="sec">%s地区のほかの寺院</h2><div class="shrine-list">%s</div></section>'
                            % (esc(dmeta[t["district_id"]]["name"]), "".join(card(x) for x in same[:12])))

        body.append('<section><h2 class="sec">出典と更新日</h2><ul class="post-sources">')
        source_urls = set()
        for s in t["sources"]:
            body.append('<li><a href="%s" target="_blank" rel="noopener">%s</a>（%s）</li>' % (esc(s["url"]), esc(s["title"]), esc(s["note"])))
            source_urls.add(s["url"])
        for title, url, note in research_sources:
            if url not in source_urls:
                body.append('<li><a href="%s" target="_blank" rel="noopener">%s</a>（%s）</li>'
                            % (esc(url), esc(title), esc(note)))
                source_urls.add(url)
        temple_architecture_url = "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/shakaikyoikuka/bunkashinkogakari/2/774.html"
        if temple_architecture_url not in source_urls:
            body.append('<li><a href="%s" target="_blank" rel="noopener">森町教育委員会「森町の寺院建築」</a>（町内寺院の建築に関する公式資料）</li>' % temple_architecture_url)
        prefecture_registry_url = "https://www.pref.shizuoka.jp/kensei/gyoseikaikaku/1083643/1083669/1083677.html"
        if prefecture_registry_url not in source_urls:
            body.append('<li><a href="%s" target="_blank" rel="noopener">静岡県「宗教法人名簿」</a>（県知事所轄の宗教法人名簿と資料の確認先）</li>' % prefecture_registry_url)
        body.append('</ul><p>基本情報の確認日は%sです。公開資料にない本尊、御朱印、拝観条件、連絡先は補っていません。寺院関係者から訂正の連絡をいただいた場合は、根拠を確認して更新します。</p></section></div>' % esc(t["last_verified_at"]))

        addr_short = address_label.replace("静岡県周智郡森町", "森町") or (
            "森町%s" % (t.get("area") or ""))
        lead = "%s（%s）は、%sにある%sの寺院です。" % (t["name"], t["sect"], addr_short, t["sect"])
        if t.get("oldest_building"):
            lead += "本堂は元禄9年（1696年）建立で、森町の寺院建築では最古の記録とされています。"
        lead += "所在地、建築や文化財の公開記録、参拝前に確認したいことを一次資料に沿って整理します。"
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
        body.append(area_research(d, lst))
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
        body.append(sect_research(sect, lst, dmeta))
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
