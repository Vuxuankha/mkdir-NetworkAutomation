"""Headless Tk smoke test: xvfb-run -a python tests/ui_smoke.py [screenshot_dir]."""
import sys
import time
from pathlib import Path
from unittest.mock import patch
import tkinter as tk
from PIL import ImageGrab
from test_auto_ip import AutoIPTests, FakeAdapter, USER
from modules import auto_ip as a

class Dummy:
    def __init__(self, *args, **kwargs): pass
    def stop(self): pass

fixture = AutoIPTests()
fixture.setUp()
root = None
patches = []
try:
    import main
    for key in ('BackgroundAlertEngine', 'MonitoringService', 'JobQueueEngine', 'RootCauseEngine'):
        p = patch.object(main, key, Dummy)
        p.start()
        patches.append(p)
    root = tk.Tk()
    errors = []
    root.report_callback_exception = lambda *args: errors.append(args)
    app = main.NetworkAutomationApp(root, USER)
    app.show_auto_ip()
    app.auto_ip_engine.adapter_factory = FakeAdapter
    page = app.auto_ip_page
    assert len(page.notebook.tabs()) == 3
    assert app.current_page == 'T\u1ef1 \u0111\u1ed9ng IP/Excel'
    page.default_profile.set('Lab')
    page.authorized.set(True)
    page.text.insert('1.0', '192.0.2.1\n192.0.2.2')
    page.import_text()
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and app.auto_ip_engine.running:
        root.update()
        time.sleep(.02)
    for _ in range(40):
        root.update()
        time.sleep(.02)
    assert not app.auto_ip_engine.running
    assert len(page.table.get_children()) > 4
    assert not errors, errors
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/tmp/autoip-ui')
    output.mkdir(parents=True, exist_ok=True)
    root.geometry('1400x900')
    root.update()
    ImageGrab.grab().save(output / 'autoip_ui_1400.png')
    page.notebook.select(1)
    root.update()
    ImageGrab.grab().save(output / 'autoip_profiles.png')
    page.notebook.select(2)
    page.refresh_history()
    root.update()
    assert page.history_table.get_children()
    ImageGrab.grab().save(output / 'autoip_history.png')
    app.show_dashboard()
    app.show_auto_ip()
    root.geometry('980x600')
    root.update()
    ImageGrab.grab().save(output / 'autoip_ui_980.png')
    # A page change must not stop the workflow; only explicit Stop / app exit does.
    class Slow(FakeAdapter):
        def ping(self):
            self.stop.wait(.5)
            self.check()
            return super().ping()
    app.auto_ip_engine.adapter_factory = Slow
    page = app.auto_ip_page
    page.authorized.set(True)
    page.start()
    assert app.auto_ip_engine.running
    app.show_dashboard()
    assert app.auto_ip_engine.running
    app.auto_ip_engine.stop()
    app.auto_ip_engine.thread.join(6)
    app.show_auto_ip()
    for _ in range(40):
        root.update()
        time.sleep(.02)
    assert not errors, errors
    app.on_close()
    root = None
    print('PASS: 3 tabs, import/auto-start, live results, history, re-entry, navigation while running, stop, close, no Tk callback errors.')
finally:
    if root is not None:
        try: root.destroy()
        except tk.TclError: pass
    for p in reversed(patches): p.stop()
    fixture.tearDown()
