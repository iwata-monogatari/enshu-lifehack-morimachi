# -*- coding: utf-8 -*-
"""「最終確認日：確認中」の表示を、根拠のある表現に置き換える（指示書 10.1 / 10.2 / 21）。

1ページ内に確認日の表示が複数ある（要点欄と末尾）。表記が食い違わないよう、
ページ単位で1つの答えに揃える。

  そのページに記録された確認日がある  … その日付に揃える
  カテゴリ一覧ページで日付が無い      … 配下ページの確認日の範囲を示す
  それ以外で日付が無い                … 記録が無いことをそのまま書く

台帳に無い日付を書き足すことはしない（指示書21「出典のない期限を掲載しない」）。
確認日が記録されれば、このスクリプトが自動的に日付表示へ戻す。冪等。
"""
from __future__ import annotations

import re
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

# 「確認中」と、このスクリプトが過去に書いた表現の両方を置換対象にする（冪等のため）
PENDING_RE = re.compile(
    r"最終確認日[：:]\s*(?:確認中"
    r"|未記録（[^）]*）"
    r"|\d{4}-\d{2}-\d{2}(?:〜\d{4}-\d{2}-\d{2})?（このページから案内している各ページの確認日）)")
DATE_RE = re.compile(r"最終確認日[：:]\s*(\d{4}-\d{2}-\d{2})(?!〜?\d*（このページ)")

UNRECORDED = (
    "最終確認日：未記録（出典は確認済みですが、確認日の記録がありません。"
    "公式ページで最新の内容をご確認ください）"
)

DISPLAY_RE = re.compile(
    r"最終確認日[：:]\s*(?:確認中|未記録（[^）]*）|"
    r"\d{4}-\d{2}-\d{2}(?:〜\d{4}-\d{2}-\d{2})?"
    r"(?:（このページから案内している各ページの確認日）)?)")
SYNC_HUBS = {
    "/life/start-living/", "/life/living-soon/", "/life/end-of-life/",
    "/life/health-medical/", "/life/parents-care/",
}


def recorded_date(html: str) -> str | None:
    """このスクリプトが書いた表現を除いた、素の確認日を取り出す。"""
    bare = PENDING_RE.sub("", html)
    m = DATE_RE.search(bare)
    return m.group(1) if m else None


def child_dates(category_dir: Path) -> list[str]:
    dates = []
    for path in category_dir.rglob("index.html"):
        if path.parent == category_dir:
            continue
        d = recorded_date(path.read_text(encoding="utf-8"))
        if d:
            dates.append(d)
    return sorted(set(dates))


def main() -> None:
    # 台帳にページ自身の確認日がある場合は、それを画面上の全表示へ同期する。
    # 重要ページの実質更新日・構造化データ・sitemapと食い違わせない。
    topics = json.loads((ROOT / "data" / "topics_master.json").read_text(encoding="utf-8"))
    synced = 0
    for topic in topics:
        href = topic.get("href", "")
        date = topic.get("verified_date", "")
        if (not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date or "")
                or not href.startswith("/life/")
                or (not topic.get("content_updated") and href not in SYNC_HUBS)):
            continue
        path = ROOT / href.strip("/") / "index.html"
        if not path.is_file():
            continue
        html = path.read_text(encoding="utf-8")
        updated = DISPLAY_RE.sub(f"最終確認日：{date}", html)
        if updated != html:
            path.write_text(updated, encoding="utf-8")
            synced += 1

    to_date = to_span = to_unrecorded = 0
    for path in sorted((ROOT / "life").rglob("index.html")):
        html = path.read_text(encoding="utf-8")
        if not PENDING_RE.search(html):
            continue

        own = recorded_date(html)
        if own:
            replacement = f"最終確認日：{own}"
            to_date += 1
        else:
            is_category_top = (path.parent.parent.name == "life"
                               or path.parent.name == "farmland")
            dates = child_dates(path.parent) if is_category_top else []
            if dates:
                span = dates[0] if len(dates) == 1 else f"{dates[0]}〜{dates[-1]}"
                replacement = f"最終確認日：{span}（このページから案内している各ページの確認日）"
                to_span += 1
            else:
                replacement = UNRECORDED
                to_unrecorded += 1
        path.write_text(PENDING_RE.sub(replacement, html), encoding="utf-8")

    print(f"台帳の確認日に同期          : {synced} 件")
    print(f"ページ自身の確認日に揃えた  : {to_date} 件")
    print(f"配下ページの確認日の範囲    : {to_span} 件")
    print(f"「未記録」と明示            : {to_unrecorded} 件")

    # 検算：1ページ内で表記が食い違っていないか
    conflicts = []
    for path in sorted((ROOT / "life").rglob("index.html")):
        html = path.read_text(encoding="utf-8")
        shown = {v.strip() for v in re.findall(r"最終確認日[：:]\s*([^<／]{0,60})", html)}
        if len(shown) > 1:
            conflicts.append(str(path.relative_to(ROOT)))
    if conflicts:
        print(f"[!!] 表記が食い違うページ {len(conflicts)} 件: {conflicts[:5]}")
    else:
        print("1ページ内の確認日表記の食い違いはありません。")


if __name__ == "__main__":
    main()
