"""Final, idempotent reader routes. Run after all content and CTA generators."""
import json
import re
from html import escape
from pathlib import Path
from growth_routes import group, next_reading, owner_card, SAFE
from mori_jikka import url

ROOT = Path(__file__).resolve().parent.parent
SKIP = {'.git', 'node_modules', 'scripts', 'parts', 'data', 'docs', 'reports', 'work', '_cache', '.github'}
FORBIDDEN = ('/life/emergency/', '/life/health-medical/', '/hub/trouble/',
             '/life/troubles-consult/living-costs-trouble/', '/life/troubles-consult/cannot-pay-tax/',
             '/life/troubles-consult/consumer-fraud/', '/life/troubles-consult/child-consultation/',
             '/life/housing/public-housing-consultation/')

def remove_marker(src, name):
    return re.sub(r'<!-- ' + name + r':START -->.*?<!-- ' + name + r':END -->', '', src, flags=re.S)

def replace_actions(src, body):
    start = src.find('<div class="action-grid">')
    if start < 0:
        raise ValueError('Blog action block missing')
    depth = 0
    for match in re.finditer(r'<div\b[^>]*>|</div>', src[start:]):
        depth += -1 if match[0].startswith('</') else 1
        if depth == 0:
            return src[:start] + '<div class="action-grid">' + body + '</div>' + src[start + match.end():]
    raise ValueError('Unclosed blog action block')

def apply(path, posts, page_types):
    src = original = path.read_text(encoding='utf-8')
    if '/assets/growth.css?' not in src:
        src = src.replace('</head>', '<link rel="stylesheet" href="/assets/growth.css?v=20261021a"></head>', 1)
    route = '/' + path.relative_to(ROOT).as_posix().removesuffix('index.html')
    post = posts.get(route)
    forbidden = route.startswith(FORBIDDEN) or bool(post and SAFE.search(post['title']))
    if forbidden:
        src = re.sub(r'<nav class="site-footer__nav" aria-label="住まいの案内">.*?</nav>', '', src, flags=re.S)
    if post:
        # This block is outside the editorial body. Keep its exact class for the article audit.
        src = replace_actions(src, next_reading(post))
    elif route not in ('/fudosan/sell/', '/life/housing/close-parents-house/'):
        is_owner = page_types.get(route) in ('real_estate', 'both', 'care') or route in ('/inheritance/', '/vacant-house/', '/hub/property/')
        if is_owner and not forbidden:
            # Older specialist pages have a handwritten aside as well as the shared CTA.
            src = re.sub(r'<aside class="company-strip[^\"]*">(?:(?!</aside>).)*fudosan\.atawi\.link(?:(?!</aside>).)*</aside>', '', src, flags=re.S)
            for name in ('KARTE-CTA-EARLY', 'KARTE-CTA-MOBILE', 'MORI-JIKKA-INBOUND'):
                src = remove_marker(src, name)
            block = '<!-- CTA-BLOCK:START -->' + owner_card('growth_owner') + '<!-- CTA-BLOCK:END -->'
            if '<!-- CTA-BLOCK:START -->' in src:
                src = re.sub(r'<!-- CTA-BLOCK:START -->.*?<!-- CTA-BLOCK:END -->', lambda _: block, src, flags=re.S)
            else:
                src = src.replace('</main>', '<div class="wrap">' + block + '</div></main>', 1)
        if route in ('/housing/districts/', '/life/living-soon/about-morimachi/', '/life/housing/buy-house/'):
            src = remove_marker(src, 'GROWTH-BUY')
            block = next_reading({'title': '森町へ移住・住宅選び', 'axis': 'sun'})
            # Avoid a self-link on the district guide.
            if route == '/housing/districts/':
                block = block.replace('href="/housing/districts/"', 'href="/life/housing/buy-house/"').replace('地区ごとの暮らしを比べる', '購入前の確認項目を読む')
            src = src.replace('</main>', '<!-- GROWTH-BUY:START --><div class="wrap">' + block + '</div><!-- GROWTH-BUY:END --></main>', 1)
    # Unify remaining direct Mori consultation exits, preserving the already supported sale intent.
    if route != '/about/related-sites/':
        src = re.sub(r'https://fudosan\.atawi\.link/areas/mori/(?:\?[^"<>]*)?', lambda _: escape(url('growth_owner'), quote=True), src)
    if path == ROOT / 'index.html':
        src = src.replace('実家・空き家の相談窓口を見る', '実家カルテの見本を見る')
        src = src.replace(escape(url('growth_owner'), quote=True), escape(url('growth_home', sample=True), quote=True))
    def consultation_event(match):
        tag = match[0]
        event = 'mori_growth_sample_click' if '/karte/sample/' in tag else 'mori_growth_apply_click'
        if 'data-track-click=' in tag:
            return re.sub(r'data-track-click="[^"]*"', 'data-track-click="' + event + '"', tag)
        return tag[:-1] + ' data-track-click="' + event + '">'
    src = re.sub(r'<a\b[^>]*href="[^"]*utm_content=growth_(?:home|owner)[^"]*"[^>]*>', consultation_event, src)
    if src != original:
        path.write_text(src, encoding='utf-8', newline='\n')
        return True
    return False

def main():
    posts = {'/blog/' + p['slug'] + '/': p for p in json.loads((ROOT/'data/blog-posts.json').read_text(encoding='utf-8'))['posts']}
    page_types = {p['url']: p['cta_type'] for p in json.loads((ROOT/'data/pages.json').read_text(encoding='utf-8-sig'))}
    changed = sum(apply(path, posts, page_types) for path in sorted(ROOT.rglob('*.html')) if not (set(path.relative_to(ROOT).parts) & SKIP))
    print(f'目的別の記事案内・相談導線: {changed}ページ更新 / ブログ{len(posts)}件')

if __name__ == '__main__':
    main()
