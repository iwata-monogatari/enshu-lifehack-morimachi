#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第4期300検索意図を、6,000字以上の独立した実用ページとして生成する。"""
from __future__ import annotations

import argparse
import json
import random
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://morimachi.enshu-lifehack.com"
TODAY = "2026-08-12"
TOPICS = ROOT / "data" / "seo-phase4-topics.json"
PUBLICATION = ROOT / "data" / "seo-phase4-publication.json"
ENRICHMENT_FILES = tuple(ROOT / "data" / f"seo-phase4-enrichment-{start:03d}-{start+99:03d}.json" for start in (1, 101, 201))
LINK_START = "<!-- SEO-PHASE4-LINKS:START -->"
LINK_END = "<!-- SEO-PHASE4-LINKS:END -->"
ROBOTS_PENDING = '<meta name="robots" content="noindex,nofollow" data-phase4-pending>'

CATEGORY_PATH = {
    "行政手続き": "/life/start-living/", "子育て": "/life/family-grow/", "教育": "/life/education/",
    "健康": "/life/health-medical/", "防災": "/life/emergency/", "交通生活": "/life/play-out/",
    "住宅": "/hub/property/", "空き家": "/vacant-house/", "相続": "/inheritance/", "土地": "/land/",
    "農地": "/farmland/", "山林": "/forest/", "事業": "/life/work-life/", "仕事": "/life/work-life/",
    "文化財": "/hub/enjoy/", "神社": "/shrine/", "寺院": "/temple/", "祭り": "/hub/enjoy/",
    "歴史": "/hub/enjoy/", "観光": "/hub/enjoy/", "食": "/hub/enjoy/", "農業": "/farmland/",
}

CATEGORY_CONTEXT = {
    "行政手続き": ("届出・証明・本人確認・期限を別々に整理する", "役場の担当窓口と国の所管情報", "住所、氏名、対象日、本人確認書類"),
    "子育て": ("子どもの年齢と利用開始日から逆算する", "健康こども課と制度所管機関", "年齢、世帯状況、希望日、申請期限"),
    "教育": ("年度・住所・在籍状況をそろえて確認する", "学校教育課と教育機関", "学年、住所、在籍校、希望時期"),
    "健康": ("緊急性と通常相談を分け、対象条件を確認する", "町の保健案内と県・国の医療情報", "年齢、症状、受診歴、保険情報"),
    "防災": ("平時の準備と発災時の行動を混同しない", "森町の防災情報と所管機関", "住所、家族構成、避難経路、連絡先"),
    "交通生活": ("往路・帰路・代替手段を一組で考える", "町の公共交通案内と交通事業者", "出発地、目的地、曜日、帰宅時刻"),
    "住宅": ("建物・敷地・設備・契約資料を分ける", "森町の住まい案内と登記・建築の所管情報", "所在地、地番、名義、設備状況"),
    "空き家": ("所有関係と現在の管理状態を先に確かめる", "森町の空き家窓口と国の不動産情報", "名義、鍵、残置物、管理費"),
    "相続": ("相続人・名義・財産種類・期限を一覧にする", "町の手続き案内と法務・税務の所管情報", "被相続人、相続人、登記、財産資料"),
    "土地": ("登記と現況、接道、利用条件を照合する", "森町の土地利用案内と登記・都市計画情報", "地番、地目、境界、接道"),
    "農地": ("地目・耕作者・権利・水路管理を分ける", "森町農業委員会と農地制度の所管情報", "地番、地目、耕作状況、権利者"),
    "山林": ("境界・進入路・樹木・管理責任を確認する", "森町の林業案内と県・国の森林情報", "地番、所有者、境界、作業道"),
    "事業": ("事業内容・場所・許認可・資金を順に確認する", "森町の産業窓口と事業所管機関", "事業計画、所在地、開始時期、必要手続き"),
    "仕事": ("働き方・通勤・保険・家族時間を同時に見る", "町の就業情報と雇用所管機関", "勤務先、時間帯、交通手段、保険"),
    "文化財": ("指定名称・区分・所在地・管理者を分ける", "森町の文化財資料と国・県の文化資料", "資料名、指定区分、所在地、確認日"),
    "神社": ("神社台帳の事実と祭礼の当年運用を分ける", "神社関係者と森町の文化資料", "社名、所在地、御祭神、当年案内"),
    "寺院": ("法人名簿の事実と拝観・寺務の運用を分ける", "寺院関係者と県・町の公的資料", "寺名、宗派、所在地、拝観条件"),
    "祭り": ("文化的背景と当年の日程・交通を分ける", "主催者の当年案内と森町の文化資料", "行事名、開催年、場所、交通情報"),
    "歴史": ("史料で確認できる事実と伝承を分ける", "森町の歴史資料と文化財所管資料", "史料名、年代、地名、確認箇所"),
    "観光": ("移動・滞在・安全・営業確認を一日でつなぐ", "森町の観光情報と施設・交通の当事者情報", "訪問日、移動手段、同行者、帰路"),
    "食": ("産地・製造・販売・保存条件を表示から確かめる", "森町の産業情報と販売者の一次情報", "商品名、産地、製造者、保存条件"),
    "農業": ("品目・時期・生産者・圃場管理を分ける", "森町の農林業情報と県・国の所管資料", "品目、時期、所在地、管理者"),
    "統計資料": ("統計名・基準日・対象・単位を分ける", "森町の統計資料とe-Stat", "統計名、基準日、単位、対象地域"),
    "上下水道記録": ("水道・下水道・対象期間・使用量を分ける", "森町上下水道課の料金案内", "使用者、検針期間、使用量、請求区分"),
    "都市計画資料": ("図面・凡例・区域・対象地点を分ける", "森町の都市計画資料と国の制度案内", "対象地点、図面名、凡例、確認日"),
    "高齢者福祉": ("本人条件・家族状況・サービス内容を分ける", "森町地域包括支援センターと保健福祉課", "本人の年齢・状態、家族状況、希望する支援"),
}

# 検索意図の中心に期限・警戒段階・届出条件がある記事は、一般的な
# 「窓口で確認」だけで済ませない。所管官庁の公表内容を本文冒頭に置く。
CRITICAL_FACTS = {
    82: [
        "土砂災害警戒情報は、避難が必要となる警戒レベル4に相当する情報です。危険な場所にいる人は、森町の避難情報と気象庁の危険度分布を確認し、避難先まで安全に移動できるうちに行動します。",
        "高齢者や移動に時間がかかる人は、警戒レベル3の高齢者等避難を待たずに準備を始める場合もあります。家族の体調、夜間、道路状況を含めて早めに判断します。",
    ],
    131: [
        "相続で不動産を取得したことを知った相続人は、その事実を知った日から3年以内に相続登記を申請することが基本です。2024年4月1日より前の相続で未登記の不動産も対象となり、原則として2027年3月31日までの対応が必要です。",
        "遺産分割が成立した場合は、成立日から3年以内に、その内容を反映した登記を申請する追加の義務があります。個別の起算日や必要書類は、管轄法務局または司法書士へ確認します。",
    ],
    245: [
        "国土利用計画法の事後届出は、届出対象となる土地売買等の契約を結んだ日を含めて2週間以内が基本です。契約前ではなく、契約後の期限として日付を管理します。",
        "一般的な面積要件は、市街化区域2,000平方メートル以上、市街化区域を除く都市計画区域5,000平方メートル以上、都市計画区域外10,000平方メートル以上です。森町の対象区域と一団の土地の扱いは、契約前に県・町の担当窓口へ確認します。",
    ],
}

# Day2で一次資料を再調査した3件は、汎用の「資料整理」文ではなく、
# 各手続の判断順・成果物・期限に沿って説明する。各組の1段落目は
# 事実の意味、2段落目は読者が残す記録を扱い、公式事実と編集上の助言を混ぜない。
DAY2_SECTION_NOTES = {
    236: [
        (
            "境界確定の相手は、目の前にある道路の見た目ではなく、その土地を管理する主体で決まります。町道に見えても国・県管理の場合があるため、申請書を書き始める前に管理者を確かめます。",
            "家の台帳には、公共用地の種類、所在、管理者を確認した資料、確認日を一組で残します。道路・河川・水路のどれか分からない段階では、推測した名称を確定欄へ書きません。",
        ),
        (
            "公図と登記簿は、申請先を探す入口です。現地の舗装幅や側溝だけで所有・管理範囲を決めず、公図上の表示と登記名義を照合してから町へ相談します。",
            "公図の取得日、対象地番、前面に表示された土地の表記をメモします。図面の切り抜きだけを保存せず、方位・縮尺・周辺地番が分かる範囲も残すと再確認しやすくなります。",
        ),
        (
            "森町公式ページが対象としているのは、町が管理する道路、河川、水路、その他の町有地と民有地との境界です。国道や県管理地の一般手順を、そのまま森町の申請方法として扱うことはできません。",
            "用地係へ伝える内容は、申請地、隣接する公共用地、境界確定の目的、手元にある図面です。相談日時と回答の要点も台帳へ追記し、後の立会準備へつなげます。",
        ),
        (
            "様式第1号は案件の起点になります。申請地と申請目的が後の図面・立会記録と一致するよう、通称ではなく登記や公式資料で確認した表記を使います。",
            "提出版の写しには提出日と添付図書名を記録します。差し替えがあった場合は旧版を黙って上書きせず、差し替え理由と新旧の対応が分かるようにします。",
        ),
        (
            "隣接所有者一覧は、現地で隣に見える人を並べるメモではありません。対象地周辺の登記情報を基に、立会や協議に関係する所有者を確認するための書類です。",
            "氏名や住所を含む一覧は公開用資料と分けて保管します。登記を確認した日と、一覧へ転記した日を残し、後に所有関係が変わったとき再確認できるようにします。",
        ),
        (
            "代理人へ依頼する場合でも、何を委任したかを申請者が追える状態にします。委任状、申請書、代理人から受け取った図面の案件名をそろえることが重要です。",
            "委任状の写しと連絡履歴を同じファイルへ入れ、測量、日程調整、図面作成のどこまでを依頼したかを別紙にまとめます。口頭だけの役割分担を残さないようにします。",
        ),
        (
            "既存の境界確定図や道路台帳資料と現地測量は役割が異なります。国管理道路の手順は両者を比較する図面を求めており、既存資料だけでも現地の杭だけでも確定できないことを示しています。",
            "比較図を受け取ったら、基準点、測点、使用した既存資料名を確認します。家族向けの簡略図を作る場合も、正式な境界確定図と見分けられる名称を付けます。",
        ),
        (
            "現地立会者一覧は、誰がどの立場で立ち会ったかを後からたどる記録です。出席者の記憶だけに頼らず、申請者、代理人、隣接者、管理者を区別します。",
            "立会日、参加区分、当日確認した図面、持ち帰った宿題を一枚にまとめます。合意前の提案線を確定線のように色付けして家族へ渡さないよう注意します。",
        ),
        (
            "コンクリート杭、金属プレート、舗装止めブロックは、存在するだけで財産境界を証明するものではありません。工事などで移動している可能性もあるため、管理資料と測量結果を優先します。",
            "現地写真には撮影日、方向、写っている標識の種類を付けます。写真上の印を正式な境界線と断定せず、確定図の測点と対応できたものだけを確認済みにします。",
        ),
        (
            "境界は一方的な許可ではなく、関係者の協議を経て確定します。立会時の説明、修正後の線、最終図面が同じ内容かを確認してから成果物として保管します。",
            "境界確定図には受領日と発行・確認主体を記録し、測量図や立会メモと一緒に綴じます。家族が売買や工事で使うとき、途中案を取り出さない配置にします。",
        ),
        (
            "里道や水路の公共機能がなくなった場合の用途廃止は、境界確定とは別の手続です。境界が分かったことだけで払い下げが決まったと受け取らないようにします。",
            "用途廃止を相談した案件は、事前調査、本申請、普通財産の相談を境界ファイルから分けます。境界確定・測量・契約・登記などの費用負担も別表で管理します。",
        ),
        (
            "この台帳の目的は、確定図だけを保存することではなく、どの管理者と、どの資料を使い、誰が立ち会って確定したかを再現できる状態にすることです。",
            "最後に申請書、隣接所有者一覧、委任状、立会者一覧、確定図、連絡履歴の有無を点検します。不足書類は『なし』と決めず、未受領か不要かを区別します。",
        ),
    ],
    243: [
        (
            "最初に、新築・増改築・外観変更・工作物・開発行為のどれに当たるかを分けます。行為種別が違えば、確認する規模や着手の考え方も変わります。",
            "工事台帳の一行目に、行為種別、対象部分、計画日、設計担当を記録します。まだ決まっていない項目は空欄にせず、確定予定日を置きます。",
        ),
        (
            "建築確認や開発許可などが必要な工事は、その申請等の30日前が景観届出期限です。それらが不要な外観変更などは、行為着手の30日前が基準になります。",
            "確認申請等の予定日と工事着手予定日を別の列へ置き、どちらを起点にしたか明記します。二つの日付を混ぜると、届出準備の開始日を誤ります。",
        ),
        (
            "高さ、延べ面積、増改築部分、見付面積は別の判定値です。高さ10メートル、延べ面積1,000平方メートル、増改築部分10平方メートル、見付面積2分の1という条件を一つにまとめません。",
            "設計図から転記した数値には図面番号と版を付けます。設計変更で数値が変わったら旧値を消さず、どの届出版に対応するかを残します。",
        ),
        (
            "土地の造成などの開発行為は、都市計画法の開発許可が不要でも1,000平方メートル以上なら景観届出が必要となる可能性があります。許可不要と届出不要は同義ではありません。",
            "開発面積は建築面積と別欄にし、切土・盛土を始める予定日も記録します。建築の詳細が未定なら、開発と建築を分けて届けるか町へ相談します。",
        ),
        (
            "町は構想・計画の早い段階での相談を案内しています。届出後の変更は調整が難しくなるため、30日前を提出日ではなく最終準備期限として使うと安全です。",
            "工程表には事前相談、図書作成、社内・家族確認、提出、着手を並べます。相談で修正を求められた場合に備え、提出直前まで設計を固定しない進め方は避けます。",
        ),
        (
            "当初届は様式第2号と添付図書を正副各1部、計2部用意します。適合通知は、書類に不備がなく景観形成基準に適合した場合に交付されます。",
            "提出控えには提出日、受領された図面版、適合通知の受領日を記録します。届出を出した事実と、基準への適合が確認された事実を同じ欄にしません。",
        ),
        (
            "近景写真は敷地の状況を確認するため、周辺道路などから撮影します。建物だけを大きく写すのではなく、対象部分と敷地の関係が読める構図にします。",
            "撮影位置を配置図へ落とし、方向、撮影日、ファイル名を対応させます。完了写真と比べる基準写真は、加工前の元データも保管します。",
        ),
        (
            "遠景写真は、少し離れた場所から周辺景観との関係を示す資料です。私有地へ無断で入らず、公道や利用可能な場所から対象が分かる位置を選びます。",
            "近景と遠景を同じ名称で保存せず、撮影地点番号を分けます。稜線、周辺建物、道路方向など、審査で周辺との調和を読む要素が画面内にあるか確認します。",
        ),
        (
            "外部仕上げ表には、屋根・壁など部分ごとの仕上げ方法、マンセル値、面積を記載します。アクセント色がある場合は、その割合も必要です。",
            "材料見本、立面図、仕上げ表で名称と色番号を統一します。似た色という感覚的な説明だけでなく、届出版と発注仕様の対応を残します。",
        ),
        (
            "景観形成基準に関わる変更は、様式第3号と変更部分の添付図書で事前に届けます。着手前か着手後かで、30日間の制限がかかる範囲も変わります。",
            "変更台帳には変更理由、対象箇所、新旧図面、変更届提出日を記録します。施工者へは口頭変更だけで進めず、届出済み版を共有します。",
        ),
        (
            "完了写真は、届け出た行為が完了したことを示す資料です。着手前と同じ撮影位置・方向を使えば、届出内容との対応を確認しやすくなります。",
            "天候や駐車車両で同じ構図が撮れない場合は、理由と代替位置を残します。見栄えを整える加工より、対象部分が確認できる元写真を優先します。",
        ),
        (
            "工事が完了したら、完了日から14日以内に様式第4号と完了写真を提出します。基本的に完了検査は行わない案内ですが、必要に応じて現地確認があります。",
            "台帳の最後に完了日、写真撮影日、完了届提出日を別々に記録します。当初届、変更届、適合通知、完了届を同じ案件番号で束ねて手続を閉じます。",
        ),
    ],
    245: [
        (
            "届出期限は土地売買等の契約締結日から動き始めます。面積確認や様式選びを契約後に始めると2週間を圧迫するため、契約前に判定材料をそろえます。",
            "契約書を受け取ったら、契約締結日、対象筆、取得者、提出期限を一枚へ転記します。引渡日や代金支払日を期限の起点にしないよう欄を分けます。",
        ),
        (
            "届出者は土地の権利を取得する側です。売買では買主、権利金を伴う賃貸借などでは借主が該当し得るため、契約上の立場を先に確認します。",
            "共有で取得する場合は共有者一覧の要否も確認します。届出担当者と権利取得者を同一視せず、代理提出なら連絡先と役割を記録します。",
        ),
        (
            "森町では都市計画区域内と区域外で面積基準が異なります。町の都市計画図は概略資料なので、境界付近や判断が難しい土地は役場で区域を確認します。",
            "台帳には区域名、確認に使った図面、役場へ確認した日を残します。住所だけで区域を推測せず、複数筆が別区域にまたがる場合も個別に整理します。",
        ),
        (
            "森町公式案内では、都市計画区域内は5,000平方メートル以上、区域外は10,000平方メートル以上が基準です。県の一般表にある市街化区域2,000平方メートルという区分を、森町に存在すると決めつけません。",
            "各筆の面積、区域、適用した基準を同じ表へ置きます。区域が二つにまたがる場合の基準は県案内を確認し、最終判断を町の担当へ照会します。",
        ),
        (
            "一筆ずつが基準未満でも、同じ取得者が一連の計画で取得する一団の土地は合計して判定します。契約を分けたことだけで対象外になるとは限りません。",
            "隣接性、取得時期、利用目的、取得者を筆一覧へ記録します。一団か判断に迷う計画は、契約前に全筆を示して町・県へ確認します。",
        ),
        (
            "対象となり得るのは売買だけではありません。交換、共有持分、営業譲渡、譲渡担保、地上権・賃借権、予約完結権、信託受益権、地位の譲渡なども確認対象です。",
            "契約書の表題だけで対象外と判断せず、移転する権利、対価、権利金の有無を整理します。判断根拠にした公式資料と照会結果を契約ファイルへ残します。",
        ),
        (
            "期限は契約締結日から2週間以内です。県案内では契約締結日を含めて数え、土地が所在する市町の窓口へ提出するよう示しています。",
            "カレンダーには契約日、14日目、提出予定日を記載します。郵送や書類補正の時間を考え、14日目を作業開始日にしない日程を組みます。",
        ),
        (
            "2週間目の日が土日・祝日など行政機関の休日なら、次の開庁日が期限になります。これは期限の延長を自由に選べるという意味ではありません。",
            "休日補正前の日付と実際の期限を両方残します。年末年始など開庁日が分かりにくい時期は、町の開庁案内も確認します。",
        ),
        (
            "2026年4月1日以降に提出する場合は新様式が必要です。契約日が3月31日以前でも、提出日が4月1日以降なら新様式を使います。",
            "様式ファイルには取得日と適用開始日を付けます。前年に保存した様式を複製せず、提出直前に森町公式ページから現行版を確認します。",
        ),
        (
            "森町は本紙に収まらない筆の一覧、共有者一覧、海外居住者用の別紙を用意しています。該当条件を確認して必要な別紙を本紙と一緒に管理します。",
            "筆番号、共有者、国外住所を本紙と別紙で照合し、記載漏れや表記揺れを点検します。別紙だけを送付・保存して本紙との関係が分からなくならないようにします。",
        ),
        (
            "静岡県の案内では届出書は2部、受付控えを希望する場合は3部です。提出方法ごとの扱いは、実行前に森町の窓口へ確認します。",
            "提出用、行政保管用、受付控えのどれかを表紙に明記します。控えを受け取ったら受付日が読める状態で契約書と一緒に保存します。",
        ),
        (
            "手続後の記録は、期限内に提出したことだけでなく、どの土地・契約・様式版について届けたかを再現できる必要があります。",
            "契約書、区域確認、面積表、本紙、別紙、添付書類、受付控えを一案件にまとめます。後の照会に備え、未確認事項と町へ質問した内容も残します。",
        ),
    ],
}

# URLの存在確認や編集手順は、出典付きであっても主題そのものの事実ではない。
# enrichmentを本文へ渡す前に除外し、件数だけを満たす疑似的な項目を防ぐ。
PSEUDO_FACT_MARKERS = (
    "判断する中心は",
    "判断を分ける確認項目",
    "一次情報として実在する",
    "も実在し、",
    "第3の確認先になる",
    "HTTP 200",
    "確認対象は、",
    "資料の更新日と混同せず",
    "だけから断定できないため",
    "という問いに答えるには",
    "制度・分類の上位枠は",
    "法定期限・募集期限・受付期間は制度ごとに異なる",
    "最初の窓口候補は",
    "別欄で照合し、確認日と未確認事項を記録",
    "公式資料で確定できる範囲と、資料だけでは確定できない範囲",
)

SECTION_HEADINGS = [
    "この問いで最初に決めること", "一次情報から確定できる範囲", "森町で条件が変わるポイント",
    "資料を集める順番", "現地または窓口で確認すること", "期限と実行日の組み立て方",
    "費用と見えにくい負担", "家族・関係者との共有", "判断を急がないための代案",
    "記録を次の人へ残す", "大石の視点", "まとめと次の一歩",
]

def e(value: object) -> str:
    return escape(str(value), quote=True)

def canonical_url(row: dict) -> str:
    slug = row["slug"].strip()
    if slug.startswith("/"):
        return "/" + slug.strip("/") + "/"
    base = CATEGORY_PATH.get(row["category"], "/guide/")
    return base + slug.strip("/") + "/"

def visible_chars(html: str) -> int:
    text = re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", "", html, flags=re.S)
    return len(re.sub(r"\s+", "", text))

def editorial_chars(html: str) -> int:
    match = re.search(r'<article class="post-editorial-body">(.*?)</article>', html, re.S)
    return visible_chars(match.group(1)) if match else 0

def substantive_facts(row: dict) -> list[dict]:
    """主題の実内容と出典URLを持つ事実だけを返す。"""
    accepted = []
    source_urls = {str(item.get("url", "")) for item in row.get("sources", [])}
    for item in row.get("verified_facts", []):
        if not isinstance(item, dict):
            continue
        statement = str(item.get("statement", "")).strip()
        source_url = str(item.get("source_url", "")).strip()
        if not statement or len(statement) < 25:
            continue
        if not source_url.startswith("https://") or source_url not in source_urls:
            continue
        if any(marker in statement for marker in PSEUDO_FACT_MARKERS):
            continue
        accepted.append(item)
    return accepted

def load_rows() -> list[dict]:
    rows = json.loads(TOPICS.read_text(encoding="utf-8"))
    enrichments: dict[int, dict] = {}
    for path in ENRICHMENT_FILES:
        if not path.exists():
            raise RuntimeError(f"公開用固有データがありません: {path.name}")
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("records") or data.get("topics") or data.get("items") or []
        for item in data:
            enrichments[int(item["id"])] = item
    if set(enrichments) != set(range(1, 301)):
        missing = sorted(set(range(1, 301)) - set(enrichments))
        raise RuntimeError(f"固有データが300件そろっていません: missing={missing[:10]}")
    merged = []
    for row in rows:
        item = {**row, **enrichments[int(row["id"])]}
        for key, minimum in {"verified_facts": 6, "morimachi_conditions": 3, "section_headings": 12, "faqs": 4, "sources": 3}.items():
            if len(item.get(key, [])) < minimum:
                raise RuntimeError(f"ID{row['id']} {key} が{minimum}件未満です")
        # 未承認ページはnoindexの下書きとして生成を続ける。本文には疑似的な
        # 項目を出さず、公開候補へ移す時点で ensure_release_quality が止める。
        item["all_verified_facts"] = list(item["verified_facts"])
        item["verified_facts"] = substantive_facts(item)
        item["substantive_fact_count"] = len(item["verified_facts"])
        merged.append(item)
    return merged


def parse_ids(value: str | None, valid_ids: set[int]) -> set[int]:
    """Parse a comma-separated ID/range list such as ``1,4,10-12``."""
    if value is None:
        return set(valid_ids)
    selected: set[int] = set()
    for token in value.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            left, right = token.split("-", 1)
            start, end = int(left), int(right)
            if start > end:
                raise ValueError(f"ID範囲が逆順です: {token}")
            selected.update(range(start, end + 1))
        else:
            selected.add(int(token))
    if not selected:
        raise ValueError("--ids に1件以上のIDを指定してください")
    unknown = selected - valid_ids
    if unknown:
        raise ValueError(f"存在しない第4期IDです: {sorted(unknown)}")
    return selected

def category_context(category: str) -> tuple[str, str, str]:
    return CATEGORY_CONTEXT.get(category, ("対象・時点・担当者・根拠を分ける", "森町と所管機関の一次情報", "対象地、目的、時期、確認資料"))

def topic_details(row: dict) -> list[str]:
    """タイトル・検索意図・構成案から、その記事だけの確認項目を取り出す。"""
    title_parts = [part.strip() for part in str(row["title"]).split("｜") if part.strip()]
    intent_parts = [part.strip() for part in re.split(r"[、，。]|または|そのうえで", str(row["search_intent"])) if len(part.strip()) >= 5]
    blueprint = row.get("required_sections") or row.get("content_blueprint") or []
    candidates = title_parts + intent_parts + list(blueprint) + list(row.get("section_headings", []))
    unique = []
    for value in candidates:
        value = re.sub(r"^森町で", "", str(value)).strip(" 「」。")
        if 5 <= len(value) <= 80 and value not in unique:
            unique.append(value)
    return unique or [str(row["title"]).split("｜", 1)[0]]

