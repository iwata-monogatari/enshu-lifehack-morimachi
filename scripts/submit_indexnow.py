#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sitemap.xml の全URLを IndexNow へ一括送信する。

760ページ公開・クロールも来ているのに検索稼働が0のままだったため、
インデックス段階の未着手レバーとして導入した（2026-08-28）。
IndexNow は Bing / Yandex / Naver 系に届く仕組みで、Google には効かない。

前提: 鍵ファイル https://morimachi.enshu-lifehack.com/<KEY>.txt が
      本番で200を返していること。公開前に送ると422で弾かれる。

実行: python scripts/submit_indexnow.py
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

HOST = "morimachi.enshu-lifehack.com"
SITE = f"https://{HOST}"
KEY = "66e43655159534f53551a1a114dc1a07"
KEY_LOCATION = f"{SITE}/{KEY}.txt"
ENDPOINT = "https://api.indexnow.org/indexnow"

# IndexNow の1リクエスト上限は10,000URL。現状760件なので分割しない。
MAX_URLS = 10000


def sitemap_urls() -> list[str]:
    xml = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    return re.findall(r"<loc>([^<]+)</loc>", xml)


def main() -> int:
    urls = sitemap_urls()
    if not urls:
        print("sitemap.xml から <loc> を取得できませんでした")
        return 1
    if len(urls) > MAX_URLS:
        print(f"URLが{len(urls)}件で1リクエスト上限{MAX_URLS}件を超えています")
        return 1

    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": urls,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "morimachi-lifehack-indexnow/1.0",
        },
    )

    print(f"送信URL件数: {len(urls)}")
    print(f"keyLocation: {KEY_LOCATION}")
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            status = res.status
            text = res.read().decode("utf-8", "replace").strip()
    except urllib.error.HTTPError as e:
        status = e.code
        text = e.read().decode("utf-8", "replace").strip()
    except urllib.error.URLError as e:
        print(f"送信に失敗しました: {e.reason}")
        return 1

    print(f"HTTPステータス: {status}")
    if text:
        print(f"レスポンス本文: {text}")
    # 200=受理、202=鍵の検証待ちで受理。どちらも成功扱い。
    return 0 if status in (200, 202) else 1


if __name__ == "__main__":
    raise SystemExit(main())
