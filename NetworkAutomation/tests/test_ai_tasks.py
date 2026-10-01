import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch,Mock
from modules import ai_tasks

class TaskTests(unittest.TestCase):
    def scope(self):return {'allowed_ips':['192.0.2.1','1.1.1.1'],'devices':[{'name':'Switch','ip':'192.0.2.1'}],'cameras':[],
        'allowed_tools':['ping_ip','ping_devices','read_summary','check_wifi','check_cameras'],'max_calls':10,'max_requests':6,'deadline_seconds':300}
    def test_scope_contains_only_registered_and_explicit_ips(self):
        with patch.object(ai_tasks.tools,'read_rows',side_effect=[[{'ip':'192.0.2.1'}],[]]):
            scope=ai_tasks.make_scope('Ping 192.0.2.2 và tổng hợp')
        self.assertIn('192.0.2.2',scope['allowed_ips']);self.assertNotIn('192.0.2.3',scope['allowed_ips'])
        self.assertFalse(ai_tasks.allow(scope,'ping_ip',{'ip':'192.0.2.3'}))
    def test_report_and_steps_saved(self):
        def chat(*args,**kwargs):
            self.assertEqual(kwargs['max_requests'],6)
            self.assertTrue(args[4]('ping_ip',{'ip':'192.0.2.1'}))
            args[6]('ping_ip',{'ip':'192.0.2.1'},'{"status":"Online"}')
            return 'Thiết bị phản hồi'
        with tempfile.TemporaryDirectory() as root:
            result=ai_tasks.run_task('Kiểm tra','OpenAI','model',self.scope(),root=root,chat_fn=chat)
            self.assertEqual(result['state'],'finished');self.assertEqual(result['steps'],1)
            self.assertTrue(Path(result['report']).is_file())
            self.assertEqual(ai_tasks.task_history(root)[0]['state'],'finished')
    def test_error_produces_partial_report(self):
        def chat(*args,**kwargs):
            args[6]('read_summary',{},'{"count":2}')
            raise TimeoutError('API timeout')
        with tempfile.TemporaryDirectory() as root:
            result=ai_tasks.run_task('Check','Gemini','model',self.scope(),root=root,chat_fn=chat)
            self.assertEqual(result['state'],'failed')
            self.assertIn('API timeout',Path(result['report']).read_text())
            self.assertEqual(result['steps'],1)
    def test_cancel_records_cancelled(self):
        stop=threading.Event();stop.set()
        with tempfile.TemporaryDirectory() as root:
            result=ai_tasks.run_task('Check','OpenAI','model',self.scope(),stop=stop,root=root,chat_fn=Mock(side_effect=RuntimeError('cancel')))
            self.assertEqual(result['state'],'cancelled')
    def test_scoped_batch_does_not_read_new_targets(self):
        with patch.object(ai_tasks.tools,'ping_host',return_value={'status':'Online'}) as ping,patch.object(ai_tasks.tools,'read_rows') as rows:
            result=ai_tasks.execute_scoped(self.scope(),'ping_devices',{})
        ping.assert_called_once_with('192.0.2.1',1000);rows.assert_not_called()
        self.assertEqual(result['selected'],1)
    def test_errors_mark_review(self):
        def chat(*args,**kwargs):args[6]('ping_ip',{},'{"error":"denied"}');return 'Có lỗi'
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(ai_tasks.run_task('Check','OpenAI','model',self.scope(),root=root,chat_fn=chat)['state'],'needs_review')

class ProgressTests(unittest.TestCase):
    scope=TaskTests.scope
    def test_batch_reports_target_then_completion(self):
        updates=[]
        with patch.object(ai_tasks.tools,'ping_host',return_value={'status':'Online'}):
            ai_tasks.execute_scoped(self.scope(),'ping_devices',{},progress=lambda name,info:updates.append(info))
        self.assertEqual(updates,[{'completed':0,'total':1,'target':'192.0.2.1'},{'completed':1,'total':1,'target':''}])
    def test_progress_is_saved_before_tool_finishes(self):
        updates=[]
        def chat(*args,**kwargs):
            result=kwargs['execute_tool']('ping_devices',{},None)
            args[6]('ping_devices',{},json.dumps(result))
            return 'Completed'
        with tempfile.TemporaryDirectory() as root,patch.object(ai_tasks.tools,'ping_host',return_value={'status':'Online'}):
            result=ai_tasks.run_task('Check','OpenAI','model',self.scope(),root=root,chat_fn=chat,status_callback=lambda name,info:updates.append(info))
            record=ai_tasks.task_history(root)[0]
        self.assertEqual(result['state'],'finished')
        self.assertEqual(record['current_step']['completed'],1)
        self.assertEqual(updates[-1]['total'],1)
    def test_cancelled_batch_does_not_claim_completion(self):
        updates=[];stop=threading.Event();stop.set()
        with patch.object(ai_tasks.tools,'ping_host') as ping:
            result=ai_tasks.execute_scoped(self.scope(),'ping_devices',{},stop=stop,progress=lambda name,info:updates.append(info))
        ping.assert_not_called();self.assertTrue(result['partial']);self.assertEqual(updates[-1]['completed'],0)

if __name__=='__main__':unittest.main()
