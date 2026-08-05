# -*- coding: utf-8 -*-
"""2026-07-03〜2026-08-05の不足分33本を生成する。

記事本文、表紙JPG、図版SVG 2点、data/blog-posts.json を同時に更新する。
既存の2026-08-04記事は対象外。繰り返しの図版マークアップはこのスクリプトで生成する。

実行: python scripts/generate_daily_blog_backfill.py
"""
from __future__ import annotations

import datetime as dt
import html
import json
import sys
import textwrap
import xml.dom.minidom
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"
LEDGER = ROOT / "data" / "blog-posts.json"
SITE = "https://morimachi.enshu-lifehack.com"
SITE_NAME = "森町ライフハック"
AUTHOR = "大石浩之（宅地建物取引士）"
TODAY = dt.date.today().isoformat()
JP_TODAY = f"{dt.date.today().year}年{dt.date.today().month}月{dt.date.today().day}日"

FONT_BOLD = Path(r"C:\Windows\Fonts\YuGothB.ttc")
FONT_MEDIUM = Path(r"C:\Windows\Fonts\YuGothM.ttc")

AXIS_LABEL = {
    "mon": "手続き・制度",
    "tue": "空き家・実家・相続",
    "wed": "寺社・歴史",
    "thu": "農地・山林・茶畑",
    "fri": "地区めぐり",
    "sat": "祭礼・イベント",
    "sun": "移住・暮らし・データ",
}


def post(date, slug, axis, title, description, question, answer, fact,
         good, caution, view, actions, internal, source):
    return {
        "date": date, "slug": slug, "axis": axis, "title": title,
        "description": description, "question": question, "answer": answer,
        "fact": fact, "good": good, "caution": caution, "view": view,
        "actions": actions, "internal": internal, "source": source,
    }


