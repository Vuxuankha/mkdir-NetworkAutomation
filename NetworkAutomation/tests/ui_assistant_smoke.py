"""Run on Windows: py -3 tests/ui_assistant_smoke.py (no API calls)."""
import sys
import os
import tempfile
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
test_data=tempfile.TemporaryDirectory()
os.environ["NETWORK_AUTOMATION_DATA_DIR"]=test_data.name
import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace
from unittest.mock import patch
from modules.global_assistant import GlobalAssistant

root=tk.Tk();root.geometry('1000x700');errors=[]
root.report_callback_exception=lambda *args:errors.append(args)
style=ttk.Style();style.theme_use('clam')
app=SimpleNamespace(root=root,current_page='Quét mạng',scan_results=[{'ip':'192.0.2.1','status':'Online'}])
assistant=GlobalAssistant(app)
try:
    assistant.open();window=assistant.window
    for width,height in [(1200,850),(960,780),(800,640),(640,700)]:
        window.geometry(f'{width}x{height}');root.update()
        for widget in [assistant.prompt,assistant.send_button,assistant.progress]:
            assert widget.winfo_ismapped(),str(widget)
            assert widget.winfo_rooty()+widget.winfo_height()<=window.winfo_rooty()+window.winfo_height(),str(widget)
            assert widget.winfo_rootx()+widget.winfo_width()<=window.winfo_rootx()+window.winfo_width(),str(widget)
    assistant.template('Kiểm tra thiết bị');assistant.context();root.update()
    assert '192.0.2.1' in assistant.prompt.get('1.0','end')
    assistant.append_chat('Kết quả kiểm tra thử','ai')
    assert assistant.chat['state']=='disabled'
    window.withdraw();assistant.open();root.update();assert assistant.window is window
    assistant.tabs.select(1);root.update();assert assistant.task_list.winfo_ismapped()
    assistant.tabs.select(2);root.update();assert assistant.key_label.winfo_ismapped()
    assistant.provider.set('OpenAI');assistant.model.set('test-openai-model');assistant.save_ai_config()
    assistant.provider.set('Gemini');assistant.model.set('test-gemini-model');assistant.save_ai_config()
    assistant.provider.set('OpenAI');assistant.change_provider();assert assistant.model.get()=='test-openai-model'
    with patch('modules.monitor_extensions.ai_analyze',return_value='OK') as test_api:
        assistant.test_ai_connection()
        end=time.monotonic()+5
        while assistant.busy and time.monotonic()<end:root.update();time.sleep(.01)
        assert not assistant.busy
        assert 'thành công' in assistant.status.get()
        test_api.assert_called_once_with('Trả lời đúng một từ: OK','test-openai-model')
    assert not errors,errors
    print('PASS: layout 1200x850/960x780/800x640/640x700, context, readonly chat, persistent window, task/config tabs, provider model persistence, mocked API test.')
finally:
    assistant.shutdown();root.destroy();test_data.cleanup()
