import json
import threading
import unittest
from unittest.mock import Mock,patch
from modules import assistant_agent as agent
from modules import assistant_tools as local

class AssistantAgentTests(unittest.TestCase):
    def test_openai_approved_tool_roundtrip(self):
        first={'output':[{'type':'reasoning','id':'reasoning'}, {'type':'function_call','name':'ping_ip','arguments':'{"ip":"192.0.2.1"}','call_id':'call1'}]}
        last={'output':[{'type':'message','content':[{'type':'output_text','text':'done'}]}]}
        transport=Mock(side_effect=[first,last]);approve=Mock(return_value=True)
        with patch.dict(agent.os.environ,{'OPENAI_API_KEY':'test'}),patch.object(local,'execute',return_value={'status':'Online'}) as execute:
            self.assertEqual(agent.chat('OpenAI','model','ping',approve=approve,transport=transport),'done')
        execute.assert_called_once_with('ping_ip',{'ip':'192.0.2.1'},None)
        second=transport.call_args_list[1].args[1]['input']
        self.assertIn(first['output'][0],second)
        self.assertEqual(second[-1]['call_id'],'call1')
        self.assertEqual(second[-1]['type'],'function_call_output')

    def test_denied_tool_never_executes(self):
        response={'output':[{'type':'function_call','name':'read_summary','arguments':'{}','call_id':'1'}]}
        final={'output':[{'content':[{'type':'output_text','text':'denied'}]}]}
        transport=Mock(side_effect=[response,final])
        with patch.dict(agent.os.environ,{'OPENAI_API_KEY':'test'}),patch.object(local,'execute') as execute:
            agent.chat('OpenAI','model','summary',approve=lambda *a:False,transport=transport)
        execute.assert_not_called()
        self.assertIn('chưa thực hiện',transport.call_args.args[1]['input'][-1]['output'])

    def test_unknown_tool_cannot_execute_or_get_approval(self):
        response={'output':[{'type':'function_call','name':'shell','arguments':'{"cmd":"reboot"}','call_id':'1'}]}
        final={'output':[{'content':[{'type':'output_text','text':'unsupported'}]}]}
        approve=Mock()
        with patch.dict(agent.os.environ,{'OPENAI_API_KEY':'test'}),patch.object(local,'execute') as execute:
            agent.chat('OpenAI','model','test',approve=approve,transport=Mock(side_effect=[response,final]))
        approve.assert_not_called();execute.assert_not_called()

    def test_gemini_preserves_thought_signature(self):
        content={'role':'model','parts':[{'functionCall':{'name':'read_summary','args':{},'id':'id1'},'thoughtSignature':'opaque'}]}
        final={'candidates':[{'content':{'role':'model','parts':[{'text':'done'}]}}]}
        transport=Mock(side_effect=[{'candidates':[{'content':content}]},final])
        with patch.dict(agent.os.environ,{'GEMINI_API_KEY':'test'}),patch.object(local,'execute',return_value={'ok':True}):
            self.assertEqual(agent.chat('Gemini','model','test',approve=lambda *a:True,transport=transport),'done')
        messages=transport.call_args.args[1]['contents']
        self.assertIn(content,messages)
        self.assertEqual(messages[-1]['parts'][0]['functionResponse']['id'],'id1')

    def test_limit_does_not_run_unbounded_tools(self):
        response={'output':[{'type':'function_call','name':'read_summary','arguments':'{}','call_id':'1'}]}
        transport=Mock(return_value=response)
        with patch.dict(agent.os.environ,{'OPENAI_API_KEY':'test'}),patch.object(local,'execute',return_value={}) as execute:
            with self.assertRaises(RuntimeError):agent.chat('OpenAI','model','loop',approve=lambda *a:True,transport=transport)
        self.assertEqual(execute.call_count,1);self.assertEqual(transport.call_count,4)

    def test_cancelled_chat_no_network(self):
        stop=threading.Event();stop.set();transport=Mock()
        with patch.dict(agent.os.environ,{'OPENAI_API_KEY':'test'}):
            with self.assertRaises(RuntimeError):agent.chat('OpenAI','model','test',stop=stop,transport=transport)
        transport.assert_not_called()

    def test_arguments_reject_commands_and_sql(self):
        for name,args in [('ping_ip',{'ip':'-n 1000'}),('ping_ip',{'ip':'hostname'}),('read_summary',{'sql':'select * from settings'}),('check_cameras',{'password':'abc'})]:
            with self.assertRaises(ValueError):local.validate(name,args)
        with self.assertRaises(ValueError):local.read_rows('settings')
        with self.assertRaises(ValueError):local.read_rows('snmpv3_credentials')

    def test_context_never_includes_credentials(self):
        with patch.object(local,'read_rows',return_value=[]) as rows:
            result=local.page_context('Wi-Fi / Camera / AI')
        self.assertEqual([x.args[0] for x in rows.call_args_list],['camera_registry','extension_history'])
        self.assertNotIn('stream_enc',local.PROJECTIONS['camera_registry'][0])
        self.assertIn('note',local.page_context('Tự động hóa SSH'))

if __name__=='__main__':unittest.main()
