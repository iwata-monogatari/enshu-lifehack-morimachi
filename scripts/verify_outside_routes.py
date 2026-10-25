"""Check new reader paths, summary placement, and optional live artifact equality."""
import argparse
import hashlib
import json
import re
import sys
import time
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
from build_outside_routes import ROUTES, SUMMARIES

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://morimachi.enshu-lifehack.com'
PAGES = ['/', *['/for/' + row[0] + '/' for row in ROUTES], *SUMMARIES,
         '/blog/20261001-morimachi-jirogaki-chokubaijo/']

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids, self.stack, self.bad_summary = [], set(), [], False
    def handle_starttag(self, tag, pairs):
        attrs = dict(pairs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        if tag == 'a':
            self.links.append(attrs.get('href', ''))
        if 'outside-quick' in attrs.get('class', '').split():
            self.bad_summary |= any('hero-visual' in c.split() for t, c in self.stack)
        if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:
            self.stack.append((tag, attrs.get('class', '')))
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i][0] == tag:
                self.stack = self.stack[:i]
                break

def page_path(route):
    return ROOT / route.lstrip('/') / 'index.html'

def normalized(data):
    return data.replace(b'\r\n', b'\n')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    errors, checked = [], []
    for route in PAGES:
        src = page_path(route).read_text(encoding='utf-8')
        page = Page()
        page.feed(src)
        if page.bad_summary:
            errors.append(route + ': summary inside hero image layout')
        if src.count('<h1') != 1:
            errors.append(route + ': H1 count')
        if route in SUMMARIES and src.count('<!-- OUTSIDE-QUICK:START -->') != 1:
            errors.append(route + ': summary missing or duplicated')
        if 'href="' + SITE + route + '"' not in src:
            errors.append(route + ': canonical missing')
        for href in page.links:
            parsed = urlsplit(href)
            if parsed.scheme or parsed.netloc or not href:
                continue
            if not parsed.path or parsed.path.startswith('/'):
                target = page_path(parsed.path or route)
                if parsed.path and not parsed.path.endswith('/'):
                    target = ROOT / parsed.path.lstrip('/')
                if not target.is_file():
                    errors.append(route + ': missing target ' + href)
                elif parsed.fragment and target.suffix == '.html':
                    linked = Page()
                    linked.feed(target.read_text(encoding='utf-8'))
                    if unquote(parsed.fragment) not in linked.ids:
                        errors.append(route + ': missing anchor ' + href)
        checked.append(route)
    sitemap = (ROOT/'sitemap.xml').read_text(encoding='utf-8')
    index = json.loads((ROOT/'search-index.json').read_text(encoding='utf-8'))
    index_text = json.dumps(index,ensure_ascii=False)
    home = (ROOT/'index.html').read_text(encoding='utf-8')
    for slug, *_ in ROUTES:
        route = '/for/' + slug + '/'
        if route not in home or SITE+route not in sitemap or route not in index_text:
            errors.append(route + ': missing home/sitemap/search entry')
        if not any(p.get('href') == route and p.get('kind') == '目的別ガイド' for p in index):
            errors.append(route + ': wrong search classification')
    matches = []
    if args.live:
        assets = ['/assets/outside-routes.css', '/assets/site.css', '/assets/search-app.js',
                  '/assets/img/hero-morimachi.svg', '/assets/img/jirogaki-feature.svg']
        stamp = str(int(time.time()))
        for route in PAGES + assets:
            path = page_path(route) if route in PAGES else ROOT/route.lstrip('/')
            req = urllib.request.Request(SITE+route+'?release_check='+stamp+'&fga_internal=1', headers={
                'User-Agent':'morimachi-lifehack-deploy-check/1.0', 'Cache-Control':'no-cache'})
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    remote = normalized(response.read())
                    local = normalized(path.read_bytes())
                    matched = remote == local
                    matches.append({'url':SITE+route,'status':response.status,'match':matched,
                                    'sha256':hashlib.sha256(remote).hexdigest()})
                    if not matched:
                        errors.append(route+': live artifact mismatch')
            except Exception as e:
                errors.append(route+': '+str(e))
    report={'pages':checked,'live':matches,'errors':errors}
    out=ROOT/'work/outside-verification.json'
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    sys.exit(bool(errors))

if __name__ == '__main__':
    main()
