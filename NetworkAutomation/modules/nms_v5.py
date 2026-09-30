import base64
import hashlib
import hmac
import os
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

from database.db import DB_PATH, init_database

APP_DIR = Path(__file__).resolve().parents[1]
BACKUP_DIR = APP_DIR / 'backups'
BACKUP_DIR.mkdir(exist_ok=True)
KEY_FILE = APP_DIR / 'database' / '.credential.key'


def _now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def _connect():
    init_database()
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def ensure_v5_tables():
    c = _connect()
    try:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS credentials(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            kind TEXT NOT NULL DEFAULT 'SSH',
            username TEXT DEFAULT '',
            secret_enc TEXT NOT NULL,
            port INTEGER,
            note TEXT DEFAULT '',
            created_at TEXT,
            updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS device_credentials(
            device_id INTEGER NOT NULL,
            credential_id INTEGER NOT NULL,
            purpose TEXT NOT NULL DEFAULT 'SSH',
            created_at TEXT,
            UNIQUE(device_id,purpose)
        );
        CREATE TABLE IF NOT EXISTS secure_backup_jobs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            device_id INTEGER NOT NULL,
            credential_id INTEGER NOT NULL,
            command TEXT DEFAULT 'show running-config',
            interval_min INTEGER DEFAULT 1440,
            enabled INTEGER DEFAULT 1,
            last_run TEXT,
            last_status TEXT,
            next_run REAL,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS app_users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'Viewer',
            enabled INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS auth_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            success INTEGER,
            detail TEXT,
            created_at TEXT
        );
        ''')
        c.commit()
    finally:
        c.close()


def _fernet():
    try:
        from cryptography.fernet import Fernet
    except Exception as e:
        raise RuntimeError('Thiếu thư viện cryptography. Hãy chạy: pip install cryptography') from e
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not KEY_FILE.exists():
        key = Fernet.generate_key()
        KEY_FILE.write_bytes(key)
        try:
            os.chmod(KEY_FILE, 0o600)
        except Exception:
            pass
    return Fernet(KEY_FILE.read_bytes().strip())


def encrypt_secret(text):
    return _fernet().encrypt((text or '').encode('utf-8')).decode('ascii')


def decrypt_secret(token):
    return _fernet().decrypt((token or '').encode('ascii')).decode('utf-8')


def _hash_password(password, salt=None):
    salt = salt or os.urandom(16)
    rounds = 240000
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, rounds)
    return f'pbkdf2_sha256${rounds}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}'


def _verify_password(password, stored):
    try:
        algo, rounds, s, expected = stored.split('$', 3)
        if algo != 'pbkdf2_sha256': return False
        salt = base64.b64decode(s)
        got = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, int(rounds))
        return hmac.compare_digest(base64.b64encode(got).decode(), expected)
    except Exception:
        return False


def authenticate(username, password):
    ensure_v5_tables(); c = _connect()
    try:
        r = c.execute('SELECT * FROM app_users WHERE username=? AND enabled=1', (username,)).fetchone()
        ok = bool(r and _verify_password(password, r['password_hash']))
        c.execute('INSERT INTO auth_log(username,success,detail,created_at) VALUES(?,?,?,?)',
                  (username, 1 if ok else 0, 'Đăng nhập thành công' if ok else 'Sai tài khoản hoặc mật khẩu', _now()))
        c.commit()
        return dict(r) if ok else None
    finally:
        c.close()


def has_local_users():
    ensure_v5_tables(); c = _connect()
    try:
        return c.execute('SELECT COUNT(*) FROM app_users WHERE enabled=1').fetchone()[0] > 0
    finally:
        c.close()


def ssh_backup(device, credential, command, destination=None):
    import paramiko
    secret = decrypt_secret(credential['secret_enc'])
    host = device['ip']; port = int(credential['port'] or 22)
    cli = paramiko.SSHClient(); cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        cli.connect(host, port=port, username=credential['username'], password=secret,
                    timeout=10, look_for_keys=False, allow_agent=False)
        stdin, stdout, stderr = cli.exec_command(command or 'show running-config', timeout=30)
        data = stdout.read().decode(errors='replace')
        err = stderr.read().decode(errors='replace')
        if err and not data:
            raise RuntimeError(err.strip())
    finally:
        cli.close()
    if destination is None:
        safe = ''.join(ch if ch.isalnum() or ch in '-_.' else '_' for ch in (device['name'] or host))
        destination = BACKUP_DIR / f"{safe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.cfg"
    destination = Path(destination)
    destination.write_text(data, encoding='utf-8')
    c = _connect()
    try:
        c.execute('INSERT INTO config_backups(device_name,source,file_path,size_bytes,note,created_at) VALUES(?,?,?,?,?,?)',
                  (device['name'] or host, 'SSH mã hóa', str(destination), destination.stat().st_size,
                   f"Credential: {credential['name']}", _now()))
        c.commit()
    finally:
        c.close()
    return destination


class CredentialManagerPage:
    def __init__(self, parent, activity_callback=None):
        ensure_v5_tables(); self.parent=parent; self.activity=activity_callback or (lambda m:None)
        self._build(); self.refresh()

    def _build(self):
        ctl=tk.Frame(self.parent,bg='#F3F4F6'); ctl.pack(fill='x',padx=25,pady=(0,8))
        tk.Button(ctl,text='Thêm Credential',command=self.add,bg='#2563EB',fg='white',relief='flat').pack(side='left')
        tk.Button(ctl,text='Sửa',command=self.edit).pack(side='left',padx=5)
        tk.Button(ctl,text='Gán cho thiết bị',command=self.assign).pack(side='left',padx=5)
        tk.Button(ctl,text='Kiểm tra SSH',command=self.test).pack(side='left',padx=5)
        tk.Button(ctl,text='Xóa',command=self.delete).pack(side='left',padx=5)
        tk.Button(ctl,text='Làm mới',command=self.refresh).pack(side='left',padx=5)
        box=tk.Frame(self.parent,bg='white',bd=1,relief='solid'); box.pack(fill='both',expand=True,padx=25,pady=(0,10))
        cols=('name','kind','username','port','assigned','note','updated')
        self.t=ttk.Treeview(box,columns=cols,show='headings',selectmode='browse')
        for c,h,w in [('name','Tên',180),('kind','Loại',90),('username','Tài khoản',150),('port','Cổng',70),('assigned','Đã gán',90),('note','Ghi chú',260),('updated','Cập nhật',150)]:
            self.t.heading(c,text=h); self.t.column(c,width=w,anchor='w')
        self.t.pack(fill='both',expand=True,padx=8,pady=8)
        tk.Label(self.parent,text='Mật khẩu/community được mã hóa bằng Fernet và không hiển thị lại trên giao diện.',bg='#F3F4F6',fg='#6B7280').pack(anchor='w',padx=25,pady=(0,8))

    def refresh(self):
        for x in self.t.get_children(): self.t.delete(x)
        c=_connect(); rows=c.execute('''SELECT cr.*,COUNT(dc.device_id) assigned FROM credentials cr LEFT JOIN device_credentials dc ON dc.credential_id=cr.id GROUP BY cr.id ORDER BY cr.name''').fetchall(); c.close()
        for r in rows:self.t.insert('','end',iid=str(r['id']),values=(r['name'],r['kind'],r['username'],r['port'] or '-',r['assigned'],r['note'],r['updated_at'] or r['created_at']))

    def _selected(self):
        s=self.t.selection(); return int(s[0]) if s else None

    def _dialog(self,title,row=None):
        w=tk.Toplevel(self.parent); w.title(title); w.geometry('430x330'); w.transient(self.parent.winfo_toplevel()); w.grab_set()
        vals={'name':tk.StringVar(value=(row or {}).get('name','')),'kind':tk.StringVar(value=(row or {}).get('kind','SSH')),
              'username':tk.StringVar(value=(row or {}).get('username','')),'port':tk.StringVar(value=str((row or {}).get('port') or 22)),
              'secret':tk.StringVar(),'note':tk.StringVar(value=(row or {}).get('note',''))}
        labels=[('Tên credential','name'),('Loại','kind'),('Username','username'),('Port','port'),('Mật khẩu / Community','secret'),('Ghi chú','note')]
        for i,(lab,k) in enumerate(labels):
            tk.Label(w,text=lab).grid(row=i,column=0,sticky='w',padx=15,pady=8)
            if k=='kind': z=ttk.Combobox(w,textvariable=vals[k],values=['SSH','SNMPv2c'],state='readonly',width=28)
            else: z=tk.Entry(w,textvariable=vals[k],width=31,show='*' if k=='secret' else '')
            z.grid(row=i,column=1,padx=10,pady=8)
        result={}
        def save():
            if not vals['name'].get().strip(): messagebox.showwarning(title,'Vui lòng nhập tên.',parent=w); return
            if not row and not vals['secret'].get(): messagebox.showwarning(title,'Vui lòng nhập mật khẩu/community.',parent=w); return
            result.update({k:v.get().strip() for k,v in vals.items()}); w.destroy()
        tk.Button(w,text='Lưu',command=save,bg='#2563EB',fg='white',width=12).grid(row=7,column=1,sticky='e',padx=10,pady=15)
        w.wait_window(); return result or None

    def add(self):
        d=self._dialog('Thêm Credential')
        if not d:return
        try: port=int(d['port'] or (161 if d['kind']=='SNMPv2c' else 22))
        except: port=161 if d['kind']=='SNMPv2c' else 22
        c=_connect()
        try:c.execute('INSERT INTO credentials(name,kind,username,secret_enc,port,note,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)',(d['name'],d['kind'],d['username'],encrypt_secret(d['secret']),port,d['note'],_now(),_now()));c.commit()
        except sqlite3.IntegrityError: messagebox.showerror('Credential','Tên credential đã tồn tại.')
        finally:c.close()
        self.activity('Đã thêm credential: '+d['name']); self.refresh()

    def edit(self):
        i=self._selected()
        if not i:return
        c=_connect(); r=c.execute('SELECT * FROM credentials WHERE id=?',(i,)).fetchone(); c.close(); d=self._dialog('Sửa Credential',dict(r))
        if not d:return
        try: port=int(d['port'] or 22)
        except: port=22
        c=_connect()
        try:
            if d['secret']: c.execute('UPDATE credentials SET name=?,kind=?,username=?,secret_enc=?,port=?,note=?,updated_at=? WHERE id=?',(d['name'],d['kind'],d['username'],encrypt_secret(d['secret']),port,d['note'],_now(),i))
            else:c.execute('UPDATE credentials SET name=?,kind=?,username=?,port=?,note=?,updated_at=? WHERE id=?',(d['name'],d['kind'],d['username'],port,d['note'],_now(),i))
            c.commit()
        finally:c.close()
        self.refresh()

    def assign(self):
        cid=self._selected()
        if not cid: messagebox.showinfo('Credential','Chọn một credential trước.'); return
        c=_connect(); devices=[dict(r) for r in c.execute('SELECT id,name,ip FROM network_devices ORDER BY name,ip')]; cred=c.execute('SELECT * FROM credentials WHERE id=?',(cid,)).fetchone(); c.close()
        if not devices: messagebox.showinfo('Credential','Chưa có thiết bị mạng.'); return
        w=tk.Toplevel(self.parent);w.title('Gán Credential');w.geometry('430x180');w.transient(self.parent.winfo_toplevel());w.grab_set()
        labels=[f"{x['name']} ({x['ip']})" for x in devices]; dv=tk.StringVar(value=labels[0]); purpose=tk.StringVar(value='SNMP' if cred['kind']=='SNMPv2c' else 'SSH')
        tk.Label(w,text='Thiết bị').pack(anchor='w',padx=15,pady=(15,3));ttk.Combobox(w,textvariable=dv,values=labels,state='readonly',width=48).pack(padx=15)
        tk.Label(w,text='Mục đích').pack(anchor='w',padx=15,pady=(10,3));ttk.Combobox(w,textvariable=purpose,values=['SSH','SNMP','Backup'],state='readonly',width=20).pack(anchor='w',padx=15)
        def save():
            did=devices[labels.index(dv.get())]['id']; c=_connect();c.execute('INSERT INTO device_credentials(device_id,credential_id,purpose,created_at) VALUES(?,?,?,?) ON CONFLICT(device_id,purpose) DO UPDATE SET credential_id=excluded.credential_id,created_at=excluded.created_at',(did,cid,purpose.get(),_now()));c.commit();c.close();w.destroy();self.refresh()
        tk.Button(w,text='Gán',command=save,bg='#2563EB',fg='white').pack(anchor='e',padx=15,pady=12)

    def test(self):
        i=self._selected()
        if not i:return
        c=_connect(); cr=c.execute('SELECT * FROM credentials WHERE id=?',(i,)).fetchone(); c.close()
        if cr['kind']!='SSH': messagebox.showinfo('Kiểm tra','Chức năng này dùng cho credential SSH.'); return
        host=simpledialog.askstring('Kiểm tra SSH','IP / Host:',parent=self.parent)
        if not host:return
        def work():
            try:
                import paramiko; cli=paramiko.SSHClient();cli.set_missing_host_key_policy(paramiko.AutoAddPolicy());cli.connect(host,port=int(cr['port'] or 22),username=cr['username'],password=decrypt_secret(cr['secret_enc']),timeout=8,look_for_keys=False,allow_agent=False);cli.close();msg='Kết nối SSH thành công.'
            except Exception as e:msg='Không kết nối được SSH:\n'+str(e)
            self.parent.after(0,lambda:messagebox.showinfo('Kiểm tra SSH',msg))
        threading.Thread(target=work,daemon=True).start()

    def delete(self):
        i=self._selected()
        if not i:return
        if not messagebox.askyesno('Xóa Credential','Xóa credential đã chọn? Các gán liên quan cũng sẽ bị xóa.'):return
        c=_connect();c.execute('DELETE FROM device_credentials WHERE credential_id=?',(i,));c.execute('DELETE FROM secure_backup_jobs WHERE credential_id=?',(i,));c.execute('DELETE FROM credentials WHERE id=?',(i,));c.commit();c.close();self.refresh()


class SecureBackupSchedulerPage:
    def __init__(self,parent,activity_callback=None):
        ensure_v5_tables();self.parent=parent;self.activity=activity_callback or (lambda m:None);self._build();self.refresh();self.parent.after(5000,self._tick)
    def _build(self):
        ctl=tk.Frame(self.parent,bg='#F3F4F6');ctl.pack(fill='x',padx=25,pady=(0,8))
        tk.Button(ctl,text='Thêm lịch sao lưu',command=self.add,bg='#2563EB',fg='white',relief='flat').pack(side='left')
        tk.Button(ctl,text='Chạy ngay',command=self.run_now).pack(side='left',padx=5);tk.Button(ctl,text='Bật/Tắt',command=self.toggle).pack(side='left',padx=5);tk.Button(ctl,text='Xóa',command=self.delete).pack(side='left',padx=5);tk.Button(ctl,text='Làm mới',command=self.refresh).pack(side='left',padx=5)
        box=tk.Frame(self.parent,bg='white',bd=1,relief='solid');box.pack(fill='both',expand=True,padx=25,pady=(0,10));cols=('name','device','credential','interval','last','status','enabled');self.t=ttk.Treeview(box,columns=cols,show='headings')
        for c,h,w in [('name','Tên lịch',170),('device','Thiết bị',180),('credential','Credential',160),('interval','Chu kỳ',100),('last','Lần chạy cuối',150),('status','Kết quả',220),('enabled','Bật',60)]:self.t.heading(c,text=h);self.t.column(c,width=w,anchor='w')
        self.t.pack(fill='both',expand=True,padx=8,pady=8)
    def refresh(self):
        for x in self.t.get_children():self.t.delete(x)
        c=_connect();rows=c.execute('''SELECT j.*,d.name device_name,d.ip,cr.name cred_name FROM secure_backup_jobs j JOIN network_devices d ON d.id=j.device_id JOIN credentials cr ON cr.id=j.credential_id ORDER BY j.name''').fetchall();c.close()
        for r in rows:self.t.insert('','end',iid=str(r['id']),values=(r['name'],f"{r['device_name']} ({r['ip']})",r['cred_name'],f"{r['interval_min']} phút",r['last_run'] or '-',r['last_status'] or '-', 'Có' if r['enabled'] else 'Không'))
    def _selected(self):s=self.t.selection();return int(s[0]) if s else None
    def add(self):
        c=_connect();dev=[dict(r) for r in c.execute('SELECT id,name,ip FROM network_devices ORDER BY name')];creds=[dict(r) for r in c.execute("SELECT * FROM credentials WHERE kind='SSH' ORDER BY name")];c.close()
        if not dev or not creds:messagebox.showinfo('Lịch sao lưu','Cần có ít nhất 1 thiết bị và 1 credential SSH.');return
        w=tk.Toplevel(self.parent);w.title('Thêm lịch sao lưu');w.geometry('470x330');w.transient(self.parent.winfo_toplevel());w.grab_set()
        name=tk.StringVar();dl=[f"{x['name']} ({x['ip']})" for x in dev];cl=[x['name'] for x in creds];dv=tk.StringVar(value=dl[0]);cv=tk.StringVar(value=cl[0]);cmd=tk.StringVar(value='show running-config');mins=tk.StringVar(value='1440')
        def apply_profile_command(event=None):
            try:
                from modules.nms_v7 import get_profile_for_device
                did=dev[dl.index(dv.get())]['id'];p=get_profile_for_device(device_id=did)
                if p and p.get('backup_command'):cmd.set(p['backup_command'])
            except Exception:pass
        apply_profile_command()
        for i,(lab,var,vals) in enumerate([('Tên lịch',name,None),('Thiết bị',dv,dl),('Credential SSH',cv,cl),('Lệnh backup',cmd,None),('Chu kỳ (phút)',mins,None)]):
            tk.Label(w,text=lab).grid(row=i,column=0,sticky='w',padx=15,pady=10);z=ttk.Combobox(w,textvariable=var,values=vals,state='readonly',width=35) if vals else tk.Entry(w,textvariable=var,width=38);z.grid(row=i,column=1,padx=10,pady=10)
            if lab=='Thiết bị': z.bind('<<ComboboxSelected>>',apply_profile_command)
        def save():
            if not name.get().strip():messagebox.showwarning('Lịch sao lưu','Nhập tên lịch.',parent=w);return
            try:m=max(1,int(mins.get()))
            except:messagebox.showwarning('Lịch sao lưu','Chu kỳ phải là số phút.',parent=w);return
            did=dev[dl.index(dv.get())]['id'];cid=creds[cl.index(cv.get())]['id'];c=_connect();c.execute('INSERT INTO secure_backup_jobs(name,device_id,credential_id,command,interval_min,enabled,next_run,created_at) VALUES(?,?,?,?,?,1,?,?)',(name.get().strip(),did,cid,cmd.get().strip() or 'show running-config',m,time.time(),_now()));c.commit();c.close();w.destroy();self.refresh()
        tk.Button(w,text='Lưu',command=save,bg='#2563EB',fg='white').grid(row=6,column=1,sticky='e',padx=10,pady=15)
    def run_now(self):
        i=self._selected()
        if i:self._run(i)
    def toggle(self):
        i=self._selected()
        if not i:return
        c=_connect();c.execute('UPDATE secure_backup_jobs SET enabled=CASE enabled WHEN 1 THEN 0 ELSE 1 END WHERE id=?',(i,));c.commit();c.close();self.refresh()
    def delete(self):
        i=self._selected()
        if not i:return
        c=_connect();c.execute('DELETE FROM secure_backup_jobs WHERE id=?',(i,));c.commit();c.close();self.refresh()
    def _tick(self):
        try:
            c=_connect();rows=c.execute('SELECT id FROM secure_backup_jobs WHERE enabled=1 AND next_run<=?',(time.time(),)).fetchall();c.close()
            for r in rows:self._run(r['id'])
            self.parent.after(5000,self._tick)
        except tk.TclError:pass
    def _run(self,i):
        c=_connect();r=c.execute('''SELECT j.*,d.name device_name,d.ip,cr.name cred_name,cr.kind,cr.username,cr.secret_enc,cr.port,cr.note FROM secure_backup_jobs j JOIN network_devices d ON d.id=j.device_id JOIN credentials cr ON cr.id=j.credential_id WHERE j.id=?''',(i,)).fetchone();c.close()
        if not r:return
        def work():
            status=''
            try:
                rr=dict(r);device={'name':rr['device_name'],'ip':rr['ip']};cred={'name':rr['cred_name'],'username':rr['username'],'secret_enc':rr['secret_enc'],'port':rr['port']};dst=ssh_backup(device,cred,rr['command']);status='OK: '+dst.name;self.activity('Sao lưu tự động thành công: '+str(dst))
            except Exception as e:status='Lỗi: '+str(e);self.activity('Sao lưu tự động lỗi: '+str(e))
            c=_connect();c.execute('UPDATE secure_backup_jobs SET last_run=?,last_status=?,next_run=? WHERE id=?',(_now(),status,time.time()+int(r['interval_min'])*60,i));c.commit();c.close()
            try:self.parent.after(0,self.refresh)
            except:pass
        threading.Thread(target=work,daemon=True).start()


class ConfigComparePage:
    def __init__(self,parent,activity_callback=None):
        self.parent=parent;self.activity=activity_callback or (lambda m:None);self._build();self.refresh()
    def _build(self):
        ctl=tk.Frame(self.parent,bg='#F3F4F6');ctl.pack(fill='x',padx=25,pady=(0,8));tk.Label(ctl,text='Bản A:',bg='#F3F4F6').pack(side='left');self.a=tk.StringVar();self.ac=ttk.Combobox(ctl,textvariable=self.a,state='readonly',width=38);self.ac.pack(side='left',padx=5);tk.Label(ctl,text='Bản B:',bg='#F3F4F6').pack(side='left');self.b=tk.StringVar();self.bc=ttk.Combobox(ctl,textvariable=self.b,state='readonly',width=38);self.bc.pack(side='left',padx=5);tk.Button(ctl,text='So sánh',command=self.compare,bg='#2563EB',fg='white',relief='flat').pack(side='left',padx=5);tk.Button(ctl,text='Làm mới',command=self.refresh).pack(side='left')
        box=tk.Frame(self.parent,bg='white',bd=1,relief='solid');box.pack(fill='both',expand=True,padx=25,pady=(0,10));self.text=tk.Text(box,wrap='none',font=('Consolas',10));ys=ttk.Scrollbar(box,orient='vertical',command=self.text.yview);xs=ttk.Scrollbar(box,orient='horizontal',command=self.text.xview);self.text.configure(yscrollcommand=ys.set,xscrollcommand=xs.set);self.text.grid(row=0,column=0,sticky='nsew');ys.grid(row=0,column=1,sticky='ns');xs.grid(row=1,column=0,sticky='ew');box.grid_rowconfigure(0,weight=1);box.grid_columnconfigure(0,weight=1)
    def refresh(self):
        c=_connect();rows=[dict(r) for r in c.execute('SELECT id,device_name,file_path,created_at FROM config_backups WHERE file_path IS NOT NULL ORDER BY id DESC LIMIT 300')];c.close();self.rows=rows;labels=[f"#{r['id']} | {r['device_name']} | {r['created_at']}" for r in rows];self.ac['values']=labels;self.bc['values']=labels
        if labels and not self.a.get():self.a.set(labels[min(1,len(labels)-1)]);self.b.set(labels[0])
    def compare(self):
        import difflib
        vals=list(self.ac['values'])
        if self.a.get() not in vals or self.b.get() not in vals:return
        ra=self.rows[vals.index(self.a.get())];rb=self.rows[vals.index(self.b.get())]
        try:A=Path(ra['file_path']).read_text(encoding='utf-8',errors='replace').splitlines();B=Path(rb['file_path']).read_text(encoding='utf-8',errors='replace').splitlines()
        except Exception as e:messagebox.showerror('So sánh config',str(e));return
        diff=list(difflib.unified_diff(A,B,fromfile=self.a.get(),tofile=self.b.get(),lineterm=''))
        self.text.delete('1.0','end');self.text.insert('1.0','\n'.join(diff) if diff else 'Hai bản cấu hình không có khác biệt.');self.activity('Đã so sánh hai bản cấu hình.')


class UserRolePage:
    def __init__(self,parent,activity_callback=None):
        ensure_v5_tables();self.parent=parent;self.activity=activity_callback or (lambda m:None);self._build();self.refresh()
    def _build(self):
        ctl=tk.Frame(self.parent,bg='#F3F4F6');ctl.pack(fill='x',padx=25,pady=(0,8));tk.Button(ctl,text='Thêm người dùng',command=self.add,bg='#2563EB',fg='white',relief='flat').pack(side='left');tk.Button(ctl,text='Đổi mật khẩu',command=self.password).pack(side='left',padx=5);tk.Button(ctl,text='Đổi vai trò',command=self.role).pack(side='left',padx=5);tk.Button(ctl,text='Bật/Tắt',command=self.toggle).pack(side='left',padx=5);tk.Button(ctl,text='Xóa',command=self.delete).pack(side='left',padx=5);tk.Button(ctl,text='Làm mới',command=self.refresh).pack(side='left',padx=5)
        box=tk.Frame(self.parent,bg='white',bd=1,relief='solid');box.pack(fill='both',expand=True,padx=25,pady=(0,10));self.t=ttk.Treeview(box,columns=('user','role','enabled','created','updated'),show='headings');
        for c,h,w in [('user','Tài khoản',180),('role','Vai trò',120),('enabled','Hoạt động',90),('created','Tạo lúc',160),('updated','Cập nhật',160)]:self.t.heading(c,text=h);self.t.column(c,width=w,anchor='w')
        self.t.pack(fill='both',expand=True,padx=8,pady=8);tk.Label(self.parent,text='Admin: toàn quyền • Operator: vận hành/giám sát • Viewer: chỉ xem các màn hình giám sát.',bg='#F3F4F6',fg='#6B7280').pack(anchor='w',padx=25,pady=(0,8))
    def refresh(self):
        for x in self.t.get_children():self.t.delete(x)
        c=_connect();rows=c.execute('SELECT * FROM app_users ORDER BY username').fetchall();c.close()
        for r in rows:self.t.insert('','end',iid=str(r['id']),values=(r['username'],r['role'],'Có' if r['enabled'] else 'Không',r['created_at'],r['updated_at'] or '-'))
    def _selected(self):s=self.t.selection();return int(s[0]) if s else None
    def add(self):
        u=simpledialog.askstring('Người dùng','Tên đăng nhập:',parent=self.parent)
        if not u:return
        p=simpledialog.askstring('Người dùng','Mật khẩu:',show='*',parent=self.parent)
        if not p:return
        role=simpledialog.askstring('Người dùng','Vai trò: Admin / Operator / Viewer',initialvalue='Viewer',parent=self.parent) or 'Viewer';role=role.title()
        if role not in ('Admin','Operator','Viewer'):messagebox.showwarning('Người dùng','Vai trò không hợp lệ.');return
        c=_connect()
        try:c.execute('INSERT INTO app_users(username,password_hash,role,enabled,created_at,updated_at) VALUES(?,?,?,?,?,?)',(u.strip(),_hash_password(p),role,1,_now(),_now()));c.commit()
        except sqlite3.IntegrityError:messagebox.showerror('Người dùng','Tài khoản đã tồn tại.')
        finally:c.close()
        self.refresh()
    def password(self):
        i=self._selected()
        if not i:return
        p=simpledialog.askstring('Đổi mật khẩu','Mật khẩu mới:',show='*',parent=self.parent)
        if not p:return
        c=_connect();c.execute('UPDATE app_users SET password_hash=?,updated_at=? WHERE id=?',(_hash_password(p),_now(),i));c.commit();c.close();self.refresh()
    def role(self):
        i=self._selected()
        if not i:return
        role=simpledialog.askstring('Vai trò','Admin / Operator / Viewer:',parent=self.parent)
        if not role:return
        role=role.title()
        if role not in ('Admin','Operator','Viewer'):messagebox.showwarning('Vai trò','Vai trò không hợp lệ.');return
        c=_connect();c.execute('UPDATE app_users SET role=?,updated_at=? WHERE id=?',(role,_now(),i));c.commit();c.close();self.refresh()
    def toggle(self):
        i=self._selected()
        if not i:return
        c=_connect();c.execute('UPDATE app_users SET enabled=CASE enabled WHEN 1 THEN 0 ELSE 1 END,updated_at=? WHERE id=?',(_now(),i));c.commit();c.close();self.refresh()
    def delete(self):
        i=self._selected()
        if not i:return
        c=_connect();c.execute('DELETE FROM app_users WHERE id=?',(i,));c.commit();c.close();self.refresh()


class LoginDialog:
    def __init__(self,root):
        self.root=root;self.user=None
    def run(self):
        if not has_local_users():
            return {'username':'local-admin','role':'Admin','bootstrap':True}
        w=tk.Toplevel(self.root);w.title('Đăng nhập Network Automation');w.geometry('390x230');w.resizable(False,False);w.grab_set();w.protocol('WM_DELETE_WINDOW',lambda:(setattr(self,'user',None),w.destroy()))
        tk.Label(w,text='NETWORK AUTOMATION',font=('Segoe UI',16,'bold')).pack(pady=(18,12));frm=tk.Frame(w);frm.pack(fill='x',padx=35);u=tk.StringVar();p=tk.StringVar();tk.Label(frm,text='Tài khoản').grid(row=0,column=0,sticky='w',pady=7);tk.Entry(frm,textvariable=u,width=27).grid(row=0,column=1,pady=7);tk.Label(frm,text='Mật khẩu').grid(row=1,column=0,sticky='w',pady=7);pe=tk.Entry(frm,textvariable=p,show='*',width=27);pe.grid(row=1,column=1,pady=7)
        msg=tk.StringVar();tk.Label(w,textvariable=msg,fg='#DC2626').pack()
        def go(event=None):
            r=authenticate(u.get().strip(),p.get())
            if r:self.user=r;w.destroy()
            else:msg.set('Sai tài khoản hoặc mật khẩu.')
        tk.Button(w,text='Đăng nhập',command=go,bg='#2563EB',fg='white',width=14).pack(pady=8);pe.bind('<Return>',go);w.wait_window();return self.user


__all__=['ensure_v5_tables','CredentialManagerPage','SecureBackupSchedulerPage','ConfigComparePage','UserRolePage','LoginDialog','has_local_users']
