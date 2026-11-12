"""Keep the two reviewed waste-routing titles consistent in existing links.

Only replace the former full title for its matching destination. Custom action
labels and historical prose are retained.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = {
    '/life/start-living/bulky-garbage-dropoff/': '森町で粗大ごみを出す。持ち込み先は中遠広域粗大ごみ処理施設（磐田市）。',
    '/life/moving-out/bulk-garbage-cleaning/': '転出前の片付けは、粗大ごみは中遠広域施設へ・家電は家電リサイクル法対応で',
}


def main():
    titles = {x['href']: x['title'] for x in json.loads((ROOT / 'data/topics_master.json').read_text(encoding='utf8')) if x['href'] in OLD}
    urls = re.findall(r'<loc>https://morimachi\.enshu-lifehack\.com(/.*?)</loc>', (ROOT / 'sitemap.xml').read_text(encoding='utf8'))
    changed = 0
    for url in urls:
        path = ROOT / url.strip('/') / 'index.html'
        if not path.is_file():
            continue
        raw = path.read_bytes().decode('utf8')
        out = raw
        for href, old in OLD.items():
            pattern = r'(<a\b[^>]*\bhref="' + re.escape(href) + r'"[^>]*>)' + re.escape(html.escape(old)) + r'(</a>)'
            out = re.sub(pattern, lambda m: m[1] + html.escape(titles[href]) + m[2], out)
        if out != raw:
            path.write_bytes(out.encode('utf8'))
            changed += 1
    print('Reviewed destination link titles synchronized:', changed)


if __name__ == '__main__':
    main()