POSTS = [
    post(
        "2026-07-03", "20260703-six-districts", "fri",
        "森町を「六つの地区」から見ると、暮らしの輪郭が分かる",
        "森町は三倉、天方、森、一宮、園田、飯田の六つの地区に分かれます。町名だけでは見えにくい、移動・近所づきあい・暮らしの違いをどう確かめるか考えます。",
        "森町で住む場所を探すとき、地区名まで見る必要がありますか？",
        "あります。町公式も六地区に分けて案内しており、同じ森町でも日常の移動や地域との関わり方は一様ではありません。",
        "町公式の引越・新生活案内では、町内を三倉、天方、森、一宮、園田、飯田の六地区として示しています。地区は単なる住所の区分ではなく、自治会や生活動線を考える入口になります。",
        ("六地区という共通の見取り図が公式に示されている", "転入手続きと町内会の相談先を同じ案内で確認できる"),
        ("地区名だけで買い物や通勤の便利さを決めつけない", "昼の下見だけでなく朝夕の道路や移動時間も見る"),
        "不動産の相談では、建物の新しさより、毎日の移動と近所との距離感が住み続けやすさを左右します。六地区を序列にせず、自分の一日に合う場所を現地で確かめることが大切です。",
        ("公式の町全体図で六地区の位置を確認する", "通勤・通学時間帯に候補地から実際に移動する", "自治会やごみ出しなど入居後の確認事項を整理する"),
        ("/life/start-living/moved-in/", "森町へ転入したときの手続き"),
        ("引越・新生活／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/morimachiyakuba/hikkoshi_shinseikatsu/index.html"),
    ),
    post(
        "2026-07-04", "20260704-festival-and-life", "sat",
        "森の祭りは、観光情報だけでなく「地域の暮らし」として読みたい",
        "森町には屋台の曳き廻しや三社に伝わる舞楽があります。見る側の楽しさと、地域が受け継ぐ時間の両方から祭りを考えます。",
        "森町の祭りを知ると、暮らしの何が見えてきますか？",
        "行事の日程だけでなく、地域のつながりや一年の生活リズムが見えてきます。住まい選びでも無関係ではありません。",
        "町公式の移住案内は、森のまつりで十四台の屋台が曳き廻されること、小國神社・天宮神社の十二段舞楽、山名神社の天王祭舞楽などを森町の暮らしの魅力として紹介しています。",
        ("伝統が観光資源だけでなく地域の生活に根付いている", "子どもから大人まで地域を知る入口になる"),
        ("開催日だけを追い、準備や交通への影響を見落とさない", "参加の形は地域ごとに異なるため一律に決めつけない"),
        "祭りのある地域で家を探す方には、音や交通規制だけでなく、どんな関わり方が地域で大切にされているかも聞くよう勧めます。負担と決めつけず、つながりの機会として理解してから選ぶのがよいと思います。",
        ("町公式で行事と文化の背景を読む", "訪問前に開催情報と交通案内を確認する", "住む予定なら地域での関わり方を無理なく尋ねる"),
        ("/life/play-out/", "森町の催し・施設を調べる"),
        ("暮らしの森町自慢／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/teijusuishinka/ijukoryugakari/2/izyusankouzyohou/2119.html"),
    ),
    post(
        "2026-07-05", "20260705-test-daily-travel", "sun",
        "森町への移住前、家より先に「一日の移動」を試してみる",
        "森町への移住を考えるときは、景色や物件だけでなく通勤、買い物、通院、送迎の動線確認が欠かせません。下見で試したい順番を整理します。",
        "移住の下見では、物件以外に何を確かめるべきですか？",
        "平日の通勤、買い物、通院、子どもの送迎など、自分の一日の移動を実際の時間帯で試すのが先です。",
        "森町公式の移住案内は、自然や歴史だけでなく、移住の段階や住まいの情報をまとめています。町内には鉄道、路線バス、町営バスなどがありますが、行き先と時間帯で使い方が変わります。",
        ("移住情報と住まい情報を町がまとめて案内している", "完全移住だけでなく段階を踏んで検討できる"),
        ("観光で快適だった一日を日常生活と同じだと考えない", "車が使えない日や家族別の移動も想定する"),
        "物件の内覧は一時間でも、暮らしは毎日続きます。私は候補の家から職場、スーパー、病院まで動き、帰宅時間の道路も見ることが、間取りを見るのと同じくらい大事だと考えています。",
        ("家族全員の平日の移動を書き出す", "候補地から同じ曜日・時間帯に移動してみる", "車以外の手段と災害時の経路も確認する"),
        ("/life/start-living/public-transit/", "森町の公共交通を確認する"),
        ("移住定住／静岡県森町", "https://www.town.morimachi.shizuoka.jp/ijyu/index.html"),
    ),
    post(
        "2026-07-06", "20260706-moving-in-order", "mon",
        "森町への転入届は、オンライン予約だけで終わらない",
        "森町への転入届は住み始めてから14日以内です。マイナポータルを利用しても窓口手続きが必要になる点と、当日の順番を整理します。",
        "マイナポータルで転入予約をすれば、役場へ行かなくてもよいですか？",
        "いいえ。森町公式は、転入届は必ず来庁して手続きする必要があると案内しています。",
        "転入届の期間は、引っ越しが完了した日から14日以内です。本人確認書類や転出証明書、該当者のマイナンバーカードなどが必要で、カードの継続利用や電子証明書の住所変更も窓口で確認できます。",
        ("必要書類と届出期間が公式ページで具体的に示されている", "引っ越しワンストップで来庁予定を事前に伝えられる"),
        ("オンライン申請だけで転入が完了したと思わない", "代理人手続きでは当日に完了しない項目がある点を確認する"),
        "引っ越し直後は水道、ごみ、学校などが重なります。役場へ行く日を一日確保し、家族分のカードと暗証番号まで先に確認しておくと、二度手間を減らせます。",
        ("引っ越し完了日から14日以内の日程を確保する", "家族全員分の必要書類と暗証番号を確認する", "水道・学校・手当など同日に聞く項目をメモする"),
        ("/life/start-living/moved-in/", "転入後の手続きを順番に見る"),
        ("転入届／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/juminseikatsuka/juminkakari/2/3/2901.html"),
    ),
    post(
        "2026-07-07", "20260707-vacant-house-bank-owner", "tue",
        "森町の空き家バンクは、登録すれば町が売ってくれる制度ではない",
        "森町の空き家・空き地バンクは物件情報を届ける仕組みです。所有者が登録前に確かめたい登記、家財、管理状態、契約の役割分担を整理します。",
        "空き家バンクに登録すれば、町が売買契約までしてくれますか？",
        "いいえ。町は情報を登録・公開しますが、交渉や契約は所有者と利用希望者、必要に応じて専門事業者が進めます。",
        "森町公式は、町内の空き家・空き地を登録・公開し、移住・定住や地域活性化につなげる制度として案内しています。抵当権や農地など物件の状態によって登録できない場合もあります。",
        ("民間市場だけでは届きにくい移住希望者へ情報を出せる", "家財処分など登録に関連する支援を確認できる"),
        ("名義・抵当権・農地・境界を未確認のまま申し込まない", "町が価格交渉や契約責任を負う制度だと誤解しない"),
        "空き家の相談では、売り出し方より前に名義と残置物で止まることが少なくありません。写真を撮る前に、登記、家財、雨漏り、境界を一枚のメモにするのが現実的です。",
        ("登記事項と共有者の意思を確認する", "家財・設備・雨漏り・管理頻度を整理する", "登録条件と契約の進め方を窓口へ相談する"),
        ("/life/housing/vacant-house/", "森町の空き家対策を見る"),
        ("森町空き家・空き地バンク／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/teijusuishinka/ijukoryugakari/2/2/379.html"),
    ),
    post(
        "2026-07-08", "20260708-shrine-architecture", "wed",
        "森町の神社は、名前だけでなく建物の年代から見ても面白い",
        "森町には小國神社、天宮神社、山名神社だけでなく各地区に多くの神社があります。公式の町史資料から、社殿を傷めずに歴史を読む入口を紹介します。",
        "森町の神社を調べるとき、どこを見ると歴史が分かりますか？",
        "祭神や由緒だけでなく、本殿の建築形式、棟札、再建年代、覆い屋の有無を見ると地域の歴史が立体的になります。",
        "町公式の図説町史は、町内に宗教法人として登録された神社が40社ほどあるとし、天宮神社本殿・拝殿などの年代や建築形式を紹介しています。古い社殿は覆い屋の中にある場合もあります。",
        ("町史資料で建築年代や形式を具体的に確認できる", "著名な三社以外にも地区の歴史を伝える社殿がある"),
        ("立入禁止区域や祭祀の場へ無断で入らない", "古さを外観だけで断定せず公式資料と照合する"),
        "不動産を見るときも、地域の神社や道の形は土地の成り立ちを知る手掛かりになります。ただし見学対象である前に祈りの場です。静かに見て、資料で補う姿勢を大切にしたいです。",
        ("町史資料で所在地と建築年代を確認する", "現地では案内と立入範囲を守る", "近くの街道や集落との関係も地図で見る"),
        ("/shrine/", "森町の神社データベースを見る"),
        ("森町の神社建築／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/shakaikyoikuka/bunkashinkogakari/2/776.html"),
    ),
    post(
        "2026-07-09", "20260709-farmland-inheritance", "thu",
        "田んぼや畑を相続したら、登記だけで終わりではない",
        "森町で農地を相続した場合は、相続登記とは別に農業委員会への届出確認が必要です。耕作できない場合も含め、最初の相談順を整理します。",
        "農地を相続登記すれば、町への手続きは終わりですか？",
        "終わりとは限りません。農地を相続したときは農業委員会への届出が必要になるため、農地管理係へ確認します。",
        "森町公式の農林業案内には、農地の相続、売買・貸借、農地転用などが別の手続きとして掲載されています。所有者になったことと、耕作・貸借・転用できることは分けて考える必要があります。",
        ("農地に関する相談窓口と各手続きが町公式に整理されている", "耕作できない場合も貸借などの選択肢を相談できる"),
        ("宅地と同じ感覚で売却や駐車場利用を決めない", "場所や地番が分からないまま家族内の話だけで止めない"),
        "実家の相続相談では、家の後から田畑の存在が分かることがあります。納税通知書、公図、登記を並べ、どの土地が農地かを確定するところから始めるのが安全です。",
        ("納税通知書と登記で農地の地番を洗い出す", "相続の届出と利用意向を農地管理係へ相談する", "耕作・貸借・保全・転用を別々に検討する"),
        ("/life/troubles-consult/farmland/", "相続した農地の相談順を見る"),
        ("農林業／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/sangyo_shigoto/noringyo/index.html"),
    ),
    post(
        "2026-07-10", "20260710-center-and-outskirts", "fri",
        "森町の中心部だけ見て、町全体を知ったつもりにならない",
        "役場や文化会館のある中心部と、山あいを含む各地区では移動条件が違います。森町で暮らす場所を比べるときの見方を整理します。",
        "森町の下見は、中心部を回れば十分ですか？",
        "十分とは言えません。六地区の位置と公共交通、日常の行き先を重ねて、自分の生活範囲として確かめる必要があります。",
        "町公式は森町を六地区に分け、鉄道、民間路線バス、町営バスなどの公共交通を案内しています。町内の一地点を見ただけでは、別の地区の移動条件までは分かりません。",
        ("町全体図と公共交通案内を公式に確認できる", "中心部と各地区を同じ基準で比較できる"),
        ("駅や役場への近さだけで暮らしやすさを決めない", "地図上の距離と実際の所要時間を同じだと思わない"),
        "物件の所在地に『森町』と書かれていても、毎日の使い勝手は同じではありません。中心部か山間部かという二択にもせず、自分が週に何度どこへ行くかで比べるのが現実的です。",
        ("六地区と主要施設を一枚の地図に置く", "朝夕と休日に同じ経路を走る", "車が使えない場合の代替手段を確認する"),
        ("/life/play-out/parking-access/", "森町内の移動とアクセスを見る"),
        ("森町の公共交通について／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/seisakukikakuka/seisakukikakugakari/4/422.html"),
    ),
    post(
        "2026-07-11", "20260711-three-bugaku", "sat",
        "森町の三社に伝わる舞楽は、三つの舞をひと括りにしない方が面白い",
        "小國神社、天宮神社、山名神社に伝わる舞は国の重要無形民俗文化財です。それぞれの成り立ちと見方の違いを町史資料からたどります。",
        "森町の三社の舞は、すべて同じ十二段舞楽ですか？",
        "同じではありません。小國神社と天宮神社の十二段舞楽に対し、山名神社は祇園祭に伝わる風流舞の系統です。",
        "町公式の文化財一覧は、小國神社十二段舞楽、天宮神社十二段舞楽、山名神社天王祭舞楽を『遠江森町の舞楽』として国指定文化財に挙げています。三社で伝承の内容は異なります。",
        ("三つの舞が国指定として地域で受け継がれている", "町史資料で演目や背景まで学べる"),
        ("三社の舞を同じ内容として紹介しない", "開催情報を古い記憶だけで判断しない"),
        "文化財は名前を覚えるだけでは残りません。見る側も違いを知り、時間や場所の案内を守ることが、受け継ぐ人の負担を増やさない応援になると思います。",
        ("三社それぞれの公式解説を読む", "最新の奉納日時と観覧案内を確認する", "写真撮影や立入の決まりを現地で守る"),
        ("/shrine/", "森町の神社と祭礼を調べる"),
        ("文化財／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/shakaikyoikuka/bunkashinkogakari/1/1096.html"),
    ),
    post(
        "2026-07-12", "20260712-vacant-house-bank-buyer", "sun",
        "空き家バンクで森町へ移住するとき、価格より先に確認したいこと",
        "空き家バンクの物件は一軒ごとに水道、下水、家財、修繕、農地の条件が違います。内覧前後に確認したい項目を整理します。",
        "空き家バンクの物件なら、すぐ住める状態ですか？",
        "物件ごとに異なります。設備、雨漏り、家財、接道、災害リスク、農地の有無を現地と資料で確認する必要があります。",
        "森町公式の空き家・空き地バンクは、所有者から提供された情報を登録・公開する仕組みです。登録可否には物件状態などの条件があり、交渉や契約で町が当事者になる制度ではありません。",
        ("町内の空き家を移住希望者が探せる窓口になる", "物件に関係する支援制度も合わせて確認できる"),
        ("掲載写真と価格だけで修繕費を判断しない", "農地や山林が付く場合は住宅とは別に手続きを確認する"),
        "安く見える家ほど、修繕と片付けを合計すると予算が変わることがあります。私は購入費、修繕費、毎年の管理費を三列に分けてから判断するのがよいと考えています。",
        ("設備・雨漏り・家財・境界を内覧で確認する", "修繕と片付けの概算を購入費と分けて出す", "地域の移動と自治会を含めて家族で判断する"),
        ("/life/housing/buy-house/", "森町で家を買う前の確認事項"),
        ("森町空き家・空き地バンク／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/teijusuishinka/ijukoryugakari/2/2/379.html"),
    ),
    post(
        "2026-07-13", "20260713-resident-certificate", "mon",
        "森町の住民票は、窓口へ行く前に「何を載せるか」を決める",
        "住民票は提出先によって世帯主・続柄、本籍、マイナンバーなど必要な記載が違います。受取方法より先に確認したいことを整理します。",
        "住民票は、とりあえず世帯全員・全部記載で取ればよいですか？",
        "提出先が求める人と記載項目を先に確認する方が確実です。不要な個人情報を載せると受理されない場合もあります。",
        "森町公式は窓口請求、コンビニ交付などの方法を案内しています。請求書では世帯主・続柄、本籍、住民票コード、マイナンバーなどの記載要否を選ぶため、提出先への確認が先です。",
        ("窓口以外の取得方法が用意されている", "必要な記載項目を選べる書式が明確になっている"),
        ("用途を確認せず全部入りの住民票を請求しない", "代理請求やマイナンバー記載時の受取条件を見落とさない"),
        "証明書は早く取ることより、取り直さないことが大切です。提出先に『誰の、どの記載が必要か』を一度聞き、その答えをメモしてから請求すると無駄が減ります。",
        ("提出先へ必要な人と記載項目を聞く", "窓口・郵送・コンビニの条件を比べる", "本人確認書類と手数料を用意する"),
        ("/life/start-living/certificates/", "住民票・戸籍・印鑑証明を選ぶ"),
        ("証明書コンビニ交付サービス／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/juminseikatsuka/juminkakari/2/4826.html"),
    ),
    post(
        "2026-07-14", "20260714-clean-parents-house", "tue",
        "実家の片付けは、捨て始める前に「残す理由」を分ける",
        "森町で親の家を片付けるときは、ごみ分別だけでなく相続、空き家管理、売却資料の保全が関わります。失くして困る物から整理します。",
        "実家じまいは、まず家の中の物を減らせばよいですか？",
        "先に権利書、納税通知書、通帳、契約書、写真などを避難させ、相続人で残す基準を決めてから処分するのが安全です。",
        "森町公式は家庭ごみの分別と、空き家対策、空き家バンクの制度を別々に案内しています。片付けはごみ処理だけでなく、その後に使う、貸す、売る、解体する選択につながります。",
        ("分別方法と空き家の相談先を町公式で確認できる", "空き家バンク登録に関係する家財処分支援を確認できる"),
        ("重要書類や思い出の品を他の家財と一緒に処分しない", "一人の判断で片付けを進め家族関係をこじらせない"),
        "実家じまいでは、物の量より判断の回数が人を疲れさせます。『重要書類』『家族に確認』『処分』の三つに分け、売るかどうかは片付けの途中で決めなくてもよいと思います。",
        ("重要書類と貴重品を最初に別室へ移す", "家族で残す基準と期限を決める", "処分方法と家の次の使い方を並行して確認する"),
        ("/life/housing/clean-parents-house/", "親の家を片付ける順番"),
        ("空き家対策／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/teijusuishinka/sumaishiengakari/2/2222.html"),
    ),
    post(
        "2026-07-15", "20260715-oguni-amemiya-bugaku", "wed",
        "小國神社と天宮神社の十二段舞楽、演目の外側にも目を向ける",
        "森町の十二段舞楽は、舞だけでなく練習場所や浜垢離など周辺の営みも含めて受け継がれています。町史資料から見どころを整理します。",
        "十二段舞楽は、当日の舞だけを見れば分かりますか？",
        "町史資料には練習所、潮くみ、装束、稚児舞なども記録されており、舞台の外側にある準備を知ると理解が深まります。",
        "町公式の図説町史は、天宮神社の練習所、小國神社の浜垢離、花の舞、菩薩、庭胡蝶など、伝承を支える場所と所作を写真付きで紹介しています。",
        ("演目だけでなく準備や場所も公的資料に残されている", "子どもが担う舞を含め地域で伝承されている"),
        ("短い動画だけで舞全体を理解したつもりにならない", "担い手や稚児の負担を考えず撮影を優先しない"),
        "文化を残すのは、当日の拍手だけではありません。公式資料を読み、案内に従い、静かに見守る来訪者が増えることも、地域の負担を抑える支えになると思います。",
        ("演目と背景を町史資料で予習する", "最新の奉納案内と観覧場所を確認する", "現地の撮影・立入ルールを優先する"),
        ("/shrine/", "森町の神社と祭礼を見る"),
        ("小國・天宮両社の舞楽／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/shakaikyoikuka/bunkashinkogakari/2/782.html"),
    ),
    post(
        "2026-07-16", "20260716-mori-tea-history", "thu",
        "「森の茶」は商品名だけでなく、町の歴史そのものだった",
        "古くから茶産地として栄えた森町では、茶の歴史をまとめた『遠州森の茶業史』が刊行されています。土地と産業を一緒に見る意味を考えます。",
        "森町の茶を知るには、味や銘柄以外に何を見ればよいですか？",
        "茶園の立地、生産と流通の歴史、地域の暮らしとの関係を見ると、森町で茶が持つ意味が分かります。",
        "森町公式は『遠州森の茶業史』とダイジェスト版を刊行し、古くから茶産地として栄えた森町の歴史と文化をまとめた資料として案内しています。",
        ("茶業の歴史を町がまとまった資料として残している", "本編とダイジェスト版があり学ぶ深さを選べる"),
        ("現在の茶園や経営状況を歴史資料だけで判断しない", "景観の美しさと農地管理の負担を混同しない"),
        "茶畑のある土地は景色だけで評価できません。農地としての手続き、進入路、水、管理の担い手まで見て初めて、残す方法を話し合えます。歴史への敬意と現在の採算を分けて考えたいです。",
        ("茶業史で地域と茶の関係を知る", "現地の農地条件と管理者を確認する", "残す・貸す・別の利用を窓口へ相談する"),
        ("/life/troubles-consult/farmland/", "田畑の相談先を確認する"),
        ("『遠州森の茶業史』販売について／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/shakaikyoikuka/bunkashinkogakari/rekishi/5783.html"),
    ),
    post(
        "2026-07-17", "20260717-mikura-amagata-travel", "fri",
        "三倉・天方で暮らすなら、距離より「移動の代替」を見る",
        "森町の山あいを含む地域で暮らすときは、自家用車だけでなく、通院や買い物の代替手段を確認する必要があります。考え方を整理します。",
        "車を運転できる間は、公共交通を確認しなくてもよいですか？",
        "今使わなくても、家族の送迎、故障、加齢、災害時を考え、鉄道・バス・支援の有無を知っておく方が安心です。",
        "森町公式は鉄道、民間路線バス、タクシー、町営バスなどを公共交通として案内しています。利用できる路線と時刻は地区や目的地によって異なります。",
        ("複数の移動手段を町公式の一覧からたどれる", "通院や生活目的に応じた交通を比較できる"),
        ("今の運転能力だけで長期の住みやすさを判断しない", "距離が短いから送迎負担も小さいと決めつけない"),
        "山あいの家は静けさが魅力ですが、家族の送迎が毎日必要になると負担が変わります。『車がない日にも暮らせるか』を一度試すことが、長く住むための現実的な確認です。",
        ("候補地から最寄りの停留所と時刻を調べる", "通院・買い物を車なしで一度組み立てる", "家族が送迎できない日の代替を決める"),
        ("/life/start-living/public-transit/", "森町の公共交通を見る"),
        ("森町の公共交通について／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/seisakukikakuka/seisakukikakugakari/4/422.html"),
    ),
    post(
        "2026-07-18", "20260718-yamana-dance", "sat",
        "山名神社祇園祭のお舞に、応仁の乱以前の面影が残る",
        "森町飯田の山名神社に伝わるお舞は、十二段舞楽とは異なる風流舞の系統です。八段の演目と地域で伝わった背景を町史から読みます。",
        "山名神社のお舞は、小國神社の十二段舞楽と同じですか？",
        "異なります。町史は、京都祇園祭の古い姿を伝える風流舞の系統とし、八つの演目を挙げています。",
        "町公式の図説町史は、山名神社の舞が応仁の乱以前の京都祇園祭の諸相を伝える風流舞の系統で、八初児、神子、鶴、獅子、迦陵頻、龍、蟷螂、優填獅子の八段から成ると説明しています。",
        ("演目と歴史的背景が町史資料に具体的に残る", "地域の祭礼と国指定文化財が一体になっている"),
        ("難しい名称だけを切り取って珍しさを競わない", "開催時期や観覧方法を過去情報のまま案内しない"),
        "文化財を伝える記事は、派手な場面だけでなく、地域が長く守ってきた事実を丁寧に書く必要があります。来訪者が背景を知って静かに見ることも、保存への協力だと思います。",
        ("八段の名称と由来を公式資料で読む", "最新の開催情報を主催者側で確認する", "地域の通行と祭礼の進行を妨げない"),
        ("/shrine/", "森町の神社・祭礼情報を見る"),
        ("山名神社祇園祭のお舞／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/shakaikyoikuka/bunkashinkogakari/2/783.html"),
    ),
    post(
        "2026-07-19", "20260719-population-by-district", "sun",
        "人口データは、森町の地区を比べるための入口であって結論ではない",
        "森町の六地区は人口規模が異なります。公表資料の時点を確かめ、数字だけで地域の将来や暮らしやすさを決めない読み方を考えます。",
        "地区別人口を見れば、住みやすい地区が分かりますか？",
        "分かるのは人口規模と構成の一部です。交通、医療、買い物、地域活動、災害リスクを重ねて判断する必要があります。",
        "森町の地域福祉に関する公表資料には、2023年10月1日時点の住民基本台帳をもとに六地区の人口が掲載されています。数字は有用ですが、特定時点の記録であり現在値とは限りません。",
        ("地区別の規模を同じ時点の数字で比較できる", "福祉や地域づくりを考える基礎資料になる"),
        ("古い時点の人口を現在の人数として扱わない", "人口が少ないことを暮らしにくさと直結させない"),
        "不動産では人口の多い少ないより、本人の生活動線と地域の支えが合うかが重要です。数字は現地で何を聞くべきかを決める質問表として使うのがよいと思います。",
        ("資料の基準日と出典を確認する", "交通・医療・買い物の情報を重ねる", "現地で自治会や日常の助け合いを尋ねる"),
        ("/tools/", "森町の便利ツールを見る"),
        ("森町地域福祉に関する公表資料／静岡県森町", "https://www.town.morimachi.shizuoka.jp/material/files/group/7/r5chiikifukushikeikaku.pdf"),
    ),
    post(
        "2026-07-20", "20260720-care-first-consultation", "mon",
        "親の介護が始まったら、施設探しより先に相談先を一つ決める",
        "介護は家族だけで制度を調べ切ろうとすると疲れます。森町の地域包括支援センターを入口に、困りごとを整理する順番を考えます。",
        "親の介護が必要になったら、すぐ施設を探すべきですか？",
        "まず本人の状態と家族の困りごとを整理し、地域包括支援センターへ相談するのが先です。必要な制度や支援へつないでもらえます。",
        "森町公式は、地域包括支援センターを高齢者の総合相談窓口として案内しています。介護だけでなく、健康、権利擁護、生活上の困りごとを含めて相談できます。",
        ("相談先が町の窓口として明確に示されている", "介護認定前でも困りごとの整理から相談できる"),
        ("家族だけで施設・費用・申請を同時に決めようとしない", "本人の希望を聞かず家の処分まで急いで進めない"),
        "介護と実家の問題は同時に動きがちですが、住まいの結論を急ぐと本人も家族も疲れます。まず安全と介護体制を整え、家の判断は別の紙に置くのがよいと考えます。",
        ("困っていることを一文ずつ書き出す", "地域包括支援センターへ相談する", "介護と家・お金の判断を分けて家族で話す"),
        ("/life/parents-care/community-support-center/", "地域包括支援センターの使い方"),
        ("地域包括支援センター／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/hokenfukushika/chiikihokatsushiencenterkakari/index.html"),
    ),
    post(
        "2026-07-21", "20260721-inherited-home-deduction", "tue",
        "相続した実家を売る前に、3,000万円控除の確認書を調べる",
        "被相続人が住んでいた家を売る場合、要件を満たせば譲渡所得の特例対象になる可能性があります。契約前に確認したい役場書類を整理します。",
        "実家を売った後で、空き家の税の特例を申請すればよいですか？",
        "契約や解体の前に要件と必要書類を確認すべきです。森町内の家屋に関する確認書は町の資産税係が発行します。",
        "森町公式は、被相続人居住用家屋等確認書の発行手続きを案内しています。この確認書だけで特例適用が決まるものではなく、家屋、相続、売却時期、耐震や解体など複数の要件があります。",
        ("町内家屋の確認書窓口と提出書類が公式に示されている", "売却前に特例の可能性を検討する入口がある"),
        ("確認書を取れば必ず控除されると考えない", "解体・改修・売買契約の順番を要件確認前に決めない"),
        "実家売却は価格だけでなく、いつ何をするかで税の扱いが変わる場合があります。売却査定と税の確認を同時に始め、税理士や税務署への確認を後回しにしないことが大切です。",
        ("相続日・居住状況・家屋の状態を整理する", "町の確認書と国税の適用要件を照合する", "契約・解体前に税務の専門家へ確認する"),
        ("/life/end-of-life/inherited-house/", "相続した親の家の選択肢を見る"),
        ("被相続人居住用家屋等確認書の発行について／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/zeimuka/shisanzeigakari/1/kaoku/543.html"),
    ),
    post(
        "2026-07-22", "20260722-temple-architecture", "wed",
        "森町の寺院は、宗派の数から地域史が見えてくる",
        "森町の町史資料では曹洞宗寺院が多く、最古級の本堂や文化財の山門も紹介されています。寺院を一覧と建築の両方から見る方法を考えます。",
        "森町の寺院には、どのような特徴がありますか？",
        "町史資料では曹洞宗が27か寺と多く、他に日蓮宗、真言宗、天台宗、浄土宗の寺院があると整理されています。",
        "町公式の図説町史は、寺院を宗派別に整理し、金剛院山門と天宮神社神宮寺が町の文化財であること、建立年代が分かる最古の本堂として三倉の栄泉寺を紹介しています。",
        ("宗派と建築を公的な町史資料から確認できる", "有名寺院だけでなく地区の寺院を一覧で見られる"),
        ("寺院数を現在の活動状況と同じだと考えない", "墓地や境内へ観光施設の感覚で立ち入らない"),
        "実家じまいでは菩提寺や墓の確認が後から出てくることがあります。建物の処分だけを先に考えず、家と寺院の関係を家族に聞いておくことも大切な引き継ぎです。",
        ("宗派と所在地を町史・寺院一覧で確認する", "家の菩提寺や墓の情報を家族に聞く", "訪問時は寺院の案内と礼節を守る"),
        ("/temple/", "森町の寺院データベースを見る"),
        ("森町の寺院建築／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/shakaikyoikuka/bunkashinkogakari/2/774.html"),
    ),
    post(
        "2026-07-23", "20260723-farmland-conversion", "thu",
        "農地を駐車場や宅地にしたい——先に工事を始めてはいけない",
        "森町で農地を宅地や駐車場などへ変える場合は、農地転用の許可確認が必要です。4条・5条の違いと相談の順番を整理します。",
        "自分の農地なら、整地して駐車場にしてもよいですか？",
        "許可前に進めてはいけません。所有者自身の転用は4条、売買や賃借を伴う転用は5条として事前相談と申請が必要です。",
        "森町公式は、農地以外の目的へ転用する場合は申請と許可が必要と案内しています。申請締切は原則毎月25日、許可は翌月末の予定とされ、完了後にも届出と地目変更登記があります。",
        ("4条・5条の違いと提出先が公式に整理されている", "締切と許可時期の目安が公表されている"),
        ("工事・売買契約を先に進めてから相談しない", "登記地目だけで現況や許可可能性を判断しない"),
        "土地活用の相談では『使っていないから宅地にできる』という思い込みが一番危険です。計画図と地番を持って事前相談し、許可の見通しが立ってから費用をかけるべきです。",
        ("登記・公図・現況写真をそろえる", "用途と工事内容を農地管理係へ事前相談する", "許可後に工事し完了届と地目変更を進める"),
        ("/life/troubles-consult/farmland/conversion/", "農地転用の相談順を見る"),
        ("農地を農地以外のものにする場合／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/sangyo_shigoto/noringyo/6758.html"),
    ),
    post(
        "2026-07-24", "20260724-three-eastern-districts", "fri",
        "一宮・園田・飯田を、地図の近さだけで同じ暮らしと考えない",
        "森町の六地区のうち一宮、園田、飯田にもそれぞれの生活動線があります。物件比較で地区名と実際の行き先を重ねる方法を考えます。",
        "隣り合う地区なら、生活条件もほぼ同じですか？",
        "同じとは限りません。駅、幹線道路、学校、買い物先への経路を候補地ごとに確認する必要があります。",
        "町公式は森町を六地区として案内し、公共交通を鉄道、路線バス、町営バスなどに分けて掲載しています。利用条件は住所だけでなく目的地と時間帯で変わります。",
        ("地区と交通を公式情報から同じ地図上で確認できる", "複数候補を生活動線で比較しやすい"),
        ("地区の評判だけで候補から外さない", "直線距離だけで通勤・通学時間を判断しない"),
        "家の価格差には理由がありますが、その理由が自分にとって欠点とは限りません。毎日使う道と週一回使う道を分けて比べると、必要な立地が見えやすくなります。",
        ("家族の主な行き先を地図に置く", "候補地ごとに実走時間を測る", "公共交通と災害時の別経路も確認する"),
        ("/life/play-out/parking-access/", "森町内の移動を確認する"),
        ("引越・新生活／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/morimachiyakuba/hikkoshi_shinseikatsu/index.html"),
    ),
    post(
        "2026-07-25", "20260725-supporting-festivals", "sat",
        "祭礼を残すのは、当日の人出だけではない",
        "森町の祭りや舞楽は、準備、練習、片付けを担う人によって続いています。訪れる側と住む側が無理なく支える方法を考えます。",
        "祭礼を応援するには、見に行けば十分ですか？",
        "観覧も支えになりますが、交通や撮影の決まりを守り、地域の準備を妨げないことも重要です。住民はできる範囲の関わり方を相談できます。",
        "森町公式は、森のまつり、三社の舞楽、石松まつりなどを暮らしの魅力として紹介しています。行事は観光の一日だけでなく、地域が長く受け継いできた活動です。",
        ("伝統行事が町の魅力として公的に位置づけられている", "世代を超えた地域のつながりをつくる機会になる"),
        ("担い手の善意を無限の労力として期待しない", "外からの撮影や駐車を地域の暮らしより優先しない"),
        "移住相談では祭りへの参加を心配する声もあります。参加か不参加の二択ではなく、準備、清掃、見守りなど無理のない関わり方を地域に聞くことが、長続きする関係につながると思います。",
        ("行事の背景と地域の案内を読む", "観覧時は交通・撮影・ごみの決まりを守る", "住民になる場合は可能な関わり方を相談する"),
        ("/life/play-out/", "森町の催し・施設を見る"),
        ("暮らしの森町自慢／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/teijusuishinka/ijukoryugakari/2/izyusankouzyohou/2119.html"),
    ),
    post(
        "2026-07-26", "20260726-dual-location", "sun",
        "森町の二地域居住——移住か現状維持かの二択をやめる",
        "森町は二地域居住を、観光と完全移住の中間にある暮らし方として案内しています。家を買う前に試せる関わり方を考えます。",
        "森町に関わるには、住民票を移して移住するしかありませんか？",
        "いいえ。町は都市部などと森町の二つに生活拠点を持つ二地域居住を進め、段階的に地域と関わる考え方を示しています。",
        "森町公式は二地域居住を、観光と完全移住の中間に位置する暮らし方と説明しています。令和7年度には促進計画を策定し、森町を第二の実家のような場所にする考えを掲げています。",
        ("移住を0か100かで決めない選択肢が示されている", "仕事や今の生活を保ちながら地域を知れる"),
        ("空き家を買うことだけを二地域居住の出発点にしない", "使わない期間の管理・費用・近隣対応を軽く考えない"),
        "二拠点目の家は、使う日より使わない日の方が多いことがあります。購入前に賃貸や短期滞在で季節を変えて通い、管理を続けられるか試すのがよいと思います。",
        ("年間に森町で過ごす日数と目的を決める", "季節を変えて複数回滞在する", "住まいの管理費と不在時の対応を見積もる"),
        ("/life/housing/rent-house/", "森町で住まいを探す"),
        ("二地域居住の促進／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/teijusuishinka/ijukoryugakari/6727.html"),
    ),
    post(
        "2026-07-27", "20260727-bereavement-order", "mon",
        "家族が亡くなった後の手続きは、期限と窓口を一枚にまとめる",
        "死亡後は役場、年金、保険、相続、家の管理などが重なります。森町の案内を入口に、家族が抱え込まない整理方法を考えます。",
        "家族が亡くなった後、何から始めればよいですか？",
        "町の死亡・おくやみ案内で役場手続きを確認し、期限、担当者、必要書類を一枚にまとめます。相続や家の判断は別の欄に分けます。",
        "森町公式には死亡にともなう手続きの案内があります。役場で完結する届出と、年金、金融機関、法務局、税務など別の機関へ確認する事項は分けて進める必要があります。",
        ("おくやみに関する町の入口が用意されている", "役場内の手続きをまとめて確認しやすい"),
        ("悲しみの中で一人が全手続きを抱えない", "相続人が決まる前に家財処分や家の売却を急がない"),
        "実家の相談では、期限のある届出と家族で考える問題が混ざって疲れてしまいます。『今週』『一か月以内』『急がない』に分け、担当を決めるだけでも負担は軽くなります。",
        ("町の案内から必要手続きを書き出す", "期限と窓口で三つの優先度に分ける", "相続・家・墓の判断は家族会議の項目に分ける"),
        ("/life/end-of-life/bereavement/", "おくやみ手続きを順番に見る"),
        ("死亡にともなう手続き／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/lifeevent/okuyami/1830.html"),
    ),
    post(
        "2026-07-28", "20260728-before-selling-house", "tue",
        "森町で家を売る前に、価格より境界・接道・名義を確認する",
        "売却査定の金額は、物件情報が正しくそろって初めて比較できます。森町の空き家バンク確認票から、先に整理したい項目を読み解きます。",
        "家を売ると決めたら、最初に査定を頼めばよいですか？",
        "査定と並行して、所有者、登記、境界、接道、設備、災害リスク、家財の有無を整理すると話が早くなります。",
        "森町の空き家・空き地バンク確認票には、所有者、土地建物の名義、登記、境界、接道、災害区域、設備、雨漏り、家財などの確認項目があります。これらは一般の売却でも重要です。",
        ("売る前の確認事項が具体的なチェック項目になっている", "物件の弱点も含めて早い段階で整理できる"),
        ("査定額だけを比べ資料の前提差を見落とさない", "境界や接道を現地の見た目だけで断定しない"),
        "高い査定額より、後で金額が変わらない査定の方が安心です。分からない項目を隠さず『未確認』と書き、調べる順番をつくることが売却の近道です。",
        ("登記・公図・納税通知書を集める", "境界・接道・設備・家財を現地で確認する", "同じ資料を渡して査定条件を比較する"),
        ("/life/housing/sell-house/", "森町で家を売る前の確認事項"),
        ("空き家・空き地バンク確認票／静岡県森町", "https://www.town.morimachi.shizuoka.jp/material/files/group/10/cyekkurisuto.pdf"),
    ),
    post(
        "2026-07-29", "20260729-suzuki-tozaburo", "wed",
        "鈴木藤三郎——森町から製糖業を変えた発明家",
        "森町本町出身の鈴木藤三郎は、氷砂糖の製法を発明し、精製糖事業や台湾製糖に関わりました。その歩みから地域の産業を見る視点を考えます。",
        "鈴木藤三郎は、森町とどのような関係がありますか？",
        "森町本町出身で、森町で氷砂糖の製法を発明し、日本の精製糖事業を興した近代産業の先駆者です。",
        "森町公式は、鈴木藤三郎を1855年生まれの実業家、発明家として紹介しています。報徳の教えの影響を受け、氷砂糖の製法を発明し、台湾製糖の初代社長も務めました。",
        ("町公式が人物紹介と動画で功績を伝えている", "発明だけでなく事業化と地域の学びを考えられる"),
        ("偉人の成功だけを切り取り試行錯誤を消さない", "現在の地域産業へ単純に同じ方法を当てはめない"),
        "藤三郎の話から私が感じるのは、地域にいることと外へ挑戦することは矛盾しないという点です。森町の資源を守るだけでなく、今の暮らしに合う使い方へつなぐ発想が必要だと思います。",
        ("町公式の人物紹介と動画を見る", "森町の産業史と合わせて読む", "今の地域資源で試せる小さな改善を考える"),
        ("/life/play-out/cultural-facilities/", "森町の文化施設を見る"),
        ("鈴木藤三郎／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/shakaikyoikuka/bunkashinkogakari/rekishi/morimatinoijin/5583.html"),
    ),
    post(
        "2026-07-30", "20260730-forest-inheritance", "thu",
        "山林を相続したら、場所が分からなくても90日届出を確認する",
        "森町で森林の土地を相続・売買で取得した場合、対象となる民有林では所有者届出が必要です。地番と現地が一致しないときの確認順を整理します。",
        "相続した山林の場所が分からなくても、届出は必要ですか？",
        "対象森林なら必要です。森町公式は、相続の場合は前所有者の死亡日から90日以内の提出と案内しています。まず対象か窓口へ確認します。",
        "森町公式は、地域森林計画の対象となる民有林を相続・売買などで取得した場合、町への所有者届出が必要と案内しています。位置図と登記事項証明書なども提出書類です。",
        ("対象、期限、提出書類、相談先が公式に明示されている", "場所が不明でも対象確認から相談できる"),
        ("固定資産税が少額だから手続き不要と思わない", "現地を確認せず伐採や売却の話を先に進めない"),
        "山林相続では、地番は分かっても入口が分からないことがあります。登記、公図、森林計画図、親族の記憶を別々に集め、まず届出期限を守ることを優先すべきです。",
        ("登記と納税通知書から地番を確認する", "対象森林か林政係へ確認し90日以内に届ける", "境界・進入路・管理状況を後から現地確認する"),
        ("/life/end-of-life/inheritance/", "土地を相続したときの整理"),
        ("森林の土地の所有者届出制度／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/sangyo_shigoto/noringyo/1307.html"),
    ),
    post(
        "2026-07-31", "20260731-home-location-check", "fri",
        "森町の住所選びは、地区名より通勤・買い物・災害地図を重ねる",
        "住む場所を比べるときは、便利さと安全を別々に見ず、一日の移動とハザードマップを同じ地図に重ねることが大切です。",
        "便利な場所なら、災害リスクの確認は後でもよいですか？",
        "先に確認します。通勤や買い物の経路と、洪水・土砂災害などの想定区域、避難先を一緒に見て候補を比べます。",
        "森町公式は、洪水や土砂災害などを確認するハザードマップと公共交通情報を公開しています。住所だけでは、日常の移動と災害時の経路の両方は分かりません。",
        ("災害リスクと避難先を地図で確認できる", "公共交通と日常施設への経路を別資料で補える"),
        ("区域内だから住めない、区域外だから安全と単純化しない", "昼間の経路だけ見て夜間や大雨時の動きを考えない"),
        "住まい探しで大切なのは、リスクをゼロに見せることではなく、知った上で備えられることです。候補ごとに避難先と連絡方法まで書ける家を選ぶ方が安心です。",
        ("候補地をハザードマップで確認する", "日常と避難の二つの経路を実際に歩く", "家族の連絡先と避難先を候補ごとに決める"),
        ("/life/living-soon/disaster-risk/", "引っ越す前の災害リスク確認"),
        ("森町防災ハザードマップ／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/bosai_anzen/bosai/hazardmap/1255.html"),
    ),
    post(
        "2026-08-01", "20260801-event-traffic-manners", "sat",
        "森町の祭りへ行く前に、駐車場と交通案内を確認する",
        "祭りや催しの日は普段と道路の使われ方が変わります。地域の暮らしを妨げず楽しむために、出発前に見る情報を整理します。",
        "森町の催しへ車で行くとき、現地で駐車場を探せばよいですか？",
        "事前に主催者と町の最新案内を確認します。臨時駐車場、交通規制、公共交通、歩行経路が通常と異なる場合があります。",
        "森町公式には産業・観光に関するイベント情報のページがあります。開催内容は年度ごとに変わるため、古い記事や地図ではなく、当日の公式案内を見る必要があります。",
        ("町公式から開催中の催し情報を確認できる", "公共交通や町内アクセス情報と組み合わせられる"),
        ("店舗や住宅の敷地へ無断駐車しない", "過去開催時の交通案内をそのまま使わない"),
        "イベントの印象は、行き帰りの混乱でも変わります。少し歩いても指定駐車場を使い、地域の生活道路をふさがないことが、また来たいと思える催しを支えます。",
        ("開催日の公式情報を確認する", "指定駐車場・規制・公共交通を地図に保存する", "ごみと通行の決まりを守り時間に余裕を持つ"),
        ("/life/play-out/", "森町の催し・施設を見る"),
        ("イベント情報／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/sangyoseisakuka/sangyoshinkokakari/2/index.html"),
    ),
    post(
        "2026-08-02", "20260802-parenting-migration", "sun",
        "子育て移住は、支援制度の数より「困った日の相談先」で比べる",
        "森町への子育て移住を考えるなら、手当だけでなく、相談、遊び場、保育、学校、送迎を一日の流れで確認することが大切です。",
        "子育て支援が多い町なら、移住後も安心ですか？",
        "制度の数だけでは判断できません。困ったときの相談先、利用条件、距離、開所時間、家族の送迎を具体的に確認します。",
        "森町公式は、こども家庭センター、児童館、子育て応援アプリなど複数の支援窓口を案内しています。支援ごとに対象や使い方が異なるため、年齢と困りごとで使い分けます。",
        ("相談・交流・情報確認の複数の入口が用意されている", "妊娠期から子育てまで継続して相談先を探せる"),
        ("給付額や制度名だけで暮らしやすさを決めない", "保育・学校・通勤の送迎時間を別々に見ない"),
        "子育て世帯の住まい相談では、家の広さより朝の一時間が重要です。保育先、職場、買い物を実際の時刻で回り、困った日の相談先をスマホに登録してから決めると安心です。",
        ("子どもの年齢ごとに使える窓口を確認する", "平日の送迎と通勤を同じ時刻で試す", "病気・仕事・孤立時の相談先を家族で共有する"),
        ("/life/family-grow/parenting-support/", "森町の子育て相談先を見る"),
        ("こども家庭センター／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/kenkokodomoka/kodomokateikakari/1/837.html"),
    ),
    post(
        "2026-08-03", "20260803-mynumber-support", "mon",
        "マイナンバーカード申請は、出張申請を使える場合がある",
        "森町では事業所や地域団体などを対象に出張申請の案内があります。窓口へ行きにくい人が確認したい条件と受取方法を整理します。",
        "役場へ行けないと、マイナンバーカードは申請できませんか？",
        "出張申請を利用できる場合があります。対象、人数、会場、本人確認書類などの条件を住民係へ事前に確認します。",
        "森町公式はマイナンバーカードの出張申請を案内し、申請後は一定期間を経て住所地への郵送または役場での受取になると説明しています。利用条件は申込み前の確認が必要です。",
        ("窓口へ行きにくい人の申請機会を地域や職場でつくれる", "申請から受取までの流れが公式に示されている"),
        ("個人一人でも必ず来てもらえる制度だと考えない", "本人確認書類や受取条件を当日に初めて確認しない"),
        "デジタル手続きは、使える人だけに便利では意味がありません。出張申請のような支援は、家族や地域が情報を届け、条件を先に確認することで生きる仕組みだと思います。",
        ("対象人数と会場条件を住民係へ確認する", "申請者ごとの本人確認書類をそろえる", "郵送・窓口の受取方法を事前に共有する"),
        ("/life/start-living/mynumber/", "マイナンバーカード申請の流れ"),
        ("マイナンバーカードの出張申請／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/juminseikatsuka/juminkakari/1/5169.html"),
    ),
    post(
        "2026-08-05", "20260805-cultural-assets", "wed",
        "友田家住宅、次郎柿原木、三つの舞楽——森町の文化財を暮らしにつなぐ",
        "森町の文化財は有名寺社だけではありません。住宅、果樹、祭礼、街並みを一つの一覧で見ると、地域の暮らしが文化として残る意味が見えてきます。",
        "森町の文化財には、どのようなものがありますか？",
        "国指定の友田家住宅や遠江森町の舞楽、県指定の次郎柿原木など、建物・民俗・天然記念物にまたがります。",
        "森町公式の文化財一覧は、友田家住宅、小國神社・天宮神社・山名神社の舞楽、次郎柿原木、寺社の建造物や史跡などを紹介しています。文化財は暮らしから離れた展示物だけではありません。",
        ("建物・祭礼・植物を横断して地域の歴史を学べる", "町公式が所在地や指定区分を一覧で示している"),
        ("個人所有や信仰の場を自由に見学できると思わない", "指定名称だけを転載し現在の公開状況を確認しない"),
        "古い家や木は、所有者にとって維持の責任も伴います。価値を褒めるだけでなく、見学ルールを守り、修理や継承を支える情報まで伝える記事にしたいと思います。",
        ("文化財一覧で名称と所在地を確認する", "公開・見学条件を管理者側へ確認する", "地域の歴史と現在の維持課題を一緒に考える"),
        ("/life/play-out/cultural-facilities/", "森町の歴史・文化施設を調べる"),
        ("文化財／静岡県森町", "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/shakaikyoikuka/bunkashinkogakari/1/1096.html"),
    ),
]


