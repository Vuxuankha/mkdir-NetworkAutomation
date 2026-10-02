"""Local SSH integration tests. No access to external devices or operator data."""
from datetime import datetime
from pathlib import Path
import socket
import sqlite3
import tempfile
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import paramiko
from modules import nms_v5 as backup, ssh_runner


class LocalSSHHost:
    key = paramiko.RSAKey.generate(2048)
    password = '  test secret  '

    def __init__(self, responses):
        self.responses = responses
        self.stop = threading.Event()
        self.socket = socket.socket()
        self.socket.bind(('127.0.0.1',0)); self.socket.listen(2); self.socket.settimeout(.1)
        self.port = self.socket.getsockname()[1]
        self.commands = []; self.failures = []
        self.thread = threading.Thread(target=self.serve,daemon=True)

    def serve(self):
        class Handler(paramiko.ServerInterface):
            def __init__(self):
                self.request = threading.Event();self.command = None
            def check_auth_password(self, username, password):
                return paramiko.AUTH_SUCCESSFUL if username=='tester' and password==LocalSSHHost.password else paramiko.AUTH_FAILED
            def get_allowed_auths(self, username):
                return 'password'
            def check_channel_request(self, kind, channel_id):
                return paramiko.OPEN_SUCCEEDED if kind=='session' else paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
            def check_channel_exec_request(self, channel, command):
                self.command=command.decode();self.request.set();return True
        for out, err, status in self.responses:
            transport = None
            try:
                while not self.stop.is_set():
                    try:
                        connection, _ = self.socket.accept();break
                    except socket.timeout:
                        continue
                else:
                    return
                transport = paramiko.Transport(connection);transport.add_server_key(self.key)
                handler=Handler();transport.start_server(server=handler)
                channel=transport.accept(5)
                if channel is None or not handler.request.wait(5):
                    raise RuntimeError('No exec request from test client')
                self.commands.append(handler.command)
                if out: channel.sendall(out)
                if err: channel.sendall_stderr(err)
                channel.send_exit_status(status);channel.shutdown_write();channel.close()
                deadline=time.monotonic()+3
                while transport.is_active() and time.monotonic()<deadline:
                    time.sleep(.01)
            except Exception as e:
                if not self.stop.is_set():self.failures.append(e)
            finally:
                if transport:transport.close()

    def __enter__(self):
        self.thread.start();return self

    def __exit__(self,*args):
        self.stop.set();self.socket.close();self.thread.join(6)
        if self.thread.is_alive():raise RuntimeError('Local SSH test server did not stop')
        if not args[0] and self.failures:raise self.failures[0]


class QA153BackupTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.backups=self.root/'backups';self.backups.mkdir()
        self.database=self.root/'test.db'
        with self.connect() as c:
            c.executescript('''CREATE TABLE credentials(secret_enc);
                CREATE TABLE config_backups(device_name,source,file_path,size_bytes,note,created_at);''')
        self.patches=[patch.object(backup,'_connect',self.connect),
                      patch.object(backup,'KEY_FILE',self.root/'key'),
                      patch.object(backup,'BACKUP_DIR',self.backups)]
        for p in self.patches:p.start()
        self.secret=backup.encrypt_secret(LocalSSHHost.password)

    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()

    def connect(self):
        c=sqlite3.connect(self.database);c.row_factory=sqlite3.Row;return c

    def call_backup(self, host, destination=None):
        return backup.ssh_backup({'name':'LAB','ip':'127.0.0.1'},
            {'name':'test','port':host.port,'username':'tester','secret_enc':self.secret},
            'show running-config',destination)

    def test_loopback_ssh_auth_and_backup_content(self):
        content=b'hostname LAB\ninterface Ethernet1\n description QA\n'
        with LocalSSHHost([(content,b'warning: lab only',0)]) as host:
            path=self.call_backup(host)
        self.assertEqual(host.commands,['show running-config'])
        self.assertEqual(path.read_bytes(),content)
        with self.connect() as c:
            row=c.execute('SELECT * FROM config_backups').fetchone()
        self.assertEqual(row['file_path'],str(path));self.assertEqual(row['size_bytes'],len(content))

    def test_nonzero_exit_does_not_create_successful_backup(self):
        with LocalSSHHost([(b'permission denied\n',b'',2)]) as host:
            with self.assertRaises(RuntimeError):self.call_backup(host)
        self.assertEqual(list(self.backups.iterdir()),[])
        with self.connect() as c:self.assertEqual(c.execute('SELECT COUNT(*) FROM config_backups').fetchone()[0],0)

    def test_empty_output_is_not_a_valid_backup(self):
        with LocalSSHHost([(b'',b'',0)]) as host:
            with self.assertRaises(RuntimeError):self.call_backup(host)
        self.assertEqual(list(self.backups.iterdir()),[])

    def test_failed_command_preserves_explicit_destination(self):
        destination=self.backups/'existing.cfg';destination.write_text('keep original')
        with LocalSSHHost([(b'partial invalid output',b'failed',1)]) as host:
            with self.assertRaises(RuntimeError):self.call_backup(host,destination)
        self.assertEqual(destination.read_text(),'keep original')

    def test_backups_in_same_second_have_distinct_files_and_records(self):
        clock=Mock();clock.now.return_value=datetime(2026,10,2,12,0,0)
        with LocalSSHHost([(b'first config\n',b'',0),(b'second config\n',b'',0)]) as host, \
             patch.object(backup,'datetime',clock):
            first=self.call_backup(host);second=self.call_backup(host)
        self.assertNotEqual(first,second)
        self.assertEqual(first.read_text(),'first config\n');self.assertEqual(second.read_text(),'second config\n')
        with self.connect() as c:
            self.assertEqual(c.execute('SELECT COUNT(DISTINCT file_path) FROM config_backups').fetchone()[0],2)

    def test_backup_handles_large_stderr_without_deadlock(self):
        # Exceeds the initial SSH window; sequential stdout.read() would stall stderr.
        with LocalSSHHost([(b'hostname LAB\n',b'w'*2300000,0)]) as host:
            started=time.monotonic();path=self.call_backup(host)
        self.assertLess(time.monotonic()-started,10)
        self.assertEqual(path.read_text(),'hostname LAB\n')

    def test_failed_atomic_replace_preserves_previous_backup(self):
        destination=self.backups/'existing.cfg';destination.write_text('keep original')
        with LocalSSHHost([(b'new config',b'',0)]) as host, \
             patch.object(backup.os,'replace',side_effect=OSError('disk error')):
            with self.assertRaises(OSError):self.call_backup(host,destination)
        self.assertEqual(destination.read_text(),'keep original')
        self.assertEqual(list(self.backups.iterdir()),[destination])

    def test_failed_file_flush_leaves_no_backup_or_db_record(self):
        with LocalSSHHost([(b'new config',b'',0)]) as host, \
             patch.object(backup.os,'fsync',side_effect=OSError('disk error')):
            with self.assertRaises(OSError):self.call_backup(host)
        self.assertEqual(list(self.backups.iterdir()),[])
        with self.connect() as c:self.assertEqual(c.execute('SELECT COUNT(*) FROM config_backups').fetchone()[0],0)


