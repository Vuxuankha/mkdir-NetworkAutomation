"""Regression tests for defects found in the October 2 QA review."""
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import queue
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]


class QA151Tests(unittest.TestCase):
    def target(self, host='server.example', port=80, protocol='HTTP'):
        return {'host':host,'port':port,'protocol':protocol,'service_name':''}

    def test_http_and_https_use_protocol_specific_default_ports(self):
        from modules import server_monitor as monitor
        for protocol, port, expected in (('HTTP',443,'http://server.example:443/'),
                                          ('HTTPS',80,'https://server.example:80/'),
                                          ('HTTP',80,'http://server.example/'),
                                          ('HTTPS',443,'https://server.example/')):
            with patch.object(monitor.urllib.request,'urlopen') as request:
                request.return_value.__enter__.return_value.status=200
                result=monitor.check_target(self.target(port=port,protocol=protocol))
                self.assertEqual(request.call_args.args[0],expected)
                self.assertEqual(result['status'],'UP')

    def test_ipv6_url_uses_brackets(self):
        from modules import server_monitor as monitor
        with patch.object(monitor.urllib.request,'urlopen') as request:
            request.return_value.__enter__.return_value.status=200
            monitor.check_target(self.target(host='2001:db8::1',port=8080))
            self.assertEqual(request.call_args.args[0],'http://[2001:db8::1]:8080/')

    def test_target_validation_rejects_bad_port_protocol_and_url(self):
        from modules.server_monitor import validate_target
        for host,port,protocol in [('host',0,'TCP'),('host',65536,'TCP'),('host','abc','HTTP'),
                                   ('http://host',80,'HTTP'),('host',80,'HTTPX'),('a b',22,'TCP')]:
            with self.assertRaises(ValueError):
                validate_target(host,port,protocol)
        self.assertEqual(validate_target(' server.example ','443','https'),('server.example',443,'HTTPS'))

    def monitor_page(self):
        from modules.server_monitor import ServerMonitorPage
        page=ServerMonitorPage.__new__(ServerMonitorPage)
        page.parent=Mock();page.tree=Mock();page.tree.winfo_exists.return_value=True
        page.activity=Mock();page.refresh=Mock();page.run_button=Mock()
        page.stop_event=threading.Event();page.results=queue.Queue();page.busy=False;page.worker_threads=[]
        return page

    def test_server_worker_never_calls_tk_or_activity_callback(self):
        from modules import server_monitor as monitor
        page=self.monitor_page();owner=threading.get_ident()
        def main_thread(*args,**kwargs):
            self.assertEqual(threading.get_ident(),owner)
        page.parent.after.side_effect=main_thread
        page.activity.side_effect=main_thread
        page.run_button.configure.side_effect=main_thread
        page.refresh.side_effect=main_thread
        with patch.object(monitor,'run_all_targets',return_value=[('server',{})]) as run:
            page.run_checks()
            result=page.results.get(timeout=3)
        self.assertEqual(result,(1,None));run.assert_called_once_with(stop=page.stop_event)
        page.activity.assert_not_called()
        page.results.put(result);page.poll_result()
        page.refresh.assert_called_once();page.activity.assert_called_once()

    def test_worker_exception_message_survives_until_main_thread_poll(self):
        from modules import server_monitor as monitor
        page=self.monitor_page()
        with patch.object(monitor,'run_all_targets',side_effect=RuntimeError('database unavailable')), \
             patch.object(monitor.logging,'getLogger'):
            page.run_checks()
            result=page.results.get(timeout=3)
        page.results.put(result)
        with patch.object(monitor.messagebox,'showerror') as show:
            page.poll_result()
        show.assert_called_once_with('Server Monitor','database unavailable',parent=page.parent)
        self.assertFalse(page.busy)

    def test_repeated_start_does_not_spawn_duplicate_worker(self):
        from modules import server_monitor as monitor
        page=self.monitor_page();started=threading.Event();release=threading.Event()
        def run(**kwargs):
            started.set();release.wait(3);return []
        try:
            with patch.object(monitor,'run_all_targets',side_effect=run) as task:
                page.run_checks();self.assertTrue(started.wait(1));page.run_checks()
                task.assert_called_once()
                self.assertEqual(len(page.worker_threads),1)
                release.set();page.worker_threads[0].join(timeout=2)
        finally:
            release.set()

    def test_navigation_ignores_results_and_requests_stop(self):
        page=self.monitor_page()
        page.on_destroy(Mock(widget=page.tree))
        self.assertTrue(page.stop_event.is_set())
        page.results.put((1,None));page.poll_result()
        page.refresh.assert_not_called();page.activity.assert_not_called()

    def test_shutdown_waits_for_server_worker(self):
        from main import NetworkAutomationApp
        app=NetworkAutomationApp.__new__(NetworkAutomationApp)
        app.root=Mock();app.server_monitor_workers=[Mock()]
        app.server_monitor_workers[0].is_alive.return_value=True
        app._finish_close()
        app.root.after.assert_called_once_with(250,app._finish_close)
        app.root.destroy.assert_not_called()

    def test_server_page_activity_callback_runs_without_missing_user(self):
        import main
        app = main.NetworkAutomationApp.__new__(main.NetworkAutomationApp)
        app.clear_content = Mock()
        app.set_page_title = Mock()
        app.content = Mock()
        app.add_activity = Mock()
        with patch('main.ServerMonitorPage') as page:
            app.show_server_monitor()
        callback = page.call_args.kwargs['activity_callback']
        callback('Giám sát server hoàn tất')
        app.add_activity.assert_called_once_with('Giám sát server hoàn tất')

    def test_regression_keeps_operator_database_and_wal_untouched(self):
        with tempfile.TemporaryDirectory(prefix='qa-real-db-') as folder:
            root = Path(folder)
            database_dir = root/'database';database_dir.mkdir()
            database = database_dir/'network_automation.db'
            connection = sqlite3.connect(database)
            try:
                connection.execute('PRAGMA journal_mode=WAL')
                connection.execute('PRAGMA wal_autocheckpoint=0')
                connection.execute('CREATE TABLE operator_data(value)')
                connection.execute("INSERT INTO operator_data VALUES('untouched')")
                connection.commit()
                before = {p.name:p.read_bytes() for p in database_dir.iterdir() if p.is_file()}
                env = dict(os.environ, NETWORK_AUTOMATION_DATA_DIR=folder)
                env.pop('NA_REGRESSION_CHILD',None)
                result = subprocess.run([sys.executable,str(ROOT/'regression_test.py')],
                                        cwd=ROOT,env=env,capture_output=True,text=True,timeout=45)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                after = {p.name:p.read_bytes() for p in database_dir.iterdir() if p.is_file()}
                self.assertEqual(before,after)
                self.assertEqual(connection.execute('SELECT value FROM operator_data').fetchone()[0],'untouched')
            finally:
                connection.close()


if __name__ == '__main__':
    unittest.main()