def paragraph_set(row: dict, section: int) -> list[str]:
    title, intent, category = row["title"], row["search_intent"], row["category"]
    method, authorities, memo = category_context(category)
    risk = str(row.get("risk", "medium")).lower()
    sets = [
        [
            f"{title}で最初に行うのは、検索結果を増やすことではなく、何を決めるための確認かを一文にすることです。このページでは「{intent}」という迷いを扱います。対象、時点、利用者が変われば答えも変わるため、条件を書かずに結論だけを持ち帰らないでください。",
            f"基本の順序は、{method}ことです。森町の案内だけで完結する事項と、県・国・施設・所有者など別の確認先が必要な事項を分けます。一つの窓口で全部決まると思わないことが、手戻りを減らします。",
            f"手元のメモには「今日確定したいこと」「実行直前に再確認すること」「専門判断が必要なこと」の三欄を作ります。{memo}を最初に書けば、問い合わせ時に説明が短くなり、担当者も対象を絞りやすくなります。",
            f"このテーマのリスク区分は{risk}として扱います。これは不安を煽る表示ではなく、古い案内や個別条件を一般化しないための編集上の印です。分からない項目は推測で埋めず、未確認と記録します。",
        ],
        [
            f"一次情報は{authorities}を起点にします。資料が説明している対象者、適用日、場所、担当部署を確認し、ページの更新日だけで新しさを判断しません。制度や行事では、公開日と実施年度が異なる場合があります。",
            "第一の公式資料は、ページ名、確認日、該当する見出しを一緒に残します。PDFならページ番号と注記、表なら単位と対象期間も記録し、数字だけを切り離さないでください。",
            "第二の公式資料は、一件目と対象範囲や管理主体が同じかを確かめます。食い違いがあれば新しい方へ自動的に寄せず、定義と適用範囲を比べます。",
            f"検索結果の要約、個人ブログ、地図の口コミは確認の入口にはなりますが、最終根拠にはしません。{title}について実行日が決まったら、掲載した一次情報をもう一度開き、現在も同じ条件かを確かめます。",
        ],
        [
            f"森町は中心市街地、天浜線沿線、平地の集落、天方・三倉の山間部で、距離と移動の感じ方が異なります。町全体の説明が正しくても、対象地点の道路、標高差、通信、周辺施設まで同じとは限りません。",
            f"住所が分かる場合は地図上の一点だけでなく、入口、接道、最寄りの公共施設、避難経路、帰路を一緒に見ます。住所が未確定なら地区名と目的地を分け、同名施設や旧地名との取り違えを防ぎます。",
            f"曜日と時間帯も条件です。窓口、交通、行事、医療、買物、農作業は平日と休日、朝と夕方で利用状況が変わります。一度の訪問や一枚の写真を、年間を通じた状態として一般化しません。",
            f"山、川、農地、社寺、住宅地では、公開情報だけで見えない管理の都合があります。私有地や作業場所へ入らず、地域の生活と安全を妨げない範囲で確認することを、情報収集の前提にします。",
        ],
        [
            f"資料は、本人・対象を特定するもの、現在の状態を示すもの、期限を示すもの、権利や利用条件を示すものに分けます。全部を一つの封筒へ入れるより、何を証明する資料か付箋を付ける方が不足を見つけやすくなります。",
            f"{memo}を一覧にし、原本が必要か、写しでよいか、発行からの期限があるかを確認します。まだ取得しない資料も「取得先」「必要になる場面」「費用」を書いておくと、家族が代わって動くときに迷いません。",
            f"オンラインで取得した資料はファイル名へ日付と資料名を入れます。紙の資料は該当箇所へ印を付けます。個人番号、医療情報、登記識別情報などを家族共有の一般フォルダへ無防備に置かないでください。",
            f"不足資料があるときは、推定値で話を進めず、どの判断までなら保留のまま進められるかを確認します。{title}の目的は書類を集めきることではなく、次の安全な判断に必要な根拠をそろえることです。",
        ],
        [
            f"窓口や当事者へ問い合わせるときは、{intent}とだけ伝えるのではなく、対象地点、希望時期、すでに見た資料、今日知りたい範囲を伝えます。担当外なら次の窓口名と、引継ぎに必要な説明を聞きます。",
            f"現地では安全、利用条件、周辺動線の三点を優先します。写真には確認日と撮影方向を残し、人物、表札、車両番号、生活状況など個人を特定できる情報を公開しないようにします。",
            f"看板や掲示がウェブ案内と違う場合は、その場で都合よく解釈しません。掲示の対象期間と管理者を確認し、必要なら双方の資料名を示して問い合わせます。現地情報も確認日の記録がなければ再利用できません。",
            f"危険、医療、税、法務、構造、安全性など資格や所管判断が必要な事項は、このページで結論を出しません。事実関係を整理し、専門家や担当機関へ相談するための準備として使います。",
        ],
        [
            f"期限は、申請・予約の締切、資料の有効期間、実施日、支払日、見直し日へ分けます。一つの日付だけをカレンダーへ入れると、前提資料が間に合わないため、準備開始日も設定します。",
            f"{title}を実行する日から逆算し、二週間前、一週間前、前日、当日に確認する事項を置きます。変動しやすい運行、天候、在庫、受付、行事情報は直前確認へ回し、早い段階で断定しません。",
            f"役場、事業者、家族、専門家の返答待ちがある場合は、相手の回答期限ではなく、自分が次の判断をする期限を決めます。返答がなければ保留するのか、別案へ切り替えるのかも先に共有します。",
            f"年度をまたぐ情報は特に注意します。前年の対象者、金額、日程、受付方法を翌年へそのまま当てはめず、当年版の資料が出た時点で差分を確認してください。",
        ],
        [
            f"費用は窓口で支払う金額だけではありません。交通、郵送、証明取得、専門相談、修繕、管理、休業時間、家族の移動などを別々に書き、分からない項目をゼロ円にしないことが大切です。",
            f"見積りが必要な項目は、対象範囲と前提条件をそろえて依頼します。安い・高いという評価より、何を含み何を含まないかを比較します。追加作業が起こる条件も質問してください。",
            f"公的な支援や減免が見つかっても、対象要件、申請時期、着手前申請の有無を確認します。利用できる可能性と、今回実際に利用できることを同じ文章にしません。",
            f"お金をかけない代案にも時間と管理責任があります。先送り、家族対応、自主管理を選ぶなら、誰がいつまで担当し、できなくなったときにどう切り替えるかを決めます。",
        ],
        [
            f"家族や共有者がいる場合、情報を集める人と決定できる人は同じとは限りません。連絡役だけが結論を背負わないよう、選択肢、根拠、費用、未確認事項を一枚で共有します。",
            f"話合いでは賛成・反対を先に聞かず、事実、希望、困りごと、保留条件の順に整理します。{intent}という目的へ戻り、何が分かれば次へ進めるかを各人から確認します。",
            f"遠方の家族には写真だけでなく、住所、地図、資料名、確認日を送ります。写真の印象だけで安全性や管理状態を判断しないよう、撮影していない範囲と未確認事項も添えます。",
            f"本人の意思確認が必要なテーマでは、家族の都合で結論を置き換えません。支援が必要な場合も、本人が理解し選べる情報量と順序を整え、必要に応じて公的相談先へつなぎます。",
        ],
        [
            f"結論を急がないため、実行する案、条件が整えば実行する案、今回は見送る案の三つを残します。二択にすると、未確認事項が多い段階で無理な判断をしやすくなります。",
            f"最小の一歩は、資料一件を確認する、対象地点を地図に記す、担当窓口を確認する、家族一人へ共有する、のいずれかで十分です。大きな契約や申請を最初の行動にしません。",
            f"目的そのものを見直すことも代案です。{title}で本当に解決したいのが時間、費用、安全、家族負担のどれかを確認すれば、別の制度や方法が合う場合があります。",
            f"保留を選ぶ場合も、再確認日と保留理由を残します。何もしない状態と、根拠を持って待つ状態は違います。更新情報が出たときに再開できる形へ整えてください。",
        ],
        [
            f"記録には、対象、確認日、確認者、資料名、分かったこと、未確認事項、次の担当を残します。結論だけでは、前提が変わったときにどこから見直すか分かりません。",
            f"住所と地番、通称と正式名称、年度と暦年など、似ているが役割の違う情報を同じ欄へ入れないでください。元資料の表記を保存し、家族向けの説明を別欄に書きます。",
            f"更新した資料は古い版を黙って上書きせず、確認日の違いが分かるようにします。不要になった個人情報は適切に破棄し、共有範囲も定期的に見直します。",
            f"次の人が同じ問い合わせを繰り返さずに済む記録が理想です。担当者の個人名を必要以上に共有せず、部署名、公式連絡先、回答の要点と確認日を残します。",
        ],
        [
            f"私は小さな不動産業者として、{title}のような相談でも、いきなり売却や契約の話へ進めるべきではないと考えます。対象、道路、境界、名義、農地、維持負担など関係する事実を先に分ける方が、家族の選択肢を守れます。",
            f"森町では地図上の近さだけでなく、道路幅、坂、川、山、鉄道、地域の管理との関係が判断に影響します。私は現地を見ていない事項を体験談のように語らず、確認が必要な条件として明示します。",
            f"まだ決めていない人に必要なのは、結論を迫る言葉より、何が分かれば決められるかを整理する道具です。査定額や制度名だけを先に置かず、家族が引き継げる記録を作ることを勧めます。",
            f"良い選択は一つではありません。実行、管理継続、専門相談、時期を待つという案を同じ表で比べ、地域への配慮と所有者・利用者の現実的な負担を同時に見ます。",
        ],
        [
            f"{title}の結論は、{method}ことから始め、{authorities}で現在の条件を確認することです。一般記事は順序を整える道具であり、個別の可否を保証するものではありません。",
            f"今日できるのは、{memo}を書き出し、二つの一次情報の確認日を残すことです。そのうえで、現地・窓口・家族・専門家のうち、次に確認する相手を一人だけ決めます。",
            f"実行直前には期限、安全、権利・利用条件、費用、帰路または管理方法を再点検します。どれかが未確認なら、結論を急がず代案へ戻れるようにしてください。",
            f"このページを家族へ送る場合は、ページURLだけでなく、自分たちの対象地点、希望時期、保留事項を短く添えます。同じ情報を読んでも前提が違えば判断が変わることを共有して終えます。",
        ],
    ]
    return sets[section]

