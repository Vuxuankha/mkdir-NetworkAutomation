import sqlite3
import unittest
from modules.dark_dashboard import collect_snapshot,dashboard_columns

class DashboardTests(unittest.TestCase):
    def database(self):
        connection=sqlite3.connect(':memory:')
        connection.executescript('''CREATE TABLE network_devices(name,ip,device_type,status,updated_at);
        CREATE TABLE alerts(id,created_at,severity,ip,alert_type,message,status);
        CREATE TABLE incidents(id,last_seen,severity,host,title,status);''')
        return connection
    def test_actual_totals_unknown_states_and_open_events(self):
        connection=self.database()
        connection.executemany('INSERT INTO network_devices VALUES(?,?,?,?,?)',[
            ('A','192.0.2.1','Switch',' Online ','2026-10-01'),('B','192.0.2.2','AP','OFFLINE','2026-10-01'),('C','192.0.2.3','Camera',None,'2026-10-01')])
        connection.executemany('INSERT INTO alerts VALUES(?,?,?,?,?,?,?)',[
            (1,'2026-10-01 10:00','High','192.0.2.2','Ping','Timeout','Open'),(2,'2026-10-01 11:00','High','192.0.2.1','Ping','Recovered',' Closed ')])
        connection.executemany('INSERT INTO incidents VALUES(?,?,?,?,?,?)',[
            (1,'2026-10-01 12:00','High','192.0.2.3','Camera offline','Open'),(2,'2026-10-01 13:00','High','192.0.2.1','Old incident','Resolved')])
        snap=collect_snapshot(lambda:connection)
        self.assertEqual([snap[key] for key in ('total','online','offline','other','alerts','incidents')],[3,1,1,1,1,1])
        self.assertEqual(snap['events'][0][3],'Camera offline')
        self.assertEqual(len(snap['events']),2)
        self.assertEqual(snap['unavailable'],[])
    def test_empty_database_has_zero_counts(self):
        snap=collect_snapshot(self.database)
        self.assertEqual(snap['total'],0);self.assertEqual(snap['alerts'],0);self.assertEqual(snap['events'],[])
    def test_missing_schema_shows_unavailable_not_healthy_zero(self):
        snap=collect_snapshot(lambda:sqlite3.connect(':memory:'))
        self.assertIsNone(snap['total']);self.assertIsNone(snap['alerts']);self.assertIsNone(snap['incidents'])
        self.assertEqual(len(snap['unavailable']),3)
    def test_connect_failure_retains_unavailable_state(self):
        def failure():raise sqlite3.OperationalError('unavailable')
        snap=collect_snapshot(failure)
        self.assertIsNone(snap['total']);self.assertEqual(len(snap['unavailable']),3)
    def test_missing_incidents_does_not_hide_devices(self):
        connection=self.database();connection.execute('DROP TABLE incidents')
        snap=collect_snapshot(lambda:connection)
        self.assertEqual(snap['total'],0);self.assertIsNone(snap['incidents'])
        self.assertEqual(snap['unavailable'],['Sự cố'])
    def test_cards_reflow_at_small_widths(self):
        self.assertEqual([dashboard_columns(width) for width in (1200,900,640)],[5,3,2])

if __name__=='__main__':unittest.main()
