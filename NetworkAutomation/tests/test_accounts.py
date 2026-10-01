import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock, patch

from database import db
from modules import accounts
from modules.nms_v5 import authenticate, has_local_users, LoginDialog
from modules.account_ui import AccountDialog

BOOTSTRAP = {'username': 'local-admin', 'role': 'Admin', 'bootstrap': True}


class AccountTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        (root / 'VERSION.txt').write_text('1.5.0')
        self.patches = [patch.object(db, 'DB_PATH', root / 'test.db'), patch.object(db, 'BASE_DIR', root), patch.object(db, 'RESOURCE_DIR', root)]
        for item in self.patches:
            item.start()
        self.admin = accounts.create_user(BOOTSTRAP, 'admin', 'AdminPass123!', 'Admin')

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def tech(self):
        return accounts.create_user(self.admin, 'technician', 'TechPass123!', 'Operator')

    def test_authentication_and_profile_exclude_password_hash(self):
        user = authenticate('admin', 'AdminPass123!')
        self.assertEqual(user, self.admin)
        self.assertNotIn('password_hash', accounts.get_profile(user))
        self.assertIsNone(authenticate('admin', 'incorrect'))

    def test_create_update_lock_unlock_delete(self):
        user = self.tech()
        user = accounts.update_user(self.admin, user['id'], 'tech-new', 'Viewer', False)
        self.assertEqual(user['role'], 'Viewer')
        self.assertIsNone(authenticate('tech-new', 'TechPass123!'))
        accounts.update_user(self.admin, user['id'], 'tech-new', 'Operator', True)
        self.assertIsNotNone(authenticate('tech-new', 'TechPass123!'))
        accounts.delete_user(self.admin, user['id'])
        self.assertEqual(len(accounts.list_users(self.admin)), 1)

    def test_operator_and_viewer_cannot_manage_accounts(self):
        tech = self.tech()
        for role in ('Operator', 'Viewer'):
            tech = accounts.update_user(self.admin, tech['id'], tech['username'], role, True)
            operations = [lambda: accounts.list_users(tech), lambda: accounts.create_user(tech, 'evil', 'Password123!'),
                          lambda: accounts.update_user(tech, self.admin['id'], 'admin', 'Viewer', False),
                          lambda: accounts.delete_user(tech, self.admin['id']), lambda: accounts.reset_password(tech, self.admin['id'], 'Password123!')]
            for op in operations:
                with self.assertRaises(ValueError):
                    op()

    def test_self_delete_disable_demote_are_rejected(self):
        operations = [lambda: accounts.delete_user(self.admin, self.admin['id']),
                      lambda: accounts.update_user(self.admin, self.admin['id'], 'admin', 'Admin', False),
                      lambda: accounts.update_user(self.admin, self.admin['id'], 'admin', 'Operator', True)]
        for operation in operations:
            with self.assertRaises(ValueError):
                operation()
        self.assertEqual(accounts.get_profile(self.admin)['role'], 'Admin')

    def test_admin_can_rename_own_account(self):
        user = accounts.update_user(self.admin, self.admin['id'], 'admin-new', 'Admin', True)
        self.assertEqual(accounts.get_profile(self.admin)['username'], 'admin-new')
        self.assertEqual(authenticate('admin-new', 'AdminPass123!')['id'], user['id'])

    def test_concurrent_admin_deletes_keep_one_enabled_admin(self):
        other = accounts.create_user(self.admin, 'admin-two', 'OtherPass123!', 'Admin')
        def remove(actor, target):
            try:
                accounts.delete_user(actor, target['id'])
                return True
            except ValueError:
                return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(remove, self.admin, other), pool.submit(remove, other, self.admin)]
            self.assertEqual(sum(f.result() for f in futures), 1)
        with db.get_connection() as c:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM app_users WHERE role='Admin' AND enabled=1").fetchone()[0], 1)

    def test_stale_admin_role_is_checked_in_database(self):
        other = accounts.create_user(self.admin, 'admin-two', 'OtherPass123!', 'Admin')
        accounts.update_user(self.admin, other['id'], other['username'], 'Viewer', True)
        with self.assertRaises(ValueError):
            accounts.create_user(other, 'forbidden', 'Password123!')

    def test_duplicate_invalid_fields_and_weak_password_do_not_write(self):
        cases = [('admin', 'Password123!', 'Viewer'), ('bad name', 'Password123!', 'Viewer'),
                 ('new', 'short', 'Viewer'), ('new', 'Password123!', 'Unknown')]
        for username, password, role in cases:
            with self.assertRaises(ValueError):
                accounts.create_user(self.admin, username, password, role)
        self.assertEqual(len(accounts.list_users(self.admin)), 1)

    def test_own_password_requires_current_password_and_confirmation(self):
        for old, new, confirm in [('wrong', 'NewPassword123!', 'NewPassword123!'),
                                  ('AdminPass123!', 'NewPassword123!', 'Mismatch123!')]:
            with self.assertRaises(ValueError):
                accounts.change_password(self.admin, old, new, confirm)
        self.assertIsNotNone(authenticate('admin', 'AdminPass123!'))
        accounts.change_password(self.admin, 'AdminPass123!', 'NewPassword123!', 'NewPassword123!')
        self.assertIsNone(authenticate('admin', 'AdminPass123!'))
        self.assertIsNotNone(authenticate('admin', 'NewPassword123!'))

    def test_admin_resets_other_password_without_logging_secrets(self):
        tech = self.tech()
        accounts.reset_password(self.admin, tech['id'], 'ResetPassword123!')
        self.assertIsNone(authenticate('technician', 'TechPass123!'))
        self.assertIsNotNone(authenticate('technician', 'ResetPassword123!'))
        events = accounts.activity_rows(self.admin)
        self.assertIn('Đặt lại mật khẩu', [r['action'] for r in events])
        self.assertNotIn('ResetPassword123!', json.dumps(events))
        with self.assertRaises(ValueError):
            accounts.reset_password(self.admin, self.admin['id'], 'ResetPassword123!')

    def test_activity_log_scope_and_search(self):
        tech = self.tech()
        accounts.change_password(tech, 'TechPass123!', 'NewTechPass123!', 'NewTechPass123!')
        events = accounts.activity_rows(tech)
        self.assertTrue(events)
        self.assertTrue(all(r['username'] == tech['username'] for r in events))
        self.assertEqual(len(accounts.activity_rows(tech, 'Đổi mật khẩu')), 1)
        self.assertFalse(accounts.activity_rows(tech, 'Thêm tài khoản'))
        self.assertGreater(len(accounts.activity_rows(self.admin)), len(events))

    def test_all_disabled_accounts_do_not_reenable_bootstrap(self):
        with db.get_connection() as c:
            c.execute('UPDATE app_users SET enabled=0')
        self.assertTrue(has_local_users())
        self.assertIsNone(authenticate('admin', 'AdminPass123!'))
        with self.assertRaises(ValueError):
            accounts.create_user(BOOTSTRAP, 'backdoor', 'Password123!', 'Admin')

    def test_first_account_requires_enabled_admin_and_bootstrap_expires(self):
        with self.assertRaises(ValueError):
            accounts.list_users(BOOTSTRAP)
        with db.get_connection() as c:
            c.execute('DELETE FROM app_users')
        for role, enabled in [('Viewer', True), ('Admin', False)]:
            with self.assertRaises(ValueError):
                accounts.create_user(BOOTSTRAP, 'first', 'Password123!', role, enabled)
        first = accounts.create_user(BOOTSTRAP, 'first', 'Password123!', 'Admin')
        self.assertEqual(authenticate('first', 'Password123!'), first)
        with self.assertRaises(ValueError):
            accounts.list_users(BOOTSTRAP)

    def test_dialog_error_keeps_form_open_for_retry(self):
        dialog = AccountDialog.__new__(AccountDialog)
        dialog.saving = False
        dialog.window = Mock()
        dialog.window.winfo_exists.return_value = True
        dialog.save_button = Mock()
        dialog.status = Mock()
        dialog.fields = {'username': Mock(get=Mock(return_value='admin'))}
        dialog.action = Mock(side_effect=ValueError('Tên đăng nhập đã tồn tại.'))
        dialog.save()
        dialog.window.destroy.assert_not_called()
        dialog.status.set.assert_called_once()
        dialog.save_button.configure.assert_called_with(state='normal')
        dialog.action.side_effect = None
        dialog.save()
        dialog.window.destroy.assert_called_once()


