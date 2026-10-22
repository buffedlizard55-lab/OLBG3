"""Local publication checks must cover both Pages publishers, not source URLs."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_links import check_tree


class PublicationLinks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def put(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')

    def test_committed_secondary_track_is_checked_without_artifact(self):
        self.put('index.html', '<p>ok</p>')
        self.put('olbg/sports/tennis.html', "<a href='../missing.html'>bad</a>")
        pages, checked, errors = check_tree(self.root)
        self.assertEqual((pages, checked, len(errors)), (2, 1, 1))
        self.assertEqual(errors[0][0], 'olbg/sports/tennis.html')

    def test_fragments_decoding_and_legacy_named_anchors(self):
        self.put('index.html', """<a href='#a%20b'>ok</a><div id='a b'></div>
            <a href='other.html?x=1&amp;y=2#old'>ok</a><a href='#absent'>bad</a>
            <a href='#:~:text=hello'>text fragment</a>""")
        self.put('other.html', '<a name="old"></a>')
        _, _, errors = check_tree(self.root)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0][2], 'missing fragment ID')

    def test_artifact_cannot_borrow_files_from_legacy_root(self):
        self.put('only-root.html', '<p>legacy</p>')
        self.put('site/index.html', "<a href='../only-root.html'>bad</a>")
        self.assertEqual(check_tree(self.root)[2][0][2], 'escapes publication root')

    def test_directory_links_require_index_and_project_base_is_supported(self):
        self.put('index.html', """<a href='olbg/'>ok</a><a href='/OLBG3/olbg/#ok'>ok</a>
            <a href='empty/'>bad</a><a href='/outside.html'>bad</a>""")
        self.put('olbg/index.html', '<p id="ok">ok</p>')
        (self.root / 'empty').mkdir()
        self.assertEqual(len(check_tree(self.root)[2]), 2)

    def test_external_links_are_not_claimed_verified(self):
        self.put('index.html', """<a href='https://www.olbg.com/'>external</a>
            <a href='//example.com/'>external</a><a href='mailto:a@example.com'>mail</a>
            <img src='data:image/png;base64,abc'><a href='https://[bad'>malformed</a>""")
        _, checked, errors = check_tree(self.root)
        self.assertEqual(checked, 0)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0][2], 'malformed URL')

    def test_site_and_legacy_project_paths_are_separate(self):
        self.put('index.html', '<p id="legacy">legacy</p>')
        self.put('site/index.html', '<a href="/OLBG3/#artifact">ok</a><p id="artifact">ok</p>')
        self.assertEqual(check_tree(self.root)[2], [])


if __name__ == '__main__':
    unittest.main()
