#!/usr/bin/env python3
"""Verify the first Phase 4 release cohort locally or after production deploy.

Local pending audit:
  python scripts/verify_phase4_release_cohort.py --local --expect-pending

Production audit (cache bypass is automatic):
  python scripts/verify_phase4_release_cohort.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from html import unescape
from pathlib import Path
from urllib.parse import urljoin


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://morimachi.enshu-lifehack.com"
UA = "morimachi-phase4-release-audit/1.0"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


OPENER = urllib.request.build_opener(NoRedirect)

COHORT = (
    (215, "/records/census-resident-register-difference/", "森町で国勢調査と住民基本台帳の人口差を混同しない", "国勢調査"),
    (232, "/records/water-sewer-bill-fields/", "森町で水道料金と下水道使用料の請求区分を読み分ける", "請求区分"),
    (241, "/records/zoning-map-legend-guide/", "森町で都市計画図の色と凡例と境界線を順に読む", "境界線"),
    (270, "/records/home-care-eligibility-sheet/", "森町で在宅福祉サービスの対象条件を本人情報と照合する", "対象条件"),
    (277, "/agriculture/forest-owner-notification/", "森町の森林所有者届出｜相続・売買後の確認", "森林所有者届出"),
)


def cache_bust(url: str, token: str) -> str:
    return f"{url}{'&' if '?' in url else '?'}audit={token}"


def fetch(url: str, token: str) -> tuple[int, dict[str, str], bytes]:
    request = urllib.request.Request(
        cache_bust(url, token),
        headers={"User-Agent": UA, "Cache-Control": "no-cache", "Pragma": "no-cache"},
    )
    try:
        with OPENER.open(request, timeout=30) as response:
            return response.status, dict(response.headers.items()), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers.items()) if exc.headers else {}, exc.read()
    except Exception as exc:
        return 0, {}, str(exc).encode("utf-8", errors="replace")


def attr_values(html: str, tag: str, attr: str, suffix: str | None = None) -> list[str]:
    values = re.findall(rf"<{tag}\b[^>]*\b{attr}=[\"']([^\"']+)[\"']", html, re.I)
    return [value for value in values if suffix is None or value.split("?", 1)[0].lower().endswith(suffix)]


def canonical(html: str) -> str:
    match = re.search(r"<link\b(?=[^>]*\brel=[\"']canonical[\"'])[^>]*\bhref=[\"']([^\"']+)[\"']", html, re.I)
    return unescape(match.group(1)) if match else ""


def has_noindex(html: str) -> bool:
    return bool(re.search(r"<meta\b[^>]*\bname=[\"']robots[\"'][^>]*\bcontent=[\"'][^\"']*noindex", html, re.I))


def local_asset_path(page_path: str, reference: str) -> Path:
    clean = reference.split("?", 1)[0]
    if clean.startswith("/"):
        return ROOT / clean.lstrip("/")
    return ROOT / page_path.strip("/") / clean


def check_page_local(page_path: str, title: str, marker: str, pending: bool, errors: list[str]) -> None:
    index = ROOT / page_path.strip("/") / "index.html"
    prefix = f"local {page_path}"
    if not index.is_file():
        errors.append(f"{prefix}: index.html missing")
        return
    html = index.read_text(encoding="utf-8", errors="replace")
    expected = SITE + page_path
    if title not in html or marker not in html:
        errors.append(f"{prefix}: unique title/marker missing")
    if canonical(html) != expected:
        errors.append(f"{prefix}: canonical mismatch ({canonical(html)!r})")
    if has_noindex(html) != pending:
        errors.append(f"{prefix}: noindex state mismatch (expected pending={pending})")
    svgs = attr_values(html, "img", "src", ".svg")
    if not {"cover.svg", "fig1.svg", "fig2.svg"}.issubset({Path(x.split("?", 1)[0]).name for x in svgs}):
        errors.append(f"{prefix}: cover.svg/fig1.svg/fig2.svg references incomplete")
    css = attr_values(html, "link", "href", ".css")
    if not css:
        errors.append(f"{prefix}: stylesheet reference missing")
    for ref in svgs + css + attr_values(html, "script", "src", ".js"):
        asset = local_asset_path(page_path, ref)
        if not asset.is_file() or asset.stat().st_size == 0:
            errors.append(f"{prefix}: asset missing/empty {ref}")


def check_page_live(page_path: str, title: str, marker: str, token: str, errors: list[str]) -> None:
    url = SITE + page_path
    status, _, payload = fetch(url, token)
    prefix = f"live {page_path}"
    if status != 200:
        errors.append(f"{prefix}: HTTP {status}")
        return
    html = payload.decode("utf-8", errors="replace")
    if title not in html or marker not in html:
        errors.append(f"{prefix}: unique title/marker missing")
    if canonical(html) != url:
        errors.append(f"{prefix}: canonical mismatch ({canonical(html)!r})")
    if has_noindex(html):
        errors.append(f"{prefix}: noindex remains")
    svgs = attr_values(html, "img", "src", ".svg")
    names = {Path(x.split("?", 1)[0]).name for x in svgs}
    if not {"cover.svg", "fig1.svg", "fig2.svg"}.issubset(names):
        errors.append(f"{prefix}: cover.svg/fig1.svg/fig2.svg references incomplete")
    css = attr_values(html, "link", "href", ".css")
    if not css:
        errors.append(f"{prefix}: stylesheet reference missing")
    refs = svgs + css + attr_values(html, "script", "src", ".js")
    for ref in refs:
        asset_url = urljoin(url, ref)
        asset_status, headers, body = fetch(asset_url, token)
        if asset_status != 200 or not body:
            errors.append(f"{prefix}: asset HTTP {asset_status} {ref}")
            continue
        if ref.split("?", 1)[0].lower().endswith(".svg") and "svg" not in headers.get("Content-Type", "").lower():
            errors.append(f"{prefix}: SVG content-type mismatch {ref}")


def local_surfaces(pending: bool, errors: list[str]) -> None:
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8", errors="replace")
    index = json.loads((ROOT / "search-index.json").read_text(encoding="utf-8"))
    hrefs = {row.get("href") for row in index if isinstance(row, dict)}
    for _, path, _, _ in COHORT:
        in_map = f"<loc>{SITE + path}</loc>" in sitemap
        in_search = path in hrefs
        if pending and (in_map or in_search):
            errors.append(f"local surfaces: pending page exposed {path} sitemap={in_map} search={in_search}")
        if not pending and (not in_map or not in_search):
            errors.append(f"local surfaces: released page missing {path} sitemap={in_map} search={in_search}")


def live_surfaces(token: str, errors: list[str]) -> None:
    sm_status, _, sm_body = fetch(SITE + "/sitemap.xml", token)
    si_status, _, si_body = fetch(SITE + "/search-index.json", token)
    if sm_status != 200:
        errors.append(f"live sitemap: HTTP {sm_status}")
        sitemap = ""
    else:
        sitemap = sm_body.decode("utf-8", errors="replace")
    try:
        index = json.loads(si_body.decode("utf-8")) if si_status == 200 else []
    except json.JSONDecodeError:
        index = []
        errors.append("live search-index: invalid JSON")
    if si_status != 200:
        errors.append(f"live search-index: HTTP {si_status}")
    by_href = {row.get("href"): row for row in index if isinstance(row, dict)}
    for _, path, title, _ in COHORT:
        if f"<loc>{SITE + path}</loc>" not in sitemap:
            errors.append(f"live sitemap: URL missing {path}")
        if path not in by_href:
            errors.append(f"live search-index: href missing {path}")
        elif by_href[path].get("title") != title:
            errors.append(f"live search-index: title mismatch {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", action="store_true", help="read the worktree instead of production")
    parser.add_argument("--expect-pending", action="store_true", help="expect noindex and exclusion from local public surfaces")
    args = parser.parse_args()
    if args.expect_pending and not args.local:
        parser.error("--expect-pending is only valid with --local")
    errors: list[str] = []
    token = str(time.time_ns())
    for _, path, title, marker in COHORT:
        if args.local:
            check_page_local(path, title, marker, args.expect_pending, errors)
        else:
            check_page_live(path, title, marker, token, errors)
    if args.local:
        local_surfaces(args.expect_pending, errors)
    else:
        live_surfaces(token, errors)
    if errors:
        print("Phase 4 cohort audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    state = "local pending" if args.expect_pending else ("local released" if args.local else "production released")
    print(f"Phase 4 cohort audit: PASS ({state}, {len(COHORT)} pages)")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
