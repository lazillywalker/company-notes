import io,json,sqlite3,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import gui

class TimingTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=patch.object(gui,'ROOT',Path(self.tmp.name));self.root.start()
 def tearDown(self):self.root.stop();self.tmp.cleanup()
 def request(self,path,payload):
  raw=json.dumps(dict(token='test',**payload)).encode()
  h=gui.Handler.__new__(gui.Handler);h.server=SimpleNamespace(server_port=8766,token='test',model='qwen3:8b');h.path=path
  h.headers={'Host':'127.0.0.1:8766','Origin':'http://127.0.0.1:8766','Content-Length':str(len(raw))};h.rfile=io.BytesIO(raw)
  result=[];h.send=lambda data,status=200:result.append((status,data));h.do_POST();return result[0]
 def test_legacy_migration_preserves_rows_and_unknown_timing(self):
  with sqlite3.connect(gui.ROOT/'notes.sqlite3') as d:
   d.execute('CREATE TABLE chats(id INTEGER PRIMARY KEY,question TEXT,answer TEXT,refs TEXT,created TEXT)')
   d.execute("INSERT INTO chats VALUES(1,'Q','A','[]','today')")
  for _ in range(2):
   with gui.connect() as d:
    r=dict(d.execute('SELECT * FROM chats').fetchone());self.assertEqual(r['answer'],'A');self.assertIsNone(r['elapsed_seconds']);self.assertIsNone(r['model'])
 def test_model_time_saved_and_exported(self):
  with patch.object(gui,'retrieve',return_value=[{'id':1}]),patch.object(gui,'generate',return_value='回答'),patch.object(gui.time,'perf_counter',side_effect=[10,12.3456]):
   status,r=self.request('/api/ask',{'text':'質問','language':'ja'})
  self.assertEqual(status,200);self.assertAlmostEqual(r['elapsed_seconds'],2.3456);self.assertEqual(r['model'],'qwen3:8b')
  with gui.connect() as d:
   row=dict(d.execute('SELECT * FROM chats').fetchone());self.assertEqual(row['elapsed_seconds'],r['elapsed_seconds'])
  _,export=self.request('/api/chatlogs/export',{'format':'json'})
  self.assertEqual(json.loads(export['content'])['conversations'][0]['model'],'qwen3:8b')
  _,export=self.request('/api/chatlogs/export',{'format':'txt'})
  self.assertIn('2.346',export['content']);self.assertIn('qwen3:8b',export['content'])
 def test_no_references_does_not_misreport_model(self):
  with patch.object(gui,'generate') as generate:
   status,r=self.request('/api/ask',{'text':'未知','language':'ja'})
  generate.assert_not_called();self.assertEqual(status,200);self.assertIsNone(r['model']);self.assertEqual(r['response_kind'],'no_reference');self.assertGreaterEqual(r['elapsed_seconds'],0)
 def test_failure_does_not_save_success_time(self):
  with patch.object(gui,'retrieve',return_value=[{'id':1}]),patch.object(gui,'generate',side_effect=ValueError('failed')):
   self.assertEqual(self.request('/api/ask',{'text':'質問'})[0],400)
  with gui.connect() as d:self.assertEqual(d.execute('SELECT COUNT(*) FROM chats').fetchone()[0],0)