def esc(value):
    return html.escape(str(value), quote=True)


def load_parts():
    return {
        name: (ROOT / "parts" / f"{name}.html").read_text(encoding="utf-8").strip()
        for name in ("head-css", "header", "disclaimer", "footer")
    }


def part(name, value):
    return f"<!-- PART:{name}:START -->{value}<!-- PART:{name}:END -->"


def short(value, limit=52):
    value = str(value).replace("\n", " ")
    return value if len(value) <= limit else value[:limit - 1] + "…"


def svg_text_lines(text, width=31, max_lines=2):
    lines = textwrap.wrap(str(text), width=width, break_long_words=True, break_on_hyphens=False)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = short(lines[-1], width)
    return lines or [""]


def build_figure(title, rows, aria):
    p = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="430" viewBox="0 0 1000 430" role="img" aria-label="%s">' % xml_escape(aria),
        '<defs><style>.ttl{font-family:"Yu Gothic","Hiragino Kaku Gothic ProN",sans-serif;font-weight:700;fill:#203b32}.lbl{font-family:"Yu Gothic","Hiragino Kaku Gothic ProN",sans-serif;fill:#50645b}.num{font-family:"Yu Gothic","Hiragino Kaku Gothic ProN",sans-serif;font-weight:700;fill:#fff}</style></defs>',
        '<rect width="1000" height="430" rx="18" fill="#f8fbf8" stroke="#c9d9d0"/>',
        '<rect x="0" y="0" width="1000" height="78" rx="18" fill="#174f3b"/>',
        '<rect x="0" y="58" width="1000" height="20" fill="#174f3b"/>',
        f'<text x="40" y="51" class="num" font-size="27">{xml_escape(title)}</text>',
    ]
    y = 96
    for index, (head, desc) in enumerate(rows, 1):
        p.append(f'<rect x="36" y="{y}" width="928" height="92" rx="13" fill="#fff" stroke="#d9e3dd"/>')
        p.append(f'<circle cx="77" cy="{y + 46}" r="23" fill="#b78b35"/>')
        p.append(f'<text x="77" y="{y + 54}" text-anchor="middle" class="num" font-size="19">{index}</text>')
        p.append(f'<text x="116" y="{y + 34}" class="ttl" font-size="19">{xml_escape(short(head, 24))}</text>')
        lines = svg_text_lines(desc)
        for line_no, line in enumerate(lines):
            p.append(f'<text x="116" y="{y + 61 + line_no * 20}" class="lbl" font-size="15">{xml_escape(line)}</text>')
        y += 102
    p.append('</svg>')
    svg = "\n".join(p)
    xml.dom.minidom.parseString(svg.encode("utf-8"))
    return svg


