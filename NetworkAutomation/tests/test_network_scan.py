import threading
import unittest
from unittest.mock import patch
from modules import network_scan, ping_check

class ScanTests(unittest.TestCase):
    def test_sorted_results_and_total(self):
        events=[]
        with patch.object(network_scan, 'scan_host', side_effect=lambda ip,*args: {'ip':ip}):
            result=network_scan.scan_network('192.0.2.0/30', callback=events.append)
        self.assertEqual([r['ip'] for r in result], ['192.0.2.1','192.0.2.2'])
        self.assertEqual(events[0], {'event':'total','total':2})

    def test_large_ipv6_cancelled_without_materializing_hosts(self):
        stop=threading.Event();stop.set()
        with patch.object(network_scan, 'scan_host') as host:
            self.assertEqual(network_scan.scan_network('2001:db8::/32',stop_event=stop), [])
        host.assert_not_called()

    def test_cancellation_bounds_submission(self):
        stop=threading.Event();seen=[]
        def scan(ip,*args):
            seen.append(ip);stop.set();return None
        with patch.object(network_scan,'scan_host',side_effect=scan):
            network_scan.scan_network('10.0.0.0/8', max_workers=1, stop_event=stop)
        self.assertLessEqual(len(seen),2)

    def test_invalid_workers_and_timeout(self):
        for opts in [{'max_workers':0},{'max_workers':257},{'timeout':0},{'timeout':float('nan')}]:
            with self.assertRaises(ValueError):network_scan.scan_network('192.0.2.0/30',**opts)

    def test_ping_process_deadline_and_rounding(self):
        for module in (network_scan,ping_check):
            with patch.object(module.platform,'system',return_value='Linux'), patch.object(module.subprocess,'run') as run:
                run.return_value.returncode=1
                module.ping_host('192.0.2.1',1500)
                self.assertEqual(run.call_args.args[0][-2],'2')
                self.assertEqual(run.call_args.kwargs['timeout'],3.5)

    def test_ping_timeout(self):
        with patch.object(network_scan.subprocess,'run',side_effect=TimeoutError()):
            self.assertFalse(network_scan.ping_host('192.0.2.1'))

if __name__=='__main__':unittest.main()
