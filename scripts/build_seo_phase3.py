#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""200ページ改修計画の第3期（No.1〜60）を安全な公開単位で確定する。"""
from __future__ import annotations

import importlib.util
import json
import re
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TODAY = "2026-08-09"
SOURCE = ROOT / "data" / "seo-renovation-200.json"
DECISIONS = ROOT / "data" / "seo-phase3-decisions.json"
PUBLICATION = ROOT / "data" / "seo-phase3-publication.json"
LINK_START = "<!-- SEO-PHASE3-LINKS:START -->"
LINK_END = "<!-- SEO-PHASE3-LINKS:END -->"
SACRED_DETAIL_PREFIXES = ("/shrine/shrines/", "/temple/temples/")

loader = importlib.util.spec_from_file_location("full", ROOT / "scripts" / "build_seo_full_expansion.py")
full = importlib.util.module_from_spec(loader)
assert loader.loader
loader.loader.exec_module(full)

SPECS = [
    ("/guide/one-day-course/", "森町観光モデルコース｜一日で歴史・自然・町歩き", "一日観光", "移動時間と滞在時間を分け、詰め込みすぎない一日を組み立てる", [3,4,9], ["施設の営業日や催事日程は訪問日直前に確認します", "山間部と中心部を同日に回る場合は移動の余白を取ります", "食事や買物は売切れと臨時休業を前提に代案を持ちます"]),
    ("/guide/train-trip/", "天浜線で巡る森町｜駅から歩く電車旅ガイド", "天浜線の電車旅", "町内駅から目的地までの往復動線と帰りの列車を先に決める", [5], ["時刻表と運行情報は天竜浜名湖鉄道の当日案内を確認します", "駅ごとに徒歩距離や道路環境が異なります", "最終列車だけでなく目的地から駅へ戻る時間も見込みます"]),
    ("/guide/family-trip/", "子どもと楽しむ森町｜家族旅行の計画と安全確認", "子連れ観光", "年齢、休憩、食事、トイレ、安全を一日の動線に重ねて計画する", [8], ["年齢制限や設備は各施設へ事前に確認します", "川や山では天候と増水、足元の状態を優先します", "混雑時に家族が離れた場合の集合場所を決めます"]),
    ("/guide/senior-friendly-trip/", "無理なく巡る森町｜シニア向け観光計画ガイド", "ゆとりある観光", "歩行距離、段差、休憩、移動手段を先に確認して訪問先を絞る", [10], ["坂や砂利、階段の状態は現地・施設へ確認します", "体調と気温に合わせて途中で切り上げられる計画にします", "介助や車いす対応は利用施設へ個別に問い合わせます"]),
    ("/food/souvenirs/", "森町のお土産選び｜お茶・農産物・菓子の確認ガイド", "森町のお土産", "渡す相手、保存条件、持ち運び時間、産地表示を確認して選ぶ", [43], ["販売品と在庫は季節や店舗で変わります", "要冷蔵品は帰宅までの時間と保冷方法を確認します", "森町産・森町製造など表示の意味を分けて見ます"]),
    ("/history/mori-no-ishimatsu/", "森の石松と森町｜伝承・浪曲・史料を分けて読む", "森の石松", "物語として広まった像と確認できる地域資料を分けてたどる", [47], ["浪曲や講談の筋書きを史実として断定しません", "墓所や伝承地では寺社と地域の案内に従います", "異なる説は優劣を決めず出典と成立時期を記録します"]),
    ("/shrine/shrines/s4410002/", "森町・天宮神社｜御祭神・舞楽・参拝の確認ガイド", "天宮神社", "神社庁の登録事実と文化財資料を照合し、舞楽の日程は当年情報で確かめる", [20], ["祭礼日は年ごとの公式案内で再確認します", "御祭神名は出典の表記を尊重します", "境内では祭礼運営と参拝者の動線を妨げません"]),
    ("/shrine/shrines/s4410004/", "森町・三島神社｜森のまつりと地域の氏神", "三島神社", "神社庁の登録情報を起点に、祭礼と地域の関係を現在の案内で確かめる", [22], ["祭礼時刻と交通規制は当年の運営案内を確認します", "御祭神は公開資料で未確認のため推測しません", "屋台の運行経路や見学場所は現地誘導に従います"]),
    ("/shrine/shrines/s4410003/", "森町・山名神社｜飯田の祇園祭と舞の歴史", "山名神社", "神社庁の登録事実と国指定の舞楽資料を分け、当年の開催案内へつなぐ", [23], ["祇園祭と舞の日時は当年の公式情報を確認します", "文化財の説明と地域の伝承を混同しません", "撮影や観覧は保存会と現地係員の案内を優先します"]),
    ("/temple/temples/t02/", "森町・蓮華寺｜萩の寺を訪ねる前の確認ガイド", "蓮華寺", "法人名簿で所在地と宗派を確かめ、花の見頃や拝観条件は直前に確認する", [25], ["花の開花と見頃は天候で変わります", "本尊・御朱印・常駐状況は未確認のまま断定しません", "境内では法要と寺院の日常を妨げないようにします"]),
    ("/life/work-life/tax/", "森町の税とふるさと納税｜住民・寄附者の確認ガイド", "森町の税と寄附", "住民として納める税と町外からの寄附を分け、対象年・期限・窓口を確認する", [44], ["控除上限や申告方法は個人条件によって異なります", "返礼品の在庫や発送時期は申込先で確認します", "税額判断は公式窓口や税理士などの専門家へ相談します"]),
]

