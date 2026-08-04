#!/usr/bin/env python3
"""_cache/jinjacho/ の取得結果から data/shrines.json を生成する。

出典は静岡県神社庁の神社紹介ページ（周智郡森町 city=33）。
**由緒本文は転載しない。**神社庁の御由緒は著作物なので、
本ファイルには事実項目（社名・鎮座地・御祭神・祭礼日・連絡先）だけを取り込み、
説明文はサイト側で自作する（01計画書5「法務・表記」）。

地区は data/shrine-districts.json の oaza リストで判定する。
地名の字面ではなく明治22年町村制の構成村に基づくため、
「向天方」「天宮」は天方ではなく森になる。

系統分類は01計画書3-3の7系統案を、実データに合わせて調整している（下の SYSTEMS 参照）。

使い方: python scripts/build_shrines.py
"""
import glob
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "_cache", "jinjacho")
OUT = os.path.join(ROOT, "data", "shrines.json")
VERIFIED = "2026-08-04"

FIELD_KEYS = (
    "神社名", "通称", "代表者", "各種御祈祷", "鎮座地", "問い合わせ先",
    "URL", "e-mail", "地図", "御祭神", "御神徳", "御由緒", "御祭典", "戻る", "静岡県神社庁",
)

# 01計画書3-3からの変更点:
#  - 「諏訪系」は森町の神社庁掲載39社に該当が無いため置かない（空の軸を作らない）
#  - 逆に「祇園・素盞嗚系」は4社あり、計画書の想定（該当が少ないので統合）と実態が違うため独立させた
#  - 山岳・修験系は秋葉街道の要衝という森町の性格上、独立の柱として残す
SYSTEMS = [
    {"id": "ichinomiya", "label": "一宮・国造系",
     "desc": "遠江国一宮・小國神社を核とする系統。森町の神社を語るうえでの中心。"},
    {"id": "hachiman", "label": "八幡系",
     "desc": "誉田別命（応神天皇）を祀る八幡神社群。森町では最も数が多い。"},
    {"id": "shinmei", "label": "神明・伊勢系",
     "desc": "天照大神を祀る神明社・神明宮の系統。"},
    {"id": "gion-susanoo", "label": "祇園・素盞嗚系",
     "desc": "素盞嗚命を祀る八坂・八雲・山名などの系統。山名神社の天王祭舞楽もこの流れ。"},
    {"id": "suijin", "label": "水神・水運系",
     "desc": "宗像三女神・市杵島姫命など水にかかわる神を祀る系統。太田川水系に沿って分布する。"},
    {"id": "sangaku", "label": "山岳・修験系",
     "desc": "御嶽・白山・金山など山の信仰にかかわる系統。秋葉街道沿いの中山間地に多い。"},
    {"id": "chiiki-koyu", "label": "地域固有・その他",
     "desc": "上のいずれにも収まらない、その土地に固有の社。"},
]

# 社名による判定（優先）。同名でも祭神で裏が取れるものはあとで補正する。
NAME_RULES = [
    (re.compile(r"小國|小国"), "ichinomiya"),
    (re.compile(r"八幡"), "hachiman"),
    (re.compile(r"神明"), "shinmei"),
    (re.compile(r"八坂|八阪|八雲|山名"), "gion-susanoo"),
    (re.compile(r"厳嶋|厳島|嚴島|天宮"), "suijin"),
    (re.compile(r"御嶽|白山|金山|秋葉|山住"), "sangaku"),
]
# 祭神による判定（社名で決まらなかったとき）
SAIJIN_RULES = [
    (re.compile(r"誉田別"), "hachiman"),
    (re.compile(r"天照"), "shinmei"),
    (re.compile(r"素盞嗚|須佐之男|素戔嗚"), "gion-susanoo"),
    (re.compile(r"市[許杵]嶋姫|田心姫|湍津姫|罔象女|水波"), "suijin"),
    (re.compile(r"大山[祇津]|伊[弉邪]那"), "sangaku"),
]

TAG_RE = re.compile(r"<[^>]+>")


def page_lines(raw):
    raw = re.sub(r"<script.*?</script>", "", raw, flags=re.S)
    raw = TAG_RE.sub("\n", raw)
    return [l.strip() for l in html.unescape(raw).split("\n") if l.strip()]


def field(lines, key):
    try:
        i = lines.index(key)
    except ValueError:
        return None
    out = []
    for l in lines[i + 1 :]:
        if l in FIELD_KEYS:
            break
        out.append(l)
    return " ".join(out).strip() or None


def parse_saijin(text):
    """御祭神の記述から神名だけを取り出す。読み仮名の括弧は落とす。"""
    if not text:
        return []
    t = re.sub(r"[（(][^）)]*[）)]", "", text)
    # 「〜のご祭神は「A」です。」のような文からも拾えるように鉤括弧を優先
    quoted = re.findall(r"「([^」]+)」", text)
    if quoted:
        t = "・".join(re.sub(r"[（(][^）)]*[）)]", "", q) for q in quoted)
    parts = re.split(r"[・、,／/]|\s+および\s+", t)
    out = []
    for p in parts:
        p = p.strip(" 　。")
        if 2 <= len(p) <= 20 and re.search(r"[命神尊姫彦大御]", p):
            out.append(p)
    seen, uniq = set(), []
    for p in out:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


