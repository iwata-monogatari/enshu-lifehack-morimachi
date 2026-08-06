#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""森町サイトの「自然検索だけで1日100PV」を本人確認する。

Search Console のクリック数を自然検索流入の主指標とし、独自解析の
人間PVをボット混入・計測欠落の照合値として並べる。2つの数値は足さない。

実行例:
  python scripts/report_organic_100pv.py \
    --date 2026-08-30 --gsc-csv "C:/Downloads/Dates.csv" --domain-confirmed
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

SUMMARY_URL = (
    "https://fujigaoka-analytics-worker.hiroyukio0122.workers.dev/api/summary"
)
SITE_ID = "morimachi-lifehack"
SITE_HOST = "morimachi.enshu-lifehack.com"
TARGET = 100
JST = ZoneInfo("Asia/Tokyo")

DATE_HEADERS = ("日付", "Date")
CLICK_HEADERS = ("クリック数", "Clicks")


@dataclass(frozen=True)
class GscResult:
    clicks: int | None
    matched_date: bool


def parse_int(value: object) -> int:
    text = str(value or "0").replace(",", "").strip()
    return int(float(text))


def parse_date(value: str) -> date | None:
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    return None


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    last_error: UnicodeDecodeError | None = None
    for encoding in ("utf-8-sig", "cp932"):
        try:
            with path.open(encoding=encoding, newline="") as handle:
                return list(csv.DictReader(handle))
        except UnicodeDecodeError as exc:
            last_error = exc
    assert last_error is not None
    raise last_error


def gsc_clicks_from_csv(path: Path, target_date: date) -> GscResult:
    rows = read_csv_rows(path)
    if not rows:
        return GscResult(None, False)
    headers = set(rows[0])
    date_header = next((h for h in DATE_HEADERS if h in headers), None)
    click_header = next((h for h in CLICK_HEADERS if h in headers), None)
    if not date_header or not click_header:
        raise ValueError(
            "Search Consoleの『日付』表CSVではありません。"
            "日付/Date と クリック数/Clicks の列が必要です。"
        )
    for row in rows:
        if parse_date(row.get(date_header, "")) == target_date:
            return GscResult(parse_int(row.get(click_header)), True)
    return GscResult(None, False)


def fetch_summary(url: str = SUMMARY_URL) -> dict:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "morimachi-organic-100pv-report/1.0"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def human_pv_for_date(summary: dict, target_date: date) -> int | None:
    site = next((row for row in summary.get("sites", []) if row.get("id") == SITE_ID), None)
    if not site:
        raise ValueError(f"アクセス解析に site_id={SITE_ID} がありません。")

    date_fields = (
        ("today", "today_human_pv"),
        ("yesterday", "yesterday_human_pv"),
        ("day_before_yesterday", "day_before_human_pv"),
    )
    for date_key, pv_key in date_fields:
        raw_date = summary.get(date_key)
        if raw_date and parse_date(str(raw_date)) == target_date:
            return parse_int(site.get(pv_key))
    return None


def status_for(
    clicks: int | None,
    human_pv: int | None,
    domain_confirmed: bool,
) -> tuple[str, str]:
    missing = []
    if clicks is None:
        missing.append("Search Consoleクリック数")
    if human_pv is None:
        missing.append("人間PV")
    if not domain_confirmed:
        missing.append("森町ホスト絞り込みの確認")
    if missing:
        return "判定不能", "不足: " + "、".join(missing)
    if clicks >= TARGET and human_pv >= TARGET:
        return "達成", "自然検索クリックと人間PVがともに100以上です。"
    gaps = []
    if clicks < TARGET:
        gaps.append(f"自然検索クリックがあと{TARGET - clicks}")
    if human_pv < TARGET:
        gaps.append(f"人間PVがあと{TARGET - human_pv}")
    return "未達", "、".join(gaps) + "必要です。"


def render_report(
    target_date: date,
    clicks: int | None,
    human_pv: int | None,
    domain_confirmed: bool,
) -> str:
    status, reason = status_for(clicks, human_pv, domain_confirmed)
    click_text = "取得できず" if clicks is None else f"{clicks:,}"
    human_text = "取得できず" if human_pv is None else f"{human_pv:,}"
    filter_text = "確認済み" if domain_confirmed else "未確認"
    generated = datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")
    return f"""# 自然検索100PV 本人確認レポート

- 対象日: {target_date.isoformat()}
- 判定: **{status}**
- Google Search Console 自然検索クリック: **{click_text}**
- 独自解析 人間PV: **{human_text}**
- Search ConsoleのURLフィルタ `{SITE_HOST}`: **{filter_text}**
- 目標: 両方100以上（足し算はしない）

{reason}

## 判定の意味

Search Consoleのクリック数を自然検索入口の主指標にします。人間PVは、ボットを除いた
実アクセスが同程度あるかを確かめる照合値です。LINE、SNS、広告、関連サイト、内部閲覧は
Search Consoleの自然検索クリックには入りません。

生成日時: {generated}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="対象日 (YYYY-MM-DD)")
    parser.add_argument("--gsc-csv", type=Path, help="Search Consoleの日付CSV")
    parser.add_argument(
        "--domain-confirmed",
        action="store_true",
        help=f"Search Consoleを {SITE_HOST} で絞ったことを本人確認済みにする",
    )
    parser.add_argument("--human-pv", type=int, help="3日より前を確認する場合の保存済み人間PV")
    parser.add_argument("--summary-json", type=Path, help="テスト・保存済み解析JSON")
    parser.add_argument("--output", type=Path, help="Markdownレポートの保存先")
    args = parser.parse_args()

    try:
        target_date = date.fromisoformat(args.date)
        clicks = None
        if args.gsc_csv:
            gsc = gsc_clicks_from_csv(args.gsc_csv, target_date)
            clicks = gsc.clicks

        if args.human_pv is not None:
            human_pv = args.human_pv
        else:
            summary = (
                json.loads(args.summary_json.read_text(encoding="utf-8"))
                if args.summary_json
                else fetch_summary()
            )
            human_pv = human_pv_for_date(summary, target_date)

        report = render_report(
            target_date,
            clicks,
            human_pv,
            args.domain_confirmed,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[エラー] {exc}", file=sys.stderr)
        return 2

    print(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8", newline="\n")
        print(f"保存: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