OFFICIAL = {
    "guide": [("https://www.town.morimachi.shizuoka.jp/gyosei/kanko_bunka/kanko/index.html", "森町 観光情報"), ("https://www.tenhama.co.jp/", "天竜浜名湖鉄道")],
    "food": [("https://www.town.morimachi.shizuoka.jp/gyosei/sangyo_shigoto/noringyo/index.html", "森町 農林業"), ("https://www.town.morimachi.shizuoka.jp/gyosei/kanko_bunka/kanko/index.html", "森町 観光情報")],
    "history": [("https://www.town.morimachi.shizuoka.jp/gyosei/kanko_bunka/bunkazai/index.html", "森町 文化財情報"), ("https://www.town.morimachi.shizuoka.jp/gyosei/kanko_bunka/kanko/index.html", "森町 観光情報")],
    "shrine": [("http://www.shizuoka-jinjacho.or.jp/shokai/", "静岡県神社庁 神社紹介"), ("https://www.town.morimachi.shizuoka.jp/gyosei/kanko_bunka/bunkazai/index.html", "森町 文化財情報")],
    "temple": [("https://www.pref.shizuoka.jp/_res/projects/default_project/_page_/001/083/677/meibo4.pdf", "静岡県 宗教法人名簿"), ("https://www.town.morimachi.shizuoka.jp/gyosei/kanko_bunka/kanko/index.html", "森町 観光情報")],
    "life": [("https://www.town.morimachi.shizuoka.jp/gyosei/kurashi_tetsuzuki/zeikin/index.html", "森町 税金"), ("https://www.furusato-tax.jp/city/product/22461", "ふるさとチョイス 森町")],
}

FIELDWORK = {
    "guide": ("訪問日と同行者、使う交通手段を記録する", "目的地間の所要時間を地図と時刻表で照合する", "実際に使う駅・道路・休憩地点を安全な範囲で見る", "当日の公式運行・営業案内を優先する"),
    "food": ("商品名・原材料・産地・製造者を分ける", "保存条件と賞味期限を表示で確かめる", "販売者の許可なく売場や作業場所を撮影しない", "購入日の在庫と表示を基準にする"),
    "history": ("史料名・成立時期・記述範囲を記録する", "伝承地と現在地を地図で照合する", "墓所や寺社で静かに案内を読む", "物語と確認事実を別欄にする"),
    "shrine": ("神社庁の社名・所在地・御祭神を記録する", "文化財指定と祭礼運営を別資料で照合する", "参拝者と地域行事の動線を妨げず確認する", "当年日程は主催者案内を優先する"),
    "temple": ("法人名簿の名称・宗派・所在地を記録する", "観光案内と寺院の案内を分けて照合する", "境内と周辺道路を静かに確認する", "開花や拝観条件は直前情報を優先する"),
    "life": ("対象年・税目・納税者・期限を記録する", "町・県・国の担当範囲を分ける", "窓口へ行く前に必要書類を確認する", "個別税額は資格者または公式窓口で確かめる"),
}