def svg(row: dict, index: int) -> str:
    seed = int(row["id"]) * 31 + index * 17
    rng = random.Random(seed)
    palettes = [("#173f36", "#dcefe5", "#d49a3a"), ("#283f66", "#e2ebf7", "#b75d43"), ("#5a3827", "#f4e4c8", "#4f7b57")]
    dark, pale, accent = palettes[seed % len(palettes)]
    ridge = " ".join(f"{x},{rng.randint(120,250)}" for x in range(0, 1001, 100))
    motif = row["category"][:4]
    decorations = "".join(
        f'<circle cx="{110+n*67}" cy="{180+(n%3)*42}" r="{12+(n%4)*3}" fill="{accent}" opacity=".55"/>'
        for n in range(1 + (int(row["id"]) + index) % 11)
    )
    scene_kind = (int(row["id"]) + index) % 6
    scenes = [
        f'<g data-scene="document"><rect x="360" y="250" width="260" height="180" rx="18" fill="#fff" stroke="{dark}" stroke-width="8"/><path d="M395 305h190M395 345h150M395 385h175" stroke="{dark}" stroke-width="10" opacity=".55"/></g>',
        f'<g data-scene="home"><path d="M350 350 500 225l150 125v140H350Z" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="470" y="405" width="60" height="85" fill="{accent}"/></g>',
        f'<g data-scene="transport"><rect x="330" y="305" width="340" height="130" rx="34" fill="#fff" stroke="{dark}" stroke-width="9"/><circle cx="410" cy="455" r="32" fill="{accent}"/><circle cx="590" cy="455" r="32" fill="{accent}"/></g>',
        f'<g data-scene="people"><circle cx="430" cy="290" r="42" fill="{accent}"/><circle cx="570" cy="290" r="42" fill="#fff" stroke="{dark}" stroke-width="8"/><path d="M355 475q75-155 150 0M495 475q75-155 150 0" fill="none" stroke="{dark}" stroke-width="18"/></g>',
        f'<g data-scene="land"><path d="M285 460 390 270l110 105 105-155 120 240Z" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M500 375v100" stroke="{accent}" stroke-width="18"/></g>',
        f'<g data-scene="culture"><path d="M350 470V320h300v150M320 320h360L500 205Z" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M430 470V365h140v105" fill="{accent}"/></g>',
    ]
    # 公開監査済みのDay5記事は、主題を一目で識別できる固有モチーフを使う。
    special_scenes = {
        81: [
            f'<g data-scene="wildfire-two-sheet-ledger"><path d="M120 455 270 255l105 125 120-175 115 175 120-125 150 200Z" fill="{pale}" stroke="{dark}" stroke-width="9"/><rect x="155" y="245" width="265" height="210" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><rect x="580" y="245" width="265" height="210" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M195 310h185M195 365h185M620 310h185M620 365h185" stroke="{accent}" stroke-width="9"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="287" y="285">火を使う前</text><text x="287" y="410">許可・届出・発令</text><text x="712" y="285">煙を見た後</text><text x="712" y="410">安全・119番・場所</text></g></g>',
            f'<g data-scene="wildfire-alert-cancel-field"><path d="M110 455 270 235l110 145 120-190 125 190 105-145 160 220Z" fill="{pale}" stroke="{dark}" stroke-width="10"/><path d="M500 215q-38 45 0 85q38-45 0-85M472 320q28-34 56 0q-28 34-56 0" fill="{accent}"/><path d="M330 430h340" stroke="{dark}" stroke-width="12"/><rect x="685" y="225" width="190" height="155" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M720 275h120M720 325h120" stroke="{accent}" stroke-width="9"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="500" y="475">風・乾燥・水・人数</text><text x="780" y="260">注意報</text><text x="780" y="355">中止連絡</text></g></g>',
            f'<g data-scene="wildfire-safe-119-location-route"><path d="M130 445 260 265l105 120 110-165 125 165 105-120 165 180Z" fill="{pale}" stroke="{dark}" stroke-width="10"/><circle cx="275" cy="365" r="48" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M275 315v100M225 365h100" stroke="{accent}" stroke-width="10"/><path d="M345 365h120M625 365h120" stroke="{accent}" stroke-width="13"/><rect x="465" y="285" width="160" height="160" rx="28" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M505 325q40 65 80 0M505 405q40-65 80 0" fill="none" stroke="{accent}" stroke-width="11"/><circle cx="785" cy="365" r="54" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M785 325v80M745 365h80" stroke="{accent}" stroke-width="10"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="275" y="470">安全な退避</text><text x="545" y="485">119番</text><text x="785" y="470">現在地と方向</text></g></g>',
        ],
        80: [
            f'<g data-scene="fire-alarm-room-ledger"><path d="M150 455h700M210 455V250h580v205M500 250v205M210 350h580" fill="#fff" stroke="{dark}" stroke-width="10"/><circle cx="350" cy="300" r="34" fill="{accent}"/><circle cx="650" cy="300" r="34" fill="{accent}"/><circle cx="350" cy="400" r="34" fill="#fff" stroke="{accent}" stroke-width="9"/><circle cx="650" cy="400" r="34" fill="#fff" stroke="{accent}" stroke-width="9"/><g font-family="sans-serif" font-size="17" font-weight="700" fill="{dark}" text-anchor="middle"><text x="350" y="307">A1</text><text x="650" y="307">A2</text><text x="350" y="407">S1</text><text x="650" y="407">K1</text><text x="500" y="500">部屋と機器を一行で対応</text></g></g>',
            f'<g data-scene="fire-alarm-test-and-age-check"><circle cx="300" cy="330" r="105" fill="#fff" stroke="{dark}" stroke-width="10"/><circle cx="300" cy="330" r="32" fill="{accent}"/><path d="M435 270q55 60 0 120M480 240q90 90 0 180" fill="none" stroke="{accent}" stroke-width="12"/><rect x="610" y="230" width="200" height="220" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M650 290h120M650 345h120M650 400h90" stroke="{accent}" stroke-width="9"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="300" y="480">点検ボタン</text><text x="710" y="270">製造年</text><text x="710" y="330">電源・方式</text><text x="710" y="385">十年目安</text></g></g>',
            f'<g data-scene="fire-alarm-replacement-support-route"><rect x="145" y="260" width="210" height="145" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><rect x="395" y="230" width="210" height="175" rx="18" fill="{pale}" stroke="{dark}" stroke-width="10"/><rect x="645" y="260" width="210" height="145" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M355 330h40M605 330h40" stroke="{accent}" stroke-width="13"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="250" y="305">部屋別台帳</text><text x="250" y="355">交換候補</text><text x="500" y="285">対象確認</text><text x="500" y="335">取付支援</text><text x="500" y="375">専門業者</text><text x="750" y="305">交換・作動</text><text x="750" y="355">履歴保存</text></g></g>',
        ],
        70: [
            f'<g data-scene="prenatal-nhi-tax-month-ledger"><rect x="135" y="235" width="730" height="245" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M135 310h730M360 235v245M640 235v245" stroke="{accent}" stroke-width="8"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="247" y="280">出産予定月</text><text x="500" y="280">単胎4か月</text><text x="752" y="280">多胎6か月</text><text x="247" y="385">届出資料</text><text x="500" y="385">対象月</text><text x="752" y="385">税額通知</text></g></g>',
            f'<g data-scene="single-multiple-exemption-months"><g fill="#fff" stroke="{dark}" stroke-width="7"><rect x="210" y="235" width="120" height="78" rx="12"/><rect x="340" y="235" width="120" height="78" rx="12"/><rect x="470" y="235" width="120" height="78" rx="12"/><rect x="600" y="235" width="120" height="78" rx="12"/></g><g fill="{pale}" stroke="{accent}" stroke-width="7"><rect x="80" y="375" width="120" height="78" rx="12"/><rect x="210" y="375" width="120" height="78" rx="12"/><rect x="340" y="375" width="120" height="78" rx="12"/><rect x="470" y="375" width="120" height="78" rx="12"/><rect x="600" y="375" width="120" height="78" rx="12"/><rect x="730" y="375" width="120" height="78" rx="12"/></g><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="140" y="285">単胎</text><text x="140" y="425">多胎</text><text x="400" y="345">予定月を中心に月単位で確認</text></g></g>',
            f'<g data-scene="notification-document-tax-notice-route"><rect x="110" y="250" width="190" height="155" rx="16" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="405" y="250" width="190" height="155" rx="16" fill="{pale}" stroke="{dark}" stroke-width="9"/><rect x="700" y="250" width="190" height="155" rx="16" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M300 327h105M595 327h105" stroke="{accent}" stroke-width="13"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="205" y="300">本人確認</text><text x="205" y="350">母子健康手帳</text><text x="500" y="300">届出・受付</text><text x="500" y="350">届出不要確認</text><text x="795" y="300">税額通知</text><text x="795" y="350">対象月照合</text></g></g>',
        ],
        60: [
            f'<g data-scene="funeral-benefit-claim-ledger"><rect x="135" y="235" width="730" height="245" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M135 310h730M330 235v245M525 235v245M700 235v245" stroke="{accent}" stroke-width="8"/><g font-family="sans-serif" font-size="17" font-weight="700" fill="{dark}" text-anchor="middle"><text x="232" y="280">亡くなった人</text><text x="427" y="280">葬祭を行った人</text><text x="612" y="280">請求書</text><text x="782" y="280">受付・入金</text><text x="232" y="390">国保資格</text><text x="427" y="390">請求者確認</text><text x="612" y="390">様式1の2</text><text x="782" y="390">状態更新</text></g></g>',
            f'<g data-scene="funeral-performer-claimant-roles"><circle cx="500" cy="335" r="62" fill="{pale}" stroke="{dark}" stroke-width="10"/><rect x="105" y="245" width="195" height="105" rx="16" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="105" y="395" width="195" height="105" rx="16" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="700" y="245" width="195" height="105" rx="16" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="700" y="395" width="195" height="105" rx="16" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M300 300 438 330M300 445 450 370M562 330 700 300M550 370 700 445" stroke="{accent}" stroke-width="11"/><g font-family="sans-serif" font-size="17" font-weight="700" fill="{dark}" text-anchor="middle"><text x="202" y="310">葬祭を行った人</text><text x="202" y="460">問い合わせる人</text><text x="500" y="342">町へ確認</text><text x="797" y="310">請求書の人</text><text x="797" y="460">口座名義人</text></g></g>',
            f'<g data-scene="claim-receipt-payment-stages"><rect x="95" y="270" width="140" height="115" rx="14" fill="#fff" stroke="{dark}" stroke-width="8"/><rect x="260" y="270" width="140" height="115" rx="14" fill="{pale}" stroke="{dark}" stroke-width="8"/><rect x="425" y="270" width="140" height="115" rx="14" fill="#fff" stroke="{dark}" stroke-width="8"/><rect x="590" y="270" width="140" height="115" rx="14" fill="{pale}" stroke="{dark}" stroke-width="8"/><rect x="755" y="270" width="140" height="115" rx="14" fill="#fff" stroke="{dark}" stroke-width="8"/><path d="M235 327h25M400 327h25M565 327h25M730 327h25" stroke="{accent}" stroke-width="12"/><g font-family="sans-serif" font-size="17" font-weight="700" fill="{dark}" text-anchor="middle"><text x="165" y="335">様式取得</text><text x="330" y="335">資料確認</text><text x="495" y="335">提出</text><text x="660" y="335">受付・決定</text><text x="825" y="335">入金確認</text></g></g>',
        ],
        64: [
            f'<g data-scene="medical-expense-claim-packet"><rect x="105" y="235" width="790" height="250" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M105 315h790M300 235v250M500 235v250M700 235v250" stroke="{accent}" stroke-width="8"/><g font-family="sans-serif" font-size="17" font-weight="700" fill="{dark}" text-anchor="middle"><text x="202" y="285">支払理由</text><text x="400" y="285">専用証明</text><text x="600" y="285">資格・口座</text><text x="797" y="285">受付・決定</text><text x="202" y="405">一件を選ぶ</text><text x="400" y="405">資料名を照合</text><text x="600" y="405">共通欄</text><text x="797" y="405">状態更新</text></g></g>',
            f'<g data-scene="five-payment-reason-document-branches"><rect x="405" y="210" width="190" height="95" rx="16" fill="{pale}" stroke="{dark}" stroke-width="9"/><g fill="#fff" stroke="{dark}" stroke-width="7"><rect x="55" y="385" width="155" height="85" rx="13"/><rect x="235" y="385" width="155" height="85" rx="13"/><rect x="415" y="385" width="155" height="85" rx="13"/><rect x="595" y="385" width="155" height="85" rx="13"/><rect x="775" y="385" width="155" height="85" rx="13"/></g><path d="M500 305v45M500 350H132v35M500 350H312v35M500 350v35M500 350h172v35M500 350h352v35" fill="none" stroke="{accent}" stroke-width="9"/><g font-family="sans-serif" font-size="15" font-weight="700" fill="{dark}" text-anchor="middle"><text x="500" y="268">全額支払の理由</text><text x="132" y="435">資格未提示</text><text x="312" y="435">柔道整復</text><text x="492" y="435">はり等</text><text x="672" y="435">治療用装具</text><text x="852" y="435">生血代</text></g></g>',
            f'<g data-scene="receipt-review-payment-status-route"><g fill="#fff" stroke="{dark}" stroke-width="8"><rect x="70" y="280" width="145" height="115" rx="14"/><rect x="250" y="280" width="145" height="115" rx="14"/><rect x="430" y="280" width="145" height="115" rx="14"/><rect x="610" y="280" width="145" height="115" rx="14"/><rect x="790" y="280" width="145" height="115" rx="14"/></g><path d="M215 337h35M395 337h35M575 337h35M755 337h35" stroke="{accent}" stroke-width="12"/><g font-family="sans-serif" font-size="16" font-weight="700" fill="{dark}" text-anchor="middle"><text x="142" y="345">資料確認</text><text x="322" y="345">提出・受付</text><text x="502" y="345">追加照会</text><text x="682" y="345">支給決定</text><text x="862" y="345">入金照合</text></g></g>',
        ],
        65: [
            f'<g data-scene="third-party-accident-four-contact-lines"><path d="M120 455 290 245l120 155 100-180 120 180 115-140 135 195Z" fill="{pale}" stroke="{dark}" stroke-width="9"/><circle cx="500" cy="340" r="54" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M475 330h50m-25-25v50M455 375l-42 38m132-38 42 38M455 305l-45-45m135 45 45-45" stroke="{accent}" stroke-width="11"/><rect x="155" y="210" width="145" height="75" rx="14" fill="#fff" stroke="{dark}" stroke-width="8"/><rect x="700" y="210" width="145" height="75" rx="14" fill="#fff" stroke="{dark}" stroke-width="8"/><g font-family="sans-serif" font-size="17" font-weight="700" fill="{dark}" text-anchor="middle"><text x="227" y="257">警察</text><text x="772" y="257">森町国保</text><text x="500" y="430">事故地点</text></g></g>',
            f'<g data-scene="accident-police-town-document-desk"><path d="M140 420h720M210 420V275h170v145M620 420V275h170v145" fill="none" stroke="{dark}" stroke-width="10"/><path d="M210 275l85-70 85 70M620 275l85-70 85 70" fill="{pale}" stroke="{dark}" stroke-width="9"/><rect x="405" y="235" width="190" height="225" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M435 285h130M435 330h130M435 375h105" stroke="{accent}" stroke-width="8"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="295" y="455">警察</text><text x="500" y="500">傷病届</text><text x="705" y="455">森町役場</text></g></g>',
            f'<g data-scene="settlement-stopline-claim-route"><path d="M120 365h760" stroke="{dark}" stroke-width="18"/><path d="M250 315v100M500 285v160M750 315v100" stroke="{accent}" stroke-width="13"/><rect x="415" y="210" width="170" height="95" rx="16" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M455 235 545 280M545 235l-90 45" stroke="#b0443c" stroke-width="12"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="250" y="460">治療・届出</text><text x="500" y="485">示談前相談</text><text x="750" y="460">相手方請求</text></g></g>',
        ],
        57: [
            f'<g data-scene="high-cost-medical-monthly-ledger"><rect x="145" y="240" width="710" height="245" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M145 310h710M305 240v245M485 240v245M665 240v245" stroke="{accent}" stroke-width="8"/><path d="M210 190h170l35 50H175Z" fill="{pale}" stroke="{dark}" stroke-width="9"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="225" y="280">暦月</text><text x="395" y="280">受診者</text><text x="575" y="280">医療機関</text><text x="760" y="280">入院・外来</text><text x="295" y="220">8月受診分</text></g></g>',
            f'<g data-scene="age-calculation-order-desk"><rect x="130" y="230" width="335" height="250" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><rect x="535" y="230" width="335" height="250" rx="18" fill="{pale}" stroke="{dark}" stroke-width="10"/><path d="M210 330h170m-25-25 30 25-30 25M615 300h170m-25-25 30 25-30 25M615 390h170" fill="none" stroke="{accent}" stroke-width="11"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="297" y="270">70歳未満</text><text x="297" y="315">個別行</text><text x="297" y="405">世帯合算</text><text x="702" y="270">70～74歳</text><text x="702" y="355">外来個人</text><text x="702" y="440">世帯</text></g></g>',
            f'<g data-scene="application-decision-twelve-month-route"><rect x="110" y="225" width="210" height="105" rx="15" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="395" y="225" width="210" height="105" rx="15" fill="{pale}" stroke="{dark}" stroke-width="9"/><rect x="680" y="225" width="210" height="105" rx="15" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M320 277h75M605 277h75" stroke="{accent}" stroke-width="12"/><g font-family="sans-serif" font-size="17" font-weight="700" fill="{dark}" text-anchor="middle"><text x="215" y="285">申請書到着</text><text x="500" y="285">提出</text><text x="785" y="285">決定通知</text></g><g fill="{accent}"><rect x="130" y="390" width="48" height="55" rx="8"/><rect x="192" y="390" width="48" height="55" rx="8"/><rect x="254" y="390" width="48" height="55" rx="8"/><rect x="316" y="390" width="48" height="55" rx="8"/><rect x="378" y="390" width="48" height="55" rx="8"/><rect x="440" y="390" width="48" height="55" rx="8"/><rect x="502" y="390" width="48" height="55" rx="8"/><rect x="564" y="390" width="48" height="55" rx="8"/><rect x="626" y="390" width="48" height="55" rx="8"/><rect x="688" y="390" width="48" height="55" rx="8"/><rect x="750" y="390" width="48" height="55" rx="8"/><rect x="812" y="390" width="48" height="55" rx="8"/></g><text x="500" y="485" font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle">過去12か月の支給月</text></g>',
        ],
        20: [
            f'<g data-scene="house-demolition-two-public-records"><path d="M170 445 300 270l105 115 95-160 135 160 95-115 120 175" fill="none" stroke="{dark}" stroke-width="18"/><path d="M170 470h660" stroke="{accent}" stroke-width="14"/><path d="M390 420V300l110-85 110 85v120Z" fill="none" stroke="{dark}" stroke-width="11" stroke-dasharray="18 12"/><rect x="205" y="285" width="145" height="145" rx="15" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="650" y="285" width="145" height="145" rx="15" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M235 335h85M235 380h85M680 335h85M680 380h85" stroke="{accent}" stroke-width="8"/></g>',
            f'<g data-scene="demolished-and-remaining-building-map"><path d="M180 450V250h640v200Z" fill="{pale}" stroke="{dark}" stroke-width="10"/><path d="M180 370h640" stroke="{accent}" stroke-width="14"/><path d="M245 350V275l70-55 70 55v75Z" fill="none" stroke="{dark}" stroke-width="9" stroke-dasharray="15 10"/><path d="M580 350V275l70-55 70 55v75Z" fill="#fff" stroke="{dark}" stroke-width="9"/><circle cx="315" cy="400" r="25" fill="{accent}"/><circle cx="650" cy="400" r="25" fill="{accent}"/><g font-family="sans-serif" font-size="20" font-weight="700" fill="{dark}" text-anchor="middle"><text x="315" y="410">1</text><text x="650" y="410">2</text></g></g>',
            f'<g data-scene="town-notice-registry-next-year-route"><rect x="160" y="275" width="185" height="130" rx="16" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="410" y="275" width="185" height="130" rx="16" fill="{pale}" stroke="{dark}" stroke-width="9"/><rect x="660" y="275" width="185" height="130" rx="16" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M345 340h65M595 340h65" stroke="{accent}" stroke-width="14"/><circle cx="500" cy="475" r="45" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M500 475v-28M500 475l25 18" stroke="{accent}" stroke-width="9"/></g>',
        ],
        1: [
            f'<g data-scene="mori-divorce-effective-date-fork-ledger"><path d="M165 445 330 285l95 75 90-125 125 105 110-95 105 200Z" fill="{pale}" stroke="{dark}" stroke-width="9"/><path d="M500 195v90M500 285 330 405M500 285l170 120" fill="none" stroke="{accent}" stroke-width="12"/><rect x="210" y="390" width="240" height="105" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="550" y="390" width="240" height="105" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="500" y="175">離婚成立日</text><text x="330" y="430">2026年3月31日以前</text><text x="330" y="470">旧ルール欄</text><text x="670" y="430">2026年4月1日以後</text><text x="670" y="470">新ルール欄</text></g></g>',
            f'<g data-scene="four-issue-effective-date-routing-board"><rect x="165" y="235" width="670" height="250" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M165 310h670M332 235v250M500 235v250M668 235v250" stroke="{accent}" stroke-width="8"/><g font-family="sans-serif" font-size="17" font-weight="700" fill="{dark}" text-anchor="middle"><text x="248" y="280">親権</text><text x="416" y="280">法定養育費</text><text x="584" y="280">既存合意</text><text x="752" y="280">財産分与</text><text x="248" y="365">成立日</text><text x="416" y="365">適用・暫定</text><text x="584" y="365">各期を分離</text><text x="752" y="365">二年・五年</text></g></g>',
            f'<g data-scene="two-clocks-two-counters-safe-handoff"><circle cx="290" cy="320" r="92" fill="#fff" stroke="{dark}" stroke-width="10"/><circle cx="505" cy="320" r="92" fill="{pale}" stroke="{dark}" stroke-width="10"/><path d="M290 320v-55m0 55 42 28M505 320v-55m0 55-38 32" stroke="{accent}" stroke-width="11"/><rect x="650" y="235" width="190" height="170" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M650 320h190" stroke="{accent}" stroke-width="8"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="290" y="450">二年</text><text x="505" y="450">五年</text><text x="745" y="280">森町窓口</text><text x="745" y="365">法律相談</text></g></g>',
        ],
        168: [
            f'<g data-scene="regional-plan-four-column-parcel-sheet"><path d="M150 440 300 230l120 210 110-180 120 180 115-155 85 155Z" fill="{pale}" stroke="{dark}" stroke-width="9"/><rect x="205" y="265" width="590" height="220" rx="16" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M205 330h590M352 265v220M500 265v220M648 265v220" stroke="{accent}" stroke-width="8"/><g font-family="sans-serif" font-size="17" font-weight="700" fill="{dark}" text-anchor="middle"><text x="278" y="305">所有者</text><text x="426" y="305">現在耕作者</text><text x="574" y="305">将来担い手</text><text x="722" y="305">更新日</text></g></g>',
            f'<g data-scene="goal-map-number-to-actor-list"><path d="M195 245 445 215l75 105-65 155-250-15Z" fill="#fff" stroke="{dark}" stroke-width="10"/><circle cx="285" cy="330" r="28" fill="{accent}"/><circle cx="400" cy="390" r="28" fill="{pale}" stroke="{dark}" stroke-width="7"/><path d="M520 350h65m-28-28 28 28-28 28" fill="none" stroke="{dark}" stroke-width="12"/><rect x="610" y="225" width="210" height="250" rx="16" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M610 290h210M680 225v250" stroke="{accent}" stroke-width="8"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="285" y="337">12</text><text x="400" y="397">27</text><text x="645" y="267">番号</text><text x="750" y="267">担い手</text><text x="715" y="355">一覧へ照合</text></g></g>',
            f'<g data-scene="regional-plan-version-timeline"><path d="M180 360h640" stroke="{dark}" stroke-width="14"/><circle cx="260" cy="360" r="28" fill="{accent}"/><circle cx="500" cy="360" r="28" fill="#fff" stroke="{accent}" stroke-width="9"/><circle cx="740" cy="360" r="28" fill="{pale}" stroke="{dark}" stroke-width="9"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="260" y="275">2025年3月26日</text><text x="260" y="310">策定</text><text x="500" y="275">2026年3月12日</text><text x="500" y="310">第1回変更</text><text x="740" y="275">2035年度</text><text x="740" y="310">将来像</text><text x="500" y="445">現在の権利とは別欄</text></g></g>',
        ],
        172: [
            f'<g data-scene="electric-fence-prepurchase-safety-layout"><path d="M170 450h660M230 450V245h540v205" fill="none" stroke="{dark}" stroke-width="10"/><path d="M275 420V280m90 140V280m90 140V280m90 140V280m90 140V280m90 140V280" stroke="{accent}" stroke-width="8"/><path d="M230 335h540" stroke="{accent}" stroke-width="7" stroke-dasharray="15 10"/><path d="M150 500h700" stroke="{dark}" stroke-width="20"/><path d="M620 245q70-90 145 0" fill="none" stroke="{dark}" stroke-width="12"/><g font-family="sans-serif" font-size="17" font-weight="700" fill="{dark}" text-anchor="middle"><text x="500" y="220">柵線・出入口・草刈り動線</text><text x="500" y="530">道路・水路側</text><text x="690" y="275">電源装置</text></g></g>',
            f'<g data-scene="public-boundary-and-warning-sign-plan"><path d="M170 440h660" stroke="{dark}" stroke-width="18"/><path d="M245 420V245m145 175V245m145 175V245m145 175V245" stroke="{accent}" stroke-width="9"/><rect x="285" y="275" width="150" height="75" rx="8" fill="#fff" stroke="{dark}" stroke-width="8"/><rect x="565" y="275" width="150" height="75" rx="8" fill="#fff" stroke="{dark}" stroke-width="8"/><path d="M210 470h580" stroke="{pale}" stroke-width="14"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="360" y="322">危険表示</text><text x="640" y="322">危険表示</text><text x="500" y="505">公共境界</text></g></g>',
            f'<g data-scene="power-device-and-maintenance-check-route"><rect x="190" y="245" width="180" height="200" rx="16" fill="#fff" stroke="{dark}" stroke-width="10"/><rect x="410" y="215" width="180" height="230" rx="16" fill="{pale}" stroke="{dark}" stroke-width="10"/><rect x="630" y="245" width="180" height="200" rx="16" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M370 345h40m180 0h40" stroke="{accent}" stroke-width="13"/><g font-family="sans-serif" font-size="17" font-weight="700" fill="{dark}" text-anchor="middle"><text x="280" y="285">電源装置</text><text x="280" y="335">30V超</text><text x="280" y="385">仕様確認</text><text x="500" y="270">立入り条件</text><text x="500" y="325">漏電遮断器</text><text x="500" y="380">専用開閉器</text><text x="720" y="285">草・断線</text><text x="720" y="335">傾き・接地</text><text x="720" y="385">点検履歴</text></g></g>',
        ],
        149: [
            f'<g data-scene="mori-narrow-road-four-lines"><path d="M180 455 420 205M820 455 580 205" stroke="{dark}" stroke-width="12"/><path d="M265 455 455 230M735 455 545 230" stroke="{accent}" stroke-width="9" stroke-dasharray="18 12"/><path d="M500 185v300" stroke="{dark}" stroke-width="8" stroke-dasharray="10 12"/><path d="M410 410V300l90-70 90 70v110Z" fill="#fff" stroke="{dark}" stroke-width="9"/><g font-family="sans-serif" font-size="16" font-weight="700" fill="{dark}" text-anchor="middle"><text x="245" y="490">町有道路境界</text><text x="390" y="460">後退候補線</text><text x="500" y="520">基準時中心線</text><text x="755" y="490">道路区域の線</text></g></g>',
            f'<g data-scene="gis-counter-field-crosscheck"><rect x="220" y="235" width="180" height="210" rx="16" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="410" y="285" width="180" height="160" rx="16" fill="{pale}" stroke="{dark}" stroke-width="9"/><rect x="600" y="235" width="180" height="210" rx="16" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M400 340h10m180 0h10" stroke="{accent}" stroke-width="14"/><g font-family="sans-serif" font-size="19" font-weight="700" fill="{dark}" text-anchor="middle"><text x="310" y="275">指定道路図</text><text x="310" y="355">GIS</text><text x="500" y="325">町・県</text><text x="500" y="365">窓口確認</text><text x="690" y="275">地番・写真</text><text x="690" y="355">現地確認</text></g></g>',
            f'<g data-scene="setback-design-version-route"><rect x="215" y="255" width="175" height="170" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="415" y="225" width="175" height="200" rx="14" fill="{pale}" stroke="{dark}" stroke-width="9"/><rect x="615" y="275" width="175" height="150" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M390 340h25m175 0h25" stroke="{accent}" stroke-width="13"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="302" y="305">照会前図</text><text x="302" y="365">未確認線</text><text x="502" y="285">確認回答</text><text x="502" y="345">日付・担当</text><text x="702" y="325">配置図版</text><text x="702" y="375">設計者確認</text></g></g>',
        ],
        159: [
            f'<g data-scene="public-land-price-comparison-card"><rect x="210" y="245" width="180" height="195" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="410" y="215" width="180" height="225" rx="14" fill="{pale}" stroke="{dark}" stroke-width="9"/><rect x="610" y="245" width="180" height="195" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M250 310h100M250 360h85M450 285h100M450 340h85M650 310h100M650 360h85" stroke="{accent}" stroke-width="8"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="300" y="275">地価公示</text><text x="500" y="255">取引価格</text><text x="700" y="275">用途図</text><text x="500" y="405">比較条件カード</text></g></g>',
            f'<g data-scene="property-type-period-filter-board"><rect x="210" y="235" width="580" height="235" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M210 305h580M355 235v235M500 235v235M645 235v235" stroke="{accent}" stroke-width="8"/><g font-family="sans-serif" font-size="17" font-weight="700" fill="{dark}" text-anchor="middle"><text x="282" y="280">土地</text><text x="427" y="280">土地建物</text><text x="572" y="280">農地</text><text x="717" y="280">林地</text><text x="282" y="355">地域</text><text x="427" y="355">期間</text><text x="572" y="355">面積帯</text><text x="717" y="355">採否理由</text></g><path d="m665 420 25 25 55-75" fill="none" stroke="{dark}" stroke-width="12"/></g>',
            f'<g data-scene="comparable-sale-question-sheet"><path d="M230 245h230v210H230Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M270 300h150M270 345h115M270 390h140" stroke="{accent}" stroke-width="8"/><path d="M460 350h85m-30-28 30 28-30 28" fill="none" stroke="{dark}" stroke-width="13"/><rect x="570" y="230" width="210" height="240" rx="16" fill="{pale}" stroke="{dark}" stroke-width="10"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="345" y="275">比較候補</text><text x="675" y="275">査定前の質問</text><text x="675" y="330">面積・形状</text><text x="675" y="375">接道・時点</text><text x="675" y="420">未確認項目</text></g></g>',
        ],
        166: [
            f'<g data-scene="conversion-permit-construction-brief"><rect x="220" y="240" width="210" height="205" rx="15" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M260 295h130M260 340h100M260 385h115" stroke="{accent}" stroke-width="8"/><path d="M430 345h85m-30-28 30 28-30 28" fill="none" stroke="{dark}" stroke-width="13"/><path d="M565 440V305l90-70 90 70v135Z" fill="#fff" stroke="{dark}" stroke-width="10"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="325" y="275">許可書・申請図</text><text x="655" y="285">着工前</text><text x="655" y="375">対象範囲を照合</text></g></g>',
            f'<g data-scene="parcel-road-water-plan-overlay"><path d="M230 250 455 215l90 100-55 155-235 10Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M330 235l45 235M240 365l270 55" stroke="{accent}" stroke-width="8"/><path d="M555 420q85-155 205-85" fill="none" stroke="{dark}" stroke-width="18"/><path d="M555 455q85-155 205-85" fill="none" stroke="{accent}" stroke-width="12"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}"><text x="265" y="300">申請地</text><text x="585" y="300">道路</text><text x="665" y="410">排水</text></g></g>',
            f'<g data-scene="construction-progress-completion-route"><rect x="190" y="285" width="160" height="130" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="420" y="235" width="160" height="180" rx="14" fill="{pale}" stroke="{dark}" stroke-width="9"/><rect x="650" y="285" width="160" height="130" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M350 350h70m160 0h70" stroke="{accent}" stroke-width="14"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="270" y="335">許可条件</text><text x="270" y="380">計画変更</text><text x="500" y="300">工事進捗</text><text x="500" y="355">写真・日付</text><text x="730" y="335">完了報告</text><text x="730" y="380">結果保管</text></g></g>',
        ],
        176: [
            f'<g data-scene="forest-notice-all-parcels-map"><path d="M210 250 390 205l105 90-65 175-205 5Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M300 228l35 237M220 360l245 55" stroke="{accent}" stroke-width="8"/><rect x="555" y="225" width="230" height="245" rx="15" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M555 290h230M630 225v245M705 225v245" stroke="{accent}" stroke-width="8"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="290" y="320">図上1</text><text x="390" y="400">図上2</text><text x="592" y="265">行</text><text x="667" y="265">地番</text><text x="745" y="265">図番</text></g></g>',
            f'<g data-scene="forest-map-source-comparison-desk"><rect x="200" y="250" width="170" height="190" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="415" y="215" width="170" height="225" rx="14" fill="{pale}" stroke="{dark}" stroke-width="9"/><rect x="630" y="250" width="170" height="190" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="285" y="300">地理院地図</text><text x="285" y="370">縮尺・取得日</text><text x="500" y="270">町の案内図</text><text x="500" y="350">概略位置</text><text x="715" y="300">手元の地図</text><text x="715" y="370">出典未確認</text></g></g>',
            f'<g data-scene="parcel-row-map-number-handover"><rect x="205" y="235" width="260" height="230" rx="15" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M205 300h260M290 235v230M380 235v230" stroke="{accent}" stroke-width="8"/><path d="M465 350h80m-30-28 30 28-30 28" fill="none" stroke="{dark}" stroke-width="13"/><path d="M585 250 770 225l45 105-65 135-195-20-35-105Z" fill="#fff" stroke="{dark}" stroke-width="10"/><circle cx="635" cy="330" r="24" fill="{accent}"/><circle cx="735" cy="380" r="24" fill="{pale}" stroke="{dark}" stroke-width="7"/><g font-family="sans-serif" font-size="17" font-weight="700" fill="{dark}" text-anchor="middle"><text x="248" y="275">届出行</text><text x="335" y="275">地番</text><text x="422" y="275">図番</text><text x="675" y="475">全筆照合</text></g></g>',
        ],
        249: [
            f'<g data-scene="property-tax-certificate-router"><rect x="235" y="245" width="190" height="210" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M270 300h120M270 345h95M270 390h110" stroke="{accent}" stroke-width="8"/><path d="M425 350h75m-25-25 25 25-25 25" fill="none" stroke="{dark}" stroke-width="12"/><rect x="535" y="205" width="210" height="275" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M535 270h210M535 335h210M535 400h210M640 205v275" stroke="{accent}" stroke-width="8"/><g font-family="sans-serif" font-size="17" font-weight="700" fill="{dark}" text-anchor="middle"><text x="330" y="285">課税明細</text><text x="585" y="245">評価</text><text x="690" y="245">通知</text><text x="585" y="310">公課</text><text x="690" y="310">資産</text><text x="640" y="375">提出先の必要項目</text><text x="640" y="445">年度・対象</text></g></g>',
            f'<g data-scene="five-purpose-certificate-branches"><circle cx="500" cy="235" r="42" fill="{accent}"/><path d="M500 277v55M500 332 285 415M500 332 390 415M500 332v83M500 332l110 83M500 332l215 83" fill="none" stroke="{dark}" stroke-width="11"/><g fill="#fff" stroke="{accent}" stroke-width="8"><rect x="225" y="415" width="120" height="70" rx="12"/><rect x="350" y="415" width="120" height="70" rx="12"/><rect x="475" y="415" width="120" height="70" rx="12"/><rect x="600" y="415" width="120" height="70" rx="12"/><rect x="725" y="415" width="120" height="70" rx="12"/></g><g font-family="sans-serif" font-size="15" font-weight="700" fill="{dark}" text-anchor="middle"><text x="500" y="242">必要項目</text><text x="285" y="457">年次確認</text><text x="410" y="457">一般用</text><text x="535" y="457">登記用</text><text x="660" y="448">記載項目</text><text x="660" y="469">を確認</text><text x="785" y="448">所有資産</text><text x="785" y="469">を確認</text></g></g>',
            f'<g data-scene="property-certificate-scope-dials"><g fill="#fff" stroke="{dark}" stroke-width="8"><circle cx="270" cy="285" r="48"/><circle cx="385" cy="285" r="48"/><circle cx="500" cy="285" r="48"/><circle cx="615" cy="285" r="48"/><circle cx="730" cy="285" r="48"/></g><path d="M270 285l20-24M385 285l-22-20M500 285l25 15M615 285l-20 25M730 285l18-25" stroke="{accent}" stroke-width="10"/><path d="M500 345v55M500 400 375 465M500 400l125 65" fill="none" stroke="{dark}" stroke-width="12"/><rect x="285" y="445" width="180" height="65" rx="12" fill="#fff" stroke="{accent}" stroke-width="8"/><rect x="535" y="445" width="180" height="65" rx="12" fill="{pale}" stroke="{accent}" stroke-width="8"/><g font-family="sans-serif" font-size="16" font-weight="700" fill="{dark}" text-anchor="middle"><text x="270" y="220">年度</text><text x="385" y="220">名義</text><text x="500" y="220">土地家屋</text><text x="615" y="220">範囲</text><text x="730" y="220">番号</text><text x="375" y="486">窓口用</text><text x="625" y="486">郵便用</text></g></g>',
        ],
        288: [
            f'<g data-scene="public-facility-evidence-index"><path d="M220 420V335l65-50 65 50v85Zm190 0V315l75-58 75 58v105Zm205 0V335l65-50 65 50v85Z" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M350 365h60m150 0h55" stroke="{accent}" stroke-width="11"/><rect x="250" y="445" width="500" height="70" rx="14" fill="{pale}" stroke="{dark}" stroke-width="9"/><path d="M375 445v70M500 445v70M625 445v70" stroke="{accent}" stroke-width="8"/><g font-family="sans-serif" font-size="17" font-weight="700" fill="{dark}" text-anchor="middle"><text x="285" y="470">計画</text><text x="435" y="470">予算</text><text x="560" y="470">入札</text><text x="688" y="470">完了</text></g></g>',
            f'<g data-scene="repair-renovation-renewal-cutaway"><path d="M230 455V260h540v195Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M410 260v195M590 260v195" stroke="{accent}" stroke-width="9"/><path d="m270 320 35 28-28 35 38 25" fill="none" stroke="{dark}" stroke-width="10"/><path d="M465 400v-95h70v95M445 325h110" fill="{pale}" stroke="{dark}" stroke-width="9"/><path d="M635 410 720 300M675 410l55-70M625 315h105" fill="none" stroke="{dark}" stroke-width="12"/><g font-family="sans-serif" font-size="20" font-weight="700" fill="{dark}" text-anchor="middle"><text x="320" y="225">修繕</text><text x="500" y="225">改修</text><text x="680" y="225">更新等</text></g></g>',
            f'<g data-scene="plan-budget-bid-completion-route"><path d="M225 385h550" stroke="{dark}" stroke-width="14"/><path d="m360 350 35 35-35 35m135-70 35 35-35 35m135-70 35 35-35 35" fill="none" stroke="{accent}" stroke-width="11"/><g fill="#fff" stroke="{dark}" stroke-width="9"><rect x="195" y="250" width="120" height="105" rx="12"/><rect x="335" y="250" width="120" height="105" rx="12"/><rect x="475" y="250" width="120" height="105" rx="12"/><rect x="615" y="250" width="150" height="105" rx="12"/></g><path d="M220 290h70M220 320h55M360 290h70M360 320h55M500 290h70M500 320h55M645 290h90M645 320h70" stroke="{accent}" stroke-width="7"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="255" y="225">計画</text><text x="395" y="225">予算</text><text x="535" y="225">入札</text><text x="690" y="225">完了確認</text></g></g>',
        ],
        190: [
            f'<g data-scene="outdoor-sign-two-permit-route"><path d="M285 455V320l125-95 125 95v135Z" fill="#fff" stroke="{dark}" stroke-width="10"/><rect x="355" y="330" width="110" height="65" rx="8" fill="{accent}"/><path d="M535 350h65m-35-35 35 35-35 35" fill="none" stroke="{dark}" stroke-width="13"/><rect x="620" y="235" width="145" height="105" rx="12" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="620" y="385" width="145" height="105" rx="12" fill="{pale}" stroke="{dark}" stroke-width="9"/><path d="M650 280h85M650 430h85" stroke="{accent}" stroke-width="8"/></g>',
            f'<g data-scene="sign-location-dimension-survey"><path d="M270 455V275h250v180Z" fill="#fff" stroke="{dark}" stroke-width="10"/><rect x="325" y="325" width="140" height="75" rx="8" fill="{pale}" stroke="{accent}" stroke-width="9"/><path d="M295 245h200m-200-20v40m200-40v40M240 285v160m-20-160h40m-40 160h40" stroke="{dark}" stroke-width="8"/><path d="M585 255h165v210H585Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M620 305h95M620 350h75M620 395h90" stroke="{accent}" stroke-width="9"/></g>',
            f'<g data-scene="advertisement-building-action-split"><rect x="245" y="255" width="210" height="190" rx="14" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M285 305h130M285 355h100M285 405h115" stroke="{accent}" stroke-width="9"/><path d="M455 350h90m-30-28 30 28-30 28" fill="none" stroke="{dark}" stroke-width="13"/><path d="M585 455V315l80-65 80 65v140Z" fill="#fff" stroke="{dark}" stroke-width="10"/><rect x="620" y="335" width="90" height="60" fill="{pale}" stroke="{accent}" stroke-width="8"/></g>',
        ],
        194: [
            f'<g data-scene="procurement-four-stage-entry-route"><path d="M245 410h510" stroke="{dark}" stroke-width="14"/><circle cx="290" cy="410" r="32" fill="{accent}"/><circle cx="430" cy="410" r="32" fill="#fff" stroke="{dark}" stroke-width="8"/><circle cx="570" cy="410" r="32" fill="{pale}" stroke="{dark}" stroke-width="8"/><circle cx="710" cy="410" r="32" fill="{accent}"/><path d="M290 378V255h420v123M430 255v123M570 255v123" fill="none" stroke="{accent}" stroke-width="9"/></g>',
            f'<g data-scene="three-procurement-category-desks"><rect x="235" y="285" width="155" height="155" rx="15" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="422" y="245" width="155" height="195" rx="15" fill="{pale}" stroke="{dark}" stroke-width="9"/><rect x="610" y="285" width="155" height="155" rx="15" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M275 335h75M275 380h75M462 300h75M462 350h75M462 400h75M650 335h75M650 380h75" stroke="{accent}" stroke-width="8"/></g>',
            f'<g data-scene="ledger-to-electronic-registration"><rect x="245" y="260" width="210" height="190" rx="15" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M285 310h130M285 355h105M285 400h120" stroke="{accent}" stroke-width="9"/><path d="M455 355h100m-32-30 32 30-32 30" fill="none" stroke="{dark}" stroke-width="13"/><rect x="595" y="235" width="165" height="225" rx="14" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M630 285h95M630 330h75M630 375h90" stroke="{accent}" stroke-width="8"/><rect x="645" y="400" width="65" height="35" rx="8" fill="{pale}" stroke="{dark}" stroke-width="7"/></g>',
        ],
        17: [
            f'<g data-scene="family-furigana-notice-rows"><path d="M250 225h245v245H250Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="m250 225 122 92 123-92M275 355h195M275 405h195" fill="none" stroke="{accent}" stroke-width="9"/><path d="M535 225h230v245H535Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M535 285h230M535 345h230M535 405h230M610 225v245M690 225v245" stroke="{accent}" stroke-width="7"/><g font-family="sans-serif" font-size="17" font-weight="700" fill="{dark}" text-anchor="middle"><text x="372" y="205">圧着はがき</text><text x="575" y="260">家族</text><text x="650" y="260">氏</text><text x="728" y="260">名</text><text x="575" y="323">1</text><text x="575" y="383">2</text><text x="575" y="443">3・4</text></g></g>',
            f'<g data-scene="furigana-responsibility-lines"><circle cx="280" cy="285" r="39" fill="{accent}"/><circle cx="280" cy="415" r="39" fill="#fff" stroke="{dark}" stroke-width="8"/><path d="M320 285h145M320 415h145" stroke="{dark}" stroke-width="13"/><rect x="465" y="235" width="245" height="100" rx="16" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="465" y="365" width="245" height="100" rx="16" fill="{pale}" stroke="{dark}" stroke-width="9"/><path d="M710 285h55M710 415h55" stroke="{accent}" stroke-width="13"/><g font-family="sans-serif" font-size="20" font-weight="700" fill="{dark}" text-anchor="middle"><text x="280" y="292">氏</text><text x="280" y="422">名</text><text x="587" y="278">原則・筆頭者</text><text x="587" y="408">本人</text><text x="587" y="438">または法定代理人</text></g></g>',
            f'<g data-scene="furigana-three-time-crosscheck"><rect x="225" y="245" width="185" height="190" rx="15" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="410" y="245" width="185" height="190" rx="15" fill="{pale}" stroke="{dark}" stroke-width="9"/><rect x="595" y="245" width="185" height="190" rx="15" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M260 320h115M260 365h90M445 320h115M445 365h90M630 320h115M630 365h90" stroke="{accent}" stroke-width="8"/><path d="M410 465h185M502 435v55" stroke="{dark}" stroke-width="10"/><g font-family="sans-serif" font-size="20" font-weight="700" fill="{dark}" text-anchor="middle"><text x="317" y="285">2025年通知</text><text x="502" y="285">届出控え</text><text x="687" y="285">現在記載</text><text x="502" y="520">家族番号で照合</text></g></g>',
        ],
        207: [
            f'<g data-scene="festival-photo-envelope"><rect x="285" y="245" width="280" height="210" rx="16" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M315 400l75-82 58 55 52-42 35 69" fill="none" stroke="{accent}" stroke-width="12"/><circle cx="365" cy="300" r="27" fill="{pale}" stroke="{dark}" stroke-width="8"/><path d="M595 300h145v150H595Zm0 0 72 62 73-62" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M625 395h85" stroke="{accent}" stroke-width="9"/></g>',
            f'<g data-scene="photo-provenance-chain"><rect x="250" y="285" width="155" height="135" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="595" y="285" width="155" height="135" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><circle cx="500" cy="350" r="55" fill="{pale}" stroke="{accent}" stroke-width="10"/><path d="M405 350h40m110 0h40" stroke="{dark}" stroke-width="14"/><path d="m430 330 20 20-20 20m140-40 20 20-20 20" fill="none" stroke="{accent}" stroke-width="9"/><path d="M285 325h85m-85 45h60m285-45h85m-85 45h60" stroke="{accent}" stroke-width="8"/></g>',
            f'<g data-scene="photo-publication-scope"><rect x="270" y="250" width="220" height="190" rx="15" fill="#fff" stroke="{dark}" stroke-width="10"/><circle cx="340" cy="325" r="28" fill="{accent}"/><circle cx="420" cy="325" r="28" fill="{pale}" stroke="{dark}" stroke-width="7"/><path d="M300 405q40-80 80 0m0 0q40-80 80 0" fill="none" stroke="{dark}" stroke-width="12"/><path d="M540 290h190v150H540Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M575 330h120M575 370h85" stroke="{accent}" stroke-width="9"/><path d="M635 250v-45m-45 25 45-25 45 25" fill="none" stroke="{dark}" stroke-width="11"/></g>',
        ],
        206: [
            f'<g data-scene="festival-float"><path d="M315 410h370l-42-135H357Z" fill="#fff" stroke="{dark}" stroke-width="10"/><circle cx="395" cy="440" r="42" fill="{accent}"/><circle cx="605" cy="440" r="42" fill="{accent}"/><path d="M420 275v-82m160 82v-82M382 193h236" stroke="{dark}" stroke-width="12"/><circle cx="420" cy="185" r="24" fill="#fff" stroke="{accent}" stroke-width="8"/><circle cx="580" cy="185" r="24" fill="#fff" stroke="{accent}" stroke-width="8"/></g>',
            f'<g data-scene="bugaku-fan"><path d="M500 445 355 250q145-92 290 0Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M500 445 405 230M500 445l95-215M500 445V205" stroke="{accent}" stroke-width="9"/><circle cx="500" cy="445" r="23" fill="{dark}"/></g>',
            f'<g data-scene="festival-photo-log"><rect x="300" y="260" width="250" height="175" rx="22" fill="#fff" stroke="{dark}" stroke-width="10"/><circle cx="425" cy="347" r="54" fill="{pale}" stroke="{accent}" stroke-width="12"/><path d="M365 260l35-45h70l35 45M610 250h105v220H610M635 300h55M635 345h55M635 390h55" fill="none" stroke="{dark}" stroke-width="10"/></g>',
        ],
        208: [
            f'<g data-scene="town-history-volumes"><path d="M310 420h380v60H310Zm35-85h310v70H345Zm40-95h230v80H385Z" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M430 240v80M405 335v70M380 420v60" stroke="{accent}" stroke-width="12"/></g>',
            f'<g data-scene="archive-index"><path d="M310 280h380v205H310Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M340 245h110l25 35H340Zm180 0h110l25 35H520Z" fill="{accent}" stroke="{dark}" stroke-width="8"/><path d="M370 335h260M370 385h210M370 435h245" stroke="{dark}" stroke-width="9"/></g>',
            f'<g data-scene="map-page-reference"><path d="M300 245 430 215l140 45 130-30v230l-130 30-140-45-130 30Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M430 215v230M570 260v230M345 380q90-105 180-25t130-20" fill="none" stroke="{accent}" stroke-width="11"/><circle cx="525" cy="355" r="22" fill="{dark}"/></g>',
        ],
        218: [
            f'<g data-scene="ota-river-basin"><path d="M300 270 395 160l100 125 90-145 120 145" fill="none" stroke="{dark}" stroke-width="14"/><path d="M500 250c-85 80-30 120-145 225M500 250c60 75 25 120 150 225M500 250v225" fill="none" stroke="{accent}" stroke-width="18"/><circle cx="500" cy="245" r="20" fill="#fff" stroke="{dark}" stroke-width="8"/></g>',
            f'<g data-scene="river-walk-sequence"><path d="M275 400q110-120 220-10t230-25" fill="none" stroke="{accent}" stroke-width="22"/><path d="M340 465v-150h95v150M590 465V290h110v175" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M310 315h155l-78-70Zm250-25h170l-85-80Z" fill="#fff" stroke="{dark}" stroke-width="10"/></g>',
            f'<g data-scene="flood-map-layers"><rect x="295" y="220" width="410" height="255" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M330 420q85-135 175-40t165-85" fill="none" stroke="{accent}" stroke-width="20"/><path d="M360 260h110v60H360Zm160 95h120v70H520Z" fill="{pale}" stroke="{dark}" stroke-width="8"/><path d="M500 220v255" stroke="{dark}" stroke-width="6" stroke-dasharray="15 12"/></g>',
        ],
        223: [
            f'<g data-scene="moving-calendar"><rect x="300" y="225" width="400" height="255" rx="22" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M300 300h400M390 225v75M610 225v75" stroke="{dark}" stroke-width="10"/><path d="M355 355h70v70h-70Zm110 0h70v70h-70Zm110 0h70v70h-70" fill="{pale}" stroke="{accent}" stroke-width="9"/><path d="m480 390 20 20 48-55" fill="none" stroke="{dark}" stroke-width="12"/></g>',
            f'<g data-scene="certificate-transfer"><rect x="285" y="265" width="240" height="175" rx="16" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M325 315h160M325 360h125M325 405h145" stroke="{dark}" stroke-width="9"/><path d="M555 350h155m-65-65 65 65-65 65" fill="none" stroke="{accent}" stroke-width="18"/><rect x="690" y="285" width="35" height="130" fill="{dark}"/></g>',
            f'<g data-scene="old-new-address"><path d="M285 445V315l110-85 110 85v130Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M335 445v-85h65v85" fill="{accent}"/><path d="M535 350h130m-55-55 55 55-55 55" fill="none" stroke="{dark}" stroke-width="16"/><rect x="690" y="260" width="65" height="185" rx="8" fill="#fff" stroke="{accent}" stroke-width="10"/></g>',
        ],
        229: [
            f'<g data-scene="tax-notice-years"><path d="M300 260h230v175H300Zm75-45h230v175H375Zm75-45h230v175H450Z" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M485 225h155M410 270h155M335 315h155" stroke="{accent}" stroke-width="10"/><circle cx="595" cy="310" r="30" fill="{pale}" stroke="{dark}" stroke-width="8"/></g>',
            f'<g data-scene="parcel-house-ledger"><path d="M290 290h250v180H290Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M290 350h250M370 290v180M455 290v180" stroke="{accent}" stroke-width="8"/><path d="M590 450V315l75-65 75 65v135Z" fill="#fff" stroke="{dark}" stroke-width="10"/><rect x="645" y="385" width="45" height="65" fill="{accent}"/></g>',
            f'<g data-scene="tax-versus-registry"><path d="M285 250h265v220H285Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M450 250h265v220H450Z" fill="{pale}" stroke="{dark}" stroke-width="10"/><path d="M325 315h175M325 365h150M490 315h175M490 365h150" stroke="{accent}" stroke-width="9"/><path d="M475 425h50" stroke="{dark}" stroke-width="18"/></g>',
        ],
        234: [
            f'<g data-scene="water-meter"><circle cx="500" cy="350" r="112" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M500 350 565 292" stroke="{accent}" stroke-width="14"/><circle cx="500" cy="350" r="16" fill="{dark}"/><path d="M405 430h190" stroke="{dark}" stroke-width="12"/></g>',
            f'<g data-scene="water-key"><path d="M365 350a72 72 0 1 0 144 0 72 72 0 1 0-144 0" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M505 350h180v38h-48v42h-42v-42h-90" fill="none" stroke="{accent}" stroke-width="18"/></g>',
            f'<g data-scene="moving-calendar"><rect x="340" y="245" width="320" height="230" rx="20" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M340 305h320M420 245v60M580 245v60" stroke="{dark}" stroke-width="9"/><path d="m430 395 42 42 92-105" fill="none" stroke="{accent}" stroke-width="18"/></g>',
        ],
        247: [
            f'<g data-scene="shared-property"><circle cx="445" cy="350" r="105" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M445 245v210M340 350h210" stroke="{accent}" stroke-width="10"/><rect x="575" y="280" width="150" height="190" rx="16" fill="#fff" stroke="{dark}" stroke-width="9"/></g>',
            f'<g data-scene="representative-order"><path d="M330 455h340M370 455v-65h80v-65h80v-65h80v-65" fill="none" stroke="{dark}" stroke-width="14"/><circle cx="610" cy="195" r="28" fill="{accent}"/></g>',
            f'<g data-scene="tax-ledger"><rect x="330" y="245" width="340" height="230" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M330 315h340M500 245v230M365 360h100M535 360h100M365 415h100M535 415h100" stroke="{accent}" stroke-width="9"/></g>',
        ],
        252: [
            f'<g data-scene="evacuation-signs"><path d="M500 470V245M500 275h185l-55 50 55 50H500M500 330H315l55 50-55 50h185" fill="#fff" stroke="{dark}" stroke-width="10"/><circle cx="500" cy="225" r="24" fill="{accent}"/></g>',
            f'<g data-scene="shelter"><path d="M330 355 500 220l170 135v125H330Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M455 480V370h90v110" fill="{accent}"/><path d="M385 355h230" stroke="{dark}" stroke-width="9"/></g>',
            f'<g data-scene="hazard-choice"><circle cx="500" cy="270" r="52" fill="{accent}"/><path d="M500 322v145M500 375 365 455M500 375l135 80" stroke="{dark}" stroke-width="16"/><circle cx="350" cy="465" r="26" fill="#fff" stroke="{dark}" stroke-width="8"/><circle cx="650" cy="465" r="26" fill="#fff" stroke="{dark}" stroke-width="8"/></g>',
        ],
        262: [
            f'<g data-scene="mori-bus"><rect x="300" y="285" width="400" height="170" rx="35" fill="#fff" stroke="{dark}" stroke-width="10"/><rect x="350" y="320" width="95" height="65" fill="{pale}" stroke="{dark}" stroke-width="7"/><rect x="465" y="320" width="95" height="65" fill="{pale}" stroke="{dark}" stroke-width="7"/><circle cx="390" cy="470" r="34" fill="{accent}"/><circle cx="610" cy="470" r="34" fill="{accent}"/></g>',
            f'<g data-scene="bus-timetable"><rect x="340" y="235" width="320" height="245" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M340 300h320M440 300v180M365 345h55M470 345h150M365 400h55M470 400h150" stroke="{accent}" stroke-width="9"/></g>',
            f'<g data-scene="hospital-route"><path d="M300 440c95-170 180 35 280-105 45-62 90-70 130-65" fill="none" stroke="{accent}" stroke-width="18"/><circle cx="310" cy="435" r="25" fill="#fff" stroke="{dark}" stroke-width="8"/><path d="M620 335v-95h90v95M665 220v135M620 275h90" stroke="{dark}" stroke-width="14"/></g>',
        ],
        263: [
            f'<g data-scene="tea-terraces"><path d="M285 455Q430 280 715 250M310 480Q470 325 735 305M360 500Q520 385 750 370" fill="none" stroke="{dark}" stroke-width="18"/><path d="M390 430q35-70 70 0M500 370q35-70 70 0M610 315q35-70 70 0" fill="none" stroke="{accent}" stroke-width="12"/></g>',
            f'<g data-scene="tea-leaf"><path d="M500 465C355 385 350 245 500 225c150 20 145 160 0 240Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M500 245v220M500 330c-50-35-85-35-115-25M500 385c55-40 95-42 125-28" stroke="{accent}" stroke-width="12"/></g>',
            f'<g data-scene="tea-route"><path d="M310 435Q400 315 495 390T700 280" fill="none" stroke="{accent}" stroke-width="18"/><path d="M285 440 365 300l85 140ZM585 440V325h125v115M565 325h165l-82-82Z" fill="#fff" stroke="{dark}" stroke-width="9"/></g>',
        ],
        246: [
            f'<g data-scene="parcel-building-tax-ledger"><path d="M270 270 420 230l90 75-45 145-180 15-55-115Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M335 250l25 205M260 355l225 55" stroke="{accent}" stroke-width="8"/><path d="M560 450V315l85-70 85 70v135Z" fill="#fff" stroke="{dark}" stroke-width="10"/><rect x="620" y="375" width="52" height="75" fill="{accent}"/></g>',
            f'<g data-scene="tax-document-three-roles"><rect x="260" y="285" width="190" height="175" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="405" y="240" width="190" height="175" rx="14" fill="{pale}" stroke="{dark}" stroke-width="9"/><rect x="550" y="195" width="190" height="175" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M295 335h120m-120 45h90m145-90h120m-120 45h90m95-90h120m-120 45h90" stroke="{accent}" stroke-width="8"/></g>',
            f'<g data-scene="shared-property-ledger"><circle cx="330" cy="295" r="38" fill="{accent}"/><circle cx="455" cy="295" r="38" fill="#fff" stroke="{dark}" stroke-width="8"/><path d="M275 420q55-105 110 0m15 0q55-105 110 0" fill="none" stroke="{dark}" stroke-width="15"/><rect x="555" y="245" width="190" height="210" rx="16" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M555 310h190M650 245v210M585 355h45m50 0h35m-130 50h45m50 0h35" stroke="{accent}" stroke-width="8"/></g>',
        ],
        269: [
            f'<g data-scene="senior-consultation-desk"><rect x="355" y="360" width="290" height="100" rx="18" fill="#fff" stroke="{dark}" stroke-width="9"/><circle cx="405" cy="270" r="38" fill="{accent}"/><circle cx="590" cy="270" r="38" fill="#fff" stroke="{dark}" stroke-width="8"/><path d="M350 365q55-105 110 0M535 365q55-105 110 0" fill="none" stroke="{dark}" stroke-width="15"/><path d="M455 385h95v58h-95Z" fill="{pale}" stroke="{accent}" stroke-width="8"/><path d="M470 405h65M470 425h45" stroke="{dark}" stroke-width="7"/></g>',
            f'<g data-scene="senior-call-and-date-log"><path d="M325 265q35-45 78-8l32 38-42 45q42 72 116 112l42-43 42 32q35 28 4 72-35 42-92 13-145-74-220-220-25-48 40-41Z" fill="#fff" stroke="{dark}" stroke-width="10"/><rect x="570" y="230" width="165" height="210" rx="18" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M570 295h165M610 230v65M695 230v65" stroke="{accent}" stroke-width="9"/><circle cx="650" cy="360" r="37" fill="{pale}" stroke="{dark}" stroke-width="8"/><path d="M650 360v-24M650 360l20 13" stroke="{accent}" stroke-width="8"/></g>',
            f'<g data-scene="senior-support-handoff"><circle cx="325" cy="390" r="42" fill="#fff" stroke="{dark}" stroke-width="9"/><circle cx="500" cy="275" r="42" fill="{accent}"/><circle cx="690" cy="390" r="42" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M365 370 455 300M540 300l105 70" fill="none" stroke="{dark}" stroke-width="14" stroke-linecap="round"/><path d="m425 315 30-15-7 31m166 6 31 33-44-3" fill="{dark}"/><rect x="430" y="405" width="145" height="78" rx="12" fill="#fff" stroke="{accent}" stroke-width="8"/><path d="M458 432h90M458 457h65" stroke="{dark}" stroke-width="7"/></g>',
        ],
        284: [
            f'<g data-scene="after-school-three-clubs"><path d="M260 450V325l105-82 105 82v125Zm270 0V325l105-82 105 82v125Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M335 450v-72h60v72m210 0v-72h60v72" fill="{accent}"/><path d="M310 325h110m160 0h110" stroke="{dark}" stroke-width="8"/><circle cx="500" cy="335" r="54" fill="{pale}" stroke="{accent}" stroke-width="10"/><path d="M500 300v70m-35-35h70" stroke="{dark}" stroke-width="12"/></g>',
            f'<g data-scene="school-term-time-columns"><rect x="270" y="235" width="460" height="235" rx="20" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M270 305h460M385 235v235M500 235v235M615 235v235" stroke="{dark}" stroke-width="8"/><circle cx="328" cy="365" r="34" fill="{pale}" stroke="{accent}" stroke-width="9"/><path d="M328 365v-22m0 22 18 12" stroke="{dark}" stroke-width="8"/><path d="M420 350h45v75h-45Zm115-30h45v105h-45Zm115-60h45v165h-45" fill="{accent}" opacity=".8"/></g>',
            f'<g data-scene="guardian-pickup-route"><path d="M275 425q95-165 205-40t240-125" fill="none" stroke="{accent}" stroke-width="20"/><path d="M255 445V345l75-60 75 60v100Z" fill="#fff" stroke="{dark}" stroke-width="10"/><rect x="305" y="385" width="45" height="60" fill="{accent}"/><path d="M600 430V300h135v130M575 300h185l-92-72Z" fill="#fff" stroke="{dark}" stroke-width="10"/><circle cx="475" cy="385" r="28" fill="#fff" stroke="{dark}" stroke-width="8"/><circle cx="525" cy="335" r="22" fill="{accent}"/><path d="M495 365 515 350" stroke="{dark}" stroke-width="9"/></g>',
        ],
        286: [
            f'<g data-scene="public-facility-reservation-board"><path d="M290 455V305h175v150M265 305h225l-112-90Z" fill="#fff" stroke="{dark}" stroke-width="10"/><rect x="520" y="235" width="220" height="225" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M520 300h220M575 235v65M685 235v65" stroke="{accent}" stroke-width="9"/><path d="M555 335h42v42h-42Zm55 0h42v42h-42Zm55 0h42v42h-42Zm-110 55h42v42h-42Zm55 0h42v42h-42" fill="{pale}" stroke="{dark}" stroke-width="6"/><path d="m670 408 17 17 36-48" fill="none" stroke="{accent}" stroke-width="11"/></g>',
            f'<g data-scene="facility-room-capacity-layout"><rect x="280" y="225" width="440" height="245" rx="16" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M500 225v245M280 315h440" stroke="{accent}" stroke-width="8"/><rect x="315" y="255" width="150" height="35" rx="8" fill="{pale}" stroke="{dark}" stroke-width="6"/><circle cx="340" cy="365" r="18" fill="{accent}"/><circle cx="405" cy="365" r="18" fill="{accent}"/><circle cx="340" cy="420" r="18" fill="{accent}"/><circle cx="405" cy="420" r="18" fill="{accent}"/><path d="M550 350h120v85H550Z" fill="{pale}" stroke="{dark}" stroke-width="8"/><path d="M570 375h80M570 405h55" stroke="{accent}" stroke-width="7"/></g>',
            f'<g data-scene="reservation-counter-key-route"><rect x="270" y="250" width="170" height="205" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M305 300h100M305 345h78M305 390h95" stroke="{accent}" stroke-width="8"/><path d="M455 355h105m-38-35 38 35-38 35" fill="none" stroke="{dark}" stroke-width="13"/><path d="M595 420v-95h145v95" fill="#fff" stroke="{dark}" stroke-width="10"/><circle cx="635" cy="300" r="38" fill="{pale}" stroke="{accent}" stroke-width="9"/><path d="M673 300h80v25h-26v28h-28v-28h-26" fill="none" stroke="{dark}" stroke-width="12"/></g>',
        ],
        208: [
            f'<g data-scene="town-history-routing-table"><path d="M265 450h470M330 490V225" stroke="{dark}" stroke-width="12"/><path d="M330 390h360M330 320h300M330 250h230" stroke="{accent}" stroke-width="10"/><rect x="360" y="360" width="100" height="55" rx="10" fill="#fff" stroke="{dark}" stroke-width="7"/><rect x="500" y="290" width="100" height="55" rx="10" fill="{pale}" stroke="{dark}" stroke-width="7"/><rect x="640" y="220" width="100" height="55" rx="10" fill="#fff" stroke="{dark}" stroke-width="7"/><path d="m445 345 28-25-28-25m140-20 28-25-28-25" fill="none" stroke="{accent}" stroke-width="9"/></g>',
            f'<g data-scene="town-history-period-volume-lanes"><path d="M255 445h490" stroke="{dark}" stroke-width="12"/><circle cx="300" cy="445" r="18" fill="{accent}"/><circle cx="430" cy="445" r="18" fill="{accent}"/><circle cx="560" cy="445" r="18" fill="{accent}"/><circle cx="700" cy="445" r="18" fill="{accent}"/><rect x="260" y="235" width="95" height="145" rx="12" fill="#fff" stroke="{dark}" stroke-width="8"/><rect x="390" y="235" width="95" height="145" rx="12" fill="{pale}" stroke="{dark}" stroke-width="8"/><rect x="520" y="235" width="95" height="145" rx="12" fill="#fff" stroke="{dark}" stroke-width="8"/><rect x="655" y="235" width="95" height="145" rx="12" fill="{pale}" stroke="{dark}" stroke-width="8"/><path d="M310 380v45M440 380v45M570 380v45M705 380v45" stroke="{accent}" stroke-width="9"/><g font-family="sans-serif" font-size="20" font-weight="700" fill="{dark}" text-anchor="middle"><text x="307" y="315">資料編1</text><text x="437" y="315">資料編2</text><text x="567" y="315">資料編3</text><text x="702" y="315">資料編4</text><text x="360" y="195">通史</text><text x="500" y="195">資料編5</text><text x="640" y="195">別冊</text></g></g>',
            f'<g data-scene="town-history-question-sorter"><rect x="250" y="220" width="500" height="110" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M300 330v105M400 330v105M500 330v105M600 330v105M700 330v105" stroke="{accent}" stroke-width="10"/><path d="m280 405 20 24 20-24m60 0 20 24 20-24m60 0 20 24 20-24m60 0 20 24 20-24m60 0 20 24 20-24" fill="none" stroke="{dark}" stroke-width="9"/><rect x="260" y="448" width="80" height="48" rx="8" fill="{pale}"/><rect x="360" y="448" width="80" height="48" rx="8" fill="#fff" stroke="{dark}" stroke-width="6"/><rect x="460" y="448" width="80" height="48" rx="8" fill="{pale}"/><rect x="560" y="448" width="80" height="48" rx="8" fill="#fff" stroke="{dark}" stroke-width="6"/><rect x="660" y="448" width="80" height="48" rx="8" fill="{pale}"/><g font-family="sans-serif" font-size="16" font-weight="700" fill="{dark}" text-anchor="middle"><text x="300" y="270">検地帳</text><text x="400" y="270">舞楽</text><text x="500" y="270">棟札</text><text x="600" y="270">古写真</text><text x="700" y="270">家文書</text><text x="300" y="478">資料編3</text><text x="400" y="478">資料編5</text><text x="500" y="478">別冊</text><text x="600" y="478">図説</text><text x="700" y="478">目録</text></g></g>',
        ],
        209: [
            f'<g data-scene="library-call-number-card"><rect x="270" y="255" width="175" height="220" rx="14" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M310 300h95M310 345h70M310 390h90" stroke="{accent}" stroke-width="9"/><path d="M500 235h225v240H500Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M550 235v240M615 235v240M680 235v240" stroke="{accent}" stroke-width="8"/></g>',
            f'<g data-scene="catalog-shelf-page-route"><rect x="245" y="275" width="150" height="150" rx="16" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M395 350h100m-28-28 28 28-28 28" fill="none" stroke="{accent}" stroke-width="12"/><path d="M535 235h210v220H535Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M575 280h130M575 330h105M575 380h120" stroke="{accent}" stroke-width="9"/></g>',
            f'<g data-scene="family-local-history-index"><path d="M270 250h220v210H270Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M310 300h140M310 350h115M310 400h130" stroke="{accent}" stroke-width="9"/><path d="M540 420V300l85-70 85 70v120Z" fill="#fff" stroke="{dark}" stroke-width="10"/><circle cx="625" cy="350" r="35" fill="{pale}" stroke="{accent}" stroke-width="9"/></g>',
        ],
        212: [
            f'<g data-scene="old-map-place-name-crosswalk"><path d="M255 245 430 210l120 70-45 180-205 20Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M330 225l35 245M255 355l270 55" stroke="{accent}" stroke-width="8"/><path d="M570 260h175v195H570Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M605 310h105M605 355h85M605 400h100" stroke="{accent}" stroke-width="9"/><path d="M520 350h50" stroke="{dark}" stroke-width="14"/></g>',
            f'<g data-scene="landmark-to-current-map"><path d="M260 265 430 225l90 85-55 155-185 10Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M335 245l35 220M265 370l230 55" stroke="{accent}" stroke-width="8"/><circle cx="390" cy="335" r="25" fill="{dark}"/><path d="M530 345h95m-32-30 32 30-32 30" fill="none" stroke="{accent}" stroke-width="13"/><path d="M650 280h105v165H650Z" fill="#fff" stroke="{dark}" stroke-width="9"/><circle cx="702" cy="355" r="30" fill="{pale}" stroke="{accent}" stroke-width="8"/></g>',
            f'<g data-scene="place-name-confidence-ledger"><rect x="270" y="245" width="460" height="225" rx="16" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M270 315h460M430 245v225M580 245v225" stroke="{accent}" stroke-width="8"/><circle cx="350" cy="365" r="24" fill="{accent}"/><circle cx="505" cy="365" r="24" fill="{pale}" stroke="{dark}" stroke-width="7"/><circle cx="655" cy="365" r="24" fill="#fff" stroke="{dark}" stroke-width="7"/><path d="M320 425h60M475 425h60M625 425h60" stroke="{dark}" stroke-width="9"/></g>',
        ],
        219: [
            f'<g data-scene="statistics-date-unit-notes"><rect x="275" y="240" width="450" height="235" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M275 310h450M425 240v235M575 240v235" stroke="{accent}" stroke-width="8"/><circle cx="350" cy="380" r="30" fill="{pale}" stroke="{dark}" stroke-width="8"/><path d="M470 360h60M470 400h60M620 360h60M620 400h60" stroke="{dark}" stroke-width="9"/></g>',
            f'<g data-scene="statistics-three-table-scope"><rect x="250" y="285" width="190" height="175" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="405" y="240" width="190" height="175" fill="{pale}" stroke="{dark}" stroke-width="9"/><rect x="560" y="195" width="190" height="175" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M285 330h120M440 285h120M595 240h120" stroke="{accent}" stroke-width="9"/></g>',
            f'<g data-scene="statistics-citation-card"><path d="M280 265h280v200H280Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M320 315h200M320 360h165M320 405h185" stroke="{accent}" stroke-width="9"/><path d="M610 240v220M575 280h145M575 350h145M575 420h145" stroke="{dark}" stroke-width="10"/><circle cx="610" cy="350" r="24" fill="{accent}"/></g>',
        ],
        230: [
            f'<g data-scene="inheritance-document-purpose-map"><rect x="255" y="255" width="190" height="205" rx="14" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M295 305h110M295 350h85M295 395h100" stroke="{accent}" stroke-width="9"/><path d="M445 355h95" stroke="{dark}" stroke-width="14"/><path d="M540 355 630 285M540 355l90 70" stroke="{accent}" stroke-width="13"/><rect x="630" y="225" width="135" height="115" rx="12" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="630" y="380" width="135" height="115" rx="12" fill="{pale}" stroke="{dark}" stroke-width="9"/></g>',
            f'<g data-scene="inheritance-office-acceptance-gates"><rect x="240" y="270" width="170" height="170" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M280 315h90M280 360h70M280 405h85" stroke="{accent}" stroke-width="8"/><path d="M410 355h105" stroke="{dark}" stroke-width="13"/><path d="M515 355 600 285M515 355l85 70" stroke="{accent}" stroke-width="12"/><rect x="600" y="225" width="170" height="120" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="600" y="375" width="170" height="120" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M625 275h120M625 425h120" stroke="{accent}" stroke-width="8"/><circle cx="600" cy="285" r="18" fill="{accent}"/><circle cx="600" cy="435" r="18" fill="{accent}"/></g>',
            f'<g data-scene="original-copy-return-ledger"><rect x="260" y="245" width="480" height="225" rx="16" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M260 315h480M420 245v225M580 245v225" stroke="{accent}" stroke-width="8"/><path d="M300 365h80M460 365h80M620 365h80M300 415h80M460 415h80M620 415h80" stroke="{dark}" stroke-width="8"/><path d="m342 285 18 18 35-42m107 24 18 18 35-42m107 24 18 18 35-42" fill="none" stroke="{accent}" stroke-width="9"/></g>',
        ],
        253: [
            f'<g data-scene="hazard-map-property-date"><path d="M260 270 430 225l95 85-60 150-185 10Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M335 250l40 205M270 365l230 55" stroke="{accent}" stroke-width="8"/><rect x="575" y="245" width="165" height="210" rx="16" fill="#fff" stroke="{dark}" stroke-width="9"/><circle cx="658" cy="355" r="45" fill="{pale}" stroke="{accent}" stroke-width="10"/></g>',
            f'<g data-scene="hazard-map-district-zoom"><rect x="270" y="235" width="220" height="220" fill="#fff" stroke="{dark}" stroke-width="10"/><rect x="570" y="285" width="170" height="170" fill="{pale}" stroke="{dark}" stroke-width="10"/><circle cx="470" cy="330" r="65" fill="none" stroke="{accent}" stroke-width="14"/><path d="M515 375l80 70" stroke="{accent}" stroke-width="18"/></g>',
            f'<g data-scene="hazard-map-version-timeline"><rect x="250" y="260" width="185" height="180" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="565" y="230" width="185" height="210" rx="14" fill="{pale}" stroke="{dark}" stroke-width="9"/><path d="M435 350h130m-35-30 35 30-35 30" fill="none" stroke="{accent}" stroke-width="14"/><path d="M290 310h105M605 285h105M605 335h105" stroke="{dark}" stroke-width="8"/></g>',
        ],
        280: [
            f'<g data-scene="family-checkin-network"><path d="M420 430V315l80-65 80 65v115Z" fill="#fff" stroke="{dark}" stroke-width="10"/><circle cx="275" cy="300" r="34" fill="{accent}"/><circle cx="725" cy="300" r="34" fill="{pale}" stroke="{dark}" stroke-width="8"/><circle cx="500" cy="190" r="34" fill="#fff" stroke="{dark}" stroke-width="8"/><path d="M305 310l115 55M695 310l-115 55M500 224v26" stroke="{accent}" stroke-width="12"/></g>',
            f'<g data-scene="three-level-watch-plan"><circle cx="300" cy="350" r="42" fill="#fff" stroke="{dark}" stroke-width="9"/><circle cx="500" cy="350" r="42" fill="{pale}" stroke="{dark}" stroke-width="9"/><circle cx="700" cy="350" r="42" fill="{accent}"/><path d="M342 350h116m84 0h116" stroke="{dark}" stroke-width="14"/><path d="m430 325 28 25-28 25m200-50 28 25-28 25" fill="none" stroke="{accent}" stroke-width="10"/></g>',
            f'<g data-scene="emergency-kit-support-route"><rect x="250" y="285" width="170" height="180" rx="14" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M285 330h100M285 375h75" stroke="{accent}" stroke-width="9"/><path d="M420 375h120" stroke="{dark}" stroke-width="14"/><circle cx="600" cy="300" r="38" fill="{accent}"/><path d="M600 338v115M545 453h110M600 385h130" stroke="{dark}" stroke-width="14"/></g>',
        ],
        291: [
            f'<g data-scene="inherited-farmland-parcel-map"><path d="M275 255 430 220l80 95-72 145-168-45Zm235 60 115-92 115 50-28 142-150 45-124-5Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M350 238l35 202M510 315l202 100M625 223l-63 237" stroke="{accent}" stroke-width="8"/><circle cx="500" cy="190" r="29" fill="{accent}"/><circle cx="445" cy="145" r="23" fill="#fff" stroke="{dark}" stroke-width="7"/><circle cx="555" cy="145" r="23" fill="#fff" stroke="{dark}" stroke-width="7"/><path d="M500 175 460 155M500 175l40-20" stroke="{dark}" stroke-width="8"/></g>',
            f'<g data-scene="registry-to-farmland-crosscheck"><rect x="275" y="245" width="215" height="205" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M310 300h145M310 345h110M310 390h130" stroke="{accent}" stroke-width="8"/><path d="M545 250 705 225l55 90-42 135-185 10-48-105Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M600 242l15 207M545 330l194 65" stroke="{accent}" stroke-width="8"/><circle cx="520" cy="365" r="65" fill="none" stroke="{dark}" stroke-width="12"/><path d="M565 412l70 65" stroke="{dark}" stroke-width="17" stroke-linecap="round"/></g>',
            f'<g data-scene="parcel-heir-verification-route"><circle cx="300" cy="360" r="34" fill="#fff" stroke="{dark}" stroke-width="8"/><circle cx="300" cy="265" r="25" fill="{accent}"/><circle cx="245" cy="215" r="20" fill="#fff" stroke="{dark}" stroke-width="7"/><circle cx="355" cy="215" r="20" fill="#fff" stroke="{dark}" stroke-width="7"/><path d="M300 240 260 222M300 240l40-18M335 350h120" stroke="{dark}" stroke-width="10"/><path d="m425 322 32 28-32 28" fill="none" stroke="{accent}" stroke-width="10"/><path d="M480 275 620 235l115 70-30 135-175 25-75-95Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M550 255l-20 210M620 235l85 205M480 355l245-15" stroke="{accent}" stroke-width="8"/><circle cx="650" cy="365" r="26" fill="{dark}"/></g>',
        ],
        292: [
            f'<g data-scene="farmland-transfer-parties"><path d="M260 455Q420 300 740 265M285 495Q455 350 760 330" fill="none" stroke="{dark}" stroke-width="18"/><path d="M355 420q35-72 70 0M520 350q35-72 70 0M650 305q35-72 70 0" fill="none" stroke="{accent}" stroke-width="12"/><circle cx="300" cy="245" r="34" fill="{accent}"/><circle cx="700" cy="245" r="34" fill="#fff" stroke="{dark}" stroke-width="8"/><rect x="405" y="220" width="190" height="150" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M440 265h120M440 310h95" stroke="{accent}" stroke-width="8"/><path d="M330 260l75 35m265-35-75 35" stroke="{dark}" stroke-width="10"/></g>',
            f'<g data-scene="farmland-rights-parcel-branches"><path d="M260 270 425 225l105 85-55 155-195 10Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M335 245l35 220M265 370l235 55" stroke="{accent}" stroke-width="8"/><rect x="565" y="205" width="175" height="80" rx="12" fill="#fff" stroke="{dark}" stroke-width="8"/><rect x="565" y="325" width="175" height="80" rx="12" fill="{pale}" stroke="{dark}" stroke-width="8"/><rect x="565" y="445" width="175" height="80" rx="12" fill="#fff" stroke="{dark}" stroke-width="8"/><path d="M500 350 565 245M500 350h65M500 350l65 135" stroke="{dark}" stroke-width="12"/><circle cx="500" cy="350" r="22" fill="{accent}"/><g font-family="sans-serif" font-size="19" font-weight="700" fill="{dark}" text-anchor="middle"><text x="335" y="310">地番</text><text x="390" y="370">登記地目</text><text x="405" y="430">現況地目</text><text x="652" y="255">所有権</text><text x="652" y="375">賃借権</text><text x="652" y="495">使用貸借</text></g></g>',
            f'<g data-scene="farmland-deadline-field-meeting-calendar"><rect x="250" y="230" width="500" height="240" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M250 300h500M415 230v240M585 230v240" stroke="{accent}" stroke-width="8"/><circle cx="330" cy="370" r="34" fill="{pale}" stroke="{dark}" stroke-width="8"/><path d="M500 338v70m-35-35h70" stroke="{dark}" stroke-width="14"/><path d="M645 405V330l48-38 48 38v75Z" fill="{pale}" stroke="{dark}" stroke-width="8"/><path d="m305 420 24 24 50-65" fill="none" stroke="{accent}" stroke-width="11"/><g font-family="sans-serif" font-size="20" font-weight="700" fill="{dark}" text-anchor="middle"><text x="332" y="275">締切</text><text x="500" y="275">現地調査</text><text x="668" y="275">農業委員会</text></g></g>',
        ],
        191: [
            f'<g data-scene="corporate-tax-single-file-route"><rect x="230" y="250" width="540" height="210" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M230 320h540M365 250v210M500 250v210M635 250v210" stroke="{accent}" stroke-width="8"/><path d="M285 370h70M420 370h70M555 370h70M690 370h55" stroke="{dark}" stroke-width="9"/><path d="M300 415h420" stroke="{accent}" stroke-width="13"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="298" y="292">設立届</text><text x="432" y="292">初回申告</text><text x="568" y="292">納付</text><text x="702" y="292">異動届</text></g></g>',
            f'<g data-scene="office-opening-fact-sheet"><path d="M250 430V300l110-85 110 85v130Z" fill="#fff" stroke="{dark}" stroke-width="10"/><rect x="525" y="225" width="235" height="235" rx="16" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M560 285h165M560 335h135M560 385h155" stroke="{accent}" stroke-width="9"/><path d="M360 215v-55h130v90" fill="none" stroke="{dark}" stroke-width="10"/><g font-family="sans-serif" font-size="17" font-weight="700" fill="{dark}" text-anchor="middle"><text x="642" y="275">登記事項</text><text x="642" y="325">定款</text><text x="642" y="375">事業年度</text><text x="642" y="425">事務所設置日</text></g></g>',
            f'<g data-scene="filing-payment-change-loop"><rect x="250" y="255" width="150" height="125" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="600" y="255" width="150" height="125" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="425" y="405" width="150" height="95" rx="14" fill="{pale}" stroke="{dark}" stroke-width="9"/><path d="M400 315h200m-35-30 35 30-35 30M670 380q-15 95-95 95M425 455q-95-10-100-75" fill="none" stroke="{accent}" stroke-width="13"/><g font-family="sans-serif" font-size="19" font-weight="700" fill="{dark}" text-anchor="middle"><text x="325" y="325">申告</text><text x="675" y="325">納付</text><text x="500" y="463">異動届</text></g></g>',
        ],
        103: [
            f'<g data-scene="septic-record-handover-desk"><path d="M245 430V305l105-82 105 82v125Z" fill="#fff" stroke="{dark}" stroke-width="10"/><ellipse cx="350" cy="450" rx="105" ry="42" fill="{pale}" stroke="{accent}" stroke-width="10"/><rect x="525" y="235" width="235" height="225" rx="16" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M560 295h165M560 345h145M560 395h155" stroke="{accent}" stroke-width="9"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="642" y="285">設備票</text><text x="642" y="335">保守点検</text><text x="642" y="385">法定検査</text></g></g>',
            f'<g data-scene="septic-equipment-identification"><path d="M245 455V300l105-80 105 80v155Z" fill="#fff" stroke="{dark}" stroke-width="10"/><rect x="515" y="250" width="245" height="205" rx="95" fill="#fff" stroke="{dark}" stroke-width="10"/><ellipse cx="575" cy="290" rx="35" ry="18" fill="{pale}" stroke="{accent}" stroke-width="8"/><ellipse cx="685" cy="290" rx="35" ry="18" fill="{pale}" stroke="{accent}" stroke-width="8"/><path d="M630 250v205M550 360h160" stroke="{accent}" stroke-width="8"/><g font-family="sans-serif" font-size="17" font-weight="700" fill="{dark}" text-anchor="middle"><text x="630" y="342">合併・単独</text><text x="585" y="405">人槽</text><text x="685" y="405">設置年</text></g></g>',
            f'<g data-scene="maintenance-and-manager-change-route"><rect x="240" y="230" width="185" height="90" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="240" y="360" width="185" height="90" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="575" y="230" width="185" height="90" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="575" y="360" width="185" height="90" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><circle cx="500" cy="340" r="38" fill="{accent}"/><path d="M425 275l75 50m-75 80 75-50m75-80-75 50m75 80-75-50" stroke="{dark}" stroke-width="12"/><g font-family="sans-serif" font-size="17" font-weight="700" fill="{dark}" text-anchor="middle"><text x="332" y="270">管理者変更</text><text x="332" y="292">報告</text><text x="332" y="410">契約名義</text><text x="668" y="270">保守・清掃</text><text x="668" y="292">法定検査</text><text x="668" y="410">一年予定表</text></g></g>',
        ],
        162: [
            f'<g data-scene="twelve-month-farmland-calendar"><rect x="235" y="215" width="530" height="270" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M235 285h530M235 352h530M235 419h530M367 215v270M500 215v270M633 215v270" stroke="{accent}" stroke-width="7"/><g font-family="sans-serif" font-size="17" font-weight="700" fill="{dark}" text-anchor="middle"><text x="301" y="258">4月</text><text x="434" y="258">5月</text><text x="566" y="258">6月</text><text x="699" y="258">7月</text><text x="301" y="326">8月</text><text x="434" y="326">9月</text><text x="566" y="326">10月</text><text x="699" y="326">11月</text><text x="301" y="393">12月</text><text x="434" y="393">1月</text><text x="566" y="393">2月</text><text x="699" y="393">3月</text></g></g>',
            f'<g data-scene="four-column-calendar-desk"><rect x="240" y="235" width="520" height="235" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M240 305h520M370 235v235M500 235v235M630 235v235" stroke="{accent}" stroke-width="8"/><path d="M275 355h60M405 355h60M535 355h60M665 355h60M275 410h60M405 410h60M535 410h60M665 410h60" stroke="{dark}" stroke-width="8"/><g font-family="sans-serif" font-size="17" font-weight="700" fill="{dark}" text-anchor="middle"><text x="305" y="280">締切</text><text x="435" y="280">発送</text><text x="565" y="280">現地調査</text><text x="695" y="280">総会</text></g></g>',
            f'<g data-scene="planned-actual-version-archive"><rect x="235" y="255" width="170" height="160" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="415" y="305" width="170" height="160" rx="14" fill="{pale}" stroke="{dark}" stroke-width="9"/><rect x="595" y="235" width="170" height="180" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M405 335h10M585 355h10" stroke="{accent}" stroke-width="13"/><g font-family="sans-serif" font-size="19" font-weight="700" fill="{dark}" text-anchor="middle"><text x="320" y="325">予定表</text><text x="500" y="375">実績表</text><text x="680" y="300">変更確認</text><text x="680" y="355">次年度版</text></g></g>',
        ],
        21: [
            f'<g data-scene="mori-pregnancy-checkup-ticket-ledger"><path d="M180 438 300 260l96 104 92-146 116 151 90-104 126 173" fill="none" stroke="{dark}" stroke-width="18" stroke-linejoin="round"/><path d="M180 466h640" stroke="{accent}" stroke-width="14"/><rect x="245" y="250" width="170" height="190" rx="18" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M275 305h110M275 350h110M275 395h80" stroke="{accent}" stroke-width="8"/><rect x="585" y="245" width="175" height="198" rx="18" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M585 302h175M625 245v198" stroke="{accent}" stroke-width="8"/><circle cx="505" cy="335" r="45" fill="{pale}" stroke="{dark}" stroke-width="9"/><path d="M505 310v50m-25-25h50" stroke="{accent}" stroke-width="11"/></g>',
            f'<g data-scene="pregnancy-week-clinic-ticket-route"><path d="M175 425Q335 225 500 345T825 260" fill="none" stroke="{dark}" stroke-width="18"/><circle cx="250" cy="345" r="35" fill="{accent}"/><circle cx="475" cy="330" r="35" fill="{pale}" stroke="{dark}" stroke-width="8"/><circle cx="700" cy="315" r="35" fill="{accent}"/><path d="M760 420V300l80-62 80 62v120Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M840 320v70M805 355h70" stroke="{accent}" stroke-width="11"/><rect x="170" y="210" width="160" height="75" rx="12" fill="#fff" stroke="{dark}" stroke-width="8"/><rect x="390" y="190" width="170" height="75" rx="12" fill="#fff" stroke="{dark}" stroke-width="8"/><rect x="610" y="175" width="180" height="75" rx="12" fill="#fff" stroke="{dark}" stroke-width="8"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="250" y="257">通常受診票</text><text x="475" y="237">超音波等</text><text x="700" y="222">多胎追加票</text></g></g>',
            f'<g data-scene="unused-ticket-receipt-refund-route"><path d="M180 390V285l75-58 75 58v105Z" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M255 315v55M228 342h55" stroke="{accent}" stroke-width="10"/><rect x="385" y="215" width="165" height="225" rx="16" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M415 275h105M415 325h105M415 375h80" stroke="{accent}" stroke-width="8"/><rect x="670" y="265" width="165" height="155" rx="16" fill="{pale}" stroke="{dark}" stroke-width="9"/><path d="M550 325h120m-35-30 35 30-35 30" fill="none" stroke="{accent}" stroke-width="12"/><circle cx="610" cy="455" r="46" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M610 455v-28M610 455l24 18" stroke="{accent}" stroke-width="9"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="255" y="445">県外受診</text><text x="468" y="475">未使用票・領収書</text><text x="752" y="330">森町へ申請</text><text x="752" y="372">出産月から一年</text></g></g>',
        ],
        24: [
            f'<g data-scene="newborn-insurance-medical-aid-handover"><path d="M170 445 300 270l110 120 95-165 135 165 95-115 115 170" fill="none" stroke="{dark}" stroke-width="18"/><path d="M170 470h660" stroke="{accent}" stroke-width="14"/><circle cx="500" cy="330" r="58" fill="{pale}" stroke="{dark}" stroke-width="9"/><circle cx="500" cy="312" r="20" fill="{accent}"/><path d="M465 375q35-48 70 0" fill="none" stroke="{dark}" stroke-width="11"/><rect x="225" y="270" width="170" height="145" rx="16" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M255 320h110M255 365h90" stroke="{accent}" stroke-width="8"/><rect x="610" y="260" width="180" height="160" rx="16" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M610 315h180M660 260v160" stroke="{accent}" stroke-width="8"/></g>',
            f'<g data-scene="newborn-two-insurance-branches"><path d="M190 430V315l85-68 85 68v115Z" fill="#fff" stroke="{dark}" stroke-width="10"/><circle cx="275" cy="350" r="28" fill="{accent}"/><path d="M360 365Q470 210 575 300M360 385Q490 475 620 390" fill="none" stroke="{accent}" stroke-width="14"/><rect x="560" y="205" width="210" height="120" rx="16" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="620" y="370" width="215" height="120" rx="16" fill="{pale}" stroke="{dark}" stroke-width="9"/><path d="M600 255h130M660 420h135" stroke="{accent}" stroke-width="8"/><g font-family="sans-serif" font-size="19" font-weight="700" fill="{dark}" text-anchor="middle"><text x="665" y="285">森町国保</text><text x="727" y="455">勤務先等の保険</text></g></g>',
            f'<g data-scene="newborn-receipt-reimbursement-route"><path d="M165 405V285l80-62 80 62v120Z" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M245 312v65M212 345h66" stroke="{accent}" stroke-width="10"/><rect x="385" y="220" width="175" height="225" rx="16" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M420 280h105M420 330h105M420 380h82" stroke="{accent}" stroke-width="8"/><path d="M560 335h105m-35-30 35 30-35 30" fill="none" stroke="{accent}" stroke-width="12"/><rect x="665" y="260" width="180" height="165" rx="16" fill="{pale}" stroke="{dark}" stroke-width="9"/><circle cx="755" cy="470" r="45" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M755 470v-27M755 470l24 17" stroke="{accent}" stroke-width="9"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="245" y="455">県外医療機関</text><text x="472" y="485">領収書・資格情報</text><text x="755" y="325">森町へ申請</text><text x="755" y="370">受診日から一年</text></g></g>',
        ],
        91: [
            f'<g data-scene="license-return-two-subsidy-ledger"><rect x="220" y="235" width="250" height="235" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><rect x="530" y="235" width="250" height="235" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M250 315h190M560 315h190M250 385h190M560 385h190" stroke="{accent}" stroke-width="8"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="345" y="278">経歴証明書助成</text><text x="655" y="278">交通利用券助成</text><text x="345" y="355">交付日から1年</text><text x="655" y="355">購入日から3か月</text><text x="345" y="430">危機管理課</text><text x="655" y="430">保健福祉課</text></g></g>',
            f'<g data-scene="subsidy-two-starting-dates"><circle cx="335" cy="340" r="105" fill="#fff" stroke="{dark}" stroke-width="10"/><circle cx="665" cy="340" r="105" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M335 340V275M335 340l55 30M665 340V285M665 340l-45 55" stroke="{accent}" stroke-width="13" stroke-linecap="round"/><path d="M440 340h120" stroke="{dark}" stroke-width="10" stroke-dasharray="15 12"/><g font-family="sans-serif" font-size="20" font-weight="700" fill="{dark}" text-anchor="middle"><text x="335" y="500">経歴証明書交付日</text><text x="665" y="500">利用券購入日</text></g></g>',
            f'<g data-scene="subsidy-evidence-account-route"><rect x="215" y="245" width="185" height="105" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="215" y="395" width="185" height="105" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="600" y="245" width="185" height="105" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="600" y="395" width="185" height="105" rx="14" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="435" y="315" width="130" height="115" rx="14" fill="{pale}" stroke="{dark}" stroke-width="9"/><path d="M400 300l35 55M400 445l35-55M565 355l35-55M565 390l35 55" stroke="{accent}" stroke-width="11"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="307" y="308">領収証</text><text x="307" y="458">交付資料</text><text x="500" y="375">申請台帳</text><text x="692" y="308">口座</text><text x="692" y="458">担当課</text></g></g>',
        ],
        180: [
            f'<g data-scene="forest-three-deadline-workflow"><rect x="190" y="265" width="190" height="150" rx="16" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="405" y="265" width="190" height="150" rx="16" fill="{pale}" stroke="{dark}" stroke-width="9"/><rect x="620" y="265" width="190" height="150" rx="16" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M380 340h25M595 340h25" stroke="{accent}" stroke-width="13"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="285" y="305">伐採届</text><text x="285" y="350">開始90〜30日前</text><text x="500" y="305">伐採完了報告</text><text x="500" y="350">完了後30日</text><text x="715" y="305">造林完了報告</text><text x="715" y="350">完了後30日</text></g></g>',
            f'<g data-scene="forest-parcel-method-reforestation-sheet"><path d="M205 445 315 255l110 190Z" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M285 445 395 235l110 210Z" fill="{pale}" stroke="{dark}" stroke-width="10"/><rect x="555" y="225" width="235" height="245" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M590 290h165M590 350h165M590 410h165" stroke="{accent}" stroke-width="9"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="672" y="278">対象地番</text><text x="672" y="338">伐採方法</text><text x="672" y="398">造林方法</text><text x="672" y="452">面積</text></g></g>',
            f'<g data-scene="forest-planned-actual-report-archive"><rect x="205" y="250" width="180" height="210" rx="16" fill="#fff" stroke="{dark}" stroke-width="9"/><rect x="410" y="250" width="180" height="210" rx="16" fill="{pale}" stroke="{dark}" stroke-width="9"/><rect x="615" y="250" width="180" height="210" rx="16" fill="#fff" stroke="{dark}" stroke-width="9"/><path d="M385 355h25M590 355h25" stroke="{accent}" stroke-width="13"/><path d="m245 390 30 30 65-80M450 390l30 30 65-80M655 390l30 30 65-80" fill="none" stroke="{dark}" stroke-width="11"/><g font-family="sans-serif" font-size="18" font-weight="700" fill="{dark}" text-anchor="middle"><text x="295" y="305">届出計画</text><text x="500" y="305">伐採実績</text><text x="705" y="305">造林実績</text></g></g>',
        ],
    }
    special_labels = {
        81: ["林野火災・二枚の確認票", "林野火災・発令時は中止", "林野火災・安全から119番"],
        80: ["火災警報器・部屋別台帳", "火災警報器・音と製造年", "火災警報器・交換と支援"],
        70: ["国保税・産前産後の対象月", "国保税・単胎と多胎", "国保税・届出から通知"],
        60: ["国保葬祭費・一件表", "国保葬祭費・役割を分ける", "国保葬祭費・受付から入金"],
        64: ["療養費・申請束の一件表", "療養費・五つの支払理由", "療養費・受付から入金"],
        65: ["事故後の四本線", "届出書を役割別に", "示談前に町へ相談"],
        57: ["高額療養費・暦月台帳", "年齢別の計算順", "申請と支給月をつなぐ"],
        20: ["町届出と滅失登記へ", "壊した棟と残す棟", "翌年度明細まで確認"],
        21: ["受診票を一回一行へ", "週数と票を分ける", "未使用票を申請へ"],
        24: ["保険加入から受給者証へ", "加入先を先に決める", "領収書を払い戻しへ"],
        1: ["離婚成立日で分ける", "四論点を別欄へ", "期限と確認先を分ける"],
        168: ["所有・現在・将来・更新日", "番号を一覧へつなぐ", "版と将来像を分ける"],
        172: ["購入前の安全配置図", "公共境界と注意表示", "電源と点検動線"],
        91: ["返納助成・二つの期限", "返納助成・二つの起算日", "返納助成・証憑と口座"],
        180: ["森林伐採・三つの期限", "森林伐採・地番と方法", "森林伐採・予定と実績"],
        149: ["接道確認・四本の線", "接道確認・GISと現地", "接道確認・図面の版"],
        159: ["土地価格・比較条件カード", "土地価格・種類と期間", "土地価格・質問へ変換"],
        166: ["農地転用・許可後の着工前", "農地転用・図面を重ねる", "農地転用・進捗と完了"],
        176: ["森林届・全対象筆の位置図", "森林届・地図の出典", "森林届・地番と図番"],
        249: ["固定資産・証明書ルート", "固定資産・必要項目から選ぶ", "固定資産・年度と範囲"],
        288: ["施設修繕・証拠段階索引", "施設修繕・直し方を分ける", "施設修繕・予定から完了"],
        190: ["看板設置・二つの制度確認", "場所・寸法・色を固定", "広告物と建築行為を分ける"],
        194: ["入札参加・四段階確認", "受注内容から区分を選ぶ", "名簿の次に電子登録"],
        17: ["戸籍フリガナ・家族別判定表", "戸籍フリガナ・氏と名の担当", "戸籍フリガナ・三時点照合"],
        207: ["古写真・原本と来歴", "古写真・撮影時期と場所", "古写真・権利と公開範囲"],
        208: ["森町史・最初の一冊", "森町史・年代と巻の分岐", "森町史・問いから巻へ"],
        209: ["郷土資料・請求記号", "郷土資料・書架からページ", "郷土資料・家族の索引"],
        212: ["古地名・原表記と現在候補", "古地名・目印の照合", "古地名・確度と確認先"],
        219: ["森町統計・基準日と単位", "森町統計・表の範囲", "森町統計・引用カード"],
        230: ["相続書類・用途を分ける", "相続書類・受入可否を確認", "相続書類・原本と返却"],
        253: ["防災地図・版の日付", "防災地図・地区図の照合", "防災地図・新旧版"],
        280: ["見守り・普段の連絡", "見守り・三段階", "見守り・支援の接続"],
        246: ["課税明細・資料の役割", "課税明細・一筆一棟", "課税明細・単有と共有"],
        284: ["児童クラブ・利用時間の比較", "児童クラブ・三つの実施場所", "児童クラブ・迎え経路"],
        292: ["農地・譲渡人と譲受人", "農地・一筆と権利の種類", "農地・締切と現地と総会"],
        191: ["法人町民税・一件ファイル", "法人町民税・設立情報を固定", "法人町民税・申告から異動"],
        103: ["浄化槽・設備と記録の引継ぎ", "浄化槽・設備票を確認", "浄化槽・管理者変更と維持管理"],
        162: ["農業委員会・令和8年度12か月", "農業委員会・四つの日付", "農業委員会・予定と実績"],
    }
    special_descriptions = {
        81: [
            "森町の山林を背景に、火を使う前の許可・届出・発令確認と、煙を見た後の安全・119番・場所情報を二枚に分ける図",
            "森町の山並みと火気使用地点、風・乾燥・消火用水・作業人数を確認し、林野火災注意報で中止連絡へ進む図",
            "煙や炎を見た人が安全に退避し、119番へ現在地と火が見える方向を伝える流れを森町の山林で示す図",
        ],
        80: [
            "寝室、階段、台所の警報器へ番号を付け、部屋別台帳へ対応させる図",
            "住宅用火災警報器の点検ボタン、警報音、製造年、電源、十年目安を分けて確認する図",
            "部屋別台帳から交換候補を選び、取付支援または専門業者を経て交換履歴を残す図",
        ],
        70: [
            "出産予定月、単胎四か月、多胎六か月、届出資料、税額通知を一件表で結ぶ図",
            "単胎四か月と多胎六か月の免除対象月を上下の月札で分ける図",
            "本人確認書類と母子健康手帳から届出、受付、税額通知の照合へ進む図",
        ],
        60: [
            "亡くなった人、葬祭を行った人、請求書、受付、入金を一枚で分ける図",
            "葬祭を行った人、問い合わせる人、請求者、口座名義人を別欄で確認する図",
            "様式取得、資料確認、提出、受付、決定、入金を段階別に追う図",
        ],
        64: [
            "支払理由、専用証明、資格・口座、受付・決定を一件表で分ける図",
            "資格未提示、柔道整復、はり等、治療用装具、生血代を五本に分岐する図",
            "資料確認、提出・受付、追加照会、支給決定、入金照合を順に追う図",
        ],
        65: ["事故地点から治療、警察、森町国保、相手方保険へ連絡線を分ける", "警察、医療機関、森町役場と第三者行為届の役割を照合する", "治療と国保届出から相手方請求へ進む道に示談前相談の停止線を置く"],
        57: ["暦月ごとに受診者、医療機関、入院・外来を別欄へ分ける高額療養費台帳", "70歳未満と70歳以上75歳未満で異なる計算順を左右に分ける", "申請書到着から決定通知までを過去12か月の支給月へつなぐ"],
        20: ["取り壊した家屋から森町の課税台帳と法務局の登記記録へ二本の確認路を分ける図", "道路側から見た母屋跡と残存物置を棟番号付き配置図へ対応させる図", "町届出・現地確認・滅失登記・翌年度課税明細を別の節目として進む図"],
        21: [
            "妊婦健診一回ごとに、週数・受診先・通常受診票・追加票・精算方法を一行へまとめる図",
            "妊娠週数の流れに通常受診票、超音波等受診票、多胎妊婦追加受診票、受診先を分けて置く図",
            "県外受診から未使用受診票・領収書・母子健康手帳をそろえ、森町への申請期限へつなぐ図",
        ],
        24: [
            "出生後に国民健康保険または勤務先等の健康保険へ加入し、資格情報を森町こども医療費受給者証へつなぐ図",
            "赤ちゃんの家から森町国保と勤務先等の健康保険へ道を分け、加入先を確認する図",
            "県外受診の領収書・資格情報・受給者証をそろえ、森町への払い戻しと一年期限へつなぐ図",
        ],
        1: [
            "離婚成立日を2026年3月31日以前と4月1日以後へ分け、親権・養育費・財産分与を整理する図",
            "親権、法定養育費、既存合意、財産分与期限を四つの別欄へ振り分ける図",
            "財産分与の二年と五年の時計、森町窓口、法律相談を分けて安全に引き継ぐ図",
        ],
        168: [
            "地域計画と目標地図を読み、所有者・現在耕作者・将来担い手・更新日を一筆ごとに分ける図",
            "目標地図の表示番号を担い手一覧へつなぎ、番号と氏名を照合する図",
            "地域計画の策定日、変更日、2035年度の将来像を現在の権利と分ける図",
        ],
        172: [
            "電気柵を買う前に、柵線・出入口・道路水路・電源装置・点検動線を一枚へ置く図",
            "道路や水路との公共境界と、人が近づく方向の危険表示を分けて描く図",
            "電源仕様、立入り条件、漏電遮断器、専用開閉器、設置後の点検を別欄で確認する図",
        ],
        91: [
            "運転経歴証明書交付手数料助成と公共交通利用券助成を、起算日・期限・担当課ごとに分ける図",
            "運転経歴証明書の交付日と公共交通利用券の購入日を、別々の時計で管理する図",
            "二つの助成申請について、領収証・交付資料・口座・担当課を一件台帳へ振り分ける図",
        ],
        180: [
            "伐採開始前の届出、伐採完了報告、造林完了報告を三つの期限でつなぐ工程図",
            "森林の対象地番、伐採方法、造林方法、面積を一件の確認票へそろえる図",
            "伐採の届出計画、伐採実績、造林実績を別書類として保存する図",
        ],
        149: [
            "狭い道路沿いの建替え前に、道路区域、町有道路境界、基準時中心線、後退候補線を別々に照合する図",
            "静岡県指定道路図のGIS、町と県の窓口、地番資料と現地写真を順に照合する図",
            "照会前の未確認線、窓口回答、設計者が使う配置図を版ごとに分ける図",
        ],
        159: [
            "地価公示、取引価格情報、森町用途図を別資料として一枚の比較条件カードへ置く図",
            "土地・土地建物・農地・林地を分け、地域・期間・面積帯・採否理由をそろえる検索盤",
            "面積・形状・接道・時点の違いを比較候補から査定前の質問表へ移す図",
        ],
        166: [
            "農地転用の許可書と申請図を、許可対象の工事範囲と着工前に照合する図",
            "申請地、道路、排水計画を別の線として重ね、変更の有無を確認する図",
            "許可条件と計画変更、工事進捗、完了報告を一件の記録経路でつなぐ図",
        ],
        176: [
            "森林土地所有者届の全対象地番を、位置図上の番号と一対一で対応させる図",
            "地理院地図、町の案内図、手元の地図を出典・縮尺・取得日ごとに分ける図",
            "届出書の行番号、地番、位置図番号を照合し、全筆を示したか確認する図",
        ],
        249: [
            "課税明細書と評価証明・評価通知・公課証明・資産証明を、提出先の必要項目と年度で選ぶ図",
            "年次確認・一般用・登記用・記載項目確認・所有資産確認を五つの書類へ結ぶ分岐図",
            "年度・名義・土地家屋・一部全部・物件番号を確認して窓口用と郵便用へ分ける図",
        ],
        288: [
            "森町の公共施設を計画・予算・入札・完了の証拠段階ごとに索引へ結ぶ図",
            "一棟の公共施設を三分割し、修繕・改修・更新等の違いを示す図",
            "計画資料から予算・入札を経て工事の完了確認へ進む証拠経路の図",
        ],
        190: [
            "森町の店舗看板から静岡県の屋外広告物許可と森町の景観届出へ二本の確認経路を分ける図",
            "看板の設置場所、縦横寸法、地上高、色を位置図と立面図へ固定する図",
            "広告面だけの変更と建物・支持工作物を含む建築行為を分けて確認する図",
        ],
        194: [
            "資格区分、申請受付、資格者名簿、電子入札登録の四段階を順に確認する図",
            "受注したい仕事を建設工事、測量・建設コンサルタント等、物品製造等へ振り分ける図",
            "資格者名簿の登載確認から利用届、登録番号、電子入札利用者登録へ進む図",
        ],
        17: [
            "圧着はがきに記載された最大4名を家族別の行へ分け、氏と名を個別に確認する図",
            "氏は原則筆頭者、名は本人または法定代理人へ割り当て、届出の責任線を分ける図",
            "2025年通知、期限までの届出控え、2026年5月26日以後の現在記載を家族番号で照合する図",
        ],
        208: [
            "年代と資料種別の二軸から、森町史の最初の一冊を選ぶ巻別ルーティング表",
            "先史から近現代の年代軸へ資料編1から4を置き、通史・民俗・別冊を別レーンに分ける図",
            "検地帳、舞楽、棟札、古写真、特定家文書の問いを対応する森町史の巻へ振り分ける図",
        ],
        212: [
            "古絵図の原表記と現在地候補を分けて対照表へ記録する図",
            "古絵図の方角、水路、道、目印を現在地図の候補と照合する図",
            "古地名の一致、有力、未確認を分けて確認先とともに残す図",
        ],
        230: [
            "戸籍束、法定相続情報一覧図、町への提出書類を用途別に分ける図",
            "町の各手続で法定相続情報一覧図の受入可否を確認してから提出先を分ける図",
            "相続書類の原本、写し、提示、返却、再交付を表で管理する図",
        ],
        292: [
            "茶畑の一筆を挟み、譲渡人と譲受人が権利種別を分けて確認する図",
            "農地一筆の地番、登記地目、現況地目と所有権・賃借権・使用貸借を分岐して照合する図",
            "農地手続の締切日、現地調査日、農業委員会の日を別々に管理する図",
        ],
        191: [
            "法人の設立・設置届、初回申告、納付、異動届を一件ファイルでつなぐ図",
            "登記事項、定款、事業年度、森町内の事務所設置日を基礎情報票へ照合する図",
            "法人町民税の申告と納付の証跡を保管し、その後の変更を異動届へ戻す図",
        ],
        103: [
            "浄化槽付き住宅の設備票と保守点検・清掃・法定検査の記録を引き継ぐ図",
            "住宅と浄化槽の銘板・点検口・ブロワを照合し、合併・単独、人槽、設置年を設備票へ記す図",
            "県への管理者変更報告、維持管理三業務、民間契約名義を別経路で確認し一年予定表へ結ぶ図",
        ],
        162: [
            "森町農業委員会の令和8年度12か月を、締切・発送・現地調査・総会の予定とともに一覧化する図",
            "公式PDFの議案締切、議案発送、現地調査、農業委員会の四列を別々に転記する図",
            "公式予定表、開催後の実績、変更確認、次年度の空白表を版ごとに分けて保存する図",
        ],
    }
    item_id = int(row["id"])
    day31_40_visuals = {
        5: (["戸籍広域交付・請求判定", "戸籍広域交付・続柄分岐", "戸籍広域交付・三証明"], ["family-register-request-card", "family-register-relationship-gate", "family-register-three-certificates"]),
        22: (["妊娠転入・手帳と受診票", "妊娠転入・残回数", "妊娠転入・未使用票"], ["pregnancy-transfer-handbook-tickets", "pregnancy-ticket-remaining-count", "pregnancy-unused-ticket-route"]),
        27: (["保育申込・世帯別証明", "保育申込・就労時間", "保育申込・証明日"], ["childcare-household-certificates", "childcare-work-hours-board", "childcare-certificate-date-route"]),
        58: (["国保入院・暦月台帳", "国保入院・負担区分", "国保入院・領収書"], ["nhi-hospital-calendar-ledger", "nhi-income-limit-branches", "nhi-receipt-application-route"]),
        66: (["肝炎検査・受診歴", "肝炎検査・B型とC型", "肝炎検査・結果相談"], ["hepatitis-test-history-card", "hepatitis-b-c-result-columns", "hepatitis-result-consultation-route"]),
        101: (["中古住宅水道・設備票", "中古住宅水道・メーター", "中古住宅水道・名義と漏水"], ["used-home-water-ledger", "water-meter-pilot-check", "water-name-leak-route"]),
        102: (["公共下水道・三列表", "公共下水道・公共ます", "公共下水道・宅内工事"], ["sewer-three-column-ledger", "sewer-public-inlet-field", "sewer-private-pipe-contractor"]),
        105: (["家屋解体・二手続", "家屋解体・棟と写真", "家屋解体・届と登記"], ["demolition-two-procedure-file", "demolished-building-photo-ledger", "demolition-town-registry-route"]),
        109: (["火災警報器・一台一行", "火災警報器・製造年", "火災警報器・交換支援"], ["alarm-room-unit-ledger", "alarm-manufacture-year-check", "alarm-replacement-support-route"]),
        121: (["空き家登録・所有者資料", "空き家登録・名義と同意", "空き家登録・調査と公開"], ["vacant-bank-owner-file", "vacant-bank-land-building-consent", "vacant-bank-survey-publication-route"]),
        108: (["耐震改修・診断と見積", "耐震改修・弱点と工事項目", "耐震改修・申請と完了"], ["seismic-diagnosis-estimate-ledger", "seismic-weakness-work-item-crosscheck", "seismic-application-completion-route"]),
        104: (["増築照合・三つの資料", "増築照合・一棟一行", "増築照合・届出と登記"], ["extension-tax-registry-site-ledger", "extension-building-row-crosscheck", "extension-town-registry-route"]),
        122: (["空き家内覧・案内表", "空き家内覧・外観と設備", "空き家内覧・鍵と回答"], ["vacant-bank-viewing-guide-sheet", "vacant-house-viewing-safety-route", "key-question-exit-check-route"]),
        123: (["空き家登録・変更と抹消", "空き家登録・公開差分", "空き家登録・終了引継ぎ"], ["vacant-bank-change-cancel-file", "listing-old-new-condition-board", "listing-close-key-management-route"]),
        124: (["空き家修繕・見積り表", "空き家修繕・部位照合", "空き家修繕・四区分"], ["vacant-repair-estimate-desk", "house-part-photo-estimate-route", "repair-inspect-dispose-defer-route"]),
        125: (["修繕履歴・一件台帳", "修繕履歴・写真三時点", "修繕履歴・次回点検"], ["vacant-maintenance-history-desk", "before-during-after-photo-route", "repair-record-warranty-next-check-route"]),
        126: (["空き家連絡・緊急カード", "空き家連絡・現地と所有者", "空き家連絡・一次確認順"], ["vacant-neighbor-emergency-contact-board", "neighbor-owner-manager-contact-route", "incident-observe-owner-emergency-route"]),
        127: (["台風点検・前後比較", "台風点検・六つの部位", "台風点検・安全な撤退"], ["vacant-typhoon-before-after-board", "roof-drain-tree-equipment-check-route", "weather-stop-safe-return-route"]),
        128: (["動物痕跡・接触しない", "動物痕跡・侵入口候補", "動物痕跡・四工程"], ["vacant-animal-trace-record-board", "trace-room-entry-candidate-map", "animal-health-seal-repair-route"]),
        129: (["家族役割・四担当", "家族役割・巡回と支払", "家族役割・交代手順"], ["vacant-family-role-board", "inspection-payment-contact-document-route", "family-role-backup-handover"]),
        131: (["相続登記・二つの起点", "相続登記・三年時計", "相続登記・申告分岐"], ["inheritance-deadline-two-starts", "knowledge-division-three-year-clocks", "registration-declaration-route"]),
        132: (["相続資産・三資料照合", "相続資産・土地家屋行", "相続資産・未確認一覧"], ["inheritance-property-three-source-crosscheck", "tax-ledger-land-building-rows", "property-gap-confirmation-route"]),
        133: (["共有実家・四つの合意", "共有実家・費用と利用", "共有実家・判断記録"], ["shared-house-family-agreement-board", "share-use-cost-repair-route", "shared-property-decision-history"]),
        130: (["空き家連絡・危険箇所", "空き家連絡・外観点検", "空き家連絡・応急と恒久"], ["unsafe-vacant-house-contact-file", "vacant-house-exterior-risk-survey", "temporary-permanent-response-route"]),
        2: (["転籍・本籍と筆頭者", "転籍・現在と新本籍", "転籍・届出と戸籍請求"], ["domicile-transfer-ledger", "old-new-domicile-bridge", "transfer-filing-certificate-route"]),
        3: (["世帯変更・三つの届", "世帯変更・住所と生計", "世帯変更・届出後確認"], ["household-change-three-forms", "address-livelihood-households", "household-result-check-route"]),
        4: (["不受理申出・本人意思", "不受理申出・対象届", "不受理申出・取下げ"], ["nonacceptance-personal-intent", "nonacceptance-filing-types", "nonacceptance-withdrawal-route"]),
        6: (["戸籍附票・住所履歴", "戸籍附票・必要表示", "戸籍附票・提出範囲"], ["family-register-address-history", "address-history-display-fields", "address-history-purpose-route"]),
        7: (["記載事項証明・指定様式", "記載事項証明・必要項目", "記載事項証明・提出"], ["resident-items-form", "resident-items-field-selector", "resident-items-submission-route"]),
        8: (["印鑑登録証・紛失記録", "印鑑登録証・廃止と再登録", "印鑑登録証・証明取得"], ["seal-card-loss-ledger", "seal-card-cancel-reregister", "seal-card-certificate-route"]),
        9: (["電子証明書・二期限", "電子証明書・二暗証番号", "電子証明書・更新後利用"], ["digital-certificate-two-expiries", "digital-certificate-two-pins", "digital-certificate-renewal-route"]),
        10: (["カード紛失・停止記録", "カード紛失・警察届", "カード紛失・再交付"], ["my-number-loss-stop-ledger", "my-number-police-report", "my-number-reissue-route"]),
        11: (["暗証番号・四種類", "暗証番号・失念とロック", "暗証番号・安全な再設定"], ["my-number-four-pins", "pin-forgotten-locked", "pin-reset-safe-route"]),
        14: (["代理届・委任状確認", "代理届・三つの異動", "代理届・受付結果"], ["proxy-moving-authorization", "proxy-three-moving-types", "proxy-filing-result-route"]),
    }
    for visual_id, (visual_labels, visual_scenes) in day31_40_visuals.items():
        shift = visual_id % 37
        special_labels[visual_id] = visual_labels
        special_descriptions[visual_id] = [
            f"{visual_labels[0]}について対象、資料、確認日を一枚に配置する図",
            f"{visual_labels[1]}について二つの条件を左右に分けて照合する図",
            f"{visual_labels[2]}について確認から次の担当までを矢印でつなぐ図",
        ]
        special_scenes[visual_id] = [
            f'<g data-scene="{visual_scenes[0]}"><rect x="{180+shift}" y="220" width="250" height="245" rx="20" fill="#fff" stroke="{dark}" stroke-width="10"/><rect x="570" y="250" width="240" height="205" rx="20" fill="{pale}" stroke="{dark}" stroke-width="10"/><path d="M{225+shift} 290h160M{225+shift} 350h160M{225+shift} 410h120M620 315h140M620 375h140" stroke="{accent}" stroke-width="9"/><path d="M430 340h140" stroke="{dark}" stroke-width="13"/></g>',
            f'<g data-scene="{visual_scenes[1]}"><circle cx="{330-shift//2}" cy="350" r="112" fill="#fff" stroke="{dark}" stroke-width="10"/><circle cx="{670+shift//2}" cy="350" r="112" fill="{pale}" stroke="{dark}" stroke-width="10"/><path d="M442 350h116" stroke="{accent}" stroke-width="15"/><path d="M280 350h100M330 300v100M620 350h100M670 300v100" stroke="{dark}" stroke-width="10"/></g>',
            f'<g data-scene="{visual_scenes[2]}"><rect x="170" y="285" width="185" height="150" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><rect x="{410+shift}" y="245" width="185" height="190" rx="18" fill="{pale}" stroke="{dark}" stroke-width="10"/><rect x="650" y="285" width="185" height="150" rx="18" fill="#fff" stroke="{dark}" stroke-width="10"/><path d="M355 360h{55+shift}M{595+shift} 360h{55-shift}" stroke="{accent}" stroke-width="14"/><path d="M205 335h115M205 385h90M{445+shift} 305h115M{445+shift} 365h115M685 335h115M685 385h90" stroke="{dark}" stroke-width="8"/></g>',
        ]
    special_scene_orders = {246: (1, 0, 2), 284: (1, 0, 2)}
    special_index = special_scene_orders.get(item_id, (0, 1, 2))[(index - 1) % 3]
    scene = special_scenes.get(item_id, scenes)[special_index] if item_id in special_scenes else scenes[scene_kind]
    label = special_labels[item_id][(index - 1) % 3] if item_id in special_labels else f"{motif}・{row['section_headings'][(index+2)%len(row['section_headings'])][:16]}"
    description = special_descriptions.get(item_id, [])[index - 1] if item_id in special_descriptions else f"森町の山並み、道、{row['section_headings'][(index-1)%len(row['section_headings'])]}の確認場面"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="560" viewBox="0 0 1000 560" role="img" aria-labelledby="title desc" data-illustration="mori-editorial" data-topic-id="{item_id}" data-scene-index="{index}"><title id="title">{e(row['title'])}の挿絵{index}</title><desc id="desc">{e(description)}</desc><rect width="1000" height="560" rx="32" fill="{pale}"/><polygon points="{ridge} 1000,350 0,350" fill="{dark}" opacity=".22"/><path d="M0 430 Q250 {rng.randint(330,410)} 500 430 T1000 410 V560 H0Z" fill="{dark}" opacity=".18"/><path d="M60 500 C230 {rng.randint(350,440)} 360 {rng.randint(360,450)} 520 450 S780 {rng.randint(330,430)} 940 390" fill="none" stroke="{accent}" stroke-width="24" stroke-linecap="round"/>{decorations}{scene}<text x="500" y="72" text-anchor="middle" font-family="sans-serif" font-size="32" font-weight="700" fill="{dark}">{e(label)}</text></svg>'''

def specific_blocks(row: dict) -> str:
    headings = list(row["section_headings"])
    facts = row["verified_facts"]
    conditions = row["morimachi_conditions"]
    title = row["title"]
    intent = row["search_intent"]
    article_key = re.sub(r"^森町(?:で|の)?", "", title.split("｜", 1)[0]).strip()
    method, authorities, memo = category_context(row["category"])
    details = topic_details(row)

    def clean_fact(value: object) -> str:
        """台帳の編集メモを、読者が理解できる事実文へ整える。"""
        text = str(value).strip().replace("。。", "。").replace("。です。", "です。")
        text = re.sub(r"^「(.+?)」は「.+?」の判断を分ける確認項目である。", r"\1は、確認結果を左右する項目です。", text)
        text = re.sub(r"森町公式の担当情報を根拠に、", "森町公式の案内を基に、", text)
        text = re.sub(r"対象地番・対象者・資料基準日を一致させて確認する。", "対象地、対象者、資料の日付をそろえて確認します。", text)
        return text

    # FAQは検索者の問いそのものなので、本文冒頭で短く先に答える。
    direct = ['<section class="direct-answer"><h2 class="sec">先に答えを確認する</h2>']
    for item in row["faqs"][:4]:
        question = str(item["question"]).rstrip("？?")
        answer = str(item["answer"]).replace("。。", "。").strip()
        direct.append(f'<p><strong>{e(question)}。</strong>{e(answer)}</p>')
    direct.append("</section>")

    blocks = []
    for number, heading in enumerate(headings[:12], 1):
        fact = facts[(number - 1) % len(facts)]
        fact_text = clean_fact(fact.get("statement") if isinstance(fact, dict) else fact)
        condition = conditions[(number - 1) % len(conditions)]
        detail = details[(number - 1) % len(details)]
        styles = number % 4
        if styles == 0:
            paragraphs = [
                f"{heading}では、特に{detail}を確かめます。{fact_text}資料の対象と自分の住所、立場、予定日が一致するかを読み、当てはまらない条件は未確認のまま残します。",
                f"{article_key}のうち{detail}について森町で実際に動く際は、{condition}条件が違えば必要な資料や相談先も変わります。町全体の説明を個別の答えへ置き換えないことが大切です。",
                f"{heading}を尋ねる窓口へは、{detail}と{memo}を一枚にして持参します。質問は「できるか」だけで終わらせず、根拠資料、次の部署、再確認時期まで聞けば、家族へ正確に共有できます。",
            ]
        elif styles == 1:
            paragraphs = [
                f"{intent}なら、{detail}から確認します。結論を急ぐ前に、誰の、どの場所の、いつの話かを書き出すと、別の制度や別年度の案内を混ぜにくくなります。",
                f"{article_key}に関して、{detail}の公式資料から読める要点は次のとおりです。{fact_text}ただし、ページの更新日と適用日、実施日、書類の有効期間は同じとは限りません。",
                f"{heading}を整理する段階では、{detail}を起点に{method}順序で進めます。分からない項目を推測で埋めず、確認先と期限を決める方が手戻りを減らせます。",
            ]
        elif styles == 2:
            paragraphs = [
                f"{heading}は、{detail}の資料を集めるだけの作業ではありません。今決められることと、現地や窓口でなければ決められないことを分ける作業です。",
                f"{article_key}で{detail}の判断材料になる公表事項は、{fact_text}検索結果の短い説明ではなく、本文の対象者、場所、日付、例外まで確認し、ページ名と確認日を記録します。",
                f"{heading}について森町で注意する条件は、{condition}{detail}を家族へ伝えるときも、結論だけでなく未確認事項を添えてください。",
            ]
        else:
            paragraphs = [
                f"ここでは、{heading}のうち{detail}を扱います。{authorities}の役割を分け、同じ言葉でも担当範囲が同じかを確かめます。",
                f"{article_key}における{detail}の確認の土台は、{fact_text}この内容が当てはまるとは限らないため、住所、対象者、実行日を添えて担当窓口へ照会します。",
                f"{heading}の実行前メモには、{detail}を含め、確認済み、未確認、対象外の三欄を作ります。{condition}保留事項にも次の担当と再確認日を付けます。",
            ]
        blocks.append(
            f'<section class="topic-specific"><h2 class="sec">{e(heading)}</h2>'
            + ''.join(f'<p>{e(p.replace("。。", "。"))}</p>' for p in paragraphs)
            + '</section>'
        )
        if number == 4:
            blocks.append(f'<figure><img style="width:100%;height:auto" src="fig1.svg" width="1000" height="560" loading="lazy" alt="森町で{e(row["search_intent"])}ため、資料と現地条件を照合する場面"><figcaption>対象地点と一次資料を同じ確認表へ置きます。</figcaption></figure>')
        if number == 9:
            blocks.append(f'<figure><img style="width:100%;height:auto" src="fig2.svg" width="1000" height="560" loading="lazy" alt="{e(row["title"])}について、窓口確認から家族共有へ進む図"><figcaption>未確認事項、次の担当、再確認日を残します。</figcaption></figure>')
    closing = [
        '<section class="editorial-conclusion"><h2 class="sec">大石の視点と次の一歩</h2>',
        f'<p>{e(title)}について、私は結論を急ぐより、分かっている事実と未確認事項を分けることを優先します。特に{e(details[0])}を先に確かめ、申請や契約を最初の行動にしない方が選択肢を守れます。</p>',
        f'<p>{e(article_key)}では、森町内の地区による移動、道路、周辺施設、土地の使われ方の違いも確認します。現地を見ていない内容を体験談のように語らず、{e(memo)}を公式資料と照合してください。</p>',
        f'<p>{e(article_key)}について今日できることは、{e(details[1 % len(details)])}に関係する一次情報を一件開き、自分に当てはまる条件へ印を付けることです。資料名、部署名、確認日、残った疑問を記録します。</p>',
        f'<p>{e(article_key)}のうち{e(details[2 % len(details)])}が対象外なら、その理由も記録します。対象外と未確認を分けておけば、条件が変わったときに必要な箇所だけ確認し直せます。</p>',
        '</section>',
    ]
    return "".join(direct + blocks + closing)


def safe_faqs(row: dict) -> list[tuple[str, str]]:
    """検索意図へ直接答える、短く自然なFAQを作る。"""
    if row.get("section_paragraphs") or int(row["id"]) in DAY2_SECTION_NOTES:
        return [
            (str(item["question"]).strip(), str(item["answer"]).strip())
            for item in row["faqs"][:4]
        ]
    subject = str(row["title"]).split("｜", 1)[0]
    source_titles = [str(item.get("title") or "公式ページ") for item in row["sources"]]
    _, _, memo = category_context(row["category"])
    critical = CRITICAL_FACTS.get(int(row["id"]), [])
    deadline_answer = critical[0] if critical else (
        "期限は制度や予定日によって異なります。公式ページの対象年度と受付期間を確認し、"
        "実行日から資料取得と問い合わせの日を逆算してください。"
    )
    return [
        (f"{subject}では、最初に何を確認しますか？",
         f"最初に対象となる人・場所・予定日を一枚に書き、{memo}をそろえます。"
         f"そのうえで「{source_titles[0]}」の対象条件と担当窓口を確認します。"),
        (f"{subject}の期限や行動時期はどう考えますか？", deadline_answer),
        (f"森町ではどの資料から確認しますか？",
         f"「{source_titles[0]}」を主資料にし、「{source_titles[1]}」で関連条件を照合します。"
         "ページ名、対象年度、確認日を記録し、個別条件は担当窓口へ伝えてください。"),
        ("家族や次の担当者へ何を残せばよいですか？",
         "確認済みの事実、根拠にした資料、未確認事項、次の担当、再確認日を残します。"
         "結論だけでなく、判断の前提が分かる形にしてください。"),
    ]


def editorial_blocks_curated(row: dict) -> str:
    """調査担当が主題ごとに書いた専用本文を、改変せず記事構造へ組み込む。"""
    sections = row.get("section_paragraphs")
    if not isinstance(sections, list) or len(sections) != 12:
        raise RuntimeError(f"ID{row['id']} 専用本文は12節が必要です")
    total_paragraphs = sum(len(section.get("paragraphs", [])) for section in sections)
    if total_paragraphs < 36:
        raise RuntimeError(f"ID{row['id']} 専用本文は36段落以上が必要です")
    first_faq = row.get("faqs", [{}])[0]
    conditions = row.get("morimachi_conditions", [])
    answer = str(first_faq.get("answer") or row["search_intent"]).strip()
    condition_value = conditions[0] if conditions else "実行前に森町の担当窓口で対象条件を確認します。"
    if isinstance(condition_value, dict):
        condition_value = condition_value.get("condition") or condition_value.get("statement") or ""
    local_condition = str(condition_value).strip()
    parts = [
        '<!-- PHASE4-CURATED -->',
        '<section class="direct-answer"><h2 class="sec">先に結論を確認する</h2>',
        f'<p><strong>この記事の答え：</strong>{e(answer)}</p>',
        f'<p><strong>森町で最初に照合する条件：</strong>{e(local_condition)}</p></section>',
    ]
    item_id = int(row["id"])
    special_figures = {
        81: {
            4: ("fig1.svg", "森町の山林で発令情報、風、乾燥、消火用水、作業人数を照合して火の使用を中止する図", "許可や届出だけで実施を決めず、発令情報と現地条件を当日に照合します。"),
            6: ("fig2.svg", "山林の煙を見た人が安全に退避し、119番へ現在地と火が見える方向を伝える図", "火元へ近づかず、安全な場所から現在地・方向・目標物・見えた事実を伝えます。"),
        },
        70: {
            2: ("fig1.svg", "単胎四か月と多胎六か月の国民健康保険税免除対象月を上下に並べた図", "出産予定月または出産月を中心に、単胎は前月から四か月、多胎は三か月前から六か月を月単位で分けます。"),
            8: ("fig2.svg", "本人確認書類と母子健康手帳から届出受付と税額通知の照合へ進む図", "届出資料、提出または郵送、受付・届出不要の確認、税額通知の対象月照合を別の工程として残します。"),
        },
        60: {
            2: ("fig1.svg", "葬祭を行った人、問い合わせる人、請求者、口座名義人を別欄で確認する図", "家族内の立場だけで請求者を決めず、森町の確認結果を役割別に残します。"),
            8: ("fig2.svg", "葬祭費請求書の取得から資料確認、提出、受付、決定、入金へ進む図", "請求書を提出した時点で完了にせず、受付結果と入金まで段階別に追います。"),
        },
        64: {
            5: ("fig1.svg", "全額を支払った理由を五つに分け、各場面の専用証明を選ぶ図", "資格未提示、柔道整復、はり等、治療用補装具、生血代を混ぜず、支払理由と資料を一対一で結びます。"),
            9: ("fig2.svg", "療養費申請の資料確認から受付、追加照会、決定、入金を追う図", "提出した時点で完了にせず、追加照会と支給決定を経て通帳の入金まで状態を更新します。"),
        },
        65: {
            4: ("fig1.svg", "事故地点・警察・医療機関・森町役場と第三者行為の提出書類を役割別に照合する図", "警察への届出と森町国保への提出を分け、各書類を事故番号へ結びます。"),
            7: ("fig2.svg", "治療と国保届出から相手方請求へ進む道に示談前の森町相談という停止線を置く図", "治療費の受領や示談を進める前に、国保の求償への影響を森町へ確認します。"),
        },
        57: {
            3: ("fig1.svg", "70歳未満と70歳以上75歳未満の高額療養費計算順を左右に分けた図", "年齢区分ごとの計算順を混ぜず、町へ確認する単位を残します。"),
            8: ("fig2.svg", "高額療養費の申請書到着、提出、決定通知と過去12か月の支給月をつなぐ図", "申請の進捗と多数回該当を確認する支給月を同じ一件ファイルへつなぎます。"),
        },
        20: {
            4: ("fig1.svg", "道路、母屋跡、残した物置を俯瞰し、課税明細の棟番号と配置図番号を対応させる図", "壊した棟と残した棟へ同じ番号を振り、町の現地確認へつなぎます。"),
            9: ("fig2.svg", "町届出・現地確認・滅失登記・翌年度課税明細を別の節目として進む道筋", "町の受付と登記の受付を分け、翌年度明細の照合まで進捗を残します。"),
        },
        21: {
            4: ("fig1.svg", "妊娠週数に通常受診票・超音波等受診票・多胎妊婦追加受診票と受診先を分けて置く図", "週数の目安だけで票を決めず、健診ごとに受診先と使った票を一行へ残します。"),
            7: ("fig2.svg", "県外受診から未使用受診票・領収書・母子健康手帳をそろえ、森町への申請期限へつなぐ図", "県外受診の支払い記録と未使用票をそろえ、出産月から一年以内の申請へつなぎます。"),
        },
        24: {
            2: ("fig1.svg", "赤ちゃんの家から森町国保と勤務先等の健康保険へ道を分け、加入先を確認する図", "国保と勤務先等の保険を同時に申請せず、各保険者へ加入先を確認します。"),
            8: ("fig2.svg", "県外受診の領収書・資格情報・受給者証をそろえ、森町への払い戻しと一年期限へつなぐ図", "県外受診の支払いを一件ずつ残し、受診日から一年以内の申請へつなぎます。"),
        },
        1: {
            7: ("fig1.svg", "親権・法定養育費・既存合意・財産分与期限を四つの別欄へ振り分ける図", "離婚成立日を基準に、四つの論点を一件表の別欄へ置きます。"),
            8: ("fig2.svg", "財産分与の二年と五年の期限、森町窓口、法律相談を分けて引き継ぐ図", "期限の時計と確認先を分け、安全上の事情も別に扱います。"),
        },
        168: {
            3: ("fig1.svg", "目標地図の表示番号を担い手一覧へつなぎ、番号と氏名を照合する図", "地図上の番号だけで担い手を決めず、同じ版の一覧へ照合します。"),
            6: ("fig2.svg", "地域計画の策定日・変更日・2035年度の将来像を現在の権利と分ける図", "資料の版と将来像を残し、現在の所有や貸借を上書きしません。"),
        },
        172: {
            5: ("fig1.svg", "道路・水路との公共境界と、人が近づく方向の危険表示を分ける図", "公共境界と危険表示を別の線で描き、人が近づく方向ごとに確認します。"),
            7: ("fig2.svg", "電源仕様・立入り条件・漏電遮断器・専用開閉器・点検履歴を分ける図", "二つの漏電遮断器条件と専用開閉器を分け、設置後の点検へつなぎます。"),
        },
        91: {
            1: ("fig1.svg", "運転経歴証明書の交付日と公共交通利用券の購入日を別々の起算日として管理する図", "交付日から一年と購入日から三か月を、別々の期限として台帳へ置きます。"),
            9: ("fig2.svg", "二つの免許返納助成について領収証・交付資料・口座・担当課を振り分ける図", "証憑、口座、担当課を二つの申請へ分け、提出済みか確認します。"),
        },
        180: {
            4: ("fig1.svg", "森林の対象地番・伐採方法・造林方法・面積を一件の確認票へそろえる図", "対象地番と伐採・造林の方法をそろえ、事前届の期間へつなぎます。"),
            8: ("fig2.svg", "森林の届出計画・伐採実績・造林実績を別書類として保存する図", "伐採と造林の完了日を別々に記録し、それぞれの報告期限を管理します。"),
        },
        149: {
            3: ("fig1.svg", "静岡県指定道路図GIS、町と県の窓口、地番資料と現地を照合する図", "GIS表示を確定線とせず、窓口回答と地番・現地資料へ順に照合します。"),
            9: ("fig2.svg", "接道照会前の未確認線、窓口回答、設計者の配置図を版ごとに分ける図", "回答日と担当を残し、設計へ渡した線を前の版へ上書きしません。"),
        },
        159: {
            3: ("fig1.svg", "土地・土地建物・農地・林地を分け、地域・期間・面積帯をそろえる検索盤", "物件種類と期間を混ぜず、比較候補の採否理由まで同じ表へ残します。"),
            9: ("fig2.svg", "面積・形状・接道・時点の違いを査定前の質問表へ移す図", "公的データの数字を価格結論にせず、比較できない条件を質問へ変えます。"),
        },
        166: {
            3: ("fig1.svg", "農地転用の申請地、公図の道路・水路、現地の施工範囲を重ねて照合する図", "許可申請時の道路・水路・隣接地と、着工前の現地条件を別の線で確認します。"),
            8: ("fig2.svg", "農地転用の許可条件、工事進捗、完了報告を一件でつなぐ図", "許可済み、着工済み、完了報告済みを同じ状態とせず、証拠を段階別に残します。"),
        },
        176: {
            3: ("fig1.svg", "地理院地図、町の案内図、手元の地図を出典・縮尺・取得日で分ける図", "位置図の候補を一種類へ決めつけず、出典と縮尺を記して森町へ確認します。"),
            9: ("fig2.svg", "森林届の行番号、全対象地番、位置図番号を一対一で照合する図", "差替え後も全対象筆が位置図に残るよう、届出行と図上番号を版ごとに確認します。"),
        },
        17: {
            4: ("fig1.svg", "戸籍の氏は原則筆頭者、名は本人または法定代理人へ届出担当を分ける図", "氏と名で届出担当が異なるため、家族の行ごとに責任線を分けます。"),
            8: ("fig2.svg", "2025年の通知、届出控え、2026年5月26日以後の現在記載を家族番号で照合する図", "通知だけで決めず、届出控えと現在の戸籍記載を家族番号ごとに照合します。"),
        },
        190: {
            1: ("fig1.svg", "屋外広告物の設置場所、寸法、地上高、色を図面へ固定する図", "住所と道路条件に加え、看板の寸法・高さ・色を図面へ固定します。"),
            5: ("fig2.svg", "屋外広告物の変更と建物・支持工作物を含む建築行為を分ける図", "看板だけの変更と、建物や支持工作物を含む行為を分けて確認します。"),
        },
        194: {
            1: ("fig1.svg", "受注したい仕事を建設工事、測量等、物品製造等の三区分へ振り分ける図", "受注内容から、森町へ申請する入札参加資格の区分を選びます。"),
            7: ("fig2.svg", "資格者名簿の登載確認から電子入札利用者登録へ進む図", "名簿登載と電子入札登録を同じ手続だと考えず、順番に確認します。"),
        },
        249: {
            6: ("fig1.svg", "提出先の必要項目を課税明細・評価証明・評価通知・公課証明・資産証明へ結ぶ図", "書類名を先に決めず、提出先が必要とする項目から五つの書類へ振り分けます。"),
            7: ("fig2.svg", "固定資産証明の年度・名義・土地家屋・範囲・物件番号を確認する図", "年度、名義、土地・家屋、一部・全部、物件番号をそろえてから申請方法を分けます。"),
        },
        288: {
            4: ("fig1.svg", "公共施設の修繕・改修・更新等を三つに分ける図", "原資料の区分を保ち、修繕・改修・更新等を同じ実績としてまとめません。"),
            7: ("fig2.svg", "公共施設の計画資料から予算・入札を経て完了確認へ進む図", "計画、予算、入札、完了を別の証拠段階として順に追います。"),
        },
        208: {
            6: ("fig1.svg", "森町史の資料編1から4を年代軸へ置き、通史編と民俗・別冊を別レーンに分ける図", "先史から近現代までの年代に対応する資料編と、年代を横断する通史・民俗・別冊を分けます。"),
            10: ("fig2.svg", "検地帳、舞楽、棟札、古写真、特定家文書の問いを対応する森町史の巻へ振り分ける図", "調べたい資料種別を、資料編3・資料編5・別冊・図説・所在古文書目録の入口へ振り分けます。"),
        },
        212: {
            4: ("fig1.svg", "古絵図の方角、水路、道、目印を現在地図の候補と照合する図", "古絵図の目印を言葉に置き換え、現在地図の候補と照合します。"),
            8: ("fig2.svg", "古地名の一致、有力、未確認を分けて確認先とともに残す図", "一致、有力、未確認を分け、次の確認先まで対照表へ残します。"),
        },
        230: {
            7: ("fig1.svg", "町の各手続で法定相続情報一覧図の受入可否を確認する図", "一覧図を受け入れられるか各提出先へ確認してから、書類の経路を分けます。"),
            8: ("fig2.svg", "相続書類の原本、写し、提示、返却、再交付を管理する図", "原本、写し、提示のみ、返却、再交付を手続ごとに記録します。"),
        },
        292: {
            3: ("fig1.svg", "農地一筆の地番と地目を、所有権・賃借権・使用貸借の権利種別へ分ける図", "一筆ごとの土地情報と、取得する権利の種類を同じ確認表で照合します。"),
            9: ("fig2.svg", "農地手続の締切日、現地調査日、農業委員会の日を別々に管理する図", "締切、現地調査、農業委員会の日を混同せず、別々の予定として残します。"),
        },
    }
    day31_40_figure_text = {
        5: ("戸籍の請求者と対象者の続柄を広域交付の可否へ分ける図", "取得する戸籍三種類と必要通数を請求表へまとめる図"),
        22: ("母子健康手帳と妊婦健診受診票の残回数を分ける図", "未使用受診票と県外受診の領収書を森町の確認へつなぐ図"),
        27: ("父母と同居親族の就労証明書を世帯別に並べる図", "証明日、勤務変更、再提出を申込予定へつなぐ図"),
        58: ("年齢と所得区分から入院時の限度額確認へ進む図", "領収書、暦月、申請案内を一件台帳へつなぐ図"),
        66: ("B型とC型の検査歴を結果票ごとに分ける図", "検査日から結果説明と相談先へつなぐ図"),
        101: ("中古住宅の水道メーターとパイロットを現地確認する図", "給水名義、漏水修理、引渡日を設備票へつなぐ図"),
        102: ("供用通知と現地の公共ますを照合する図", "宅内排水設備から指定工事店の工事へつなぐ図"),
        105: ("解体した棟と工事前後写真を一件記録へ対応させる図", "森町の家屋届と法務局の滅失登記を分ける図"),
        109: ("部屋ごとの火災警報器と製造年を対応させる図", "交換候補を購入、取付支援、交換記録へつなぐ図"),
        121: ("空き家の土地建物名義と所有者同意を照合する図", "登録申込から現地調査と情報公開へ進む図"),
        108: ("耐震診断の指摘箇所、補強図面、工事見積項目を一行ずつ照合する図", "着工前申請、変更確認、工事写真、完了報告を順に管理する図"),
        104: ("課税明細書、登記事項証明書、現況写真を一棟一行で照合する図", "森町の未登記家屋異動届と法務局の登記相談を分ける図"),
        122: ("道路側の危険、室内設備、残置物を内覧前に順番に確認する図", "鍵の受渡し、質問の持帰り、退出確認を一件記録へつなぐ図"),
        123: ("公開中の空き家と変更後の写真・設備・価格を並べて照合する図", "変更届・抹消届から問い合わせ、鍵、管理担当の終了確認へ進む図"),
        124: ("空き家の屋根・外壁・床・水回りを写真番号で見積りへ結ぶ図", "修繕・専門調査・残置物処分・見送りを四経路に分ける図"),
        125: ("空き家の同じ部位を着手前・施工中・完了後の写真で結ぶ図", "施工記録・領収書・保証から次回点検へ引き継ぐ図"),
        126: ("近隣の観察情報を所有者・家族・現地管理者へ安全に渡す図", "見えた異常から所有者確認または119・110へ分岐する図"),
        127: ("屋根外壁・窓・排水・飛散物・立木設備を部位番号で確認する図", "気象情報から点検実施・中止・通過後確認へ安全に分岐する図"),
        128: ("糞・毛・足跡・音を部屋番号と侵入口候補へ結ぶ図", "生体確認・衛生清掃・侵入口封鎖・建物修繕を四工程に分ける図"),
        129: ("巡回・支払・連絡・書類保管を家族の四担当へ分ける図", "正担当が不在のとき予備担当へ鍵と期限を渡す図"),
        131: ("相続開始と不動産取得を知った日から三年を確認する図", "遺産分割と相続人申告登記を別の経路で管理する図"),
        132: ("課税明細・名寄帳・登記事項を一筆一棟で照合する図", "一致しない土地家屋を未確認一覧から次の窓口へ渡す図"),
        133: ("共有実家の利用・費用・修繕・将来判断を四欄に分ける図", "兄弟の回答と未合意を決定履歴へ残す図"),
        130: ("道路側から門塀・屋根・外壁・立木の危険箇所を安全に確認する図", "危険連絡から応急対応・町相談・恒久対応へ分けて進む図"),
    }
    if item_id in day31_40_figure_text:
        first, second = day31_40_figure_text[item_id]
        special_figures[item_id] = {
            3: ("fig1.svg", first, first.replace("図", "順序を確認します。")),
            8: ("fig2.svg", second, second.replace("図", "順序を確認します。")),
        }
    for index, section in enumerate(sections):
        heading = str(section.get("heading", "")).strip()
        paragraphs = section.get("paragraphs", [])
        if not heading or not isinstance(paragraphs, list) or len(paragraphs) < 3:
            raise RuntimeError(f"ID{row['id']} 専用本文の節{index + 1}が不正です")
        parts.append(f'<section class="topic-specific"><h2 class="sec">{e(heading)}</h2>')
        parts.extend(f'<p>{e(str(paragraph).strip())}</p>' for paragraph in paragraphs)
        if item_id in special_figures and index in special_figures[item_id]:
            filename, alt_text, caption = special_figures[item_id][index]
            parts.append(
                f'<figure><img style="width:100%;height:auto" src="{filename}" width="1000" height="560" '
                f'loading="lazy" alt="{e(alt_text)}">'
                f'<figcaption>{e(caption)}</figcaption></figure>'
            )
        elif item_id not in special_figures and index == 2:
            parts.append(
                f'<figure><img style="width:100%;height:auto" src="fig1.svg" width="1000" height="560" '
                f'loading="lazy" alt="{e(row["title"])}で対象と一次資料を照合する場面">'
                f'<figcaption>{e(heading)}の対象と森町の一次資料を同じ順序で照合します。</figcaption></figure>'
            )
        if item_id not in special_figures and index == 8:
            parts.append(
                f'<figure><img style="width:100%;height:auto" src="fig2.svg" width="1000" height="560" '
                f'loading="lazy" alt="{e(row["title"])}の確認結果を次の担当へ渡す場面">'
                f'<figcaption>{e(heading)}の確認結果と次の行動を、この記事の流れで引き継ぎます。</figcaption></figure>'
            )
        parts.append('</section>')
    return ''.join(parts)


def editorial_blocks_fact_ledger(row: dict) -> str:
    """実査済み記事を、事実と編集上の助言を明示して組み立てる。"""
    facts = list(row["verified_facts"])
    headings = [str(value).strip() for value in row["section_headings"]]
    conditions = [str(value).strip() for value in row["morimachi_conditions"]]
    faqs = list(row["faqs"])
    sources = {str(item.get("url", "")): item for item in row["sources"]}

    def clean(value: object) -> str:
        text = re.sub(r"\s+", "", str(value).strip()).replace("。。", "。").replace("？？", "？")
        return text if not text or text[-1] in "。！？" else text + "。"

    def fact_statement(item: object) -> str:
        return clean(item.get("statement", "") if isinstance(item, dict) else item)

    prompts = [
        "この項目は、記録の目的と利用場面を固定するために置きます。家族内のメモと、公的な回答を同じ欄へ書かないでください。",
        "似た名称や数字が出たときは、意味が同じだと決めず、資料が使う正式名称と対象範囲をそのまま残します。",
        "森町全体への案内と個別の土地・世帯・申請への回答は分けます。個別の可否は、必要事項を示して担当窓口へ確認します。",
        "準備資料は、提出するもの、照合に使うもの、家族内で保管するものに分けます。原本を渡す場合は返却予定も記録します。",
        "問い合わせ記録には、質問、回答、回答部署、確認日を残します。口頭回答は自分の解釈を混ぜず、要点を短く記します。",
        "日付は、資料の基準日、問い合わせ日、提出日、実行予定日を分けます。期限がある場合は準備開始日も逆算します。",
        "資料に書かれていない費用、期間、可否は未確認事項です。一般的な例を森町での確定条件として補わないでください。",
        "家族へ共有するときは、必要な人だけに資料を渡し、個人情報や土地情報を含む写しの保管場所を決めます。",
        "条件がそろわないときは、保留、追加照会、計画変更を分けます。急いで一つの結論へ寄せず、再開条件を記録します。",
        "次の担当者が同じ根拠へ戻れるよう、資料名、URL、確認日、該当箇所を一組で残します。略称だけの引継ぎは避けます。",
        "大石の視点として、売却や申請を先に決めず、確認できた事実と未確認事項を分けます。この記事の助言は個別判断の代わりではありません。",
        "最後に、タイトルの問いへ答えた事実、まだ答えられない点、次に連絡する相手を一行ずつ書きます。実行直前に公式ページを開き直します。",
    ]

    facts_by_section = [[] for _ in headings]
    configured_indices = row.get("fact_section_indices", [])
    all_facts = row.get("all_verified_facts", facts)
    if len(configured_indices) != len(all_facts) or any(not isinstance(value, int) or not 0 <= value < len(headings) for value in configured_indices):
        raise RuntimeError(f"ID{row['id']} fact_section_indices がverified_factsと対応していません")
    section_by_statement = {
        str(item.get("statement", "")): section_index
        for item, section_index in zip(all_facts, configured_indices)
        if isinstance(item, dict)
    }
    section_indices = [section_by_statement.get(str(item.get("statement", "")), 0) for item in facts]
    for section_index, item in zip(section_indices, facts):
        facts_by_section[section_index].append(item)

    parts = [
        '<section class="direct-answer"><h2 class="sec">先に結論を確認する</h2>',
        f'<p><strong>この記事が答える問い：</strong>{e(clean(row["search_intent"]))}</p>',
        f'<p><strong>この記事で勧める整理：</strong>{e(clean(conditions[0]))}'
        '以下では、公式資料で確認できる事実と、記録を作るための助言を分けて示します。</p>',
        f'<p>「{e(row["title"])}」で扱う個別の土地、世帯、証明書についての最終的な可否は、掲載資料だけでは確定しません。'
        '対象情報をそろえ、各資料の担当窓口へ確認してください。</p></section>',
    ]

    condition_slots = {3: 1, 8: 2}
    faq_slots = {1: 0, 4: 1, 7: 2, 10: 3}
    for index, heading in enumerate(headings):
        items = facts_by_section[index]
        parts.append(f'<section class="topic-specific"><h2 class="sec">{e(heading)}</h2>')
        for item in items:
            statement = fact_statement(item)
            source = sources.get(str(item.get("source_url", "")), {}) if isinstance(item, dict) else {}
            source_name = source.get("title") or "公式資料"
            parts.append(f'<p><strong>公式資料で確認できる事実：</strong>{e(statement)}</p>')
            parts.append(
                f'<p><strong>「{e(heading)}」の根拠の範囲：</strong>「{e(statement)}」という記述の根拠は「{e(source_name)}」です。'
                '資料が示していない個別条件へ意味を広げず、対象と確認日を添えて使います。</p>'
            )
        if items:
            joined = "、".join(fact_statement(item).rstrip("。") for item in items)
            parts.append(
                f'<p><strong>この見出しで整理すること：</strong>「{e(heading)}」について、'
                f'確認済みの範囲は「{e(joined)}」です。ここから先の個別判断は未確認事項として分けます。</p>'
            )
        else:
            parts.append(
                f'<p><strong>この見出しの位置付け：</strong>「{e(heading)}」は、上記の確認済み事実を'
                '家族や次の担当へ渡すための編集上の整理です。新しい公的条件を示すものではありません。</p>'
            )
        parts.append(
            f'<p><strong>「{e(heading)}」で勧める記録方法：</strong>{e(prompts[index])}</p>'
        )
        if index in condition_slots and condition_slots[index] < len(conditions):
            parts.append(
                f'<p><strong>森町で照合する条件：</strong>{e(clean(conditions[condition_slots[index]]))}</p>'
            )
        if index in faq_slots and faq_slots[index] < len(faqs):
            item = faqs[faq_slots[index]]
            parts.append(
                f'<p><strong>{e(clean(item["question"]))}</strong>{e(clean(item["answer"]))}</p>'
            )
        if index == 2:
            parts.append(f'<figure><img style="width:100%;height:auto" src="fig1.svg" width="1000" height="560" loading="lazy" alt="{e(row["title"])}の対象と一次資料を照合する場面"><figcaption>対象と一次資料を同じ記録上で照合します。</figcaption></figure>')
        if index == 8:
            parts.append(f'<figure><img style="width:100%;height:auto" src="fig2.svg" width="1000" height="560" loading="lazy" alt="{e(row["title"])}の確認結果を次の担当へ渡す場面"><figcaption>確認済みの事実、未確認事項、次の担当を分けます。</figcaption></figure>')
        parts.append('</section>')
    return ''.join(parts)


def editorial_blocks_day2(row: dict) -> str:
    """Day2実査3件を、固有見出しと手続順に沿って自然文で構成する。"""
    row_id = int(row["id"])
    headings = [str(value).strip() for value in row["section_headings"][:12]]
    notes = DAY2_SECTION_NOTES[row_id]
    facts = list(row["verified_facts"])
    conditions = list(row["morimachi_conditions"])
    faqs = list(row["faqs"])
    sources = list(row["sources"])
    if len(headings) != 12 or len(notes) != 12 or len(facts) < 12:
        raise RuntimeError(f"ID{row_id} Day2固有構成が不足しています")

    def sentence(value: object) -> str:
        if isinstance(value, dict):
            value = value.get("condition") or value.get("statement") or ""
        text = re.sub(r"\s+", "", str(value).strip())
        return text if not text or text[-1] in "。！？" else text + "。"

    def fact_text(item: object) -> str:
        return sentence(item.get("statement", "") if isinstance(item, dict) else item)

    fact_groups = [[] for _ in headings]
    for index, item in enumerate(facts):
        fact_groups[index % len(headings)].append(item)

    intro = {
        236: (
            "森町が管理する道路・河川・水路などと民有地の境界は、申請書、隣接所有者、現地立会、境界確定図を一つの案件として残すと、後の売買や工事で確認経路をたどれます。",
            "現地の杭や舗装端だけで線を決めず、まず管理者を確認してください。森町の申請と、国・県管理地の手続、里道・水路の用途廃止は別に扱います。",
        ),
        243: (
            "森町の景観届出は、行為種別と規模を判定し、着手前の近景・遠景、届出版、変更版、完了写真を同じ案件で追えるようにすると手戻りを減らせます。",
            "確認申請等がある場合とない場合では30日前の起算点が異なります。工事完了後も14日以内の完了届があるため、着工前だけの手続として扱わないでください。",
        ),
        245: (
            "一定規模の土地取引では、契約締結日、取得者、都市計画区域、一団の土地、提出様式を一枚にまとめ、契約日から2週間以内の届出を管理します。",
            "森町内は都市計画区域内5,000平方メートル以上、区域外10,000平方メートル以上が町公式の基準です。複数筆や区域境界は契約前に町へ確認してください。",
        ),
    }[row_id]
    parts = [
        '<section class="direct-answer"><h2 class="sec">先に結論を確認する</h2>',
        f'<p>{e(intro[0])}</p><p>{e(intro[1])}</p></section>',
    ]
    condition_slots = {2: 0, 6: 1, 10: 2}
    faq_slots = {1: 0, 4: 1, 7: 2, 11: 3}
    source_slots = {3: 0, 8: min(1, len(sources) - 1), 11: len(sources) - 1}
    for index, heading in enumerate(headings):
        parts.append(f'<section class="topic-specific"><h2 class="sec">{e(heading)}</h2>')
        for item in fact_groups[index]:
            parts.append(f'<p><strong>公式資料で確認できること：</strong>{e(fact_text(item))}</p>')
        parts.append(f'<p>{e(notes[index][0])}</p><p><strong>記録の作り方：</strong>{e(notes[index][1])}</p>')
        if index in condition_slots:
            parts.append(
                f'<p><strong>森町で照合する条件：</strong>'
                f'{e(sentence(conditions[condition_slots[index]]))}</p>'
            )
        if index in faq_slots:
            faq = faqs[faq_slots[index]]
            parts.append(
                f'<p><strong>{e(sentence(faq["question"]))}</strong>'
                f'{e(sentence(faq["answer"]))}</p>'
            )
        if index in source_slots and sources:
            source = sources[source_slots[index]]
            parts.append(
                f'<p><strong>ここで確認する一次資料：</strong>「{e(source.get("title") or "公式資料")}」。'
                '個別案件では掲載内容の更新日と現在の取扱いを担当窓口で再確認します。</p>'
            )
        if index == 2:
            parts.append(f'<figure><img style="width:100%;height:auto" src="fig1.svg" width="1000" height="560" loading="lazy" alt="{e(row["title"])}の対象と一次資料を照合する場面"><figcaption>対象と一次資料を同じ案件記録で照合します。</figcaption></figure>')
        if index == 8:
            parts.append(f'<figure><img style="width:100%;height:auto" src="fig2.svg" width="1000" height="560" loading="lazy" alt="{e(row["title"])}の確認結果を次の担当へ渡す場面"><figcaption>提出版、変更版、確認結果を分けて残します。</figcaption></figure>')
        parts.append('</section>')
    perspective = {
        236: (
            "境界の相談では、現地でそれらしく見える線より、管理者・測量・協議の経路を残すことを優先します。確定前の線を前提に売買や工事を進めず、正式な確定図へ戻れる記録を家族へ渡します。",
            "用途廃止や払い下げを望む場合も、境界確定とは別の判断が続きます。私は手続名を一つにまとめず、費用と担当窓口を分けて確認する進め方が安全だと考えます。",
        ),
        243: (
            "景観届出は書類を提出するだけでなく、計画時の外観と完成後の状態を結ぶ手続です。写真の撮影地点と設計版をそろえれば、変更が生じたときにも何を届け直すか判断しやすくなります。",
            "私は、工事日程を先に固定して30日前の期限へ押し込むより、規模判定と事前相談を設計初期へ置く方が現実的だと考えます。届出対象外の判断も、使った数値と図面版を残します。",
        ),
        245: (
            "土地取引届出は、面積だけを見ると一団の土地や区域境界を見落とします。私は契約前に全筆、取得者、区域、契約形態を一枚へ集め、届出要否を町へ示せる状態にすることを勧めます。",
            "契約後は2週間という短い期限が動きます。引渡日ではなく契約締結日を起点にし、現行様式と受付控えまで同じ契約ファイルへ残すと、後から提出経路を説明できます。",
        ),
    }[row_id]
    parts.append(
        '<section class="topic-specific"><h2 class="sec">大石の視点</h2>'
        f'<p>{e(perspective[0])}</p><p>{e(perspective[1])}</p></section>'
    )
    return ''.join(parts)


def editorial_blocks_v2(row: dict) -> str:
    """固有事実を主役にし、意味・注意・手順を自然文で展開する。"""
    if row.get("section_paragraphs"):
        return editorial_blocks_curated(row)
    if int(row["id"]) in DAY2_SECTION_NOTES:
        return editorial_blocks_day2(row)
    if row.get("editorial_mode") == "fact-ledger":
        return editorial_blocks_fact_ledger(row)
    title = str(row["title"])
    subject = title.split("｜", 1)[0]
    short_subject = re.sub(r"^森町(?:で|の)?", "", subject).strip()
    facts = list(row["verified_facts"])
    conditions = [str(value).strip() for value in row["morimachi_conditions"]]
    faqs = list(row["faqs"])
    sources = list(row["sources"])
    source_headings = [str(value).strip() for value in row["section_headings"]]
    method, authorities, memo = category_context(row["category"])

    def clean(text: object) -> str:
        value = re.sub(r"\s+", "", str(text).strip())
        value = value.replace("。。", "。").replace("？？", "？")
        value = value.replace("「「", "「").replace("」」", "」")
        if value and value[-1] not in "。！？":
            value += "。"
        return value

    def fact_text(item: object) -> str:
        return clean(item.get("statement", "") if isinstance(item, dict) else item)

    def focus(index: int) -> str:
        value = source_headings[index % len(source_headings)]
        value = value.replace(title, "").replace(subject, "")
        if short_subject:
            value = value.replace(short_subject, "")
        value = re.sub(r"^(の|について|では|を)+", "", value).strip(" ：。")
        return (value if len(value) >= 5 else "確認する項目")[:76]

    def role_label(role: object) -> str:
        labels = {
            "primary": "中心となる一次資料",
            "official-secondary": "国や所管機関の補足資料",
            "森町公式・主資料": "森町の中心資料",
            "森町公式・補完資料": "森町の補足資料",
            "国・県・所管機関": "国・県の制度資料",
        }
        raw = str(role or "").strip()
        return labels.get(raw, raw if raw and re.search(r"[ぁ-んァ-ヶ一-龠]", raw) else "確認用の公式資料")

    guidance = [
        (
            "最初に決めるのは、この記事で確かめた情報を何の判断に使うかです。数字、書類、区域、対象者など、答えの単位を一つに絞ると、似た案内を混ぜずに済みます。",
            f"確認表の一行目には{memo}を書きます。未定の項目には確認先と確認日を置き、空欄のまま結論へ進まないようにします。",
            "この段階では、できる・できないを決める必要はありません。まず確定した事実、条件付きで使える情報、まだ分からない点の三つに分けます。",
        ),
        (
            "一次情報から確定できる範囲を見極めます。見出しだけで判断せず、対象となる人や場所、基準日、単位、注記まで確認します。",
            f"確認の起点は{authorities}です。公開日と適用日が同じとは限らないため、引用や申請に使う日付を別に控えます。",
            "別の資料と数値や条件が違うときは、新しい方へ機械的に寄せません。定義、集計方法、対象期間が同じかを先に比べます。",
        ),
        (
            "森町で条件を当てはめるときは、町全体の説明と個別の対象を切り分けます。地区、集計単位、利用者、時期が変われば必要な確認も変わります。",
            "町の案内で確認できることと、県・国・事業者・所有者へ聞くことを分けておくと、一つの窓口へ同じ質問を繰り返さずに済みます。",
            "地図や一覧を使う場合は、凡例、縮尺、基準日、対象範囲を一緒に保存します。画面の一部分だけを切り取って根拠にしないでください。",
        ),
        (
            "資料は、知りたいことに直接答えるものから集めます。関連しそうな資料を先に増やすより、主資料、補足資料、個別確認の順に並べる方が読み違いを防げます。",
            "PDFや表を保存するときは、資料名、ページ番号、確認日をファイル名かメモへ残します。数字だけを転記すると、後から単位や注記を確かめられません。",
            "必要書類がある場合は、原本か写しか、発行期限があるか、本人以外でも取得できるかを分けて確認します。取得前に用途を伝えると手戻りを減らせます。",
        ),
        (
            "窓口へ尋ねる前に、知りたいことを一文で説明できるようにします。すでに確認した資料名と、資料だけでは決められなかった点を添えてください。",
            "問い合わせでは、答えだけでなく根拠となるページや担当部署も確認します。担当外なら、次の窓口へ何を伝えればよいかを聞いて記録します。",
            "現地確認が必要なテーマでは、安全と私有地への配慮を優先します。写真には日付と方向を残し、見えていない範囲を推測で補いません。",
        ),
        (
            "日付を扱うときは、基準日、受付日、実行日、再確認日を別々に置きます。一つの日付で全体を代表させないことが大切です。",
            "年度をまたぐ案内は、前年の条件をそのまま使わず、当年資料が公開された時点で差分を見ます。月次資料なら何月時点かも明記します。",
            "回答待ちがある場合は、自分が次に判断する日を決めます。返答がなければ保留するのか、別案へ切り替えるのかも先に共有します。",
        ),
        (
            "見えにくい負担として、確認にかかる時間、移動、資料取得、維持管理を分けて考えます。金額が示されないテーマでも手間は残ります。",
            "費用が発生しないテーマでも、古い情報を使うことによる手戻りや、家族が同じ調査を繰り返す負担があります。確認記録を残すこと自体が負担軽減になります。",
            "見積りや料金を比べるときは、含まれる作業と含まれない作業をそろえます。金額の大小だけでなく、追加対応が必要になる条件も確認してください。",
        ),
        (
            "家族や関係者へは、結論だけを送らず、根拠にした資料と確認日を添えます。前提が変われば答えも変わることを共有します。",
            "情報を集める人と決定する人が異なる場合は、誰がどこまで確認したかを残します。一人の記憶だけに頼らない形にしてください。",
            "意見が分かれたときは、賛否より先に、確定事実、希望、負担、保留条件を並べます。何が分かれば次へ進めるかを決める方が話し合いやすくなります。",
        ),
        (
            "判断案は、情報を採用する案だけでなく、条件が整うまで待つ案と、今回は使わない案も残します。選択肢を二つに絞りすぎないでください。",
            "最初の行動は、資料を一件確認する、窓口を特定する、対象を記すなど、小さく区切れます。大きな手続きや判断を最初の一歩にする必要はありません。",
            "保留にするときは、理由と再確認日を記録します。情報不足で止まっているのか、条件が合わないと判断したのかを分けておけば、再開しやすくなります。",
        ),
        (
            "記録には、確認者、確認日、資料名、分かったこと、残った疑問、次の担当を残します。結論だけでは、前提が変わったときに見直しができません。",
            "住所と地番、通称と正式名称、年度と暦年など、似ていて役割の違う情報は欄を分けます。元資料の表記は書き換えずに保存します。",
            "更新版を入手したら、古い版を黙って上書きしません。何が変わったかを短く残し、個人情報を含む資料は共有範囲も確認します。",
        ),
        (
            f"大石の視点では、一つの答えへ急いでまとめません。{memo}など、主題に関係する事実を順に分ける方が選択肢を守れます。",
            "私は、現地を見ていない事項や資料で確認できない内容を、経験談のように断定しません。分からない点は、次に確かめる条件として明記します。",
            "まだ最終判断をしていない段階でも、資料と確認記録は役立ちます。家族が後から同じ問いに向き合える形を整えることを優先します。",
        ),
        (
            "最後に、結論が資料で裏付けられているかを見直します。事実、条件、期限、確認先のどれかが欠けていれば、判断を一段戻します。",
            "今日できる一歩は、主資料を開いて基準日を記すことです。その後に、窓口、現地、家族、専門家のうち次に確認する相手を一つ決めます。",
            "実行直前には同じ公式ページを開き、更新の有無を確かめます。ページURLだけでなく、自分たちの対象と未確認事項を添えて共有してください。",
        ),
    ]

    extra_guidance = [
        (
            f"「{focus(0)}」の答えを、数値、対象者、場所、時期、手続きのどれとして残すのかを決めます。答えの形が決まれば、不要な資料を減らせます。",
            "似た名称の制度や統計があるときは、正式名称をそのままメモします。略称だけで保存すると、後で別の資料と取り違えるおそれがあります。",
            "今回の判断に使わない情報も、誤りとして捨てるのではなく、対象外になった理由を残します。別の時期や家族には必要になる場合があります。",
        ),
        (
            f"「{focus(1)}」を読む前に、資料の作成者と掲載元を確認します。転載資料なら、可能な範囲で元の公表資料まで戻ってください。",
            "表に数字が並ぶ場合は、人数、世帯、円、平方メートルなどの単位を見ます。割合なら分母、合計なら重複の有無も確認します。",
            "資料が説明していない範囲を、書いてある事実から推測しないことも重要です。個別判断が必要な点は、未確認事項として切り分けます。",
        ),
        (
            f"「{focus(2)}」を住所へ当てはめる場合は、町名だけでなく地番や区域、施設名など、公式資料が採用している単位に合わせます。",
            "同じ森町内でも、対象区域や担当、利用条件が同じとは限りません。町全体の平均や一般案内を、個別地点の答えへ置き換えないでください。",
            "現況と資料が違って見える場合は、どちらかを誤りと決めず、資料の基準日と現地の確認日を並べて担当窓口へ伝えます。",
        ),
        (
            f"「{focus(3)}」に使う資料は、確認した順ではなく役割順に並べます。結論の根拠、条件の補足、個別照会の回答が分かる構成にします。",
            "表計算へ転記する場合も、元資料のURLと該当箇所を同じ行へ残します。転記値だけでは、更新時の差分を確かめられません。",
            "資料の版が複数あるときは、最新版だけでなく、今回の基準日に対応する版を選びます。最新版が過去時点の説明に適するとは限りません。",
        ),
        (
            f"「{focus(4)}」の問い合わせでは、質問を一度に広げすぎません。まず主題に直接関係する一点を確認し、回答に応じて次の質問へ進みます。",
            "電話で確認した場合は、部署名、確認日時、回答の要点を残します。担当者個人の名前を必要以上に共有せず、公式の連絡先を記録します。",
            "法務、税務、医療、構造、安全性など専門判断が必要な内容は、担当部署の案内だけで結論を出さず、必要な資格者や所管機関へつなぎます。",
        ),
        (
            f"「{focus(5)}」を時系列にするときは、資料を確認した日と、資料が示す基準日を別の列に置きます。この二つを混ぜると比較を誤ります。",
            "締切がある場合は、締切日だけでなく、資料取得、家族確認、窓口相談を始める日も決めます。休日や郵送期間も見込んでください。",
            "定期的に更新される情報は、毎回同じ時点で確認すると変化を追いやすくなります。比較の途中で集計時点を変えないようにします。",
        ),
        (
            f"「{focus(6)}」の負担を見積もるときは、調査を担当する人の時間も含めます。無料の資料でも、探し直しや移動には負担が生じます。",
            "家族が遠方にいる場合は、郵送、オンライン共有、現地確認の担当を分けます。一人がすべて抱える前提にしないことが継続の条件です。",
            "費用や手間が予想より増えたときに、どこで中止・保留するかを先に決めます。続けることだけを前提にすると、判断を急ぎやすくなります。",
        ),
        (
            f"「{focus(7)}」を共有するときは、要約と元資料を分けます。要約には作成者と日付を付け、解釈が含まれることが分かるようにします。",
            "個人情報や権利関係を含む資料は、家族全員へ一律に送らず、必要な人だけが見られる場所で管理します。共有リンクの期限も確認します。",
            "家族から別の情報が出た場合は、どちらが正しいかをその場で決めず、出典と基準日を確認します。新しい情報も同じ確認表へ追加します。",
        ),
        (
            f"「{focus(8)}」の代案は、目的を変えずに方法を変える案と、目的自体を見直す案に分けます。何を守りたいかが分かると比較しやすくなります。",
            "公式資料だけで決められない場合は、窓口確認、専門相談、現地確認のどれを先に行うかを選びます。すべてを同時に始める必要はありません。",
            "見送る案にも、再検討する条件を付けます。制度の更新、家族状況の変化、資料の入手など、再開のきっかけを具体的にします。",
        ),
        (
            f"「{focus(9)}」の記録は、第三者が読んでも確認経路をたどれることが目標です。自分だけに通じる略称や評価語は避けます。",
            "回答を要約するときは、事実と自分の判断を別の欄に書きます。担当機関の説明を、自分の結論として言い換えないようにしてください。",
            "記録を終える前に、元資料へ戻れるリンクが開くか確認します。リンク切れに備え、資料名と担当部署も文字で残します。",
        ),
        (
            f"「{focus(10)}」では、公表事実と私の意見を明確に分けます。意見は判断の順序を提案するもので、個別の可否を保証するものではありません。",
            f"小さな不動産業者としては、{memo}を一度に結論へ結び付けず、資料で確かめられる範囲から順番に整理することを勧めます。",
            "相談者がまだ決めていない状態を尊重し、情報を採用する案、追加確認する案、保留する案、使わない案を同じ表で比べます。結論を迫ることを相談の目的にしません。",
        ),
        (
            f"「{focus(11)}」を確認したら、主資料一件、補足資料一件、未確認事項一件を声に出して説明してみます。説明できない部分が次の確認対象です。",
            "まとめには、分かったことだけでなく、今回の資料では分からなかったことも残します。情報がないことと、対象外であることを混同しないでください。",
            "最後の確認日を記したら、次に見直す時期も決めます。更新が多い情報は実行直前、変わりにくい資料は前提が変わったときに確認します。",
        ),
    ]

    final_guidance = [
        "この整理ができれば、次に開く資料と尋ねる相手を一つに絞れます。",
        "確定できた範囲が狭くても、資料が保証している範囲を正しく残す方が安全です。",
        "個別条件を確認した結果は、町全体の説明と混ぜずに対象ごとの記録へ戻します。",
        "集めた資料ごとに役割を一行で書けば、後から不要な重複を整理できます。",
        "回答を受けた後は、当初の質問に答えられたかを確認し、別の論点を同じ回答へ混ぜません。",
        "時系列の最後には次の確認日を置き、更新情報を追う担当も決めておきます。",
        "負担が大きいと分かった場合は、確認範囲を狭めることも現実的な選択です。",
        "共有後に認識が一致したかを確かめ、異なる理解は確認表の注記として残します。",
        "代案にも根拠資料を付け、単なる思いつきではなく比較できる選択肢にします。",
        "最後に未確認事項だけを一覧にし、次の担当がそのまま動ける状態へ整えます。",
        "私は、資料で確認できたことより先へ結論を広げない姿勢を大切にします。",
        "ここまでの記録を一枚にまとめれば、次の確認で最初から調べ直す必要がありません。",
    ]

    if row["category"] == "統計資料":
        extra_guidance[1] = (
            f"「{focus(1)}」は、資料の作成者、統計名、表題を確認してから読みます。転載表なら元の公表資料まで戻ってください。",
            "人口と世帯、実数と割合、月次値と調査年値を分けます。割合は分母、合計は集計範囲を確認します。",
            "資料が説明していない変化の原因を、数字だけから推測しません。読み取れない範囲も記録に含めます。",
        )
        extra_guidance[2] = (
            f"「{focus(2)}」を地区別に見る場合は、町名別と行政区別など、資料が採用する区分をそのまま使います。",
            "町全体の値と地区別の値を並べるときは、合計が一致する定義かを確認します。集計外の区分や注記も見落とさないでください。",
            "異なる基準日の表は別の列に置きます。同一時点の差に見える配置を避け、表頭にも基準日を入れます。",
        )
        extra_guidance[3] = (
            f"「{focus(3)}」に使った表は、資料名、表番号、基準日を一組で保存します。",
            "転記したセルには元表の列名と行名を残します。独自に合計や割合を計算した場合は、計算式と加工日を記録します。",
            "改訂版が出たときは、数値だけでなく定義や注記の変更も確認します。過去版を上書きせず差分を残してください。",
        )
        extra_guidance[4] = (
            f"「{focus(4)}」を問い合わせるときは、統計名、表番号、基準日、知りたい定義を伝えます。",
            "担当部署の説明は、どの統計系列についての回答かを明記します。別系列の数字へ同じ説明を広げないでください。",
            "e-Statで再確認するときは、調査名、地域、調査年を指定します。検索結果の一覧だけでなく統計表を開きます。",
        )
        extra_guidance[5] = (
            f"「{focus(5)}」は、調査日、公表日、資料を確認した日を分けて時系列にします。",
            "月次値は毎月同じ基準日のものを並べ、国勢調査は調査年ごとの系列として扱います。途中で系列を切り替えません。",
            "次に値を更新する日を決め、同じ表と同じ項目を確認します。更新がなければ、その事実も記録します。",
        )
        extra_guidance[6] = (
            f"「{focus(6)}」を調べる作業は、表の探索、定義確認、転記、照合に分けます。",
            "家族や関係者が別々に集計しないよう、採用する統計系列を先に共有します。",
            "比較に必要な表がそろわなければ、推計に進まず、どの値が不足しているかを示します。",
        )
        extra_guidance[7] = (
            f"「{focus(7)}」を共有するときは、要約表と元の統計表を一緒に渡します。",
            "独自に付けた見出しや色分けは、公表資料の表記と区別します。加工者と加工日も添えてください。",
            "別の数字が提示された場合は、正誤を先に決めず、統計名、基準日、単位を照合します。",
        )
        extra_guidance[8] = (
            f"「{focus(8)}」の代案として、同じ系列だけで比較する方法と、比較せず各値の定義を説明する方法があります。",
            "二つの値を一つのグラフへ入れない判断も有効です。見た目の連続性より、統計の一貫性を優先します。",
            "保留した比較には、再開に必要な資料名と基準日を残します。新しい表が公表されたときに確認できます。",
        )
        extra_guidance[9] = (
            f"「{focus(9)}」の記録は、第三者が同じ統計表を開けることを目標にします。",
            "事実の転記と、その数字から考えたことを別欄にします。解釈を公表事実のように書かないでください。",
            "リンクが変わっても探せるよう、統計名、表題、公表機関を文字で残します。",
        )
        extra_guidance[10] = (
            f"「{focus(10)}」では、数字の大きさより先に統計系列と基準日を見ます。",
            "小さな不動産業者としても、人口統計だけで地区や個別物件の価値を断定しません。使える範囲を限定します。",
            "家族へ説明するときは、数字、出典、基準日、比較できない点を一組にします。",
        )
        extra_guidance[11] = (
            f"「{focus(11)}」を確認したら、採用した統計名と基準日を読み上げて一致を確かめます。",
            "まとめには、確定した値だけでなく、系列が違うため比較しなかった値も残します。",
            "次回は同じ公表ページと表を開き、定義や注記が変わっていないかを確認します。",
        )
        guidance[2] = (
            "森町の統計を使うときは、対象地域と集計単位を確認します。町全体、地区別、年齢別など、集計範囲が違う数字を同列に置かないでください。",
            "同じ人口や世帯を扱う資料でも、調査方式と基準日が違えば値は一致しません。差があること自体を増減の根拠にしないことが重要です。",
            "表や一覧を保存するときは、表題、基準日、単位、注記を一緒に残します。数字の列だけを切り取って共有しないでください。",
        )
        guidance[3] = (
            "統計資料は、知りたい指標を直接掲載する表から集めます。人口、世帯、年齢、地区など、別の指標を同じ表へ混ぜないようにします。",
            "表計算へ転記するときは、列名と単位を元資料に合わせます。並べ替えや再計算をした場合は、加工したことを注記してください。",
            "過去値を確認する場合は、最新版だけでなく比較する年の資料も保存します。後から定義変更の有無を確かめられる形にします。",
        )
        guidance[4] = (
            "資料の定義が分からないときは、統計名、表番号、基準日、該当する列を示して担当部署へ尋ねます。数字だけを読み上げるより確認が早くなります。",
            "回答を受けたら、どの表のどの定義についての説明かを記録します。別の統計系列へ回答を広げないでください。",
            "e-Statを使う場合も、調査名、地域、調査年をそろえます。森町公式の月次資料とは別系列として扱います。",
        )
        guidance[6] = (
            "統計を扱う負担は、資料の探索、定義の確認、転記、更新差分の確認に分けます。無料で取得できる資料でも作業時間は必要です。",
            "家族や関係者が同じ数字を調べ直さないよう、表名と確認日を共有します。数字だけのメモは出典確認の手間を増やします。",
            "比較に必要な年や地区がそろわない場合は、無理に推計せず、比較できない理由を結論に含めます。",
        )
        guidance[8] = (
            "二つの統計を直接比べられない場合は、同じ統計系列の別時点を使う案、比較を保留する案、説明を定性的な範囲にとどめる案があります。",
            "最初の行動は、統計名と基準日を一件ずつ確認することです。すべての表を集めてから考える必要はありません。",
            "比較を見送る場合も、定義、基準日、単位のどこがそろわなかったかを残します。資料更新時に必要な箇所だけ見直せます。",
        )
        guidance[10] = (
            f"大石の視点では、統計名、基準日、単位、対象地域を分けます。数字の印象だけで地域や物件の状態を説明しないことが大切です。",
            "私は、公表資料で確かめられない原因を経験談のように補いません。数値差の理由は、調査方式と基準日の違いを確認してから考えます。",
            "統計は判断材料の一つです。家族へ渡すときは、数字と出典、基準日、読み取れない範囲を一組で残します。",
        )
    elif row["category"] == "高齢者福祉":
        extra_guidance[1] = (
            f"「{focus(1)}」は、森町の掲載ページと担当部署を確認してから読みます。転載された制度名だけで対象を判断しません。",
            "年齢、世帯状況、心身の状態、利用回数、費用を別の項目として読みます。いずれか一つだけで対象を決めないでください。",
            "掲載資料が説明していない本人の可否は推測せず、相談時に確認する項目として残します。",
        )
        extra_guidance[2] = (
            f"「{focus(2)}」を本人へ当てはめるときは、現在の生活状況と希望する支援を具体的にします。",
            "町全体の制度説明と、本人に利用が認められることは同じではありません。相談先の確認を経て判断します。",
            "本人の状態が変わった場合は、以前の相談結果をそのまま使わず、変化した点を伝えて再確認します。",
        )
        extra_guidance[5] = (
            f"「{focus(5)}」は、相談日、申込日、利用開始日、見直し日を並べて管理します。",
            "受付期間や利用回数が示されている場合は、いつから数えるのかを確認します。家族の都合だけで起算日を決めません。",
            "次の相談日を決め、本人の状態や家族状況に変化があれば予定日前でも連絡します。",
        )
        guidance[2] = (
            "森町の福祉サービスを本人へ当てはめるときは、年齢、心身の状態、世帯状況、現在受けている支援を分けて確認します。",
            "サービス名が似ていても、対象条件や相談窓口は同じとは限りません。本人の希望を置き去りにせず、家族の負担だけで選ばないようにします。",
            "緊急性がある場合は、通常の情報整理より安全確保と専門窓口への連絡を優先します。この記事だけで利用可否を判断しないでください。",
        )
        guidance[4] = (
            "相談前に、本人の状態、困っている場面、希望する支援、家族が対応できる範囲を短くまとめます。病名だけでは生活上の困りごとが伝わりません。",
            "地域包括支援センターへ相談した内容は、次の担当や必要資料と一緒に記録します。制度名を聞いただけで利用できると決めないでください。",
            "医療判断や介護認定が関係する内容は、町の案内と医療・介護の専門判断を分けます。本人の同意と個人情報の扱いにも配慮します。",
        )
        guidance[6] = (
            "福祉サービスの負担は、利用料だけでなく、送迎、見守り、申請、家族の時間、利用開始までの待機も含めて考えます。",
            "家族が遠方にいる場合は、日常の連絡役、緊急時の連絡先、手続きの担当を分けます。一人で抱え続ける前提にしないことが重要です。",
            "希望する支援が対象外の場合は、代替サービスや別の相談先を確認します。対象外と支援不要を同じ意味にしないでください。",
        )
        guidance[5] = (
            "日付は、相談日、申込日、利用開始日、見直し日を分けます。本人の状態が変わった場合は、予定日を待たずに相談し直します。",
            "年度をまたぐ案内は、対象条件、利用回数、費用、受付方法の変更を確認します。前年の利用経験だけで当年の条件を決めないでください。",
            "家族や事業者からの回答待ちがある場合は、次に連絡する日を決めます。支援が途切れないよう、緊急時の相談先も確認します。",
        )
        guidance[11] = (
            "最後に、本人の希望とサービスの対象条件が資料で確認できているかを見直します。未確認なら利用できると断定しません。",
            "今日できる一歩は、本人の状態と困っている場面をまとめ、地域包括支援センターへ相談することです。",
            "利用開始前には、対象条件、費用、連絡先、家族の担当を再確認します。状態が変わったときの連絡方法も共有してください。",
        )
        guidance[10] = (
            f"大石の視点では、本人の年齢・状態、家族状況、希望する支援を分けます。住まいの判断を先に決めず、暮らしを続ける条件から整理します。",
            "私は、本人や家族から聞いていない事情を経験談のように補いません。分からない点は、地域包括支援センターへ相談する項目として残します。",
            "まだ住まいや資産の扱いを決めていない段階でも、支援の記録は役立ちます。本人が選べる情報量と順序を整えることを優先します。",
        )

    all_fact_texts = [fact_text(item) for item in facts]
    for value in CRITICAL_FACTS.get(int(row["id"]), []):
        cleaned = clean(value)
        if cleaned not in all_fact_texts:
            all_fact_texts.append(cleaned)
    facts_by_section = [[] for _ in SECTION_HEADINGS]
    for index, value in enumerate(all_fact_texts):
        facts_by_section[index % len(SECTION_HEADINGS)].append(value)

    parts = [
        '<section class="direct-answer"><h2 class="sec">先に結論を確認する</h2>',
        f'<p>{e(row["search_intent"])}場合は、まず資料の名称、対象、基準日をそろえます。'
        f'確認の起点は「{e(sources[0].get("title") or "森町の公式資料")}」です。個別条件は、資料の本文と担当窓口で確かめてください。</p>',
        '<p>この記事では、公表済みの事実と、個別に確認する条件を分けて扱います。数値や制度名だけを抜き出さず、いつ・誰に・どこで当てはまる情報かまで記録します。</p>',
        '</section>',
    ]

    condition_slots = {1: 0, 5: 1, 8: 2}
    faq_slots = {0: 0, 3: 1, 6: 2, 9: 3}
    source_start = len(SECTION_HEADINGS) - len(sources)
    source_slots = {source_start + offset: offset for offset in range(len(sources))}

    for index, heading in enumerate(SECTION_HEADINGS):
        parts.append(f'<section class="topic-specific"><h2 class="sec">{e(heading)}</h2>')
        if facts_by_section[index]:
            parts.extend(f'<p>{e(value)}</p>' for value in facts_by_section[index])
        elif not all_fact_texts:
            parts.append(
                f'<p>「{e(focus(index))}」に対応する固有事実は、現在の確認台帳ではまだ一次情報の本文まで記録できていません。'
                '推測で補わず、下書きのまま確認を続けます。</p>'
            )
        combined_guidance = [
            clean(guidance[index][offset] + extra_guidance[index][offset])
            for offset in range(3)
        ]
        combined_guidance[1] = clean(
            combined_guidance[1]
            + f"この区別は「{focus((index + 4) % len(SECTION_HEADINGS))}」を整理するときにも使います。"
        )
        combined_guidance[-1] = clean(
            combined_guidance[-1]
            + final_guidance[index]
            + f"確認結果は「{focus((index + 8) % len(SECTION_HEADINGS))}」の記録へ反映します。"
        )
        parts.extend(f'<p>{e(value)}</p>' for value in combined_guidance)
        if index in condition_slots and condition_slots[index] < len(conditions):
            parts.append(f'<p><strong>森町で当てはめる条件：</strong>{e(clean(conditions[condition_slots[index]]))}</p>')
        if index in faq_slots and faq_slots[index] < len(faqs):
            item = faqs[faq_slots[index]]
            parts.append(
                f'<p><strong>{e(clean(item["question"]))}</strong>{e(clean(item["answer"]))}</p>'
            )
        if index in source_slots:
            source = sources[source_slots[index]]
            parts.append(
                f'<p>「{e(source.get("title") or "公式資料")}」は、{e(role_label(source.get("role")))}です。'
                '本文で使う箇所の見出し、対象年度、確認日を一緒に控えます。</p>'
            )
        if index == 2:
            parts.append(f'<figure><img style="width:100%;height:auto" src="fig1.svg" width="1000" height="560" loading="lazy" alt="森町で{e(row["search_intent"])}ため、資料と現地を照合する場面"><figcaption>対象地点と一次資料を同じ確認表で照合します。</figcaption></figure>')
        if index == 8:
            parts.append(f'<figure><img style="width:100%;height:auto" src="fig2.svg" width="1000" height="560" loading="lazy" alt="{e(subject)}について、確認から家族共有へ進む順序"><figcaption>確認済み、未確認、次の担当を分けて残します。</figcaption></figure>')
        parts.append('</section>')
    return ''.join(parts)

def render(row: dict, url: str, prev_url: str, next_url: str) -> str:
    title, intent, category = row["title"], row["search_intent"], row["category"]
    details = topic_details(row)
    article_key = re.sub(r"^森町(?:で|の)?", "", title.split("｜", 1)[0]).strip()
    focus = re.sub(r"^(で|の|を|が|に)+", "", title.split("｜", 1)[0].replace("森町", "").strip())
    out_dir = ROOT / url.strip("/")
    out_dir.mkdir(parents=True, exist_ok=True)
    for index, name in enumerate(("cover.svg", "fig1.svg", "fig2.svg"), 1):
        (out_dir / name).write_text(svg(row, index), encoding="utf-8", newline="\n")
    order = list(range(1, 11))
    random.Random(int(row["id"])).shuffle(order)
    order = [0] + order + [11]
    blocks = []
    for position, idx in enumerate(order):
        blocks.append(f'<section><h2 class="sec">{e(SECTION_HEADINGS[idx])}</h2>')
        variants = paragraph_set(row, idx)
        shift = (int(row["id"]) + idx) % 4
        variants = variants[shift:] + variants[:shift]
        blocks.extend(f"<p>{e(p)}</p>" for p in variants)
        if position == 2:
            blocks.append(f'<figure><img style="width:100%;height:auto" src="fig1.svg" width="1000" height="560" loading="lazy" alt="森町の地形と暮らしの中で{e(intent)}ための確認場面"><figcaption>資料だけでなく、森町の場所と暮らしの条件を重ねて確認します。</figcaption></figure>')
        if position == 7:
            blocks.append(f'<figure><img style="width:100%;height:auto" src="fig2.svg" width="1000" height="560" loading="lazy" alt="{e(title)}について資料、現地、窓口、家族共有へ進む順序"><figcaption>確定事項と未確認事項を分け、次の担当と期限を決めます。</figcaption></figure>')
        blocks.append("</section>")
    faq = safe_faqs(row)
    faq_html = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in faq)
    faq_json = {"@context":"https://schema.org", "@type":"FAQPage", "mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq]}
    subject = title.split("｜", 1)[0]
    desc = f"{subject}。対象条件、必要資料、森町の公式窓口、確認する順番を分かりやすく整理します。実行前の注意点と家族へ残す記録も案内します。"
    cover_alts = {
        65: "森町の道路事故地点から治療・警察・森町国保・相手方保険へ四本の連絡線を分ける事故連絡票",
        57: "森町国保の領収書を暦月・受診者・医療機関・入院外来へ分ける高額療養費台帳",
        20: "取り壊した家屋の輪郭から森町の課税台帳と法務局の登記記録へ二本の確認路を分ける一件台帳",
        21: "妊婦健診一回ごとに週数・受診先・通常受診票・追加票・精算方法を一行へまとめる受診票台帳",
        24: "赤ちゃんの健康保険加入先を分け、資格情報から森町こども医療費受給者証へつなぐ一件引継ぎ票",
        1: "離婚成立日を2026年3月31日以前と4月1日以後へ分け、親権・養育費・財産分与を整理する一件表",
        168: "森町の地域計画と目標地図を、所有者・現在耕作者・将来担い手・更新日の四欄へ分ける一筆照合票",
        172: "電気柵を買う前に柵線・道路水路・注意表示・電源装置・点検動線を一枚へ置く安全配置図",
        91: "運転経歴証明書助成と公共交通利用券助成を、起算日・期限・担当課ごとに分ける二申請台帳",
        180: "伐採開始前の届出、伐採完了報告、造林完了報告を三つの期限でつなぐ森林工程表",
        149: "狭い道路沿いの建替え前に、道路区域・町有道路境界・基準時中心線・後退候補線を分ける接道確認図",
        159: "地価公示・取引価格情報・森町用途図を別資料として置く土地価格の比較条件カード",
        166: "農地転用の許可書・申請図と着工前の工事範囲を照合する一件ファイル",
        176: "森林土地所有者届の全対象地番と位置図番号を一対一で照合する全筆位置図",
        17: "戸籍の振り仮名通知に載る家族を行へ分け、氏と名を個別に確認する判定表",
        190: "店舗の看板から静岡県の屋外広告物許可と森町の景観届出へ確認経路を分ける図",
        194: "入札参加の資格区分・申請受付・名簿登載・電子入札登録を四段階で確認する図",
        249: "課税明細と四つの固定資産証明を提出先の必要項目から選ぶ書類ルーティング図",
        288: "森町の公共施設を計画・予算・入札・完了の証拠段階ごとに結ぶ修繕資料索引",
        208: "年代と資料種別の二軸から、森町史の最初の一冊を選ぶ巻別ルーティング表",
        292: "茶畑の一筆を挟み、譲渡人と譲受人が権利の種類を分けて当事者情報票を確認する場面",
        108: "木造住宅の耐震診断結果、補強計画、工事見積書を同じ行で照合する確認表",
        104: "中古住宅の増築部を囲み、課税明細・登記事項・現況写真の三列で差異を確認する照合表",
        122: "森町の山並みを背景に、所有者が空き家の玄関前で内覧案内表、鍵、危険箇所、設備を確認する場面",
        123: "森町の山並みと空き家を背景に、所有者が公開画面、変更届、抹消届、鍵の引継ぎを確認する場面",
        124: "森町の山並みと空き家を背景に、所有者が屋根・水回り・残置物の写真と修繕見積りを照合する場面",
        125: "森町の山並みと空き家を背景に、家族が施工写真・領収書・保証書を一件の修繕履歴へまとめる場面",
        126: "森町の空き家を背景に、近隣からの異常連絡を所有者・現地担当・緊急窓口へ振り分ける連絡カード",
        127: "森町の空き家を背景に、台風接近前と通過後の写真を同じ部位番号で比べる安全点検票",
        128: "森町の空き家を背景に、動物の糞・毛・足跡へ触れず写真番号で記録する安全確認票",
        129: "森町の実家を背景に、巡回・支払・連絡・書類保管を家族四人の役割へ分けた引継ぎ表",
        131: "森町の土地と家を背景に、取得を知った日と遺産分割成立日の二つの時計を示す相続登記期限表",
        132: "森町の土地家屋を背景に、課税明細・名寄帳・登記事項を三方向から照合する相続資産一覧",
        133: "森町の実家を背景に、兄弟が利用・費用・修繕・将来判断を話し合う共有合意表",
        130: "森町の集落で道路沿いの空き家を外から確認し、屋根・外壁・立木の危険連絡を一件記録にする場面",
    }
    cover_alt = cover_alts.get(int(row["id"]), f"{title}の確認場面を森町の山並み、家、道、資料で描いた表紙")
    webpage = {"@context":"https://schema.org", "@type":"WebPage", "name":title, "url":SITE+url, "description":desc, "dateModified":TODAY, "author":{"@type":"Person","name":"大石浩之"}}
    breadcrumb = {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"静岡県森町ライフハック","item":SITE+"/"},{"@type":"ListItem","position":2,"name":category,"item":SITE+CATEGORY_PATH.get(category,"/guide/")},{"@type":"ListItem","position":3,"name":title,"item":SITE+url}]}
    role_labels = {
        "primary": "森町公式",
        "official-secondary": "国・県などの公式",
    }
    sources = "".join(
        f'<a class="official-link" href="{e(src["url"])}" target="_blank" rel="noopener">'
        f'{e(src.get("title") or "一次情報")} '
        f'<span>{e(role_labels.get(src.get("role"), "公式確認"))}</span></a>'
        for src in row["sources"]
    )
    category_hub = CATEGORY_PATH.get(category, "/guide/")
    # 未公開の第4期ページへ連鎖させず、常時公開されているハブだけを案内する。
    # これにより、コホート単位の公開でも未審査ページへの導線が生まれない。
    related = "".join([f'<a class="official-link" href="{category_hub}">{e(category)}の記事を状況から選ぶ</a>', '<a class="official-link" href="/guide/morimachi-complete-guide/">森町総合ガイド</a>', '<a class="official-link" href="/life/living-soon/about-morimachi/">森町を知る</a>', '<a class="official-link" href="/questions/">森町のよくある質問</a>'])
    if int(row["id"]) == 292:
        related = '<a class="official-link" href="/farmland/farmland-application-calendar/">令和8年度農業委員会カレンダーで日程を確認する</a>' + related
    elif int(row["id"]) == 162:
        related = '<a class="official-link" href="/records/farmland-transfer-party-sheet/">農地売買・貸借の当事者情報を整理する</a>' + related
    related += f'<script type="application/ld+json">{json.dumps(breadcrumb, ensure_ascii=False, separators=(",", ":"))}</script>'
    html = f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)} | 森町ライフハック</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{SITE}{url}"><meta property="og:type" content="website"><meta property="og:site_name" content="森町ライフハック"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{SITE}{url}"><meta property="og:image" content="{SITE}{url}cover.svg"><meta name="twitter:card" content="summary_large_image"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/site.css?v=20260702"><script type="application/ld+json">{json.dumps(webpage, ensure_ascii=False, separators=(',', ':'))}</script><script type="application/ld+json">{json.dumps(faq_json, ensure_ascii=False, separators=(',', ':'))}</script></head><body><!-- SEO-PHASE4-PAGE --><!-- PART:header:START --><header class="site"><div class="wrap"><a class="logo" href="/">森町ライフハック</a></div></header><!-- PART:header:END --><!-- PART:disclaimer:START --><div class="disclaimer"><div class="wrap">森町ライフハックは森町公式サイトではありません。最新・正確な情報は必ず公式ページで確認してください。</div></div><!-- PART:disclaimer:END --><main><div class="wrap"><p class="breadcrumb"><a href="/">静岡県森町ライフハック</a> ／ {e(category)} ／ {e(title)}</p><section class="hero"><div class="hero-visual"><span aria-hidden="true">🧭</span><h1>{e(title)}</h1></div><div class="hero-body"><p class="lead">{e(intent)}人が、事実と未確認事項を分けて次の一歩を決めるためのガイドです。</p><img style="width:100%;height:auto" src="cover.svg" width="1000" height="560" alt="{e(cover_alt)}"></div></section><article class="post-editorial-body">{editorial_blocks_v2(row)}</article><section><h2 class="sec">よくある質問</h2><div class="qa">{faq_html}</div></section><section><h2 class="sec">公式情報源</h2><p>リンク先の対象年度、担当部署、更新日を確認し、実行直前に再確認してください。</p><div class="official">{sources}</div></section><section><h2 class="sec">関連ページ</h2><div class="official">{related}</div></section><p class="verified">生成日：{TODAY} ／ 個別の可否は公式窓口・当事者・必要な専門家へ確認してください。</p></div></main><!-- PART:footer:START --><!-- PART:footer:END --></body></html>'''
    # 固有データが長い記事は、各節で重ねている出典説明だけを減らす。
    # 節ごとの事実・森町条件・FAQと、12見出しは必ず残す。
    while editorial_chars(html) > 7800:
        matches = list(re.finditer(r'<section class="topic-specific">.*?</section>', html, re.S))
        removable = None
        for section_match in reversed(matches):
            paragraph_matches = list(re.finditer(r'<p>.*?</p>', section_match.group(0), re.S))
            if len(paragraph_matches) > 3:
                paragraph = paragraph_matches[-1]
                removable = (
                    section_match.start() + paragraph.start(),
                    section_match.start() + paragraph.end(),
                )
                break
        if removable is None:
            break
        html = html[:removable[0]] + html[removable[1]:]

    supplements = [
        f"{article_key}の確認表には、{details[0]}、公式ページ名、確認日、対象となる住所や人、予定日、問い合わせ先を書きます。目的が広がった場合は欄を分けます。",
        f"{article_key}で{details[1 % len(details)]}の資料を家族へ渡す際は、まだ分からない点も示します。{row['category']}の情報は年度や個別条件で変わるため、確認日を付けます。",
        f"{article_key}のうち{details[2 % len(details)]}の予定は、資料を集める日、窓口へ確認する日、現地を見る日、最終判断をする日に分けます。回答待ちの時間も含めます。",
        f"{article_key}で{details[3 % len(details)]}に必要な費用は、申請や契約だけでなく、交通、郵送、証明書、立会い、管理、休業時間も別欄にします。",
        f"{article_key}と{details[4 % len(details)]}の確認後は、本人、家族、所有者、利用者、町の担当部署、専門家の役割を残します。担当が替わっても記録を引き継げます。",
        f"{article_key}で{details[5 % len(details)]}の現地を見る場合は、写真の撮影日と方向を残し、見えていない範囲を明記します。時期で変わる条件も確認します。",
        f"{article_key}の{details[6 % len(details)]}について判断を見直す日を決めます。公式案内、家族構成、所有関係、実行予定日が変わったときは確認し直します。",
        f"{article_key}の記録を閉じる前に、{details[7 % len(details)]}を誰が再確認するか決めます。回答が得られなかった項目は空欄にせず、未確認の理由と次の確認日を残します。",
    ]
    # 固有事実が未整備のnoindex下書きでも、汎用文の水増しはしない。
    # 各ページの条件・FAQ・出典・構成軸を交差させた確認メモで補う。
    for index in range(24):
        condition = str(row["morimachi_conditions"][index % len(row["morimachi_conditions"])])
        faq_item = row["faqs"][(index + int(row["id"])) % len(row["faqs"])]
        source = row["sources"][(index * 2 + int(row["id"])) % len(row["sources"])]
        source_heading = str(row["section_headings"][(index * 5) % len(row["section_headings"])])
        supplements.append(
            f"{source_heading}を確認表へ移す際は、{condition}"
            f"関連する問い「{faq_item['question']}」への回答は「{faq_item['answer']}」です。"
            f"根拠は「{source.get('title') or '公式資料'}」で再確認します。"
        )
    if not row.get("section_paragraphs") and editorial_chars(html) < 6000:
        extra = ['<section class="practical-notes"><h2 class="sec">実行前の確認メモ</h2>']
        for paragraph in supplements:
            extra.append(f'<p>{e(paragraph)}</p>')
            candidate = html.replace('</article>', ''.join(extra) + '</section></article>', 1)
            if editorial_chars(candidate) >= 6100:
                html = candidate
                break
        else:
            html = html.replace('</article>', ''.join(extra) + '</section></article>', 1)
    return html

