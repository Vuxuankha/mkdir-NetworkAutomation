"""Windows: py -3 tests/ui_all_pages_smoke.py. Isolated temp data, background workers disabled."""
import inspect
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
test_data=tempfile.TemporaryDirectory();os.environ['NETWORK_AUTOMATION_DATA_DIR']=test_data.name
import tkinter as tk
from tkinter import ttk
import main
from database.db import init_database
from modules.ui_theme import PALETTE,apply_theme

class IdleEngine:
    def __init__(self,*args,**kwargs):self.thread=None;self.running=False
    def stop(self):pass
    def settings(self):return {'enabled':False,'interval_sec':60,'retention_days':90,'last_run':'','last_status':'Disabled for GUI test'}
    def stats(self):return {'workers_alive':0,'queue':0,'Failed':0}

root=None;patches=[];errors=[]
try:
    init_database();main.ensure_server_monitor_tables()
    for name in ('BackgroundAlertEngine','MonitoringService','JobQueueEngine','RootCauseEngine','AutoAuditSchedulerEngine'):
        item=patch.object(main,name,IdleEngine);item.start();patches.append(item)
    root=tk.Tk();root.report_callback_exception=lambda *args:errors.append(args)
    app=main.NetworkAutomationApp(root,{'username':'gui-test','role':'Admin','bootstrap':True})
    count=0
    methods=[name for name in dir(main.NetworkAutomationApp) if name.startswith('show_') and len(inspect.signature(getattr(main.NetworkAutomationApp,name)).parameters)==1]
    for name in methods:
        getattr(app,name)()
        for size in ('1400x800','800x600'):
            root.geometry(size)
            for _ in range(3):root.update()
            assert root.cget('background')==PALETTE['background'],name
            assert not hasattr(app,'global_assistant'),name
        count+=1;print('Built',name)
    app.show_extensions();root.update()
    def notebooks(widget):
        found=[]
        if isinstance(widget,ttk.Notebook):found.append(widget)
        for child in widget.winfo_children():found.extend(notebooks(child))
        return found
    tabs=notebooks(app.content)[0]
    assert [tabs.tab(tab,'text') for tab in tabs.tabs()]==['Wi-Fi','Camera','Giám sát nền']
    style=ttk.Style(root)
    assert style.lookup('Treeview','fieldbackground')==PALETTE['surface']
    assert style.lookup('TCombobox','fieldbackground',('readonly',))==PALETTE['field']
    dialog=tk.Toplevel(root);entry=tk.Entry(dialog);entry.pack();root.update()
    assert entry.cget('background')==PALETTE['field']
    assert entry.cget('foreground')==PALETTE['text']
    dialog.destroy()
    assert not errors,errors
    print('PASS:',count,'pages; dark shared styles/dialog; 3 extension tabs; no AI; no callback errors.')
finally:
    if root is not None:
        try:
            if 'app' in globals():app.on_close()
            else:root.destroy()
        except tk.TclError:pass
    for item in reversed(patches):item.stop()
    test_data.cleanup()
