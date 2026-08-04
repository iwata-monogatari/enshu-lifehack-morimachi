# -*- coding: utf-8 -*-
"""CTAの出し分けを指示書 11.2 に合わせ直す。

  空き家・親の家・相続不動産   → real_estate
  親の介護・高齢者住宅         → care
  寺院・法要・墓               → guide（実家整理へ直接進めず、関連ガイドを1段挟む）
  一般行政手続き               → none
  緊急・医療・生活困窮          → none

あわせて data/pages.json から統合済みページを取り除き、
公式サイトへの遷移の計測名を指示書16.1の official_link_click にそろえる。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

# 明示的に営業CTAを出さないページ（緊急・医療・生活困窮・一般行政手続き）
NO_CTA = {
    "/life/troubles-consult/cannot-pay-tax/",
    "/life/troubles-consult/living-costs-trouble/",
    "/life/troubles-consult/consumer-fraud/",
    "/life/troubles-consult/child-consultation/",
    "/life/housing/public-housing-consultation/",
    "/life/housing/municipal-housing/",
    "/life/housing/rent-house/",
    "/life/housing/buy-house/",
    "/life/housing/build-house/",
    "/life/end-of-life/pension-inheritance/",
    "/life/moving-out/",
    "/life/moving-out/moving-away/",
    "/life/moving-out/move-out-notice/",
    "/life/moving-out/bulk-garbage-cleaning/",
    "/life/moving-out/dog-ownership-change/",
    "/life/moving-out/school-nursery-procedures/",
}

# 実家整理へ直接進めず、関連ガイドを1段挟むページ（指示書 11.2）
GUIDE_CTA = {
    "/life/end-of-life/grave-memorial/",
}

GUIDE_RULE = {
    "label": "関連ガイド",
    "strength": "weak",
    "heading": "あわせて確認したいこと",
    "description": "お墓や供養の手続きのあと、実家や仏具の整理が必要になることがあります。"
                   "順番に整理したい方向けのガイドです。",
    "button_text": "実家じまいの進め方ガイドを見る",
    "url": "/temple/guide/",
    "provider": "森町ライフハック",
    "internal": True,
}


def update_rules() -> None:
    path = ROOT / "data" / "cta-rules.json"
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    data["rules"]["guide"] = GUIDE_RULE
    data["_disclosure_policy"] = (
        "real_estate / care / both の各CTAには必ず disclosure を表示する"
        "（景表法ステルスマーケティング規制。2023年10月1日施行）。"
        "guide はサイト内の案内のため disclosure を持たない。"
        "緊急・医療・生活困窮・一般行政手続きのページには営業CTAを出さない（改修指示書11.2）。"
    )
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_pages() -> dict[str, int]:
    path = ROOT / "data" / "pages.json"
    topics = json.loads((ROOT / "data" / "topics_master.json").read_text(encoding="utf-8"))
    merged = {t["href"] for t in topics if t.get("action") == "merge"}
    pages = json.loads(path.read_text(encoding="utf-8-sig"))

    kept, changes = [], {"removed": 0, "to_none": 0, "to_guide": 0}
    for page in pages:
        if page["url"] in merged:
            changes["removed"] += 1
            continue
        if page["url"] in NO_CTA and page.get("cta_type") != "none":
            page["cta_type"] = "none"
            page["cta_strength"] = "none"
            page["cta_grade"] = "C"
            changes["to_none"] += 1
        elif page["url"] in GUIDE_CTA and page.get("cta_type") != "guide":
            page["cta_type"] = "guide"
            page["cta_strength"] = "weak"
            page["cta_grade"] = "B"
            changes["to_guide"] += 1
        kept.append(page)
    path.write_text(json.dumps(kept, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changes


def rename_official_event() -> int:
    """cta_official は営業CTAではなく公式ページへの遷移。指示書16.1の名前にそろえる。"""
    n = 0
    for p in sorted(ROOT.rglob("*.html")):
        if {".git", "_cache", "node_modules", "reports"} & set(p.relative_to(ROOT).parts):
            continue
        s = p.read_text(encoding="utf-8")
        if "cta_official" in s:
            p.write_text(s.replace('data-track-click="cta_official"',
                                   'data-track-click="official_link_click"'), encoding="utf-8")
            n += 1
    rules_path = ROOT / "data" / "cta-rules.json"
    s = rules_path.read_text(encoding="utf-8")
    rules_path.write_text(s, encoding="utf-8")
    return n


def main() -> None:
    update_rules()
    changes = update_pages()
    print("data/pages.json を更新")
    print(f"  統合により削除     : {changes['removed']} ページ")
    print(f"  営業CTAを外した    : {changes['to_none']} ページ")
    print(f"  ガイドを1段挟んだ  : {changes['to_guide']} ページ")
    print(f"公式リンクの計測名を official_link_click に統一: {rename_official_event()} ページ")


if __name__ == "__main__":
    main()