def inject_discovery(rows: list[dict]) -> None:
    guide = ROOT / "guide" / "morimachi-complete-guide" / "index.html"
    html = guide.read_text(encoding="utf-8")
    groups = {}
    for row in rows:
        groups.setdefault(row["category"], canonical_url(row))
    links = "".join(f'<a class="official-link" href="{url}">第4期・{e(category)}の確認ガイド</a>' for category, url in sorted(groups.items()))
    block = LINK_START + '<section><h2 class="sec">公開済みの具体的な確認ガイド</h2><p>手続き、住まい、土地、文化、訪問などを、一つの判断ごとに確認できます。</p><div class="official">' + links + "</div></section>" + LINK_END
    html = re.sub(re.escape(LINK_START)+r".*?"+re.escape(LINK_END), block, html, flags=re.S) if LINK_START in html else html.replace("</main>", block+"</main>", 1)
    guide.write_text(html, encoding="utf-8", newline="\n")

def remove_discovery() -> None:
    """未公開ページへの発見導線を総合ガイドから取り除く。"""
    guide = ROOT / "guide" / "morimachi-complete-guide" / "index.html"
    if not guide.is_file():
        return
    html = guide.read_text(encoding="utf-8")
    html = re.sub(re.escape(LINK_START) + r".*?" + re.escape(LINK_END), "", html, flags=re.S)
    guide.write_text(html, encoding="utf-8", newline="\n")


