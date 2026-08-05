# -*- coding: utf-8 -*-
"""戸籍届書の「印鑑が必要」表現を、押印任意の現行制度に合わせて直す（修正指示書 P0-1）。

根拠:
  法務省「戸籍届書の様式変更について」
  https://www.moj.go.jp/MINJI/minji04_00827.html
  「押印義務は廃止されますが、改正以降も、届出人の意向により、
    届書に任意に押印することは可能とされております。」（令和3年9月1日施行）

  一方、森町公式の死亡届ページ（更新日 2020-02-25）には「届出人の印鑑」の記載が残る。
  https://www.town.morimachi.shizuoka.jp/gyosei/machinososhiki/juminseikatsuka/juminkakari/2/2/2896.html
  自治体ページだけを根拠に「確認済み」としない、という方針でこの差を注記として明示する。

対象は戸籍の届書（死亡・出生・婚姻・離婚・転籍）のみ。
印鑑登録証明書、印鑑登録証、給水届など、印鑑が実際に必要な別手続きは変更しない。
そのため一括置換をせず、文言ごとの対応表で置き換える。冪等。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

# 修正前 → 修正後（戸籍届書に関するものだけを列挙する）
REPLACEMENTS = [
    (
        "死亡届は、病院などが発行する死亡診断書と一体になった用紙です。"
        "届出人の印鑑を用意し、住民生活課住民係へ提出します。",
        "死亡届は、病院などが発行する死亡診断書と一体になった用紙です。"
        "届出人が署名して、住民生活課住民係へ提出します。戸籍の届書への押印は任意です。"
        "後見人等が届け出る場合は、追加の書類が必要になることがあります。",
    ),
    (
        "死亡診断書と一体になった死亡届、届出人の印鑑が必要です。"
        "後見人等の場合は3か月以内の登記事項証明書または裁判の謄本も必要になります。",
        "死亡診断書と一体になった死亡届が必要です。届出人が署名し、押印は任意です。"
        "後見人・保佐人・補助人・任意後見人が届出人になる場合は、3か月以内の登記事項証明書"
        "または裁判の謄本も必要になります。個別の必要書類は住民生活課住民係へ確認してください。",
    ),
    (
        "死亡診断書と一体になった死亡届、届出人の印鑑"
        "（後見人等の場合は3か月以内の登記事項証明書等）",
        "死亡診断書と一体になった死亡届（届出人が署名。押印は任意）"
        "。後見人等の場合は3か月以内の登記事項証明書等",
    ),
    ("届出人の印鑑を持参する", "届出人を確認し、死亡届の署名欄を記入する（押印は任意）"),
    ("死亡届・届出人の印鑑もあわせて持参する",
     "死亡届に届出人が署名する（押印は任意）。後見人等であることを確認できる書類も用意する"),
    ("届出人になる人と印鑑を確認する", "届出人になる人と、死亡届の署名欄を確認する"),
]

# 森町公式ページと国の制度に差があることの注記（bereavement ページにだけ入れる）
NOTE_MARK = "<!-- SEAL-NOTE -->"
NOTE_HTML = (
    NOTE_MARK
    + '<p class="mini source-gap">※森町公式ページには「届出人の印鑑」との記載が残っていますが'
    + "（同ページの更新日は2020年2月25日）、法務省の制度改正により戸籍の届書への押印義務は"
    + "2021年9月1日に廃止され、押印は任意です。持参しても差し支えありません。"
    + "個別の取り扱いは住民生活課住民係（0538-85-6312）へご確認ください。</p>"
)

TARGET_FILES = [
    ROOT / "data" / "content" / "end-of-life.json",
    ROOT / "data" / "topics_master.json",
]


def apply_replacements(text: str) -> tuple[str, int]:
    n = 0
    for before, after in REPLACEMENTS:
        if before in text:
            n += text.count(before)
            text = text.replace(before, after)
    return text, n


def main() -> None:
    total = 0
    for path in TARGET_FILES:
        text = path.read_text(encoding="utf-8")
        new, n = apply_replacements(text)
        if n:
            path.write_text(new, encoding="utf-8")
        print(f"  {path.relative_to(ROOT)}: {n} 箇所")
        total += n

    html_total = 0
    for path in sorted((ROOT / "life").rglob("index.html")):
        html = path.read_text(encoding="utf-8")
        new, n = apply_replacements(html)
        if n:
            new = new.replace("届出人の印鑑", "届出人の署名")  # 取りこぼしの保険
            path.write_text(new, encoding="utf-8")
            html_total += n
            print(f"  {path.relative_to(ROOT)}: {n} 箇所")
    total += html_total

    # 公式との差の注記を、死亡届の公式窓口ブロック直前に入れる
    bereavement = ROOT / "life" / "end-of-life" / "bereavement" / "index.html"
    if bereavement.exists():
        html = bereavement.read_text(encoding="utf-8")
        if NOTE_MARK in html:
            html = re.sub(re.escape(NOTE_MARK) + r'<p class="mini source-gap">.*?</p>',
                          NOTE_HTML, html, flags=re.S)
        else:
            anchor = '<h2 class="sec" id="official">公式窓口・確認先</h2>'
            html = html.replace(anchor, NOTE_HTML + anchor, 1)
        bereavement.write_text(html, encoding="utf-8")
        print("  死亡届ページに、国制度と森町公式の差の注記を追加")

    print(f"\n戸籍届書の押印表現を {total} 箇所修正しました")

    # 検算：戸籍届書まわりに必須表現が残っていないか
    leftovers = []
    seal_required = re.compile(r"(印鑑が必要|印鑑を持参|印鑑を用意|届出人の印鑑)")
    for path in sorted((ROOT / "life").rglob("index.html")):
        html = path.read_text(encoding="utf-8")
        # 注記そのものは、森町公式の記載を引用しているので検算の対象外
        html = re.sub(re.escape(NOTE_MARK) + r'<p class="mini source-gap">.*?</p>',
                      "", html, flags=re.S)
        for m in seal_required.finditer(html):
            around = html[max(0, m.start() - 60):m.end() + 60]
            # 給水届など、戸籍届書ではない手続きは対象外
            if any(w in around for w in ("給水届", "印鑑登録", "印鑑証明")):
                continue
            leftovers.append((str(path.relative_to(ROOT)), around))
    if leftovers:
        print(f"[!!] 戸籍届書まわりに残っている必須表現 {len(leftovers)} 件:")
        for f, around in leftovers[:10]:
            print(f"   {f}: …{around}…")
    else:
        print("戸籍届書まわりに「印鑑が必要」表現は残っていません。")


if __name__ == "__main__":
    main()
