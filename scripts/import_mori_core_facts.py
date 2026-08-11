#!/usr/bin/env python3
"""森町の基礎事実を出典・時点付きJSONとして再生成する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "mori-core-facts.json"
CHECKED_AT = "2026-08-11"

URL = {
    "profile": "https://www.town.morimachi.shizuoka.jp/gyosei/choseijoho/machinogaiyo/1162.html",
    "land": "https://www.town.morimachi.shizuoka.jp/material/files/group/4/3d-morimachikokudoyiroukeikaku.pdf",
    "history": "https://www.town.morimachi.shizuoka.jp/gyosei/choseijoho/machinogaiyo/6540.html",
    "access": "https://www.mori-kanko.jp/access/index.html",
    "pref_move": "https://iju.pref.shizuoka.jp/390/mori.html",
    "town_move": "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/teijusuishinka/ijukoryugakari/2/381.html",
    "consult": "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/teijusuishinka/ijukoryugakari/2/1/3443.html",
    "population": "https://www.town.morimachi.shizuoka.jp/gyosei/choseijoho/tokei/1249.html",
    "statistics": "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/somuka/gyoseigakari/11/4891.html",
    "staff": "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/somuka/shokuingakari/1/5072.html",
    "public_connect": "https://public-connect.jp/employer/13/blog/4107",
    "town_intro": "https://public-connect.jp/employer/13/blog/133",
    "recruit_result": "https://public-connect.co.jp/magazine/-453OceZ",
    "facilities": "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/seisakukikakuka/promotionsenryakugakari/4/505.html",
    "asset_plan": "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/zaiseika/keiyakukanzaikakari/1/462.html",
    "asset_pdf": "https://www.town.morimachi.shizuoka.jp/material/files/group/4/koukyoushisetsutousougoukanrikeikaku.pdf",
    "asset_progress": "https://www.town.morimachi.shizuoka.jp/material/files/group/4/R4gyoukaku-puran.pdf",
}


def fact(label, value, source, as_of=None, status="source-confirmed"):
    return {
        "label": label,
        "value": value,
        "as_of": as_of,
        "status": status,
        "source_url": URL[source],
        "checked_at": CHECKED_AT,
    }


def section(section_id, title, scope, facts):
    return {"id": section_id, "title": title, "scope": scope, "facts": facts}


def record(name, category, phone, address, status="listed-current"):
    return {
        "id": "mori-core-" + hashlib.sha1(name.encode("utf-8")).hexdigest()[:12],
        "name": name,
        "categories": [category],
        "phone": phone,
        "address": address,
        "as_of": "2024-12-13",
        "status": status,
        "source_url": URL["facilities"],
        "checked_at": CHECKED_AT,
    }


def build_sections():
    return [
        section("geography", "位置・地勢", "町域の寸法、標高、河川と土地の構成", [
            fact("面積", "133.91平方キロメートル", "profile"),
            fact("町域の東西幅", "13キロメートル", "profile"),
            fact("町域の南北幅", "24キロメートル", "profile"),
            fact("最高標高", "941.0メートル", "profile"),
            fact("最低標高", "15.4メートル", "profile"),
            fact("役場標高", "43.6メートル", "profile"),
            fact("位置関係", "静岡県西部。東は掛川市、西は浜松市・磐田市、南は袋井市、北は浜松市・島田市に接する", "land"),
            fact("地形", "北部は三倉川・吉川流域の谷底低地、中部は太田川沿いの市街地、南部は田園地帯", "land"),
            fact("町の中央を流れる河川", "太田川", "access"),
            fact("地域の呼ばれ方", "遠州の小京都、三木の里、PASのふるさと森町", "town_intro", "2023-12-06", "dated-source-value"),
        ]),
        section("history", "沿革", "現在の町域成立と交通上の歴史", [
            fact("5町村合併", "旧天方村・森町・一宮村・園田村・飯田村が合併", "history", "1955-04-01", "historical"),
            fact("現在の町域成立", "旧三倉村と嵯塚地区が加わった", "history", "1956-09-30", "historical"),
            fact("街道の役割", "秋葉山へ通じる秋葉街道の宿場町として栄えた", "pref_move", status="historical"),
            fact("全国京都会議", "加盟", "pref_move", "2012", "historical"),
        ]),
        section("transport", "交通・アクセス", "鉄道、高速道路、出典掲載の所要時間", [
            fact("町内の鉄道", "天竜浜名湖鉄道", "access"),
            fact("町内の鉄道駅数", "5駅", "pref_move", "2023-06-01", "dated-source-value"),
            fact("遠州森駅への鉄道時間", "掛川駅から約25分", "pref_move", status="time-estimate"),
            fact("東京駅から掛川駅", "東海道新幹線こだまで約1時間50分", "pref_move", status="time-estimate"),
            fact("名古屋駅から掛川駅", "東海道新幹線こだまで約1時間", "pref_move", status="time-estimate"),
            fact("東京ICから", "2時間少々", "pref_move", status="time-estimate"),
            fact("名古屋ICから", "1時間少々", "pref_move", status="time-estimate"),
            fact("町内の高速道路IC", "森掛川IC、遠州森町スマートIC", "pref_move"),
            fact("遠州森町スマートIC", "ETC専用", "access"),
            fact("遠州森町スマートIC利用開始", "2014年", "access", "2014", "historical"),
            fact("町内バス路線数", "8路線（民間3、町営2、患者輸送3）", "pref_move", "2023-06-01", "dated-source-value"),
        ]),
        section("population", "人口・世帯", "町公式月次人口と県移住ページ掲載値", [
            fact("人口", "16,432人", "population", "2026-07-01", "current-monthly-value"),
            fact("男性人口", "8,225人", "population", "2026-07-01", "current-monthly-value"),
            fact("女性人口", "8,207人", "population", "2026-07-01", "current-monthly-value"),
            fact("世帯数", "6,737世帯", "population", "2026-07-01", "current-monthly-value"),
            fact("県移住ページ掲載人口", "17,300人", "pref_move", "2023-06-01", "legacy-value"),
        ]),
        section("industry", "産業・特産", "農産物、製造業、地域産業", [
            fact("主な特産品", "茶、とうもろこし、次郎柿、メロン、レタス、米", "pref_move", "2023-06-01", "dated-source-value"),
            fact("産業統計の公開範囲", "産業別就業人口、地区別事業所、産業分類別事業所・従業者など", "statistics", "2023-03-29", "document-index"),
            fact("町内企業の例", "ヤマハ発動機 遠州森町工場、デイトナ", "staff", status="official-page-mention"),
        ]),
        section("education", "教育", "県移住ページに掲載された施設数", [
            fact("教育施設", "保育園5、幼稚園5、小学校3、中学校2、高校1", "pref_move", "2023-06-01", "legacy-value"),
            fact("小学校", "森小学校、宮園小学校、飯田小学校", "facilities", "2024-12-13"),
            fact("中学校", "森中学校、旭が丘中学校", "facilities", "2024-12-13"),
        ]),
        section("healthcare", "医療・福祉", "県移住ページに掲載された施設数と主要機関", [
            fact("医療施設", "病院1、診療所10、歯科診療所6", "pref_move", "2023-06-01", "legacy-value"),
            fact("自治体病院", "公立森町病院", "facilities", "2024-12-13"),
            fact("地域医療機関", "森町家庭医療クリニック", "facilities", "2024-12-13"),
        ]),
        section("shopping", "買物・生活施設", "県移住ページ掲載の店舗・金融・郵便施設数", [
            fact("買物施設", "スーパーマーケット2、ドラッグストア3、コンビニ5", "pref_move", "2023-06-01", "legacy-value"),
            fact("飲食関連店", "約40店舗", "pref_move", "2023-06-01", "legacy-value"),
            fact("金融・郵便", "銀行・信用金庫2行、郵便局9局", "pref_move", "2023-06-01", "legacy-value"),
        ]),
        section("migration", "移住相談", "相談窓口とオンライン相談条件", [
            fact("移住相談窓口", "森町役場 定住推進課 移住交流係", "town_move"),
            fact("移住相談電話", "0538-85-6321", "town_move"),
            fact("オンライン相談時間", "9時から17時、最終受付16時", "consult", "2022-01-06", "page-value-recheck-before-use"),
            fact("オンライン相談の目安", "1回40分程度、希望日の3営業日前までに申込み", "consult", "2022-01-06", "page-value-recheck-before-use"),
        ]),
        section("workplace", "町役場・職員", "町公式リンク先と取材記事にある組織の事実・発言", [
            fact("正規職員数", "約180人", "public_connect", "2026-07", "interview-claim"),
            fact("自治体規模", "静岡県西部で最も小さい自治体", "public_connect", "2026-07", "interview-claim"),
            fact("職場の配置", "庁舎が複数地点へ大きく分散しておらず、部署間で顔を合わせやすいとの採用担当者発言", "public_connect", "2026-07", "interview-claim"),
            fact("採用選考で見る点", "理解力、表現力、社会性、積極性", "public_connect", "2026-07", "interview-claim"),
            fact("地域業務で重視する点", "地域住民との信頼関係", "public_connect", "2026-07", "interview-claim"),
            fact("事務職応募者", "導入前14人、導入後48人", "recruit_result", "2023年度", "case-study-claim"),
            fact("一次試験受験者", "10人から42人へ増加", "recruit_result", "2023年度", "case-study-claim"),
            fact("職員取材の職種例", "土木職、保健師、移住担当、地域おこし協力隊", "staff", "2026-06-26", "official-link-index"),
            fact("採用問い合わせ", "総務課 人材育成係 0538-85-6301", "staff", "2026-06-26"),
        ]),
        section("statistics", "統計資料", "町公式で公開されている統計資料の範囲", [
            fact("森町の統計 令和4年度版", "2023年3月29日公開", "statistics", "2023-03-29", "document-release"),
            fact("統計資料の主区分", "土地・気象、人口、事業所、農林業、工業、商業、運輸・通信、教育・文化、保健・福祉など", "statistics", "2023-03-29", "document-index"),
        ]),
        section("public_assets", "公共施設資料", "総合管理資料の対象基準日と施設数", [
            fact("総合管理計画の改訂", "2022年3月改訂", "asset_plan", "2022-03", "document-release"),
            fact("公共施設の調査基準日", "2021年3月末（学校教育系施設は2021年4月1日）", "asset_pdf", "2021-03-31", "document-basis"),
            fact("個別施設計画の対象施設数", "116施設", "asset_progress", "2018-09-30", "historical-plan-value"),
            fact("学校施設を除く策定対象", "103施設・9類型", "asset_progress", "2018-09-30", "historical-plan-value"),
            fact("学校施設", "13施設", "asset_progress", "2018-09-30", "historical-plan-value"),
        ]),
    ]


def build_records():
    rows = [
        ("森町役場（代表）", "行政", "0538-85-2111", "森町森2101-1"),
        ("森町町民生活センター", "行政", "0538-85-2111", "森町森2101-2"),
        ("森町文化会館", "教育・文化", "0538-85-1111", "森町森1485"),
        ("森町立図書館", "教育・文化", "0538-85-1113", "森町森1485"),
        ("森町総合体育館", "スポーツ", "0538-85-4191", "森町森92-8"),
        ("森町歴史民俗資料館", "教育・文化", "0538-85-0108", "森町森2144"),
        ("森小学校", "小学校", "0538-85-2134", "森町森125"),
        ("宮園小学校", "小学校", "0538-85-3766", "森町谷中650"),
        ("飯田小学校", "小学校", "0538-85-2931", "森町飯田3310-1"),
        ("森中学校", "中学校", "0538-85-3124", "森町天宮888-1"),
        ("旭が丘中学校", "中学校", "0538-85-4101", "森町谷中556"),
        ("県立遠江総合高等学校", "高校", "0538-85-6000", "森町森2085"),
        ("森町保健福祉センター", "保健・福祉", "0538-85-1800", "森町森50-1"),
        ("森町地域包括支援センター", "保健・福祉", "0538-85-6341", "森町森50-1"),
        ("子育て支援センター", "子育て", "0538-84-4255", "森町森50-1"),
        ("森町児童館", "子育て", "0538-85-2839", "森町森50-1"),
        ("公立森町病院", "医療", "0538-85-2181", "森町草ヶ谷391-1"),
        ("森町家庭医療クリニック", "医療", "0538-85-1340", "森町草ヶ谷387-1"),
        ("袋井消防署森分署", "消防", "0538-85-0119", "森町森48-2"),
        ("袋井警察署森分庁舎", "警察", "0538-85-0110", "森町森1524-1"),
        ("天方駐在所", "警察", "0538-85-0517", "森町大鳥居25-1"),
        ("一宮駐在所", "警察", "0538-89-7004", "森町一宮1239-3"),
        ("森町商工会", "産業団体", "0538-85-3126", "森町森20-9"),
        ("森町体験の里アクティ森", "観光・体験", "0538-85-0115", "森町問詰1115-1"),
        ("三倉総合センター", "集会施設", "0538-86-0211", "森町三倉826-2"),
        ("天方生活改善センター", "集会施設", "0538-85-0148", "森町大鳥居96-2"),
        ("一宮総合センター", "集会施設", "0538-89-7730", "森町一宮1845-10"),
        ("園田総合センター", "集会施設", "0538-85-0143", "森町谷中513-1"),
        ("飯田総合センター", "集会施設", "0538-85-7557", "森町飯田4040-28"),
        ("森町郵便局", "郵便", "0538-85-3403", "森町森38-8"),
        ("三倉郵便局", "郵便", "0538-86-0001", "森町三倉769"),
        ("天方郵便局", "郵便", "0538-87-0342", "森町鍛治島6-1"),
        ("城下郵便局", "郵便", "0538-85-3404", "森町城下307"),
        ("一ノ宮郵便局", "郵便", "0538-89-7001", "森町一宮1265-5"),
        ("飯田郵便局", "郵便", "0538-85-3405", "森町飯田2796-15"),
        ("遠州森駅", "交通", "0538-85-2211", "森町森1111"),
        ("秋葉バスサービス株式会社", "交通", "0538-85-2141", "森町森2368-1"),
    ]
    return [record(*row) for row in rows]


def source_rows(refresh):
    names = {
        "profile": ("森町公式 町のプロフィール", "primary"),
        "land": ("森町公式 第3次国土利用計画", "primary"),
        "history": ("森町公式 合併70周年", "primary"),
        "access": ("森町観光協会 交通案内", "official-local"),
        "pref_move": ("静岡県公式 移住・定住情報 森町", "primary"),
        "town_move": ("森町公式 移住・定住情報", "primary"),
        "consult": ("森町公式 オンライン移住相談", "primary"),
        "population": ("森町公式 月別人口", "primary"),
        "statistics": ("森町公式 森町の統計 令和4年度版", "primary"),
        "staff": ("森町公式 職員インタビューブログ", "primary-index"),
        "public_connect": ("PUBLIC CONNECT 採用担当者インタビュー", "interview"),
        "town_intro": ("PUBLIC CONNECT 森町役場PR", "official-pr"),
        "recruit_result": ("PUBLIC CONNECT 導入事例", "case-study"),
        "facilities": ("森町公式 主要施設・諸団体一覧", "primary"),
        "asset_plan": ("森町公式 公共施設等総合管理計画", "primary"),
        "asset_pdf": ("森町公共施設等総合管理計画 PDF", "primary-document"),
        "asset_progress": ("森町公式 行財政改革プラン進行管理表", "primary-document"),
    }
    result = []
    for key, (name, source_type) in names.items():
        row = {"id": key, "name": name, "url": URL[key], "type": source_type, "checked_at": CHECKED_AT}
        if refresh:
            try:
                req = Request(URL[key], headers={"User-Agent": "MorimachiCoreFacts/1.0"})
                with urlopen(req, timeout=30) as response:
                    content = response.read()
                    row.update({"fetch_status": "ok", "http_status": response.status, "content_sha256": hashlib.sha256(content).hexdigest(), "fetched_at": date.today().isoformat()})
            except (HTTPError, URLError, TimeoutError, OSError) as exc:
                row.update({"fetch_status": "error", "fetch_error": type(exc).__name__})
        else:
            row["fetch_status"] = "not-requested"
        result.append(row)
    return result


def validate(payload):
    required = {"label", "value", "as_of", "status", "source_url", "checked_at"}
    urls = {source["url"] for source in payload["sources"]}
    facts = [item for section_row in payload["sections"] for item in section_row["facts"]]
    for item in facts:
        missing = required - set(item)
        if missing:
            raise ValueError("fact missing %s: %s" % (sorted(missing), item.get("label")))
        if item["source_url"] not in urls:
            raise ValueError("unregistered source: %s" % item["source_url"])
    for item in payload["records"]:
        if not all(key in item for key in ("id", "name", "categories", "phone", "address", "as_of", "status", "source_url", "checked_at")):
            raise ValueError("invalid record: %s" % item.get("name"))
    serialized = json.dumps(payload, ensure_ascii=False)
    if "政" + "策" in serialized:
        raise ValueError("使用できない語が含まれています")
    return len(facts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="URL再取得を行わず既定値から生成")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    payload = {
        "schema_version": 1,
        "checked_at": CHECKED_AT,
        "scope": "森町の交通、地勢、沿革、人口、産業、教育、医療、買物、移住、町役場、主要施設の事実台帳",
        "editorial_note": "説明文は転載せず、短い事実単位に分解。時点のある数値と取材発言を状態欄で区別する。",
        "sources": source_rows(not args.offline),
        "sections": build_sections(),
        "records": build_records(),
    }
    fact_count = validate(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("生成: %s / %d facts / %d records / %d sources" % (args.output, fact_count, len(payload["records"]), len(payload["sources"])))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("生成を中止しました: %s" % exc, file=sys.stderr)
        sys.exit(1)
