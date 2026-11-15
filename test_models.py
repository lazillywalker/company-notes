import unittest
from types import SimpleNamespace
from unittest.mock import patch
import gui
from test_timing import TimingTest

class ModelTests(TimingTest):
 def tags(self,names):return {'models':[{'name':name} for name in names]}
 def state(self):
  handler=gui.Handler.__new__(gui.Handler)
  handler.server=SimpleNamespace(server_port=8766,token='test',model='qwen3:8b')
  handler.headers={'Host':'127.0.0.1:8766'};handler.path='/api/state'
  result=[];handler.send=lambda data,status=200:result.append((status,data))
  handler.do_GET();return result[0]
 def test_state_discovers_installed_models_and_refreshes(self):
  with patch.object(gui.lab,'api',side_effect=[self.tags(['qwen3:8b',gui.TINY_SWALLOW,'new:latest',gui.TINY_SWALLOW]),self.tags(['new:latest'])]) as api:
   status,state=self.state();self.assertEqual(status,200)
   self.assertEqual(state['models'],['qwen3:8b',gui.TINY_SWALLOW,'new:latest'])
   self.assertEqual(state['model_error'],'');self.assertIn('notes',state)
   self.assertEqual(self.state()[1]['models'],['new:latest'])
   api.assert_called_with('/api/tags',timeout=2)
 def test_offline_state_and_selection(self):
  with patch.object(gui.lab,'api',side_effect=OSError('offline')):
   state=self.state()[1];self.assertTrue(state['model_error'])
   self.assertIn(gui.TINY_SWALLOW,state['models'])
   self.assertEqual(gui.selected_model(SimpleNamespace(model='qwen3:8b'),{'model':gui.TINY_SWALLOW}),gui.TINY_SWALLOW)
 def test_empty_installation(self):
  with patch.object(gui.lab,'api',return_value=self.tags([])):
   self.assertEqual(self.state()[1]['models'],[])
 def test_cloud_remote_and_unknown_rejected(self):
  tags={'models':[{'name':'local:latest'},{'name':'remote:cloud'},{'name':'proxy:latest','remote_host':'example.com'}]}
  with patch.object(gui.lab,'api',return_value=tags),patch.object(gui,'generate') as generate:
   self.assertEqual(self.state()[1]['models'],['local:latest'])
   for name in ['remote:cloud','proxy:latest','unknown',[],None]:
    self.assertEqual(self.request('/api/educate',{'text':'test','model':name})[0],400)
   generate.assert_not_called()
 def test_tinyswallow_education_and_response(self):
  with patch.object(gui.lab,'api',return_value=self.tags([gui.TINY_SWALLOW])),patch.object(gui,'retrieve',return_value=[{'id':1}]),patch.object(gui,'generate',return_value='回答') as generate:
   self.assertEqual(self.request('/api/educate',{'text':'教材案','model':gui.TINY_SWALLOW}), (200,{'answer':'回答'}))
   status,response=self.request('/api/ask',{'text':'質問','language':'ja','model':gui.TINY_SWALLOW})
   self.assertEqual(status,200);self.assertEqual(response['model'],gui.TINY_SWALLOW)
   self.assertEqual([call.args[0] for call in generate.call_args_list],[gui.TINY_SWALLOW]*2)
  with gui.connect() as db:
   self.assertEqual(db.execute('SELECT model FROM chats').fetchone()[0],gui.TINY_SWALLOW)

if __name__=='__main__':unittest.main()
