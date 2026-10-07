#!/usr/bin/env python3
"""Cross-check editorial updates, crawl evidence and generated publication."""
import json
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
doc = json.loads((ROOT/'data/official-updates.json').read_text(encoding='utf-8'))
catalog = json.loads((ROOT/'data/official-source-catalog.json').read_text(encoding='utf-8'))
sources = {r['url']:r for r in catalog['sources']}
page = BeautifulSoup((ROOT/'updates/index.html').read_text(encoding='utf-8'), 'html.parser')
assert len(doc['entries']) == len({r['id'] for r in doc['entries']})
assert len(page.select('.official-update-item')) == len(doc['entries'])
assert page.select_one('link[rel=canonical]')['href'] == 'https://morimachi.enshu-lifehack.com/updates/'
for entry in doc['entries']:
    source = sources[entry['source_url']]
    assert source['status'] == 'http-200', entry['source_url']
    assert source['checked_at'] == entry['checked_at'] == doc['checked_at']
    assert entry['source_updated'] <= entry['checked_at']
    assert page.select_one('#update-'+entry['id']), entry['id']
    for href in entry['pages']:
        html = (ROOT/href.strip('/')/'index.html').read_text(encoding='utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        assert len(soup.select('#update-'+entry['id'])) == 1, href
        assert entry['summary'] in soup.get_text(), href
        assert soup.select_one('a[href="'+entry['source_url']+'"]'), href
        ids = [el['id'] for el in soup.select('[id]')]
        assert len(ids) == len(set(ids)), href+' has duplicate ids'
nursery = (ROOT/'life/family-grow/nursery-school/index.html').read_text(encoding='utf-8')
assert '令和9年度（2027年度）入所可能数見込み' in nursery
assert 'search-tools.mjs?v=20261008a' in nursery
assert not any(s in nursery for s in ['町立幼稚園5園','ときわ保育園','2026年度の入所案内'])
club = (ROOT/'life/education/after-school-club/index.html').read_text(encoding='utf-8')
assert '令和7年9月16日' not in club and '10月17日' not in club
print(f'PASS: {len(doc["entries"])} reviewed updates, links, dates, unique IDs and current application years')
