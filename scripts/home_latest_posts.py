"""Keep the bounded home latest-posts list in sync during ordinary blog builds."""
import re
from html import escape


def latest_links(posts):
    return ''.join(
        f'<li><a href="/blog/{escape(p["slug"], quote=True)}/">{escape(p["title"])}</a>'
        f' <time datetime="{escape(p["date"], quote=True)}">{escape(p["date"])}</time></li>'
        for p in sorted(posts, key=lambda p: (p['date'], p['slug']), reverse=True)[:4])


def sync(html, posts):
    pattern = r'(<section\b[^>]*class="home-blog-latest"[^>]*>.*?<ul>).*?(</ul>)'
    result, count = re.subn(pattern, lambda m: m[1] + latest_links(posts) + m[2], html, flags=re.S)
    if count != 1:
        raise ValueError(f'Expected one home latest-posts list, found {count}')
    return result
