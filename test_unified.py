import json
from unittest.mock import patch
from test_timing import TimingTest
import gui
class UnifiedTest(TimingTest):
 def test_selection_and_shared_references(self):
  refs=[{'id':7,'title':'営業時間'}]
  with patch.object(gui,'retrieve',return_value=refs),patch.object(gui,'generate',side_effect=['4B回答','8B回答']) as generate:
   status,r=self.request('/api/ask',{'text':'営業時間','language':'ja','model':'qwen3:8b','compare':True})
  self.assertEqual(status,200);self.assertEqual([c.args[0] for c in generate.call_args_list],['qwen3:4b','qwen3:8b'])
  self.assertEqual(generate.call_args_list[0].args[2],generate.call_args_list[1].args[2])
  self.assertEqual(len(r['results']),2);self.assertTrue(r['comparison_id'])
  with gui.connect() as db:
   rows=db.execute('SELECT * FROM chats').fetchall();self.assertEqual(len(rows),2)
   self.assertTrue(all(x['review_state']=='unverified' for x in rows));self.assertEqual(rows[0]['comparison_id'],rows[1]['comparison_id'])
 def test_comparison_failure_rolls_back(self):
  with patch.object(gui,'retrieve',return_value=[{'id':1}]),patch.object(gui,'generate',side_effect=['first',ValueError('failed')]):
   self.assertEqual(self.request('/api/ask',{'text':'Q','compare':True})[0],400)
  with gui.connect() as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM chats').fetchone()[0],0)
 def test_no_references_comparison_and_invalid_model_rejected(self):
  self.assertEqual(self.request('/api/ask',{'text':'Q','compare':True})[0],400)
  self.assertEqual(self.request('/api/ask',{'text':'Q','model':'arbitrary'})[0],400)
 def test_old_archive_does_not_become_knowledge(self):
  with gui.connect() as db:db.execute('INSERT INTO legacy_archive VALUES(?,?,?)',('exchanges',1,json.dumps({'id':1,'question':'秘密','answer':'未検証'})))
  self.assertEqual(self.request('/api/legacy',{})[1]['rows'][0]['answer'],'未検証')
  with gui.connect() as db:self.assertEqual(gui.retrieve(db,'秘密'),[])