SPECIFIC = {
    "/guide/one-day-course/": '<section class="fact-card"><h2 class="sec">森町の一日は中心部と一宮を分けて考える</h2><p>森町で一日を組むときは、遠州森駅周辺の町歩きと、一宮地区の小國神社方面を別の滞在単位として考えると無理がありません。さらに天方・三倉方面まで加えると移動の比重が増えます。行きたい場所を地図上で結び、観光時間ではなく「目的地を出て次の入口へ着くまで」を移動時間として計上します。</p><p>天浜線を使う日は帰りの列車から逆算し、車の日は祭礼・催事による交通変更を当年案内で確認します。食事、買物、参拝は営業時間や授与時間を固定情報として扱わず、当日の公式・運営者情報を見てください。</p></section>',
    "/guide/train-trip/": '<section class="fact-card"><h2 class="sec">森町内の5駅を目的別に使い分ける</h2><p>森町内には遠州森、戸綿、円田、森町病院前、遠江一宮の5駅があります。同じ町内駅でも、中心市街地へ歩く起点、生活施設に近い駅、一宮地区へ向かう起点という役割が異なります。駅名だけで目的地の最寄りを決めず、駅から入口までの道路、横断、坂、日没後の明るさを地図と現地で確認します。</p><p>天竜浜名湖鉄道は運行事業者の時刻表・運行情報が一次情報です。往路の到着時刻だけでなく、目的地を出る時刻、駅での待ち時間、乗継ぎ、運休時の連絡手段まで一枚にしてください。</p></section>',
    "/guide/family-trip/": '<section class="fact-card"><h2 class="sec">家族旅行は年齢別の負担を先に置く</h2><p>森町では寺社、町歩き、農産物の買物、山や川に近い場所など、訪問先によって足元と休憩条件が変わります。乳幼児連れはおむつ替えと昼寝、小学生は歩行距離と水分、高学年以上は集合場所を先に決めます。大人が行きたい場所の数からではなく、子どもが安全に移動できる一単位から組み立てます。</p><p>公園や文化施設の設備、飲食店の席、体験の対象年齢は年度や運営で変わります。本ページでは施設名の羅列で確定せず、利用日の公式案内を確認する順序を示します。</p></section>',
    "/guide/senior-friendly-trip/": '<section class="fact-card"><h2 class="sec">距離より段差と休憩間隔を見る</h2><p>寺社の境内や旧道沿いは、地図上の距離が短くても砂利、坂、階段、道路横断が負担になる場合があります。森町観光では「歩ける総距離」だけでなく、車や駅から入口まで、入口から見学地点まで、戻り道の三つに分けて確認してください。</p><p>車いす対応、手すり、休憩場所、介助の可否は施設ごとに異なります。体調、気温、服薬、日没を考え、一か所を外しても帰路が崩れない計画にします。</p></section>',
    "/food/souvenirs/": '<section class="fact-card"><h2 class="sec">森町らしさは表示と季節から確かめる</h2><p>森町のお土産候補には茶、とうもろこしなどの農産物、加工品、菓子があります。ただし「森町で販売」「森町産原料」「森町で製造」は同じ意味ではありません。贈る目的に合うかを、商品名の印象だけでなく原材料、産地、製造者、販売者の表示から確かめます。</p><p>生鮮品は旬と収穫状況、茶や菓子は保存条件と賞味期限が選択の軸です。価格、在庫、販売時刻、発送対応は変動するため、来訪前または購入時に販売者へ確認してください。</p></section>',
    "/history/mori-no-ishimatsu/": '<section class="fact-card"><h2 class="sec">森町との結びつきを三つの資料層で読む</h2><p>森の石松を調べるときは、浪曲・講談などで形づくられた人物像、寺院や墓所に伝わる案内、自治体・文化資料で確認できる記述を分けます。物語が広く親しまれていることと、個々の逸話が史実として確認できることは同じではありません。</p><p>異説に出会ったら、どちらかを即座に誤りとせず、資料名、語り手、刊行・成立時期、対象箇所を記録します。伝承地を訪れる際は観光地である前に寺社や地域の場であることを忘れず、案内と参拝マナーに従います。</p></section>',
    "/shrine/shrines/s4410002/": '<section class="fact-card"><h2 class="sec">天宮神社の確認済み基本情報</h2><p>静岡県神社庁の神社紹介では、天宮神社は森町天宮576に鎮座し、御祭神は田心姫命、湍津姫命、市許嶋姫命とされています。データ確認日は2026年8月4日です。社名の読みは「あめのみやじんじゃ」で、地名の天宮と合わせて場所を特定します。</p><p>例大祭や舞楽は文化の継承と地域運営を伴うため、過去の暦を翌年へ機械的に当てはめません。開催日、観覧場所、駐車・交通の扱いは当年の神社・保存関係者・町の案内を確認します。</p></section>',
    "/shrine/shrines/s4410004/": '<section class="fact-card"><h2 class="sec">三島神社の確認済み基本情報</h2><p>静岡県神社庁の神社紹介では、三島神社は森町森三島山36312に鎮座します。公開台帳では御祭神を確認できていないため、本ページでは推測して補いません。データ確認日は2026年8月4日です。</p><p>登録情報には11月の例大祭・神幸祭に関する記載がありますが、森のまつりの運行、交通規制、見学場所は年ごとに確認が必要です。神社の基本情報と祭り全体の運営情報を別の資料として見てください。</p></section>',
    "/shrine/shrines/s4410003/": '<section class="fact-card"><h2 class="sec">山名神社の確認済み基本情報</h2><p>静岡県神社庁の神社紹介では、山名神社は森町飯田2590に鎮座し、御祭神は素盞嗚命です。読みは「やまなじんじゃ」、データ確認日は2026年8月4日です。飯田地区の神社として、同名社との取り違えを住所で防ぎます。</p><p>山名神社の舞は、森町の他社に伝わる舞と一括りにせず、国・町の文化財資料で位置づけを確認します。当年の開催、演目、撮影、交通は保存関係者と主催側の案内を優先してください。</p></section>',
    "/temple/temples/t02/": '<section class="fact-card"><h2 class="sec">蓮華寺の確認済み基本情報</h2><p>静岡県知事所轄宗教法人名簿では、蓮華寺は森町森2144に所在する天台宗の宗教法人として確認できます。参照箇所は名簿p.71の該当行、データ確認日は2026年8月4日です。</p><p>本尊、御朱印、寺務の常駐状況は公開台帳で未確認のため断定しません。「萩の寺」として訪れる場合も、開花は天候で変わり、境内は寺院の日常と法要の場です。見頃、拝観条件、撮影可否は直前の寺院・観光案内を確認します。</p></section>',
    "/life/work-life/tax/": '<section class="fact-card"><h2 class="sec">納税と寄附を同じ手続きにしない</h2><p>森町に住む人が確認する住民税、固定資産税、軽自動車税、国民健康保険税などと、森町外の人を含むふるさと納税は、対象者も手続きも異なります。最初に「何年分か」「税目か寄附か」「納税者・寄附者は誰か」を書き分けます。</p><p>控除上限、確定申告、ワンストップ特例の適否は個人の収入や他の控除、寄附先数などで変わります。返礼品の内容や発送時期も変動します。本ページは個別税額を算定せず、森町の税担当ページ、国税当局、申込先、必要に応じ税理士へ確認する準備に使います。</p></section>',
}

