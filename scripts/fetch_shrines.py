#!/usr/bin/env python3
"""静岡県神社庁から周智郡森町の神社情報を取得し、_cache/jinjacho/ に保存する。

01計画書 3-1 の技術注意を厳守する:
  - **https ではなく http のまま**アクセスする（https は http へ302リダイレクトし、
    HTTPSを強制するライブラリではリダイレクトループになる）
  - リダイレクトは追わない
  - 小規模サーバのため **1件あたり1.5秒間隔**
  - **1回のクロールで完結**。取得済みはキャッシュから読み、二度と取りに行かない
  - キャッシュは _cache/ に置き、.assetsignore で配信対象から除外する

使い方:
  python scripts/fetch_shrines.py            # 未取得のものだけ取得
  python scripts/fetch_shrines.py --list-only # 一覧ページだけ取り直す
"""
import argparse
import os
import re
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "_cache", "jinjacho")
BASE = "http://www.shizuoka-jinjacho.or.jp/shokai"
LIST_URL = BASE + "/search.php?mode=city&city=33"  # city=33 = 周智郡森町
INTERVAL = 1.5
UA = "Mozilla/5.0 (compatible; morimachi-lifehack/1.0; +https://morimachi.enshu-lifehack.com/)"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("リダイレクトされました(%s -> %s)。httpのまま取得すること。" % (code, newurl))


def opener():
    op = urllib.request.build_opener(NoRedirect)
    op.addheaders = [("User-Agent", UA)]
    return op


def fetch(url, cache_path, op):
    """キャッシュがあればそれを返す。無ければ1回だけ取得して保存する。"""
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            return f.read(), False
    with op.open(url, timeout=30) as r:
        body = r.read().decode("utf-8", errors="replace")
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    return body, True


def parse_list(html_text):
    out = []
    for row in re.findall(r"<tr>(.*?)</tr>", html_text, re.S):
        idm = re.search(r"jinja\.php\?id=(\d+)", row)
        if not idm:
            continue
        tds = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
        if len(tds) >= 3:
            out.append({"jinjacho_id": idm.group(1), "name": tds[0], "kana": tds[1], "address": tds[2]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list-only", action="store_true")
    args = ap.parse_args()

    op = opener()
    os.makedirs(CACHE, exist_ok=True)

    list_path = os.path.join(CACHE, "_list.html")
    if args.list_only and os.path.exists(list_path):
        os.remove(list_path)
    list_html, fetched = fetch(LIST_URL, list_path, op)
    print("一覧: %s" % ("取得" if fetched else "キャッシュ"))

    shrines = parse_list(list_html)
    print("一覧から %d 社を検出" % len(shrines))
    if args.list_only:
        return 0

    got = cached = 0
    for i, s in enumerate(shrines, 1):
        path = os.path.join(CACHE, "%s.html" % s["jinjacho_id"])
        url = "%s/jinja.php?id=%s" % (BASE, s["jinjacho_id"])
        try:
            _, fetched = fetch(url, path, op)
        except Exception as e:
            print("  [%d/%d] %s 取得失敗: %s" % (i, len(shrines), s["name"], e))
            continue
        if fetched:
            got += 1
            print("  [%d/%d] %s を取得" % (i, len(shrines), s["name"]))
            time.sleep(INTERVAL)  # 取得したときだけ待つ（キャッシュ読みでは待たない）
        else:
            cached += 1

    print("新規取得 %d 件 / キャッシュ利用 %d 件 / 合計 %d 件" % (got, cached, len(shrines)))
    print("キャッシュ: %s" % os.path.relpath(CACHE, ROOT).replace(os.sep, "/"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
