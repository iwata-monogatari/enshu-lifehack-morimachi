# -*- coding: utf-8 -*-
"""全URL台帳（抜本改修指示書 5.1）を生成する。

サイト内の全HTMLを走査し、指示書 5.1 の14列を持つ台帳を
reports/url-ledger.csv / data/url-ledger.json として出力する。

url / title / h1 / category / new_hub / intent / primary_keyword /
official_source / verified_at / action / merge_target / priority / owner / status

new_hub・intent・primary_keyword・action・merge_target・priority は
data/ledger-decisions.json（人が編集する判断ファイル）で上書きできる。
判断ファイルに無いURLは機械推定値のまま「未判定」として出力する。
"""
from __future__ import annotations

import csv
import json
import re
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://morimachi.enshu-lifehack.com"

# parts/ と data/ は公開URLではない断片・素材なので台帳の対象外
SKIP_DIRS = {".git", ".github", ".claude", "_cache", "node_modules",
             "reports", "scripts", "parts", "data"}

# 13カテゴリ → 6ハブの既定マッピング（指示書 4.1）
CATEGORY_TO_HUB = {
    "start-living": "procedures",
    "moving-out": "procedures",
    "work-life": "procedures",
    "family-grow": "family",
    "education": "family",
    "parents-care": "care",
    "housing": "property",
    "end-of-life": "property",
    "emergency": "trouble",
    "health-medical": "trouble",
    "troubles-consult": "trouble",
    "play-out": "enjoy",
    "living-soon": "procedures",
}

HUB_LABELS = {
    "procedures": "手続きしたい",
    "family": "子ども・家族",
    "care": "親・介護",
    "property": "家・土地",
    "trouble": "困った・緊急",
    "enjoy": "暮らしを楽しむ",
}

# 特定ページはカテゴリ既定とは別のハブへ寄せる（指示書 4.1 の内訳準拠）
PAGE_HUB_OVERRIDES = {
    "/life/living-soon/disaster-risk/": "trouble",
    "/life/work-life/job-change/": "procedures",
    "/life/troubles-consult/care-consultation/": "care",
    "/life/troubles-consult/vacant-house-consultation/": "property",
    "/life/troubles-consult/farmland/": "property",
    "/life/parents-care/elderly-transportation/": "care",
    "/life/health-medical/find-hospitals/": "trouble",
    "/life/living-soon/bus-license-return/": "care",
    "/life/education/study-facilities/": "enjoy",
}

TAG_RE = re.compile(r"<[^>]+>")


def text_of(html: str) -> str:
    return unescape(TAG_RE.sub("", html)).strip()


def first(pattern: str, html: str, group: int = 1) -> str:
    m = re.search(pattern, html, re.S | re.I)
    return m.group(group).strip() if m else ""


def extract(path: Path) -> dict:
    html = path.read_text(encoding="utf-8", errors="replace")
    rel = "/" + path.relative_to(ROOT).as_posix()
    url = rel[: -len("index.html")] if rel.endswith("index.html") else rel

    title = unescape(first(r"<title>(.*?)</title>", html))
    desc = unescape(first(r'<meta\s+name="description"\s+content="(.*?)"', html))
    h1 = text_of(first(r"<h1[^>]*>(.*?)</h1>", html))
    canonical = first(r'<link\s+rel="canonical"\s+href="(.*?)"', html)

    verified = first(r"最終確認日[：:]\s*(\d{4}-\d{2}-\d{2})", html)

    officials = re.findall(r'href="(https://www\.town\.morimachi\.shizuoka\.jp/[^"]*)"', html)
    tels = sorted(set(re.findall(r'href="tel:([0-9\-]+)"', html)))

    parts = [p for p in url.strip("/").split("/") if p]
    section = parts[0] if parts else "top"
    category = parts[1] if section == "life" and len(parts) >= 2 else section
    slug = parts[-1] if len(parts) > (2 if section == "life" else 1) else "index"

    hub = PAGE_HUB_OVERRIDES.get(url) or CATEGORY_TO_HUB.get(category, "")
    if section in {"shrine", "temple"}:
        hub = "enjoy"
    elif section in {"tools", "checklist"}:
        hub = "procedures"
    elif section in {"about", "terms", "blog"}:
        hub = ""
    elif section == "questions":
        hub = "procedures"

    return {
        "url": url,
        "title": title,
        "h1": h1,
        "description": desc,
        "section": section,
        "category": category,
        "slug": slug,
        "new_hub": hub,
        "new_hub_label": HUB_LABELS.get(hub, ""),
        "intent": "",
        "primary_keyword": "",
        "official_source": officials[0] if officials else "",
        "official_source_count": len(set(officials)),
        "tel": " / ".join(tels),
        "verified_at": verified,
        "canonical": canonical,
        "has_faq_jsonld": "FAQPage" in html,
        "has_breadcrumb_jsonld": "BreadcrumbList" in html,
        "exposes_raw_keys": bool(re.search(r"<b>(window|tel|note)</b>", html)),
        "bytes": len(html.encode("utf-8")),
        "action": "keep",
        "merge_target": "",
        "priority": "P2",
        "owner": "大石浩之",
        "status": "未着手",
    }


