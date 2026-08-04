#!/usr/bin/env python3
"""data/channels.json を導出する（チャネルバッジ／インスタントヘッダーの元データ）。

磐田版は categories.json に検証済みの channels / conclusion を持っているが、森町版は持たない。
そこで既に検証済みの2つの出典だけから機械的に導出する。**新規の推測はしない。**

  出典A: data/topics_master.json の facts（window 142件 / tel 138件。verified_date つき）
  出典B: 各ページ本文の <div class="official"> 内 <b>window</b>／<b>tel</b> 表記

重要な設計判断（01計画書§5「未確認項目は推測せず未確認と明記」への対応）:
  オンライン申請の可否は、森町の手元資料では155ページ中8ページ分しか根拠が取れない。
  「online が無い＝オンライン不可」と解釈されると147ページで誤情報になるため、
  **陽性の根拠があるチャネルだけを記録し、"不可" は一切記録しない。**
  表示側も「確認できた手続き方法」という肯定形の見出しにして、
  非表示のチャネルについては何も主張しない。

使い方: python scripts/derive_channel_fields.py
"""
import glob
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "channels.json")

OFFICIAL_RE = re.compile(r'<div class="official">(.*?)</div>', re.S)
WINDOW_RE = re.compile(r"<b>window</b>[：:]\s*(.*?)</p>", re.S)
TEL_RE = re.compile(r"<b>tel</b>[：:]\s*(.*?)</p>", re.S)
TEL_LINK_RE = re.compile(r'href="tel:([0-9\-]+)"')
VERIFIED_RE = re.compile(r"最終確認日：(\d{4}-\d{2}-\d{2})")
TAG_RE = re.compile(r"<[^>]+>")

# オンライン／コンビニは陽性語句がある場合のみ。誤検出を避けるため語句を絞る。
ONLINE_RE = re.compile(r"電子申請|マイナポータル|ぴったりサービス|オンライン申請|オンラインで申請|インターネットで申請")
KONBINI_RE = re.compile(r"コンビニ交付|コンビニでの交付|コンビニで取得")


def clean(s):
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub("", s))).strip()


def main():
    with open(os.path.join(ROOT, "data", "topics_master.json"), encoding="utf-8-sig") as f:
        topics = {t["href"]: t for t in json.load(f)}

    records = []
    stats = {"counter": 0, "phone": 0, "online": 0, "konbini": 0, "no_channel": 0}

    for filepath in sorted(glob.glob(os.path.join(ROOT, "life", "**", "index.html"), recursive=True)):
        rel = os.path.relpath(filepath, ROOT).replace(os.sep, "/")
        url = "/" + rel[: -len("index.html")]
        src = open(filepath, encoding="utf-8").read()

        topic = topics.get(url, {})
        facts = topic.get("facts") or {}

        official = OFFICIAL_RE.search(src)
        official_html = official.group(1) if official else ""

        # 窓口: 台帳を優先、無ければ本文
        window = facts.get("window")
        if not window:
            m = WINDOW_RE.search(official_html)
            window = clean(m.group(1)) if m else None

        # 電話: 台帳を優先、無ければ本文の表記→tel:リンク
        tel = facts.get("tel")
        if not tel:
            m = TEL_RE.search(official_html)
            if m:
                tel = clean(m.group(1))
            else:
                links = TEL_LINK_RE.findall(src)
                tel = links[0] if links else None

        channels = []
        if window:
            channels.append("counter")
            stats["counter"] += 1
        if tel:
            channels.append("phone")
            stats["phone"] += 1
        if ONLINE_RE.search(src):
            channels.append("online")
            stats["online"] += 1
        if KONBINI_RE.search(src):
            channels.append("konbini")
            stats["konbini"] += 1
        if not channels:
            stats["no_channel"] += 1

        vm = VERIFIED_RE.search(src)

        records.append(
            {
                "url": url,
                "channels": channels,
                "window": window,
                "tel": tel,
                # 期限・所要時間は明記がある場合のみ。無ければ null のまま（推測しない）
                "deadline": facts.get("deadline") or facts.get("kigen") or None,
                "hours": facts.get("hours") or facts.get("jikan") or None,
                "last_checked": vm.group(1) if vm else topic.get("verified_date"),
                "source": "topics_master.facts" if facts.get("window") or facts.get("tel") else "page_html",
            }
        )

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("data/channels.json を生成: %d ページ" % len(records))
    print("  窓口の根拠あり : %d" % stats["counter"])
    print("  電話の根拠あり : %d" % stats["phone"])
    print("  オンラインの根拠あり: %d" % stats["online"])
    print("  コンビニの根拠あり  : %d" % stats["konbini"])
    print("  チャネル根拠なし    : %d" % stats["no_channel"])
    print("  ※根拠が無いチャネルは『不可』ではなく『未確認』として扱う（表示しない）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