def wrap_pixels(draw, text, font, max_width):
    lines, current = [], ""
    for char in text:
        candidate = current + char
        if current and draw.textbbox((0, 0), candidate, font=font)[2] > max_width:
            lines.append(current)
            current = char
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def build_cover(post_data, path):
    width = height = 760
    image = Image.new("RGB", (width, height), "#0f654e")
    draw = ImageDraw.Draw(image)
    for y in range(height):
        ratio = y / height
        color = (
            int(20 + (8 - 20) * ratio),
            int(139 + (79 - 139) * ratio),
            int(105 + (59 - 105) * ratio),
        )
        draw.line((0, y, width, y), fill=color)
    draw.ellipse((540, -90, 850, 220), fill="#187f64")
    draw.arc((-80, 430, 830, 850), 205, 338, fill="#c6a45c", width=4)
    title_font = ImageFont.truetype(str(FONT_BOLD), 45)
    meta_font = ImageFont.truetype(str(FONT_BOLD), 22)
    small_font = ImageFont.truetype(str(FONT_MEDIUM), 21)
    site_font = ImageFont.truetype(str(FONT_BOLD), 29)
    lines = wrap_pixels(draw, post_data["title"], title_font, 650)
    title_y = 218 - max(0, len(lines) - 3) * 18
    for line in lines[:5]:
        draw.text((58, title_y), line, font=title_font, fill="white")
        title_y += 66
    axis = AXIS_LABEL[post_data["axis"]]
    draw.rounded_rectangle((58, 66, 58 + 25 * len(axis) + 44, 111), radius=22, fill="#f2e7c9")
    draw.text((77, 75), axis, font=meta_font, fill="#174f3b")
    jp_date = post_data["date"].replace("-", ".")
    draw.text((59, 131), jp_date, font=small_font, fill="#d6e9e1")
    draw.text((58, 652), SITE_NAME, font=site_font, fill="white")
    draw.text((59, 699), "morimachi.enshu-lifehack.com", font=small_font, fill="#d6e9e1")
    image.save(path, "JPEG", quality=91, optimize=True)


