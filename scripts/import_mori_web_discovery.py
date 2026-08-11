#!/usr/bin/env python3
"""Discover factual Mori Town POI candidates from public web indexes.

The output deliberately excludes reviews, descriptions, captions, rankings,
and promotional text.  Candidate definitions contain names and structured
facts only; each run verifies that the source still advertises the name.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import time
import unicodedata
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


CHECKED_AT = date.today().isoformat()
UA = "MorimachiWebDiscovery/1.0 (+https://morimachi.enshu-lifehack.com/)"
SOURCES = [
    {"id": "yahoo-travel", "name": "Yahoo!トラベル", "url": "https://travel.yahoo.co.jp/tokai/pr22/ct22028000/", "scope": "周智郡の宿泊一覧"},
    {"id": "yahoo-kanko", "name": "Yahoo!トラベル 観光", "url": "https://travel.yahoo.co.jp/kanko/prefecture-shizuoka/city-22461/", "scope": "周智郡森町の観光スポット"},
    {"id": "jalan-1", "name": "じゃらんnet", "url": "https://www.jalan.net/kankou/cit_224610000/", "scope": "森町観光スポット1～30件"},
    {"id": "jalan-2", "name": "じゃらんnet", "url": "https://www.jalan.net/kankou/cit_224610000/page_2/", "scope": "森町観光スポット31～41件"},
    {"id": "wikipedia", "name": "Wikipedia 森町（静岡県）", "url": "https://ja.wikipedia.org/wiki/%E6%A3%AE%E7%94%BA_%28%E9%9D%99%E5%B2%A1%E7%9C%8C%29", "scope": "観光・文化欄の固有名詞と年"},
    {"id": "bunka", "name": "文化遺産オンライン", "url": "https://bunka.nii.ac.jp/heritages/region/22/22461", "scope": "周智郡森町の国指定文化財一覧"},
]

# No prose copied from a source. Values below are names, classifications,
# addresses, times, prices, access statements, coordinates, and years only.
CANDIDATES = [
    {"source": "yahoo-travel", "name": "リバウッドリゾート", "categories": ["宿泊", "グランピング"], "address": "静岡県周智郡森町大鳥居1"},
    {"source": "yahoo-kanko", "name": "吉川キャンプ場カワセミの里", "categories": ["キャンプ場"]},
    {"source": "yahoo-kanko", "name": "香勝寺", "categories": ["寺院", "花"]},
    {"source": "yahoo-kanko", "name": "小國神社", "categories": ["神社"]},
    {"source": "jalan-1", "name": "遠州森町パーキングエリア（下り線）", "categories": ["サービスエリア"]},
    {"source": "jalan-1", "name": "森町観光協会", "categories": ["観光案内所"], "hours": "月～金 08:30～17:15", "closed": "土・日・祝日、年末年始等", "access": "天竜浜名湖鉄道戸綿駅から徒歩10分"},
    {"source": "jalan-1", "name": "森町レンタサイクル", "categories": ["レンタサイクル"], "fee": "普通自転車500円", "access": "天竜浜名湖鉄道遠州森駅"},
    {"source": "jalan-1", "name": "香勝寺のききょう", "categories": ["花", "寺院"], "fee": "大人500円、子供100円、団体20名以上450円", "access": "遠州森駅から徒歩25分"},
    {"source": "jalan-1", "name": "蓮華寺のはぎ", "categories": ["花", "寺院"], "fee": "見学無料", "access": "遠州森駅から徒歩15分"},
    {"source": "jalan-1", "name": "城ケ平公園", "categories": ["公園", "城跡"], "access": "戸綿駅から徒歩45分"},
    {"source": "jalan-1", "name": "神明の里", "categories": ["体験"]},
    {"source": "jalan-1", "name": "三木の里カントリークラブ", "categories": ["ゴルフ場"]},
    {"source": "jalan-1", "name": "彩の月", "categories": ["体験"]},
    {"source": "jalan-1", "name": "30日間の小さなマルシェ", "categories": ["買い物"]},
    {"source": "jalan-1", "name": "ナギの木", "categories": ["天然記念物", "樹木"]},
    {"source": "jalan-1", "name": "石松の墓", "categories": ["史跡"]},
    {"source": "jalan-2", "name": "小國神社花菖蒲園", "categories": ["花", "神社"]},
    {"source": "jalan-2", "name": "真田城跡", "categories": ["城跡"]},
    {"source": "jalan-2", "name": "太田川桜堤", "categories": ["花", "景観"]},
    {"source": "jalan-2", "name": "己書心笑み道場 cafe flat幸座", "categories": ["体験", "カフェ"]},
    {"source": "jalan-2", "name": "太田川ダム", "categories": ["ダム", "景観"]},
    {"source": "jalan-2", "name": "floresta fabrica glass atelier", "categories": ["ガラス工芸", "体験"]},
    {"source": "jalan-2", "name": "手打ちそば「ほっとり」", "categories": ["飲食店", "そば"]},
    {"source": "wikipedia", "name": "崇信寺", "categories": ["寺院"], "facts": [{"key": "宗派", "value": "曹洞宗"}]},
    {"source": "wikipedia", "name": "秋葉街道 森宿", "categories": ["宿場町", "街道"]},
    {"source": "wikipedia", "name": "秋葉山常夜灯", "categories": ["史跡", "街道"]},
    {"source": "wikipedia", "name": "ワンダーガーデン", "categories": ["娯楽施設"]},
    {"source": "wikipedia", "name": "山名神社", "categories": ["神社"], "established_year": 706},
    {"source": "wikipedia", "name": "蓮華寺", "categories": ["寺院"], "established_year": 704},
    {"source": "bunka", "name": "天竜浜名湖鉄道太田川橋梁", "categories": ["登録有形文化財", "橋梁"], "address": "静岡県周智郡森町森地先"},
    {"source": "bunka", "name": "天竜浜名湖鉄道遠州森駅本屋及び上りプラットホーム", "categories": ["登録有形文化財", "鉄道施設"], "address": "静岡県周智郡森町森字十七夜前980-2"},
    {"source": "bunka", "name": "天竜浜名湖鉄道遠江一宮駅本屋", "categories": ["登録有形文化財", "鉄道施設"], "address": "静岡県周智郡森町一宮字郷戸2431-2"},
    {"source": "bunka", "name": "遠江森町の舞楽", "categories": ["重要無形民俗文化財", "伝統芸能"]},
]


def fetch(url: str, retries: int = 3) -> str:
    req = Request(url, headers={"User-Agent": UA, "Accept-Language": "ja"})
    for attempt in range(retries):
        try:
            with urlopen(req, timeout=40) as response:
                raw = response.read()
                charset = response.headers.get_content_charset() or "utf-8"
                if charset.lower() == "windows-31j":
                    charset = "cp932"
                return raw.decode(charset, errors="replace")
        except (HTTPError, URLError, TimeoutError) as exc:
            if attempt + 1 == retries:
                raise RuntimeError(f"fetch failed: {url}: {exc}") from exc
            time.sleep(attempt + 1)
    raise AssertionError("unreachable")


def normalize_name(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    value = re.sub(r"(?:株式会社|有限会社|宗教法人|\(株\)|\(有\)|（株）|（有）)", "", value)
    return re.sub(r"[\s・･/／()（）「」『』【】\-‐―]+", "", value)


def existing_index(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    result = {}
    for record in payload.get("records", []):
        names = [record.get("name", ""), record.get("reading", "")]
        for name in names:
            if name:
                result[normalize_name(name)] = record.get("id", "")
    return result


def source_by_id(source_id: str) -> dict[str, object]:
    return next(source for source in SOURCES if source["id"] == source_id)


def advertised(page_text: str, name: str) -> bool:
    """Match names across HTML element and whitespace boundaries."""
    return normalize_name(name) in normalize_name(page_text)


def stable_id(source_id: str, name: str) -> str:
    digest = hashlib.sha256(f"{source_id}\0{name}".encode()).hexdigest()[:12]
    return f"web-{source_id}-{digest}"


def make_record(candidate: dict[str, object], existing: dict[str, str], checked_at: str) -> dict[str, object]:
    source = source_by_id(str(candidate["source"]))
    name = str(candidate["name"])
    existing_id = existing.get(normalize_name(name), "")
    return {
        "id": stable_id(str(candidate["source"]), name),
        "name": name,
        "categories": candidate.get("categories", []),
        "address": candidate.get("address", ""),
        "phone": candidate.get("phone", ""),
        "hours": candidate.get("hours", ""),
        "closed": candidate.get("closed", ""),
        "fee": candidate.get("fee", ""),
        "access": candidate.get("access", ""),
        "geocode": candidate.get("geocode"),
        "established_year": candidate.get("established_year"),
        "facts": candidate.get("facts", []),
        "match_status": "supplement" if existing_id else "new",
        "existing_id": existing_id,
        "source_ids": [candidate["source"]],
        "source_urls": [source["url"]],
        "checked_at": checked_at,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--existing", type=Path, default=root / "data" / "mori-directory.json")
    parser.add_argument("--output", type=Path, default=root / "data" / "mori-web-discovery.json")
    parser.add_argument("--checked-at", default=CHECKED_AT)
    args = parser.parse_args()

    fetched = {}
    source_rows = []
    for source in SOURCES:
        page = fetch(str(source["url"]))
        fetched[source["id"]] = html.unescape(re.sub(r"<[^>]+>", " ", page))
        candidates = [item for item in CANDIDATES if item["source"] == source["id"]]
        indexed = sum(advertised(fetched[source["id"]], str(item["name"])) for item in candidates)
        source_rows.append({**source, "expected_records": len(candidates), "indexed_records": indexed, "status": "ok" if indexed == len(candidates) else "partial"})

    existing = existing_index(args.existing)
    records = []
    for candidate in CANDIDATES:
        if not advertised(fetched[candidate["source"]], str(candidate["name"])):
            continue
        records.append(make_record(candidate, existing, args.checked_at))

    # One fact candidate per source/name pair; IDs and normalized names must be unique.
    deduped = {}
    for record in records:
        key = normalize_name(str(record["name"]))
        if key not in deduped:
            deduped[key] = record
        else:
            current = deduped[key]
            for source_id in record["source_ids"]:
                if source_id not in current["source_ids"]:
                    current["source_ids"].append(source_id)
            for url in record["source_urls"]:
                if url not in current["source_urls"]:
                    current["source_urls"].append(url)

    output = {"checked_at": args.checked_at, "sources": source_rows, "records": sorted(deduped.values(), key=lambda item: normalize_name(str(item["name"])))}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(output['records'])} records ({sum(r['match_status']=='new' for r in output['records'])} new)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
