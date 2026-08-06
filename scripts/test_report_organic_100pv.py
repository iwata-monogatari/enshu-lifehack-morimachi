#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from report_organic_100pv import (
    gsc_clicks_from_csv,
    human_pv_for_date,
    status_for,
)


class OrganicReportTest(unittest.TestCase):
    def test_both_values_are_required(self):
        self.assertEqual(status_for(100, 100, True)[0], "達成")
        self.assertEqual(status_for(99, 100, True)[0], "未達")
        self.assertEqual(status_for(100, 99, True)[0], "未達")
        self.assertEqual(status_for(100, 100, False)[0], "判定不能")

    def test_selects_morimachi_human_pv_by_date(self):
        summary = {
            "today": "2026-08-30",
            "yesterday": "2026-08-29",
            "day_before_yesterday": "2026-08-28",
            "sites": [
                {"id": "other", "today_human_pv": 999},
                {
                    "id": "morimachi-lifehack",
                    "today_human_pv": 101,
                    "yesterday_human_pv": 88,
                    "day_before_human_pv": 77,
                },
            ],
        }
        self.assertEqual(human_pv_for_date(summary, date(2026, 8, 30)), 101)
        self.assertEqual(human_pv_for_date(summary, date(2026, 8, 29)), 88)
        self.assertIsNone(human_pv_for_date(summary, date(2026, 8, 27)))

    def test_reads_japanese_search_console_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "日付.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["日付", "クリック数", "表示回数"])
                writer.writeheader()
                writer.writerow({"日付": "2026-08-30", "クリック数": "103", "表示回数": "3,100"})
            result = gsc_clicks_from_csv(path, date(2026, 8, 30))
            self.assertEqual(result.clicks, 103)
            self.assertTrue(result.matched_date)


if __name__ == "__main__":
    unittest.main()
