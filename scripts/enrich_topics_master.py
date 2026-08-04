# -*- coding: utf-8 -*-
"""topics_master.json に改修判断と検索辞書を付与する（抜本改修指示書 4.1 / 5.1 / 9.1）。

付与する項目
  hub             : 6つの生活場面（procedures/family/care/property/trouble/enjoy）
  page_type       : hub / parent / detail
  action          : keep / rewrite / merge / redirect / noindex
  merge_target    : 統合先URL（action=merge のときのみ）
  priority        : P0 / P1 / P2 / P3
  intent          : 検索者が解決したいこと
  primary_keyword : 主検索語
  needs           : 困りごとの文章（検索辞書）
  audience        : 対象者（検索辞書）
  department      : 担当課（facts.window から自動導出）

このスクリプトは冪等。何度実行しても同じ結果になる。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

HUBS = {
    "procedures": "手続きしたい",
    "family": "子ども・家族",
    "care": "親・介護",
    "property": "家・土地",
    "trouble": "困った・緊急",
    "enjoy": "暮らしを楽しむ",
}

# slug（/life/ 以下）→ (hub, page_type, priority, intent, primary_keyword, needs, audience)
# action / merge_target は MERGES で別に定義する。
P = "parent"
D = "detail"
H = "hub"

TABLE: dict[str, tuple] = {
    # ---------------- 手続きしたい ----------------
    "start-living/": ("procedures", H, "P1", "森町で暮らし始めたときの手続きを一覧で把握する", "森町 転入 手続き", ["引っ越してきた", "何から手続きすればいい"], ["転入者"]),
    "start-living/moved-in": ("procedures", P, "P0", "転入直後にやる手続きを順番に片づける", "森町 転入届", ["引っ越してきた", "転入の手続きが分からない", "住所変更したい"], ["転入者", "世帯主"]),
    "start-living/certificates": ("procedures", P, "P0", "必要な証明書がどれか選び、最短で受け取る", "森町 住民票 取り方", ["証明書がいる", "住民票がほしい", "戸籍謄本がいる", "印鑑証明がいる"], ["本人", "代理人"]),
    "start-living/resident-registration": ("procedures", D, "P0", "住民票の写しを急ぎで手に入れる", "森町 住民票 コンビニ", ["今日中に住民票がいる", "土日に住民票がほしい"], ["本人", "同一世帯"]),
    "start-living/mynumber": ("procedures", D, "P0", "マイナンバーカードを申請から受け取りまで進める", "森町 マイナンバーカード 申請", ["マイナンバーカードを作りたい", "受け取り方が分からない", "更新したい"], ["本人", "保護者"]),
    "start-living/city-hall-branches": ("procedures", D, "P1", "役場のどの窓口へ行けばよいか・開いている時間を知る", "森町役場 窓口 時間", ["役場は何時まで", "土日にやってる窓口はある", "支所はどこ"], ["来庁者"]),
    "start-living/how-to-garbage": ("procedures", P, "P0", "ごみの分別と出し方を調べる", "森町 ごみ 分別", ["ごみの分け方が分からない", "これは何ごみ", "ごみの出し方"], ["住民"]),
    "start-living/garbage-sorting-calendar": ("procedures", D, "P0", "自分の地区の収集日を確認する", "森町 ごみ 収集日", ["何曜日に出せる", "ごみカレンダーがほしい"], ["住民"]),
    "start-living/bulky-garbage-dropoff": ("procedures", D, "P1", "粗大ごみの持ち込み先と費用を知る", "森町 粗大ごみ", ["大きな家具を捨てたい", "粗大ごみはどこへ"], ["住民"]),
    "start-living/water-start-stop-fees": ("procedures", D, "P0", "水道の使用開始・中止を届け出る", "森町 水道 開栓 中止", ["水道を使い始めたい", "水道を止めたい", "引っ越しで水道の手続き"], ["転入者", "転出者"]),
    "start-living/water-sewer": ("procedures", D, "P2", "水道・下水道料金の仕組みと金額を知る", "森町 水道料金", ["水道代はいくら", "下水道料金の計算"], ["住民"]),
    "start-living/dog-registration": ("procedures", D, "P1", "犬の登録・鑑札交付と狂犬病予防注射を済ませる", "森町 犬 登録", ["犬を飼い始めた", "狂犬病の注射はいつ", "鑑札をなくした"], ["飼い主"]),
    "start-living/dog-registration-rabies": ("procedures", D, "P2", "毎年の狂犬病予防注射を受ける", "森町 狂犬病予防注射", ["集合注射はいつ", "注射済票がほしい"], ["飼い主"]),
    "start-living/pets-lost-animals": ("procedures", D, "P2", "いなくなった犬・猫を探す連絡先を知る", "森町 迷い犬 迷い猫", ["犬がいなくなった", "猫を保護した"], ["飼い主", "発見者"]),
    "start-living/public-transit": ("procedures", D, "P1", "森町での移動手段（町営バス・鉄道）を調べる", "森町 バス 時刻表", ["車がなくても暮らせる", "バスはどこを走っている", "駅からの行き方"], ["住民", "移住検討者"]),
    "start-living/moving-address-change": ("procedures", D, "P2", "転入・転居・転出の届出方法を確認する", "森町 住所変更 届出", ["住所が変わった", "町内で引っ越した"], ["住民"]),
    "moving-out/": ("procedures", H, "P2", "森町から引っ越すときの手続きを一覧で把握する", "森町 転出 手続き", ["森町から出ていく", "転出でやること"], ["転出者"]),
    "moving-out/moving-away": ("procedures", P, "P1", "転出時に必要な手続きをまとめて片づける", "森町 転出 やること", ["引っ越すことになった", "何を止めればいい"], ["転出者"]),
    "moving-out/move-out-notice": ("procedures", D, "P1", "転出届をいつどこで出すか確認する", "森町 転出届", ["転出届はいつから出せる", "郵送でできる"], ["転出者"]),
    "moving-out/stop-water": ("procedures", D, "P2", "水道を廃止する届出を出す", "森町 水道 廃止", ["水道を止めたい"], ["転出者"]),
    "moving-out/bulk-garbage-cleaning": ("procedures", D, "P2", "転出前の不用品・粗大ごみを処分する", "森町 引っ越し ごみ 処分", ["家具を処分したい", "家電を捨てたい"], ["転出者"]),
    "moving-out/dog-ownership-change": ("procedures", D, "P3", "転出時の犬の登録変更をする", "森町 犬 転出 登録変更", ["犬と一緒に引っ越す"], ["飼い主"]),
    "moving-out/school-nursery-procedures": ("procedures", D, "P2", "子どもの転園・転校の手続きをする", "森町 転校 手続き", ["子どもが転校する", "保育園を退園する"], ["保護者"]),
    "work-life/": ("procedures", H, "P2", "税金・保険・仕事に関する手続きを一覧で把握する", "森町 税金 手続き", ["税金のことを調べたい"], ["住民"]),
    "work-life/tax": ("procedures", P, "P1", "どの税金の話か整理して担当係にたどりつく", "森町 税金", ["税金のことで聞きたい", "どの課に行けばいい"], ["納税者"]),
    "work-life/resident-tax": ("procedures", D, "P1", "住民税の納付方法と申告を確認する", "森町 住民税", ["住民税はいくら", "申告が必要か"], ["納税者"]),
    "work-life/city-tax-payment": ("procedures", D, "P1", "町税の納付方法を選ぶ", "森町 町税 納付", ["どこで払える", "スマホで払いたい", "口座振替にしたい"], ["納税者"]),
    "work-life/national-health-insurance-tax": ("procedures", D, "P2", "国民健康保険税の税率・減免を確認する", "森町 国民健康保険税", ["保険税が高い", "減免はある"], ["国保加入者"]),
    "work-life/light-vehicle-tax": ("procedures", D, "P2", "軽自動車税の税額と手続きを確認する", "森町 軽自動車税", ["軽自動車の税金はいくら", "廃車の手続き"], ["車両所有者"]),
    "work-life/tax-certificates": ("procedures", D, "P1", "所得・課税・納税証明書を取得する", "森町 所得証明書", ["課税証明書がいる", "納税証明書がほしい"], ["本人", "代理人"]),
    "work-life/nhk-pension": ("procedures", D, "P2", "国民健康保険・国民年金の加入と喪失を手続きする", "森町 国民年金 手続き", ["会社を辞めた", "扶養から外れた"], ["退職者", "住民"]),
    "work-life/job-change": ("procedures", D, "P2", "森町で仕事を探す入口を知る", "森町 求人", ["仕事を探している", "転職したい"], ["求職者"]),
    "work-life/job-recruitment": ("procedures", D, "P3", "森町職員の採用情報を確認する", "森町 職員採用", ["役場で働きたい"], ["求職者"]),
    "work-life/start-business": ("procedures", D, "P3", "森町で起業・創業する相談先を知る", "森町 創業支援", ["店を開きたい", "創業の補助金"], ["創業希望者"]),
    "work-life/start-farming": ("procedures", D, "P3", "森町で就農する準備を進める", "森町 就農", ["農業を始めたい", "農地を借りたい"], ["就農希望者"]),
    "work-life/subsidies": ("procedures", D, "P2", "森町の補助金にどんなものがあるか調べる", "森町 補助金", ["使える補助金はある", "助成金を探している"], ["住民"]),
    "work-life/tax-guide": ("trouble", D, "P0", "納付が難しいときの猶予制度を相談する", "森町 税金 納付猶予", ["分割で払いたい", "納付を待ってほしい"], ["納税者"]),
    "work-life/my-number-card": ("procedures", D, "P1", "マイナンバーカードを申請する", "森町 マイナンバーカード", ["カードを作りたい"], ["本人"]),
    "living-soon/": ("procedures", H, "P2", "森町へ移り住む前に確認することを把握する", "森町 移住", ["森町に住もうか迷っている"], ["移住検討者"]),
    "living-soon/about-morimachi": ("procedures", D, "P3", "森町での暮らしの実際を知る", "森町 住みやすさ", ["どんな町か知りたい"], ["移住検討者"]),
    "living-soon/moving-decided": ("procedures", P, "P1", "引っ越しが決まってからの段取りを立てる", "引っ越し やることリスト", ["何をいつまでにやる", "引っ越しの段取り"], ["引っ越す人"]),
    "living-soon/want-to-live": ("procedures", D, "P3", "森町で広い家に住む選択肢を検討する", "森町 田舎暮らし", ["自然の中で子育てしたい"], ["移住検討者"]),
    "living-soon/transportation": ("procedures", D, "P2", "住む地区を決める前に移動手段を確かめる", "森町 交通 移動手段", ["車は必須か", "バスは通っている"], ["移住検討者"]),
    "living-soon/school-districts": ("family", D, "P2", "引っ越し先の通学区を調べる", "森町 学区", ["どの小学校に通う"], ["保護者"]),
    "living-soon/bus-license-return": ("care", D, "P2", "免許返納後の移動手段を確保する", "森町 免許返納", ["運転をやめたあと困る"], ["高齢者", "家族"]),
    "living-soon/disaster-risk": ("trouble", D, "P1", "住む候補地の災害リスクを確かめる", "森町 ハザードマップ 土地", ["浸水しないか知りたい", "土砂災害の危険はあるか"], ["移住検討者", "住宅取得者"]),

    # ---------------- 子ども・家族 ----------------
    "family-grow/": ("family", H, "P1", "結婚・妊娠・出産・子育ての手続きを一覧で把握する", "森町 子育て 手続き", ["子どものことで手続きがある"], ["保護者"]),
    "family-grow/marriage": ("family", D, "P1", "婚姻届の提出と結婚後の手続きを進める", "森町 婚姻届", ["結婚することになった", "婚姻届はどこに出す"], ["婚姻当事者"]),
    "family-grow/pregnancy": ("family", D, "P0", "妊娠届を出して母子健康手帳を受け取る", "森町 妊娠届 母子手帳", ["妊娠が分かった", "母子手帳はどこでもらう"], ["妊婦"]),
    "family-grow/childbirth": ("family", P, "P0", "出生届と出産後の手続きをまとめて進める", "森町 出生届", ["赤ちゃんが生まれた", "出産後の手続き"], ["保護者"]),
    "family-grow/child-allowance": ("family", D, "P0", "児童手当とこども医療費助成を期限内に申請する", "森町 児童手当 申請", ["児童手当をもらいたい", "医療費助成の手続き", "15日以内の申請"], ["保護者"]),
    "family-grow/child-allowance-medical": ("family", D, "P1", "児童手当とこども医療費助成の申請漏れを防ぐ", "森町 こども医療費助成", ["医療費の助成を受けたい"], ["保護者"]),
    "family-grow/infant-health-check": ("family", D, "P1", "乳幼児健診の時期と会場を確認する", "森町 乳幼児健診", ["健診はいつ", "案内が来ない"], ["保護者"]),
    "family-grow/child-vaccination": ("family", D, "P0", "子どもの予防接種を受ける", "森町 予防接種 子ども", ["予診票がほしい", "接種はどこで受ける"], ["保護者"]),
    "family-grow/nursery-school": ("family", P, "P1", "幼稚園・保育園の選び方を知る", "森町 保育園 幼稚園", ["どこに預けられる", "園を選びたい"], ["保護者"]),
    "family-grow/nursery-childcare": ("family", D, "P1", "保育園の入所申込みと病児保育を利用する", "森町 保育園 申込み", ["入所の申込み方法", "子どもが熱を出して預けたい"], ["保護者"]),
    "family-grow/parenting-support": ("family", D, "P1", "子育ての悩みを相談できる場所を見つける", "森町 子育て相談", ["子育てがつらい", "誰かに相談したい"], ["保護者"]),
    "family-grow/developmental-support": ("family", D, "P1", "子どもの発達の心配を相談する", "森町 発達相談", ["ことばが遅い気がする", "発達が気になる"], ["保護者"]),
    "family-grow/single-parent-support": ("family", D, "P1", "ひとり親家庭の手当と助成を受ける", "森町 児童扶養手当", ["ひとり親の支援を知りたい", "離婚後の手当"], ["ひとり親"]),
    "education/": ("family", H, "P2", "学校・学区・教育相談の情報を一覧で把握する", "森町 学校", ["学校のことを調べたい"], ["保護者"]),
    "education/school-zones": ("family", P, "P1", "住所からどの小中学校に通うか確かめる", "森町 通学区域", ["どの学校の学区か", "指定校を変更したい"], ["保護者"]),
    "education/elementary-middle-school": ("family", D, "P2", "森町の小中学校の一覧と連絡先を知る", "森町 小中学校 一覧", ["学校の電話番号を知りたい"], ["保護者"]),
    "education/school-district-transfer": ("family", D, "P1", "転校の手続きを進める", "森町 転校 手続き", ["転校することになった"], ["保護者"]),
    "education/educational-consulting": ("family", P, "P1", "学校に行きづらい・就学の不安を相談する", "森町 教育相談 不登校", ["学校に行きたがらない", "就学が不安", "誰に相談すれば"], ["保護者", "児童生徒"]),
    "education/school-attendance-support": ("family", D, "P1", "就学の不安を相談する", "森町 就学相談", ["就学時健診が心配"], ["保護者"]),
    "education/school-expense-support": ("family", D, "P1", "学校費用の負担を軽くする制度を使う", "森町 就学援助", ["給食費が払えない", "学用品の費用がつらい"], ["保護者"]),
    "education/school-meals": ("family", D, "P2", "学校給食の献立・費用・アレルギー対応を確認する", "森町 学校給食", ["アレルギー対応はある", "給食費はいくら"], ["保護者"]),
    "education/study-facilities": ("enjoy", D, "P3", "子どもが勉強できる場所を探す", "森町 図書館 学習室", ["勉強する場所がほしい"], ["児童生徒"]),
    "education/after-school-club": ("family", D, "P1", "放課後児童クラブの対象と申込時期を確認する", "森町 放課後児童クラブ 学童", ["放課後の預け先がない", "学童に入れたい", "申込みはいつ"], ["保護者"]),

    # ---------------- 親・介護 ----------------
    "parents-care/": ("care", H, "P0", "親の介護に関する相談先と手続きを一覧で把握する", "森町 介護", ["親の介護が心配"], ["家族"]),
    "parents-care/long-term-care-insurance": ("care", P, "P0", "親の介護が始まったときの流れ全体をつかむ", "森町 介護 始まったら", ["親に介護が必要になった", "何から始めればいい", "要介護認定を受けたい"], ["家族", "本人"]),
    "parents-care/care-certification-support-center": ("care", D, "P0", "要介護認定を申請して結果を受け取る", "森町 要介護認定 申請", ["認定を申請したい", "結果はいつ届く"], ["家族", "本人"]),
    "parents-care/care-started": ("care", D, "P0", "認定後にケアプランの作成を依頼する", "森町 ケアプラン ケアマネ", ["認定が出た次は何", "ケアマネを探したい"], ["家族", "本人"]),
    "parents-care/community-support-center": ("care", P, "P0", "介護の困りごとをまず相談する窓口を知る", "森町 地域包括支援センター", ["どこに相談すればいい", "介護で困っている"], ["家族", "本人"]),
    "parents-care/dementia-consultation": ("care", D, "P0", "認知症かもしれない親のことを相談する", "森町 認知症 相談", ["物忘れがひどい", "認知症かもしれない"], ["家族"]),
    "parents-care/check-parents": ("care", D, "P1", "離れて暮らす親の様子を見守る方法を知る", "森町 高齢者 見守り", ["遠くの親が心配", "一人暮らしの親"], ["別居の家族"]),
    "parents-care/find-nursing-home": ("care", D, "P1", "親が入る介護施設を探す", "森町 介護施設 探し方", ["施設に入れたい", "どんな施設がある"], ["家族"]),
    "parents-care/adult-guardianship": ("care", D, "P1", "判断能力が落ちた親の財産と契約を守る", "森町 成年後見", ["契約ができなくなった", "財産管理が心配"], ["家族"]),
    "parents-care/elderly-transportation": ("care", D, "P1", "高齢の親の通院・買い物の移動手段を確保する", "森町 公共交通利用券 高齢者", ["親が運転をやめた", "通院の足がない"], ["高齢者", "家族"]),
    "troubles-consult/care-consultation": ("care", D, "P1", "介護の困りごとを相談する", "森町 介護 相談", ["介護で困った"], ["家族"]),

    # ---------------- 家・土地 ----------------
    "housing/": ("property", H, "P1", "住まい・空き家・不動産の情報を一覧で把握する", "森町 住まい", ["家のことを調べたい"], ["住民"]),
    "housing/vacant-house": ("property", P, "P0", "空き家の制度（対策計画・バンク・税）を整理する", "森町 空き家", ["空き家をどうするか", "空き家バンクを使いたい"], ["所有者"]),
    "housing/sell-house": ("property", D, "P1", "森町で家を売る前に確認することを知る", "森町 家 売却", ["家を売りたい", "売る前に何を調べる"], ["所有者"]),
    "housing/buy-house": ("property", D, "P2", "森町で家を買う前に確認することを知る", "森町 家 購入", ["家を買いたい"], ["購入検討者"]),
    "housing/build-house": ("property", D, "P2", "森町で家を建てる前に補助制度を確認する", "森町 住宅 補助金", ["家を建てたい", "使える補助はある"], ["建築希望者"]),
    "housing/rent-house": ("property", D, "P2", "森町で借りられる住まいを探す", "森町 賃貸 町営住宅", ["借りる家を探している"], ["入居希望者"]),
    "housing/municipal-housing": ("property", D, "P2", "町営住宅の募集条件と申込みを確認する", "森町 町営住宅", ["町営住宅に入りたい"], ["入居希望者"]),
    "housing/public-housing-consultation": ("property", D, "P1", "住むところに困ったときの相談先を知る", "森町 住まい 相談", ["住む家がない", "家賃が払えない"], ["生活困窮者"]),
    "housing/property-tax": ("property", D, "P1", "土地・家屋の固定資産税の中身を確認する", "森町 固定資産税", ["固定資産税が高い", "課税の内容を知りたい"], ["所有者"]),
    "housing/earthquake-demolition": ("property", D, "P1", "耐震診断・改修・解体の助成を使う", "森町 耐震 解体 補助", ["古い家が心配", "解体費用の助成"], ["所有者"]),
    "housing/clean-parents-house": ("property", D, "P1", "親の家の片付けを進める", "森町 実家 片付け", ["実家の物が多い", "片付けが進まない"], ["家族"]),
    "end-of-life/": ("property", H, "P0", "おくやみ・相続・空き家の手続きを一覧で把握する", "森町 おくやみ 相続", ["家族が亡くなった"], ["遺族"]),
    "end-of-life/bereavement": ("property", P, "P0", "家族が亡くなった後の手続きを期限順に進める", "森町 死亡届 おくやみ", ["家族が亡くなった", "何から手続きする", "期限が知りたい"], ["遺族"]),
    "end-of-life/after-death-procedures": ("property", D, "P0", "死亡後の急ぐ届出を確認する", "森町 死亡後 手続き", ["急ぐ手続きは何"], ["遺族"]),
    "end-of-life/bereavement-procedures": ("property", D, "P0", "おくやみの手続きを家族で分担する", "森町 お悔やみ 手続き 一覧", ["手続きが多すぎる"], ["遺族"]),
    "end-of-life/inheritance": ("property", P, "P0", "相続で何をいつまでにやるか整理する", "森町 相続 手続き", ["相続が発生した", "相続登記はいつまで"], ["相続人"]),
    "end-of-life/inherited-house": ("property", P, "P0", "相続した親の家を使う・貸す・売る・解体するを決める", "親の家 相続 どうする", ["実家を相続した", "空き家になった実家", "売るか残すか迷う"], ["相続人"]),
    "end-of-life/inherited-vacant-house": ("property", D, "P0", "相続した家の使い道を整理する", "相続した家 空き家", ["相続した家が空いている"], ["相続人"]),
    "end-of-life/house-became-vacant": ("property", D, "P0", "相続後に空き家になった家の制度を確認する", "相続後 空き家 補助", ["空き家になってしまった"], ["相続人"]),
    "end-of-life/property-tax-inheritance": ("property", D, "P1", "相続した不動産の固定資産税の手続きをする", "森町 固定資産税 相続人代表者", ["納税通知書は誰に届く"], ["相続人"]),
    "end-of-life/pension-inheritance": ("property", D, "P1", "亡くなった後の年金・保険の手続きをする", "森町 死亡 年金 手続き", ["年金を止める手続き", "未支給年金"], ["遺族"]),
    "end-of-life/grave-memorial": ("property", D, "P2", "お墓・供養・改葬の進め方を知る", "森町 改葬許可 墓", ["墓じまいしたい", "お墓を移したい"], ["遺族"]),
    "troubles-consult/vacant-house-consultation": ("property", D, "P0", "親の家・実家をどうするか迷ったときに整理を始める", "実家 どうする 相談", ["実家をどうしよう"], ["家族"]),
    "troubles-consult/farmland/": ("property", P, "P1", "相続した農地の扱いを整理する", "森町 農地 相続", ["田んぼを相続した", "畑をどうする"], ["相続人", "所有者"]),
    "troubles-consult/farmland/inheritance": ("property", D, "P1", "農地を相続したときの届出をする", "農地 相続 届出", ["農地の相続手続き"], ["相続人"]),
    "troubles-consult/farmland/sell-or-rent": ("property", D, "P1", "使っていない農地を売る・貸す", "農地 売りたい 貸したい", ["耕作できない農地がある"], ["所有者"]),
    "troubles-consult/farmland/conversion": ("property", D, "P2", "農地を宅地・駐車場にする（農地法4条・5条）", "農地転用 4条 5条", ["農地に家を建てたい", "駐車場にしたい"], ["所有者"]),
    "troubles-consult/farmland/change-use": ("property", D, "P2", "農地を別の用途に使う相談をする", "農地 用途変更", ["農地の使い道を変えたい"], ["所有者"]),
    "troubles-consult/farmland/noshin-exclusion": ("property", D, "P2", "農振農用地区域からの除外を相談する", "農振除外 森町", ["青地を白地にしたい"], ["所有者"]),
    "troubles-consult/farmland/certificates": ("property", D, "P2", "耕作証明・非農地証明を取得する", "耕作証明書 非農地証明", ["証明書が必要と言われた"], ["所有者"]),

    # ---------------- 困った・緊急 ----------------
    "emergency/": ("trouble", H, "P0", "防災・災害時の行動と窓口を一覧で把握する", "森町 防災", ["災害に備えたい"], ["住民"]),
    "emergency/evacuation-hazard-map": ("trouble", P, "P0", "いつ・どこへ逃げるかを決めておく", "森町 ハザードマップ 避難", ["どこに逃げればいい", "いつ避難する", "大雨で不安"], ["住民"]),
    "emergency/hazard-maps": ("trouble", D, "P0", "自宅の災害リスクを確かめる", "森町 ハザードマップ", ["家は安全か"], ["住民"]),
    "emergency/evacuation-centers": ("trouble", D, "P0", "指定避難所の場所を確認する", "森町 避難所", ["避難所はどこ"], ["住民"]),
    "emergency/storm-heavy-rain": ("trouble", D, "P0", "台風・大雨が近づいたときの行動を決める", "森町 台風 大雨 避難", ["台風が来る"], ["住民"]),
    "emergency/earthquake": ("trouble", D, "P0", "地震・津波に備える", "森町 地震 備え", ["地震が心配", "耐震の補助"], ["住民"]),
    "emergency/road-river-info": ("trouble", D, "P1", "道路の通行止めと川の水位を今すぐ確かめる", "森町 通行止め 川 水位", ["道が通れるか", "川が増水している"], ["住民", "通勤者"]),
    "emergency/disaster-mail-line": ("trouble", D, "P1", "災害情報の受け取り方を設定する", "森町 防災 LINE メール", ["災害情報を受け取りたい"], ["住民"]),
    "emergency/disaster-certificates-procedures": ("trouble", D, "P1", "り災証明書と税の減免を申請する", "森町 り災証明書", ["家が被害を受けた", "被災後の手続き"], ["被災者"]),
    "emergency/fire-ambulance": ("trouble", D, "P0", "火事・急病のときの119番と管轄を知る", "森町 消防 救急 119", ["救急車を呼びたい", "火事のとき"], ["住民"]),
    "emergency/emergency-medical": ("trouble", D, "P0", "救急車を呼ぶか迷ったときに判断する", "♯7119 森町", ["救急車を呼ぶべきか", "病院に行くべきか"], ["住民"]),
    "emergency/pet-disaster-prevention": ("trouble", D, "P2", "ペットと一緒に避難する備えをする", "森町 ペット 同行避難", ["ペットと避難できる"], ["飼い主"]),
    "health-medical/": ("trouble", H, "P0", "医療・検診・障がい福祉の情報を一覧で把握する", "森町 医療", ["病院のことを調べたい"], ["住民"]),
    "health-medical/night-holiday-medical": ("trouble", P, "P0", "夜間・休日に具合が悪くなったときの受診先を決める", "森町 夜間 休日 救急", ["夜に熱が出た", "休日に病院はやっている", "子どもの急病"], ["住民", "保護者"]),
    "health-medical/holiday-night-emergency-care": ("trouble", D, "P0", "休日夜間の急患の受診先を知る", "森町 休日夜間 急患", ["休日に診てもらいたい"], ["住民"]),
    "health-medical/find-hospitals": ("trouble", D, "P1", "森町とその周辺で医療機関を探す", "森町 病院 診療所", ["近くの病院を探したい", "何科にかかる"], ["住民"]),
    "health-medical/vaccinations": ("trouble", P, "P1", "自分・家族が受ける予防接種を選ぶ", "森町 予防接種", ["予防接種を受けたい", "対象になるか知りたい"], ["住民", "保護者"]),
    "health-medical/adult-vaccination": ("trouble", D, "P1", "おとなの予防接種の対象と費用を確認する", "森町 高齢者 予防接種", ["インフルエンザの助成", "肺炎球菌ワクチン"], ["成人", "高齢者"]),
    "health-medical/health-checkups": ("trouble", P, "P1", "受けられる健診・検診を選ぶ", "森町 健康診断 検診", ["健診を受けたい", "受診券が届いた"], ["住民"]),
    "health-medical/cancer-specific-checkups": ("trouble", D, "P1", "がん検診の対象と時期を確認する", "森町 がん検診", ["がん検診はいつ"], ["住民"]),
    "health-medical/health-promotion": ("trouble", D, "P2", "健康づくりの取り組みに参加する", "森町 健康マイレージ", ["健康づくりをしたい"], ["住民"]),
    "health-medical/dental-care": ("trouble", D, "P2", "歯科検診と町内の歯科医院を確認する", "森町 歯科 歯周病検診", ["歯医者を探している"], ["住民"]),
    "health-medical/mental-health-consulting": ("trouble", D, "P1", "こころの不調を相談する", "森町 こころの相談", ["気持ちがつらい", "眠れない"], ["住民", "家族"]),
    "health-medical/disability-welfare": ("trouble", P, "P1", "障がい者手帳の取得と福祉サービスを利用する", "森町 障害者手帳", ["手帳を取りたい", "どんな支援がある"], ["本人", "家族"]),
    "health-medical/disability-services": ("trouble", D, "P1", "障がい福祉サービスの内容を知る", "森町 障害福祉サービス", ["サービスを使いたい"], ["本人", "家族"]),
    "troubles-consult/": ("trouble", H, "P1", "困りごとの相談窓口を一覧で把握する", "森町 相談窓口", ["誰に相談すればいい"], ["住民"]),
    "troubles-consult/legal-general-consultation": ("trouble", D, "P1", "無料法律相談など専門相談につなぐ", "森町 無料法律相談", ["弁護士に相談したい", "どこに相談すれば"], ["住民"]),
    "troubles-consult/cannot-pay-tax": ("trouble", P, "P0", "税金・保険税が払えないときに差押えの前に相談する", "森町 税金 払えない", ["税金が払えない", "督促状が来た", "差押えが怖い"], ["納税者"]),
    "troubles-consult/living-costs-trouble": ("trouble", D, "P0", "生活費が足りないときの支援を受ける", "森町 生活困窮 相談", ["お金がない", "生活が苦しい"], ["生活困窮者"]),
    "troubles-consult/consumer-fraud": ("trouble", D, "P0", "詐欺・悪質商法の被害を相談する", "森町 消費生活相談", ["だまされたかも", "解約したい", "特殊詐欺"], ["住民"]),
    "troubles-consult/child-consultation": ("trouble", D, "P1", "子どものことの不安を相談する", "森町 こども家庭センター", ["子どものことで不安"], ["保護者"]),
    "troubles-consult/disability-consultation": ("trouble", D, "P1", "障害のことを相談する", "森町 障害 相談", ["障害のことで相談したい"], ["本人", "家族"]),
    "troubles-consult/foreign-resident-consultation": ("trouble", D, "P2", "外国人住民の手続きと相談先を知る", "森町 外国人 相談", ["日本語が不安", "在留の手続き"], ["外国人住民"]),
    "troubles-consult/animal-pet-consultation": ("trouble", D, "P2", "動物・ペットの困りごとを相談する", "森町 動物 苦情 相談", ["野良猫が困る", "近所の犬"], ["住民"]),
    "troubles-consult/road-repair-mirror": ("trouble", D, "P2", "道路の穴・カーブミラーの不具合を通報する", "森町 道路 通報", ["道路が壊れている", "ミラーが見えない"], ["住民"]),

    # ---------------- 暮らしを楽しむ ----------------
    "play-out/": ("enjoy", H, "P2", "公園・図書館・公共施設の情報を一覧で把握する", "森町 施設", ["出かける場所を探したい"], ["住民"]),
    "play-out/facilities-library-parks": ("enjoy", P, "P2", "森町の公共施設を目的別に探す", "森町 公共施設", ["どんな施設がある"], ["住民"]),
    "play-out/find-parks": ("enjoy", D, "P2", "目的に合う公園・遊び場を選ぶ", "森町 公園", ["子どもを遊ばせたい", "遊具のある公園"], ["家族"]),
    "play-out/kids-playgrounds": ("enjoy", D, "P3", "子どもの遊び場を探す", "森町 子ども 遊び場", ["雨の日に遊べる場所"], ["家族"]),
    "play-out/visit-library": ("enjoy", D, "P2", "図書館の開館日と利用方法を確認する", "森町立図書館", ["図書館は開いている", "本を借りたい"], ["住民"]),
    "play-out/cultural-facilities": ("enjoy", D, "P3", "文化施設（ミキホール）の利用方法を確認する", "森町 ミキホール", ["ホールを使いたい"], ["住民"]),
    "play-out/sports-facilities": ("enjoy", D, "P3", "スポーツ施設の予約・料金を確認する", "森町 体育館 予約", ["体育館を借りたい"], ["住民"]),
    "play-out/swimming-pools": ("enjoy", D, "P3", "プールの営業日・料金を確認する", "森町 プール", ["プールはやっている"], ["住民"]),
    "play-out/rent-public-facilities": ("enjoy", D, "P2", "公共施設を借りる手続きをする", "森町 施設 予約", ["会議室を借りたい"], ["住民", "団体"]),
    "play-out/parking-access": ("enjoy", D, "P3", "公共施設の駐車場とアクセスを確認する", "森町 施設 駐車場", ["駐車場はある", "行き方を知りたい"], ["来訪者"]),
}

# 統合（301）: 統合元 → 統合先
MERGES: dict[str, str] = {
    "/life/health-medical/holiday-night-emergency-care/": "/life/health-medical/night-holiday-medical/",
    "/life/emergency/emergency-medical/": "/life/health-medical/night-holiday-medical/",
    "/life/emergency/hazard-maps/": "/life/emergency/evacuation-hazard-map/",
    "/life/emergency/storm-heavy-rain/": "/life/emergency/evacuation-hazard-map/",
    "/life/end-of-life/after-death-procedures/": "/life/end-of-life/bereavement/",
    "/life/end-of-life/bereavement-procedures/": "/life/end-of-life/bereavement/",
    "/life/end-of-life/house-became-vacant/": "/life/end-of-life/inherited-house/",
    "/life/end-of-life/inherited-vacant-house/": "/life/end-of-life/inherited-house/",
    "/life/troubles-consult/vacant-house-consultation/": "/life/end-of-life/inherited-house/",
    "/life/troubles-consult/care-consultation/": "/life/parents-care/community-support-center/",
    "/life/parents-care/care-certification-support-center/": "/life/parents-care/long-term-care-insurance/",
    "/life/work-life/my-number-card/": "/life/start-living/mynumber/",
    "/life/start-living/garbage-sorting-calendar/": "/life/start-living/how-to-garbage/",
    "/life/work-life/tax-guide/": "/life/troubles-consult/cannot-pay-tax/",
    "/life/troubles-consult/disability-consultation/": "/life/health-medical/disability-welfare/",
    "/life/health-medical/disability-services/": "/life/health-medical/disability-welfare/",
    "/life/living-soon/transportation/": "/life/start-living/public-transit/",
    "/life/living-soon/bus-license-return/": "/life/parents-care/elderly-transportation/",
    "/life/start-living/moving-address-change/": "/life/start-living/moved-in/",
    "/life/moving-out/stop-water/": "/life/start-living/water-start-stop-fees/",
    "/life/living-soon/school-districts/": "/life/education/school-zones/",
    "/life/education/school-attendance-support/": "/life/education/educational-consulting/",
    "/life/family-grow/child-allowance-medical/": "/life/family-grow/child-allowance/",
    "/life/start-living/dog-registration-rabies/": "/life/start-living/dog-registration/",
    "/life/play-out/kids-playgrounds/": "/life/play-out/find-parks/",
    "/life/troubles-consult/farmland/change-use/": "/life/troubles-consult/farmland/conversion/",
}

# 統合先として内容を書き直すページ
REWRITES = sorted(set(MERGES.values()))


def department_from_facts(facts: dict) -> list[str]:
    window = (facts or {}).get("window") or ""
    if not window:
        return []
    parts = re.split(r"[、／/（(]", window)
    depts = []
    for part in parts:
        part = part.strip().rstrip("）)")
        if not part:
            continue
        m = re.match(r"^([^\s]*?(?:課|係|センター|委員会|支所|本部|病院))", part)
        if m and m.group(1) not in depts:
            depts.append(m.group(1))
    return depts[:4]


def main() -> None:
    path = ROOT / "data" / "topics_master.json"
    topics = json.loads(path.read_text(encoding="utf-8"))

    missing = []
    for topic in topics:
        href = topic["href"]
        key = href.replace("/life/", "").rstrip("/") or "/"
        # ディレクトリindex（末尾が / のカテゴリ）はキーを "xxx/" とする
        if href.count("/") == 3 or (href.startswith("/life/troubles-consult/farmland/") and href.endswith("farmland/")):
            key = href.replace("/life/", "")
        entry = TABLE.get(key) or TABLE.get(key + "/")
        if not entry:
            missing.append(href)
            continue
        hub, page_type, priority, intent, kw, needs, audience = entry
        topic["hub"] = hub
        topic["hub_label"] = HUBS[hub]
        topic["page_type"] = page_type
        topic["priority"] = priority
        topic["intent"] = intent
        topic["primary_keyword"] = kw
        topic["needs"] = needs
        topic["audience"] = audience
        topic["department"] = department_from_facts(topic.get("facts", {}))
        if href in MERGES:
            topic["action"] = "merge"
            topic["merge_target"] = MERGES[href]
        elif href in REWRITES:
            topic["action"] = "rewrite"
            topic["merge_target"] = ""
        else:
            topic["action"] = "keep"
            topic["merge_target"] = ""
        topic["ledger_status"] = "作業中"

    if missing:
        print("【未マッピング】TABLE に定義が無いページ:")
        for href in missing:
            print("  " + href)

    path.write_text(json.dumps(topics, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    counts: dict[str, int] = {}
    for t in topics:
        counts[t.get("action", "?")] = counts.get(t.get("action", "?"), 0) + 1
    print(f"topics_master.json を更新: {len(topics)} 件")
    print("  action: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    hubs: dict[str, int] = {}
    for t in topics:
        hubs[t.get("hub", "?")] = hubs.get(t.get("hub", "?"), 0) + 1
    print("  hub: " + ", ".join(f"{k}={v}" for k, v in sorted(hubs.items())))
    print(f"  統合（301）: {len(MERGES)} 件 / 統合先: {len(REWRITES)} 件")


if __name__ == "__main__":
    main()