def parse_sairei(text):
    """御祭典から「祭名＋日付」だけを取り出す。説明文は転載しない。"""
    if not text:
        return []
    out = []
    # 「例祭」は2文字なので {1,10}。ここを{2,}にすると最重要の例祭を取りこぼす。
    for m in re.finditer(r"([^\s　]{1,10}祭[^\s　]{0,4})[\s　]+((?:\d{1,2}月[\d第][^\s　]{0,12})|(?:毎月[^\s　]{0,12}))", text):
        name, date = m.group(1).strip(), m.group(2).strip()
        if not any(o["name"] == name for o in out):
            out.append({"name": name, "date": date})
    return out


def oaza_of(address, districts):
    body = re.sub(r"^.*?森町", "", address)
    for d in districts:
        for oaza in sorted(d["oaza"], key=len, reverse=True):
            if body.startswith(oaza):
                return d["district_id"], oaza
    return None, None


def slugify(jid, name):
    return "%s-%s" % (re.sub(r"[^a-z0-9]", "", "s"), jid) if not name else "s%s" % jid


def main():
    with open(os.path.join(ROOT, "data", "shrine-districts.json"), encoding="utf-8-sig") as f:
        districts = json.load(f)["districts"]

    list_path = os.path.join(CACHE, "_list.html")
    if not os.path.exists(list_path):
        print("先に scripts/fetch_shrines.py を実行してください。")
        return 1
    list_html = open(list_path, encoding="utf-8").read()
    listing = {}
    for row in re.findall(r"<tr>(.*?)</tr>", list_html, re.S):
        idm = re.search(r"jinja\.php\?id=(\d+)", row)
        if not idm:
            continue
        tds = [re.sub(r"\s+", " ", TAG_RE.sub("", c)).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
        if len(tds) >= 3:
            listing[idm.group(1)] = {"name": html.unescape(tds[0]), "kana": html.unescape(tds[1]), "address": html.unescape(tds[2])}

    shrines, unmapped = [], []
    for jid, base in sorted(listing.items(), key=lambda kv: kv[1]["kana"]):
        path = os.path.join(CACHE, "%s.html" % jid)
        detail = {}
        if os.path.exists(path):
            L = page_lines(open(path, encoding="utf-8").read())
            detail = {
                "tsusho": field(L, "通称"),
                "saijin_raw": field(L, "御祭神"),
                "saiten_raw": field(L, "御祭典"),
                "contact": field(L, "問い合わせ先"),
                "url": field(L, "URL"),
                "addr_full": field(L, "鎮座地"),
            }

        district_id, oaza = oaza_of(base["address"], districts)
        if not district_id:
            unmapped.append((base["name"], base["address"]))

        saijin = parse_saijin(detail.get("saijin_raw"))

        system = None
        for rx, sid in NAME_RULES:
            if rx.search(base["name"]):
                system = sid
                break
        if not system and saijin:
            joined = "・".join(saijin)
            for rx, sid in SAIJIN_RULES:
                if rx.search(joined):
                    system = sid
                    break
        basis = "社名" if any(rx.search(base["name"]) for rx, _ in NAME_RULES) else ("御祭神" if system else "未分類")
        if not system:
            system = "chiiki-koyu"

        tel = None
        if detail.get("contact"):
            m = re.search(r"(0\d{1,3}-\d{2,4}-\d{3,4})", detail["contact"])
            tel = m.group(1) if m else None

        url = detail.get("url")
        if url and not url.startswith("http"):
            url = None

        postal = None
        if detail.get("addr_full"):
            m = re.search(r"〒?(\d{3}-\d{4})", detail["addr_full"])
            postal = m.group(1) if m else None

        shrines.append(
            {
                "shrine_id": "morimachi-s%s" % jid,
                "jinjacho_id": jid,
                "slug": "s%s" % jid,
                "name": base["name"],
                "name_kana": base["kana"],
                "tsusho": detail.get("tsusho"),
                "district_id": district_id,
                "area": oaza,
                "system": system,
                "system_basis": basis,
                "saijin": saijin,
                "sairei": parse_sairei(detail.get("saiten_raw")),
                "postal_code": postal,
                "address": "静岡県" + base["address"],
                "tel": tel,
                "official_url": url,
                "lat": None,
                "lng": None,
                "status": "existing",
                "status_label": "現存",
                "detail_status": "公開情報調査済み",
                "visit_status": "未訪問",
                "last_verified_at": VERIFIED,
                "sources": [
                    {
                        "title": "静岡県神社庁 神社紹介 %s" % base["name"],
                        "type": "宗教団体公式",
                        "url": "http://www.shizuoka-jinjacho.or.jp/shokai/jinja.php?id=%s" % jid,
                        "note": "社名・鎮座地・御祭神・祭礼日を確認（%s）" % VERIFIED,
                    }
                ],
            }
        )

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"_note": "出典は静岡県神社庁。由緒本文は転載していない（事実項目のみ）。", "shrines": shrines}, f, ensure_ascii=False, indent=2)
        f.write("\n")

    from collections import Counter

    print("data/shrines.json を生成: %d 社" % len(shrines))
    print("  地区別:", dict(Counter(s["district_id"] for s in shrines)))
    print("  系統別:", dict(Counter(s["system"] for s in shrines)))
    print("  御祭神あり: %d / 祭礼日あり: %d / 電話あり: %d / 公式サイトあり: %d"
          % (sum(1 for s in shrines if s["saijin"]), sum(1 for s in shrines if s["sairei"]),
             sum(1 for s in shrines if s["tel"]), sum(1 for s in shrines if s["official_url"])))
    if unmapped:
        print("  ★地区が判定できなかった社 %d:" % len(unmapped), unmapped)
    return 0


if __name__ == "__main__":
    sys.exit(main())
