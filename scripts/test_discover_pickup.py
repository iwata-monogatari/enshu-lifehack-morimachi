import hashlib,json,subprocess,sys,unittest,tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent))
import build_discover as build

class DiscoverSeasonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=json.loads(build.DATA.read_text(encoding='utf-8'))['pages']

    def test_date_boundaries_and_labels(self):
        for day,slug,label in [
            ('2026-10-31','mori-festival','10月の1本'),
            ('2026-11-01','mori-festival','2026年11月6〜8日の催し'),
            ('2026-11-05','mori-festival','2026年11月6〜8日の催し'),
            ('2026-11-08','mori-festival','2026年11月6〜8日の催し'),
            ('2026-11-09','oguni-shrine-autumn-leaves','11月の1本'),
            ('2027-11-05','oguni-shrine-autumn-leaves','11月の1本')]:
            with self.subTest(day=day):
                target=date.fromisoformat(day)
                selected=build.pickup_slugs(target)
                self.assertEqual(selected[0],slug)
                self.assertEqual(len(selected),8)
                self.assertEqual(len(set(selected)),8)
                rendered=build.index_html(self.rows,target)
                self.assertIn(f'class="pickup-feature" href="/discover/{slug}/"',rendered)
                self.assertIn(f'<small>{label}</small>',rendered)
                self.assertIn(f'data-pickup-date="{day}"',rendered)
                self.assertIn(f'data-pickup-month="{target.month}"',rendered)

    def test_default_resolves_jst_once(self):
        with patch.object(build,'jst_today',side_effect=[date(2026,11,8),date(2026,11,9)]) as clock:
            rendered=build.index_html(self.rows)
            self.assertIn('2026年11月6〜8日の催し',rendered)
            self.assertIn('data-pickup-date="2026-11-08"',rendered)
            self.assertEqual(clock.call_count,1)

    def test_index_only_preserves_articles_and_images(self):
        def hashes():
            return {str(p.relative_to(build.OUT)):hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in build.OUT.rglob('*') if p.is_file() and p != build.OUT/'index.html'}
        before=hashes()
        subprocess.run([sys.executable,str(Path(build.__file__)),'--index-only'],check=True)
        first=(build.OUT/'index.html').read_bytes()
        subprocess.run([sys.executable,str(Path(build.__file__)),'--index-only'],check=True)
        self.assertEqual(first,(build.OUT/'index.html').read_bytes())
        self.assertEqual(before,hashes())
        self.assertEqual(len(before),800)

if __name__=='__main__':unittest.main()
