"""Actual Tk SSH page + loopback SSH transport, isolated data."""
import os,sys,tempfile,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));sys.path.insert(0,str(Path(__file__).resolve().parent))
with tempfile.TemporaryDirectory(prefix='qa-ssh-ui-') as folder:
 os.environ['NETWORK_AUTOMATION_DATA_DIR']=folder
 import tkinter as tk
 from tkinter import ttk
 from test_qa153 import LocalSSHHost
 from modules.advanced_pages import SSHAutomationPage
 from modules.ui_theme import apply_theme
 root=tk.Tk();apply_theme(root);root.geometry('1000x700')
 errors=[];activities=[];threads=[]
 root.report_callback_exception=lambda *e:errors.append(e)
 try:
  frame=ttk.Frame(root);frame.pack(fill='both',expand=True)
  page=SSHAutomationPage(frame,activities.append,worker_threads=threads)
  with LocalSSHHost([(b'hostname LAB\n',b'',0)]) as host:
   page.host.set('127.0.0.1');page.port.set(str(host.port))
   page.username.set('tester');page.password.set(LocalSSHHost.password)
   page.commands.insert('1.0','show running-config')
   page.run_commands()
   deadline=time.monotonic()+10
   while page._busy and time.monotonic()<deadline:
    root.update();time.sleep(.01)
   assert not page._busy,'SSH UI operation timed out'
   assert page.status.get()=='Completed',page.output.get('1.0','end')
   assert 'hostname LAB' in page.output.get('1.0','end')
   assert len(activities)==1
   assert len(threads)==1
   threads[0].join(2);assert not threads[0].is_alive()
  assert not errors,errors
  print('PASS: actual SSH page connects to loopback server, exact password authentication, queue result, activity callback and tracked worker completion.')
 finally:
  root.destroy()
