"""Published question identity must survive unrelated source-count changes."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import build_questions as q


class SelectionTests(unittest.TestCase):
    def test_extra_qa_does_not_replace_the_published_question(self):
        content = copy.deepcopy(q.load_content())
        parent = '/life/start-living/certificates/'
        before = next(row for row in q.candidates() if row['parent_href'] == parent)
        content[parent]['qa'].insert(0, {'question': '新しい質問を候補へ追加します',
                                       'answer': '回答の条件を説明します。' * 10})
        with patch.object(q, 'load_content', return_value=content), \
             patch.object(q, 'question_rank', return_value=(-100, 0)):
            after = next(row for row in q.candidates() if row['parent_href'] == parent)
        self.assertEqual(after['question'], before['question'])
        self.assertEqual(after['answer'], before['answer'])

    def test_new_sources_cannot_displace_published_questions(self):
        selected = q.select_questions()
        extra = copy.deepcopy(selected[-1])
        extra.update(parent_href='/life/new-candidate/', slug='new-candidate', priority='P1')
        extra['sources'] = [{}] * 3
        changed = copy.deepcopy(selected) + [extra]
        for row in changed:
            row['sources'] = list(reversed(row.get('sources', [])))
        with patch.object(q, 'candidates', return_value=changed):
            after = q.select_questions()
        self.assertEqual([r['href'] for r in selected], [r['href'] for r in after])
        self.assertIn('/questions/emergency-disaster-certificates-procedures/',
                      [r['href'] for r in after])

    def test_missing_published_source_fails_explicitly(self):
        selected = q.select_questions()
        with patch.object(q, 'candidates', return_value=selected[:-1]):
            with self.assertRaisesRegex(RuntimeError, '生成元が不足'):
                q.select_questions()

    def test_duplicate_selection_fails(self):
        selected = q.select_questions()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'data').mkdir()
            hrefs = [r['parent_href'] for r in selected]
            hrefs[-1] = hrefs[0]
            (root / 'data/question-selection.json').write_text(
                json.dumps({'parent_hrefs': hrefs}), encoding='utf-8')
            with patch.object(q, 'ROOT', root), patch.object(q, 'candidates', return_value=selected):
                with self.assertRaisesRegex(RuntimeError, '重複のない100件'):
                    q.select_questions()


if __name__ == '__main__':
    unittest.main()
