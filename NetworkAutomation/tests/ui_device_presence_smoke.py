"""Actual Tk Device Manager + real presence worker, simulated LAN, disposable DB."""
import os,sys,tempfile,time,threading
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
folder=tempfile.TemporaryDirectory();os.environ['NETWORK_AUTOMATION_DATA_DIR']=folder.name
import tkinter as tk
import main
from database.db import init_database, get_connection
from modules.device_presence import DevicePresenceMonitor

class IdleEngine:
    def __init__(self,*args,**kwargs):self.thread=None;self.threads=[];self.running=False
    def stop(self):pass
    def settings(self):return {'enabled':False,'interval_sec':60,'retention_days':90,'last_run':'','last_status':''}
    def stats(self):return {'workers_alive':0,'queue':0,'Failed':0}

root=None;patches=[];errors=[];release=threading.Event();state={'online':False};monitor=None
try:
    init_database();c=get_connection()
    c.executemany('INSERT INTO devices(ip,hostname,status,first_seen,last_seen) VALUES(?,?,?,?,?)',
                  [(f'192.0.2.{i}',f'lab-{i}','Offline','old','old') for i in range(1,94)])
    c.commit();c.close()
    for name in ('BackgroundAlertEngine','MonitoringService','JobQueueEngine','RootCauseEngine','AutoAuditSchedulerEngine'):
        item=patch.object(main,name,IdleEngine);item.start();patches.append(item)
    def probe(ip):release.wait(3);return state['online'] and ip=='192.0.2.1'
    def make_monitor():
        global monitor
        monitor=DevicePresenceMonitor(interval=.15,probe=probe);return monitor
    item=patch.object(main,'DevicePresenceMonitor',make_monitor);item.start();patches.append(item)
    root=tk.Tk();root.report_callback_exception=lambda *args:errors.append(args)
    app=main.NetworkAutomationApp(root,{'username':'gui-test','role':'Admin','bootstrap':True})
    assert monitor.thread.is_alive(),'Monitor must start during app startup'
    def wait(predicate,timeout=4):
        deadline=time.monotonic()+timeout
        while not predicate() and time.monotonic()<deadline:root.update();time.sleep(.01)
        assert predicate(),'Timed out waiting for UI / worker'
    app.show_device_manager();root.update()
    assert len(app.device_table.get_children())==93
    assert all(app.device_table.item(i,'values')[4]=='Unknown' for i in app.device_table.get_children()),'Old Offline must not appear live'
    release.set()
    wait(lambda:'Offline: 93' in app.device_summary_label.cget('text'))
    app.device_table.selection_set('1');app.device_table.focus('1')
    state['online']=True
    # No click: periodic worker + UI timer must reflect reconnect.
    wait(lambda:app.device_table.item('1','values')[4]=='Online')
    assert app.device_table.selection()==('1',);assert app.device_table.focus()=='1'
    assert app.device_table.item('1','values')[8]!='-'
    assert 'Online: 1' in app.device_summary_label.cget('text')
    output=Path(folder.name)/'devices.xlsx'
    with patch.object(main.filedialog,'asksaveasfilename',return_value=str(output)),patch.object(main.messagebox,'showinfo'):
        app.export_devices_excel()
    exported=main.pd.read_excel(output)
    assert len(exported)==93 and 'Lần kiểm tra mạng' in exported.columns
    assert exported.loc[exported['ID']==1,'Trạng thái'].iloc[0]=='Online'

    app.device_status_filter_var.set('Online');app.apply_device_filters()
    assert app.device_table.get_children()==('1',)
    app.device_status_filter_var.set('All');app.device_search_var.set('lab-93');app.apply_device_filters()
    assert len(app.device_table.get_children())==1
    app.device_search_var.set('');app.apply_device_filters()
    # Manual refresh wakes a monitor whose next scheduled cycle is far away.
    monitor.interval=120;wait(lambda:not monitor.snapshot()[1]);state['online']=False
    app.refresh_device_manager();wait(lambda:app.device_table.item('1','values')[4]=='Offline')
    app.show_dashboard();root.update();app.show_device_manager();root.update()
    app.show_dashboard();root.update()
    # Old table's timer must be cancelled, even after its due time.
    deadline=time.monotonic()+1.1
    while time.monotonic()<deadline:root.update();time.sleep(.01)
    assert not errors,errors
    app.on_close();wait(lambda:not monitor.thread.is_alive())
    assert not errors,errors
    print('PASS: 93-device real Tk page; startup Unknown; automatic Offline→Online; fresh timestamp; selection/filter; manual refresh; page timer cleanup; worker shutdown; no callback errors.')
finally:
    release.set()
    if monitor:
        monitor.stop();monitor.thread.join(4)
    if root:
        try:root.destroy()
        except tk.TclError:pass
    for item in reversed(patches):item.stop()
    folder.cleanup()
