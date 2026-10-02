"""Regression smoke tests v3.12. Chạy: python regression_test.py
Bộ test chạy trên dữ liệu tạm, không sao chép/ghi đè database vận hành.
"""
import compileall, sqlite3, shutil, tempfile, os, sys, subprocess, re
from pathlib import Path

ROOT=Path(__file__).resolve().parent
if os.environ.get('NA_REGRESSION_CHILD') != '1':
    with tempfile.TemporaryDirectory(prefix='na-regression-') as folder:
        env = dict(os.environ, NETWORK_AUTOMATION_DATA_DIR=folder, NA_REGRESSION_CHILD='1')
        result = subprocess.run([sys.executable, str(Path(__file__).resolve())], cwd=ROOT, env=env)
    raise SystemExit(result.returncode)
from database.db import DB_PATH
SNAPSHOT=Path(DB_PATH).parent/'network_automation_regression_snapshot.db'
if Path(DB_PATH).exists(): shutil.copy2(DB_PATH,SNAPSHOT)
checks=[]

def bootstrap_schema():
    from database.db import init_database
    from modules.advanced_pages import ensure_advanced_tables
    from modules.server_monitor import ensure_server_monitor_tables
    from modules.nms_v3 import ensure_v3_tables
    from modules.nms_v4 import ensure_v4_tables
    from modules.nms_v5 import ensure_v5_tables
    from modules.nms_v6 import ensure_v6_tables
    from modules.nms_v7 import ensure_v7_tables
    from modules.nms_v8 import ensure_v8_tables
    from modules.nms_v9 import ensure_v9_tables
    from modules.nms_v10 import ensure_v10_tables
    from modules.nms_v11 import ensure_v11_tables
    from modules.nms_v12 import ensure_v12_tables
    init_database(); ensure_advanced_tables(); ensure_server_monitor_tables()
    ensure_v3_tables(); ensure_v4_tables(); ensure_v5_tables(); ensure_v6_tables()
    ensure_v7_tables(); ensure_v8_tables(); ensure_v9_tables(); ensure_v10_tables()
    ensure_v11_tables(); ensure_v12_tables()

bootstrap_schema()
def check(name, fn):
    try: fn(); checks.append((name,'PASS',''))
    except Exception as e: checks.append((name,'FAIL',repr(e)))

