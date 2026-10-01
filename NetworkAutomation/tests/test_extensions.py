import threading
import unittest
from unittest.mock import Mock,patch
from modules import monitor_extensions as ext

class ExtensionTests(unittest.TestCase):
    def test_redacts_secrets_and_bounds_text(self):
        out=ext.redact('password=abc\napi_key: xyz\nrtsp://user:pw@192.0.2.1/live')
        self.assertNotIn('abc',out);self.assertNotIn('xyz',out);self.assertNotIn('user:pw',out)
        self.assertEqual(len(ext.redact('x'*40000)),30000)

    def test_host_validation(self):
        for host in ['','-x','a b','http://host']:
            with self.assertRaises(ValueError):ext.validate_host(host)
        self.assertEqual(ext.validate_host('192.0.2.1'),'192.0.2.1')

    def test_camera_tcp_not_claimed_video(self):
        with patch.object(ext.socket,'create_connection'):
            status,detail=ext.check_camera({'host':'192.0.2.1','port':554})
            self.assertEqual(status,'Reachable');self.assertIn('chưa xác nhận',detail)
        with patch.object(ext.socket,'create_connection',side_effect=OSError):
            self.assertEqual(ext.check_camera({'host':'192.0.2.1','port':554})[0],'Unreachable')

    def test_wifi_loss_and_latency(self):
        samples=[{'status':'Online','response':10},{'status':'Offline','response':None}]*4
        with patch.object(ext.os,'name','nt'),patch.object(ext,'command_output',return_value='raw wifi'),patch.object(ext,'ping_host',side_effect=samples):
            result=ext.wifi_diagnostics('192.0.2.1','192.0.2.2')
        self.assertEqual(result['probes']['192.0.2.1']['loss_percent'],50)
        self.assertEqual(result['probes']['192.0.2.2']['latency_ms'],10)

    def test_agent_already_stopped_does_not_probe(self):
        import monitor_agent
        stop=threading.Event();stop.set()
        with patch.object(monitor_agent,'ensure_tables'),patch.object(monitor_agent,'setup_logging'),patch.object(monitor_agent,'data_path') as path,patch.object(monitor_agent,'cycle') as cycle:
            monitor_agent.run(stop)
        cycle.assert_not_called()

if __name__=='__main__':unittest.main()
