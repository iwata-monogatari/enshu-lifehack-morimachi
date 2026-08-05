# -*- coding: utf-8 -*-
"""「市役所」テンプレート残りを森町の表現に直し、空セクションを消す（修正指示書 P0-2 / P0-3）。

森町は町なので庁舎は森町役場。しかし横展開元のテンプレートの
「市役所でできること／市役所以外で必要なこと」が残っていた。

一括置換はしない。他自治体を正式名称で指す「磐田市役所」等や、
一般名称の「市区町村役場」まで壊れるため、テンプレート由来の文言だけを対象にする。
見出しは記事の内容に合うよう、カテゴリごとに変える。

あわせて、中身が空の行動ステップを描画しない（見出しだけ出ている状態をなくす）。
冪等。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

CITY = json.loads((ROOT / "data" / "city.json").read_text(encoding="utf-8"))
OFFICE = CITY["municipality"]["office_formal"]

OLD_INTRO = "行動順と、市役所でできること／市役所以外で必要なことを分けています。"
NEW_INTRO = (f"行動する順番に沿って、{OFFICE}・公的窓口で行うことと、"
             "それ以外の場所で進めることを分けています。")

# カテゴリ → 「役場以外」のブロック見出し（記事の内容に合わせる）
OUTSIDE_LABEL = {
    "start-living": "役場以外で進めること",
    "moving-out": "役場以外で進めること",
    "living-soon": "役場以外で進めること",
    "work-life": "勤務先・金融機関などで進めること",
    "end-of-life": "葬儀・供養・相続で進めること",
    "housing": "所有者・家族で決めること",
    "parents-care": "家族・介護事業者と進めること",
    "health-medical": "医療機関・家庭で進めること",
    "emergency": "家庭で備えておくこと",
    "family-grow": "園・病院・家庭で進めること",
    "education": "学校・家庭で進めること",
    "play-out": "施設・現地で確認すること",
    "troubles-consult": "専門機関・民間で進めること",
}
DEFAULT_OUTSIDE = "役場以外で進めること"

# 個別に書かれていた本文（テンプレートではないので1件ずつ直す）
BODY_FIXES = {
    "市役所でできることと、市役所以外（医療機関・相談先）で必要":
        f"{OFFICE}でできることと、それ以外（医療機関・相談先）で必要",
    "市役所だけで認定が完結するわけではない点に注意してください":
        "役場の窓口だけで認定が完結するわけではない点に注意してください",
    "市役所以外：地域包括支援センターに相談する":
        "役場以外：地域包括支援センターに相談する",
}

STEP_BLOCK_RE = re.compile(
    r'<div class="step([^"]*)"><span class="label">([^<]*)</span><ul>(.*?)</ul></div>', re.S)
STEPS_WRAP_RE = re.compile(r'<div class="steps">(.*?)</div>(?=<h2)', re.S)


def category_of(path: Path) -> str:
    parts = path.relative_to(ROOT).parts
    return parts[1] if len(parts) > 2 and parts[0] == "life" else ""


def fix_html(path: Path) -> dict[str, int]:
    html = original = path.read_text(encoding="utf-8")
    counts = {"intro": 0, "label": 0, "empty_step": 0, "empty_steps_block": 0, "body": 0}
    cat = category_of(path)
    outside = OUTSIDE_LABEL.get(cat, DEFAULT_OUTSIDE)

    if OLD_INTRO in html:
        counts["intro"] = html.count(OLD_INTRO)
        html = html.replace(OLD_INTRO, NEW_INTRO)

    if "市役所以外で必要なこと" in html:
        counts["label"] = html.count("市役所以外で必要なこと")
        html = html.replace("市役所以外で必要なこと", outside)

    for before, after in BODY_FIXES.items():
        if before in html:
            counts["body"] += html.count(before)
            html = html.replace(before, after)

    # 中身が空のステップブロックは描画しない
    def drop_empty(m: re.Match) -> str:
        if not m.group(3).strip():
            counts["empty_step"] += 1
            return ""
        return m.group(0)

    html = STEP_BLOCK_RE.sub(drop_empty, html)

    # ステップが1つも残らなかったら、見出しとリード文ごと消す
    def drop_empty_wrap(m: re.Match) -> str:
        if not m.group(1).strip():
            counts["empty_steps_block"] += 1
            return ""
        return m.group(0)

    html = STEPS_WRAP_RE.sub(drop_empty_wrap, html)
    if counts["empty_steps_block"]:
        html = re.sub(
            r'<h2 class="sec"[^>]*>行動のステップ</h2><p class="lead">[^<]*</p>(?=<h2|<!--)',
            "", html)

    if html != original:
        path.write_text(html, encoding="utf-8")
    return counts


def fix_data() -> int:
    """生成元データにも同じ文言が入っているので直す（再生成で戻らないように）。"""
    n = 0
    for path in list((ROOT / "data").rglob("*.json")):
        text = path.read_text(encoding="utf-8")
        new = text.replace(OLD_INTRO, NEW_INTRO)
        for before, after in BODY_FIXES.items():
            new = new.replace(before, after)
        if new != text:
            path.write_text(new, encoding="utf-8")
            n += 1
    return n


def main() -> None:
    totals = {"intro": 0, "label": 0, "empty_step": 0, "empty_steps_block": 0, "body": 0}
    files = 0
    for path in sorted(ROOT.rglob("*.html")):
        if {".git", "_cache", "node_modules", "reports", "parts", "data"} & set(
                path.relative_to(ROOT).parts):
            continue
        counts = fix_html(path)
        if any(counts.values()):
            files += 1
        for k, v in counts.items():
            totals[k] += v

    print(f"HTML {files} ファイルを更新")
    print(f"  テンプレートのリード文 : {totals['intro']} 箇所")
    print(f"  「市役所以外」の見出し : {totals['label']} 箇所")
    print(f"  個別本文               : {totals['body']} 箇所")
    print(f"  空のステップを削除     : {totals['empty_step']} 箇所")
    print(f"  空の行動ステップ節ごと : {totals['empty_steps_block']} 箇所")
    print(f"生成元データ {fix_data()} ファイルを更新")

    remaining = []
    for path in sorted(ROOT.rglob("*.html")):
        if {".git", "_cache", "node_modules", "reports", "data"} & set(
                path.relative_to(ROOT).parts):
            continue
        for m in re.finditer(r".{0,12}市役所.{0,12}", path.read_text(encoding="utf-8")):
            # 他自治体を正式名称で指すものは残してよい
            if re.search(r"(磐田|袋井|掛川|浜松|菊川|御前崎|湖西)市役所", m.group(0)):
                continue
            remaining.append((str(path.relative_to(ROOT)), m.group(0)))
    if remaining:
        print(f"\n[!!] 「市役所」が残っています {len(remaining)} 件:")
        for f, t in remaining[:10]:
            print(f"   {f}: …{t}…")
    else:
        print("\nテンプレート由来の「市役所」は残っていません。")


if __name__ == "__main__":
    main()
