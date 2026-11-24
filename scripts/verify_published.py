#!/usr/bin/env python3
"""Verify the live Mori sitemap, permanent redirects, and custom 404."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from pathlib import Path
from threading import Lock
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://morimachi.enshu-lifehack.com"
UA = "morimachi-lifehack-deploy-check/2.0"
SITEMAP_NAMESPACE = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
NOT_FOUND_PATH = "/this-page-should-not-exist-20260804/"
TIMEOUT = 20
MAX_ATTEMPTS = 5
WORKERS = 4


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


OPENER = build_opener(NoRedirect)


@dataclass(frozen=True)
class Response:
    status: int
    location: str = ""
    retry_after: str = ""
    body: bytes = b""
    error: str = ""


class RequestPacer:
    """Space requests to production and share any cooldown across workers."""

    def __init__(self) -> None:
        self.lock = Lock()
        self.interval = 0.2
        self.next_request = 0.0
        self.cooldown_end = 0.0
        self.rate_limit_count = 0
        self.retry_count = 0

    def wait(self) -> None:
        while True:
            with self.lock:
                now = time.monotonic()
                remaining = max(self.cooldown_end, self.next_request) - now
                if remaining <= 0:
                    self.next_request = now + self.interval
                    return
            time.sleep(remaining)

    def defer(self, delay: float, rate_limited: bool) -> None:
        with self.lock:
            self.retry_count += 1
            if rate_limited:
                self.rate_limit_count += 1
                if time.monotonic() >= self.cooldown_end:
                    self.interval = min(self.interval * 2, 2.0)
                    print(f"Rate limited. Pausing for {delay:.0f}s, then spacing requests by {self.interval:g}s.")
            self.cooldown_end = max(self.cooldown_end, time.monotonic() + delay)


def request_once(url: str, *, read_body: bool) -> Response:
    request = Request(url, headers={"User-Agent": UA}, method="GET")
    try:
        with OPENER.open(request, timeout=TIMEOUT) as result:
            return Response(result.status, body=result.read() if read_body else b"")
    except HTTPError as result:
        with result:
            return Response(
                result.code,
                location=result.headers.get("Location", ""),
                retry_after=result.headers.get("Retry-After", ""),
                body=result.read() if read_body and result.code == 404 else b"",
            )
    except (OSError, URLError) as error:
        return Response(0, error=str(error))


def retry_delay(value: str, fallback: float) -> float:
    if not value:
        return fallback
    try:
        seconds = int(value)
    except ValueError:
        try:
            seconds = parsedate_to_datetime(value).timestamp() - time.time()
        except (ValueError, TypeError, OverflowError):
            return fallback
    return max(1.0, seconds)


def fetch(url: str, pacer: RequestPacer, *, read_body: bool = False) -> Response:
    for attempt in range(MAX_ATTEMPTS):
        pacer.wait()
        response = request_once(url, read_body=read_body)
        if response.status not in (0, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524):
            return response
        if attempt == MAX_ATTEMPTS - 1:
            return response
        limited = response.status == 429
        pacer.defer(retry_delay(response.retry_after, 30 if limited else 2 ** attempt), limited)
    raise AssertionError("Retry loop did not return a response")


def sitemap_urls(content: bytes) -> list[str]:
    root = ET.fromstring(content)
    if root.tag != SITEMAP_NAMESPACE + "urlset":
        raise ValueError("The production sitemap is not a sitemap urlset.")
    urls = [node.text for node in root.findall(f"{SITEMAP_NAMESPACE}url/{SITEMAP_NAMESPACE}loc")]
    if not urls or len(set(urls)) != len(urls):
        raise ValueError("The production sitemap is empty or contains duplicate URLs.")
    for url in urls:
        if not url or not url.startswith(SITE + "/") or urlsplit(url).query or urlsplit(url).fragment:
            raise ValueError(f"Unexpected public sitemap URL: {url!r}")
    return urls


def permanent_redirects() -> dict[str, str]:
    redirects = {}
    for line in (ROOT / "_redirects").read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) != 3 or fields[2] != "301" or line.lstrip().startswith("#"):
            continue
        source, target, _ = fields
        if "*" in source:
            # Probe the /iwata/* wildcard with an existing public page.
            source, target = source.replace("*", "terms/"), target.replace(":splat", "terms/")
        redirects[source] = target
    return redirects


def matches_redirect(url: str, response: Response, target: str) -> bool:
    return response.status == 301 and urljoin(url, response.location) == urljoin(SITE, target)


def check_pages(urls: list[str], pacer: RequestPacer) -> list[str]:
    problems = []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        pending = {pool.submit(fetch, url, pacer): url for url in urls}
        for checked, job in enumerate(as_completed(pending), 1):
            response = job.result()
            url = pending[job]
            if response.status != 200:
                problems.append(f"{url} returned {response.status or response.error}, expected 200")
            if checked % 100 == 0 or checked == len(urls):
                print(f"Public pages checked: {checked}/{len(urls)}")
    return problems


def main() -> int:
    pacer = RequestPacer()
    print(f"Checking production: {SITE}")
    sitemap = fetch(SITE + "/sitemap.xml", pacer, read_body=True)
    if sitemap.status != 200:
        print(f"Could not read production sitemap: {sitemap.status or sitemap.error}")
        return 2
    try:
        urls = sitemap_urls(sitemap.body)
    except (ET.ParseError, ValueError) as error:
        print(f"Invalid production sitemap: {error}")
        return 2

    print(f"Production sitemap URLs: {len(urls)}")
    page_problems = check_pages(urls, pacer)
    redirect_problems = []
    redirects = permanent_redirects()
    for source, target in redirects.items():
        url = SITE + source
        response = fetch(url, pacer)
        if not matches_redirect(url, response, target):
            actual = response.status or response.error
            redirect_problems.append(f"{source} returned {actual} {response.location}, expected 301 {target}")

    not_found = fetch(SITE + NOT_FOUND_PATH, pacer, read_body=True)
    custom_404 = not_found.status == 404 and "ページが見つかりません".encode() in not_found.body
    print(f"Public URLs (HTTP 200): {len(urls) - len(page_problems)}/{len(urls)}")
    print(f"Permanent redirects (HTTP 301): {len(redirects) - len(redirect_problems)}/{len(redirects)}")
    print(f"Custom 404: {'OK' if custom_404 else f'failed ({not_found.status or not_found.error})'}")
    print(f"Retries: {pacer.retry_count} ({pacer.rate_limit_count} rate-limited)")
    for problem in sorted(page_problems + redirect_problems):
        print(f"FAIL: {problem}")

    return int(bool(page_problems or redirect_problems or not custom_404))


if __name__ == "__main__":
    sys.exit(main())
