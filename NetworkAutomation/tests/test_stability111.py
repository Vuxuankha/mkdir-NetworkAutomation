import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch,Mock
from agent_runtime import AgentLock,Heartbeat,heartbeat_status
from modules import monitor_extensions as ext

class StabilityTests(unittest.TestCase):
    def test_lock_excludes_other_process_and_releases(self):
        with tempfile.TemporaryDirectory() as folder:
            lock=Path(folder)/'agent.lock'
            code='from agent_runtime import AgentLock\nimport sys\nwith AgentLock(sys.argv[1]): pass'
            with AgentLock(lock):
                result=subprocess.run([sys.executable,'-c',code,str(lock)],capture_output=True,text=True)
                self.assertNotEqual(result.returncode,0)
                self.assertIn('Agent đang chạy',result.stderr)
            result=subprocess.run([sys.executable,'-c',code,str(lock)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)

    def test_heartbeat_lifecycle_and_stale(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'status.json';pulse=Heartbeat(path);pulse.start()
            try:
                pulse.write(state='running')
                state,info=heartbeat_status(path)
                self.assertEqual(state,'Đang giám sát')
                self.assertIn('Mất heartbeat',heartbeat_status(path,info['heartbeat']+36)[0])
                self.assertFalse(path.with_suffix('.tmp').exists())
            finally:pulse.close()
            self.assertEqual(heartbeat_status(path)[0],'Đã dừng')

    def test_invalid_heartbeat(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'bad';path.write_text('{bad')
            self.assertEqual(heartbeat_status(path)[1],{})

    def test_no_wifi_still_probes_gateway(self):
        outputs=[RuntimeError('no adapter'),RuntimeError('scan unavailable')]
        with patch.object(ext.os,'name','nt'),patch.object(ext,'command_output',side_effect=outputs),patch.object(ext,'ping_host',return_value={'status':'Online','response':1}):
            data=ext.wifi_diagnostics('192.0.2.1','192.0.2.2')
        self.assertEqual(len(data['probes']),2);self.assertIn('Không đọc được',data['interfaces'])

    def test_destroy_cancels_ui_poll(self):
        from modules.extension_page import ExtensionPage
        page=ExtensionPage.__new__(ExtensionPage);page.stop_event=Mock();page._poll_id='after#1';page.after_cancel=Mock()
        event=Mock();event.widget=page;page.on_destroy(event)
        page.after_cancel.assert_called_once_with('after#1');page.stop_event.set.assert_called_once()
        self.assertIsNone(page._poll_id)

if __name__=='__main__':unittest.main()
