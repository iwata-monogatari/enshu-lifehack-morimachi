import json
import re
import unittest
from pathlib import Path
from growth_routes import group, next_reading
from apply_growth_routes import apply, FORBIDDEN

ROOT=Path(__file__).resolve().parent.parent

class RoutesTest(unittest.TestCase):
    def test_intent_before_weekday(self):
        self.assertEqual(group({'title':'森町の次郎柿直売所','axis':'tue'}),'outings')
        self.assertNotIn('fudosan.atawi.link',next_reading({'title':'森町の次郎柿直売所','axis':'tue'}))
        self.assertIn('/fudosan/buy/',next_reading({'title':'森町へ移住前の交通','axis':'sun'}))
        self.assertIn('/karte/sample/',next_reading({'title':'相続した実家の片付け','axis':'tue'}))
        self.assertNotIn('fudosan.atawi.link',next_reading({'title':'実家の空き家防火','axis':'tue'}))

    def test_generated_routes_and_idempotence(self):
        posts={'/blog/'+p['slug']+'/':p for p in json.loads((ROOT/'data/blog-posts.json').read_text(encoding='utf-8'))['posts']}
        types={p['url']:p['cta_type'] for p in json.loads((ROOT/'data/pages.json').read_text(encoding='utf-8-sig'))}
        for route in list(posts)+['/life/housing/vacant-house/','/life/housing/sell-house/','/housing/districts/']:
            path=ROOT/route.strip('/')/'index.html'
            src=path.read_text(encoding='utf-8')
            self.assertFalse(apply(path,posts,types),route)
            if route in posts:
                self.assertEqual(src.count('class="mg-next"'),1,route)
            if route=='/life/housing/vacant-house/':
                self.assertNotIn('company-strip',src)
                self.assertEqual(src.count('class="mg-next"'),1)
        for prefix in FORBIDDEN:
            path=ROOT/prefix.strip('/')/'index.html'
            if path.exists():
                self.assertNotIn('aria-label="住まいの案内"',path.read_text(encoding='utf-8'))

    def test_index_is_crawlable_without_javascript(self):
        src=(ROOT/'blog/index.html').read_text(encoding='utf-8')
        expected=len(json.loads((ROOT/'data/blog-posts.json').read_text(encoding='utf-8'))['posts'])
        self.assertEqual(len(re.findall(r'<li class="post-item" data-topic=',src)),expected)
        self.assertNotRegex(src,r'<li class="post-item"[^>]*hidden')
        for group in ('outings','living','family'):
            self.assertIn('href="#'+group+'"',src)

if __name__=='__main__': unittest.main()
