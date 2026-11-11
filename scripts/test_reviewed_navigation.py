import json
import unittest
from pathlib import Path
from home_latest_posts import sync
from repair_external_links import repair, NOTICE
from build_official_updates import source_link
from sync_content_descriptions import shorten

ROOT = Path(__file__).resolve().parents[1]


class ReviewedNavigationTests(unittest.TestCase):
    def test_new_blog_enters_home_without_rebuilding_other_sections(self):
        html = '<header>keep</header><section class="home-blog-latest"><h2>新着</h2><ul>old</ul></section><footer>keep</footer>'
        posts = [{'slug':str(i),'date':f'2026-11-{i:02}','title':'<&'+str(i)} for i in range(1,7)]
        after=sync(html,posts)
        self.assertTrue(after.startswith('<header>keep</header>'))
        self.assertTrue(after.endswith('<footer>keep</footer>'))
        self.assertEqual(after.count('<li>'),4)
        self.assertLess(after.index('/blog/6/'),after.index('/blog/5/'))
        self.assertNotIn('/blog/2/',after)
        self.assertIn('&lt;&amp;6',after)
        self.assertEqual(sync(after,posts),after)

    def test_missing_home_boundary_fails_instead_of_overwriting(self):
        with self.assertRaises(ValueError):sync('<main>keep</main>',[])

    def test_archive_is_distinct_from_replacement_and_idempotent(self):
        rules={'https://old.test/a.pdf':{'mode':'archive','replacement_url':'https://new.test/list','label':'現行資料一覧'}}
        original='<main><a href="https://old.test/a.pdf">当時の要綱</a><a href="/keep/">keep</a></main>'
        after,counts=repair(original,rules)
        self.assertNotIn('href="https://old.test',after)
        self.assertIn('当時の要綱（旧リンク',after)
        self.assertIn('別の現行案内',after)
        self.assertIn('<a href="/keep/">keep</a>',after)
        self.assertEqual(sum(counts.values()),1)
        self.assertEqual(repair(after,rules)[0],after)

    def test_redirect_annotation_refreshes_without_duplicate_history(self):
        old='https://old.test/article'
        rules={old:{'mode':'archive','replacement_url':'https://new.test/','label':'現在のお知らせ','reason':'redirects_to_home'}}
        after,_=repair('<main><a href="'+old+'">当時の募集</a></main>',rules)
        self.assertIn('公式トップへ転送',after)
        self.assertEqual(repair(after,rules)[0],after)
        rules[old]['label']='現在の公式確認先'
        updated,_=repair(after,rules)
        self.assertIn('現在の公式確認先',updated)
        self.assertEqual(updated.count('公式トップへ転送'),1)

    def test_stop_notice_is_once_and_existing_official_notice_is_preserved(self):
        h='<main><a href="https://www.mori-kanko.jp/place">x</a></main>'
        a,_=repair(h,{})
        self.assertEqual(a.count(NOTICE),1)
        self.assertEqual(repair(a,{})[0],a)
        existing=h.replace('</main>','<a href="https://www.town.morimachi.shizuoka.jp/gyosei/kanko_bunka/kanko/7109.html">停止案内</a></main>')
        self.assertEqual(repair(existing,{})[0],existing)

    def test_retired_update_does_not_offer_deleted_registration_link(self):
        self.assertNotIn('<a',source_link({'source_unavailable':True}))

    def test_every_reviewed_replacement_has_explicit_label_and_mode(self):
        rules=json.loads((ROOT/'data/external-link-repairs.json').read_text(encoding='utf8'))['repairs']
        self.assertGreaterEqual(len(rules),55)
        for old,e in rules.items():
            self.assertNotEqual(old,e['replacement_url'])
            self.assertIn(e['mode'],['archive','direct'])
            self.assertTrue(e['label'])

    def test_metadata_keeps_a_complete_sentence_when_it_fits(self):
        sentence='あ'*99+'。'
        self.assertEqual(shorten(sentence+'続き'*40),sentence)
        self.assertTrue(shorten('あ'*150).endswith('…'))
        self.assertEqual(shorten('短い説明です。'),'短い説明です。')

    def test_school_support_is_consistent_in_the_answer_and_action(self):
        rows=json.loads((ROOT/'data/content/education.json').read_text(encoding='utf8'))
        row=next(x for x in rows if x['href']=='/life/education/school-meals/')
        self.assertEqual(len(row['qa']),4)
        answer=next(x['answer'] for x in row['qa'] if x['question']=='給食費の無償化や補助はありますか')
        self.assertIn('小学校給食費の無償化',answer)
        self.assertIn('一部補助',answer)
        self.assertTrue(row['lead_actions'][0]['href'].endswith('/6651.html'))
        self.assertNotIn('実施状況は公式サイトで未確認',json.dumps(row,ensure_ascii=False))
        self.assertTrue(all(x['icon'] for x in row['real_cards']))

    def test_retired_citations_do_not_qualify_a_new_article(self):
        from build_blog import official_source_urls
        live = "https://www.town.morimachi.shizuoka.jp/current.html"
        retired = "https://www.town.morimachi.shizuoka.jp/retired.html"
        markup = f'<a href="{live}">current</a><span data-retired-url="{retired}">archive</span>'
        reviewed = {retired: {"mode": "archive"}}
        self.assertEqual(official_source_urls(markup, "20261112-new-article", reviewed), {live})
        self.assertEqual(official_source_urls(markup, "20260917-nosagyo-hitorishigoto-renraku", reviewed), {live, retired})
        self.assertEqual(official_source_urls(markup, "20260917-nosagyo-hitorishigoto-renraku", {}), {live})

    def test_related_links_cannot_create_a_procedure_channel(self):
        import tempfile
        from unittest.mock import patch
        import derive_channel_fields as derive
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'data').mkdir()
            target=root/'life/test';target.mkdir(parents=True)
            (target/'index.html').write_text('<main>電子申請はありません。</main><aside>関連記事：コンビニ交付・オンライン申請</aside>',encoding='utf8')
            (root/'data/topics_master.json').write_text(json.dumps([{'href':'/life/test/','facts':{'window':'担当窓口','tel':'0538-00-0000'}}]),encoding='utf8')
            (root/'data/channel-evidence.json').write_text('{}',encoding='utf8')
            with patch.object(derive,'ROOT',str(root)),patch.object(derive,'OUT',str(root/'data/channels.json')):
                self.assertEqual(derive.main(),0)
            row=json.loads((root/'data/channels.json').read_text(encoding='utf8'))[0]
            self.assertEqual(row['channels'],['counter','phone'])


if __name__=='__main__':unittest.main()
