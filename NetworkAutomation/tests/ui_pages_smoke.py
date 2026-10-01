"""Windows GUI check: py -3 tests/ui_pages_smoke.py. Uses isolated temp data, no network checks."""
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
test_data=tempfile.TemporaryDirectory()
os.environ['NETWORK_AUTOMATION_DATA_DIR']=test_data.name
import tkinter as tk
from tkinter import ttk
from database.db import init_database
from modules.extension_page import ExtensionPage
from modules.advanced_pages import SSHAutomationPage
from modules.extra_pages import SettingsPage,ensure_extra_tables
from main import NetworkAutomationApp

root=tk.Tk();root.geometry('1000x700');errors=[]
root.report_callback_exception=lambda *args:errors.append(args)
from modules.ui_theme import apply_theme
style=apply_theme(root);init_database();ensure_extra_tables()

def contained(widget,container):
    assert widget.winfo_ismapped(),str(widget)
    assert widget.winfo_rootx()>=container.winfo_rootx(),str(widget)
    assert widget.winfo_rootx()+widget.winfo_width()<=container.winfo_rootx()+container.winfo_width(),str(widget)

try:
    for kind in ('extensions','ssh','settings','scan'):
        container=ttk.Frame(root);container.pack(fill='both',expand=True)
        if kind=='extensions':page=ExtensionPage(container)
        elif kind=='ssh':page=SSHAutomationPage(container)
        elif kind=='settings':page=SettingsPage(container)
        else:
            page=NetworkAutomationApp.__new__(NetworkAutomationApp);page.content=container
            page.clear_content=lambda:None;page.set_page_title=lambda *args:None
            page.show_network_scan()
        for width,height in [(1200,850),(1000,700),(800,600)]:
            root.geometry(f'{width}x{height}')
            for _ in range(5):root.update()
            if kind=='extensions':
                tabs=page.winfo_children()[0]
                for tab in tabs.tabs():
                    tabs.select(tab)
                    for _ in range(5):root.update()
                    contained(root.nametowidget(tab),container)
                    if tabs.tab(tab,'text')=='Camera':contained(page.camera_list,container)
            elif kind=='ssh':contained(page.commands,container);contained(page.output,container)
            elif kind=='settings':contained(page.panel.canvas,container)
            else:
                for widget in (page.network_entry,page.scan_button,page.scan_search_entry,page.scan_sort_combo,page.scan_table):contained(widget,container)
        container.destroy();root.update()
    assert not errors,errors
    print('PASS: pages built/resized at 1200x850, 1000x700, 800x600; no network/API calls.')
finally:
    root.destroy();test_data.cleanup()
