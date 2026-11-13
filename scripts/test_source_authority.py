import unittest
from generate_pages import source_authority, sources_html
import tempfile
from pathlib import Path
from unittest.mock import patch
import generate_pages


class SourceAuthorityTests(unittest.TestCase):
    def test_existing_summary_survives_regeneration_with_new_contact(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            page = root / 'life/test/index.html'
            page.parent.mkdir(parents=True)
            page.write_text('<!-- INSTANT-HEADER:START -->old<!-- INSTANT-HEADER:END -->', encoding='utf-8')
            item = {'href':'/life/test/', 'verified_date':'2026-07-03',
                    'facts':{'window':'担当課', 'tel':'0538-85-6312'}}
            with patch.object(generate_pages, 'ROOT', root):
                result = generate_pages.retained_instant_header(item)
                page.write_text(result, encoding='utf-8')
                self.assertEqual(generate_pages.retained_instant_header(item), result)
            self.assertIn('tel:0538-85-6312', result)
            self.assertIn('2026-07-03', result)
            self.assertNotIn('old', result)

    def test_summary_is_not_invented_for_an_unmarked_page(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(generate_pages, 'ROOT', Path(temp)):
                self.assertEqual(generate_pages.retained_instant_header({'href':'/life/test/'}), '')

    def test_source_host_cannot_be_mislabelled_as_town(self):
        self.assertEqual(source_authority('https://www.town.morimachi.shizuoka.jp/a', '森町'), '森町公式')
        self.assertEqual(source_authority('https://www.pref.shizuoka.jp/a', '森町'), '静岡県公式')
        self.assertEqual(source_authority('https://jsite.mhlw.go.jp/a', '森町'), '厚生労働省・労働局')
        self.assertEqual(source_authority('https://pref.shizuoka.jp.unrelated.test/a', '森町'), '参照先')

    def test_label_and_url_remain_escaped(self):
        html = sources_html([{'url':'https://www.pref.shizuoka.jp/?x="', 'label':'<資料>'}], '森町')
        self.assertNotIn('森町公式', html)
        self.assertIn('静岡県公式', html)
        self.assertIn('&lt;資料&gt;', html)
        self.assertIn('&quot;', html)

    def test_questions_use_the_same_authority_as_parent_guides(self):
        from build_questions import official_links
        html = official_links({'sources':[
            {'url':'https://www.pref.shizuoka.jp/a', 'label':'県の現行額'},
            {'url':'https://jsite.mhlw.go.jp/a', 'label':'相談先'}]})
        self.assertIn('静岡県公式', html)
        self.assertIn('厚生労働省・労働局', html)
        self.assertNotIn('森町公式', html)


if __name__ == '__main__':
    unittest.main()