def visible_chars(html: str) -> int:
    text = re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", "", html, flags=re.S)
    return len(re.sub(r"\s+", "", text))

def build_decisions() -> list[dict]:
    rows = json.loads(SOURCE.read_text(encoding="utf-8"))[:60]
    for row in rows:
        row = dict(row)
        if row["id"] == 54:
            row["decision"] = "MERGE"
            row["final_url"] = "/history/roads/"
            row["decision_reason"] = "公開済みの街道総合ページが秋葉街道を含むため正規URLを統合"
        row["phase"] = 3
        row["phase_status"] = "ON_HOLD_VERIFICATION" if row["decision"] == "HOLD" else "COMPLETE"
        yield row

def ensure_blog_article(path: Path, url: str) -> None:
    html = path.read_text(encoding="utf-8")
    if '"@type":"Article"' in html or '"@type": "Article"' in html or '"@type":"BlogPosting"' in html or '"@type": "BlogPosting"' in html:
        return
    title_m = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
    desc_m = re.search(r'<meta\s+name="description"\s+content="(.*?)">', html, re.S | re.I)
    title = unescape(re.sub(r"\s*\|.*$", "", title_m.group(1)).strip())
    desc = unescape(desc_m.group(1)).strip()
    schema = {"@context":"https://schema.org", "@type":"Article", "headline":title, "description":desc, "url":full.SITE + url, "dateModified":TODAY, "author":{"@type":"Person","name":"大石博之"}, "publisher":{"@type":"Organization","name":"森町ライフハック"}}
    html = html.replace("</head>", f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False, separators=(",", ":"))}</script></head>', 1)
    path.write_text(html, encoding="utf-8", newline="\n")

