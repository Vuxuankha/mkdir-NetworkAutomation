"""Task records and fixed execution scope for autonomous diagnostics."""
import ipaddress
import json
import os
import re
import time
import uuid
from datetime import datetime,timezone
from pathlib import Path
from app_runtime import REPORT_DIR
from modules import assistant_tools as tools
from modules.monitor_extensions import redact


def make_scope(objective):
    devices=tools.read_rows('network_devices',100)
    cameras=tools.read_rows('camera_registry',20)
    ips={'1.1.1.1'}
    for row in devices+cameras:
        try:ips.add(str(ipaddress.ip_address(row.get('ip') or row.get('host',''))))
        except ValueError:pass
    for token in re.findall(r'[0-9A-Fa-f:.]+',objective):
        try:ips.add(str(ipaddress.ip_address(token.strip('.'))))
        except ValueError:pass
    return {'allowed_ips':sorted(ips),'devices':devices[:50],'cameras':cameras,
            'allowed_tools':['ping_ip','ping_devices','check_cameras','read_summary','check_wifi'],
            'max_calls':10,'max_requests':6,'deadline_seconds':300}


def allow(scope,name,args):
    tools.validate(name,args)
    if name not in scope['allowed_tools']:return False
    for field in ('ip','gateway','internet'):
        if field in args and args[field] and str(ipaddress.ip_address(args[field])) not in scope['allowed_ips']:
            return False
    return True


def execute_scoped(scope,name,args,stop=None,deadline=None,progress=None):
    if not allow(scope,name,args):raise ValueError('Công cụ hoặc IP nằm ngoài phạm vi đã duyệt.')
    if name in ('ping_devices','check_cameras'):
        rows=scope['devices'] if name=='ping_devices' else scope['cameras']
        results=[]
        for index,row in enumerate(rows):
            if progress:progress(name,{'completed':index,'total':len(rows),'target':row.get('ip') or row.get('host','')})
            if (stop is not None and stop.is_set()) or (deadline is not None and time.monotonic()>=deadline):
                return {'results':results,'selected':len(rows),'partial':True,'error':'Đã hủy hoặc đạt giới hạn thời gian'}
            if name=='ping_devices':
                ip=row.get('ip','')
                try:ip=str(ipaddress.ip_address(ip))
                except ValueError:
                    results.append({'name':row.get('name'),'status':'Skipped','error':'Thiết bị không có IP literal hợp lệ'});continue
                result=tools.ping_host(ip,1000)
                results.append({'name':row.get('name'),'result':result})
            else:
                status,detail=tools.ext.check_camera(row)
                results.append({'name':row['name'],'host':row['host'],'status':status,'detail':detail})
        if progress:progress(name,{'completed':len(rows),'total':len(rows),'target':''})
        return {'results':results,'selected':len(rows),'note':'Kết quả tại thời điểm kiểm tra; camera chỉ kiểm tra TCP.'}
    return tools.execute(name,args,stop)


class TaskRecord:
    def __init__(self,objective,provider,model,scope,root=None):
        self.root=Path(root) if root is not None else REPORT_DIR/'ai_tasks'
        self.id=datetime.now().strftime('%Y%m%d_%H%M%S_')+uuid.uuid4().hex[:8]
        self.folder=self.root/self.id;self.folder.mkdir(parents=True)
        self.data={'id':self.id,'objective':redact(objective),'provider':provider,'model':model,
                   'scope':scope,'state':'starting','created_at':datetime.now(timezone.utc).isoformat(),'steps':[]}
        self.started=time.monotonic();self.save()
    def save(self):
        self.data['updated_at']=datetime.now(timezone.utc).isoformat()
        temporary=self.folder/'task.tmp';temporary.write_text(json.dumps(self.data,ensure_ascii=False,indent=2),encoding='utf-8')
        os.replace(temporary,self.folder/'task.json')
    def step(self,name,args,result):
        self.data['state']='running'
        self.data['steps'].append({'tool':name,'args':args,'result':result})
        self.save()
    def finish(self,state,answer='',error=''):
        self.data.update(state=state,answer=redact(answer),error=redact(error));self.save()
        report=self.folder/'report.txt'
        body='TÁC VỤ AI '+self.id+'\nTrạng thái: '+state+'\nMục tiêu: '+self.data['objective']+'\n\n'
        for step in self.data['steps']:
            body+='Công cụ: '+step['tool']+'\nTham số: '+json.dumps(step['args'],ensure_ascii=False)+'\nKết quả: '+str(step['result'])+'\n\n'
        body+='Tổng hợp AI:\n'+self.data['answer']+'\nLỗi/giới hạn:\n'+self.data['error']
        report.write_text(body,encoding='utf-8');return report


def task_history(root=None):
    folder=Path(root) if root is not None else REPORT_DIR/'ai_tasks'
    records=[]
    if not folder.exists():return records
    for path in sorted(folder.glob('*/task.json'),reverse=True)[:30]:
        try:record=json.loads(path.read_text(encoding='utf-8'))
        except (OSError,ValueError):continue
        if record.get('state') in ('starting','running'):
            record['display_state']='Đang chạy hoặc bị gián đoạn — xem thời gian cập nhật'
        else:record['display_state']={'finished':'Đã tổng hợp','failed':'Có lỗi','needs_review':'Cần xem lại','cancelled':'Đã hủy'}.get(record.get('state'),'Chưa xác định')
        records.append(record)
    return records


def run_task(objective,provider,model,scope,image=None,stop=None,trace=None,root=None,chat_fn=None,status_callback=None):
    from modules.assistant_agent import chat
    record=TaskRecord(objective,provider,model,scope,root)
    def progress(name,args,result):
        record.step(name,args,result)
        if trace:trace(name,args,result)
    deadline=record.started+scope['deadline_seconds']
    def bounded_execute(name,args,cancel):
        if time.monotonic()>=deadline:raise TimeoutError('Đạt giới hạn thời gian tác vụ')
        def update(tool,info):
            record.data['current_step']={'tool':tool,**info};record.save()
            if status_callback:status_callback(tool,info)
        if name not in ('ping_devices','check_cameras'):
            target=args.get('ip') or args.get('gateway') or ''
            update(name,{'completed':0,'total':1,'target':target})
            result=execute_scoped(scope,name,args,cancel,deadline,update)
            update(name,{'completed':1,'total':1,'target':target})
            return result
        return execute_scoped(scope,name,args,cancel,deadline,update)
    try:
        answer=(chat_fn or chat)(provider,model,objective,image,lambda name,args:allow(scope,name,args),stop,progress,
            execute_tool=bounded_execute,max_requests=scope['max_requests'],max_calls=scope['max_calls'],deadline=deadline)
        if stop is not None and stop.is_set():raise RuntimeError('Đã hủy tác vụ')
        tool_errors=[step for step in record.data['steps'] if '"error"' in str(step['result'])]
        state='needs_review' if tool_errors or not record.data['steps'] else 'finished'
        note='Có công cụ bị lỗi/từ chối; xem chi tiết.' if tool_errors else ('AI chưa thực hiện bước kiểm tra nào; cần xem lại kết quả.' if not record.data['steps'] else '')
        report=record.finish(state,answer,note)
    except Exception as exc:
        state='cancelled' if stop is not None and stop.is_set() else 'failed'
        answer='Tác vụ '+state+': '+str(exc)
        report=record.finish(state,error=str(exc))
    return {'id':record.id,'state':record.data['state'],'answer':answer,'report':str(report),'steps':len(record.data['steps'])}
