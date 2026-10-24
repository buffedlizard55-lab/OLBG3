import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import probe_cited


class ProbeSourceTests(unittest.TestCase):
    def test_pdf_is_preserved_byte_for_byte(self):
        body = b'%PDF-1.7\n%\xff\xfe\xfd\x00\nendobj\n'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'pages').mkdir()
            entry = probe_cited.save_response(root, 'test', body, 'application/pdf', 'https://example.org/a.pdf')
            self.assertEqual(entry['representation'], 'verbatim_binary')
            self.assertEqual((root / entry['file']).read_bytes(), body)
            self.assertEqual(hashlib.sha256((root / entry['file']).read_bytes()).digest(), hashlib.sha256(body).digest())

    def test_json_is_not_decoded_as_html(self):
        body = b'{"text":"<p>literal</p>"}'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'pages').mkdir()
            entry = probe_cited.save_response(root, 'test', body, 'application/json', 'https://example.org/api')
            self.assertEqual((root / entry['file']).read_bytes(), body)

    def test_additional_sources_require_explicit_official_host(self):
        good = 'https://www.legavolley.it/classifica/?IdCampionato=999'
        self.assertEqual(probe_cited.extra_urls({'cited_urls': [good]}), [good])
        for bad in ('http://www.legavolley.it/', 'https://www.legavolley.it.attacker.example/',
                    'https://user@www.legavolley.it/', 'https://www.olbg.com/'):
            with self.assertRaises(ValueError):
                probe_cited.extra_urls({'cited_urls': [bad]})