def main() -> None:
    decisions = list(build_decisions())
    keywords = [r["primary_keyword"] for r in decisions] + [""] * 140
    full.TOPIC_TITLES = keywords
    full.OFFICIAL.update(OFFICIAL)
    full.FIELDWORK.update(FIELDWORK)
    active_specs = [s for s in SPECS if not s[0].startswith(SACRED_DETAIL_PREFIXES)]
    rendered = {s[0] for s in active_specs}
    for spec in active_specs:
        path = ROOT / spec[0].strip("/") / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        html = full.render(spec)
        html = html.replace('<img src="figure-', '<img style="width:100%;height:auto" src="figure-')
        html = html.replace('<section><h2 class="sec">このページの使い方</h2>', SPECIFIC[spec[0]] + '<section><h2 class="sec">このページの使い方</h2>', 1)
        if spec[0] == "/life/work-life/tax/":
            feedback = '<section class="feedback-box"><h2 class="sec">この案内は役に立ちましたか</h2><p>税や寄附の条件は年度と個人状況で変わります。分かりにくい点は公式窓口で確認してください。</p></section>'
            html = html.replace('<p class="verified">', feedback + '<p class="verified">', 1)
        path.write_text(html, encoding="utf-8", newline="\n")

    for url in ("/blog/20260806-tea-garden-conditions/", "/blog/20260808-yatai-storage-ownership/"):
        ensure_blog_article(ROOT / url.strip("/") / "index.html", url)

    guide = ROOT / "guide" / "morimachi-complete-guide" / "index.html"
    guide_html = guide.read_text(encoding="utf-8")
    new_specs = SPECS[:6]
    links = "".join(f'<a class="official-link" href="{spec[0]}">{spec[1]}</a>' for spec in new_specs)
    block = LINK_START + '<section><h2 class="sec">目的別に旅を組み立てる</h2><p>滞在時間、交通手段、同行者に合わせて、次の詳しいガイドから確認できます。</p><div class="official">' + links + "</div></section>" + LINK_END
    if LINK_START in guide_html:
        guide_html = re.sub(re.escape(LINK_START) + r".*?" + re.escape(LINK_END), block, guide_html, flags=re.S)
    else:
        guide_html = guide_html.replace("</main>", block + "</main>", 1)
    guide.write_text(guide_html, encoding="utf-8", newline="\n")

    publish = []
    seen = set()
    for row in decisions:
        if row["decision"] not in {"CREATE", "EXPAND_EXISTING"}:
            continue
        url = row["final_url"]
        if url.startswith(SACRED_DETAIL_PREFIXES):
            continue
        if url in seen:
            continue
        seen.add(url)
        path = ROOT / url.strip("/") / "index.html"
        if not path.is_file():
            raise RuntimeError(f"第3期公開先がありません: {url}")
        chars = visible_chars(path.read_text(encoding="utf-8"))
        if chars < 6000:
            raise RuntimeError(f"第3期公開先が6000文字未満です: {url} {chars}")
        publish.append({"url": url, "title": row["proposed_title_h1"], "fact_checked_at": TODAY, "visible_chars": chars, "generated_in_phase3": url in rendered})

    DECISIONS.write_text(json.dumps(decisions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    PUBLICATION.write_text(json.dumps(publish, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    holds = sum(r["decision"] == "HOLD" for r in decisions)
    print(f"第3期確定: 60件 / 公開正規URL {len(publish)}件 / 現地・当事者確認待ち {holds}件")

if __name__ == "__main__":
    main()