def released_rows() -> list[dict]:
    """Return rows that have passed every publication gate in the ledger."""
    if not PUBLICATION.is_file():
        return []
    publication = json.loads(PUBLICATION.read_text(encoding="utf-8"))
    released_ids = {
        int(item["id"])
        for item in publication
        if item.get("publish_ready") is True
        and item.get("human_reviewed") is True
        and item.get("source_validation") == "verified"
        and item.get("uniqueness_validation") == "verified"
        and item.get("visual_validation") == "verified"
    }
    return [
        row for row in load_rows()
        if int(row["id"]) in released_ids and row["substantive_fact_count"] >= 6
    ]


def sync_discovery() -> None:
    rows = released_rows()
    inject_discovery(rows) if rows else remove_discovery()


def ensure_release_quality(rows: list[dict]) -> None:
    """公開対象に固有事実と主題専用本文を要求する。"""
    failures = [
        f"ID{row['id']} {row['substantive_fact_count']}/6"
        for row in rows if row["substantive_fact_count"] < 6
    ]
    if failures:
        raise RuntimeError(
            "公開候補に実内容の固有事実が6件未満のページがあります: "
            + ", ".join(failures[:20])
            + (f" ほか{len(failures) - 20}件" if len(failures) > 20 else "")
        )
    grandfathered_ids = {215, 232, 241, 270, 277}
    missing_curated = [
        f"ID{row['id']}"
        for row in rows
        if int(row["id"]) not in grandfathered_ids and not row.get("section_paragraphs")
    ]
    if missing_curated:
        raise RuntimeError(
            "新規公開候補に主題専用本文section_paragraphsがありません: "
            + ", ".join(missing_curated[:20])
        )

