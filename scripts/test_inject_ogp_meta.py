import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import inject_ogp_meta as ogp


class CanonicalInjectionTest(unittest.TestCase):
    def test_existing_and_managed_canonicals_remain_single_on_rebuild(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            expected = {}
            for slug, external in (("external", True), ("managed", False)):
                page = root / "life" / "example" / slug / "index.html"
                page.parent.mkdir(parents=True)
                url = f"{ogp.SITE_ORIGIN}/life/example/{slug}/"
                canonical = f'<link rel="canonical" href="{url}">'
                outside = canonical if external else ""
                page.write_text(
                    f'<html><head><title>Example | Site</title><meta name="description" content="Example">'
                    f'{outside}{ogp.START}{canonical}{ogp.END}<link rel="icon" href="/favicon.svg">'
                    '</head><body></body></html>', encoding="utf-8"
                )
                expected[page] = url
            with patch.object(ogp, "ROOT", str(root)), patch.object(sys, "argv", ["inject_ogp_meta.py"]):
                for _ in range(2):
                    with contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(ogp.main(), 0)
                    for page, url in expected.items():
                        matches = ogp.CANONICAL_RE.findall(page.read_text(encoding="utf-8"))
                        self.assertEqual(matches, [f'<link rel="canonical" href="{url}">'])


if __name__ == "__main__":
    unittest.main()
