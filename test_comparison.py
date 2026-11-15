import io,json,threading,time,unittest
from unittest.mock import patch
from test_timing import TimingTest
import comparison as c
import gui

class ComparisonTests(TimingTest):
 def test_split_native_inline_and_implicit(self):
  for raw,native,answer,thinking in [('答え','思考','答え','思考'),('<think>思考</think>答え','','答え','思考'),('思考</think>答え','','答え','思考'),('<think>未完','','','未完')]:
   a,t,_=c.split_output(raw,native);self.assertEqual((a,t),(answer,thinking))
 def test_stream_measures_answer_after_split_tag(self):
  events=[{'message':{'content':'<thi'}},{'message':{'content':'nk>検討</think>'}},{'message':{'content':'回答 [#7]'}},{'done':True,'done_reason':'stop','eval_count':20,'eval_duration':2_000_000_000,'load_duration':1000000}]
  response=io.BytesIO(b'\n'.join(json.dumps(e).encode() for e in events))
  with patch('comparison.urllib.request.build_opener') as opener,patch('comparison.time.perf_counter',side_effect=[0,1,2,3,4,5]):
   opener.return_value.open.return_value=response
   r=c.stream('fake',[],{},'off')
  self.assertEqual(r['first_output_seconds'],1);self.assertEqual(r['first_answer_seconds'],3)
  self.assertEqual(r['thinking'],'検討');self.assertEqual(r['answer'],'回答 [#7]');self.assertEqual(r['tokens_per_second'],10)
 def test_stream_disconnect_not_success(self):
  with patch('comparison.urllib.request.build_opener') as opener:
   opener.return_value.open.return_value=io.BytesIO(b'{"message":{"content":"partial"}}\n')
   with self.assertRaisesRegex(ValueError,'切断'):c.stream('fake',[],{},'default')
 def test_worker_shared_prompt_partial_failure_and_reviews(self):
  refs=[{'id':7,'title':'教材','ja':'本文'}]
  def fake_api(path,body=None):return {'models':[]} if path=='/api/ps' else {'load_duration':1000000}
  def fake_stream(model,messages,options,think):
   if model=='qwen3:8b':raise ValueError('test failure')
   return {'answer':'回答 [#教材ID:7] [#99]','status':'ok'}
  with patch.object(c.lab,'model_info',return_value={'name':'test'}),patch.object(c.lab,'api',side_effect=fake_api),patch.object(c,'stream',side_effect=fake_stream) as stream,patch.object(gui,'retrieve',return_value=refs):
   status,r=self.request('/api/comparison/start',{'question':'質問','expected':'秘密の評価基準','num_ctx':16384})
   self.assertEqual(status,200)
   for _ in range(100):
    _,run=self.request('/api/comparison/get',{'id':r['id']})
    if run['status']!='running':break
    time.sleep(.01)
  self.assertEqual(run['status'],'complete');self.assertEqual(len(run['results']),3)
  self.assertEqual(run['results'][1]['status'],'error');self.assertEqual(run['results'][0]['unknown_citations'],['99'])
  self.assertEqual(stream.call_args_list[0].args[1],stream.call_args_list[2].args[1])
  self.assertNotIn('秘密の評価基準',json.dumps(run['messages'],ensure_ascii=False))
  _,reviewed=self.request('/api/comparison/review',{'id':r['id'],'model':c.MODELS[0],'review':{'accuracy':'correct','references':'supported','comment':'確認済み'}})
  self.assertEqual(reviewed['results'][0]['review']['accuracy'],'correct')
  with gui.connect() as db:self.assertEqual(db.execute('select count(*) from chats').fetchone()[0],0)
 def test_busy_and_context_validation(self):
  with patch.object(gui,'retrieve',return_value=[{'id':1,'ja':'長'*3000}]):
   self.assertEqual(self.request('/api/comparison/start',{'question':'Q'})[0],400)
  with patch.object(gui,'retrieve',return_value=[{'id':1}]):
   gui.GENERATION_LOCK.acquire()
   try:self.assertEqual(self.request('/api/comparison/start',{'question':'Q'})[0],400)
   finally:gui.GENERATION_LOCK.release()
 def test_interrupted_and_missing_refs(self):
  self.assertEqual(self.request('/api/comparison/start',{'question':'Q'})[0],400)
  c.save(gui.connect,{'id':'old','created':'date','status':'running','results':[]})
  self.assertEqual(self.request('/api/comparison/get',{'id':'old'})[1]['status'],'interrupted')
if __name__=='__main__':unittest.main()
