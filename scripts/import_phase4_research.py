#!/usr/bin/env python3
"""検証済みの第4期調査JSONをenrichment台帳へ安全に統合する。"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
from urllib.parse import urlparse

from build_seo_phase4 import substantive_facts


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET = ROOT / "data" / "seo-phase4-enrichment-201-300.json"
PUBLICATION = ROOT / "data" / "seo-phase4-publication.json"
ALLOWED_FIELDS = (
    "verified_facts",
    "morimachi_conditions",
    "section_headings",
    "faqs",
    "sources",
)
OPTIONAL_FIELDS = ("section_paragraphs",)


def records_from(document: object, source: Path) -> list[dict]:
    if isinstance(document, list):
        rows = document
    elif isinstance(document, dict):
        rows = None
        for key in ("records", "items", "candidates", "selected_candidates", "selected"):
            value = document.get(key)
            if isinstance(value, list):
                rows = value
                break
        if rows is None:
            raise ValueError(f"{source}: 候補配列がありません")
    else:
        raise ValueError(f"{source}: JSONのルート形式が不正です")
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"{source}: 候補はオブジェクト配列である必要があります")
    return rows


def validate_candidate(row: dict, source: Path) -> dict:
    try:
        item_id = int(row["id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{source}: idが不正です") from exc
    if not 1 <= item_id <= 300:
        raise ValueError(f"{source}: ID{item_id} は1-300の範囲外です")

    normalized = {"id": item_id}
    for field in ALLOWED_FIELDS:
        value = row.get(field)
        if not isinstance(value, list):
            raise ValueError(f"{source}: ID{item_id} {field} は配列が必要です")
        normalized[field] = value
    for field in OPTIONAL_FIELDS:
        if field in row:
            normalized[field] = row[field]

    facts = normalized["verified_facts"]
    conditions = normalized["morimachi_conditions"]
    headings = normalized["section_headings"]
    faqs = normalized["faqs"]
    sources = normalized["sources"]
    if len(facts) < 12:
        raise ValueError(f"{source}: ID{item_id} 固有事実が12件未満です")
    if len(conditions) < 3:
        raise ValueError(f"{source}: ID{item_id} 森町条件が3件未満です")
    if len(headings) != 12 or len(set(headings)) != 12:
        raise ValueError(f"{source}: ID{item_id} 固有見出しは重複なし12件が必要です")
    if len(faqs) < 4:
        raise ValueError(f"{source}: ID{item_id} FAQが4件未満です")
    if len(sources) < 3:
        raise ValueError(f"{source}: ID{item_id} 出典が3件未満です")

    curated_sections = normalized.get("section_paragraphs")
    if curated_sections is None:
        raise ValueError(f"{source}: ID{item_id} 主題専用本文section_paragraphsがありません")
    if curated_sections is not None:
        if not isinstance(curated_sections, list) or len(curated_sections) != 12:
            raise ValueError(f"{source}: ID{item_id} 専用本文は12節が必要です")
        curated_paragraphs: list[str] = []
        curated_headings: list[str] = []
        for section in curated_sections:
            if not isinstance(section, dict):
                raise ValueError(f"{source}: ID{item_id} 専用本文の節形式が不正です")
            heading = str(section.get("heading", "")).strip()
            paragraphs = section.get("paragraphs")
            if not heading or not isinstance(paragraphs, list) or len(paragraphs) < 3:
                raise ValueError(f"{source}: ID{item_id} 各節に見出しと3段落以上が必要です")
            if not all(isinstance(value, str) and value.strip() for value in paragraphs):
                raise ValueError(f"{source}: ID{item_id} 専用段落に空欄があります")
            if any(len("".join(value.split())) > 360 for value in paragraphs):
                raise ValueError(f"{source}: ID{item_id} 専用段落に360字超があります")
            curated_headings.append(heading)
            curated_paragraphs.extend(value.strip() for value in paragraphs)
        if curated_headings != headings:
            raise ValueError(f"{source}: ID{item_id} 専用本文の見出しがsection_headingsと一致しません")
        if len(curated_paragraphs) < 36:
            raise ValueError(f"{source}: ID{item_id} 専用本文は36段落以上が必要です")
        if len(set(curated_paragraphs)) != len(curated_paragraphs):
            raise ValueError(f"{source}: ID{item_id} 専用本文内に完全重複段落があります")
        visible_chars = sum(len("".join(value.split())) for value in curated_paragraphs)
        if visible_chars < 5000:
            raise ValueError(f"{source}: ID{item_id} 専用本文が5000字未満です ({visible_chars})")

    source_urls: list[str] = []
    source_refs: dict[str, str] = {}
    normalized_sources: list[dict] = []
    town_sources = 0
    external_official = 0
    for entry in sources:
        if not isinstance(entry, dict):
            raise ValueError(f"{source}: ID{item_id} 出典形式が不正です")
        url = str(entry.get("url", ""))
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError(f"{source}: ID{item_id} HTTPSでない出典があります: {url}")
        status = entry.get("status")
        if status is None and entry.get("http_status") == 200:
            status = "verified-http-200"
        checked_at = str(entry.get("checked_at", ""))[:10]
        if status != "verified-http-200" or not checked_at:
            raise ValueError(f"{source}: ID{item_id} 出典のHTTP確認状態が不足しています: {url}")
        source_urls.append(url)
        for reference_key in (entry.get("id"), entry.get("source_id")):
            if reference_key:
                source_refs[str(reference_key)] = url
        if parsed.netloc == "www.town.morimachi.shizuoka.jp":
            town_sources += 1
            role = "primary"
        elif parsed.netloc.endswith(".go.jp") or parsed.netloc.endswith(".lg.jp") or parsed.netloc.endswith("pref.shizuoka.jp"):
            external_official += 1
            role = "official-secondary"
        else:
            role = str(entry.get("role") or "official-secondary")
        normalized_sources.append({
            "url": url,
            "role": role,
            "title": str(entry.get("title") or entry.get("name") or "一次情報"),
            "status": status,
            "checked_at": checked_at,
        })
    if len(source_urls) != len(set(source_urls)):
        raise ValueError(f"{source}: ID{item_id} 出典URLが重複しています")
    if town_sources < 2 or external_official < 1:
        raise ValueError(f"{source}: ID{item_id} は森町公式2件と国・県一次1件が必要です")

    known = set(source_urls)
    normalized_facts: list[dict] = []
    for fact in facts:
        if not isinstance(fact, dict):
            raise ValueError(f"{source}: ID{item_id} 事実項目の本文が不正です")
        statement = str(fact.get("statement") or fact.get("fact") or "").strip()
        if not statement:
            raise ValueError(f"{source}: ID{item_id} 事実項目の本文が不正です")
        fact_url = fact.get("source_url")
        if not fact_url:
            reference_ids = fact.get("source_ids") or [fact.get("source_id")]
            fact_url = next((source_refs.get(str(ref)) for ref in reference_ids if ref), None)
        if fact_url not in known:
            raise ValueError(f"{source}: ID{item_id} 事実の出典がsourcesにありません")
        normalized_facts.append({"statement": statement, "source_url": fact_url})
    normalized["verified_facts"] = normalized_facts
    normalized["sources"] = normalized_sources
    accepted_facts = substantive_facts(normalized)
    if len(accepted_facts) < 6:
        rejected = len(normalized_facts) - len(accepted_facts)
        raise ValueError(
            f"{source}: ID{item_id} 実内容の固有事実が6件未満です "
            f"({len(accepted_facts)}/6、除外{rejected}件)"
        )
    return normalized


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("proposals", nargs="+", type=Path)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument(
        "--allow-published",
        action="store_true",
        help="監査済みの既公開記事を意図的に改稿する場合だけ上書きを許可する",
    )
    args = parser.parse_args()

    publication = json.loads(PUBLICATION.read_text(encoding="utf-8"))
    published_ids = {int(row["id"]) for row in publication if row.get("publish_ready") is True}
    updates: dict[int, dict] = {}
    for proposal in args.proposals:
        path = proposal if proposal.is_absolute() else ROOT / proposal
        document = json.loads(path.read_text(encoding="utf-8"))
        for raw in records_from(document, path):
            row = validate_candidate(raw, path)
            item_id = row["id"]
            if item_id in published_ids and not args.allow_published:
                raise ValueError(f"ID{item_id} は公開済みのため上書きできません")
            if item_id in updates:
                raise ValueError(f"ID{item_id} が複数の調査ファイルにあります")
            updates[item_id] = row

    normalized_paragraphs: list[str] = []
    for row in updates.values():
        for section in row["section_paragraphs"]:
            for paragraph in section["paragraphs"]:
                normalized = re.sub(r"\s+|\d+", "", paragraph)
                normalized = re.sub(r"「[^」]{1,90}」", "「固有語」", normalized)
                normalized_paragraphs.append(normalized)
    repeated = Counter(normalized_paragraphs)
    repeated_occurrences = sum(count for count in repeated.values() if count > 1)
    repeated_ratio = repeated_occurrences / max(1, len(normalized_paragraphs))
    if repeated_ratio > 0.25:
        raise ValueError(f"調査候補間の正規化段落反復率が25%を超えています: {repeated_ratio:.1%}")

    target = args.target if args.target.is_absolute() else ROOT / args.target
    rows = json.loads(target.read_text(encoding="utf-8"))
    by_id = {int(row["id"]): row for row in rows}
    missing = sorted(set(updates) - set(by_id))
    if missing:
        raise ValueError(f"統合先にIDがありません: {missing}")
    for item_id, update in updates.items():
        by_id[item_id].update(update)

    print(f"Phase4調査統合検証: {len(updates)}件 / IDs {','.join(map(str, sorted(updates)))}")
    if not args.check_only:
        target.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"更新: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
