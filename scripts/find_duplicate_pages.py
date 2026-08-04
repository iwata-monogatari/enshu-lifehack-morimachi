# -*- coding: utf-8 -*-
"""類似ページ群を抽出する（抜本改修指示書 5.2）。

判定条件（2つ以上該当で統合候補）
  1. 本文の類似度が高い（2-gram Jaccard）
  2. 公式出典URLが一致する
  3. 電話番号が一致する
  4. 見出し（h2/h3）の重なりが大きい
"""
from __future__ import annotations

import json
import re
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

DROP_BLOCKS = [
    (r"<!-- PART:footer:START -->", r"<!-- PART:footer:END -->"),
    (r"<!-- PART:header:START -->", r"<!-- PART:header:END -->"),
    (r"<!-- PART:disclaimer:START -->", r"<!-- PART:disclaimer:END -->"),
    (r"<!-- SHARE-BOX:START -->", r"<!-- SHARE-BOX:END -->"),
    (r"<!-- CTA-BLOCK:START -->", r"<!-- CTA-BLOCK:END -->"),
    (r"<head", r"</head>"),
]


def body_text(html: str) -> str:
    for start, end in DROP_BLOCKS:
        html = re.sub(start + r".*?" + end, " ", html, flags=re.S)
    html = re.sub(r"<script.*?</script>", " ", html, flags=re.S)
    html = re.sub(r"<style.*?</style>", " ", html, flags=re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", "", unescape(html))


def bigrams(text: str) -> set[str]:
    return {text[i:i + 2] for i in range(len(text) - 1)}


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def load() -> list[dict]:
    pages = []
    for path in sorted((ROOT / "life").rglob("index.html")):
        html = path.read_text(encoding="utf-8", errors="replace")
        url = "/" + path.relative_to(ROOT).as_posix()[: -len("index.html")]
        text = body_text(html)
        heads = {
            re.sub(r"<[^>]+>", "", h).strip()
            for h in re.findall(r"<h[23][^>]*>(.*?)</h[23]>", html, re.S)
        }
        pages.append({
            "url": url,
            "grams": bigrams(text),
            "len": len(text),
            "officials": set(re.findall(
                r'href="(https://www\.town\.morimachi\.shizuoka\.jp/[^"]*)"', html)),
            "tels": set(re.findall(r'href="tel:([0-9\-]+)"', html)),
            "heads": heads,
        })
    return pages


def main() -> None:
    pages = load()
    print(f"対象: {len(pages)} ページ\n")
    results = []
    for i, a in enumerate(pages):
        for b in pages[i + 1:]:
            sim = jaccard(a["grams"], b["grams"])
            off = jaccard(a["officials"], b["officials"])
            tel = jaccard(a["tels"], b["tels"])
            head = jaccard(a["heads"], b["heads"])
            hits = sum([sim >= 0.45, off >= 0.5, tel >= 0.5, head >= 0.4])
            if hits >= 2 and sim >= 0.30:
                results.append((sim, off, tel, head, hits, a["url"], b["url"]))
    results.sort(reverse=True)
    print(f"統合候補ペア: {len(results)} 件（本文類似 / 出典一致 / 電話一致 / 見出し一致）\n")
    for sim, off, tel, head, hits, ua, ub in results:
        print(f"[{hits}] 本文{sim:.2f} 出典{off:.2f} 電話{tel:.2f} 見出し{head:.2f}")
        print(f"      {ua}")
        print(f"      {ub}")
    (ROOT / "reports" / "duplicate-candidates.json").write_text(
        json.dumps(
            [{"similarity": round(s, 3), "official": round(o, 3), "tel": round(t, 3),
              "heading": round(h, 3), "hits": n, "a": ua, "b": ub}
             for s, o, t, h, n, ua, ub in results],
            ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
