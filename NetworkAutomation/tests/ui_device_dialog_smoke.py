"""Windows: py -3 tests/ui_device_dialog_smoke.py. Temp database; no network calls."""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
test_data=tempfile.TemporaryDirectory();os.environ['NETWORK_AUTOMATION_DATA_DIR']=test_data.name
import tkinter as tk
from database.db import init_database
from modules.ui_theme import apply_theme
from modules.device_manager import device_manager
from main import NetworkAutomationApp

root=tk.Tk();root.geometry('1000x700');apply_theme(root);init_database();errors=[]
root.report_callback_exception=lambda *args:errors.append(args)
app=NetworkAutomationApp.__new__(NetworkAutomationApp);app.root=root;app.add_activity=Mock();app.refresh_device_manager=Mock()

def check_buttons(editor):
    for widget in (editor.save_button,editor.cancel_button):
        assert widget.winfo_ismapped(),str(widget)
        assert widget.winfo_rooty()>=editor.window.winfo_rooty(),str(widget)
        assert widget.winfo_rooty()+widget.winfo_height()<=editor.window.winfo_rooty()+editor.window.winfo_height(),str(widget)
        assert widget.winfo_rootx()+widget.winfo_width()<=editor.window.winfo_rootx()+editor.window.winfo_width(),str(widget)

try:
    for index,scale in enumerate((1.333333,1.666667,2.0)):
        root.tk.call('tk','scaling',scale);apply_theme(root)
        app.add_device_dialog();editor=app.device_editor
        for size in ('560x580','450x400','380x300'):
            editor.window.geometry(size)
            for _ in range(4):root.update()
            check_buttons(editor)
            editor.panel.canvas.yview_moveto(1);root.update();check_buttons(editor)
        editor.vars['ip'].set('bad-ip');editor.save_button.invoke();root.update()
        assert editor.window.winfo_exists();assert 'không hợp lệ' in editor.status.get()
        ip='192.0.2.'+str(90+index);editor.vars['ip'].set(ip);editor.vars['hostname'].set('GUI Test')
        editor.save_button.invoke();root.update();assert not editor.window.winfo_exists()
        device=next(row for row in device_manager.get_devices() if row['ip']==ip)
        app.get_selected_device_id=lambda value=device['id']:value
        app.edit_selected_device();editor=app.device_editor
        editor.window.geometry('380x300');root.update();check_buttons(editor)
        assert editor.vars['hostname'].get()=='GUI Test'
        editor.vars['hostname'].set('Edited GUI Test');editor.save_button.invoke();root.update()
        assert device_manager.get_device(device['id'])['hostname']=='Edited GUI Test'
    assert app.refresh_device_manager.call_count==6
    assert not errors,errors
    print('PASS: Add/Edit footer visible at 560x580, 450x400, 380x300; 100/125/150% equivalent Tk scaling; real temp CRUD; refresh.')
finally:
    root.destroy();test_data.cleanup()
