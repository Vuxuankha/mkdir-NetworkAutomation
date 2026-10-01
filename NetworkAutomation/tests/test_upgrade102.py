import json
import sqlite3
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from modules import network_scan
from upgrade_backup import backup_before_release

class UpgradeTests(unittest.TestCase):
    def test_dns_success(self):
        with patch.object(network_scan.socket,'gethostbyaddr',return_value=('switch',[],[])):
            self.assertEqual(network_scan.get_hostname('192.0.2.1'),'switch')

    def test_slow_dns_is_bounded(self):
        release=threading.Event()
        def resolve(ip):
            release.wait(2)
            return ('late',[],[])
        try:
            with patch.object(network_scan.socket,'gethostbyaddr',side_effect=resolve):
                start=time.monotonic()
                self.assertEqual(network_scan.get_hostname('192.0.2.1',.05),'')
                self.assertLess(time.monotonic()-start,.5)
        finally:release.set()

    def test_dns_saturation_skips(self):
        with patch.object(network_scan,'_dns_slots',threading.BoundedSemaphore(0)), patch.object(network_scan.socket,'gethostbyaddr') as resolve:
            self.assertEqual(network_scan.get_hostname('192.0.2.1'),'')
            resolve.assert_not_called()

    def test_dns_disabled(self):
        with patch.object(network_scan,'ping_host',return_value=True), patch.object(network_scan,'get_hostname') as dns, patch.object(network_scan,'get_mac_from_arp',return_value=''):
            result=network_scan.scan_host('192.0.2.1',resolve_hostnames=False)
            self.assertEqual(result['hostname'],'')
            dns.assert_not_called()

    def test_backup_preserves_wal_and_key_once_per_release(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);db=base/'app.db'
            conn=sqlite3.connect(db)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('CREATE TABLE demo(value)')
            conn.execute("INSERT INTO demo VALUES('original')");conn.commit()
            (base/'.credential.key').write_bytes(b'test-key')
            backup=backup_before_release(db,base,'1.0.2')
            copy=sqlite3.connect(backup/'app.db')
            try:self.assertEqual(copy.execute('SELECT value FROM demo').fetchone()[0],'original')
            finally:copy.close()
            self.assertEqual((backup/'.credential.key').read_bytes(),b'test-key')
            conn.execute("UPDATE demo SET value='new'");conn.commit();conn.close()
            self.assertIsNone(backup_before_release(db,base,'1.0.2'))
            self.assertIsNotNone(backup_before_release(db,base,'1.0.3'))
            self.assertEqual(json.loads((backup/'manifest.json').read_text())['version'],'1.0.2')

    def test_backup_failure_does_not_mark_release(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);db=base/'app.db';db.write_bytes(b'not sqlite')
            with self.assertRaises(sqlite3.DatabaseError):backup_before_release(db,base,'1.0.2')
            self.assertFalse((base/'.release_backup_1.0.2.json').exists())

    def test_new_install_has_no_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertIsNone(backup_before_release(Path(folder)/'new.db',folder,'1.0.2'))

if __name__=='__main__':unittest.main()
