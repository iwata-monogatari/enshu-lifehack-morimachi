# -*- coding: utf-8 -*-
"""公開後の実地検証（抜本改修指示書 18 フェーズ7）。

本番URLへ実際にHTTPリクエストを送り、以下を確認する。

  1. sitemap.xml の全URLが 200 を返すか
  2. 統合した旧URLが 301 で、正しい統合先へ飛ぶか
  3. 存在しないURLがカスタム404を返すか

ローカルのファイル存在チェックでは、配信側（Cloudflare）の挙動は検証できない。
公開のたびにこれを走らせる。

実行: python scripts/verify_published.py
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

SITE = "https://morimachi.enshu-lifehack.com"
UA = "morimachi-lifehack-deploy-check/1.0"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def fetch_once(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
    try:
        with OPENER.open(req, timeout=25) as res:
            return res.status, res.headers.get("Location", "")
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Location", "") if e.headers else ""
    except Exception as e:  # ネットワーク断など
        return 0, str(e)


def fetch(url: str) -> tuple[int, str]:
    """429（レート制限）は待って数回やり直す。

    まとめて叩くと Cloudflare 側で 429 が返り、実際の配信の問題と区別できなくなる。
    """
    delay = 2.0
    for attempt in range(5):
        status, loc = fetch_once(url)
        if status != 429:
            return status, loc
        time.sleep(delay)
        delay *= 2
    return 429, "レート制限が解除されませんでした"


def main() -> None:
    xml = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    urls = re.findall(r"<loc>([^<]+)</loc>", xml)
    topics = json.loads((ROOT / "data" / "topics_master.json").read_text(encoding="utf-8"))
    merges = {t["href"]: t["merge_target"] for t in topics if t.get("action") == "merge"}

    print(f"1. sitemap.xml の全URL（{len(urls)}件）が200を返すか")
    bad_pages = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        for url, (status, loc) in zip(urls, pool.map(fetch, urls)):
            if status != 200:
                bad_pages.append((url, status, loc))
    print(f"   200以外: {len(bad_pages)} 件")
    for url, status, loc in bad_pages[:20]:
        print(f"   x {status} {url} {loc}")

    print(f"\n2. 統合した旧URL（{len(merges)}件）が301で統合先へ飛ぶか")
    bad_redirects = []
    targets = [SITE + src for src in merges]
    with ThreadPoolExecutor(max_workers=3) as pool:
        for src, (status, loc) in zip(merges, pool.map(fetch, targets)):
            expected = merges[src]
            ok = status == 301 and loc.rstrip("/").endswith(expected.rstrip("/"))
            if not ok:
                bad_redirects.append((src, status, loc, expected))
    print(f"   期待どおりでない: {len(bad_redirects)} 件")
    for src, status, loc, expected in bad_redirects[:20]:
        print(f"   x {src} → {status} {loc}（期待: 301 {expected}）")

    print("\n3. 存在しないURLがカスタム404を返すか")
    status, _ = fetch(SITE + "/this-page-should-not-exist-20260804/")
    print(f"   {status}（404が正しい）")
    not_found_ok = status == 404

    print("\n" + "=" * 60)
    if bad_pages or bad_redirects or not not_found_ok:
        print("公開後の検証で不整合があります。上の一覧を確認してください。")
        sys.exit(1)
    print("公開後の検証: すべて期待どおりです。")


if __name__ == "__main__":
    main()
