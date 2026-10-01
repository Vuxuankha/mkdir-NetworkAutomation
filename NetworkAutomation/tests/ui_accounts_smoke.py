"""Windows: py -3 tests/ui_accounts_smoke.py. Temp data; no network operations."""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
test_data = tempfile.TemporaryDirectory()
os.environ['NETWORK_AUTOMATION_DATA_DIR'] = test_data.name
import tkinter as tk
import main
from modules import accounts
from modules.account_ui import password_dialog
from modules.nms_v5 import authenticate
from modules.ui_theme import apply_theme


class IdleEngine:
    def __init__(self, *args, **kwargs):
        self.thread = None
        self.threads = []
        self.running = False
    def stop(self):
        pass


def fill(dialog, **fields):
    for key, value in fields.items():
        dialog.fields[key].set(value)


def check_footer(dialog):
    widget = dialog.save_button
    assert widget.winfo_ismapped()
    assert widget.winfo_rooty() >= dialog.window.winfo_rooty()
    assert widget.winfo_rooty()+widget.winfo_height() <= dialog.window.winfo_rooty()+dialog.window.winfo_height()
    assert widget.winfo_rootx()+widget.winfo_width() <= dialog.window.winfo_rootx()+dialog.window.winfo_width()


root = None
patches = []
errors = []
try:
    for name in ('BackgroundAlertEngine', 'MonitoringService', 'JobQueueEngine', 'RootCauseEngine', 'AutoAuditSchedulerEngine'):
        item = patch.object(main, name, IdleEngine)
        item.start()
        patches.append(item)
    main.init_database()
    main.ensure_server_monitor_tables()
    root = tk.Tk()
    root.report_callback_exception = lambda *args: errors.append(args)
    app = main.NetworkAutomationApp(root)
    menu = app.account_header.menu
    assert [menu.entrycget(i, 'label') for i in (0, 1, 2, 4)] == ['Hồ sơ cá nhân', 'Đổi mật khẩu', 'Nhật ký hoạt động', 'Đăng xuất']
    assert 'Quản lý tài khoản' in app.nav_buttons
    for size in ('1400x800', '800x600'):
        root.geometry(size)
        root.update()
        assert app.account_header.button.winfo_ismapped()
    app.show_user_roles()
    page = app.user_role_page.page
    editor = page.add()
    for scale in (1.333333, 1.666667, 2.0):
        root.tk.call('tk', 'scaling', scale)
        apply_theme(root)
        for size in ('500x530', '360x300'):
            editor.window.geometry(size)
            root.update()
            check_footer(editor)
            editor.panel.canvas.yview_moveto(1)
            root.update()
            check_footer(editor)
    fill(editor, username='admin', password='short', confirm='short')
    editor.save_button.invoke()
    root.update()
    assert editor.window.winfo_exists()
    fill(editor, password='AdminPass123!', confirm='AdminPass123!')
    editor.save_button.invoke()
    root.update()
    assert not app.session_user.get('bootstrap')
    assert app.session_user['id'] == authenticate('admin', 'AdminPass123!')['id']
    assert 'admin' in app.account_header.button.cget('text') or root.winfo_width() < 1100
    menu.invoke(0)
    root.update()
    for child in root.winfo_children():
        if isinstance(child, tk.Toplevel):
            assert child.title() == 'Hồ sơ cá nhân'
            child.destroy()
    editor = page.add()
    fill(editor, username='technician', password='TechPass123!', confirm='TechPass123!', role='Operator')
    editor.save_button.invoke()
    root.update()
    tech = next(row for row in accounts.list_users(app.session_user) if row['username'] == 'technician')
    page.t.selection_set(str(tech['id']))
    editor = page.edit()
    fill(editor, role='Viewer')
    editor.save_button.invoke()
    root.update()
    assert authenticate('technician', 'TechPass123!')['role'] == 'Viewer'
    dialog = password_dialog(root, app.session_user)
    fill(dialog, current='incorrect', password='NewPassword123!', confirm='NewPassword123!')
    dialog.save_button.invoke()
    root.update()
    assert dialog.window.winfo_exists()
    fill(dialog, current='AdminPass123!')
    dialog.save_button.invoke()
    root.update()
    assert authenticate('admin', 'NewPassword123!')
    with patch('modules.account_ui.messagebox.askyesno', return_value=True):
        page.delete()
    assert authenticate('technician', 'TechPass123!') is None
    menu.invoke(2)
    root.update()
    assert app.current_page == 'Nhật ký hoạt động'
    viewer = accounts.create_user(app.session_user, 'viewer', 'ViewerPass123!', 'Viewer')
    menu.invoke(4)
    assert app.exit_reason == 'logout'
    root = tk.Tk()
    root.report_callback_exception = lambda *args: errors.append(args)
    app = main.NetworkAutomationApp(root, viewer)
    root.geometry('800x600')
    root.update()
    assert 'Quản lý tài khoản' not in app.nav_buttons
    assert app.account_header.button.winfo_ismapped()
    app.show_audit_log()
    root.update()
    assert all(row['username'] == 'viewer' for row in accounts.activity_rows(viewer))
    assert not errors, errors
    app.on_close()
    print('PASS: Avatar menu; bootstrap adoption; account CRUD/roles; password verification; compact footer; Viewer scope; logout.')
finally:
    if root is not None:
        try:
            root.destroy()
        except tk.TclError:
            pass
    for item in reversed(patches):
        item.stop()
    test_data.cleanup()
