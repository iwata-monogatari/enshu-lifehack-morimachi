#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第3期公開ゲート。60候補の状態と公開正規URLの品質を検査する。"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def visible_chars(html):
    text = re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", "", html, flags=re.S)
    return len(re.sub(r"\s+", "", text))

def main():
    rows = json.loads((ROOT / "data/seo-phase3-decisions.json").read_text(encoding="utf-8"))
    pub = json.loads((ROOT / "data/seo-phase3-publication.json").read_text(encoding="utf-8"))
    failures = []
    if len(rows) != 60 or {r["id"] for r in rows} != set(range(1, 61)):
        failures.append("第3期台帳がNo.1〜60の60件ではありません")
    pub_urls = {p["url"] for p in pub}
    hold_urls = {r["final_url"] for r in rows if r["decision"] == "HOLD"}
    if pub_urls & hold_urls:
        failures.append("確認待ちURLが第3期公開台帳へ混入しています")
    for p in pub:
        url = p["url"]
        path = ROOT / url.strip("/") / "index.html"
        if not path.is_file():
            failures.append(f"HTMLなし {url}")
            continue
        html = path.read_text(encoding="utf-8")
        chars = visible_chars(html)
        checks = {
            "6000文字": chars >= 6000,
            "H1一つ": html.count("<h1") == 1,
            "H2五つ以上": html.count("<h2") >= 5,
            "画像三点以上": html.count("<img ") >= 3,
            "画像レスポンシブ": html.count('style="width:100%;height:auto"') >= 3 if p.get("generated_in_phase3") else True,
            "canonical一つ": html.count('rel="canonical"') == 1,
            "description一つ": html.count('name="description"') == 1,
            "OGP一式": all(html.count(x) == 1 for x in ['property="og:title"', 'property="og:description"', 'property="og:url"', 'property="og:image"']),
            "構造化データ": ("WebPage" in html or "Article" in html) and "BreadcrumbList" in html,
            "内部リンク五つ": len(re.findall(r'href="/(?!/)', html)) >= 5,
            "一次情報二つ": html.count('target="_blank"') >= 2,
            "禁止語なし": "政" + "策" not in html,
        }
        bad = [k for k, ok in checks.items() if not ok]
        if bad:
            failures.append(f"{url} {chars}字: {', '.join(bad)}")
    if failures:
        raise SystemExit("第3期監査失敗\n- " + "\n- ".join(failures))
    print(f"第3期監査: 60候補確定 / 公開正規URL {len(pub)}件すべて6000文字以上・構造合格")

if __name__ == "__main__":
    main()
