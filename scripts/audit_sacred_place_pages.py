#!/usr/bin/env python3
"""神社・寺院の全個別ページが、人向けの公開文として読めることを検査する。"""
from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COLLECTIONS = (
    ("神社", ROOT / "data" / "shrines.json", "shrines", ROOT / "shrine" / "shrines", 39),
    ("寺院", ROOT / "data" / "temples.json", "temples", ROOT / "temple" / "temples", 35),
)

INTERNAL_PHRASES = (
    "確認する論点：",
    "資料に残すこと：",
    "森町での現地確認：",
    "判断へつなげる方法：",
    "断定前の深掘り確認",
    "このページに統合した検索意図",
    "更新確認ノート",
    "今日決めること",
    "後で確かめること",
    "担当者へ聞くこと",
    "資料待ち",
    "公開情報調査済み",
    "未確認",
    "未訪問",
    "この条件は、",
    "結論を左右する前提です",
)


def visible_text(source: str) -> str:
    source = re.sub(r"<script.*?</script>|<style.*?</style>", "", source, flags=re.S | re.I)
    return unescape(re.sub(r"<[^>]+>", " ", source))


def meta_value(source: str, name: str) -> str:
    match = re.search(rf'<meta\s+name="{re.escape(name)}"\s+content="([^"]*)"', source, re.I)
    return unescape(match.group(1)).strip() if match else ""


def main() -> None:
    failures: list[str] = []
    titles: dict[str, str] = {}
    descriptions: dict[str, str] = {}
    totals: list[tuple[str, int, int]] = []

    for label, ledger_path, key, directory, expected in COLLECTIONS:
        rows = json.loads(ledger_path.read_text(encoding="utf-8-sig"))[key]
        actual_dirs = {p.name for p in directory.iterdir() if p.is_dir()}
        expected_dirs = {row["slug"] for row in rows}
        if len(rows) != expected or actual_dirs != expected_dirs:
            failures.append(
                f"{label}件数不一致: 台帳 {len(rows)} / HTML {len(actual_dirs)} / 想定 {expected}"
            )

        for row in rows:
            slug = row["slug"]
            path = directory / slug / "index.html"
            if not path.is_file():
                failures.append(f"HTMLなし: {path.relative_to(ROOT)}")
                continue
            source = path.read_text(encoding="utf-8")
            text = visible_text(source)
            compact = re.sub(r"\s+", "", text)
            rel = str(path.relative_to(ROOT)).replace("\\", "/")
            page_failures: list[str] = []

            if row["name"] not in text:
                page_failures.append("名称なし")
            if row.get("address") and "未確認" not in row["address"] and row["address"] not in text:
                page_failures.append("所在地なし")
            if len(compact) < 1200:
                page_failures.append(f"本文不足 {len(compact)}字")
            if source.count("<h1") != 1:
                page_failures.append("H1が一つでない")
            if source.count("<h2") < 5:
                page_failures.append("H2が5個未満")
            if source.count("<p") < 12:
                page_failures.append("段落が12個未満")
            if len(re.findall(r'href="/(?!/)', source)) < 3:
                page_failures.append("内部リンクが3個未満")
            if source.count('target="_blank"') < 2:
                page_failures.append("公的出典が2件未満")
            if source.count('rel="canonical"') != 1:
                page_failures.append("canonicalが一つでない")
            if slug != "s4410001" and 'data-content-quality="human-readable"' not in source:
                page_failures.append("人向け本文マーカーなし")
            if slug == "s4410003" and len(re.findall(r'src="yamana-shrine-[^"]+\.jpg"', source)) != 4:
                page_failures.append("山名神社の提供写真が4点でない")
            found_internal = [phrase for phrase in INTERNAL_PHRASES if phrase in source]
            if found_internal:
                page_failures.append("内部管理文: " + " / ".join(found_internal))

            title_match = re.search(r"<title>(.*?)</title>", source, re.S | re.I)
            title = unescape(title_match.group(1)).strip() if title_match else ""
            desc = meta_value(source, "description")
            if not title or title in titles:
                page_failures.append("titleなし・重複")
            else:
                titles[title] = rel
            if len(desc) < 55 or desc in descriptions:
                page_failures.append("description不足・重複")
            else:
                descriptions[desc] = rel

            if page_failures:
                failures.append(f"{rel}: " + ", ".join(page_failures))
            totals.append((label, len(compact), source.count("<h2")))

    if failures:
        raise SystemExit("社寺個別ページ監査失敗\n- " + "\n- ".join(failures))

    shrine_lengths = [length for label, length, _ in totals if label == "神社"]
    temple_lengths = [length for label, length, _ in totals if label == "寺院"]
    print(
        "社寺個別ページ監査: 合格 "
        f"神社{len(shrine_lengths)}件（最短{min(shrine_lengths)}字） / "
        f"寺院{len(temple_lengths)}件（最短{min(temple_lengths)}字） / 内部管理文0件"
    )


if __name__ == "__main__":
    main()
