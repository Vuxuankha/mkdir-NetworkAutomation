from modules.ui_theme import PALETTE as UI_COLORS
import json, platform, socket, subprocess, threading, time, urllib.request
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from modules.advanced_pages import _connect, notify_alert
from app_runtime import hidden_subprocess_kwargs

APP_PRESETS = {
    'SQL Server': 1433, 'IIS / HTTP': 80, 'HTTPS': 443, 'MySQL': 3306,
    'PostgreSQL': 5432, 'DNS': 53, 'DHCP': 67, 'Apache/Nginx': 80,
}

def ensure_server_monitor_tables():
    c=_connect()
    try:
        c.execute('''CREATE TABLE IF NOT EXISTS server_monitor_targets(
            id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,host TEXT NOT NULL,
            app_type TEXT DEFAULT 'Custom',port INTEGER DEFAULT 0,protocol TEXT DEFAULT 'TCP',
            service_name TEXT DEFAULT '',enabled INTEGER DEFAULT 1,created_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS server_monitor_results(
            id INTEGER PRIMARY KEY AUTOINCREMENT,target_id INTEGER,status TEXT,latency_ms REAL,
            cpu REAL,ram REAL,disk REAL,service_status TEXT,detail TEXT,checked_at TEXT)''')
        c.commit()
    finally:c.close()

def _now(): return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def _is_local(host):
    h=(host or '').strip().lower()
    return h in ('localhost','127.0.0.1','::1',socket.gethostname().lower(),platform.node().lower())

def _local_windows_health(service_name=''):
    if platform.system()!='Windows': return None
    svc=(service_name or '').replace("'","''")
    ps="$cpu=(Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average;" \
       "$os=Get-CimInstance Win32_OperatingSystem;$ram=[math]::Round((1-$os.FreePhysicalMemory/$os.TotalVisibleMemorySize)*100,1);" \
       "$d=Get-CimInstance Win32_LogicalDisk -Filter \"DriveType=3\" | Sort-Object DeviceID | Select-Object -First 1;" \
       "$disk=if($d.Size){[math]::Round((1-$d.FreeSpace/$d.Size)*100,1)}else{$null};" \
       f"$svc=if('{svc}'){{(Get-Service -Name '{svc}' -ErrorAction SilentlyContinue).Status.ToString()}}else{{''}};" \
       "@{cpu=$cpu;ram=$ram;disk=$disk;service=$svc}|ConvertTo-Json -Compress"
    try:
        r=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-Command',ps],capture_output=True,text=True,timeout=15,**hidden_subprocess_kwargs())
        return json.loads(r.stdout.strip()) if r.returncode==0 and r.stdout.strip() else None
    except Exception:return None

def check_target(row):
    host=row['host']; port=int(row['port'] or 0); proto=(row['protocol'] or 'TCP').upper(); t0=time.perf_counter()
    status='DOWN'; detail=''; latency=None
    try:
        if proto in ('HTTP','HTTPS'):
            scheme=proto.lower(); url=f'{scheme}://{host}' + (f':{port}' if port and port not in (80,443) else '') + '/'
            with urllib.request.urlopen(url,timeout=5) as r:
                code=getattr(r,'status',200); status='UP' if code < 500 else 'WARN'; detail=f'HTTP {code}'
        else:
            with socket.create_connection((host,port),timeout=5): pass
            status='UP'; detail=f'TCP {port} open'
        latency=round((time.perf_counter()-t0)*1000,1)
    except Exception as exc:
        latency=round((time.perf_counter()-t0)*1000,1); detail=str(exc)[:300]
    health=_local_windows_health(row['service_name']) if _is_local(host) else None
    cpu=ram=disk=None; service=''
    if health:
        cpu=health.get('cpu'); ram=health.get('ram'); disk=health.get('disk'); service=health.get('service','')
        if service and service.lower()!='running': status='WARN'; detail += f'; service={service}'
        if any(v is not None and float(v)>=90 for v in (cpu,ram,disk)): status='WARN'; detail += '; resource >=90%'
    return {'status':status,'latency_ms':latency,'cpu':cpu,'ram':ram,'disk':disk,'service_status':service,'detail':detail}

def save_result(target_id,res):
    c=_connect()
    try:
        c.execute('''INSERT INTO server_monitor_results(target_id,status,latency_ms,cpu,ram,disk,service_status,detail,checked_at)
                     VALUES(?,?,?,?,?,?,?,?,?)''',(target_id,res['status'],res['latency_ms'],res['cpu'],res['ram'],res['disk'],res['service_status'],res['detail'],_now()));c.commit()
    finally:c.close()

def run_all_targets():
    ensure_server_monitor_tables(); c=_connect()
    try: rows=c.execute('SELECT * FROM server_monitor_targets WHERE enabled=1 ORDER BY id').fetchall()
    finally:c.close()
    out=[]
    for row in rows:
        res=check_target(row); save_result(row['id'],res); out.append((dict(row),res))
        if res['status'] in ('DOWN','WARN'):
            notify_alert(row['host'],f"Application/Server {res['status']}",f"{row['name']} ({row['app_type']}): {res['detail']}",'Critical' if res['status']=='DOWN' else 'Warning',event_key=f"server-monitor|{row['id']}|{res['status']}")
    return out

