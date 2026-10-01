import ast
import unittest
from pathlib import Path
from unittest.mock import Mock
from modules import monitor_extensions
from modules.ui_theme import PALETTE
from modules.responsive_layout import cancel_page_timers

ROOT=Path(__file__).resolve().parents[1]

def luminance(color):
    channels=[int(color[index:index+2],16)/255 for index in (1,3,5)]
    channels=[value/12.92 if value<=.04045 else ((value+.055)/1.055)**2.4 for value in channels]
    return sum(value*weight for value,weight in zip(channels,(.2126,.7152,.0722)))

def contrast(first,second):
    values=sorted((luminance(first),luminance(second)))
    return (values[1]+.05)/(values[0]+.05)

class ReleaseTests(unittest.TestCase):
    def test_text_and_state_colors_readable_on_dark_surfaces(self):
        for fg in ('text','muted','accent','success','danger','warning','pink'):
            for bg in ('background','surface','surface_alt','field'):
                self.assertGreaterEqual(contrast(PALETTE[fg],PALETTE[bg]),4.5,(fg,bg))
        for bg in ('primary','hover','selection','danger_bg','success_bg'):
            self.assertGreaterEqual(contrast(PALETTE['text'],PALETTE[bg]),4.5,bg)
    def test_ai_entry_points_and_endpoints_are_gone(self):
        self.assertFalse(hasattr(monitor_extensions,'ai_analyze'))
        self.assertFalse(hasattr(monitor_extensions,'gemini_analyze'))
        for path in [ROOT/'main.py',*(ROOT/'modules').glob('*.py')]:
            source=path.read_text()
            for marker in ('global_assistant','api.openai.com','generativelanguage.googleapis.com','OPENAI_API_KEY','GEMINI_API_KEY'):
                self.assertNotIn(marker,source,str(path))
    def test_camera_wifi_and_history_remain_available(self):
        for name in ('wifi_diagnostics','save_camera','cameras','check_camera','history','ensure_tables'):
            self.assertTrue(callable(getattr(monitor_extensions,name,None)),name)
    def test_no_legacy_light_backgrounds_in_any_page(self):
        forbidden={'white','#ffffff','#f3f4f6','#f9fafb','#f8fafc'}
        for path in [ROOT/'main.py',*(ROOT/'modules').glob('*.py')]:
            tree=ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node,ast.keyword) and node.arg in ('bg','background','fieldbackground'):
                    for value in ast.walk(node.value):
                        if isinstance(value,ast.Constant) and isinstance(value.value,str):
                            self.assertNotIn(value.value.lower(),forbidden,(str(path),value.lineno))
    def test_page_cleanup_keeps_root_monitoring_callbacks(self):
        child=Mock(_tclCommands=['child_tick']);child.winfo_children.return_value=[]
        container=Mock(_tclCommands=['page_tick']);container.winfo_children.return_value=[child]
        responses={('after','info'):('page_timer','child_timer','service_timer'),
                   ('after','info','page_timer'):('page_tick','timer'),
                   ('after','info','child_timer'):('child_tick','timer'),
                   ('after','info','service_timer'):('root_service_tick','timer')}
        container.tk.call.side_effect=lambda *args:responses[args]
        cancel_page_timers(container)
        container.after_cancel.assert_called_once_with('page_timer')
        child.after_cancel.assert_called_once_with('child_timer')

if __name__=='__main__':unittest.main()
