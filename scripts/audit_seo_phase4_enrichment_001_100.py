#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第4期ID 1〜100の固有情報データを検証する。"""
from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "seo-phase4-enrichment-001-100.json"
TOPICS = ROOT / "data" / "seo-phase4-topics.json"
MORI_HOST = "www.town.morimachi.shizuoka.jp"
FORBIDDEN = "政" + "策"
REQUIRED_KEYS = {"id", "verified_facts", "morimachi_conditions", "section_headings", "faqs", "sources"}
MAX_SIMILARITY = 0.80


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def normalized(value: str) -> str:
    return re.sub(r"[\s、。・｜|（）()「」『』：:／/\-]", "", value)


def record_text(record: dict) -> str:
    return "".join(
        [x["statement"] for x in record["verified_facts"]]
        + record["morimachi_conditions"]
        + record["section_headings"]
        + [x["question"] + x["answer"] for x in record["faqs"]]
    )


def trigrams(value: str) -> set[str]:
    value = normalized(value)
    return {value[i:i + 3] for i in range(max(0, len(value) - 2))}


def similarity(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a or b else 1.0


def check_url(url: str) -> tuple[str, int | str]:
    request = urllib.request.Request(url, headers={"User-Agent": "MorimachiPhase4Audit/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            response.read(1)
            return url, int(response.status)
    except Exception as exc:
        return url, f"{type(exc).__name__}: {exc}"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="森町公式URLへ実アクセスしてHTTP 200を確認")
    args = parser.parse_args()

    records = json.loads(DATA.read_text(encoding="utf-8"))
    topics = {int(r["id"]): r for r in json.loads(TOPICS.read_text(encoding="utf-8"))}
    errors: list[str] = []
    if not isinstance(records, list):
        raise SystemExit("トップレベルは配列である必要があります")
    ids = [r.get("id") for r in records]
    if ids != list(range(1, 101)):
        fail(errors, f"IDが1〜100の昇順ではありません: {ids[:5]} ... {ids[-5:]}")

    all_questions: list[str] = []
    all_headings: list[str] = []
    source_urls: set[str] = set()
    for record in records:
        rid = record.get("id", "?")
        if set(record) != REQUIRED_KEYS:
            fail(errors, f"ID {rid}: schemaキー不一致 {sorted(set(record) ^ REQUIRED_KEYS)}")
            continue
        if rid not in topics:
            fail(errors, f"ID {rid}: 元トピックなし")
        facts = record["verified_facts"]
        conditions = record["morimachi_conditions"]
        headings = record["section_headings"]
        faqs = record["faqs"]
        sources = record["sources"]
        if len(facts) < 6:
            fail(errors, f"ID {rid}: verified_factsが6件未満")
        if len(conditions) < 3 or any(len(x.strip()) < 25 for x in conditions):
            fail(errors, f"ID {rid}: 森町条件が3件未満または短すぎます")
        if len(headings) < 12 or len(set(headings)) != len(headings):
            fail(errors, f"ID {rid}: 見出しが12件未満または記事内重複")
        if len(faqs) < 4 or len({x.get('question') for x in faqs}) != len(faqs):
            fail(errors, f"ID {rid}: FAQが4件未満または記事内重複")
        if not any("期限" in x["statement"] or "前日" in x["statement"] or "直前" in x["statement"] for x in facts):
            fail(errors, f"ID {rid}: 期限・再確認日の核心事実なし")
        if not any("課" in x["statement"] or "窓口" in x["statement"] or "図書館" in x["statement"] for x in facts):
            fail(errors, f"ID {rid}: 窓口の核心事実なし")
        if len(sources) < 3:
            fail(errors, f"ID {rid}: 森町公式ソースが3件未満")
        urls = []
        for source in sources:
            if set(source) != {"url", "role", "title", "status"}:
                fail(errors, f"ID {rid}: source schema不一致")
                continue
            url = source["url"]
            urls.append(url)
            source_urls.add(url)
            parsed = urlparse(url)
            if parsed.scheme != "https" or parsed.netloc != MORI_HOST:
                fail(errors, f"ID {rid}: 森町公式でないsource {url}")
            if not source["status"].startswith("verified-http-200-"):
                fail(errors, f"ID {rid}: URL実在確認statusなし {url}")
            if len(source["title"].strip()) < 2 or len(source["role"].strip()) < 8:
                fail(errors, f"ID {rid}: sourceのtitle/role不足 {url}")
        if len(urls) != len(set(urls)):
            fail(errors, f"ID {rid}: source URL重複")
        known_urls = set(urls)
        for fact in facts:
            if set(fact) != {"statement", "source_url"}:
                fail(errors, f"ID {rid}: fact schema不一致")
            elif fact["source_url"] not in known_urls:
                fail(errors, f"ID {rid}: factのsource_urlがsourcesにない")
        all_questions.extend(x["question"] for x in faqs)
        all_headings.extend(headings)

    if len(all_questions) != len(set(all_questions)):
        fail(errors, "100記事間でFAQ質問が重複しています")
    if len(all_headings) != len(set(all_headings)):
        fail(errors, "100記事間で見出しが重複しています")
    serialized = json.dumps(records, ensure_ascii=False)
    if FORBIDDEN in serialized:
        fail(errors, "禁止語がenrichmentデータに含まれています")

    grams = [trigrams(record_text(r)) for r in records]
    worst = (0.0, 0, 0)
    for i, j in itertools.combinations(range(len(records)), 2):
        score = similarity(grams[i], grams[j])
        if score > worst[0]:
            worst = (score, records[i]["id"], records[j]["id"])
    if worst[0] >= MAX_SIMILARITY:
        fail(errors, f"記事固有データの3-gram類似度が高すぎます: {worst[1]}-{worst[2]} {worst[0]:.4f}")

    live_results = []
    if args.live:
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(check_url, url) for url in sorted(source_urls)]
            for future in as_completed(futures):
                url, status = future.result()
                live_results.append((url, status))
                if status != 200:
                    fail(errors, f"URL実在確認失敗: {status} {url}")

    print(f"enrichment件数: {len(records)}")
    print(f"固有FAQ質問: {len(set(all_questions))} / {len(all_questions)}")
    print(f"固有見出し: {len(set(all_headings))} / {len(all_headings)}")
    print(f"森町公式URL: {len(source_urls)}件（各記事3件以上）")
    print(f"最大3-gram Jaccard類似度: {worst[0]:.4f}（ID {worst[1]} と {worst[2]}）")
    if args.live:
        ok = sum(status == 200 for _, status in live_results)
        print(f"URLライブ検証: HTTP 200 {ok}/{len(live_results)}")
    if errors:
        print("監査失敗", file=sys.stderr)
        for message in errors:
            print(f"- {message}", file=sys.stderr)
        return 1
    print("監査合格")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
