#!/usr/bin/env python3
"""宗教法人名簿PDFから data/temples.json を生成する（01計画書②）。

出典A（一次）: 静岡県知事所轄宗教法人名簿（令和5年3月31日現在）
  _cache/shukyohojin/meibo4.pdf
  表形式「市町名 系統 包括団体 法人名 法人所在地」。森町の行は 84 行あり、
  うち仏教が 34 件。参照ページ・行番号を sources に記録する（計画書2-2の要求）。

出典B（検証）: 森町教育委員会「46 森町の寺院建築」
  曹洞宗27・日蓮宗2・真言宗2・天台宗2・浄土宗1＝34ヶ寺。
  PDFの宗派内訳と完全に一致したため、両者は相互に裏付けが取れている。

食い違いの扱い:
  町公式が名前を挙げている21ヶ寺のうち「陽向院」だけがPDFの34法人に含まれない。
  逆にPDFの14ヶ寺は町公式の記事（寺院建築の記録がある寺のみ扱う）に名前が出てこない。
  どちらも消さずに残し、陽向院は corporate_status="未確認" として記録する。
  計画書は「町公式を正とする」としているが、実際には両者は別の母集団を数えており、
  一方を捨てると情報が落ちるため、和集合＋根拠つきで持つ。

使い方: python scripts/build_temples.py
"""
import json
import os
import re
import sys
from collections import Counter

import pdfplumber

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(ROOT, "_cache", "shukyohojin", "meibo4.pdf")
OUT = os.path.join(ROOT, "data", "temples.json")
VERIFIED = "2026-08-04"

PDF_URL = "https://www.pref.shizuoka.jp/_res/projects/default_project/_page_/001/083/677/meibo4.pdf"
TOWN_URL = "https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/shakaikyoikuka/bunkashinkogakari/2/774.html"

# 旧字体・異体字 → 常用字体（照合用。表示は名簿の表記を優先し、別表記を aliases に持つ）
NORM = str.maketrans({"榮": "栄", "藏": "蔵", "龍": "竜", "萬": "万", "隨": "随", "嚴": "厳"})

# 町公式「46 森町の寺院建築」が名前を挙げている寺
TOWN_NAMED = [
    "栄泉寺", "宗源寺", "高雲寺", "福泉寺", "梅林院", "蔵雲院", "泉竜寺", "崇信寺",
    "自得院", "太慶寺", "万福寺", "陽向院", "蔵泉寺", "長月寺",
    "本立寺", "報恩寺", "金剛院", "遍照寺", "蓮華寺", "蓮増院", "安養院",
]

# 町公式で確認できた特記事項
NOTES = {
    "栄泉寺": {"history": "本堂は元禄9年（1696年）の建立で、森町の寺院建築では最も古い記録として町の資料に挙げられている。", "oldest": True},
    "金剛院": {"cultural_property": "山門が町指定文化財", "history": "山門が町の文化財に指定されている。"},
}


def normalize_addr(a):
    """全角数字を半角にし、表記を揃える。"""
    a = a.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    a = a.replace("番地の", "-").replace("番地", "").replace("番", "")
    return "静岡県" + a.strip()


def oaza_of(address, districts):
    body = re.sub(r"^.*?森町", "", address)
    for d in districts:
        for oaza in sorted(d["oaza"], key=len, reverse=True):
            if body.startswith(oaza):
                return d["district_id"], oaza
    return None, None


def sect_group(sect):
    """包括団体名から大まかな宗派にまとめる（真言宗御室派／智山派 → 真言宗）。"""
    for g in ("曹洞宗", "日蓮宗", "真言宗", "天台宗", "浄土宗", "臨済宗", "浄土真宗"):
        if sect.startswith(g):
            return g
    return sect


def slugify(name, idx):
    return "t%02d-%s" % (idx, re.sub(r"[^\w]", "", name))


