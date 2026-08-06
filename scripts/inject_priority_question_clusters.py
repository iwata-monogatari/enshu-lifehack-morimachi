# -*- coding: utf-8 -*-
"""重要11ガイドに関連質問を集約し、話題の中心ページを明確にする。"""
from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
START = "<!-- PRIORITY-QUESTIONS:START -->"
END = "<!-- PRIORITY-QUESTIONS:END -->"


def esc(value: object) -> str:
    return escape(str(value or ""), quote=True)


def select_questions(item: dict, rows: list[dict], index: int) -> list[dict]:
    pool = [row for row in rows if row.get("hub") in item["question_hubs"]]
    exact = [row for row in pool if row.get("parent_href") == item["href"]]
    others = [row for row in pool if row.get("parent_href") != item["href"]]
    if others:
        offset = (index * 5) % len(others)
        others = others[offset:] + others[:offset]
    return (exact + others)[:5]


def main() -> None:
    priority = json.loads(
        (ROOT / "data" / "search-priority-pages.json").read_text(encoding="utf-8"))
    questions = json.loads((ROOT / "data" / "questions.json").read_text(encoding="utf-8"))
    for index, item in enumerate(priority):
        path = ROOT / item["href"].strip("/") / "index.html"
        html = path.read_text(encoding="utf-8")
        html = re.sub(re.escape(START) + r".*?" + re.escape(END), "", html, flags=re.S)
        rows = select_questions(item, questions, index)
        links = "".join(
            f'<li><a href="{esc(row["href"])}" data-track-click="priority_question">'
            f'{esc(row["question"])}</a></li>' for row in rows)
        block = (
            f'{START}<section class="priority-question-cluster" '
            f'aria-labelledby="priority-questions-{index}">'
            f'<h2 class="sec" id="priority-questions-{index}">このテーマのよくある質問</h2>'
            f'<ul>{links}</ul><p><a href="/questions/">森町の100の質問をすべて見る</a></p>'
            f'</section>{END}'
        )
        if "/assets/search-tools.css" not in html:
            html = html.replace(
                "</head>",
                '<link rel="stylesheet" href="/assets/search-tools.css?v=20260806a"></head>', 1)
        anchor = "<!-- QUESTION-LINK:START -->" if "<!-- QUESTION-LINK:START -->" in html else "<!-- CTA-BLOCK:START -->"
        if anchor not in html:
            raise RuntimeError(f"挿入位置が見つかりません: {item['href']}")
        html = html.replace(anchor, block + anchor, 1)
        path.write_text(html, encoding="utf-8")
        print(f"関連質問{len(rows)}件を集約: {item['href']}")


if __name__ == "__main__":
    main()
