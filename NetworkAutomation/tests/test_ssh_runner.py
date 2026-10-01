import sys
import queue
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modules.ssh_runner import connection_options, execute_commands, _exec, _shell_read


class SSHTests(unittest.TestCase):
    def options(self, **changes):
        opts = connection_options('192.0.2.1', '22', 'admin', 'test-password')
        opts.update(changes)
        return opts

    def module(self, client):
        return SimpleNamespace(SSHClient=lambda: client, AutoAddPolicy=lambda: object())

    def test_validation(self):
        for port in ('abc', '0', '-1', '65536'):
            with self.subTest(port=port), self.assertRaises(ValueError):
                connection_options('host', port, 'admin', '')
        with self.assertRaises(ValueError):
            connection_options('', '22', 'admin', '')

    def test_password_auth_does_not_try_agent_keys(self):
        client = Mock()
        with patch('modules.ssh_runner._exec', return_value='ok'):
            self.assertIn('ok', execute_commands(self.options(), ['show version'], self.module(client)))
        self.assertFalse(client.connect.call_args.kwargs['look_for_keys'])
        self.assertFalse(client.connect.call_args.kwargs['allow_agent'])
        client.close.assert_called_once()

    def test_empty_password_preserves_key_auth(self):
        client = Mock()
        execute_commands(self.options(password=''), [], self.module(client))
        self.assertTrue(client.connect.call_args.kwargs['look_for_keys'])
        self.assertIsNone(client.connect.call_args.kwargs['password'])

    def test_connect_failure_closes_client(self):
        client = Mock()
        client.connect.side_effect = OSError('connection refused')
        with self.assertRaises(OSError):
            execute_commands(self.options(), ['ls'], self.module(client))
        client.close.assert_called_once()

    def test_shell_uses_one_session_with_paging(self):
        client = Mock()
        with patch('modules.ssh_runner._shell_read', side_effect=[('', 'SW1#'), ('', 'SW1#'), ('', 'SW1(config)#'), ('ok', 'SW1(config)#')]):
            execute_commands(self.options(mode='shell', paging='terminal length 0'),
                             ['configure terminal', 'hostname SW1'], self.module(client))
        client.invoke_shell.assert_called_once()
        self.assertEqual([c.args[0] for c in client.invoke_shell.return_value.sendall.call_args_list],
                         ['terminal length 0\n', 'configure terminal\n', 'hostname SW1\n'])
        client.invoke_shell.return_value.close.assert_called_once()
        client.exec_command.assert_not_called()

    def test_shell_timeout_closes_everything(self):
        client = Mock()
        with patch('modules.ssh_runner._shell_read', side_effect=TimeoutError('timeout')):
            with self.assertRaises(TimeoutError):
                execute_commands(self.options(mode='shell'), ['show run'], self.module(client))
        client.invoke_shell.return_value.close.assert_called_once()
        client.close.assert_called_once()

    def test_exec_drains_both_streams(self):
        client, channel = Mock(), Mock()
        channel.recv_ready.side_effect = [True, False, False]
        channel.recv_stderr_ready.side_effect = [True, False, False]
        channel.recv.return_value = b'output'
        channel.recv_stderr.return_value = b'warning'
        channel.exit_status_ready.return_value = True
        channel.recv_exit_status.return_value = 0
        client.exec_command.return_value = (Mock(), SimpleNamespace(channel=channel), Mock())
        self.assertEqual(_exec(client, 'ls', 1), 'outputwarning')
        channel.close.assert_called_once()

    def test_exec_failure_not_reported_success(self):
        client, channel = Mock(), Mock()
        channel.recv_ready.return_value = False
        channel.recv_stderr_ready.return_value = False
        channel.exit_status_ready.return_value = True
        channel.recv_exit_status.return_value = 1
        client.exec_command.return_value = (Mock(), SimpleNamespace(channel=channel), Mock())
        with self.assertRaises(RuntimeError):
            _exec(client, 'bad-command', 1)
        channel.close.assert_called_once()

    def test_shell_reads_config_prompt(self):
        channel = Mock()
        channel.recv_ready.side_effect = [True, False]
        channel.recv.return_value = b'configure terminal\r\nSW1(config)#'
        channel.closed = False
        with patch('modules.ssh_runner.time.monotonic', side_effect=[0, 0, 0, 0, 0, .2, .4]), patch('modules.ssh_runner.time.sleep'):
            text, prompt = _shell_read(channel, 30, 'SW1')
        self.assertEqual(prompt, 'SW1(config)#')

    def test_worker_never_reads_tk_or_schedules_callbacks(self):
        from modules.advanced_pages import SSHAutomationPage
        page = SSHAutomationPage.__new__(SSHAutomationPage)
        page._busy = False
        page._results = queue.Queue()
        owner = threading.get_ident()
        def main_thread_only(*args, **kwargs):
            self.assertEqual(threading.get_ident(), owner)
        page.status = Mock()
        page.status.set.side_effect = main_thread_only
        page.output = Mock()
        page.output.delete.side_effect = main_thread_only
        page.parent = Mock()
        page.parent.after.side_effect = main_thread_only
        page._snapshot = Mock(side_effect=lambda: (main_thread_only() or self.options()))
        observed = []
        def execute(commands, options):
            observed.append(threading.get_ident())
            self.assertEqual(options['host'], '192.0.2.1')
            return 'done'
        page._execute = execute
        page._start_job(['show version'])
        self.assertEqual(page._results.get(timeout=2), ('done', None, False))
        self.assertNotEqual(observed[0], owner)

    def test_result_ignored_after_navigation(self):
        from modules.advanced_pages import SSHAutomationPage
        page = SSHAutomationPage.__new__(SSHAutomationPage)
        page.output = Mock()
        page.output.winfo_exists.return_value = False
        page.parent = Mock()
        page._poll_result()
        page.parent.after.assert_not_called()


if __name__ == '__main__':
    unittest.main()
