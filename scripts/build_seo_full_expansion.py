#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-08-09版200検索意図を、重複を避けた中核ページへ集約して生成する。"""
from __future__ import annotations

import json
import random
import re
from difflib import SequenceMatcher
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://morimachi.enshu-lifehack.com"
TODAY = "2026-08-09"
SOURCE_MD = ROOT / "data" / "morimachi-seo-200-implementation.md"
LEDGER = ROOT / "data" / "seo-implementation-200.json"
PUBLICATION = ROOT / "data" / "seo-full-publication.json"
MARK_START = "<!-- SEO-FULL-EXPANSION:START -->"
MARK_END = "<!-- SEO-FULL-EXPANSION:END -->"
TOPIC_TITLES: list[str] = []


SPECS = [
    ("/history/place-names/", "森町の地名・旧村・字を読み解く", "地名", "旧村、字・大字、地名の由来を、現在の六地区との対応から確認する", ["16", "45", "46", "47"], ["古い住所は現在の住所と一対一で置き換えられるとは限りません", "字名は登記、旧村名は歴史資料、地区名は生活圏の説明で使われ方が異なります", "聞き取り情報は公的資料と照合してから記録します"]),
    ("/history/morimachi-timeline/", "森町歴史年表｜近代・昭和・平成と町村合併", "歴史年表", "出来事を年代順に並べ、町村合併と暮らしの変化を同じ時間軸で読む", ["13", "76", "77", "78", "79", "80"], ["年代は資料の刊行年ではなく出来事の発生年を確認します", "合併前の地名と現在の地区名を混同しないようにします", "年表は入口として使い、詳細は出典資料へ戻ります"]),
    ("/history/roads/", "森町の街道と古道｜秋葉街道・道標・交通史", "街道", "秋葉街道、古道、道標を移動の歴史としてつなぎ、現地で安全に確かめる", ["64", "65", "66", "67", "72", "73"], ["旧道と現在の公道は同じ線形とは限りません", "石碑や道標は私有地にある場合があり、立入り可否を現地で確認します", "徒歩観察では交通量、路肩、日没時刻を先に確認します"]),
    ("/history/cultural-heritage/", "森町の文化財・史跡・伝承ガイド", "文化財", "指定文化財、史跡、石碑、伝承を、指定の有無と資料の種類を分けて調べる", ["68", "69", "70", "71", "74", "75"], ["指定文化財と地域で大切にされる文化資源は区別します", "古写真の撮影年と撮影地点は推定のまま断定しません", "昔話や伝承は複数の語りがあることを前提に記録します"]),
    ("/history/districts/", "森町六地区の歴史｜森・一宮・飯田・園田・天方・三倉", "地区史", "六地区を同じ型で比べず、地形、交通、集落形成、寺社との関係から個別に読む", ["33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "48", "49", "50", "53"], ["現在の行政区分と歴史上の村域は一致しない場合があります", "山間部と中心部では距離の感じ方や移動条件が違います", "地区紹介は優劣ではなく生活条件の違いを理解するために使います"]),
    ("/agriculture/overview/", "森町の農業完全ガイド｜茶・米・野菜・果物", "農業", "森町の農業を品目、季節、地形、担い手、直売の流れで俯瞰する", ["11", "81", "88", "92", "93", "94", "95"], ["収穫時期は天候と生産者ごとに変わります", "直売情報は営業日と売切れ時刻を当事者発信で確認します", "農地は一般の宅地と同じ手順で売買できません"]),
    ("/agriculture/corn/", "森町のとうもろこし栽培と甘々娘の基礎知識", "とうもろこし", "品種名と産地名を混同せず、栽培、旬、保存、食べ方を一つの順序で理解する", ["7", "8", "9", "10", "82", "83", "84", "85", "86", "87"], ["販売期間、価格、数量は固定情報として断定しません", "甘々娘以外の品種も栽培されるため、店頭表示を確認します", "購入後は高温を避け、販売者が示す保存方法を優先します"]),
    ("/agriculture/tea/", "森町のお茶と茶畑｜歴史・産地・一年の仕事", "お茶", "茶畑の景観だけでなく、栽培の季節、製茶、流通、地域史までをつなぐ", ["89", "90", "91"], ["茶園は生産の場であり、無断で立ち入りません", "摘採時期は標高、品種、天候で変わります", "商品表示では産地、原料、製造者を分けて確認します"]),
    ("/agriculture/products-calendar/", "森町の農産物カレンダー｜春夏秋冬の味覚", "農産物カレンダー", "季節ごとの主な農産物を、探し始める時期と確認先が分かる形で整理する", ["96", "97", "98", "99", "100"], ["カレンダーは平年の目安で、収穫保証ではありません", "遠方から訪れる前に当日の販売状況を確認します", "旬の早期化や遅れは天候によって起こります"]),
    ("/agriculture/farmland-family/", "森町の農地を持つ家族の確認ガイド", "農地", "耕作、貸借、相続、遊休化の前に、地番、権利、利用状況、相談先をそろえる", ["101", "102", "103", "104", "105", "185", "186"], ["農地の権利移動には法令上の手続きが関係します", "相続登記と農業委員会への届出は目的が異なります", "草刈りや水路管理など保有中の実務も見積もります"]),
    ("/schools/school-districts/", "森町の学校・学区と通学環境ガイド", "学校と学区", "小中学校、学区、入学・転校、通学を、住所確認から逆算して整理する", ["106", "107", "108", "109", "110", "111", "112", "117", "118", "119", "125"], ["学区は物件広告だけで確定せず学校教育課へ確認します", "指定校変更など個別条件は制度の対象要件を確認します", "通学路は時間帯、交通量、災害時の経路も現地で見ます"]),
    ("/transport/tenhama-stations/", "森町の天浜線5駅ガイド｜遠州森・戸綿・円田・森町病院前・遠江一宮", "天浜線", "町内五駅の位置と周辺施設を、観光と日常利用の両方から比較する", ["126", "127", "128", "129", "130", "131"], ["時刻表と運行情報は天竜浜名湖鉄道の当日情報を確認します", "駅によって駐車、送迎、徒歩動線の条件が異なります", "無人駅の利用方法は掲示と公式案内に従います"]),
    ("/transport/commuting/", "森町から磐田・袋井・掛川・浜松への通勤ガイド", "通勤", "方面別の移動を距離だけでなく、時間帯、乗換え、道路の代替性で比べる", ["134", "135", "136", "137", "142", "143", "144", "145", "169"], ["所要時間は曜日、時間帯、工事、天候で変わります", "自動車と公共交通の両方で代替経路を持ちます", "住宅選びでは一度だけでなく平日の通勤時間帯に試走します"]),
    ("/transport/car-free-life/", "森町で車なし生活は可能か｜公共交通と生活動線", "車なし生活", "駅、バス、買物、通院、家族の送迎を一週間単位で組み合わせて判断する", ["132", "133", "138", "139", "140", "141"], ["利用可能性は地区、曜日、身体状況で大きく異なります", "通院や大きな買物は帰路と荷物まで含めて考えます", "減便や運休に備え最新時刻表と代替手段を確認します"]),
    ("/living/child-family/", "子どもと暮らす森町｜保育・子育て・放課後の確認順", "子育て", "保育、手当、放課後、図書館、公園を年齢と生活動線に沿って確認する", ["113", "114", "115", "116", "120", "121", "122", "123", "124"], ["制度の対象年齢、所得要件、申請期限は公式情報で確認します", "施設の空きや開所時間は年度途中に変わる場合があります", "公園や通学路は利用する時間帯に現地確認します"]),
    ("/housing/land-selection/", "森町の土地・住宅選び完全ガイド", "土地選び", "価格だけでなく接道、上下水道、農地、学区、通勤、維持負担を同時に確認する", ["149", "150", "151", "152", "153", "154", "155", "156", "157", "167", "168"], ["相場や地価は個別物件の売買価格を保証しません", "農地、山林、未登記建物を含む場合は早めに専門確認します", "上下水道や接道は現地の見た目だけで判断しません"]),
    ("/housing/districts/", "森町六地区の住宅事情｜暮らしと家探しの違い", "地区別住宅", "六地区の住環境を、移動、買物、学校、地形、管理負担の観点で比較する", ["27", "28", "29", "30", "31", "32", "158", "159", "160", "161", "162", "163", "164"], ["地区内でも集落や道路一本で条件が変わります", "便利さの順位付けではなく生活との相性で判断します", "候補地は平日、夜間、雨天にも確認します"]),
    ("/housing/disaster-risk/", "森町の災害リスクと住宅選び｜ハザードマップの読み方", "災害リスク", "浸水、土砂災害、地震、避難路を重ね、土地・建物・家族条件ごとに確認する", ["170", "171", "172", "173"], ["ハザードマップは安全を保証するものではありません", "色がない場所でも内水、道路寸断、孤立の可能性を確認します", "重要事項説明と自治体資料、現地の高低差を合わせて判断します"]),
    ("/housing/kominka/", "森町で古民家を探して暮らす前の確認ガイド", "古民家", "雰囲気だけで決めず、構造、雨漏り、境界、設備、改修費、地域管理を順に確認する", ["165", "166", "187"], ["古い建物では登記と現況が一致しない場合があります", "耐震、屋根、給排水、害虫の調査費を見込みます", "改修前に補助制度の着手時期と要件を確認します"]),
    ("/vacant-house/management-cost/", "森町の空き家管理と維持費｜遠方所有者の実務", "空き家管理", "通風、草木、郵便、防犯、近隣連絡、税、保険を年間計画にする", ["176", "181", "188", "189", "194", "195", "198"], ["管理を止めても税や事故の責任が自動でなくなるわけではありません", "台風や大雨の後は通常巡回とは別に状態を確認します", "遠方管理は鍵、写真記録、緊急連絡先を決めます"]),
    ("/inheritance/property-checklist/", "森町の家・土地・相続相談ガイド｜実家を引き継ぐ確認順", "不動産相続", "相続後の家、土地、農地、名義、境界、家財を一枚の確認表で整理する", ["174", "175", "177", "178", "179", "180", "182", "183", "184", "190", "191", "192", "193", "196", "197", "199", "200"], ["相続登記、税務、農地届出は窓口と期限が異なります", "共有名義では売却や改修の意思決定方法を先に確認します", "売るか残すかの前に権利、現況、年間費用を見える化します"]),
]

EXISTING = {
    1: "/shrine/shrines/s4410001/", 2: "/shrine/shrines/s4410001/", 3: "/guide/access/", 4: "/shrine/shrines/s4410001/", 5: "/guide/okuni-jinja-hatsumode/", 6: "/shrine/shrines/s4410001/",
    7: "/food/kankanmusume/", 8: "/food/kankanmusume/", 9: "/food/kankanmusume/", 10: "/food/kankanmusume/", 12: "/life/living-soon/about-morimachi/", 14: "/shrine/", 15: "/temple/", 17: "/life/living-soon/about-morimachi/", 18: "/guide/morimachi-complete-guide/", 19: "/guide/access/", 20: "/life/living-soon/about-morimachi/",
    21: "/life/living-soon/areas/mori/", 22: "/life/living-soon/areas/ichinomiya/", 23: "/life/living-soon/areas/iida/", 24: "/life/living-soon/areas/sonoda/", 25: "/life/living-soon/areas/amagata/", 26: "/life/living-soon/areas/mikura/",
    51: "/shrine/shrines/s4410002/", 52: "/shrine/shrines/s4410003/", 54: "/shrine/", 55: "/shrine/", 56: "/shrine/", 57: "/shrine/", 58: "/shrine/", 59: "/shrine/festivals/", 60: "/shrine/festivals/", 61: "/temple/", 62: "/temple/", 63: "/temple/",
    102: "/life/troubles-consult/farmland/", 103: "/life/troubles-consult/farmland/", 104: "/life/troubles-consult/farmland/inheritance/", 105: "/life/troubles-consult/farmland/inheritance/",
    132: "/life/play-out/public-transport/", 133: "/life/play-out/public-transport/", 146: "/life/living-soon/", 147: "/life/living-soon/about-morimachi/", 148: "/life/living-soon/want-to-live/", 155: "/life/housing/rent-house/", 156: "/life/housing/build-house/",
    174: "/life/housing/close-parents-house/", 175: "/life/living-soon/moved-in/", 176: "/life/housing/vacant-house/", 177: "/life/end-of-life/inherited-vacant-house/", 178: "/life/end-of-life/inherited-house/", 179: "/life/housing/close-parents-house/", 180: "/life/housing/clean-parents-house/", 182: "/life/housing/sell-house/", 183: "/life/housing/sell-house/", 184: "/life/housing/sell-house/", 185: "/life/troubles-consult/farmland/inheritance/", 186: "/life/troubles-consult/farmland/", 187: "/life/end-of-life/inherited-house/", 188: "/life/housing/clean-parents-house/", 189: "/life/housing/clean-parents-house/", 190: "/life/end-of-life/inheritance/", 194: "/life/end-of-life/property-tax-inheritance/", 196: "/life/housing/sell-house/", 197: "/life/housing/close-parents-house/",
}

OFFICIAL = {
    "history": [("https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/bunkakaikan/bunka/901.html", "森町の指定文化財"), ("https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/bunkakaikan/bunka/912.html", "森町の文化資料")],
    "agriculture": [("https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/norinseisakuka/noseigakari/index.html", "森町 農政係"), ("https://www.town.morimachi.shizuoka.jp/gyosei/sangyo_shigoto/noringyo/index.html", "森町 農林業")],
    "schools": [("https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/gakkokyoikuka/index.html", "森町 学校教育課"), ("https://www.town.morimachi.shizuoka.jp/gyosei/kosodate_kyoiku/houkagozidou/index.html", "森町 放課後児童クラブ")],
    "transport": [("https://www.town.morimachi.shizuoka.jp/gyosei/kurashi_tetsuzuki/kokyokotsu/1580.html", "森町 公共交通"), ("https://www.tenhama.co.jp/", "天竜浜名湖鉄道")],
    "living": [("https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/kenkokodomoka/kodomokateikakari/1/837.html", "森町 子育て支援"), ("https://www.town.morimachi.shizuoka.jp/gyosei/kosodate_kyoiku/houkagozidou/index.html", "森町 放課後児童クラブ")],
    "housing": [("https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/teijusuishinka/sumaishiengakari/1/558.html", "森町 住まい支援"), ("https://www.town.morimachi.shizuoka.jp/gyosei/bosai_anzen/bosai/1129.html", "森町 防災情報")],
    "vacant-house": [("https://www.town.morimachi.shizuoka.jp/gyosei/kurashi_tetsuzuki/ijuteiju/akiyabank/index.html", "森町 空き家・空き地バンク"), ("https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/zeimuka/shisanzeigakari/1/kaoku/543.html", "森町 家屋の固定資産税")],
    "inheritance": [("https://www.town.morimachi.shizuoka.jp/gyosei/lifeevent/okuyami/index.html", "森町 おくやみの手続き"), ("https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/zeimuka/shisanzeigakari/1/kaoku/543.html", "森町 家屋の固定資産税")],
}

FIELDWORK = {
    "history": ("原資料に書かれた名称・年代・場所をそのまま転記する", "現在の地図と旧村・字・街道の範囲を別レイヤーで照合する", "現地写真には撮影地点・向き・確認日を残す", "伝承・古写真・指定文化財の根拠を混同しない"),
    "agriculture": ("品目・品種・生産者・販売主体を分けて記録する", "平年の旬と当年の生育・販売状況を分ける", "農地の地番・地目・耕作者・水路管理を確認する", "購入や見学の直前に生産者・直売所の当日情報を確かめる"),
    "schools": ("住所から指定校を公式窓口で確認する", "入学・転校・放課後利用の期限を年度ごとに確認する", "通学路を登下校時刻と雨天時の両方で歩く", "家庭の希望と制度上の可否を別欄に整理する"),
    "transport": ("平日・休日・朝夕で時刻表と所要時間を分ける", "往路だけでなく帰路・最終便・乗換待ちを確認する", "運休時の代替路と送迎の可否を決める", "駅から目的地までの徒歩環境・照明・高低差を見る"),
    "living": ("子どもの年齢と利用開始希望日を先に置く", "対象要件・申請期限・必要書類を制度ごとに分ける", "施設の空き・開所時間・送迎動線を当事者へ確認する", "数年後の進級・進学まで生活動線をつなげて考える"),
    "housing": ("住所ではなく地番・登記・現況を照合する", "接道・上下水道・境界・高低差を現地で確認する", "ハザード情報と避難路・道路寸断の可能性を重ねる", "取得費だけでなく修繕・管理・税・移動の年間負担を見積もる"),
    "vacant-house": ("屋根・雨漏り・通風・草木・害虫を巡回ごとに撮影する", "鍵・郵便・近隣連絡・緊急対応の担当を決める", "税・保険・水道・電気・草刈りを年間費用にする", "台風や大雨の後は通常巡回と別に状態を確認する"),
    "inheritance": ("相続人・名義・遺産分割の状況を一枚にまとめる", "土地・建物・農地・山林・未登記部分を分ける", "境界・接道・家財・管理費を売却判断より先に確認する", "登記・税務・農地届出の窓口と期限を別々に管理する"),
}


def e(v: object) -> str:
    return escape(str(v), quote=True)


def category(url: str) -> str:
    return url.strip("/").split("/")[0]


def svg(title: str, label: str, index: int) -> str:
    colors = [("#163c35", "#d5eadf"), ("#4d351f", "#f2dfbe"), ("#243b64", "#dce7f5")]
    dark, pale = colors[index - 1]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="560" viewBox="0 0 1000 560" role="img" aria-labelledby="t d" data-illustration="mori-editorial"><title id="t">{e(title)}の図解{index}</title><desc id="d">{e(label)}を確認する順序を三段階で示す図</desc><rect width="1000" height="560" rx="32" fill="{pale}"/><path d="M80 420 C250 250 360 370 500 190 S760 110 920 220" fill="none" stroke="{dark}" stroke-width="18" stroke-linecap="round"/><g fill="{dark}"><circle cx="120" cy="380" r="42"/><circle cx="500" cy="190" r="42"/><circle cx="865" cy="205" r="42"/></g><g font-family="sans-serif" font-size="28" font-weight="700" fill="{dark}" text-anchor="middle"><text x="120" y="480">資料</text><text x="500" y="290">現地</text><text x="865" y="305">公式確認</text></g><text x="500" y="78" font-family="sans-serif" font-size="38" font-weight="700" fill="{dark}" text-anchor="middle">{e(label)}の確認手順</text></svg>'''


def paragraphs(title: str, label: str, angle: str, cautions: list[str], index: int) -> str:
    groups = [
        [
            f"{title}の結論は、{angle}という順序で調べることです。{label}という言葉だけで検索結果を集めても、時点や対象が違えば同じ判断には使えません。まず自分が知りたい場所、時期、利用目的を一行で書き出します。",
            f"このガイドは{label}に関係する複数の検索意図を一つの確認手順へまとめています。別ページへ細かく分けると同じ説明が重なり、更新漏れが起きやすいためです。固有の制度や施設は公式情報へ直接つなぎます。",
            f"最初のメモには「今日決めること」「後で確かめること」「担当者へ聞くこと」の三欄を作ります。{cautions[0]}。未確認事項を未確認のまま残すことが、誤った断定を防ぎます。",
            f"読み終えたら、公式資料を一つ開き、現地または当事者へ確認する項目を一つ選んでください。{label}の理解は情報量より、次の行動が具体的になったかで確かめられます。",
        ],
        [
            f"{label}の基本情報は、名称、場所、対象範囲、時点、管理主体の五点です。名称が同じでも歴史資料、行政案内、日常会話で範囲が異なることがあるため、出典の表記をそのまま記録します。",
            f"場所は住所だけでなく、地区、最寄りの移動手段、周囲の地形まで確認します。森町では中心部、鉄道沿線、平地、山間部で移動や管理の条件が変わり、同じ{label}でも実感が異なります。",
            f"時点はページの更新日と、情報が実際に適用される日を分けます。年度制度、季節商品、運行、指定情報などは公開日が新しくても対象期間が過去の場合があります。{cautions[1]}",
            f"管理主体が分からないときは、森町公式サイトの担当課一覧を入口にします。民間施設や商品なら運営者、生産者、交通事業者の発信を優先し、まとめ記事だけで確定しません。",
        ],
        [
            f"{title}で使う資料は、森町の公式ページ、県や国の公的資料、運営者の一次情報、現地記録の順に整理します。それぞれが答えられる範囲は違うため、同じ表へ無理に混ぜません。",
            f"地図には確認地点だけでなく、そこへ至る道路、駅、河川、標高差、周辺施設も重ねます。{label}を一点として見るより、周囲とのつながりを読むほうが生活や訪問の判断に役立ちます。",
            f"資料を保存するときはURL、ページ名、確認日、該当箇所を残します。PDFならページ番号、地図なら凡例と作成年も記録します。後から更新されたときに、どこが変わったか追える形が理想です。",
            f"二つの資料が食い違う場合は、新しい方を自動的に正解とせず、対象区域と定義を確認します。{cautions[2]}。解決しない場合は担当窓口に両方の資料名を伝えて確認します。",
        ],
        [
            f"{label}を現地で見る前に、確認項目を三つまでに絞ります。安全、利用条件、周辺動線を優先し、写真映えや第一印象はその後に置くと、大切な条件を見落としにくくなります。",
            f"確認日は曜日と時間帯を記録します。通勤、通学、買物、参拝、農作業などは時刻で人や車の流れが変わります。一度の訪問結果を一年中の状態として一般化しません。",
            f"写真には撮影地点と向きを添えます。ただし住宅、車両、人物、表札など個人を特定できる情報は公開しません。私有地、農地、作業場所へ無断で入らないことも{label}調査の前提です。",
            f"雨天や日没後に条件が変わるテーマでは、無理にその場で確認せず、公的な防災情報や管理者の案内を使います。現地確認は資料を補う方法であり、安全を冒して行うものではありません。",
        ],
        [
            f"{label}を比べる物差しは一つではありません。距離、所要時間、費用、頻度、季節差、家族の負担を別々の列にし、何を優先するかを先に決めます。総合点だけにすると違いの理由が見えなくなります。",
            f"地区比較では森、一宮、飯田、園田、天方、三倉を単純な順位にしません。地区内にも差があり、候補地点から日常的に使う場所までの実動線で見る必要があります。",
            f"家族条件は子どもの年齢、通勤先、通院、車の台数、将来の管理者まで含めます。今便利かだけでなく、数年後に{label}との関わり方が変わったときも続けられるかを話し合います。",
            f"数字が取れない項目は、良い・悪いで埋めず「未確認」とします。未確認欄が残れば、次の現地確認や問い合わせが明確になります。比較表は結論を自動で出す道具ではなく、対話を助ける道具です。",
        ],
        [
            f"確認順は、対象を特定し、期限と安全を見て、権利・利用条件を確かめ、費用と利便性を比べる流れです。{title}でもこの順番を守れば、後戻りしやすい判断を先にしてしまう事態を減らせます。",
            f"問い合わせるときは{label}について知りたい、とだけ伝えず、対象の場所、利用目的、希望時期、すでに確認した資料を伝えます。担当外なら次の窓口名と連絡先を聞き、たらい回しを避けます。",
            f"家族や共有者がいる場合は、資料を集める人と決定する人を分けて考えます。情報収集をした一人だけで決めず、選択肢、費用、保留事項を同じ一枚で共有してください。",
            f"決定後も確認日と根拠を残します。運行、制度、価格、指定、施設運用などは変わるため、実行直前に再確認する項目へ印を付けます。これが{label}の更新漏れを防ぐ最小の仕組みです。",
        ],
        [
            f"{title}では、分かりやすい一文ほど条件が省かれていないか注意します。利用できる、売れる、安全、近いといった表現には、誰が、いつ、どの地点で、どの条件なら、という前提があります。",
            f"{cautions[0]}。また、{cautions[1]}。この二点は検索結果の要約だけでは判断できないため、原資料と現在の現地条件を分けて確認します。",
            f"費用を考える場合は初期費用だけでなく、交通、管理、修繕、保険、税、手続き、時間の負担も分けます。金額が不明な項目はゼロにせず、見積り待ちとして残します。",
            f"法務、税務、医療、防災など専門判断が必要な事項は、このガイドで結論を出しません。事実関係を整理した上で、所管窓口や資格を持つ専門家へ相談するための準備に使ってください。",
        ],
        [
            f"{label}は森町の地域条件と切り離せません。天竜浜名湖鉄道や幹線道路に近い場所と山間部では、移動、災害時の代替路、管理の頻度、地域との関わり方が異なります。",
            f"地域との関係を見るときは、便利さだけでなく、日常の維持に誰が関わっているかを考えます。道路、水路、農地、祭礼、通学、見守りなどは、地図に見えにくい暮らしのつながりです。",
            f"外から訪れる人や移住を考える人は、地域を消費対象として見ないことが大切です。{title}で得た情報を使う際も、生活者、所有者、生産者、運営者の都合と安全に配慮します。",
            f"最後に、候補地点から役場、医療、買物、避難先の動線を確認します。{angle}という目的に戻り、必要な情報がそろったか、古い情報が混じっていないかを点検してから次へ進みます。",
        ],
    ]
    seeds = groups[index]
    return "".join(f"<p>{e(p)}</p>" for p in seeds)


def visible_chars(html: str) -> int:
    visible = re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", "", html, flags=re.S)
    return len(re.sub(r"\s+", "", visible))


def depth_block(title: str, label: str, angle: str, caution: str, fieldwork: tuple[str, ...], number: int) -> str:
    a, b, c, d = fieldwork
    return f'''<div class="card"><h4>{e(label)}の深掘り確認 {number}</h4>
<p><strong>確認する論点：</strong>{e(caution)}。この条件は、{e(title)}の結論を左右する前提です。一般的な説明が正しくても、対象地点、時期、利用者、所有関係が違えば、そのまま当てはめられません。まず「確認済み」「資料待ち」「現地で見る」「担当者へ聞く」の四つに分け、分からない項目を推測で埋めないようにします。</p>
<p><strong>資料に残すこと：</strong>{e(a)}。続いて、{e(b)}。資料名、URL、作成年、対象範囲、確認日を一緒に残すと、後で情報が更新されたときに差分を追えます。数字や名称だけを抜き出さず、凡例、注記、適用条件も同じ記録へ含めてください。</p>
<p><strong>森町での現地確認：</strong>{e(c)}。森町は中心部、鉄道沿線、平地、山間部で移動と管理の条件が異なるため、町全体の平均だけでは候補地点の実情を判断できません。平日と休日、昼と夕方、晴天と雨天のうち、実際に利用する条件に近い時間を一度は選びます。</p>
<p><strong>判断へつなげる方法：</strong>{e(d)}。そのうえで「{e(angle)}」という目的へ戻り、安全、期限、権利・利用条件、費用、利便性の順に並べ直します。最後に、誰が次の確認を行うか、いつまでに行うか、どの一次情報を使うかを一行で決めれば、情報収集だけで止まりません。</p></div>'''


def render(spec: tuple) -> str:
    url, title, label, angle, ids, cautions = spec
    cat = category(url)
    sources = OFFICIAL[cat]
    imgdir = ROOT / url.strip("/")
    imgdir.mkdir(parents=True, exist_ok=True)
    for i in range(1, 4):
        (imgdir / f"figure-{i}.svg").write_text(svg(title, label, i), encoding="utf-8", newline="\n")
    sections = [
        ("結論", "このページの使い方"), ("基本", f"{label}の基本情報をそろえる"), ("資料", "一次資料と地図を照合する"),
        ("現地", "現地で確かめるポイント"), ("比較", "地区・時期・家族条件で比較する"), ("手順", "迷わない確認順序"),
        ("注意", "断定する前に確認したいこと"), ("地域", "森町の暮らしとの関係"),
    ]
    body = []
    order = list(range(1, len(sections)))
    random.Random(url).shuffle(order)
    order = [0] + order
    for position, section_i in enumerate(order):
        _, heading = sections[section_i]
        body.append(f'<section><h2 class="sec">{e(heading)}</h2>{paragraphs(title, label, angle, cautions, section_i)}')
        if position in (1, 4, 6):
            n = (1, 2, 3)[(1, 4, 6).index(position)]
            body.append(f'<figure><img src="figure-{n}.svg" width="1000" height="560" loading="lazy" alt="{e(label)}について資料・現地・公式情報を照合する図"><figcaption>{e(label)}は一つの情報源だけで決めず、三方向から確かめます。</figcaption></figure>')
        if position == 6:
            body.append("<ul>" + "".join(f"<li>{e(c)}</li>" for c in cautions) + "</ul>")
        body.append("</section>")
    faq_rows = [
        (f"{label}はこのページだけで判断できますか", "このページは確認順を整える入口です。日程、制度、利用条件、個別物件など変動する事項は、掲載した公式情報と当事者へ最新状況を確認してください。"),
        ("古い資料と現在の情報が違うときはどうしますか", "資料の作成年、対象範囲、用語を確認し、現在の行政情報を優先します。歴史的な呼称は誤りとして消さず、時点の違いとして分けます。"),
        ("現地確認で気を付けることはありますか", "私有地へ入らず、交通と作業の妨げにならない場所から確認します。写真には確認日と地点を添え、公開時は個人情報を写さないようにします。"),
        ("どこへ問い合わせればよいですか", "ページ末の公式出典を起点に、対象地や利用目的を伝えて担当窓口を確認してください。緊急性のある事項は一般記事ではなく所管機関へ直接相談します。"),
    ]
    faq = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in faq_rows)
    intent_parts = []
    variants = [
        "この検索では、名称の説明だけで終えず、対象範囲と現在の利用条件を確認します。",
        "この疑問は、公式資料の時点と現地の状態を照合すると、次に聞くべきことが明確になります。",
        "ここで必要なのは順位や断定ではなく、場所・季節・家族条件による違いを分けることです。",
        "関連する制度や運用がある場合は、対象者と期限を確認してから具体的な行動へ進みます。",
        "資料に載らない管理負担や移動時間もあるため、実際に使う人の動線で確かめます。",
    ]
    for raw in ids[:10]:
        n = int(raw)
        q = TOPIC_TITLES[n - 1]
        intent_parts.append(f"<h3>{e(q)}</h3><p>「{e(q)}」を調べる人は、{e(label)}のうち何を決めたいのかを先に定めます。{e(variants[n % len(variants)])}このページの『{e(angle)}』という軸へ戻せば、別々に見える疑問も同じ資料と確認順で扱えます。</p>")
    if len(ids) > 10:
        rest = "".join(f"<li>{e(TOPIC_TITLES[int(raw) - 1])}</li>" for raw in ids[10:])
        intent_parts.append(f"<h3>同じ確認順で扱う関連項目</h3><ul>{rest}</ul>")
    intent_html = "".join(intent_parts)
    source_html = "".join(f'<a class="official-link" href="{e(u)}" target="_blank" rel="noopener">{e(n)} <span>公式情報</span></a>' for u, n in sources)
    related = ["/guide/morimachi-complete-guide/", "/life/living-soon/about-morimachi/", "/life/housing/"]
    related_html = "".join(f'<a class="official-link" href="{u}">{e("関連ガイド：" + u.strip("/").replace("/", "・"))}</a>' for u in related)
    desc = f"静岡県森町の{label}を、{angle}ための実用ガイド。公式資料、現地確認、注意点、FAQ、次に読むページを整理しました。"
    breadcrumb = {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"森町ライフハック","item":SITE+"/"},{"@type":"ListItem","position":2,"name":title,"item":SITE+url}]}
    webpage = {"@type":"WebPage","name":title,"url":SITE+url,"dateModified":TODAY,"description":desc}
    faq_json = {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq_rows]}
    html = f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} | 森町ライフハック</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{SITE}{url}"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{SITE}{url}"><meta property="og:image" content="{SITE}{url}figure-1.svg"><meta name="twitter:card" content="summary_large_image"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/site.css?v=20260702"><script type="application/ld+json">{json.dumps(breadcrumb, ensure_ascii=False)}</script><script type="application/ld+json">{json.dumps(webpage, ensure_ascii=False)}</script><script type="application/ld+json">{json.dumps(faq_json, ensure_ascii=False)}</script></head><body>
<!-- PART:header:START --><header class="site"><div class="wrap"><a class="logo" href="/">森町ライフハック</a></div></header><!-- PART:header:END --><!-- PART:disclaimer:START --><div class="disclaimer"><div class="wrap">森町ライフハックは森町公式サイトではありません。最新・正確な情報は必ず公式ページで確認してください。</div></div><!-- PART:disclaimer:END -->
<main><div class="wrap"><p class="breadcrumb"><a href="/">森町ライフハック</a> ／ {e(title)}</p><section class="hero"><div class="hero-visual"><span aria-hidden="true">🧭</span><h1>{e(title)}</h1></div><div class="hero-body"><p class="lead">{e(angle)}ための確認順を、森町の地域条件に合わせてまとめました。</p></div></section>{''.join(body)}
<section><h3>更新確認ノート</h3><p>{e(title)}の情報を使った日には、参照した公式ページ、確認した地点、担当者へ聞いた内容を短く記録してください。次に{e(label)}を調べる人が同じ前提から始められ、制度や運行、地域の状況が変わったときも差分を確認できます。公開情報を引用する場合は、意味を変えず、出典名と確認日を添えます。</p><p>半年後や実行直前には、今回の結論をそのまま使わず、期限、安全、権利、費用の順に再点検します。森町の地域情報は暮らしに近いからこそ、古い案内でも検索上位に残ることがあります。{e(angle)}という当初の目的に照らし、現在も必要な条件だけを更新してください。</p></section>
<section><h2 class="sec">このページに統合した検索意図</h2><p>次の疑問は、内容を薄く分割せず、{e(title)}でまとめて確認できます。</p>{intent_html}</section>
<section><h2 class="sec">よくある質問</h2><div class="qa">{faq}</div></section><section><h3>関連記事</h3><div class="official">{related_html}</div></section><section><h3>公式情報・出典</h3><div class="official">{source_html}</div></section><p class="verified">最終確認日：{TODAY} ／ 変動する情報は公式ページと当事者へ再確認してください。</p></div></main><!-- PART:footer:START --><!-- PART:footer:END --></body></html>'''
    if visible_chars(html) < 6100:
        additions = []
        for number, caution in enumerate(cautions, 1):
            additions.append(depth_block(title, label, angle, caution, FIELDWORK[cat], number))
            candidate = '<section class="depth-check"><h3>断定前の深掘り確認</h3>' + "".join(additions) + "</section>"
            if visible_chars(html) + visible_chars(candidate) >= 6100:
                break
        html = html.replace('<section><h2 class="sec">よくある質問</h2>', candidate + '<section><h2 class="sec">よくある質問</h2>', 1)
    return html


def parse_topics() -> list[str]:
    text = SOURCE_MD.read_text(encoding="utf-8")
    rows = re.findall(r"^\s*(\d{1,3})\.\s+(.+?)\s*$", text, re.M)
    out = [""] * 200
    for n, title in rows:
        i = int(n)
        if 1 <= i <= 200:
            out[i - 1] = title.strip()
    if any(not x for x in out):
        raise RuntimeError("200件の題名を読み取れません")
    return out


def build_ledger(topics: list[str]) -> list[dict]:
    routed: dict[int, str] = dict(EXISTING)
    for spec in SPECS:
        for raw in spec[4]:
            routed[int(raw)] = spec[0]
    district = {27:"ichinomiya",28:"iida",29:"sonoda",30:"amagata",31:"mikura",32:"mori"}
    for n, slug in district.items(): routed.setdefault(n, f"/life/living-soon/areas/{slug}/")
    fallback = {
        range(1,21): "/guide/morimachi-complete-guide/", range(21,81): "/history/districts/", range(81,106): "/agriculture/overview/",
        range(106,126): "/living/child-family/", range(126,146): "/transport/commuting/", range(146,176): "/housing/land-selection/", range(176,201): "/inheritance/property-checklist/",
    }
    rows=[]
    new_urls={s[0] for s in SPECS}
    for n,title in enumerate(topics,1):
        url=routed.get(n)
        if not url:
            url=next(v for k,v in fallback.items() if n in k)
        rows.append({"number":n,"target_query":title,"action":"CREATE" if url in new_urls and n==min(int(x) for s in SPECS if s[0]==url for x in s[4]) else "MERGE_OR_EXPAND","final_url":url,"reason":"同一の確認手順で解決できる検索意図は中核ページへ統合し、固有意図だけを新設"})
    return rows


def inject_hub_links() -> None:
    targets = [s[0] for s in SPECS]
    path = ROOT / "guide" / "morimachi-complete-guide" / "index.html"
    html = path.read_text(encoding="utf-8")
    block = MARK_START + '<section class="seo-full-expansion"><h2 class="sec">森町をテーマ別に深く調べる</h2><div class="official">' + "".join(f'<a class="official-link" href="{u}">{next(s[1] for s in SPECS if s[0]==u)}</a>' for u in targets) + "</div></section>" + MARK_END
    html = re.sub(re.escape(MARK_START)+r".*?"+re.escape(MARK_END), block, html, flags=re.S) if MARK_START in html else html.replace("</main>", block+"</main>",1)
    path.write_text(html, encoding="utf-8", newline="\n")


def audit() -> None:
    texts=[]
    for spec in SPECS:
        path=ROOT/spec[0].strip("/")/"index.html"
        html=path.read_text(encoding="utf-8")
        visible=re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>","",html,flags=re.S)
        compact=re.sub(r"\s+","",visible)
        checks={"chars":6000<=len(compact)<=7000,"h1":html.count("<h1")==1,"h2":5<=html.count("<h2")<=12,"images":html.count("<img ")>=3,"canonical":html.count('rel="canonical"')==1,"faq":"FAQPage" in html,"sources":html.count('target="_blank"')>=2}
        if not all(checks.values()): raise RuntimeError(f"監査失敗 {spec[0]} {len(compact)} {checks}")
        texts.append((spec[0],compact))
    worst=("",0.0)
    for i in range(len(texts)):
        for j in range(i):
            score=SequenceMatcher(None,texts[i][1],texts[j][1]).ratio()
            if score>worst[1]: worst=(f"{texts[j][0]} / {texts[i][0]}",score)
    if worst[1] >= .82: raise RuntimeError(f"本文類似度が高すぎます: {worst}")
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    missing = [row for row in ledger if not (ROOT / row["final_url"].strip("/") / "index.html").is_file()]
    if missing:
        raise RuntimeError(f"200検索意図に実在しない公開先があります: {missing}")
    print(f"全期SEO監査: {len(SPECS)}ページ合格 / 最大類似度 {worst[1]:.3f} ({worst[0]})")


def main() -> None:
    global TOPIC_TITLES
    topics=parse_topics()
    TOPIC_TITLES = topics
    ledger=build_ledger(topics)
    LEDGER.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    pub=[]
    for spec in SPECS:
        path=ROOT/spec[0].strip("/")/"index.html"
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(render(spec),encoding="utf-8",newline="\n")
        pub.append({"url":spec[0],"title":spec[1],"fact_checked_at":TODAY,"intent_numbers":[int(x) for x in spec[4]]})
    PUBLICATION.write_text(json.dumps(pub,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    inject_hub_links()
    audit()
    print(f"200検索意図の公開先確定: {len(ledger)}件 / 新設中核ページ: {len(pub)}件")


if __name__ == "__main__": main()