def figure_markup(slug, number, alt, caption):
    return (
        '<figure class="post-figure" style="margin:28px 0;overflow-x:auto;-webkit-overflow-scrolling:touch">'
        f'<img src="/blog/{esc(slug)}/fig{number}.svg" alt="{esc(alt)}" '
        'style="width:100%;min-width:600px;height:auto;border:1px solid var(--line);border-radius:12px;display:block">'
        f'<figcaption style="font-size:12.5px;color:var(--mut);margin-top:8px;line-height:1.65">図{number}　{esc(caption)}</figcaption>'
        '</figure>'
    )


def build_article(p, parts):
    slug, title, description = p["slug"], p["title"], p["description"]
    axis = AXIS_LABEL[p["axis"]]
    date_obj = dt.date.fromisoformat(p["date"])
    jp_date = f"{date_obj.year}年{date_obj.month}月{date_obj.day}日"
    good_items = "".join(f"<li>{esc(x)}</li>" for x in p["good"])
    caution_items = "".join(f"<li>{esc(x)}</li>" for x in p["caution"])
    steps = "".join(f"<li><strong>{i}.</strong> {esc(x)}</li>" for i, x in enumerate(p["actions"], 1))
    summary = "".join(f"<li>{esc(x)}</li>" for x in (p["answer"], p["good"][0], p["caution"][0]))
    source_title, source_url = p["source"]
    internal_url, internal_label = p["internal"]
    fig1 = figure_markup(slug, 1, f"{title}の事実、良い点、注意点を3段で整理した図", "公式資料から確認できること")
    fig2 = figure_markup(slug, 2, f"{title}について確認する3つの行動順を示した図", "大石が勧める確認の順番")
    json_ld = json.dumps({
        "@context": "https://schema.org", "@type": "Article", "headline": title,
        "datePublished": p["date"], "dateModified": TODAY,
        "author": {"@type": "Person", "name": "大石浩之", "url": f"{SITE}/about/author/"},
        "image": f"{SITE}/blog/{slug}/cover.jpg", "mainEntityOfPage": f"{SITE}/blog/{slug}/",
        "publisher": {"@type": "Organization", "name": "富士ヶ丘サービス株式会社"},
    }, ensure_ascii=False, separators=(",", ":"))
    return f'''<!doctype html><html lang="ja"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | {SITE_NAME}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{SITE}/blog/{esc(slug)}/">
<meta property="og:type" content="article"><meta property="og:locale" content="ja_JP">
<meta property="og:site_name" content="{SITE_NAME}"><meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:image" content="{SITE}/blog/{esc(slug)}/cover.jpg">
<meta property="og:url" content="{SITE}/blog/{esc(slug)}/"><meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{json_ld}</script>
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
{part("head-css", parts["head-css"])}
</head><body>
{part("header", parts["header"])}
{part("disclaimer", parts["disclaimer"])}
<main id="main"><div class="wrap">
<p class="breadcrumb"><a href="/">静岡県森町ライフハック</a> ／ <a href="/blog/">ブログ</a> ／ {esc(title)}</p>
<article class="post">
<p class="post-date"><time datetime="{p["date"]}">{jp_date}</time>　<span>{esc(axis)}</span></p>
<h1>{esc(title)}</h1>
<p class="post-cover"><img src="cover.jpg" alt="{esc(title)}の記事表紙" width="760" height="760" fetchpriority="high" decoding="async"></p>
<div class="post-point"><p class="post-point-label">この記事の要点</p>
<p class="post-point-q">Q. {esc(p["question"])}</p>
<p class="post-point-a">A. <strong>{esc(p["answer"])}</strong></p></div>
<p>{esc(description)}</p>
<h2 class="sec">まず、公式資料から事実を整理する</h2>
<p>{esc(p["fact"])}</p>
{fig1}
<h2 class="sec">評価——良い点と、注文したい点</h2>
<h3>良い点</h3><ul class="post-summary">{good_items}</ul>
<h3>注文したい点</h3><ul class="post-summary">{caution_items}</ul>
{fig2}
<h2 class="sec">大石の視点</h2>
<p>最後に一言。{esc(p["view"])}</p>
<h2 class="sec">確認する順番</h2>
<ol class="post-steps">{steps}</ol>
<h2 class="sec">まとめ</h2><ul class="post-summary">{summary}</ul>
<div class="action-grid"><a class="btn" href="{esc(internal_url)}">{esc(internal_label)}</a><a class="btn" href="/blog/">ブログの記事一覧へ戻る</a></div>
<h2 class="sec">参考にした公式情報</h2>
<ul class="post-sources"><li><a href="{esc(source_url)}" target="_blank" rel="noopener">{esc(source_title)}</a>（{JP_TODAY}確認）</li></ul>
<p class="post-author">この記事の執筆：<a href="/about/author/">{AUTHOR}</a>／富士ヶ丘サービス株式会社</p>
<p class="verified">最終確認日：{TODAY} ／ 本記事は公表情報と執筆者の見解を分けて記載しています。制度・開催・公開状況は変更される場合があるため、最新情報は公式ページでご確認ください。</p>
</article></div></main>
{part("footer", parts["footer"])}
</body></html>
'''


