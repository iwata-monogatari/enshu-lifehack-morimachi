"""Reviewed procedure exits stay independent of the blog index and weekdays."""
import json
from pathlib import Path
import unittest
from bs4 import BeautifulSoup
from growth_routes import READER_ROUTES, group, next_reading

ROOT = Path(__file__).resolve().parents[1]


class ReaderRoutesTest(unittest.TestCase):
    def test_reviewed_targets_and_regeneration(self):
        posts = {p['slug']: p for p in json.loads((ROOT/'data/blog-posts.json').read_text(encoding='utf-8'))['posts']}
        for slug, route in READER_ROUTES.items():
            with self.subTest(slug=slug):
                post = posts[slug]
                block = BeautifulSoup(next_reading(post), 'html.parser')
                self.assertEqual(block.select_one('aside')['data-reader-route'], 'procedure')
                self.assertNotIn('次のお出かけも', block.get_text())
                self.assertEqual(block.select_one('a')['href'], route['href'])
                page = BeautifulSoup((ROOT/'blog'/slug/'index.html').read_text(encoding='utf-8'), 'html.parser')
                self.assertTrue(page.select_one('link[href^="/assets/growth.css?"]'))
                self.assertEqual(str(page.select_one('.action-grid .mg-next')), str(block.aside))
                if route['href'].startswith('/'):
                    self.assertTrue((ROOT/route['href'].strip('/')/'index.html').exists())
                else:
                    page.select_one('.action-grid').decompose()
                    self.assertTrue(any(a.get('href')==route['href'] for a in page.select('a[href]')), 'Official destination must already be an article source')

    def test_index_and_genuine_outing_are_preserved(self):
        for weekday in ['wed','sat']:
            self.assertEqual(group({'title':'森町のパスポート申請','axis':weekday}), 'outings')
        for slug,title in [('20261003-morimachi-kanko-walk','森町観光ウォーク2026｜申込み前の確認事項'),('20261001-morimachi-jirogaki-chokubaijo','森町の次郎柿直売所')]:
            self.assertIn('次のお出かけも', next_reading({'slug':slug,'title':title,'axis':'sat'}))
        self.assertNotIn('次のお出かけも', next_reading({'title':'森町の救急医療','axis':'sat'}))


if __name__ == '__main__':
    unittest.main()
