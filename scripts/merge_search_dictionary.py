# -*- coding: utf-8 -*-
"""統合元ページの検索辞書を統合先へ引き継ぐ（抜本改修指示書 5.4 / 9.1）。

ページを301にしても、そのページで使われていた言葉（同義語・日常語・困りごとの文章）で
検索する人は残る。統合元の synonyms / needs / audience / department を統合先へ移し、
「ごみの日」「要介護認定」のような言葉で統合先にたどり着けるようにする。

冪等：重複は入れない。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")


def extend(target: dict, source: dict, key: str) -> int:
    existing = target.setdefault(key, [])
    added = 0
    for value in source.get(key) or []:
        if value not in existing:
            existing.append(value)
            added += 1
    return added


def main() -> None:
    path = ROOT / "data" / "topics_master.json"
    topics = json.loads(path.read_text(encoding="utf-8"))
    by_href = {t["href"]: t for t in topics}

    moved = 0
    pairs = 0
    for topic in topics:
        if topic.get("action") != "merge":
            continue
        target = by_href.get(topic.get("merge_target", ""))
        if not target:
            print(f"  [!!] 統合先が台帳に無い: {topic['href']}")
            continue
        pairs += 1
        n = sum(extend(target, topic, key)
                for key in ("synonyms", "needs", "audience", "department"))
        # 統合元の主検索語も、統合先の別名として拾えるようにする
        kw = topic.get("primary_keyword")
        if kw and kw not in target.get("synonyms", []):
            # 「森町 ごみ 収集日」のような検索語は語ごとに分けて入れる
            for word in kw.replace("森町", "").split():
                if word and word not in target["synonyms"]:
                    target["synonyms"].append(word)
                    n += 1
        moved += n
        if n:
            print(f"  {topic['href']} → {target['href']}：辞書 +{n}")

    path.write_text(json.dumps(topics, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"統合 {pairs} 組から辞書エントリ {moved} 件を引き継ぎました")


if __name__ == "__main__":
    main()
