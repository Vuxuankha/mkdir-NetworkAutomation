"""Reproduce failures from the second QA pass without a GUI or live devices."""
import os
import queue
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from modules import nms_v5 as vault, server_monitor as monitor


class QA152Tests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.database = self.root / 'test.db'
        self.key = self.root / '.credential.key'
        with self.connect() as c:
            c.executescript('''
                CREATE TABLE credentials(id INTEGER PRIMARY KEY,name,kind,username,secret_enc,port,note);
                CREATE TABLE network_devices(id INTEGER PRIMARY KEY,name,ip);
                CREATE TABLE secure_backup_jobs(id INTEGER PRIMARY KEY,name,device_id,credential_id,
                    command,interval_min,enabled,last_run,last_status,next_run);
                INSERT INTO credentials VALUES(1,'test','SSH','tester','token',22,'');
                INSERT INTO network_devices VALUES(1,'test','192.0.2.1');
                INSERT INTO secure_backup_jobs VALUES(1,'test',1,1,'show run',1,1,NULL,NULL,0);
            ''')
        self.threads = []
        thread_type = threading.Thread
        def tracked_thread(*args, **kwargs):
            thread = thread_type(*args, **kwargs)
            self.threads.append(thread)
            return thread
        self.patches = [patch.object(vault.threading, 'Thread', tracked_thread),
                        patch.object(vault, '_connect', self.connect),
                        patch.object(vault, 'KEY_FILE', self.key),
                        patch.object(vault, 'DATABASE_DIR', self.root)]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for thread in self.threads:
            if thread.ident is not None:
                thread.join(4)
        for item in reversed(self.patches):
            item.stop()
        self.temporary.cleanup()

    def connect(self):
        c = sqlite3.connect(self.database, timeout=5)
        c.row_factory = sqlite3.Row
        return c

    def page(self):
        page = vault.SecureBackupSchedulerPage.__new__(vault.SecureBackupSchedulerPage)
        page.parent = Mock(); page.t = Mock(); page.refresh = Mock(); page.activity = Mock()
        page.results = queue.Queue(); page.stop_event = threading.Event(); page.worker_threads = []
        return page

    def wait_workers(self, page):
        for thread in self.threads:
            thread.join(3)
            self.assertFalse(thread.is_alive())

    def wait_ready(self, pattern, count):
        deadline=time.monotonic()+15
        while len(list(self.root.glob(pattern)))<count and time.monotonic()<deadline:
            time.sleep(.01)
        self.assertEqual(len(list(self.root.glob(pattern))),count)

    def test_lost_key_with_existing_credentials_is_not_replaced(self):
        with self.assertRaisesRegex(RuntimeError, 'khóa'):
            vault.encrypt_secret('new-secret')
        self.assertFalse(self.key.exists())

    def test_decryption_never_creates_a_replacement_key(self):
        from cryptography.fernet import Fernet
        token = Fernet(Fernet.generate_key()).encrypt(b'secret').decode()
        with self.connect() as c:
            c.execute('DELETE FROM credentials')
        with self.assertRaisesRegex(RuntimeError, 'khóa'):
            vault.decrypt_secret(token)
        self.assertFalse(self.key.exists())

    def test_missing_key_detects_snmp_and_settings_ciphertext(self):
        with self.connect() as c:
            c.execute('DELETE FROM credentials')
            c.execute('CREATE TABLE snmpv3_credentials(auth_secret_enc)')
            c.execute("INSERT INTO snmpv3_credentials VALUES('old-token')")
        with self.assertRaises(RuntimeError):
            vault.encrypt_secret('secret')
        with self.connect() as c:
            c.execute('DELETE FROM snmpv3_credentials')
            c.execute('CREATE TABLE settings(key,value)')
            c.execute("INSERT INTO settings VALUES('api_token_enc','old-token')")
        with self.assertRaises(RuntimeError):
            vault.encrypt_secret('secret')
        self.assertFalse(self.key.exists())

    def test_missing_key_detects_camera_and_pool_ciphertext(self):
        with self.connect() as c:
            c.execute('DELETE FROM credentials')
            c.execute('CREATE TABLE cameras(stream_enc)')
            c.execute("INSERT INTO cameras VALUES('old-token')")
        with self.assertRaises(RuntimeError):
            vault.encrypt_secret('secret')
        with self.connect() as c:
            c.execute('DELETE FROM cameras')
            c.execute('CREATE TABLE auto_ip_pools(community_enc)')
            c.execute("INSERT INTO auto_ip_pools VALUES('old-token')")
        with self.assertRaises(RuntimeError):
            vault.encrypt_secret('secret')
        self.assertFalse(self.key.exists())

    def test_invalid_existing_key_is_not_overwritten(self):
        self.key.write_bytes(b'invalid-key')
        with self.assertRaises(ValueError):
            vault.encrypt_secret('secret')
        self.assertEqual(self.key.read_bytes(),b'invalid-key')

    def test_parallel_processes_share_one_complete_vault_key(self):
        from cryptography.fernet import Fernet
        with self.connect() as c:
            c.execute('DELETE FROM credentials')
        script = '''import sys,time,sqlite3
from pathlib import Path
from modules import nms_v5 as v
root=Path(sys.argv[1]);v.KEY_FILE=root/'.credential.key'
def connect():
 c=sqlite3.connect(root/'test.db');c.row_factory=sqlite3.Row;return c
v._connect=connect
(root/('ready-key-'+sys.argv[2])).touch()
while not (root/'start').exists():time.sleep(.01)
print(v.encrypt_secret(sys.argv[2]),flush=True)
'''
        environment = dict(os.environ, NETWORK_AUTOMATION_DATA_DIR=str(self.root/'runtime'))
        processes = [subprocess.Popen([sys.executable,'-c',script,str(self.root),str(i)],
                                     stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=environment)
                     for i in range(6)]
        try:
            self.wait_ready('ready-key-*',6)
            (self.root/'start').touch()
            tokens = []
            for p in processes:
                out, err = p.communicate(timeout=20)
                self.assertEqual(p.returncode,0,err)
                tokens.append(out.strip())
            cipher = Fernet(self.key.read_bytes())
            self.assertEqual([cipher.decrypt(t.encode()).decode() for t in tokens],list(map(str,range(6))))
            if os.name != 'nt':
                self.assertEqual(self.key.stat().st_mode & 0o777, 0o600)
        finally:
            for p in processes:
                if p.poll() is None:
                    p.kill();p.communicate()

    def test_upgrade_snapshot_is_created_once_across_processes(self):
        import json
        script = '''import sys,time,os,sqlite3
from pathlib import Path
import upgrade_backup as upgrade
root=Path(sys.argv[1])
connect=sqlite3.connect
class SlowConnection(sqlite3.Connection):
 def backup(self,*args,**kwargs):
  time.sleep(.1)
  return super().backup(*args,**kwargs)
upgrade.sqlite3.connect=lambda *args,**kwargs:connect(*args,factory=SlowConnection,**kwargs)
(root/('ready-backup-'+str(os.getpid()))).touch()
while not (root/'start-backup').exists():time.sleep(.01)
print(upgrade.backup_before_release(root/'test.db',root,'1.5.2'),flush=True)
'''
        processes = [subprocess.Popen([sys.executable,'-c',script,str(self.root)],
                                     stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                     for _ in range(6)]
        try:
            self.wait_ready('ready-backup-*',6)
            (self.root/'start-backup').touch()
            outputs = []
            for p in processes:
                out, err = p.communicate(timeout=20)
                self.assertEqual(p.returncode,0,err)
                outputs.append(out.strip())
            backups = list((self.root/'db_backups').glob('pre_app_v1.5.2_*'))
            self.assertEqual(len(backups),1)
            self.assertEqual(sum(x != 'None' for x in outputs),1)
            marker = json.loads((self.root/'.release_backup_1.5.2.json').read_text())
            self.assertEqual(Path(marker['backup']),backups[0])
            c=sqlite3.connect(backups[0]/'test.db')
            try:
                self.assertEqual(c.execute('PRAGMA quick_check').fetchone()[0],'ok')
            finally:
                c.close()
        finally:
            for p in processes:
                if p.poll() is None:
                    p.kill();p.communicate()

    def test_slow_backup_cannot_run_twice_even_across_page_instances(self):
        first, second = self.page(), self.page()
        entered, release = threading.Event(), threading.Event()
        def backup(*args):
            entered.set(); release.wait(3); return Path('backup.cfg')
        try:
            with patch.object(vault,'ssh_backup',side_effect=backup) as task:
                first._run(1);self.assertTrue(entered.wait(1))
                first._run(1);second._run(1)
                self.assertEqual(task.call_count,1)
                release.set();self.wait_workers(first);self.wait_workers(second)
        finally:
            release.set()

    def test_backup_worker_only_reports_via_queue(self):
        page = self.page()
        with patch.object(vault,'ssh_backup',return_value=Path('backup.cfg')):
            page._run(1);self.wait_workers(page)
        page.parent.after.assert_not_called()
        page.activity.assert_not_called();page.refresh.assert_not_called()
        page.poll_results()
        page.activity.assert_called_once();page.refresh.assert_called_once()
        with self.connect() as c:
            row = c.execute('SELECT * FROM secure_backup_jobs').fetchone()
        self.assertEqual(row['last_status'],'OK: backup.cfg')
        self.assertGreater(row['next_run'],time.time())

    def test_backup_failure_releases_lock_and_can_be_retried(self):
        page = self.page()
        with patch.object(vault,'ssh_backup',side_effect=RuntimeError('offline')) as task:
            page._run(1);self.wait_workers(page)
            page._run(1);self.wait_workers(page)
            self.assertEqual(task.call_count,2)
        with self.connect() as c:
            self.assertIn('offline',c.execute('SELECT last_status FROM secure_backup_jobs').fetchone()[0])

    def test_backup_database_write_failure_releases_lock(self):
        page = self.page()
        failure = Mock();failure.execute.side_effect = sqlite3.OperationalError('read-only')
        with patch.object(vault,'ssh_backup',return_value=Path('backup.cfg')), \
             patch.object(vault,'_connect',side_effect=[self.connect(),failure]), \
             patch.object(vault.logging,'getLogger'):
            self.assertTrue(page._run(1));self.wait_workers(page)
        self.assertIn('read-only',page.results.get_nowait())
        with patch.object(vault,'ssh_backup',return_value=Path('retry.cfg')):
            self.assertTrue(page._run(1));self.wait_workers(page)
        failure.close.assert_called_once()

    def test_scheduled_claim_rechecks_enabled_and_next_run(self):
        page = self.page()
        with patch.object(vault,'ssh_backup') as task:
            with self.connect() as c:
                c.execute('UPDATE secure_backup_jobs SET next_run=?',(time.time()+3600,))
            self.assertFalse(page._run(1,scheduled=True))
            with self.connect() as c:
                c.execute('UPDATE secure_backup_jobs SET enabled=0,next_run=0')
            self.assertFalse(page._run(1,scheduled=True))
            task.assert_not_called()

    def test_backup_lock_blocks_another_process_and_recovers_after_exit(self):
        script = '''import sys,time
from pathlib import Path
from agent_runtime import AgentLock
root=Path(sys.argv[1])
with AgentLock(root/'backup_job_locks'/'1.lock'):
 print('locked',flush=True)
 while not (root/'release').exists():time.sleep(.01)
'''
        child = subprocess.Popen([sys.executable,'-c',script,str(self.root)],
                                 stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            self.assertEqual(child.stdout.readline().strip(),'locked')
            page = self.page()
            with patch.object(vault,'ssh_backup',return_value=Path('backup.cfg')) as task:
                self.assertFalse(page._run(1));task.assert_not_called()
                (self.root/'release').touch()
                out,err=child.communicate(timeout=5)
                self.assertEqual(child.returncode,0,err)
                self.assertTrue(page._run(1));self.wait_workers(page)
                task.assert_called_once()
        finally:
            if child.poll() is None:
                child.kill();child.communicate()

    def test_navigation_stops_scheduling_and_ignores_late_results(self):
        page = self.page();page.on_destroy(Mock(widget=page.t))
        with patch.object(vault,'ssh_backup') as task:
            page._tick();page._run(1)
        task.assert_not_called();page.parent.after.assert_not_called()
        page.results.put('late result');page.poll_results()
        page.refresh.assert_not_called();page.activity.assert_not_called()

    def test_database_error_does_not_disable_future_scheduler_ticks(self):
        page = self.page()
        with patch.object(vault,'_connect',side_effect=sqlite3.OperationalError('locked')):
            page._tick()
        page.parent.after.assert_called_once_with(5000,page._tick)

    def test_shutdown_waits_for_secure_backup_worker(self):
        from main import NetworkAutomationApp
        app = NetworkAutomationApp.__new__(NetworkAutomationApp)
        app.root = Mock();app.secure_backup_workers = [Mock()]
        app.secure_backup_workers[0].is_alive.return_value = True
        app._finish_close()
        app.root.after.assert_called_once_with(250,app._finish_close)
        app.root.destroy.assert_not_called()

    def target(self, **updates):
        row = dict(host='localhost',port=80,protocol='HTTP',service_name='')
        row.update(updates);return row

    def test_http_error_response_is_warning_and_closes_response(self):
        from urllib.error import HTTPError
        response = Mock()
        error = HTTPError('http://localhost/',503,'unavailable',{},response)
        with patch.object(monitor.urllib.request,'urlopen',side_effect=error), \
             patch.object(monitor,'_local_windows_health',return_value=None):
            result = monitor.check_target(self.target())
        self.assertEqual(result['status'],'WARN')
        self.assertIn('HTTP 503',result['detail']);response.close.assert_called_once()

    def test_unreachable_service_stays_down_with_high_resource_warning(self):
        with patch.object(monitor.urllib.request,'urlopen',side_effect=OSError('refused')), \
             patch.object(monitor,'_local_windows_health',return_value={'cpu':99,'service':'Stopped'}):
            result = monitor.check_target(self.target())
        self.assertEqual(result['status'],'DOWN')
        self.assertIn('refused',result['detail'])

    def test_malformed_port_and_health_do_not_abort_monitoring(self):
        with patch.object(monitor,'_local_windows_health',return_value={'cpu':'N/A','service':None}):
            result = monitor.check_target(self.target(port='bad'))
        self.assertEqual(result['status'],'DOWN');self.assertIsNone(result['cpu'])

    def test_host_port_is_rejected_and_bracketed_ipv6_normalized(self):
        with self.assertRaises(ValueError):
            monitor.validate_target('server.example:443',443,'HTTPS')
        self.assertEqual(monitor.validate_target('[::1]',80,'HTTP'),('::1',80,'HTTP'))


if __name__ == '__main__':
    unittest.main()