def collect() -> list[dict]:
    rows = []
    for path in sorted(ROOT.rglob("*.html")):
        parts = set(path.relative_to(ROOT).parts)
        if parts & SKIP_DIRS:
            continue
        if path.name == "404.html":
            continue
        rows.append(extract(path))
    return rows


# /life/ 以外のページの既定判断
SECTION_DEFAULTS = {
    "shrine": ("enjoy", "森町の神社を調べる", "森町 神社", "keep", "P2"),
    "temple": ("enjoy", "森町の寺院を調べる", "森町 寺院", "keep", "P2"),
    "tools": ("procedures", "手続きを道具で片づける", "森町 ごみ 検索", "keep", "P1"),
    "checklist": ("procedures", "状況別のやることを順番に確認する", "森町 やることリスト", "keep", "P1"),
    "blog": ("", "森町の暮らしの読み物を読む", "森町 ブログ", "keep", "P3"),
    "questions": ("procedures", "森町の疑問を質問から解決する", "森町 よくある質問", "keep", "P1"),
    "about": ("", "運営者と編集方針を確認する", "森町ライフハック 運営者", "keep", "P1"),
    "terms": ("", "利用条件と免責を確認する", "森町ライフハック 免責", "keep", "P3"),
    "top": ("", "困りごとから森町の窓口を探す", "森町 手続き", "rewrite", "P0"),
}


def apply_decisions(rows: list[dict]) -> list[dict]:
    """topics_master.json（/life/）と SECTION_DEFAULTS（それ以外）から判断を反映する。"""
    topics = json.loads((ROOT / "data" / "topics_master.json").read_text(encoding="utf-8"))
    by_url = {t["href"]: t for t in topics}
    question_path = ROOT / "data" / "questions.json"
    questions = json.loads(question_path.read_text(encoding="utf-8")) if question_path.is_file() else []
    questions_by_url = {q["href"]: q for q in questions}

    for row in rows:
        t = by_url.get(row["url"])
        if t:
            row["new_hub"] = t.get("hub", row["new_hub"])
            row["intent"] = t.get("intent", "")
            row["primary_keyword"] = t.get("primary_keyword", "")
            row["action"] = t.get("action", "keep")
            row["merge_target"] = t.get("merge_target", "")
            row["priority"] = t.get("priority", "P2")
            row["page_type"] = t.get("page_type", "")
            row["department"] = " / ".join(t.get("department", []))
            row["audience"] = " / ".join(t.get("audience", []))
            row["status"] = t.get("ledger_status", "未着手")
        elif row["url"] in questions_by_url:
            q = questions_by_url[row["url"]]
            row["new_hub"] = q.get("hub", row["new_hub"])
            row["intent"] = q.get("context", "")
            row["primary_keyword"] = q.get("keyword", "")
            row["action"] = "keep"
            row["priority"] = q.get("priority", "P1")
            row["page_type"] = "question"
            row["department"] = ""
            row["audience"] = " / ".join(q.get("audience", []))
            row["status"] = "作業中"
        else:
            hub, intent, kw, action, priority = SECTION_DEFAULTS.get(
                row["section"], ("", "", "", "keep", "P3"))
            row["new_hub"] = hub or row["new_hub"]
            row["intent"] = intent
            row["primary_keyword"] = kw
            row["action"] = action
            row["priority"] = priority
            row["page_type"] = "hub" if row["slug"] == "index" else "detail"
            row.setdefault("department", "")
            row.setdefault("audience", "")
            row["status"] = "作業中"
        row["new_hub_label"] = HUB_LABELS.get(row["new_hub"], "")
    return rows


COLUMNS = [
    "url", "title", "h1", "category", "new_hub", "new_hub_label", "intent",
    "primary_keyword", "official_source", "verified_at", "action",
    "merge_target", "priority", "owner", "status",
    "section", "slug", "page_type", "department", "audience", "description",
    "tel", "official_source_count", "canonical", "has_faq_jsonld",
    "has_breadcrumb_jsonld", "exposes_raw_keys", "bytes",
]


def main() -> None:
    rows = apply_decisions(collect())

    csv_path = ROOT / "reports" / "url-ledger.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in COLUMNS})

    json_path = ROOT / "data" / "url-ledger.json"
    json_path.write_text(
        json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    print(f"台帳を出力しました: {len(rows)} URL")
    print(f"  {csv_path.relative_to(ROOT)}")
    print(f"  {json_path.relative_to(ROOT)}")

    undecided = [r for r in rows if r["action"] == "keep" and not r["intent"]]
    print(f"  未判定（intent未記入）: {len(undecided)} 件")
    for key in ("action", "priority", "new_hub"):
        counts: dict[str, int] = {}
        for row in rows:
            counts[row[key]] = counts.get(row[key], 0) + 1
        print(f"  {key}: " + ", ".join(f"{k or '(なし)'}={v}" for k, v in sorted(counts.items())))


if __name__ == "__main__":
    main()