def main():
    if not os.path.exists(PDF):
        print("宗教法人名簿PDFが %s にありません。" % os.path.relpath(PDF, ROOT))
        return 1

    with open(os.path.join(ROOT, "data", "shrine-districts.json"), encoding="utf-8-sig") as f:
        districts = json.load(f)["districts"]

    rows = []
    with pdfplumber.open(PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            for lno, line in enumerate(text.split("\n"), 1):
                s = line.strip()
                if s.startswith("森町 "):
                    rows.append((pno, lno, s))

    temples, unmapped = [], []
    idx = 0
    for pno, lno, line in rows:
        parts = line.split()
        if len(parts) < 5 or parts[1] != "仏教":
            continue
        idx += 1
        sect_full = parts[2]
        name = parts[3]
        addr_raw = " ".join(parts[4:])
        address = normalize_addr(addr_raw)
        district_id, oaza = oaza_of(address, districts)
        if not district_id:
            unmapped.append((name, address))

        canonical = name.translate(NORM)
        aliases = [canonical] if canonical != name else []
        note = NOTES.get(canonical, {})

        temples.append(
            {
                "temple_id": "morimachi-%04d" % idx,
                "slug": slugify(canonical, idx),
                "name": name,
                "aliases": aliases,
                "record_type": "temple",
                "status": "existing",
                "status_label": "現存",
                "corporate_status": "宗教法人",
                "sect": sect_group(sect_full),
                "sect_full": sect_full,
                "address": address,
                "district_id": district_id,
                "area": oaza,
                "in_town_article": canonical in TOWN_NAMED,
                "cultural_property": note.get("cultural_property"),
                "history_summary": note.get("history"),
                "oldest_building": note.get("oldest", False),
                "main_deity": "未確認",
                "manned_status": "未確認",
                "goshuin_status": "未確認",
                "visit_status": "未訪問",
                "detail_status": "公開情報調査済み",
                "lat": None,
                "lng": None,
                "last_verified_at": VERIFIED,
                "sources": [
                    {
                        "title": "静岡県知事所轄宗教法人名簿（令和5年3月31日現在）",
                        "type": "行政・公的資料",
                        "url": PDF_URL,
                        "note": "参照: p%d L%d（法人名・包括団体・所在地）" % (pno, lno),
                    }
                ],
            }
        )

    # 町公式に名前があるが法人名簿に無い寺（現時点では陽向院のみ）
    pdf_names = {t["name"].translate(NORM) for t in temples}
    for name in TOWN_NAMED:
        if name in pdf_names:
            continue
        idx += 1
        note = NOTES.get(name, {})
        temples.append(
            {
                "temple_id": "morimachi-%04d" % idx,
                "slug": slugify(name, idx),
                "name": name,
                "aliases": [],
                "record_type": "temple",
                "status": "existing",
                "status_label": "現存",
                "corporate_status": "未確認",
                "sect": "曹洞宗",
                "sect_full": "曹洞宗（町資料の分類による）",
                "address": "静岡県周智郡森町（詳細未確認）",
                "district_id": None,
                "area": None,
                "in_town_article": True,
                "cultural_property": note.get("cultural_property"),
                "history_summary": "森町教育委員会の資料に寺院建築として名前が挙がっているが、静岡県知事所轄宗教法人名簿（令和5年3月31日現在）には該当する法人が確認できなかった。",
                "oldest_building": False,
                "main_deity": "未確認",
                "manned_status": "未確認",
                "goshuin_status": "未確認",
                "visit_status": "未訪問",
                "detail_status": "要現地確認",
                "lat": None,
                "lng": None,
                "last_verified_at": VERIFIED,
                "sources": [
                    {
                        "title": "森町教育委員会「46 森町の寺院建築」",
                        "type": "行政・公的資料",
                        "url": TOWN_URL,
                        "note": "宗派内訳・寺院名を確認（%s）" % VERIFIED,
                    }
                ],
            }
        )

    payload = {
        "_note": "出典は静岡県知事所轄宗教法人名簿（参照ページ・行番号つき）と森町教育委員会の資料。",
        "_cross_check": "PDFの仏教法人は34件で、宗派内訳（曹洞宗27・日蓮宗2・真言宗2・天台宗2・浄土宗1）は森町公式の記載と完全に一致した。",
        "temples": temples,
    }
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("data/temples.json を生成: %d ヶ寺（法人34＋町資料のみ%d）" % (len(temples), len(temples) - 34))
    print("  宗派別:", dict(Counter(t["sect"] for t in temples)))
    print("  地区別:", dict(Counter(t["district_id"] for t in temples)))
    print("  町公式の記事に名前がある: %d" % sum(1 for t in temples if t["in_town_article"]))
    if unmapped:
        print("  ★地区が判定できなかった寺:", unmapped)
    return 0


if __name__ == "__main__":
    sys.exit(main())