class ServerMonitorPage:
    def __init__(self,parent,activity_callback=None):
        self.parent=parent; self.activity=activity_callback or (lambda x:None); ensure_server_monitor_tables(); self.build()
    def build(self):
        for w in self.parent.winfo_children(): w.destroy()
        top=tk.Frame(self.parent,bg=UI_COLORS['surface']);top.pack(fill='x',padx=12,pady=10)
        tk.Label(top,text='Application / Server Monitor',bg=UI_COLORS['surface'],fg=UI_COLORS['text'],font=('Segoe UI',15,'bold')).pack(side='left')
        ttk.Button(top,text='Chạy kiểm tra',command=self.run_checks).pack(side='right',padx=4)
        ttk.Button(top,text='Thêm target',command=self.add_target).pack(side='right',padx=4)
        cols=('name','host','app','port','status','latency','cpu','ram','disk','service','checked')
        self.tree=ttk.Treeview(self.parent,columns=cols,show='headings',height=18)
        labels={'name':'Tên','host':'Host/IP','app':'Ứng dụng','port':'Port','status':'Trạng thái','latency':'Latency','cpu':'CPU','ram':'RAM','disk':'Disk','service':'Service','checked':'Kiểm tra'}
        for c in cols:self.tree.heading(c,text=labels[c]);self.tree.column(c,width=105,anchor='center')
        self.tree.column('name',width=145,anchor='w');self.tree.column('host',width=125,anchor='w');self.tree.pack(fill='both',expand=True,padx=12,pady=(0,12))
        self.refresh()
    def refresh(self):
        for i in self.tree.get_children():self.tree.delete(i)
        c=_connect()
        try:
            rows=c.execute('''SELECT t.*,r.status,r.latency_ms,r.cpu,r.ram,r.disk,r.service_status,r.checked_at FROM server_monitor_targets t LEFT JOIN server_monitor_results r ON r.id=(SELECT id FROM server_monitor_results WHERE target_id=t.id ORDER BY id DESC LIMIT 1) ORDER BY t.name''').fetchall()
        finally:c.close()
        fmt=lambda v: '-' if v is None or v=='' else f'{float(v):.0f}%'
        for r in rows:self.tree.insert('', 'end', iid=str(r['id']), values=(r['name'],r['host'],r['app_type'],r['port'],r['status'] or 'Chưa kiểm tra',f"{r['latency_ms']:.1f} ms" if r['latency_ms'] is not None else '-',fmt(r['cpu']),fmt(r['ram']),fmt(r['disk']),r['service_status'] or '-',r['checked_at'] or '-'))
    def add_target(self):
        win=tk.Toplevel(self.parent);win.title('Thêm Application/Server');win.geometry('430x390');win.transient(self.parent.winfo_toplevel())
        vars={k:tk.StringVar() for k in ('name','host','app','port','protocol','service')};vars['app'].set('SQL Server');vars['port'].set('1433');vars['protocol'].set('TCP')
        fields=[('Tên hiển thị','name'),('Host / IP','host'),('Loại ứng dụng','app'),('Port','port'),('Protocol TCP/HTTP/HTTPS','protocol'),('Windows service (tùy chọn)','service')]
        for i,(lab,key) in enumerate(fields):tk.Label(win,text=lab).grid(row=i,column=0,sticky='w',padx=12,pady=8);ttk.Entry(win,textvariable=vars[key],width=28).grid(row=i,column=1,padx=8,pady=8)
        def save():
            try: port=int(vars['port'].get())
            except: return messagebox.showerror('Port','Port phải là số.',parent=win)
            if not vars['name'].get().strip() or not vars['host'].get().strip():return messagebox.showwarning('Thiếu dữ liệu','Nhập tên và Host/IP.',parent=win)
            c=_connect()
            try:c.execute('INSERT INTO server_monitor_targets(name,host,app_type,port,protocol,service_name,enabled,created_at) VALUES(?,?,?,?,?,?,1,?)',(vars['name'].get().strip(),vars['host'].get().strip(),vars['app'].get().strip(),port,vars['protocol'].get().strip().upper(),vars['service'].get().strip(),_now()));c.commit()
            finally:c.close()
            win.destroy();self.refresh()
        ttk.Button(win,text='Lưu',command=save).grid(row=len(fields),column=0,columnspan=2,pady=18)
    def run_checks(self):
        def worker():
            try:
                out=run_all_targets();self.parent.after(0,self.refresh);self.activity(f'Application/Server Monitor: checked {len(out)} targets')
            except Exception as exc:self.parent.after(0,lambda:messagebox.showerror('Server Monitor',str(exc)))
        threading.Thread(target=worker,daemon=True).start()
