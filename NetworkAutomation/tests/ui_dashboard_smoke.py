"""Windows: py -3 tests/ui_dashboard_smoke.py. Isolated data; no API/network execution."""
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
test_data=tempfile.TemporaryDirectory()
os.environ['NETWORK_AUTOMATION_DATA_DIR']=test_data.name
import tkinter as tk
from tkinter import ttk
from modules.dark_dashboard import DarkDashboard

root=tk.Tk();errors=[];root.report_callback_exception=lambda *args:errors.append(args)
from modules.ui_theme import apply_theme
style=apply_theme(root)
content=tk.Frame(root);content.pack(fill='both',expand=True)
app=SimpleNamespace(root=root,content=content,show_daily_audit=Mock(),show_noc_dashboard=Mock(),show_alerts=Mock(),show_incident_center=Mock(),
    _quick_run_all=Mock(),_quick_choose_excel=Mock(),_quick_poll=Mock(),
    _daily_audit_dashboard_summary=lambda:('Chưa cấu hình','Mở Daily Audit để thiết lập',None))
try:
    dashboard=DarkDashboard(app)
    for width,height in [(1400,800),(1024,768),(800,600)]:
        root.geometry(f'{width}x{height}')
        for _ in range(5):root.update()
        assert dashboard.columns in (2,3,5)
        for card in dashboard.cards:
            assert card.winfo_ismapped()
            assert card.winfo_rootx()+card.winfo_width()<=root.winfo_rootx()+root.winfo_width()
        dashboard.hero_action.invoke();app.show_noc_dashboard.assert_called();app.show_noc_dashboard.reset_mock()
        dashboard.toggle_quick();root.update();assert app.quick_ip_text.winfo_ismapped()
        app.quick_run_btn.invoke();app._quick_run_all.assert_called();app._quick_run_all.reset_mock()
        dashboard.toggle_quick();root.update()
        assert not app.quick_ip_text.winfo_ismapped()
        dashboard.canvas.yview_moveto(1);root.update();assert dashboard.events.winfo_ismapped()
        assert dashboard.events['style']=='NOC.Treeview'
    dashboard.frame.destroy();root.update()
    assert dashboard.closed and dashboard.after_id is None
    assert not errors,errors
    print('PASS: native dashboard sizes, cards, NOC/One-Click callbacks, scroll, cleanup. No network calls.')
finally:
    root.destroy();test_data.cleanup()
