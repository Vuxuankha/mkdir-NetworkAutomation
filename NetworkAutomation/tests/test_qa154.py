"""Presence checks with disposable DB and deterministic network outcomes."""
import sqlite3
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from modules import device_presence as presence


class PresenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)/'test.db'
        c = self.connect()
        c.execute('CREATE TABLE devices(id INTEGER PRIMARY KEY,ip TEXT,status TEXT,last_seen TEXT)')
        c.executemany('INSERT INTO devices VALUES(?,?,?,?)', [(1,'192.0.2.1','Offline','old'),(2,'192.0.2.2','Online','old')])
        c.commit();c.close()
        self.patch = patch.object(presence,'get_connection',self.connect);self.patch.start()
        self.monitors = []
    def connect(self, **kwargs):
        c = sqlite3.connect(self.path);c.row_factory = sqlite3.Row;return c
    def monitor(self, **kwargs):
        monitor = presence.DevicePresenceMonitor(autostart=False, **kwargs)
        self.monitors.append(monitor);return monitor
    def rows(self):
        c=self.connect()
        try:return [dict(r) for r in c.execute('SELECT * FROM devices ORDER BY id')]
        finally:c.close()
    def tearDown(self):
        for m in self.monitors:
            m.stop()
            if m.thread:m.thread.join(4);self.assertFalse(m.thread.is_alive())
        self.patch.stop();self.tmp.cleanup()
    def wait(self, predicate):
        deadline = time.monotonic()+3
        while not predicate() and time.monotonic()<deadline:time.sleep(.01)
        self.assertTrue(predicate())
    def test_old_offline_not_shown_before_first_probe(self):
        m=self.monitor(probe=lambda ip:True)
        self.assertEqual(m.display_result(self.rows()[0],m.snapshot()[0]),('Unknown','-'))
    def test_updates_correct_table_and_last_seen_only_on_reply(self):
        m=self.monitor(probe=lambda ip:ip.endswith('.1'));m.collect_once()
        rows=self.rows();self.assertEqual([r['status'] for r in rows],['Online','Offline'])
        self.assertNotEqual(rows[0]['last_seen'],'old');self.assertEqual(rows[1]['last_seen'],'old')
        self.assertEqual(m.display_result(rows[0],m.snapshot()[0])[0],'Online')
    def test_reconnect_changes_offline_to_online(self):
        m=self.monitor(probe=lambda ip:False);m.collect_once()
        m.probe=lambda ip:True;m.collect_once()
        self.assertEqual([r['status'] for r in self.rows()],['Online','Online'])
    def test_local_probe_error_is_unknown(self):
        m=self.monitor(probe=lambda ip:None);m.collect_once()
        self.assertEqual([r['status'] for r in self.rows()],['Unknown','Unknown'])
    def test_new_ip_and_deleted_device_do_not_receive_old_result(self):
        def probe(ip):
            c=self.connect()
            if ip.endswith('.1'):c.execute("UPDATE devices SET ip='192.0.2.3' WHERE id=1")
            else:c.execute('DELETE FROM devices WHERE id=2')
            c.commit();c.close();return True
        m=self.monitor(probe=probe,workers=1);m.collect_once()
        self.assertEqual(self.rows()[0]['status'],'Offline')
        self.assertEqual(m.snapshot()[0],{})
    def test_expired_result_is_unknown(self):
        m=self.monitor(probe=lambda ip:True);m.collect_once()
        snapshot=m.snapshot()[0];snapshot[(1,'192.0.2.1')]=dict(snapshot[(1,'192.0.2.1')],monotonic=time.monotonic()-61)
        self.assertEqual(m.display_result(self.rows()[0],snapshot),('Unknown','-'))
    def test_startup_periodic_and_manual_refresh_and_shutdown(self):
        calls=[];m=presence.DevicePresenceMonitor(interval=.15,probe=lambda ip:calls.append(ip) or True)
        self.monitors.append(m);self.wait(lambda:len(calls)>=4)
        m.interval=10;self.wait(lambda:not m.snapshot()[1]);count=len(calls)
        m.request_check();self.wait(lambda:len(calls)>count)
        m.stop();m.thread.join(3);self.assertFalse(m.thread.is_alive())
    def test_no_overlapping_cycles_and_worker_limit(self):
        entered=threading.Event();release=threading.Event();calls=[]
        def probe(ip):calls.append(ip);entered.set();release.wait(2);return True
        m=self.monitor(probe=probe,workers=1);thread=threading.Thread(target=m.collect_once);thread.start()
        try:
            self.assertTrue(entered.wait(1));m.collect_once();self.assertEqual(len(calls),1)
        finally:release.set();thread.join(3)
        self.assertEqual(len(calls),2)
    def test_stop_during_probe_cancels_remaining_and_no_late_write(self):
        entered=threading.Event();release=threading.Event();calls=[]
        def probe(ip):calls.append(ip);entered.set();release.wait(2);return True
        m=self.monitor(probe=probe,workers=1);thread=threading.Thread(target=m.collect_once);thread.start()
        self.assertTrue(entered.wait(1));m.stop();release.set();thread.join(3)
        self.assertFalse(thread.is_alive());self.assertEqual([r['last_seen'] for r in self.rows()],['old','old'])
    def test_database_error_clears_live_result(self):
        m=self.monitor(probe=lambda ip:True);m.collect_once()
        with patch.object(presence,'get_connection',side_effect=sqlite3.OperationalError('test unavailable')):
            m.collect_once()
        self.assertEqual(m.snapshot()[0],{});self.assertTrue(m.snapshot()[2]);self.assertFalse(m.snapshot()[1])


class PingTests(unittest.TestCase):
    def test_windows_unreachable_with_exit_zero_is_offline(self):
        with patch.object(presence.os,'name','nt'),patch.object(presence.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout='Reply from 192.0.2.254: Destination host unreachable.')):
            self.assertIs(presence.probe_device('192.0.2.1'),False)
    def test_windows_actual_reply_is_online(self):
        with patch.object(presence.os,'name','nt'),patch.object(presence.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout='Reply from 192.0.2.1: bytes=32 time<1ms TTL=64')) as run:
            self.assertIs(presence.probe_device('192.0.2.1'),True)
            self.assertEqual(run.call_args.kwargs['timeout'],2.5)
    def test_missing_ping_is_unknown_and_invalid_ip_never_executes(self):
        with patch.object(presence.subprocess,'run',side_effect=FileNotFoundError) as run:
            self.assertIsNone(presence.probe_device('192.0.2.1'));run.reset_mock()
            self.assertIsNone(presence.probe_device('-n 500'));run.assert_not_called()
    def test_timeout_no_reply_and_linux_local_error(self):
        with patch.object(presence.subprocess,'run',side_effect=presence.subprocess.TimeoutExpired('ping',2.5)):
            self.assertIs(presence.probe_device('192.0.2.1'),False)
        with patch.object(presence.os,'name','posix'),patch.object(presence.subprocess,'run',return_value=SimpleNamespace(returncode=2,stdout='')):
            self.assertIsNone(presence.probe_device('192.0.2.1'))

if __name__=='__main__':unittest.main()