class LogoutTests(unittest.TestCase):
    def test_relogin_uses_fresh_root_and_disables_bootstrap(self):
        import main
        roots = [Mock(), Mock()]
        users = [{'id': 1, 'username': 'admin', 'role': 'Admin'}, {'id': 2, 'username': 'viewer', 'role': 'Viewer'}]
        sessions = [Mock(exit_reason='logout'), Mock(exit_reason='close')]
        with patch('main.tk.Tk', side_effect=roots), patch('modules.ui_theme.apply_theme'), \
             patch('main.LoginDialog') as login, patch('main.NetworkAutomationApp', side_effect=sessions) as app:
            login.return_value.run.side_effect = users
            main.run_application()
            self.assertEqual(login.call_args_list[0].kwargs, {'allow_bootstrap': True})
            self.assertEqual(login.call_args_list[1].kwargs, {'allow_bootstrap': False})
            self.assertEqual(app.call_args_list[1].kwargs, {'session_user': users[1]})
            for root in roots:
                root.mainloop.assert_called_once()

    def test_logout_stops_engines_before_destroying_session(self):
        from main import NetworkAutomationApp
        app = NetworkAutomationApp.__new__(NetworkAutomationApp)
        app.root = Mock()
        app.root.winfo_children.return_value = []
        app._closing = False
        app.topbar = Mock()
        app.sidebar = Mock()
        app.clear_content = Mock()
        app.set_page_title = Mock()
        app._finish_close = Mock()
        engines = ('job_queue_engine', 'monitoring_service', 'background_alert_engine', 'root_cause_engine', 'auto_audit_scheduler', 'auto_ip_engine')
        for name in engines:
            setattr(app, name, Mock())
        with patch('modules.responsive_layout.cancel_page_timers') as cancel:
            app.logout()
        self.assertTrue(app._closing)
        self.assertEqual(app.exit_reason, 'logout')
        cancel.assert_called_once_with(app.root)
        for name in engines:
            getattr(app, name).stop.assert_called_once()
        app._finish_close.assert_called_once()
        app.root.destroy.assert_not_called()
        app.logout()
        app._finish_close.assert_called_once()

    def test_finish_waits_for_worker_then_audits_logout(self):
        from main import NetworkAutomationApp
        app = NetworkAutomationApp.__new__(NetworkAutomationApp)
        app.root = Mock()
        thread = Mock()
        thread.is_alive.return_value = True
        app._closing_threads = [thread]
        app.exit_reason = 'logout'
        app.session_user = {'username': 'admin'}
        app.current_role = 'Admin'
        with patch('main.audit') as audit:
            app._finish_close()
            app.root.after.assert_called_once_with(250, app._finish_close)
            app.root.destroy.assert_not_called()
            audit.assert_not_called()
            thread.is_alive.return_value = False
            app._finish_close()
            app.root.destroy.assert_called_once()
            self.assertEqual(audit.call_args.args[2], 'Đăng xuất')


if __name__ == '__main__':
    unittest.main()