def set_release_state(rows: list[dict], released: bool) -> None:
    """監査済みページだけをindex可能にし、発見導線を同期する。"""
    if released:
        ensure_release_quality(rows)
    for row in rows:
        path = ROOT / canonical_url(row).strip("/") / "index.html"
        html = path.read_text(encoding="utf-8")
        html = html.replace(ROBOTS_PENDING, "")
        if not released:
            html = html.replace("<head>", f"<head>{ROBOTS_PENDING}", 1)
        path.write_text(html, encoding="utf-8", newline="\n")
    # A cohort update must preserve discovery links for other released IDs.
    sync_discovery()

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ids", help="生成するID。例: 1,4,10-12（省略時は全300件）")
    args = parser.parse_args()
    all_rows = load_rows()
    if len(all_rows) != 300 or {int(r["id"]) for r in all_rows} != set(range(1, 301)):
        raise RuntimeError("第4期台帳はID 1〜300の300件である必要があります")
    if any(r.get("decision") != "CREATE" for r in all_rows):
        raise RuntimeError("第4期公開台帳にCREATE以外が含まれています")
    urls = [canonical_url(r) for r in all_rows]
    if len(urls) != len(set(urls)):
        raise RuntimeError("第4期URLが重複しています")
    selected_ids = parse_ids(args.ids, {int(row["id"]) for row in all_rows})
    rows = [row for row in all_rows if int(row["id"]) in selected_ids]
    partial = len(selected_ids) != len(all_rows)
    if partial:
        if not PUBLICATION.is_file():
            raise RuntimeError("部分生成には既存の300件公開台帳が必要です")
        existing = json.loads(PUBLICATION.read_text(encoding="utf-8"))
        if len(existing) != 300 or {int(item["id"]) for item in existing} != set(range(1, 301)):
            raise RuntimeError("部分生成前の公開台帳がID 1〜300を網羅していません")
        publication_by_id = {int(item["id"]): item for item in existing}
    else:
        publication_by_id = {}
    row_index = {int(row["id"]): index for index, row in enumerate(all_rows)}
    for row in rows:
        index = row_index[int(row["id"])]
        url = urls[index]
        path = ROOT / url.strip("/") / "index.html"
        if path.is_file() and "SEO-PHASE4-PAGE" not in path.read_text(encoding="utf-8"):
            raise RuntimeError(f"既存ページとのURL衝突: {url}")
        html = render(row, url, urls[index-1], urls[(index+1) % len(urls)])
        html = html.replace("<head>", f"<head>{ROBOTS_PENDING}", 1)
        chars = editorial_chars(html)
        minimum_chars = 5000 if row.get("section_paragraphs") else 6000
        if not minimum_chars <= chars <= 8000:
            raise RuntimeError(f"編集本文が{minimum_chars}〜8000文字の範囲外: {url} {chars}")
        path.write_text(html, encoding="utf-8", newline="\n")
        publication_by_id[int(row["id"])] = {
            "id": row["id"],
            "url": url,
            "title": row["title"],
            "category": row["category"],
            "search_intent": row["search_intent"],
            "search_aliases": [row["title"].split("｜", 1)[0], row["search_intent"]],
            "editorial_chars": chars,
            "generated_at": TODAY,
            # 第4期は本文生成だけで公開扱いにしない。一次情報の実査、
            # 類似度、表示QAの全ゲートを通した記事だけ publish_ready にする。
            "source_validation": "pending",
            "uniqueness_validation": "pending",
            "visual_validation": "pending",
            "human_reviewed": False,
            "publish_ready": False,
        }
    publication = [publication_by_id[item_id] for item_id in range(1, 301)]
    PUBLICATION.write_text(json.dumps(publication, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    # Rebuilt IDs return to pending; links for other released IDs remain intact.
    sync_discovery()
    scope = f"ID {','.join(str(i) for i in sorted(selected_ids))}" if partial else "全300件"
    print(f"第4期ページ生成: {scope} / {len(rows)}件 / 最小編集本文 {min(publication_by_id[int(r['id'])]['editorial_chars'] for r in rows)}字")

if __name__ == "__main__":
    main()
