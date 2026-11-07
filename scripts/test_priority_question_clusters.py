import json
import unittest
from inject_priority_question_clusters import ROOT, select_questions


class PriorityQuestionsTest(unittest.TestCase):
    def test_garbage_recommendations_do_not_fill_with_unrelated_procedures(self):
        rows = json.loads((ROOT / 'data/questions.json').read_text(encoding='utf-8'))
        pages = json.loads((ROOT / 'data/search-priority-pages.json').read_text(encoding='utf-8'))
        item = next(x for x in pages if x['href'] == '/life/start-living/how-to-garbage/')
        for index in range(len(pages) + 1):
            selected = select_questions(item, list(reversed(rows)), index)
            self.assertEqual(len(selected), 2)
            self.assertTrue(all('garbage' in x['parent_href'] for x in selected))

    def test_hazard_recommendations_stay_on_disaster_topics(self):
        rows = json.loads((ROOT / 'data/questions.json').read_text(encoding='utf-8'))
        pages = json.loads((ROOT / 'data/search-priority-pages.json').read_text(encoding='utf-8'))
        item = next(x for x in pages if x['href'] == '/life/emergency/evacuation-hazard-map/')
        for index in range(len(pages) + 1):
            selected = select_questions(item, rows, index)
            self.assertEqual(len(selected), 5)
            self.assertEqual(selected[0]['href'], '/questions/emergency-evacuation-hazard-map/')
            self.assertIn('/questions/emergency-evacuation-centers/', [x['href'] for x in selected])
            self.assertTrue(all(x['parent_href'].startswith('/life/emergency/') for x in selected))

    def test_broken_explicit_reference_fails_before_publication(self):
        with self.assertRaises(ValueError):
            select_questions({'href': '/example/', 'question_hrefs': ['/missing/']}, [], 0)
        with self.assertRaises(ValueError):
            select_questions({'href': '/example/', 'question_hrefs': ['/a/', '/a/']}, [{'href': '/a/'}], 0)


if __name__ == '__main__':
    unittest.main()
