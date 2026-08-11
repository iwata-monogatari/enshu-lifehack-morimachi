#!/usr/bin/env python3
"""Audit the Mori Town directory data and its generated page."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from html import escape, unescape
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


DATA_RELATIVE_PATH = Path("data/mori-directory.json")
SUPPLEMENT_RELATIVE_PATH = Path("data/mori-directory-supplement.json")
EXTRA_DATA_RELATIVE_PATHS = (
    Path("data/mori-core-facts.json"),
    Path("data/mori-web-discovery.json"),
    Path("data/acty-mori-directory.json"),
)
HTML_CANDIDATES = (
    Path("directory/index.html"),
    Path("mori-directory/index.html"),
    Path("guide/mori-directory/index.html"),
)
FORBIDDEN_KEYS = frozenset({"description", "catch", "copy", "source_text"})
REQUIRED_RECORD_FIELDS = ("name", "categories", "checked_at")
REQUIRED_SOURCE_HOSTS = (
    "ja.wikipedia.org",
    "travel.yahoo.co.jp",
    "www.jalan.net",
    "public-connect.jp",
    "www.town.morimachi.shizuoka.jp",
    "actymori.co.jp",
    "www.mori-kanko.jp",
    "tsplus.asahi.co.jp",
    "iju.pref.shizuoka.jp",
)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HTTP_URL_RE = re.compile(r"^https?://[^\s<>\"'（）]+$", re.I)
SCRIPT_SRC_RE = re.compile(
    r"<script\b[^>]*\bsrc\s*=\s*([\"'])(.*?)\1",
    flags=re.IGNORECASE | re.DOTALL,
)


class Audit:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.legacy_http_urls: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to the parent of scripts/)",
    )
    parser.add_argument(
        "--data",
        type=Path,
        help="directory JSON path, relative to root unless absolute",
    )
    parser.add_argument(
        "--html",
        type=Path,
        help="generated HTML path, relative to root unless absolute",
    )
    parser.add_argument(
        "--supplement",
        type=Path,
        help="optional supplement JSON path, relative to root unless absolute",
    )
    return parser.parse_args()


def under_root(root: Path, requested: Path | None, default: Path) -> Path:
    path = requested if requested is not None else default
    return path if path.is_absolute() else root / path


def display_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def load_json(path: Path, audit: Audit) -> Any | None:
    if not path.is_file():
        audit.error(f"missing JSON: {path}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        audit.error(f"JSON is not UTF-8: {path}: {exc}")
    except json.JSONDecodeError as exc:
        audit.error(f"invalid JSON: {path}:{exc.lineno}:{exc.colno}: {exc.msg}")
    return None


def valid_https_url(value: Any) -> bool:
    if not isinstance(value, str) or not HTTP_URL_RE.fullmatch(value.strip()):
        return False
    parts = urlsplit(value.strip())
    return parts.scheme.lower() == "https" and bool(parts.netloc) and not parts.username


def find_forbidden_keys(value: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text.casefold() in FORBIDDEN_KEYS:
                found.append(child_path)
            found.extend(find_forbidden_keys(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(find_forbidden_keys(child, f"{path}[{index}]"))
    return found


def extract_records(payload: Any, audit: Audit) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        audit.error("JSON root must be an object")
        return []
    records = payload.get("records")
    if not isinstance(records, list):
        audit.error("$.records must be an array")
        return []
    result: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            audit.error(f"$.records[{index}] must be an object")
            continue
        result.append(record)
    if not records:
        audit.error("$.records must not be empty")
    return result


def audit_structure(
    payload: Any,
    records: list[dict[str, Any]],
    audit: Audit,
    *,
    label: str,
    require_category_pages: bool,
) -> None:
    if not isinstance(payload, dict):
        return
    for path in find_forbidden_keys(payload):
        audit.error(f"narrative field is forbidden: {path}")

    category_pages = payload.get("category_pages")
    if require_category_pages and (not isinstance(category_pages, list) or not category_pages):
        audit.error(f"{label}: $.category_pages must be a non-empty array")
    elif category_pages is not None:
        if not isinstance(category_pages, list):
            audit.error(f"{label}: $.category_pages must be an array")
            category_pages = []
        category_page_ids: set[str | int] = set()
        for index, category in enumerate(category_pages):
            prefix = f"{label}: $.category_pages[{index}]"
            if not isinstance(category, dict):
                audit.error(f"{prefix} must be an object")
                continue
            if not isinstance(category.get("id"), (str, int)) or isinstance(category.get("id"), bool):
                audit.error(f"{prefix}.id must be a string or integer")
            for key in ("name", "url"):
                if not isinstance(category.get(key), str) or not category[key].strip():
                    audit.error(f"{prefix}.{key} must be a non-empty string")
            category_id = category.get("id")
            if isinstance(category_id, (str, int)) and not isinstance(category_id, bool):
                if category_id in category_page_ids:
                    audit.error(f"duplicate category id: {category_id}")
                category_page_ids.add(category_id)
            url = category.get("url")
            if url is not None and not valid_https_url(url):
                audit.error(f"{prefix}.url must be HTTPS: {url!r}")

    for index, record in enumerate(records):
        prefix = f"{label}: $.records[{index}]"
        for key in REQUIRED_RECORD_FIELDS:
            if key not in record:
                audit.error(f"{prefix}.{key} is required")

        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id.strip():
            audit.error(f"{prefix}.id must be a non-empty string")

        name = record.get("name")
        if not isinstance(name, str) or not name.strip():
            audit.error(f"{prefix}.name must be a non-empty string")

        categories = record.get("categories")
        if (
            not isinstance(categories, list)
            or not categories
            or any(not isinstance(item, str) or not item.strip() for item in categories)
        ):
            audit.error(f"{prefix}.categories must be a non-empty string array")
        elif len(categories) != len(set(categories)):
            audit.error(f"{prefix}.categories contains duplicates")

        source_url = record.get("source_url")
        source_urls = record.get("source_urls")
        if not valid_https_url(source_url):
            if (
                not isinstance(source_urls, list)
                or not source_urls
                or any(not valid_https_url(item) for item in source_urls)
            ):
                audit.error(f"{prefix} needs source_url or non-empty HTTPS source_urls")

        checked_at = record.get("checked_at")
        if not isinstance(checked_at, str) or not DATE_RE.fullmatch(checked_at):
            audit.error(f"{prefix}.checked_at must use YYYY-MM-DD: {checked_at!r}")

        for key, value in record.items():
            key_lower = str(key).casefold()
            if (key_lower.endswith("_url") or key_lower in {"url", "official_homepage"}) and value:
                if key_lower == "source_url":
                    continue
                if key_lower == "official_homepage" and isinstance(value, str):
                    parts = urlsplit(value.strip())
                    if (
                        HTTP_URL_RE.fullmatch(value.strip())
                        and parts.scheme.lower() == "http"
                        and parts.netloc
                        and not parts.username
                    ):
                        audit.legacy_http_urls.append(f"{prefix}.{key}")
                        continue
                if not valid_https_url(value):
                    audit.error(f"{prefix}.{key} must be HTTPS: {value!r}")


def audit_unique_records(records: list[dict[str, Any]], audit: Audit) -> None:
    seen_ids: dict[str, int] = {}
    for index, record in enumerate(records):
        record_id = record.get("id")
        if isinstance(record_id, str) and record_id.strip():
            if record_id in seen_ids:
                audit.error(
                    f"duplicate record id {record_id!r}: combined indexes "
                    f"{seen_ids[record_id]} and {index}"
                )
            else:
                seen_ids[record_id] = index


def choose_html(root: Path, requested: Path | None, audit: Audit) -> Path:
    if requested is not None:
        return under_root(root, requested, requested)
    existing = [root / candidate for candidate in HTML_CANDIDATES if (root / candidate).is_file()]
    if len(existing) == 1:
        return existing[0]
    if len(existing) > 1:
        audit.error(
            "multiple directory HTML candidates found; pass --html: "
            + ", ".join(display_path(path, root) for path in existing)
        )
        return existing[0]
    return root / HTML_CANDIDATES[0]


def referenced_local_scripts(html: str, html_path: Path, root: Path) -> list[Path]:
    scripts: list[Path] = []
    for match in SCRIPT_SRC_RE.finditer(html):
        src = unescape(match.group(2)).strip()
        parts = urlsplit(src)
        if parts.scheme or parts.netloc or not parts.path:
            continue
        if parts.path.startswith("/"):
            target = root / parts.path.lstrip("/")
        else:
            target = html_path.parent / parts.path
        scripts.append(target.resolve())
    return scripts


def audit_html(
    html_path: Path,
    records: list[dict[str, Any]],
    payloads: list[Any],
    root: Path,
    audit: Audit,
) -> list[Path]:
    if not html_path.is_file():
        audit.error(f"missing generated HTML: {html_path}")
        return []
    try:
        html = html_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        audit.error(f"HTML is not UTF-8: {html_path}: {exc}")
        return []

    for index, record in enumerate(records):
        for key in ("name", "source_url"):
            value = record.get(key)
            if isinstance(value, str) and value:
                compact = re.sub(r"\s+", "", value)
                representations = {
                    value,
                    unescape(value),
                    escape(value, quote=True),
                    compact,
                    escape(compact, quote=True),
                }
                if not any(candidate in html for candidate in representations):
                    audit.error(f"HTML is missing record {key} at index {index}: {value!r}")
        source_urls = record.get("source_urls", [])
        if isinstance(source_urls, list):
            for source_url in source_urls:
                if not isinstance(source_url, str) or not source_url:
                    continue
                representations = {
                    source_url,
                    unescape(source_url),
                    escape(source_url, quote=True),
                }
                if not any(candidate in html for candidate in representations):
                    audit.error(
                        f"HTML is missing record source_urls entry at index {index}: {source_url!r}"
                    )

    for payload_index, payload in enumerate(payloads):
        if not isinstance(payload, dict) or not isinstance(payload.get("sections"), list):
            continue
        for section_index, section in enumerate(payload["sections"]):
            if not isinstance(section, dict) or not isinstance(section.get("facts"), list):
                continue
            for fact_index, fact in enumerate(section["facts"]):
                if not isinstance(fact, dict):
                    continue
                for key in ("label", "value", "source_url"):
                    value = fact.get(key)
                    if not isinstance(value, str) or not value:
                        continue
                    representations = {value, unescape(value), escape(value, quote=True)}
                    if not any(candidate in html for candidate in representations):
                        audit.error(
                            "HTML is missing knowledge fact %s at payload %d, section %d, fact %d: %r"
                            % (key, payload_index, section_index, fact_index, value)
                        )

    scripts = referenced_local_scripts(html, html_path, root)
    if not scripts:
        audit.error("generated HTML must reference a local search/filter JavaScript file")
        return []

    behavior_scripts: list[Path] = []
    for script in scripts:
        if not script.is_file():
            audit.error(f"referenced JavaScript does not exist: {display_path(script, root)}")
            continue
        text = script.read_text(encoding="utf-8")
        if re.search(r"search|filter", script.name, re.IGNORECASE) or (
            re.search(r"\bfilter\s*\(", text) and re.search(r"input|change|keyup", text, re.IGNORECASE)
        ):
            behavior_scripts.append(script)
    if not behavior_scripts:
        audit.error("no referenced JavaScript implements recognizable search/filter behavior")
    return scripts


def audit_forbidden_term(paths: list[Path], root: Path, audit: Audit) -> None:
    forbidden_term = chr(25919) + chr(31574)
    for path in dict.fromkeys(paths):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            audit.error(f"cannot scan {display_path(path, root)}: {exc}")
            continue
        if forbidden_term in text:
            lines = [str(index) for index, line in enumerate(text.splitlines(), 1) if forbidden_term in line]
            audit.error(
                f"forbidden two-character term in {display_path(path, root)} at line(s) "
                + ", ".join(lines)
            )


def catalog_files(root: Path, known_paths: list[Path]) -> list[Path]:
    paths = list(known_paths)
    allowed_suffixes = {".css", ".html", ".js", ".json", ".py"}
    for directory in (root / "assets", root / "data", root / "scripts"):
        if not directory.is_dir():
            continue
        for path in directory.glob("*mori*directory*"):
            if path.is_file() and path.suffix.lower() in allowed_suffixes:
                paths.append(path)
    return list(dict.fromkeys(path.resolve() for path in paths))


def source_coverage(records: list[dict[str, Any]]) -> tuple[Counter[str], Counter[str]]:
    hosts: Counter[str] = Counter()
    categories: Counter[str] = Counter()
    for record in records:
        url = record.get("source_url")
        if isinstance(url, str):
            hosts[urlsplit(url).netloc.lower()] += 1
        values = record.get("categories")
        if isinstance(values, list):
            for category in values:
                if isinstance(category, str) and category:
                    categories[category] += 1
    return hosts, categories


def registered_source_hosts(payloads: list[Any], audit: Audit) -> Counter[str]:
    hosts: Counter[str] = Counter()
    seen_source_ids: set[str] = set()
    for payload_index, payload in enumerate(payloads):
        if not isinstance(payload, dict):
            continue
        source_items: list[tuple[str, Any]] = []
        source = payload.get("source")
        if isinstance(source, dict):
            source_items.append((f"payload[{payload_index}].source", source))
        sources = payload.get("sources")
        if sources is not None:
            if not isinstance(sources, list):
                audit.error(f"payload[{payload_index}].sources must be an array")
            else:
                for index, item in enumerate(sources):
                    source_items.append((f"payload[{payload_index}].sources[{index}]", item))

        for path, source_item in source_items:
            if not isinstance(source_item, dict):
                audit.error(f"{path} must be an object")
                continue
            url = source_item.get("url", source_item.get("directory_url"))
            if not valid_https_url(url):
                audit.error(f"{path} must contain an HTTPS url or directory_url: {url!r}")
            else:
                hosts[urlsplit(url).netloc.lower()] += 1

            source_id = source_item.get("id")
            if ".sources[" in path:
                if not isinstance(source_id, str) or not source_id.strip():
                    audit.error(f"{path}.id must be a non-empty string")
                elif source_id in seen_source_ids:
                    audit.error(f"duplicate source registry id: {source_id!r}")
                else:
                    seen_source_ids.add(source_id)
                if not isinstance(source_item.get("name"), str) or not source_item["name"].strip():
                    audit.error(f"{path}.name must be a non-empty string")

            links = source_item.get("links")
            if links is not None:
                if not isinstance(links, list):
                    audit.error(f"{path}.links must be an array")
                else:
                    for link_index, link in enumerate(links):
                        link_path = f"{path}.links[{link_index}]"
                        if not isinstance(link, dict):
                            audit.error(f"{link_path} must be an object")
                            continue
                        link_url = link.get("url")
                        if not valid_https_url(link_url):
                            audit.error(f"{link_path}.url must be HTTPS: {link_url!r}")
                        else:
                            hosts[urlsplit(link_url).netloc.lower()] += 1

            expected = source_item.get("expected_records")
            indexed = source_item.get("indexed_records")
            if expected is None and indexed is None:
                continue
            for key, value in (("expected_records", expected), ("indexed_records", indexed)):
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    audit.error(f"{path}.{key} must be a non-negative integer")
            if (
                isinstance(expected, int)
                and not isinstance(expected, bool)
                and isinstance(indexed, int)
                and not isinstance(indexed, bool)
                and expected != indexed
            ):
                audit.error(
                    f"{path} coverage mismatch: expected_records={expected}, indexed_records={indexed}"
                )
    return hosts


def audit_declared_coverage(
    payloads: list[Any],
    hosts: Counter[str],
    registry_hosts: Counter[str],
    categories: Counter[str],
    audit: Audit,
) -> None:
    for host in REQUIRED_SOURCE_HOSTS:
        if hosts[host] == 0 and registry_hosts[host] == 0:
            audit.error(f"source is not covered by records or registry: {host}")

    coverage_payloads = [payload for payload in payloads if isinstance(payload, dict) and "coverage" in payload]
    if not coverage_payloads:
        return
    for payload in coverage_payloads:
        audit_coverage_object(payload["coverage"], hosts, categories, audit)


def audit_coverage_object(
    coverage: Any,
    hosts: Counter[str],
    categories: Counter[str],
    audit: Audit,
) -> None:
    if not isinstance(coverage, dict):
        audit.error("$.coverage must be an object")
        return
    declared_sources = coverage.get("sources")
    if declared_sources is not None:
        if not isinstance(declared_sources, dict):
            audit.error("$.coverage.sources must be an object of host-to-count values")
        else:
            for host, count in declared_sources.items():
                if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                    audit.error(f"$.coverage.sources[{host!r}] must be a non-negative integer")
                elif hosts[str(host).lower()] != count:
                    audit.error(
                        f"declared source count for {host!r} is {count}, calculated {hosts[str(host).lower()]}"
                    )

    declared_categories = coverage.get("categories")
    if declared_categories is not None:
        if not isinstance(declared_categories, dict):
            audit.error("$.coverage.categories must be an object of category-to-count values")
        else:
            for category, count in declared_categories.items():
                if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                    audit.error(f"$.coverage.categories[{category!r}] must be a non-negative integer")
                elif categories[str(category)] != count:
                    audit.error(
                        f"declared category count for {category!r} is {count}, calculated {categories[str(category)]}"
                    )


def print_report(
    records: list[dict[str, Any]],
    hosts: Counter[str],
    registry_hosts: Counter[str],
    categories: Counter[str],
    audit: Audit,
) -> None:
    print(f"records: {len(records)}")
    print("source coverage:")
    if hosts:
        for host, count in sorted(hosts.items()):
            print(f"  {host}: {count}")
    else:
        print("  (none)")
    print(f"legacy HTTP official_homepage URLs: {len(audit.legacy_http_urls)}")
    print("source registry coverage:")
    if registry_hosts:
        for host, count in sorted(registry_hosts.items()):
            print(f"  {host}: {count}")
    else:
        print("  (none)")
    print("category coverage:")
    if categories:
        for category, count in sorted(categories.items()):
            print(f"  {category}: {count}")
    else:
        print("  (none)")

    for warning in audit.warnings:
        print(f"WARNING: {warning}")
    for error in audit.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if audit.errors:
        print(f"FAIL: {len(audit.errors)} error(s), {len(audit.warnings)} warning(s)", file=sys.stderr)
    else:
        print(f"PASS: 0 errors, {len(audit.warnings)} warning(s)")


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    audit = Audit()
    data_path = under_root(root, args.data, DATA_RELATIVE_PATH)
    supplement_path = under_root(root, args.supplement, SUPPLEMENT_RELATIVE_PATH)
    html_path = choose_html(root, args.html, audit)

    payload = load_json(data_path, audit)
    records = extract_records(payload, audit) if payload is not None else []
    if payload is not None:
        audit_structure(
            payload,
            records,
            audit,
            label=display_path(data_path, root),
            require_category_pages=True,
        )

    payloads = [payload] if payload is not None else []
    data_paths = [data_path, supplement_path]
    if supplement_path.is_file():
        supplement = load_json(supplement_path, audit)
        if supplement is not None:
            supplement_records = extract_records(supplement, audit)
            audit_structure(
                supplement,
                supplement_records,
                audit,
                label=display_path(supplement_path, root),
                require_category_pages=False,
            )
            records.extend(supplement_records)
            payloads.append(supplement)
    elif args.supplement is not None:
        audit.error(f"missing supplement JSON: {supplement_path}")

    for extra_relative_path in EXTRA_DATA_RELATIVE_PATHS:
        extra_path = root / extra_relative_path
        data_paths.append(extra_path)
        if not extra_path.is_file():
            audit.error(f"missing expansion JSON: {extra_path}")
            continue
        extra = load_json(extra_path, audit)
        if extra is None:
            continue
        extra_records: list[dict[str, Any]] = []
        if isinstance(extra, dict) and "records" in extra:
            extra_records = extract_records(extra, audit)
        elif not isinstance(extra, dict):
            audit.error(f"{display_path(extra_path, root)}: JSON root must be an object")
        audit_structure(
            extra,
            extra_records,
            audit,
            label=display_path(extra_path, root),
            require_category_pages=False,
        )
        records.extend(extra_records)
        payloads.append(extra)

    audit_unique_records(records, audit)

    scripts = audit_html(html_path, records, payloads, root, audit)
    scan_paths = catalog_files(root, [*data_paths, html_path, *scripts])
    audit_forbidden_term(scan_paths, root, audit)

    hosts, categories = source_coverage(records)
    registry_hosts = registered_source_hosts(payloads, audit)
    audit_declared_coverage(payloads, hosts, registry_hosts, categories, audit)
    if audit.legacy_http_urls:
        audit.warning(
            f"{len(audit.legacy_http_urls)} official_homepage URL(s) retain legacy HTTP source values"
        )
    print_report(records, hosts, registry_hosts, categories, audit)
    return 1 if audit.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
