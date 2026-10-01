"""Windows Wi-Fi diagnostics, encrypted camera registry and monitoring history."""
import os
import re
import socket
import subprocess
from urllib.parse import urlsplit
from database.db import get_connection
from app_runtime import hidden_subprocess_kwargs
from modules.nms_v5 import encrypt_secret, decrypt_secret
from modules.ping_check import ping_host


def ensure_tables():
    c=get_connection()
    try:
        c.executescript('''CREATE TABLE IF NOT EXISTS camera_registry(
          id INTEGER PRIMARY KEY, name TEXT NOT NULL, host TEXT NOT NULL,
          port INTEGER NOT NULL DEFAULT 554, stream_enc TEXT NOT NULL DEFAULT '',
          snapshot_enc TEXT NOT NULL DEFAULT '');
        CREATE TABLE IF NOT EXISTS extension_history(
          id INTEGER PRIMARY KEY, kind TEXT NOT NULL, target TEXT NOT NULL,
          status TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE INDEX IF NOT EXISTS idx_extension_history_time ON extension_history(created_at);
        ''');c.commit()
    finally:c.close()


def history(kind,target,status,detail):
    c=get_connection()
    try:
        c.execute('INSERT INTO extension_history(kind,target,status,detail) VALUES(?,?,?,?)',
                  (kind,target,status,detail));c.commit()
        # Bound history storage (latest 10,000 samples).
        c.execute('DELETE FROM extension_history WHERE id < COALESCE((SELECT id FROM extension_history ORDER BY id DESC LIMIT 1 OFFSET 9999),0)');c.commit()
    finally:c.close()


def validate_host(host):
    host=host.strip()
    if not host or host.startswith('-') or any(c.isspace() for c in host) or '/' in host or '\\' in host:
        raise ValueError('Nhập IP hoặc hostname hợp lệ.')
    return host


def save_camera(name,host,port,stream='',snapshot=''):
    host=validate_host(host);port=int(port)
    if not name.strip() or not 1<=port<=65535:raise ValueError('Tên hoặc cổng camera không hợp lệ.')
    if stream and urlsplit(stream).scheme not in ('rtsp','rtsps'):raise ValueError('Luồng phải dùng rtsp:// hoặc rtsps://')
    if snapshot and urlsplit(snapshot).scheme not in ('http','https'):raise ValueError('Snapshot phải dùng http:// hoặc https://')
    c=get_connection()
    try:
        c.execute('INSERT INTO camera_registry(name,host,port,stream_enc,snapshot_enc) VALUES(?,?,?,?,?)',
                  (name.strip(),host,port,encrypt_secret(stream) if stream else '',encrypt_secret(snapshot) if snapshot else ''));c.commit()
    finally:c.close()


def cameras():
    c=get_connection()
    try:return [dict(x) for x in c.execute('SELECT * FROM camera_registry ORDER BY id')]
    finally:c.close()


def check_camera(camera):
    try:
        with socket.create_connection((camera['host'],camera['port']),timeout=3):pass
        return 'Reachable', 'Cổng TCP truy cập được; chưa xác nhận hình ảnh hoặc đăng nhập.'
    except OSError:return 'Unreachable','Không kết nối được cổng TCP camera/đầu ghi.'


def command_output(args):
    result=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                          text=True,errors='replace',timeout=15,**hidden_subprocess_kwargs())
    if result.returncode:raise RuntimeError('Không đọc được thông tin mạng. Kiểm tra WLAN service/card Wi-Fi và quyền Windows.')
    return result.stdout


def wifi_diagnostics(gateway='',internet='1.1.1.1',stop=None):
    if os.name!='nt':raise RuntimeError('Chức năng Wi-Fi yêu cầu Windows.')
    try:
        interfaces=command_output(['netsh','wlan','show','interfaces'])
    except RuntimeError as exc:
        interfaces='Không đọc được Wi-Fi: '+str(exc)
    try:
        surrounding=command_output(['netsh','wlan','show','networks','mode=bssid'])
    except RuntimeError as exc:
        surrounding='Không quét được mạng xung quanh: '+str(exc)
    if not gateway:
        try:
            gateway=command_output(['powershell','-NoProfile','-Command',
          "(Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Sort-Object RouteMetric | Select-Object -First 1).NextHop"]).strip()
        except RuntimeError:
            gateway='' 
    probes={}
    for target in (gateway,internet):
        if not target:continue
        validate_host(target)
        samples=[]
        for _ in range(4):
            if stop is not None and stop.is_set():break
            samples.append(ping_host(target,1000))
        if not samples:continue
        online=[x['response'] for x in samples if x['status']=='Online']
        probes[target]={'samples':len(samples),'loss_percent':round(100*(len(samples)-len(online))/len(samples),1),
                        'latency_ms':round(sum(online)/len(online),2) if online else None,
                        'errors':sum(x['status']=='Error' for x in samples)}
    return {'interfaces':interfaces,'nearby_networks':surrounding,'probes':probes}


def redact(text):
    text=re.sub(r'(rtsp[s]?://|https?://)[^\s/@]+:[^\s/@]+@',r'\1[REDACTED]@',text,flags=re.I)
    text=re.sub(r'(?im)((?:password|passwd|api[_ -]?key|token|secret|community)\s*[:=]\s*)[^\s,;]+',r'\1[REDACTED]',text)
    return text[:30000]

