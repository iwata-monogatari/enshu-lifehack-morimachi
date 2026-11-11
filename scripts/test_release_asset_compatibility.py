import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import audit_discover
import build_blog
import preflight_check


class ReleaseCompatibilityTest(unittest.TestCase):
    def test_svg_cover_is_kept_and_missing_cover_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            post = root / 'example'
            post.mkdir()
            (post / 'index.html').write_text('<h1>例</h1>', encoding='utf-8')
            (post / 'cover.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
            with patch.object(build_blog, 'BLOG_DIR', tmp):
                errors = build_blog.audit([{'slug': 'example', 'title': '例'}])
                self.assertFalse(any('表紙' in message for _, message in errors))
                (post / 'cover.svg').unlink()
                errors = build_blog.audit([{'slug': 'example', 'title': '例'}])
                self.assertTrue(any('表紙' in message for _, message in errors))

    def test_photograph_wrapper_requires_a_real_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            svg = root / 'fig1.svg'
            for href, expected in [('data:image/jpeg;base64,/9j/AA==', True),
                                   ('data:image/jpeg;base64,bm90YW5pbWFnZQ==', False),
                                   ('data:image/jpeg;base64,invalid!', False),
                                   ('missing.jpg', False)]:
                svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg"><image href="{href}"/></svg>')
                self.assertEqual(audit_discover.is_local_photo(svg, root), expected)
            svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"><text>図</text></svg>')
            self.assertFalse(audit_discover.is_local_photo(svg, root))

    def test_seal_check_distinguishes_medical_and_family_register_forms(self):
        for heading, expected in [('後期高齢者医療の申請', False), ('出生届の手続き', True)]:
            errors = []
            with patch.object(preflight_check, 'ALL', {'/example/': f'<h1>{heading}</h1><p>印鑑を持参してください</p>'}), patch.object(preflight_check, 'errors', errors), contextlib.redirect_stdout(io.StringIO()):
                preflight_check.check_forbidden_terms()
            self.assertEqual(any('押印必須' in message for message in errors), expected)


if __name__ == '__main__':
    unittest.main()
