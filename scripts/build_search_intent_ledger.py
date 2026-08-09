#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""200候補を既存URLへ突合し、重複判定台帳を生成する。

機械的な類似度だけで新設を決めず、既存の生活ガイド・質問ページを優先する。
低信頼の候補は CREATE にせず REVIEW として止め、人が判断できる根拠を残す。
"""
from __future__ import annotations

import csv
import json
import re
from difflib import SequenceMatcher
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK_ORDER = ROOT / "docs" / "search-traffic-200-work-order.md"
BASELINE = ROOT / "reports" / "search-traffic-baseline-20260809"
OUT_JSON = ROOT / "data" / "search-intent-200-decisions.json"
OUT_CSV = ROOT / "reports" / "search-intent-200-decisions.csv"
EXISTING_CSV = ROOT / "reports" / "existing-129-seo-decisions.csv"

GENERIC = ("手続き", "確認事項", "相談先", "整理", "調べる", "森町", "静岡県", "周智郡")
GROUP_PREFIXES = {
    "空き家・実家じまい": ("/life/housing/", "/life/end-of-life/", "/questions/housing-", "/questions/end-of-life-"),
    "相続・おくやみ": ("/life/end-of-life/", "/life/housing/", "/questions/end-of-life-", "/questions/housing-"),
    "土地・農地・住宅": ("/life/housing/", "/life/troubles-consult/farmland/", "/questions/farmland-", "/questions/housing-"),
    "介護・親": ("/life/parents-care/", "/questions/parents-care-"),
    "ごみ・生活環境": ("/life/start-living/", "/life/moving-out/", "/questions/start-living-", "/questions/moving-out-"),
    "行政手続き": ("/life/start-living/", "/life/moving-out/", "/life/family-grow/", "/questions/start-living-", "/questions/moving-out-"),
    "税金・保険・年金": ("/life/work-life/", "/questions/work-life-", "/questions/end-of-life-"),
    "子育て・学校": ("/life/family-grow/", "/life/education/", "/questions/family-grow-", "/questions/education-"),
    "防災・医療・困りごと": ("/life/emergency/", "/life/health-medical/", "/life/troubles-consult/", "/questions/health-medical-", "/questions/troubles-consult-", "/questions/living-soon-disaster-risk/"),
    "移住・地域": ("/life/living-soon/", "/life/play-out/", "/questions/living-soon-", "/questions/play-out-", "/shrine/", "/temple/"),
}

# 既存129ページの主意図を人が読み合わせた結果。値は最終URL、CREATE: は
# 既存体系に沿った新規URLを表す。同じURLへ複数候補を寄せる場合は、候補ごとに
# ページを増やさず、一つのガイド内で関連質問として回答する。
MANUAL_TARGET_GROUPS = {
    "/life/end-of-life/inherited-house/": [1, 2, 6, 20, 23, 36, 37, 59, 80],
    "/life/housing/sell-house/": [3, 4, 18, 40, 48, 50, 53, 55, 56, 57, 60],
    "/life/housing/vacant-house/": [5, 8, 13, 14, 16],
    "/life/housing/earthquake-demolition/": [7, 54],
    "/life/end-of-life/property-tax-inheritance/": [9, 26, 140],
    "CREATE:/life/housing/close-parents-house/": [10],
    "/life/housing/clean-parents-house/": [11, 12, 15, 19],
    "/life/end-of-life/inheritance/": [17, 21, 22, 24, 25, 27, 28, 29, 30, 35, 39, 46, 47, 49, 52, 58],
    "/life/end-of-life/bereavement/": [31, 32, 33, 34],
    "/life/troubles-consult/farmland/inheritance/": [38, 41],
    "/life/troubles-consult/farmland/sell-or-rent/": [42, 44, 45],
    "/life/troubles-consult/farmland/conversion/": [43],
    "/life/housing/property-tax/": [51, 121],
    "/life/parents-care/care-started/": [63],
    "/life/parents-care/community-support-center/": [64],
    "/life/parents-care/dementia-consultation/": [65, 66],
    "/life/parents-care/long-term-care-insurance/": [61, 62, 67, 68, 69, 72, 73, 74, 75, 78, 139],
    "/life/parents-care/find-nursing-home/": [70, 71, 79],
    "/life/parents-care/check-parents/": [76, 77],
    "/life/start-living/how-to-garbage/": [81, 82, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98],
    "/life/start-living/bulky-garbage-dropoff/": [83, 84],
    "/life/moving-out/bulk-garbage-cleaning/": [99, 100],
    "/life/moving-out/move-out-notice/": [102],
    "/life/start-living/moved-in/": [101, 103, 109],
    "/life/start-living/certificates/": [104, 105, 106, 107, 112, 113, 114, 115],
    "/life/start-living/mynumber/": [108],
    "CREATE:/life/start-living/household-separation/": [110],
    "/life/start-living/resident-registration/": [111],
    "/life/living-soon/moving-decided/": [116],
    "/life/start-living/water-start-stop-fees/": [117, 118],
    "/life/moving-out/dog-ownership-change/": [119],
    "/life/work-life/light-vehicle-tax/": [120, 124],
    "/life/work-life/resident-tax/": [122, 123],
    "/life/work-life/national-health-insurance-tax/": [125],
    "/life/work-life/nhk-pension/": [126, 135, 136, 137, 138],
    "/life/troubles-consult/cannot-pay-tax/": [127],
    "/life/work-life/city-tax-payment/": [128, 129, 130],
    "/life/work-life/tax-certificates/": [131, 132, 133, 134],
    "/life/family-grow/child-allowance/": [141, 142],
    "/life/family-grow/childbirth/": [143, 159],
    "/life/family-grow/pregnancy/": [144, 145],
    "/life/family-grow/nursery-school/": [146, 147, 149],
    "/life/family-grow/nursery-childcare/": [148],
    "/life/education/school-zones/": [150, 151],
    "/life/education/school-district-transfer/": [152],
    "/life/education/school-expense-support/": [153],
    "/life/education/after-school-club/": [154],
    "/life/family-grow/child-vaccination/": [155],
    "/life/family-grow/infant-health-check/": [156],
    "/life/family-grow/single-parent-support/": [157],
    "/life/family-grow/parenting-support/": [158],
    "/life/moving-out/school-nursery-procedures/": [160],
    "/life/emergency/evacuation-hazard-map/": [161, 163, 164],
    "/life/emergency/evacuation-centers/": [162],
    "/life/emergency/road-river-info/": [165, 166],
    "/life/health-medical/night-holiday-medical/": [167, 168, 169],
    "CREATE:/life/emergency/child-emergency-care/": [170],
    "/life/emergency/disaster-mail-line/": [171],
    "CREATE:/life/emergency/power-outage/": [172],
    "CREATE:/life/emergency/water-outage/": [173],
    "/life/troubles-consult/consumer-fraud/": [174, 175],
    "/life/troubles-consult/legal-general-consultation/": [176],
    "/life/troubles-consult/living-costs-trouble/": [177, 178],
    "CREATE:/life/troubles-consult/dv-consultation/": [179],
    "CREATE:/life/troubles-consult/elder-abuse-consultation/": [180],
    "/life/living-soon/": [181],
    "/life/living-soon/about-morimachi/": [182, 197, 200],
    "/life/housing/build-house/": [183],
    "/life/work-life/subsidies/": [184],
    "/life/play-out/visit-library/": [185],
    "/life/play-out/facilities-library-parks/": [186, 187],
    "/life/play-out/find-parks/": [188],
    "/shrine/": [189],
    "/temple/": [190],
    "CREATE:/life/living-soon/areas/mori/": [191],
    "CREATE:/life/living-soon/areas/ichinomiya/": [192],
    "CREATE:/life/living-soon/areas/iida/": [193],
    "CREATE:/life/living-soon/areas/sonoda/": [194],
    "CREATE:/life/living-soon/areas/amagata/": [195],
    "CREATE:/life/living-soon/areas/mikura/": [196],
    "/life/start-living/public-transit/": [198],
    "CREATE:/life/living-soon/shopping/": [199],
}
MANUAL_TARGETS = {
    number: target
    for target, numbers in MANUAL_TARGET_GROUPS.items()
    for number in numbers
}
if set(MANUAL_TARGETS) != set(range(1, 201)):
    missing = sorted(set(range(1, 201)) - set(MANUAL_TARGETS))
    duplicate_count = sum(len(numbers) for numbers in MANUAL_TARGET_GROUPS.values()) - len(MANUAL_TARGETS)
    raise RuntimeError(f"手動判定が200件を網羅していません: missing={missing}, duplicates={duplicate_count}")


def normalize(value: str) -> str:
    value = unescape(re.sub(r"<[^>]+>", "", value))
    for word in GENERIC:
        value = value.replace(word, "")
    return re.sub(r"[\s　・/／｜|、。,.?？!！()（）「」『』【】\-—―]+", "", value).lower()


def parse_candidates() -> list[dict]:
    lines = WORK_ORDER.read_text(encoding="utf-8").splitlines()
    candidates: list[dict] = []
    group = ""
    current: dict | None = None
    for line in lines:
        heading = re.match(r"^###\s+(.+)$", line)
        if heading:
            group = heading.group(1).strip()
            continue
        row = re.match(r"^\s*(\d+)\s+(P[0-2])\s+(.*?)\s+`(/[^`]+)`\s+", line)
        if row:
            if current:
                candidates.append(current)
            current = {
                "number": int(row.group(1)),
                "priority": row.group(2),
                "group": group,
                "target_query": re.sub(r"\s+", " ", row.group(3)).strip(),
                "proposed_url": row.group(4),
            }
            continue
        if current and line.strip() and not line.lstrip().startswith("-"):
            indent = len(line) - len(line.lstrip(" "))
            if 20 <= indent <= 40:
                fragment = re.split(r"\s{2,}", line.strip(), maxsplit=1)[0].strip()
                if fragment and "｜" not in fragment and not fragment.startswith("/"):
                    current["target_query"] += " " + fragment
    if current:
        candidates.append(current)
    for item in candidates:
        item["target_query"] = re.sub(r"\s+", " ", item["target_query"]).strip()
        item["intent_phrase"] = re.sub(r"^森町\s*", "", item["target_query"]).strip()
    if len(candidates) != 200 or [x["number"] for x in candidates] != list(range(1, 201)):
        raise RuntimeError(f"200候補を正しく解析できませんでした: {len(candidates)}件")
    return candidates


def page_catalog() -> list[dict]:
    baseline = json.loads((BASELINE / "all-public-urls.json").read_text(encoding="utf-8"))
    by_path = {row["path"]: row for row in baseline}
    pages: dict[str, dict] = {}

    def add(path: str, aliases: list[str], sources: int = 0, kind: str = "page") -> None:
        live = by_path.get(path)
        if not live or live.get("http_status") != 200:
            return
        record = pages.setdefault(path, {
            "url": path,
            "kind": kind,
            "aliases": [],
            "official_source_count": sources,
            **{key: live.get(key, "") for key in (
                "title", "h1", "description", "canonical", "indexable",
                "incoming_links", "outgoing_links", "h1_count",
            )},
        })
        record["aliases"].extend(value for value in aliases if value)
        record["official_source_count"] = max(record["official_source_count"], sources)

    topics = json.loads((ROOT / "data" / "topics_master.json").read_text(encoding="utf-8"))
    for item in topics:
        aliases = [item.get("title", ""), item.get("intent", ""), item.get("primary_keyword", "")]
        aliases += item.get("synonyms", []) + item.get("needs", [])
        sources = len({s.get("url") for s in item.get("sources_morimachi", []) if s.get("url")})
        add(item["href"], aliases, sources, "life")

    questions = json.loads((ROOT / "data" / "questions.json").read_text(encoding="utf-8"))
    for item in questions:
        aliases = [item.get("title", ""), item.get("question", ""), item.get("context", ""), item.get("keyword", "")]
        aliases += item.get("needs", [])
        sources = len({s.get("url") for s in item.get("sources", []) if s.get("url")})
        add(item["href"], aliases, sources, "question")

    for path, live in by_path.items():
        if path.startswith(("/blog/", "/questions/")) or path in pages:
            continue
        if path.startswith(("/life/", "/shrine/", "/temple/", "/hub/", "/tools/")):
            add(path, [live.get("title", ""), live.get("h1", ""), path], 0, "page")
    return list(pages.values())


def score(candidate: dict, page: dict) -> tuple[float, str]:
    needle = normalize(candidate["intent_phrase"])
    tokens = [normalize(x) for x in candidate["intent_phrase"].split() if normalize(x)]
    best = 0.0
    best_alias = ""
    for alias in page["aliases"]:
        hay = normalize(alias)
        if not hay:
            continue
        value = SequenceMatcher(None, needle, hay).ratio() * 55
        if needle == hay:
            value += 150
        elif needle in hay or hay in needle:
            value += 75 * min(len(needle), len(hay)) / max(len(needle), len(hay))
        covered = sum(token in hay for token in tokens)
        if tokens:
            value += 45 * covered / len(tokens)
        if value > best:
            best, best_alias = value, alias
    if page["url"].startswith(GROUP_PREFIXES.get(candidate["group"], ())):
        best += 18
    else:
        best -= 12
    if page["kind"] == "life":
        best += 8
    return round(best, 2), best_alias


def meets_page_standard(page: dict) -> tuple[bool, list[str]]:
    gaps = []
    if page.get("h1_count") != 1:
        gaps.append("H1")
    desc_len = len(page.get("description", ""))
    if not 90 <= desc_len <= 130:
        gaps.append(f"description({desc_len}字)")
    if page.get("canonical") != "https://morimachi.enshu-lifehack.com" + page["url"]:
        gaps.append("canonical")
    if not page.get("indexable"):
        gaps.append("indexability")
    if int(page.get("incoming_links", 0)) < 3:
        gaps.append("被リンク3本未満")
    if int(page.get("outgoing_links", 0)) < 3:
        gaps.append("発リンク3本未満")
    if page.get("official_source_count", 0) < 1:
        gaps.append("一次情報")
    return not gaps, gaps


def decide(candidates: list[dict], pages: list[dict]) -> list[dict]:
    by_url = {page["url"]: page for page in pages}
    output = []
    for candidate in candidates:
        ranked = []
        for page in pages:
            value, alias = score(candidate, page)
            ranked.append((value, page, alias))
        ranked.sort(key=lambda x: (-x[0], x[1]["url"]))
        top_score, top, alias = ranked[0]
        second_score, second, _ = ranked[1]
        standard_ok, gaps = meets_page_standard(top)
        margin = round(top_score - second_score, 2)

        manual = MANUAL_TARGETS[candidate["number"]]
        if manual.startswith("CREATE:"):
            action = "CREATE"
            final_url = manual.removeprefix("CREATE:")
            confidence = "high"
            reason = "既存129ページと質問ページに同一の主要検索意図がないため、既存URL体系内に新設"
        else:
            target = by_url[manual]
            target_score, target_alias = score(candidate, target)
            target_standard, target_gaps = meets_page_standard(target)
            exact = any(normalize(candidate["intent_phrase"]) == normalize(value) for value in target["aliases"])
            if exact:
                action = "KEEP" if target_standard else "UPDATE"
            else:
                action = "MERGE"
            final_url = manual
            confidence = "high"
            top, top_score, alias = target, target_score, target_alias
            gaps = target_gaps
            reason = f"既存URLの主要意図・本文を手動確認し「{target_alias}」へ統合"
            if gaps and action in {"UPDATE", "MERGE"}:
                reason += "。不足: " + "、".join(gaps)
        output.append({
            **candidate,
            "action": action,
            "final_url": final_url,
            "matched_url": top["url"],
            "matched_title": top["title"],
            "matched_kind": top["kind"],
            "match_score": top_score,
            "score_margin": margin,
            "confidence": confidence,
            "decision_reason": reason,
            "second_url": second["url"],
            "second_score": second_score,
        })
    return output


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def build_existing_decisions(decisions: list[dict]) -> None:
    existing = json.loads((BASELINE / "existing-129-seo-ledger.json").read_text(encoding="utf-8"))
    targets: dict[str, list[dict]] = {}
    for row in decisions:
        if row["final_url"].startswith("/life/"):
            targets.setdefault(row["final_url"], []).append(row)
    for page in existing:
        matched = targets.get(page["existing_url"], [])
        if matched:
            actions = {row["action"] for row in matched}
            page["action"] = "UPDATE" if "UPDATE" in actions or "MERGE" in actions else "KEEP"
            page["candidate_numbers"] = " / ".join(str(row["number"]) for row in matched)
            page["candidate_queries"] = " / ".join(row["target_query"] for row in matched)
        else:
            old_action = page.get("action", "KEEP").upper()
            page["action"] = "UPDATE" if old_action in {"REWRITE", "UPDATE"} else "KEEP"
            page["candidate_numbers"] = ""
            page["candidate_queries"] = ""
    columns = list(existing[0])
    write_csv(EXISTING_CSV, existing, columns)


def main() -> None:
    candidates = parse_candidates()
    decisions = decide(candidates, page_catalog())
    OUT_JSON.write_text(json.dumps(decisions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    columns = [
        "number", "priority", "group", "target_query", "intent_phrase", "proposed_url",
        "action", "final_url", "matched_url", "matched_title", "matched_kind",
        "match_score", "score_margin", "confidence", "decision_reason", "second_url", "second_score",
    ]
    write_csv(OUT_CSV, decisions, columns)
    build_existing_decisions(decisions)

    print(f"候補: {len(decisions)}件")
    for key in ("action", "priority", "confidence"):
        counts: dict[str, int] = {}
        for row in decisions:
            counts[row[key]] = counts.get(row[key], 0) + 1
        print(key + ": " + ", ".join(f"{name}={count}" for name, count in sorted(counts.items())))
    print("低信頼候補:")
    for row in decisions:
        if row["confidence"] in {"low", "review"}:
            print(f"  {row['number']:03d} {row['target_query']} -> {row['matched_url']} ({row['match_score']}/{row['score_margin']})")


if __name__ == "__main__":
    main()