class QA153StreamTests(unittest.TestCase):
    def client(self,out=b'config',err=b'warning',status=0):
        channel=Mock();channel.recv_ready.side_effect=[True,False,False]
        channel.recv_stderr_ready.side_effect=[True,False,False]
        channel.recv.return_value=out;channel.recv_stderr.return_value=err
        channel.exit_status_ready.return_value=True;channel.recv_exit_status.return_value=status
        client=Mock();client.exec_command.return_value=(Mock(),SimpleNamespace(channel=channel),Mock())
        return client,channel

    def test_exec_output_limit_closes_channel(self):
        client,channel=self.client(out=b'x'*10,err=b'')
        with self.assertRaisesRegex(RuntimeError,'giới hạn'):
            ssh_runner._exec(client,'show run',1,max_output_bytes=4)
        channel.close.assert_called_once()

    def test_exec_can_keep_stderr_out_of_configuration(self):
        client,channel=self.client()
        self.assertEqual(ssh_runner.read_exec_output(client,'show run',1),('config','warning'))
        channel.close.assert_called_once()

    def test_exec_timeout_closes_channel(self):
        client,channel=self.client()
        with patch.object(ssh_runner.time,'monotonic',side_effect=[0,2]):
            with self.assertRaises(TimeoutError):ssh_runner._exec(client,'slow',1)
        channel.close.assert_called_once()


class QA153LayoutTests(unittest.TestCase):
    def flow(self):
        from modules.responsive_layout import FlowRow
        flow=FlowRow.__new__(FlowRow)
        flow.frame=Mock();flow.widgets=[Mock()];flow.gap=8;flow.last=None
        flow.pending=None;flow.destroyed=False;flow.apply=Mock()
        flow.frame.winfo_width.return_value=800;flow.widgets[0].winfo_reqwidth.return_value=100
        flow.frame.after_idle.return_value='idle-1'
        return flow

    def test_layout_waits_for_idle_and_coalesces_configure_events(self):
        flow=self.flow();flow.layout(Mock());flow.layout(Mock())
        flow.apply.assert_not_called()
        flow.frame.after_idle.assert_called_once_with(flow.apply_pending)
        flow.apply_pending();flow.apply.assert_called_once_with([(0,0)])

    def test_destroy_cancels_pending_layout_and_ignores_late_events(self):
        flow=self.flow();flow.layout(Mock());flow.on_destroy(Mock(widget=flow.frame))
        flow.frame.after_cancel.assert_called_once_with('idle-1')
        flow.apply_pending();flow.layout(Mock());flow.apply.assert_not_called()
        self.assertEqual(flow.frame.after_idle.call_count,1)


class QA153LifecycleTests(unittest.TestCase):
    def test_shutdown_waits_for_active_ssh_worker(self):
        from main import NetworkAutomationApp
        app=NetworkAutomationApp.__new__(NetworkAutomationApp)
        app.root=Mock();app.ssh_workers=[Mock()]
        app.ssh_workers[0].is_alive.return_value=True
        app._finish_close()
        app.root.after.assert_called_once_with(250,app._finish_close)
        app.root.destroy.assert_not_called()



if __name__=='__main__':
    unittest.main()
