import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from update import parse,row,EXCLUDED
from build import e
class Sources(unittest.TestCase):
    def test_mlb_empty(self): self.assertEqual(parse('Baseball','MLB',{'dates':[]},'https://statsapi.mlb.com'),[])
    def test_missing_is_rejected(self):
        with self.assertRaises(ValueError): row('Baseball','MLB',1,'A','B','',None,'https://statsapi.mlb.com')
    def test_invalid_date_rejected(self):
        with self.assertRaises(ValueError): row('Baseball','MLB',1,'A','B','tomorrow',None,'https://statsapi.mlb.com')
    def test_blanks(self):
        r=row('Baseball','MLB',1,'A','B','2026-10-21T19:00:00Z','Scheduled','https://statsapi.mlb.com')
        for field in ['winner','confidence','line','handicap','total','prediction','form','history']: self.assertIsNone(r[field])
    def test_escape(self): self.assertEqual(e('<script>'), '&lt;script&gt;')
    def test_exclusions(self):
        for sport in ['soccer','boxing','ufc','mma','football','american football','hurling','horse racing','cycling','specials']: self.assertIn(sport,EXCLUDED)
    def test_schema_failure(self):
        with self.assertRaises(KeyError): parse('Ice hockey','NHL',{},'https://api-web.nhle.com')
    def test_mlb_parse(self):
        g={'gamePk':123,'gameDate':'2026-10-21T19:00:00Z','teams':{'away':{'team':{'name':'Away'}},'home':{'team':{'name':'Home'}}},'status':{'detailedState':'Scheduled'}}
        r=parse('Baseball','MLB',{'dates':[{'games':[g]}]},'https://statsapi.mlb.com')[0]
        self.assertEqual(r['home'],'Home');self.assertEqual(r['id'],'MLB-123')
if __name__=='__main__': unittest.main()