def write_post(p, parts):
    directory = BLOG / p["slug"]
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "index.html").write_text(build_article(p, parts), encoding="utf-8", newline="\n")
    build_cover(p, directory / "cover.jpg")
    fig1_rows = (
        ("公式資料で確認", p["fact"]),
        ("良い点", p["good"][0]),
        ("注意点", p["caution"][0]),
    )
    fig2_rows = tuple((f"確認 {index}", action) for index, action in enumerate(p["actions"], 1))
    (directory / "fig1.svg").write_text(
        build_figure("公式資料から見えること", fig1_rows, f"{p['title']}の事実整理"),
        encoding="utf-8", newline="\n")
    (directory / "fig2.svg").write_text(
        build_figure("大石が勧める確認の順番", fig2_rows, f"{p['title']}の行動順"),
        encoding="utf-8", newline="\n")


def update_ledger():
    data = json.loads(LEDGER.read_text(encoding="utf-8-sig"))
    by_slug = {item["slug"]: item for item in data["posts"]}
    for p in POSTS:
        by_slug[p["slug"]] = {
            "slug": p["slug"], "date": p["date"], "axis": p["axis"],
            "title": p["title"], "description": p["description"],
            "home_description": p["description"], "cta": "official",
            "primary_source": f"{p['source'][0]}を{TODAY}に確認",
            "cover_alt": f"{p['title']}の記事表紙",
        }
    data["posts"] = sorted(by_slug.values(), key=lambda item: (item["date"], item["slug"]))
    LEDGER.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def validate_dates():
    expected = {dt.date(2026, 7, 3) + dt.timedelta(days=i) for i in range(34)}
    existing = {dt.date(2026, 8, 4)}
    actual = {dt.date.fromisoformat(p["date"]) for p in POSTS}
    if actual | existing != expected or len(POSTS) != 33:
        raise RuntimeError("日付の連続性が崩れています")
    if len({p["slug"] for p in POSTS}) != len(POSTS):
        raise RuntimeError("slugが重複しています")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    validate_dates()
    parts = load_parts()
    for item in POSTS:
        write_post(item, parts)
    update_ledger()
    print(f"日次ブログ {len(POSTS)} 本を生成しました（既存1本と合わせて34日連続）")
    print(f"記事期間: {POSTS[0]['date']}〜{POSTS[-1]['date']} / 確認日: {TODAY}")


if __name__ == "__main__":
    main()
