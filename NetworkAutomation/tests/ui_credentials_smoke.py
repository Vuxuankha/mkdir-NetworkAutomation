"""Exercise the actual modal credential form; isolated data and no network."""
import os,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
with tempfile.TemporaryDirectory(prefix='qa-credential-ui-') as folder:
 os.environ['NETWORK_AUTOMATION_DATA_DIR']=folder
 import tkinter as tk
 from modules.nms_v5 import CredentialManagerPage,encrypt_secret,decrypt_secret
 root=tk.Tk();errors=[];root.report_callback_exception=lambda *e:errors.append(e)
 page=CredentialManagerPage.__new__(CredentialManagerPage);page.parent=root
 expected='  password with spaces  '
 def submit():
  window=next(x for x in root.winfo_children() if isinstance(x,tk.Toplevel))
  fields={int(x.grid_info()['row']):x for x in window.winfo_children() if isinstance(x,tk.Entry)}
  fields[0].insert(0,'lab-test');fields[4].insert(0,expected)
  next(x for x in window.winfo_children() if isinstance(x,tk.Button)).invoke()
 try:
  root.after(50,submit)
  result=page._dialog('Credential test')
  assert result['secret']==expected,'Credential form changed leading/trailing password spaces'
  assert decrypt_secret(encrypt_secret(result['secret']))==expected
  assert not errors,errors
  print('PASS: actual credential modal preserves exact password and encrypt/decrypt round trip.')
 finally:
  root.destroy()
