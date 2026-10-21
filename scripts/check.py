"""Validate generated internal links, data provenance and safe blank predictions."""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
class Links(HTMLParser):
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k in ('href','src') and v and not urlparse(v).scheme and not v.startswith('#'):
                assert (ROOT/'site'/v.split('#')[0]).is_file(), f'Broken local link {v}'
def main():
    d=json.loads((ROOT/'site/data.json').read_text())
    allowed={'api-web.nhle.com','statsapi.mlb.com','cdn.nba.com'}
    assert len({r['id'] for r in d['matches']})==len(d['matches'])
    for r in d['matches']:
        assert urlparse(r['source']).hostname in allowed
        assert r['sport'].lower() not in d['excluded']
        for field in ['winner','confidence','line','handicap','total','prediction','form','history']:
            assert r[field] is None, f'Unvalidated betting field: {field}'
    for file in (ROOT/'site').glob('*.html'): Links().feed(file.read_text())
    print(f'PASS: {len(d["matches"])} fixture rows; official hosts, blank betting fields, unique IDs and all internal links checked.')
if __name__=='__main__': main()