def t_compile(): assert compileall.compile_dir(str(ROOT),quiet=1,rx=re.compile(r'[\\/](?:\.venv[^\\/]*|venv|build|dist)[\\/]'))
def t_schema():
    from modules.nms_v6 import ensure_v6_tables
    from modules.nms_v7 import ensure_v7_tables
    from modules.nms_v8 import ensure_v8_tables
    from modules.nms_v9 import ensure_v9_tables
    from modules.nms_v10 import ensure_v10_tables
    from modules.nms_v11 import ensure_v11_tables
    from modules.nms_v12 import ensure_v12_tables
    ensure_v6_tables();ensure_v7_tables();ensure_v8_tables();ensure_v9_tables();ensure_v10_tables();ensure_v11_tables();ensure_v12_tables();c=sqlite3.connect(DB_PATH)
    names={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")};c.close()
    expected={'audit_log','monitoring_settings','restore_history','device_profiles','device_profile_assignments','sites','device_groups','device_organization','maintenance_windows','sla_policies','incidents','incident_alerts','device_dependencies','alert_suppressions','root_cause_events','managed_services','service_members','core_settings','device_health_state','worker_jobs','system_health_history','vendor_drivers','device_driver_assignments','snmpv3_credentials','device_snmpv3_assignments','snmp_diagnostics_history'}
    assert expected <= names

def t_security():
    from modules.nms_v5 import encrypt_secret,decrypt_secret,_hash_password,_verify_password
    token=encrypt_secret('regression-secret');assert token!='regression-secret';assert decrypt_secret(token)=='regression-secret';h=_hash_password('P@ssw0rd!');assert _verify_password('P@ssw0rd!',h);assert not _verify_password('wrong',h)
def t_alerts():
    from modules.nms_v4 import evaluate_alert_rules
    a,b=evaluate_alert_rules();assert isinstance(a,int) and isinstance(b,int)
def t_profiles():
    from modules.nms_v7 import ensure_v7_tables,detect_profile
    ensure_v7_tables();assert detect_profile('Cisco IOS Software','1.3.6.1.4.1.9.1.1')['vendor']=='Cisco';assert detect_profile('MikroTik RouterOS','1.3.6.1.4.1.14988.1')['vendor']=='MikroTik'
def t_v8():
    from modules.nms_v8 import ensure_v8_tables
    from modules.advanced_pages import _connect
    ensure_v8_tables();c=_connect()
    try:c.execute('SELECT COUNT(*) FROM sites').fetchone();c.execute('SELECT COUNT(*) FROM device_groups').fetchone();c.execute('SELECT COUNT(*) FROM maintenance_windows').fetchone()
    finally:c.close()
def t_v9():
    from modules.nms_v9 import ensure_v9_tables,calculate_availability,capacity_summary,sync_incidents,_scope_hosts
    from modules.advanced_pages import _connect,_now
    ensure_v9_tables();c=_connect()
    try:
        cur=c.execute("INSERT INTO network_devices(name,ip,status,created_at,updated_at) VALUES('QA-v39','198.51.100.39','Online',?,?)",(_now(),_now()));did=cur.lastrowid
        c.execute("INSERT INTO health_samples(host,latency_ms,packet_loss,cpu,memory,created_at) VALUES('198.51.100.39',10,0,25,40,?)",(_now(),))
        c.execute("INSERT INTO sites(name,created_at,updated_at) VALUES('QA-Site-v39',?,?)",(_now(),_now()));sid=c.execute("SELECT last_insert_rowid()").fetchone()[0]
        c.execute("INSERT INTO device_groups(name,created_at,updated_at) VALUES('QA-Group-v39',?,?)",(_now(),_now()));gid=c.execute("SELECT last_insert_rowid()").fetchone()[0]
        c.execute("INSERT INTO device_organization(device_id,site_id,group_id,updated_at) VALUES(?,?,?,?)",(did,sid,gid,_now()));c.commit()
    finally:c.close()
    assert _scope_hosts('All')
    assert '198.51.100.39' in _scope_hosts('Device',did,'')
    assert '198.51.100.39' in _scope_hosts('Site',sid,'')
    assert '198.51.100.39' in _scope_hosts('Group',gid,'')
    a=calculate_availability('198.51.100.39',1);assert a['samples']>=1 and a['availability'] is not None
    cap=capacity_summary('198.51.100.39',1);assert cap['CPU %'][0] is not None
    x=sync_incidents();assert len(x)==3

def t_v10():
    from modules.nms_v10 import ensure_v10_tables,analyze_root_causes,service_status
    from modules.advanced_pages import _connect,_now
    ensure_v10_tables();c=_connect()
    try:
        p=c.execute("INSERT INTO network_devices(name,ip,status,created_at,updated_at) VALUES('QA-Core-v310','198.51.100.101','Offline',?,?)",(_now(),_now())).lastrowid
        ch=c.execute("INSERT INTO network_devices(name,ip,status,created_at,updated_at) VALUES('QA-Access-v310','198.51.100.102','Offline',?,?)",(_now(),_now())).lastrowid
        c.execute("INSERT INTO device_dependencies(parent_device_id,child_device_id,relation_type,criticality,enabled,created_at,updated_at) VALUES(?,?,'Network','High',1,?,?)",(p,ch,_now(),_now()))
        c.execute("INSERT INTO alerts(alert_type,ip_address,ip,message,severity,created_at,resolved,status) VALUES('Offline','198.51.100.101','198.51.100.101','Device offline','Critical',?,0,'Open')",(_now(),))
        c.execute("INSERT INTO alerts(alert_type,ip_address,ip,message,severity,created_at,resolved,status) VALUES('Offline','198.51.100.102','198.51.100.102','Device offline','Warning',?,0,'Open')",(_now(),))
        sid=c.execute("INSERT INTO managed_services(name,description,owner,enabled,created_at,updated_at) VALUES('QA-Service-v310','Regression','QA',1,?,?)",(_now(),_now())).lastrowid
        c.execute("INSERT INTO service_members(service_id,device_id,required) VALUES(?,?,1)",(sid,ch));c.commit()
    finally:c.close()
    r=analyze_root_causes();assert r['roots']>=1 and r['suppressed']>=1
    c=_connect()
    try:
        sup=c.execute("SELECT COUNT(*) n FROM alert_suppressions WHERE active=1 AND child_host='198.51.100.102' AND root_host='198.51.100.101'").fetchone()['n']; assert sup>=1
    finally:c.close()
    ss=service_status(sid);assert ss['status']=='Gián đoạn' and ss['required_down']>=1

def t_v11():
    import time
    from modules.nms_v11 import ensure_v11_tables,record_ping_result,JobQueueEngine,database_health,backup_database
    from modules.advanced_pages import _connect,_now
    ensure_v11_tables(); c=_connect()
    try:
        did=c.execute("INSERT INTO network_devices(name,ip,status,created_at,updated_at) VALUES('QA-v311','198.51.100.111','Online',?,?)",(_now(),_now())).lastrowid; c.commit()
    finally:c.close()
    for _ in range(3): record_ping_result(did,False,'QA timeout')
    c=_connect(); st=c.execute('SELECT status FROM network_devices WHERE id=?',(did,)).fetchone()['status']; c.close(); assert st=='Offline'
    for _ in range(2): record_ping_result(did,True)
    c=_connect(); st=c.execute('SELECT status FROM network_devices WHERE id=?',(did,)).fetchone()['status']; c.close(); assert st=='Online'
    w=JobQueueEngine(workers=1); jid=w.submit('QA','local',lambda:'ok',retries=1); deadline=time.time()+3
    while time.time()<deadline:
        c=_connect(); r=c.execute('SELECT status FROM worker_jobs WHERE id=?',(jid,)).fetchone(); c.close()
        if r and r['status']=='Success': break
        time.sleep(.05)
    else: raise AssertionError('Worker job timeout')
    w.stop(); assert database_health()[0]=='OK'; assert Path(backup_database(tempfile.gettempdir())).exists()


def t_v12():
    from modules.nms_v12 import ensure_v12_tables,detect_driver,assign_driver,get_driver_for_device
    from modules.advanced_pages import _connect,_now
    from modules.nms_v5 import encrypt_secret,decrypt_secret
    ensure_v12_tables()
    assert detect_driver('Cisco IOS XE Software','1.3.6.1.4.1.9.1.1208')['vendor']=='Cisco'
    assert detect_driver('MikroTik RouterOS','1.3.6.1.4.1.14988.1')['vendor']=='MikroTik'
    c=_connect()
    try:
        did=c.execute("INSERT INTO network_devices(name,ip,status,created_at,updated_at) VALUES('QA-v312','198.51.100.112','Online',?,?)",(_now(),_now())).lastrowid
        dr=c.execute("SELECT id FROM vendor_drivers WHERE vendor='Cisco' ORDER BY priority DESC LIMIT 1").fetchone()['id']
        auth=encrypt_secret('auth-pass'); priv=encrypt_secret('priv-pass')
        cid=c.execute("INSERT INTO snmpv3_credentials(name,username,security_level,auth_protocol,auth_secret_enc,priv_protocol,priv_secret_enc,port,created_at,updated_at) VALUES('QA-SNMPv3','qa-user','authPriv','SHA',?,'AES128',?,161,?,?)",(auth,priv,_now(),_now())).lastrowid
        c.execute("INSERT INTO device_snmpv3_assignments(device_id,credential_id,updated_at) VALUES(?,?,?)",(did,cid,_now()));c.commit()
    finally:c.close()
    assign_driver(did,dr,'qa'); d=get_driver_for_device(device_id=did); assert d and d['vendor']=='Cisco'
    c=_connect(); r=c.execute("SELECT * FROM snmpv3_credentials WHERE id=?",(cid,)).fetchone(); c.close(); assert decrypt_secret(r['auth_secret_enc'])=='auth-pass' and decrypt_secret(r['priv_secret_enc'])=='priv-pass'

def t_import_main(): import main;assert hasattr(main,'NetworkAutomationApp')

try:
    for n,f in [('Compile toàn bộ',t_compile),('Migration v3.12',t_schema),('Mã hóa + mật khẩu',t_security),('Alert engine',t_alerts),('Device Profile',t_profiles),('Site/Group/Maintenance',t_v8),('SLA/Incident/Capacity',t_v9),('Dependency/RCA/Service Impact',t_v10),('Stable Core/Worker',t_v11),('SNMPv3/Vendor Driver',t_v12),('Import ứng dụng',t_import_main)]:check(n,f)
finally:
    if SNAPSHOT.exists(): shutil.copy2(SNAPSHOT,DB_PATH); SNAPSHOT.unlink(missing_ok=True)
print('\n'.join(f'{s:4} | {n}'+(f' | {d}' if d else '') for n,s,d in checks))
raise SystemExit(1 if any(s=='FAIL' for _,s,_ in checks) else 0)
