#!/usr/bin/env python3
"""data/pages.json(155ページのメタ台帳)を生成する。

02戦略編 1-3「155ページのCTA格付け」を機械可読な形にしたもの。
全ページに一律で売却CTAを貼ると「非公式ナビ」としての信頼が毀損するため、
文脈ごとに4段階(S/A/B/C)へ振り分ける。

  S級 strong … 売却・相続に直結する文脈        -> real_estate / both
  A級 middle … 住まいが動く文脈(転出・住宅全般) -> real_estate(middle) / care
  B級 weak   … 手続き系の大半                  -> official
  C級 none   … 子育て・学校・健康・遊び         -> CTAを描画しない

タイトル・description は各ページのHTMLから読み取るため、
ページを作り直したあとに再実行すれば台帳が追従する。

使い方: python scripts/build_pages_ledger.py
"""
import glob
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "pages.json")

# --- S級: 売却直結 -----------------------------------------------------------
S_REAL_ESTATE = {
    "/life/housing/sell-house/",
    "/life/housing/vacant-house/",
    "/life/housing/clean-parents-house/",
    "/life/housing/earthquake-demolition/",
    "/life/end-of-life/inheritance/",
    "/life/end-of-life/inherited-house/",
    "/life/end-of-life/inherited-vacant-house/",
    "/life/end-of-life/house-became-vacant/",
    "/life/end-of-life/property-tax-inheritance/",
    "/life/troubles-consult/vacant-house-consultation/",
    # 中山間地・森町固有の論点(農地/山林/税金困窮)
    "/life/troubles-consult/farmland/",
    "/life/troubles-consult/farmland/inheritance/",
    "/life/troubles-consult/farmland/sell-or-rent/",
    "/life/troubles-consult/farmland/conversion/",
    "/life/troubles-consult/farmland/change-use/",
    "/life/troubles-consult/farmland/noshin-exclusion/",
    "/life/troubles-consult/farmland/certificates/",
    "/life/troubles-consult/cannot-pay-tax/",
}

# S級: 介護×不動産(自社の独占領域)。住まい判断が絡む親のことページ。
S_BOTH = {
    "/life/parents-care/find-nursing-home/",
    "/life/parents-care/check-parents/",
    "/life/end-of-life/",
}

# --- A級: 住まいが動く文脈 ---------------------------------------------------
A_REAL_ESTATE = {
    "/life/housing/",
    "/life/housing/build-house/",
    "/life/housing/buy-house/",
    "/life/housing/property-tax/",
    "/life/housing/rent-house/",
    "/life/housing/municipal-housing/",
    "/life/housing/public-housing-consultation/",
    "/life/end-of-life/after-death-procedures/",
    "/life/end-of-life/bereavement/",
    "/life/end-of-life/bereavement-procedures/",
    "/life/end-of-life/grave-memorial/",
    "/life/end-of-life/pension-inheritance/",
}
A_CARE = {
    "/life/parents-care/",
    "/life/parents-care/care-started/",
    "/life/parents-care/long-term-care-insurance/",
    "/life/parents-care/dementia-consultation/",
    "/life/parents-care/community-support-center/",
    "/life/parents-care/care-certification-support-center/",
    "/life/parents-care/adult-guardianship/",
    "/life/parents-care/elderly-transportation/",
    "/life/troubles-consult/care-consultation/",
}

# --- C級: 営業色を出さない領域(カテゴリ単位) ---------------------------------
C_CATEGORIES = {"family-grow", "education", "health-medical", "play-out"}

# A級: 転出は「家が空く」タイミングなので中強度で拾う
A_CATEGORIES = {"moving-out"}

TITLE_RE = re.compile(r"<title>(.*?)\s*\|")
TITLE_ANY_RE = re.compile(r"<title>(.*?)</title>", re.S)
DESC_RE = re.compile(r'<meta name="description" content="(.*?)">')
VERIFIED_RE = re.compile(r"最終確認日：(\d{4}-\d{2}-\d{2})")


def classify(url, category):
    """(cta_type, cta_strength, grade) を返す。"""
    if url in S_REAL_ESTATE:
        return "real_estate", "strong", "S"
    if url in S_BOTH:
        return "both", "strong", "S"
    if url in A_REAL_ESTATE:
        return "real_estate", "middle", "A"
    if url in A_CARE:
        return "care", "middle", "A"
    if category in C_CATEGORIES:
        return "none", "none", "C"
    if category in A_CATEGORIES:
        return "real_estate", "middle", "A"
    return "official", "weak", "B"


def main():
    pages = []
    for filepath in sorted(glob.glob(os.path.join(ROOT, "life", "**", "index.html"), recursive=True)):
        rel = os.path.relpath(filepath, ROOT).replace(os.sep, "/")
        url = "/" + rel[: -len("index.html")]
        parts = url.strip("/").split("/")
        category = parts[1]
        slug = "/".join(parts[2:]) or "index"

        with open(filepath, encoding="utf-8") as f:
            src = f.read()

        m = TITLE_RE.search(src) or TITLE_ANY_RE.search(src)
        title = html.unescape(m.group(1).strip()) if m else slug
        dm = DESC_RE.search(src)
        desc = html.unescape(dm.group(1)) if dm else ""
        vm = VERIFIED_RE.search(src)

        cta_type, cta_strength, grade = classify(url, category)

        pages.append(
            {
                "id": ("%s-%s" % (category, slug.replace("/", "-"))),
                "url": url,
                "category": category,
                "slug": slug,
                "title": title,
                "description": desc,
                "cta_grade": grade,
                "cta_type": cta_type,
                "cta_strength": cta_strength,
                "last_checked": vm.group(1) if vm else None,
                "status": "published",
            }
        )

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)
        f.write("\n")

    from collections import Counter

    grades = Counter(p["cta_grade"] for p in pages)
    types = Counter(p["cta_type"] for p in pages)
    print("data/pages.json を生成: %d ページ" % len(pages))
    print("  格付け:", dict(sorted(grades.items())))
    print("  CTA種別:", dict(sorted(types.items())))

    unknown = [p["url"] for p in pages if p["cta_grade"] == "B" and p["category"] == "housing"]
    if unknown:
        print("  ※housing で未分類のままB級になったページ:", unknown)
    return 0


if __name__ == "__main__":
    sys.exit(main())
