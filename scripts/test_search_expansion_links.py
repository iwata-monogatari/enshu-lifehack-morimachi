import json
import unittest
from bs4 import BeautifulSoup
from build_search_expansion_pages import DATA, render


class PowerLinksTest(unittest.TestCase):
    def test_power_answer_has_action_and_named_related_destinations(self):
        item = next(x for x in json.loads(DATA.read_text(encoding='utf-8')) if x['href'] == '/life/emergency/power-outage/')
        soup = BeautifulSoup(render(item), 'html.parser')
        self.assertEqual(soup.select_one('.hero-body a')['href'], 'https://teiden.powergrid.chuden.co.jp/p/sizuoka.html')
        self.assertEqual(len(soup.select('.qa details')), 3)
        self.assertIn('数秒の停電', soup.select('.qa details')[-1].get_text())
        self.assertIn('表示がないことだけでは判断できません', soup.select('.qa details')[-1].get_text())
        for href, label in item['related_labels'].items():
            self.assertEqual(soup.select_one(f'a[href="{href}"]').get_text(), label)

    def test_optional_fields_do_not_replace_default_related_labels(self):
        item = next(x for x in json.loads(DATA.read_text(encoding='utf-8')) if x['href'] == '/life/emergency/power-outage/')
        for key in ['lead_actions', 'revision_note', 'related_labels']:
            item.pop(key)
        soup = BeautifulSoup(render(item), 'html.parser')
        self.assertFalse(soup.select('.hero-body a'))
        self.assertIn('関連ガイドを確認する', soup.select_one('a[href="/life/emergency/disaster-mail-line/"]').get_text())


if __name__ == '__main__':
    unittest.main()
