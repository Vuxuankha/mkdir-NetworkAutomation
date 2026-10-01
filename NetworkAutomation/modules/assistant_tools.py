"""Whitelisted read-only tools; SQL and OS commands are never model-controlled."""
import ipaddress
from database.db import get_connection
from modules import monitor_extensions as ext
from modules.ping_check import ping_host

CATALOG = [
    {'name':'ping_ip','description':'Ping one literal IP address once. No hostname or command execution.',
     'parameters':{'type':'object','properties':{'ip':{'type':'string'}},'required':['ip'],'additionalProperties':False}},
    {'name':'check_cameras','description':'Check TCP reachability for up to 20 configured cameras, not video health.',
     'parameters':{'type':'object','properties':{},'required':[],'additionalProperties':False}},
    {'name':'read_summary','description':'Read device counts and up to 20 recent alerts, incidents and monitoring samples. No credentials.',
     'parameters':{'type':'object','properties':{},'required':[],'additionalProperties':False}},
    {'name':'check_wifi','description':'Read Windows Wi-Fi and ping gateway/Internet. Blank gateway chooses system default route.',
     'parameters':{'type':'object','properties':{'gateway':{'type':'string'},'internet':{'type':'string'}},
                   'required':['gateway','internet'],'additionalProperties':False}},
]

CATALOG.append({'name':'ping_devices','description':'Ping up to 50 registered devices once each; reports all results.',
                'parameters':{'type':'object','properties':{},'required':[],'additionalProperties':False}})

# Only these exact projections can be read. No settings, credentials or config tables.
PROJECTIONS={
 'network_devices':('id,name,ip,status','id'),
 'devices':('id,ip,hostname,mac,status','id'),
 'alerts':('id,ip,alert_type,message,severity,created_at','id'),
 'incidents':('id,host,title,severity,status,first_seen,last_seen','id'),
 'snmp_samples':('id,host,sys_name,oper_status,in_bps,out_bps,created_at','id'),
 'health_samples':('id,host,latency_ms,packet_loss,cpu,memory,created_at','id'),
 'extension_history':('id,kind,target,status,detail,created_at','id'),
 'camera_registry':('id,name,host,port','id'),
}


def read_rows(table,limit=20):
    if table not in PROJECTIONS:raise ValueError('Table not allowed')
    columns,order=PROJECTIONS[table];limit=min(100,max(1,int(limit)))
    c=get_connection()
    try:
        exists=c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(table,)).fetchone()
        if not exists:return []
        # Accommodate old schemas without selecting additional sensitive columns.
        available={r[1] for r in c.execute(f'PRAGMA table_info({table})')}
        selected=','.join(x for x in columns.split(',') if x in available)
        if not selected:return []
        return [dict(r) for r in c.execute(f'SELECT {selected} FROM {table} ORDER BY {order} DESC LIMIT ?',(limit,))]
    finally:c.close()


def summary():
    c=get_connection()
    try:
        exists=c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='network_devices'").fetchone()
        counts=[dict(r) for r in c.execute('SELECT status,COUNT(*) AS count FROM network_devices GROUP BY status')] if exists else []
    finally:c.close()
    return {'device_counts':counts,'recent_alerts':read_rows('alerts'),'recent_incidents':read_rows('incidents'),
            'monitoring':read_rows('extension_history')}


def page_context(page,scan_results=None):
    data={'page':page}
    if page=='Quét mạng':data['scan_results']=(scan_results or [])[:100]
    elif page in ('Tổng quan','Trung tâm giám sát NOC','Báo cáo'):data['summary']=summary()
    elif page=='Cảnh báo':data['alerts']=read_rows('alerts')
    elif page=='Trung tâm sự cố':data['incidents']=read_rows('incidents')
    elif page in ('Quản lý thiết bị','Thiết bị mạng'):data['devices']=read_rows('network_devices')
    elif page in ('Giám sát SNMP','CPU / RAM SNMP','Biểu đồ lịch sử','Sức khỏe mạng','Phân tích dung lượng'):
        data['snmp_samples']=read_rows('snmp_samples');data['health_samples']=read_rows('health_samples')
    elif page=='Wi-Fi / Camera / AI':
        data['cameras']=read_rows('camera_registry');data['history']=read_rows('extension_history')
    else:data['note']='Trang này chưa có adapter dữ liệu. Dán log/kết quả vào ô nhập để phân tích.'
    return data


def validate(name,args):
    if not isinstance(args,dict):raise ValueError('Arguments must be an object')
    if name not in {x['name'] for x in CATALOG}:raise ValueError('Tool not allowed')
    expected=next(x['parameters']['properties'] for x in CATALOG if x['name']==name)
    if set(args)!=set(expected):raise ValueError('Invalid tool arguments')
    if any(not isinstance(value,str) for value in args.values()):raise ValueError('Arguments must be strings')
    checked=dict(args)
    for key in ('ip','gateway','internet'):
        if key in checked:
            if key=='gateway' and not checked[key]:continue
            checked[key]=str(ipaddress.ip_address(checked[key].strip()))
    return checked


def execute(name,args,stop=None):
    args=validate(name,args)
    if stop is not None and stop.is_set():raise RuntimeError('Đã hủy tác vụ')
    if name=='ping_ip':return ping_host(args['ip'],1000)
    if name=='read_summary':return summary()
    if name=='ping_devices':
        results=[]
        for row in read_rows('network_devices',50):
            if stop is not None and stop.is_set():raise RuntimeError('Đã hủy tác vụ')
            try:ip=str(ipaddress.ip_address(row.get('ip','')))
            except ValueError:
                results.append({'name':row.get('name'),'status':'Skipped','error':'IP không hợp lệ'});continue
            results.append({'name':row.get('name'),'result':ping_host(ip,1000)})
        return {'results':results,'limit':50}
    if name=='check_wifi':return ext.wifi_diagnostics(args['gateway'],args['internet'],stop)
    if name=='check_cameras':
        rows=read_rows('camera_registry',20);result=[]
        for camera in rows:
            if stop is not None and stop.is_set():break
            status,detail=ext.check_camera(camera)
            result.append({'name':camera['name'],'host':camera['host'],'status':status,'detail':detail})
        return {'checked':result,'limit':20,'note':'Chỉ kiểm tra TCP; không xác nhận hình ảnh.'}
    raise ValueError('Tool not allowed')
