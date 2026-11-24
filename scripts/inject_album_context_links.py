"""Add editorially matched Mori photo links after the relevant paragraph."""
from __future__ import annotations

from collections import defaultdict
from html import escape, unescape
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "data/album-context-links.json"
ALBUM = "https://morimachialb.atawi.link"
MAIN = re.compile(r"<main\b[^>]*>.*?</main>", re.DOTALL)
HEADING = re.compile(r"<(h[23])\b[^>]*>(.*?)</\1>", re.DOTALL)
PARAGRAPH = re.compile(r"<p(?:\s[^>]*)?>.*?</p>", re.DOTALL)
MARKED = re.compile(r'<p data-album-context-links>.*?</p>', re.DOTALL)
LINK_TEXT = re.compile(r"\{([^{}]+)\}")
HREF = re.compile(r"""<a\b[^>]*\bhref=(?:"([^"]*)"|'([^']*)')""")
ROUTE = re.compile(r"/(?:[a-z0-9-]+/)+(?:#[a-z0-9-]+)?")


def plain(html: str) -> str:
    return " ".join(unescape(re.sub(r"<[^>]*>", "", html)).split())


def render_link(entry: dict[str, str], existing: set[str]) -> str:
    path = entry["target"]
    text = entry["text"]
    labels = list(LINK_TEXT.finditer(text))
    if not ROUTE.fullmatch(path) or len(labels) != 1:
        raise ValueError(f"Invalid photo link target or label: {path}")
    target = ALBUM + path
    if target in existing:
        raise ValueError(f"Duplicate photo link: {target}")
    existing.add(target)
    label = labels[0]
    return (
        escape(text[:label.start()])
        + f'<a href="{escape(target)}">{escape(label.group(1))}</a>'
        + escape(text[label.end():])
    )


def insert_links(html: str, entries: list[dict[str, str]]) -> str:
    match = MAIN.search(html)
    if not match:
        raise ValueError("No main content")
    main = MARKED.sub("", match.group())
    existing = {unescape(first or second) for first, second in HREF.findall(main)}
    by_heading = defaultdict(list)
    for entry in entries:
        by_heading[entry["heading"]].append(render_link(entry, existing))

    headings = list(HEADING.finditer(main))
    positions = {}
    for index, heading in enumerate(headings):
        title = plain(heading.group(2))
        if title not in by_heading:
            continue
        end = headings[index + 1].start() if index + 1 < len(headings) else len(main)
        paragraph = PARAGRAPH.search(main, heading.end(), end)
        if title in positions or paragraph is None:
            raise ValueError(f"Expected one heading followed by a paragraph: {title}")
        positions[title] = paragraph.end()
    missing = by_heading.keys() - positions.keys()
    if missing:
        raise ValueError("Missing heading(s): " + ", ".join(sorted(missing)))

    for title, position in sorted(positions.items(), key=lambda item: item[1], reverse=True):
        link_paragraph = '<p data-album-context-links>' + " ".join(by_heading[title]) + "</p>"
        main = main[:position] + link_paragraph + main[position:]
    return html[:match.start()] + main + html[match.end():]


def main() -> None:
    routes = json.loads(REGISTRY.read_text(encoding="utf-8"))
    updates = {}
    for route, entries in routes.items():
        path = ROOT / route.strip("/") / "index.html"
        old_html = path.read_bytes().decode("utf-8")
        try:
            new_html = insert_links(old_html, entries)
        except ValueError as error:
            raise ValueError(f"{route}: {error}") from error
        if old_html != new_html:
            updates[path] = new_html
    for path, html in updates.items():
        path.write_bytes(html.encode("utf-8"))
    print(f"Mori photo links: {sum(map(len, routes.values()))} on {len(routes)} pages")


if __name__ == "__main__":
    main()
