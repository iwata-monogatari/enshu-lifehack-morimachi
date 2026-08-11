#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第4期300ページを25件単位で機械読解監査する安全ゲート。

文字数やタグの有無だけでなく、読者向けではない編集語、不自然な句読点、
長すぎる段落、同一ページ内の文の反復、descriptionの日本語を検査する。
"""
from __future__ import annotations

import json
import re
from collections import Counter
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "phase4-reading-audit"
BATCH_SIZE = 25
EDITORIAL_TERMS = (
    "焦点「", "断定防止", "第1論点", "第2論点", "第3論点", "第4論点",
    "第5論点", "編集上の印", "生成用", "テンプレート", "カニバリ",
)
REPETITIVE_PHRASES = (
    "ここでは、", "の資料を集めるだけの作業ではありません",
    "検索結果の短い説明ではなく", "この内容が当てはまるとは限らないため",
)
CRITICAL_REQUIRED = {
    82: ("警戒レベル4", "避難"),
    131: ("3年以内", "2027年3月31日"),
    245: ("2週間以内", "2,000平方メートル", "5,000平方メートル", "10,000平方メートル"),
}


def text_of(fragment: str) -> str:
    return re.sub(r"\s+", "", unescape(re.sub(r"<[^>]+>", "", fragment)))


def audit_page(item: dict) -> dict:
    path = ROOT / item["url"].strip("/") / "index.html"
    failures: list[str] = []
    html = path.read_text(encoding="utf-8") if path.is_file() else ""
    if not html:
        return {"id": item["id"], "url": item["url"], "failures": ["HTMLなし"]}
    article_match = re.search(r'<article class="post-editorial-body">(.*?)</article>', html, re.S)
    article = article_match.group(1) if article_match else ""
    editorial = text_of(article)
    paragraphs = [text_of(x) for x in re.findall(r"<p[^>]*>(.*?)</p>", article, re.S)]
    paragraphs = [p for p in paragraphs if p]
    description_match = re.search(r'<meta name="description" content="([^"]*)">', html)
    description = unescape(description_match.group(1)) if description_match else ""
    minimum_chars = 5000 if "PHASE4-CURATED" in html else 6000
    if not minimum_chars <= len(editorial) <= 8000:
        failures.append(f"編集本文が{minimum_chars}〜8000字外:{len(editorial)}")
    if not 70 <= len(description) <= 130:
        failures.append(f"descriptionが70〜130字外:{len(description)}")
    if re.search(r"^静岡県.+人向け", description):
        failures.append("descriptionの主語が不自然")
    for term in EDITORIAL_TERMS:
        if term in editorial or term in description:
            failures.append(f"編集用語が露出:{term}")
    for phrase in REPETITIVE_PHRASES:
        if phrase in editorial:
            failures.append(f"旧反復構文が残存:{phrase}")
    if "。。" in editorial or "？？" in editorial or "。。" in description:
        failures.append("句読点の重複")
    if re.search(r"「「|」」", editorial):
        failures.append("引用符の不自然な入れ子")
    if len(paragraphs) < 35:
        failures.append(f"段落不足:{len(paragraphs)}")
    long_paragraphs = [len(p) for p in paragraphs if len(p) > 360]
    if long_paragraphs:
        failures.append(f"360字超段落:{len(long_paragraphs)}")
    normalized = [re.sub(r"[「」『』\d\s]", "", paragraph) for paragraph in paragraphs]
    paragraph_counts = Counter(normalized)
    duplicates = [paragraph for paragraph in paragraph_counts if paragraph_counts[paragraph] > 1 and len(paragraph) >= 80]
    if duplicates:
        failures.append(f"同一段落反復:{len(duplicates)}")
    title_stem = str(item["title"]).split("｜", 1)[0]
    title_repetitions = editorial.count(title_stem)
    if title_repetitions > 12:
        failures.append(f"タイトル相当語句の反復過多:{title_repetitions}")
    if re.search(r"(.{8,80})のうち\1を扱います", editorial):
        failures.append("見出し自己反復")
    for required in CRITICAL_REQUIRED.get(int(item["id"]), ()):
        if required not in editorial:
            failures.append(f"核心事実なし:{required}")
    if "先に結論を確認する" not in html:
        failures.append("質問への直接回答なし")
    if "大石の視点" not in html:
        failures.append("大石の視点なし")
    if html.count('target="_blank"') < 3:
        failures.append("一次情報3件未満")
    return {
        "id": item["id"], "url": item["url"], "title": item["title"],
        "editorial_chars": len(editorial), "paragraphs": len(paragraphs),
        "description_chars": len(description), "title_repetitions": title_repetitions,
        "failures": sorted(set(failures)),
        "sample": paragraphs[:3],
    }


def main() -> None:
    publication = json.loads((ROOT / "data" / "seo-phase4-publication.json").read_text(encoding="utf-8"))
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    results = [audit_page(item) for item in publication]
    batches = []
    for start in range(0, len(results), BATCH_SIZE):
        pages = results[start:start + BATCH_SIZE]
        batch = {
            "batch": f"{start + 1:03d}-{start + len(pages):03d}",
            "status": "PASS" if all(not p["failures"] for p in pages) else "FAIL",
            "pages": pages,
        }
        batches.append(batch)
        (REPORT_DIR / f'batch-{batch["batch"]}.json').write_text(
            json.dumps(batch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    failed = [page for page in results if page["failures"]]
    summary = {
        "status": "PASS" if not failed and len(results) == 300 else "FAIL",
        "page_count": len(results), "batch_size": BATCH_SIZE,
        "batch_count": len(batches), "failed_pages": len(failed),
        "min_chars": min(p["editorial_chars"] for p in results),
        "max_chars": max(p["editorial_chars"] for p in results),
        "min_paragraphs": min(p["paragraphs"] for p in results),
        "failed": failed,
    }
    (REPORT_DIR / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if summary["status"] != "PASS":
        raise SystemExit("第4期読解監査失敗\n" + "\n".join(
            f'- {p["url"]}: {", ".join(p["failures"])}' for p in failed[:50]
        ))
    print(
        f'第4期読解監査: 300/300 PASS / 25件×{len(batches)}バッチ / '
        f'{summary["min_chars"]}〜{summary["max_chars"]}字 / 最少{summary["min_paragraphs"]}段落'
    )


if __name__ == "__main__":
    main()
