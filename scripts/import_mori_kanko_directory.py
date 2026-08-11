#!/usr/bin/env python3
"""Build a factual directory from the Mori Town Tourism Association site.

Only the site's structured directory fields are imported. Narrative copy,
captions, images, and promotional descriptions are intentionally ignored.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen


BASE_URL = "https://www.mori-kanko.jp/"
CATEGORY_NAMES = {
    1: "お土産",
    2: "グルメ",
    3: "神社・仏閣",
    4: "体験・レジャー",
    5: "買い物・特産品",
    6: "宿泊・休憩処",
    7: "温泉",
    8: "自然・景観",
    9: "公園",
    10: "その他",
}
CATEGORY_URL = BASE_URL + "tourist/search/index/?template_id=9&category={category}"
USER_AGENT = "MorimachiInfoCatalog/1.0 (+https://morimachi.enshu-lifehack.com/)"
DETAIL_LINK_RE = re.compile(r'href=["\']([^"\']*?/touristdetail/[^"\'#?]+\.html)["\']', re.I)
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")
HTTP_URL_RE = re.compile(r"https?://[^\s<>\"'（）]+", re.I)


def fetch(url: str, retries: int = 3) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "ja"})
    for attempt in range(retries):
        try:
            with urlopen(request, timeout=30) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset, errors="replace")
        except (HTTPError, URLError, TimeoutError) as exc:
            if attempt + 1 == retries:
                raise RuntimeError(f"fetch failed: {url}: {exc}") from exc
            time.sleep(1.0 * (attempt + 1))
    raise AssertionError("unreachable")


def text_content(fragment: str) -> str:
    fragment = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    fragment = TAG_RE.sub("", fragment)
    fragment = html.unescape(fragment).replace("\u3000", " ").replace("\xa0", " ")
    lines = [SPACE_RE.sub(" ", line).strip() for line in fragment.splitlines()]
    return "\n".join(line for line in lines if line)


def canonical_detail_url(value: str) -> str:
    absolute = urljoin(BASE_URL, html.unescape(value))
    split = urlsplit(absolute)
    return urlunsplit(("https", "www.mori-kanko.jp", split.path, "", ""))


def category_page_url(category: int, page_no: int) -> str:
    base = CATEGORY_URL.format(category=category)
    if page_no == 1:
        return base
    return f"{BASE_URL}tourist/search/index/?page_no={page_no}&template_id=9&category={category}"


def discover_details(category: int, max_pages: int = 50) -> set[str]:
    found: set[str] = set()
    for page_no in range(1, max_pages + 1):
        page = fetch(category_page_url(category, page_no))
        links = {canonical_detail_url(item) for item in DETAIL_LINK_RE.findall(page)}
        new_links = links - found
        if not links or (page_no > 1 and not new_links):
            break
        found.update(links)
        # A next-page control is absent on the last page. This avoids one extra request.
        if not re.search(rf"submit\({page_no + 1}\)", page):
            break
    return found


def first_class_text(page: str, class_name: str) -> str:
    match = re.search(
        rf'<(?:span|div)[^>]*class=["\'][^"\']*\b{re.escape(class_name)}\b[^"\']*["\'][^>]*>(.*?)</(?:span|div)>',
        page,
        flags=re.I | re.S,
    )
    return text_content(match.group(1)) if match else ""


def detail_fields(page: str) -> dict[str, str]:
    block = re.search(r'<dl[^>]*class=["\'][^"\']*touristDetailData[^"\']*["\'][^>]*>(.*?)</dl>', page, re.I | re.S)
    if not block:
        return {}
    values: dict[str, str] = {}
    for label_html, value_html in re.findall(r"<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>", block.group(1), re.I | re.S):
        label = text_content(label_html)
        value = text_content(value_html)
        if label and value:
            values[label] = value
    return values


def pick(values: dict[str, str], *labels: str) -> str:
    for label in labels:
        if values.get(label):
            return values[label]
    return ""


def extract_href_for_label(page: str, labels: tuple[str, ...]) -> str:
    block = re.search(r'<dl[^>]*class=["\'][^"\']*touristDetailData[^"\']*["\'][^>]*>(.*?)</dl>', page, re.I | re.S)
    if not block:
        return ""
    for label_html, value_html in re.findall(r"<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>", block.group(1), re.I | re.S):
        if text_content(label_html) not in labels:
            continue
        match = re.search(r'href=["\']([^"\']+)["\']', value_html, re.I)
        if match:
            raw_url = html.unescape(match.group(1)).strip()
            url_match = HTTP_URL_RE.match(raw_url)
            if url_match:
                return url_match.group(0)
    return ""


def extract_geocode(page: str) -> dict[str, float] | None:
    match = re.search(r"var\s+geocode\s*=\s*['\"]\s*(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s*['\"]", page)
    if not match:
        match = re.search(r"c_geocode=(-?\d+(?:\.\d+)?)%?20(-?\d+(?:\.\d+)?)", page)
    if not match:
        return None
    return {"lat": float(match.group(1)), "lon": float(match.group(2))}


def stable_id(url: str) -> str:
    """Derive a stable, readable ID from the canonical detail-page path."""
    stem = Path(urlsplit(url).path).stem.lower()
    slug = re.sub(r"[^a-z0-9._-]+", "-", stem).strip("-.")
    if not slug:
        raise ValueError(f"cannot derive stable id from {url}")
    return f"mori-kanko-{slug}"


def parse_detail(url: str, categories: list[str], checked_at: str) -> dict[str, object]:
    page = fetch(url)
    values = detail_fields(page)
    return {
        "id": stable_id(url),
        "name": first_class_text(page, "el_title"),
        "reading": first_class_text(page, "el_phonetic"),
        "categories": categories,
        "address": pick(values, "住所", "所在地"),
        "phone": pick(values, "電話番号", "電話", "TEL"),
        "hours": pick(values, "営業時間", "開館時間", "利用時間"),
        "closed": pick(values, "定休日", "休館日", "休業日"),
        "parking": pick(values, "駐車場", "駐車台数"),
        "fee": pick(values, "料金", "入館料", "拝観料", "利用料金"),
        "inquiry": pick(values, "お問い合わせ", "問い合わせ", "問合せ先", "連絡先"),
        "official_homepage": extract_href_for_label(page, ("HP", "ホームページ", "公式サイト", "WEBサイト")),
        "geocode": extract_geocode(page),
        "source_url": url,
        "checked_at": checked_at,
    }


def build_directory(checked_at: str) -> dict[str, object]:
    memberships: dict[str, set[int]] = {}
    category_pages = []
    for category, name in CATEGORY_NAMES.items():
        url = CATEGORY_URL.format(category=category)
        category_pages.append({"id": category, "name": name, "url": url})
        urls = discover_details(category)
        print(f"category {category:02d} {name}: {len(urls)}", file=sys.stderr)
        for detail_url in urls:
            memberships.setdefault(detail_url, set()).add(category)

    records = []
    total = len(memberships)
    for index, url in enumerate(sorted(memberships), start=1):
        categories = [CATEGORY_NAMES[item] for item in sorted(memberships[url])]
        print(f"detail {index}/{total}: {url}", file=sys.stderr)
        records.append(parse_detail(url, categories, checked_at))

    records.sort(key=lambda item: (str(item["name"]), str(item["source_url"])))
    return {
        "schema_version": 1,
        "source": {
            "name": "静岡県森町観光協会",
            "directory_url": BASE_URL + "tourist/list/",
            "note": "定型の事実項目のみを収録し、紹介文・キャッチコピーは収録しない。",
        },
        "checked_at": checked_at,
        "category_pages": category_pages,
        "records": records,
    }


def main() -> int:
    default_output = Path(__file__).resolve().parents[1] / "data" / "mori-directory.json"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=default_output)
    parser.add_argument("--checked-at", default=date.today().isoformat())
    args = parser.parse_args()
    payload = build_directory(args.checked_at)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(payload['records'])} records to {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
