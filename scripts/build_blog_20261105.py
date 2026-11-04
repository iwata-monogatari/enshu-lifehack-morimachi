"""Assemble the four November 5 articles after editorial review."""
import json
import re
from pathlib import Path

from build_blog_20261104 import ROOT, page, save

DATE = "2026-11-05"
BACKLINKS = {
    "hunt": ("森林クラウド", "山の位置が分かったら、秋の見回りの前に服装も確かめられます。"),
    "land": ("用途地域", "広い土地を取得する予定なら、都市計画区域の内外で変わる届出の面積基準も確認できます。"),
    "water": ("田", "貸し借りの記録と一緒に、水路の共同作業の連絡先を控えておく方法もあります。"),
    "tea": ("ブランド", "茶の産地を説明するときは、茶草場農法の認定地域の範囲も確かめられます。"),
}


def main():
    ledger_file = ROOT / "data/blog-posts.json"
    ledger = json.loads(ledger_file.read_text(encoding="utf8"))
    for key, (term, lead) in BACKLINKS.items():
        p = json.loads((ROOT / f"data/blog-20261105-{key}.json").read_text(encoding="utf8"))
        sources = dict(enumerate(p["sources"]))
        p["sources"] = list(sources)
        folder = ROOT / "blog" / p["slug"]
        folder.mkdir(exist_ok=True)
        page(p, folder, sources, date=DATE)
        reverse = ROOT / "blog" / p["reverse"] / "index.html"
        old = reverse.read_text(encoding="utf8")
        href = f'/blog/{p["slug"]}/'
        if href not in old:
            start = old.index('<div class="post-editorial-body">')
            end = old.index('<div class="action-grid">', start)
            paragraphs = list(re.finditer(r"<p(?:\s[^>]*)?>.*?</p>", old[start:end], re.S))
            anchor = next(m for m in paragraphs if term in m.group() and "<a " not in m.group())
            pos = start + anchor.end()
            new = old[:pos] + f'<p>{lead}<a href="{href}">{p["title"]}</a>をご覧ください。</p>' + old[pos:]
            reverse.write_text(re.sub(r'("dateModified"\s*:\s*")[^"]+', r'\g<1>'+DATE, new), encoding="utf8")
        next(row for row in ledger["posts"] if row["slug"] == p["reverse"])["modified"] = DATE
        row = {k:p[k] for k in ("slug", "title", "description", "query")}
        row.update(date=DATE, modified=DATE, axis="thu", home_description=p["description"], cta="official",
                   primary_source="・".join(item[0] for item in sources.values())+"（2026年11月5日確認）",
                   cover_alt=p["cover_description"], search_index=True)
        old_row = next((r for r in ledger["posts"] if r["slug"] == p["slug"]), None)
        if old_row is None:
            ledger["posts"].append(row)
        else:
            old_row.update(row)
    save(ledger_file, ledger)


if __name__ == "__main__":
    main()
