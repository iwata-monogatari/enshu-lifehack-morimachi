# -*- coding: utf-8 -*-
"""外部の公式リンクが生きているか実測する（修正指示書 11 / 29 test:links）。

森町は組織改編で課のURLが変わることがある（例: sangyoka → norinseisakuka）。
リンク切れを放置すると「公式で確認してください」と言いながら404に送ることになる。

実行: python scripts/check_official_links_live.py
出力: reports/broken-links.csv
"""
from __future__ import annotations

import csv
import re
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

UA = "morimachi-lifehack-linkcheck/1.0"
SKIP = {".git", "_cache", "node_modules", "reports", "parts", "scripts", "data"}
# 実測しない相手（bot遮断で403を返すが、実際は生きているもの）
SKIP_HOSTS = ("fujigaoka-service.co.jp", "fujigaoka-service.info")


def collect() -> dict[str, list[str]]:
    links: dict[str, list[str]] = defaultdict(list)
    for path in sorted(ROOT.rglob("*.html")):
        if SKIP & set(path.relative_to(ROOT).parts):
            continue
        url_path = "/" + path.relative_to(ROOT).as_posix()
        url_path = url_path[: -len("index.html")] if url_path.endswith("index.html") else url_path
        for m in re.finditer(r'href="(https?://[^"]+)"', path.read_text(encoding="utf-8")):
            u = m.group(1).split("#")[0]
            if any(h in u for h in SKIP_HOSTS):
                continue
            links[u].append(url_path)
    return links


def check(url: str) -> tuple[str, int, str]:
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
            with urllib.request.urlopen(req, timeout=25) as res:
                return url, res.status, res.geturl()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2 * (attempt + 1))
                continue
            return url, e.code, ""
        except Exception as e:
            return url, 0, str(e)[:60]
    return url, 429, ""


def main() -> None:
    links = collect()
    print(f"外部リンク {len(links)} 種を実測します…")
    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for url, status, final in pool.map(check, links):
            results.append((url, status, final, links[url]))

    broken = [r for r in results if r[1] >= 400 or r[1] == 0]
    redirected = [r for r in results
                  if r[1] == 200 and r[2] and r[2].split("#")[0].rstrip("/") != r[0].rstrip("/")]

    out = ROOT / "reports" / "broken-links.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["url", "status", "final_url", "掲載ページ数", "掲載ページ"])
        for url, status, final, pages in sorted(broken + redirected, key=lambda r: -r[1]):
            w.writerow([url, status, final, len(pages), " / ".join(sorted(set(pages))[:10])])

    print(f"\n切れているリンク: {len(broken)} 件")
    for url, status, final, pages in broken:
        print(f"  [{status}] {url}")
        for p in sorted(set(pages))[:6]:
            print(f"        ← {p}")
    print(f"\n転送されているリンク: {len(redirected)} 件")
    for url, status, final, pages in redirected[:15]:
        print(f"  {url}\n      → {final}（{len(pages)}ページ）")
    print(f"\n{out.relative_to(ROOT)} に出力しました")
    sys.exit(1 if broken else 0)


if __name__ == "__main__":
    main()
