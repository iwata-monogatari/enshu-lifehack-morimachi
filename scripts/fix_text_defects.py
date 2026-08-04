# -*- coding: utf-8 -*-
"""表示テキストの不具合を直す（抜本改修指示書 2.3 / 8.2 / 19 P0）。

  1. 「森町の森町の」「森町立森町立」などの重複した地名接頭辞
  2. 検証スクリプトの内部メモ「（確認中: 本文未確認 0538-…）」が画面に出ている問題
  3. 助詞で終わる・意味が途中で切れるリンク文言

topics_master.json（データ）と生成済みHTMLの両方を直す。冪等。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

# 1. 重複接頭辞
DUP_PREFIX = [
    (re.compile(r"森町の森町の"), "森町の"),
    (re.compile(r"森町立森町立"), "森町立"),
    (re.compile(r"森町森町"), "森町"),
]

# 2. 検証メモの露出。値からは取り除き、代わりに1文だけ添える。
UNVERIFIED_RE = re.compile(r"（確認中: 本文未確認[^）]*）")
UNVERIFIED_NOTE = "（一部の番号は公式ページ本文で再確認できていません）"

# 3. 意味が途中で切れるリンク文言（指示書 8.3 の修正例に準拠）
LINK_TEXT_FIXES = {
    "学区": "森町の通学区を確認する",
    "移動手段": "森町での移動手段を確認する",
    "転出届": "森町の転出届を提出する",
    "認知症の相談": "森町の認知症の相談窓口を見る",
    "転出前の片付けは、粗大ごみは中遠広域施設へ・家電は家電リサイクル法対応で":
        "森町からの転出前に粗大ごみ・家電を処分する",
    "転出届は引っ越し予定日の14日前から住民生活課住民係で":
        "森町の転出届は引っ越し予定日の14日前から提出できる",
}


def clean_value(value: str) -> tuple[str, bool]:
    """facts の値から検証メモを取り除く。取り除いたら True を返す。"""
    if not isinstance(value, str) or not UNVERIFIED_RE.search(value):
        return value, False
    cleaned = UNVERIFIED_RE.sub("", value).strip()
    return (cleaned + UNVERIFIED_NOTE), True


def fix_topics() -> tuple[int, int]:
    path = ROOT / "data" / "topics_master.json"
    topics = json.loads(path.read_text(encoding="utf-8"))
    dup = memo = 0
    for topic in topics:
        for key in ("title", "title_iwata", "intent"):
            if isinstance(topic.get(key), str):
                before = topic[key]
                for pattern, repl in DUP_PREFIX:
                    topic[key] = pattern.sub(repl, topic[key])
                if topic[key] != before:
                    dup += 1
        facts = topic.get("facts") or {}
        for fk, fv in list(facts.items()):
            new, hit = clean_value(fv)
            if hit:
                facts[fk] = new
                memo += 1
    path.write_text(json.dumps(topics, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return dup, memo


def fix_html() -> dict[str, int]:
    counts = {"dup": 0, "memo": 0, "link": 0, "files": 0}
    for path in sorted(ROOT.rglob("*.html")):
        if {".git", "_cache", "node_modules", "reports", "parts"} & set(
                path.relative_to(ROOT).parts):
            continue
        html = original = path.read_text(encoding="utf-8")

        for pattern, repl in DUP_PREFIX:
            html, n = pattern.subn(repl, html)
            counts["dup"] += n

        # 同一要素内に複数出るので、まとめて1つの注記に畳む
        def collapse(m: re.Match) -> str:
            return ""
        if UNVERIFIED_RE.search(html):
            html = UNVERIFIED_RE.sub(collapse, html)
            counts["memo"] += 1

        for before, after in LINK_TEXT_FIXES.items():
            pattern = re.compile(r"(<a[^>]+href=\"/life/[^\"]+\"[^>]*>)"
                                 + re.escape(before) + r"(</a>)")
            html, n = pattern.subn(r"\g<1>" + after + r"\g<2>", html)
            counts["link"] += n

        if html != original:
            path.write_text(html, encoding="utf-8")
            counts["files"] += 1
    return counts


def rebuild_category_labels() -> int:
    """categories.json のリンク文言を intent（完結した行動の文）に置き換える。

    「児童手当を」「婚姻届を出す日と」のような、リンク単体で意味が通らない
    ラベルをなくす（指示書 2.3 / 8.3）。
    """
    cat_path = ROOT / "data" / "categories.json"
    topics = json.loads((ROOT / "data" / "topics_master.json").read_text(encoding="utf-8"))
    by_href = {t["href"]: t for t in topics}
    data = json.loads(cat_path.read_text(encoding="utf-8-sig"))
    fixed = 0
    for cat in data["categories"]:
        kept = []
        for item in cat["items"]:
            href = item["url"].replace("https://morimachi.enshu-lifehack.com", "")
            topic = by_href.get(href)
            if topic and topic.get("action") == "merge":
                continue  # 統合したページは一覧から外す
            if topic and topic.get("intent"):
                if item["label"] != topic["intent"]:
                    item["label"] = topic["intent"]
                    fixed += 1
            kept.append(item)
        cat["items"] = kept
    cat_path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")
    return fixed


def main() -> None:
    dup, memo = fix_topics()
    print(f"topics_master.json: 重複接頭辞 {dup} 件 / 検証メモ {memo} 件を修正")
    counts = fix_html()
    print(f"HTML: {counts['files']} ファイルを更新")
    print(f"  重複接頭辞      : {counts['dup']} 箇所")
    print(f"  検証メモの除去  : {counts['memo']} ページ")
    print(f"  リンク文言の修正: {counts['link']} 箇所")
    print(f"categories.json: リンク文言 {rebuild_category_labels()} 件を完結した文に置換")


if __name__ == "__main__":
    main()
