# -*- coding: utf-8 -*-
"""記事台帳を作る（修正指示書 9 / 10 / 11）。

「最終確認日」を、公式リンクを開いた日ではなく
「窓口名・電話番号・受付時間・費用・対象者・期限・必要書類・公式リンク・
　国制度との矛盾・時点表現を確認した日」として管理できるようにする。

review_status
  verified      重要項目を必要な一次情報で確認済み → 画面に最終確認日を表示してよい
  partial       一部のみ確認・電話確認待ち・国と自治体で記載が食い違う
  needs_review  確認期限切れ、または一次情報が未確認
  archived      制度終了・記事廃止

risk_level と見直し頻度（修正指示書10）
  A 救急・医療・法律・税・死亡・期限・給付 … 3か月
  B 受付時間・料金・電話番号・ごみ・施設運用 … 6か月
  C 公園・文化・地域紹介 … 12か月

出力: reports/morimachi-pages-ledger.csv / data/article-ledger.json
"""
from __future__ import annotations

import csv
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

TODAY = date(2026, 8, 5)

# リスク区分（修正指示書10）。カテゴリ既定＋ページ個別の上書き。
RISK_BY_CATEGORY = {
    "もしもの時": "A", "健康・医療": "A", "人生の終わり": "A",
    "親のこと": "A", "困った・相談したい": "A",
    "働く・暮らす": "B", "暮らし始めた": "B", "新しい場所へ": "B",
    "家族が増える": "B", "学ぶ・育つ": "B", "家・住まい": "B",
    "これから暮らす": "C", "遊ぶ・使う・出かける": "C",
}
RISK_OVERRIDE = {
    "/life/troubles-consult/farmland/": "A",
    "/life/housing/property-tax/": "A",
    "/life/end-of-life/inheritance/": "A",
}
REVIEW_MONTHS = {"A": 3, "B": 6, "C": 12}

# 一次情報を確認したうえで国制度との差を注記したページ（2026-08-05 実施）
NATIONAL_CHECKED = {
    "/life/end-of-life/bereavement/": {
        "national_system_checked_at": "2026-08-05",
        "notes": "法務省の戸籍届書押印廃止（2021-09-01）を確認。"
                 "森町公式の死亡届ページは更新日2020-02-25で「届出人の印鑑」の記載が残るため、"
                 "差を本文に注記。押印は任意と記載した。",
        "status": "partial",  # 電話確認が未実施のため verified にしない
    },
    "/life/start-living/how-to-garbage/": {
        "municipality_page_checked_at": "2026-08-05",
        "notes": "森町公式（更新日2026-04-15）で、令和8年4月1日からの分別ルール変更は実施済み、"
                 "令和8年度版の分別表・収集日カレンダーは配布済みと確認。"
                 "改訂作業中なのは分別ガイドブックのみ。",
        "status": "verified",
    },
    "/life/emergency/disaster-mail-line/": {
        "municipality_page_checked_at": "2026-08-05",
        "notes": "森町公式（更新日2021-02-01）に「令和8年3月で終了」の記載。"
                 "その時期は経過しているが、実際に終了したかはページから確認できないため partial。",
        "status": "partial",
    },
}


def months_after(iso: str, months: int) -> str:
    y, m, d = (int(x) for x in iso.split("-"))
    m += months
    y += (m - 1) // 12
    m = (m - 1) % 12 + 1
    try:
        return date(y, m, d).isoformat()
    except ValueError:
        return (date(y, m, 1) + timedelta(days=27)).isoformat()


def page_verified_at(href: str) -> str:
    path = ROOT / href.strip("/") / "index.html"
    if not path.exists():
        return ""
    m = re.search(r"最終確認日[：:]\s*(\d{4}-\d{2}-\d{2})",
                  path.read_text(encoding="utf-8"))
    return m.group(1) if m else ""


def main() -> None:
    topics = json.loads((ROOT / "data" / "topics_master.json").read_text(encoding="utf-8"))
    rows = []
    for t in topics:
        if t.get("action") == "merge":
            continue
        href = t["href"]
        category = t.get("category", "")
        risk = RISK_OVERRIDE.get(href) or RISK_BY_CATEGORY.get(category, "B")
        verified_at = page_verified_at(href)
        sources = t.get("sources_morimachi") or []
        override = NATIONAL_CHECKED.get(href, {})

        if not verified_at:
            status = "needs_review"
        elif not sources:
            status = "needs_review"
        else:
            status = "verified"
        status = override.get("status", status)

        next_review = months_after(verified_at, REVIEW_MONTHS[risk]) if verified_at else ""
        overdue = bool(next_review and next_review < TODAY.isoformat())
        if overdue and status == "verified":
            status = "needs_review"

        rows.append({
            "id": "mori-" + href.strip("/").replace("/", "-"),
            "url": href,
            "title": t.get("title", ""),
            "category": category,
            "hub": t.get("hub", ""),
            "risk_level": risk,
            "review_status": status,
            "content_owner": "大石浩之",
            "last_verified_at": verified_at,
            "municipality_page_checked_at":
                override.get("municipality_page_checked_at", verified_at),
            "national_system_checked_at": override.get("national_system_checked_at", ""),
            "phone_verified_at": "",
            "next_review_at": next_review,
            "review_overdue": "はい" if overdue else "いいえ",
            "source_count": len(sources),
            "source_urls": " / ".join(s.get("url", "") for s in sources[:3]),
            "notes": override.get("notes", ""),
        })

    csv_path = ROOT / "reports" / "morimachi-pages-ledger.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    (ROOT / "data" / "article-ledger.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    counts: dict[str, int] = {}
    risks: dict[str, int] = {}
    for r in rows:
        counts[r["review_status"]] = counts.get(r["review_status"], 0) + 1
        risks[r["risk_level"]] = risks.get(r["risk_level"], 0) + 1
    print(f"記事台帳を出力しました: {len(rows)} 件")
    print("  確認状態: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    print("  リスク区分: " + ", ".join(f"{k}={v}" for k, v in sorted(risks.items())))
    overdue = [r for r in rows if r["review_overdue"] == "はい"]
    print(f"  確認期限を過ぎたページ: {len(overdue)} 件")
    for r in overdue[:10]:
        print(f"    [{r['risk_level']}] {r['url']}（期限 {r['next_review_at']}）")
    print(f"  {csv_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
