import json
import unittest
from unittest.mock import Mock,patch
from modules import monitor_extensions as ext

class GeminiTests(unittest.TestCase):
    def test_request_and_response(self):
        response=Mock();response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False)
        response.read.return_value=b'{"candidates":[{"content":{"parts":[{"text":"ok"}]}}]}'
        with patch.object(ext.urllib.request,'urlopen',return_value=response) as call:
            self.assertEqual(ext.gemini_analyze('password=test','model',api_key='test-key'),'ok')
        request=call.call_args.args[0];self.assertNotIn('test-key',request.full_url)
        payload=json.loads(request.data);self.assertNotIn('password=test',payload['contents'][0]['parts'][0]['text'])
    def test_invalid_model(self):
        with self.assertRaises(ValueError):ext.gemini_analyze('hello','../model',api_key='test')
    def test_missing_key(self):
        with patch.dict(ext.os.environ,{},clear=True),patch.object(ext.urllib.request,'urlopen') as call:
            with self.assertRaises(ValueError):ext.gemini_analyze('hello','model')
        call.assert_not_called()

if __name__=='__main__':unittest.main()
