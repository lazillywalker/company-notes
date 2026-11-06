import json,tempfile,unittest
from pathlib import Path
import gui
class NotesTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.old=gui.ROOT;gui.ROOT=Path(self.tmp.name)
 def tearDown(self):gui.ROOT=self.old;self.tmp.cleanup()
 def note(self,**kw):
  return gui.validate(dict(title='営業時間 opening hours',ja='営業時間は10時から18時',en='Opening hours are 10 to 18',category=0,visibility='public',**kw))
 def add(self,n,state='approved',rev=1):
  with gui.connect() as d:d.execute('INSERT INTO notes(item,revision,state,content) VALUES(?,?,?,?)',('hours',rev,state,json.dumps(n)))
 def test_bilingual(self):
  self.add(self.note())
  with gui.connect() as d:
   self.assertEqual(len(gui.retrieve(d,'営業時間')),1);self.assertEqual(len(gui.retrieve(d,'opening hours')),1)
 def test_expired(self):
  self.add(self.note(end='2000-01-01'))
  with gui.connect() as d:self.assertEqual(gui.retrieve(d,'営業時間'),[])
 def test_draft_supersedes(self):
  self.add(self.note());self.add(self.note(),'draft',2)
  with gui.connect() as d:self.assertEqual(gui.retrieve(d,'営業時間'),[])
 def test_internal(self):
  n=self.note();n['visibility']='internal';self.add(n)
  with gui.connect() as d:self.assertEqual(gui.retrieve(d,'営業時間'),[])
 def test_invalid_dates(self):
  with self.assertRaises(ValueError):self.note(start='2027-01-01',end='2026-01-01')
 def test_correction_not_evidence(self):
  n=self.note();n['category']=4;self.add(n)
  with gui.connect() as d:self.assertEqual(gui.retrieve(d,'営業時間'),[])
class HoursTest(NotesTest):
 def hours(self):
  return {d:{'status':'closed','periods':[]} for d in gui.DAYS}
 def test_seven_days_and_store(self):
  h=self.hours();h['mon']={'status':'open','periods':[['09:00','12:00'],['13:00','18:00']]}
  n=self.note(scope='本店',weekly_hours=h);self.add(n)
  with gui.connect() as d:self.assertEqual(gui.retrieve(d,'本店の営業時間')[0]['weekly_hours'],h)
 def test_missing_day(self):
  h=self.hours();del h['sun']
  with self.assertRaises(ValueError):self.note(scope='本店',weekly_hours=h)
 def test_reversed_time(self):
  h=self.hours();h['mon']={'status':'open','periods':[['18:00','09:00']]}
  with self.assertRaises(ValueError):self.note(scope='本店',weekly_hours=h)
 def test_closed_with_hours(self):
  h=self.hours();h['mon']['periods']=[['09:00','18:00']]
  with self.assertRaises(ValueError):self.note(scope='本店',weekly_hours=h)
 def test_missing_store(self):
  with self.assertRaises(ValueError):self.note(weekly_hours=self.hours())
 def test_all_day(self):
  h=self.hours();h['sun']={'status':'open','periods':[['00:00','24:00']]}
  self.note(scope='本店',weekly_hours=h)
class AnswerTextTest(unittest.TestCase):
 def test_plain(self):self.assertEqual(gui.answer_text(' 営業時間は17時までです。 ','stop'),'営業時間は17時までです。')
 def test_complete_block(self):self.assertEqual(gui.answer_text('<think>internal text</think>17時までです。','stop'),'17時までです。')
 def test_multiple_nested(self):self.assertEqual(gui.answer_text('<THINK>a<think>b</think>c</THINK>Answer<think>d</think>','stop'),'Answer')
 def test_unclosed(self):
  with self.assertRaises(ValueError):gui.answer_text('<think>unfinished','stop')
 def test_implicit_open(self):
  self.assertEqual(gui.answer_text('internal text</think>answer','stop'),'answer')
 def test_empty_implicit_thinking(self):
  self.assertEqual(gui.answer_text('</think>回答','stop'),'回答')
 def test_implicit_without_answer(self):
  with self.assertRaises(ValueError):gui.answer_text('internal</think>','stop')
 def test_extra_closing_tag(self):
  with self.assertRaises(ValueError):gui.answer_text('internal</think>answer</think>','stop')
 def test_no_answer(self):
  with self.assertRaises(ValueError):gui.answer_text('<think>only</think>','stop')
 def test_truncated(self):
  with self.assertRaises(ValueError):gui.answer_text('<think>text</think>partial','length')
 def test_generate(self):
  from unittest.mock import patch
  with patch('gui.lab.model_info'),patch('gui.lab.api',return_value={'message':{'content':'<think>internal</think>Final'},'done_reason':'stop'}):
   self.assertEqual(gui.generate('test','system','question'),'Final')
class LogDeletionTest(NotesTest):
 def request_delete(self,payload):
  import io
  from types import SimpleNamespace
  raw=json.dumps(dict(token='test',**payload)).encode()
  h=gui.Handler.__new__(gui.Handler);h.server=SimpleNamespace(server_port=8766,token='test');h.path='/api/chatlogs/delete'
  h.headers={'Host':'127.0.0.1:8766','Origin':'http://127.0.0.1:8766','Content-Length':str(len(raw))};h.rfile=io.BytesIO(raw)
  result=[];h.send=lambda data,status=200:result.append((status,data));h.do_POST();return result[0]
 def test_delete_boundaries(self):
  self.add(self.note())
  with gui.connect() as d:
   for i in range(2):d.execute('INSERT INTO chats(question,answer,refs,created) VALUES(?,?,?,?)',('Q','A','[]','today'))
  self.assertEqual(self.request_delete({'id':1}),(200,{'deleted':1}))
  self.assertEqual(self.request_delete({'all':True})[0],400)
  with gui.connect() as d:self.assertEqual(d.execute('SELECT COUNT(*) FROM chats').fetchone()[0],1)
  self.assertEqual(self.request_delete({'all':True,'confirmation':'DELETE_ALL_RESPONSE_LOGS'}),(200,{'deleted':1}))
  with gui.connect() as d:
   self.assertEqual(d.execute('SELECT COUNT(*) FROM chats').fetchone()[0],0)
   self.assertEqual(d.execute('SELECT COUNT(*) FROM notes').fetchone()[0],1)
if __name__=='__main__':unittest.main()
