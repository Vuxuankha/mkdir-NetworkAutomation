"""Persistent assistant window and explicit read-only local diagnostic tools."""
import json
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox,filedialog
from database.db import get_connection
from modules import monitor_extensions as ext
from modules.ping_check import ping_host

class GlobalAssistant:
    def __init__(self,app):
        self.app=app;self.window=None;self.turns=[];self.busy=False;self.results=queue.Queue();self.image=None;self.stop_event=threading.Event();self.closed=False;self.poll_id=None
        tk.Button(app.root,text='AI · Trợ lý',command=self.open,bg='#2563EB',fg='white',activebackground='#1D4ED8',activeforeground='white',relief='flat',font=('Segoe UI',10,'bold'),padx=18,pady=10,cursor='hand2').place(relx=1,rely=1,anchor='se',x=-18,y=-18)

    def open(self):
        if self.window is not None and self.window.winfo_exists():
            self.window.deiconify();self.window.lift();return
        from modules.assistant_ui import build
        build(self)
        self.poll_id=self.window.after(100,self.poll)

    def append_chat(self,text,tag='ai'):
        self.chat.configure(state='normal');self.chat.insert('end',text,tag);self.chat.configure(state='disabled');self.chat.see('end')

    def template(self,text):
        if self.busy:return
        self.prompt.delete('1.0','end');self.prompt.insert('1.0',text);self.prompt.focus_set()

    def refresh_tasks(self):
        from modules.ai_tasks import task_history
        self.task_rows={record['id']:record for record in task_history()}
        for item in self.task_list.get_children():self.task_list.delete(item)
        for key,record in self.task_rows.items():
            self.task_list.insert('','end',iid=key,values=(record['created_at'][:19].replace('T',' '),record['objective'][:160],record['display_state'],len(record['steps'])))

    def open_report(self):
        import os
        from pathlib import Path
        from app_runtime import REPORT_DIR
        selected=self.task_list.selection()
        if not selected:self.status.set('Chọn tác vụ để mở báo cáo.');return
        path=(REPORT_DIR/'ai_tasks'/selected[0]/'report.txt').resolve()
        try:
            if not path.is_file():raise ValueError('Tác vụ chưa có báo cáo.')
            if os.name=='nt':os.startfile(str(path))
            else:messagebox.showinfo('Báo cáo',str(path),parent=self.window)
        except Exception as exc:self.status.set(str(exc))

    def change_provider(self,event=None):
        from modules import ai_preferences
        self.model.set(ai_preferences.load()['models'].get(self.provider.get(),''))
        self.key_label.configure(text=ai_preferences.key_status(self.provider.get()))

    def save_ai_config(self):
        from modules import ai_preferences
        try:
            ai_preferences.save(self.provider.get(),self.model.get())
            self.status.set('Đã lưu nhà cung cấp/model; không lưu API key.')
        except Exception as exc:self.status.set(str(exc))

    def test_ai_connection(self):
        provider=self.provider.get();model=self.model.get().strip()
        if not model:self.status.set('Nhập model trước khi kiểm tra API.');return
        fn=ext.ai_analyze if provider=='OpenAI' else ext.gemini_analyze
        self.job(lambda:fn('Trả lời đúng một từ: OK',model),'connection',provider)

    def task_progress(self,name,info):
        self.results.put(('step_progress',name,info,None))

    def context(self):
        page=getattr(self.app,'current_page','Tổng quan')
        from modules.assistant_tools import page_context
        try:data=page_context(page,getattr(self.app,'scan_results',[]))
        except Exception as exc:self.status.set(str(exc));return
        self.prompt.insert('end','\n'+ext.redact(json.dumps(data,ensure_ascii=False,indent=2)))

    def choose_image(self):
        self.image=filedialog.askopenfilename(parent=self.window,filetypes=[('Ảnh','*.jpg *.jpeg *.png *.webp')]) or None
        self.image_label.configure(text='Ảnh: '+(__import__('pathlib').Path(self.image).name if self.image else 'chưa chọn'))

    def job(self,fn,kind,text=''):
        if self.busy:return
        self.stop_event.clear();self.busy=True;self.status.set('Đang xử lý...');self.progress.start(12);self.send_button.configure(state='disabled')
        def worker():
            try:self.results.put((kind,text,fn(),None))
            except Exception as exc:self.results.put((kind,text,'',str(exc)))
        threading.Thread(target=worker,daemon=True).start()

    def send(self):
        if self.busy:return
        text=self.prompt.get('1.0','end').strip();provider=self.provider.get();model=self.model.get().strip();image=self.image;use_tools=self.use_tools.get()
        if not text or not model:self.status.set('Nhập nội dung và model trước.');return
        autonomous=self.autonomous.get()
        if autonomous:
            from modules.ai_tasks import make_scope,run_task
            try:scope=make_scope(text)
            except Exception as exc:self.status.set(str(exc));return
            description=('Tự hoàn thành kiểm tra trên '+str(len(scope['devices']))+' thiết bị, '+str(len(scope['cameras']))+
                ' camera đã khai báo và IP trong mục tiêu.\nIP được duyệt ('+str(len(scope['allowed_ips']))+'): '+', '.join(scope['allowed_ips'][:10])+(' …' if len(scope['allowed_ips'])>10 else '')+
                '\nTối đa 6 lượt API/10 công cụ, 5 phút + thời gian chờ tác vụ đang chạy. Kết quả gửi tới '+provider+
                ' (kèm ảnh nếu đã chọn) và báo cáo lưu cục bộ. Có thể phát sinh phí API. Không sửa cấu hình hoặc chạy SSH. Tiến hành?')
            if not messagebox.askyesno('Duyệt phạm vi tác vụ',description,parent=self.window):return
            self.job(lambda:run_task(text,provider,model,scope,image,self.stop_event,self.trace_tool,status_callback=self.task_progress),'task',text)
            return
        if not messagebox.askyesno('Gửi tới '+provider,'Gửi hội thoại/ảnh tới '+provider+'? Nếu bật công cụ, kết quả kiểm tra bạn duyệt cũng được gửi để AI tổng hợp. Có thể phát sinh phí API.',parent=self.window):return
        transcript='\n'.join(self.turns[-12:])+ '\nNgười dùng: '+text
        fn=ext.ai_analyze if provider=='OpenAI' else ext.gemini_analyze
        if use_tools:
            from modules.assistant_agent import chat
            self.job(lambda:chat(provider,model,transcript,image,self.approve_tool,self.stop_event,self.trace_tool),'ai',text)
        else:
            self.job(lambda:fn(transcript,model,image),'ai',text)

    def ping(self):
        try:host=ext.validate_host(self.host.get())
        except Exception as exc:self.status.set(str(exc));return
        self.job(lambda:json.dumps(ping_host(host,1000),ensure_ascii=False,indent=2),'tool')

    def cameras(self):
        def check():
            ext.ensure_tables();result=[]
            for camera in ext.cameras():
                status,detail=ext.check_camera(camera);result.append({'name':camera['name'],'host':camera['host'],'status':status,'detail':detail})
            return json.dumps(result,ensure_ascii=False,indent=2)
        self.job(check,'tool')

    def clear(self):
        if self.busy:return
        self.turns=[];self.chat.configure(state='normal');self.chat.delete('1.0','end');self.chat.configure(state='disabled');self.image=None;self.image_label.configure(text='Chưa chọn ảnh');self.prompt.delete('1.0','end')

    def cancel(self):
        self.stop_event.set();self.status.set('Đang dừng; yêu cầu API đã gửi có thể chờ tới timeout.')

    def approve_tool(self,name,args):
        response=queue.Queue(maxsize=1)
        self.results.put(('approval',name,args,response))
        while not self.stop_event.is_set() and not self.closed:
            try:return response.get(timeout=.1)
            except queue.Empty:pass
        return False

    def trace_tool(self,name,args,result):
        self.results.put(('trace',name,result,None))

    def shutdown(self):
        self.closed=True;self.stop_event.set()
        if self.window is not None and self.poll_id is not None:
            try:self.window.after_cancel(self.poll_id)
            except tk.TclError:pass
        self.poll_id=None

    def poll(self):
        self.poll_id=None
        if self.closed:return
        try:
            if not self.window.winfo_exists():return
        except tk.TclError:return
        try:
            kind,text,result,error=self.results.get_nowait()
            if kind=='approval':
                approved=False
                if not self.stop_event.is_set():
                    self.window.deiconify();self.window.lift()
                    approved=messagebox.askyesno('Duyệt kiểm tra cục bộ',text+'\n'+json.dumps(result,ensure_ascii=False)+'\nThao tác đọc/kiểm tra; kết quả sẽ gửi tới AI để tổng hợp.',parent=self.window)
                error.put(approved)
            elif kind=='step_progress':
                self.status.set(text+' · '+str(result.get('completed',0))+'/'+str(result.get('total',0))+' · '+result.get('target',''))
            elif kind=='trace':
                self.append_chat('Công cụ '+text+': '+str(result)+'\n\n','tool');self.status.set('Đã kiểm tra: '+text)
            else:
                self.busy=False;self.progress.stop();self.send_button.configure(state='normal')
                if kind=='task' and not error:
                    self.append_chat('Bạn: '+text+'\n','user')
                    self.append_chat(result['answer']+'\nBáo cáo: '+result['report']+'\n\n','ai')
                    label={'finished':'Đã tổng hợp','failed':'Có lỗi','needs_review':'Cần xem lại','cancelled':'Đã hủy'}.get(result['state'],result['state'])
                    self.status.set(label+' · '+str(result['steps'])+' bước · Đã lưu báo cáo')
                    self.refresh_tasks()
                    if self.prompt.get('1.0','end').strip()==text:self.prompt.delete('1.0','end')
                elif self.stop_event.is_set():self.status.set('Đã dừng tác vụ')
                elif error:self.status.set(error)
                elif kind=='connection':
                    self.status.set('Kết nối '+text+' thành công: '+str(result)[:80])
                    self.key_label.configure(text=__import__('modules.ai_preferences',fromlist=['key_status']).key_status(self.provider.get()))
                elif kind=='ai':
                    self.turns.extend(['Người dùng: '+text,'AI: '+result]);self.turns=self.turns[-20:]
                    self.append_chat('Bạn: '+text+'\n','user');self.append_chat('AI: '+result+'\n\n','ai')
                    if self.prompt.get('1.0','end').strip()==text:self.prompt.delete('1.0','end')
                    self.status.set('Hoàn tất')
                else:
                    self.prompt.insert('end','\nKết quả kiểm tra cục bộ:\n'+str(result));self.status.set('Đã kiểm tra. Xem kết quả trước khi gửi AI.')
            self.chat.see('end')
        except queue.Empty:pass
        if not self.closed:self.poll_id=self.window.after(100,self.poll)
