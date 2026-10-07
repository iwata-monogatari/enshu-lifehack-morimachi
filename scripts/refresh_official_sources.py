#!/usr/bin/env python3
"""Refresh the official catalog, keeping resumable private evidence and a diff.

The previous catalog contains hashes, not article text: hash changes are
discovery signals, never an automatic claim that a service or fee changed.
No editorial verification dates are advanced by this crawler.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.robotparser
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from harvest_official_source_catalog import (
    ROOT, OFFICIAL_HOST, OFFICIAL_SITEMAP, USER_AGENT, PageMetadataParser,
    canonical_official_url, fetch_bytes, sitemap_entries,
)

sys.stdout.reconfigure(encoding='utf-8')


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--evidence-dir', type=Path, required=True)
    ap.add_argument('--workers', type=int, default=3, choices=range(1, 5))
    args = ap.parse_args()
    evidence = args.evidence_dir.resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    now = datetime.now(ZoneInfo('Asia/Tokyo'))
    day = now.date().isoformat()
    run_path = evidence / 'run.json'
    if run_path.exists() and json.loads(run_path.read_text(encoding='utf-8'))['checked_at'] != day:
        raise SystemExit('Use a fresh evidence directory on a different date; cached pages must not receive a new check date.')
    save(run_path, {'checked_at': day})
    baseline = evidence / 'baseline.json'
    if not baseline.exists():
        baseline.write_bytes((ROOT / 'data/official-source-catalog.json').read_bytes())
    previous = json.loads(baseline.read_text(encoding='utf-8'))
    old = {r['url']: r for r in previous['sources']}

    def get(url, kind):
        key = hashlib.sha256(url.encode()).hexdigest()
        payload_path = evidence / kind / (key + '.bin')
        meta_path = evidence / kind / (key + '.json')
        if payload_path.exists() and meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding='utf-8'))
            return payload_path.read_bytes(), meta['content_type'], meta['status'], meta['final_url']
        for attempt in range(3):
            try:
                result = fetch_bytes(url, timeout=25)
                payload_path.parent.mkdir(parents=True, exist_ok=True)
                payload_path.write_bytes(result[0])
                save(meta_path, {'url': url, 'content_type': result[1], 'status': result[2], 'final_url': result[3]})
                time.sleep(.15)
                return result
            except urllib.error.HTTPError as exc:
                if exc.code not in (429, 500, 502, 503, 504):
                    raise
            except (OSError, TimeoutError):
                if attempt == 2:
                    raise
            time.sleep(2 ** attempt)
        raise RuntimeError('Retries exhausted: ' + url)

    robot_url = 'https://' + OFFICIAL_HOST + '/robots.txt'
    robots = urllib.robotparser.RobotFileParser(robot_url)
    try:
        payload, _, _, _ = get(robot_url, 'robots')
        robots.parse(payload.decode('utf-8', errors='replace').splitlines())
        robots_status = 'retrieved'
    except urllib.error.HTTPError as exc:
        if exc.code not in (404, 410):
            raise
        robots.parse([])
        robots_status = 'http-' + str(exc.code)

    sitemap = {}
    pending, seen = [OFFICIAL_SITEMAP], set()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        while pending:
            batch = [u for u in pending if u not in seen]
            pending = []
            seen.update(batch)
            for url, result in zip(batch, pool.map(lambda u: get(u, 'sitemaps'), batch)):
                kind, entries = sitemap_entries(result[0])
                for entry in entries:
                    u = canonical_official_url(entry['loc'])
                    if not u.startswith('https://' + OFFICIAL_HOST + '/'):
                        continue
                    if kind == 'sitemapindex':
                        pending.append(u)
                    elif kind == 'urlset':
                        sitemap[u] = entry.get('lastmod', '')
                    else:
                        raise ValueError('Unexpected sitemap type ' + kind)
    if not sitemap:
        raise SystemExit('No official URLs found; catalog not replaced.')
    save(evidence / 'sitemap-pages.json', sitemap)
    print(f'Sitemaps: {len(seen)}, pages: {len(sitemap)}', flush=True)

    def fetch_page(url):
        row = {'url': url, 'sitemap_lastmod': sitemap.get(url, ''), 'checked_at': day}
        if not robots.can_fetch(USER_AGENT, url):
            return {**row, 'status': 'robots-disallowed'}
        try:
            payload, mime, status, final_url = get(url, 'pages')
            row.update(status=f'http-{status}', content_type=mime, final_url=final_url,
                       payload_bytes=len(payload), payload_sha256=hashlib.sha256(payload).hexdigest())
            if mime in ('text/html', 'application/xhtml+xml'):
                html = payload.decode('utf-8', errors='replace')
                parser = PageMetadataParser()
                parser.feed(html)
                row.update(parser.metadata())
                soup = BeautifulSoup(html, 'html.parser')
                main = soup.select_one('#contentsIn') or soup.select_one('#contents') or soup.select_one('main')
                if main:
                    for tag in main.select('script,style,noscript'):
                        tag.decompose()
                    body = main.get_text('\n', strip=True)
                    row['main_sha256'] = hashlib.sha256(body.encode()).hexdigest()
                    text_path = evidence / 'text' / (hashlib.sha256(url.encode()).hexdigest() + '.txt')
                    text_path.parent.mkdir(parents=True, exist_ok=True)
                    text_path.write_text(body, encoding='utf-8')
        except urllib.error.HTTPError as exc:
            row.update(status=f'http-{exc.code}', error=f'HTTP {exc.code}')
        except Exception as exc:
            row.update(status='fetch-error', error=f'{type(exc).__name__}: {exc}')
        return row

    fetched = {}
    # Recheck sitemap removals too: absence from an index is not deletion proof.
    queue = sorted(set(sitemap) | set(old))
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(fetch_page, u): u for u in queue}
        for i, future in enumerate(as_completed(futures), 1):
            row = future.result()
            fetched[row['url']] = row
            if i % 100 == 0:
                print(f'Fetched {i}/{len(queue)}', flush=True)
    save(evidence / 'fetched.json', fetched)
    fields = ['sitemap_lastmod', 'title', 'headings', 'visible_sha256', 'status']
    added = [fetched[u] for u in sorted(set(sitemap) - set(old))]
    removed = [{**fetched[u], 'previous_title': old[u].get('title', ''),
                'previous_visible_sha256': old[u].get('visible_sha256', '')}
               for u in sorted(set(old) - set(sitemap))]
    changed = []
    unchanged = 0
    for url in sorted(set(old) & set(sitemap)):
        current = fetched[url]
        changes = {k: {'before': old[url].get(k), 'after': current.get(k)}
                   for k in fields if old[url].get(k) != current.get(k)}
        if changes:
            changed.append({'url': url, 'title': current.get('title', ''), 'changes': changes})
        else:
            unchanged += 1
    counts = {}
    for u in sitemap:
        status = fetched[u]['status']
        counts[status] = counts.get(status, 0) + 1
    document = {'generated_at': now.isoformat(timespec='seconds'), 'source_sitemap': OFFICIAL_SITEMAP,
                'total_urls': len(sitemap), 'fetched_this_run': len(queue),
                'status_counts': counts, 'sources': [fetched[u] for u in sorted(sitemap)]}
    diff = {'checked_at': day, 'baseline_generated_at': previous['generated_at'],
            'robots_status': robots_status, 'sitemaps_fetched': len(seen),
            'summary': {'previous_urls': len(old), 'current_urls': len(sitemap),
                        'added': len(added), 'absent_from_sitemap': len(removed),
                        'changed': len(changed), 'unchanged': unchanged,
                        'status_counts': counts},
            'limitations': 'Previous snapshot has metadata and hashes, not body text. Hash differences alone do not prove service changes. Sitemap absence alone does not prove deletion.',
            'added': added, 'absent_from_sitemap': removed, 'changed': changed}
    save(evidence / 'catalog.json', document)
    save(evidence / 'diff.json', diff)
    print(json.dumps(diff['summary'], ensure_ascii=False), flush=True)
    # Fail closed on retrieval errors; a partial crawl must not replace the catalog.
    if any(r['status'] == 'fetch-error' for r in fetched.values()) or any(fetched[u]['status'] != 'http-200' for u in sitemap):
        raise SystemExit('Incomplete retrieval of current pages; evidence retained, catalog not replaced.')
    save(ROOT / 'data/official-source-catalog.json', document)
    save(ROOT / 'reports' / f'official-source-diff-{day}.json', diff)


if __name__ == '__main__':
    main()
