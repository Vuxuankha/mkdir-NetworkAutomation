"""Native Tk NOC dashboard inspired by the supplied dark cyan/magenta reference."""
from datetime import datetime
import math
import tkinter as tk
from tkinter import ttk
from database.db import get_connection
from app_runtime import data_path
from agent_runtime import heartbeat_status

from modules.ui_theme import PALETTE as UI_COLORS

BG=UI_COLORS['background'];PANEL=UI_COLORS['surface'];PANEL2=UI_COLORS['surface_alt'];BORDER=UI_COLORS['border']
TEXT=UI_COLORS['text'];MUTED=UI_COLORS['muted'];CYAN=UI_COLORS['accent'];PINK=UI_COLORS['pink'];RED=UI_COLORS['danger'];GREEN=UI_COLORS['success']


def dashboard_columns(width):
    return 5 if width>=1100 else (3 if width>=780 else 2)


def collect_snapshot(connect=get_connection):
    """Read current state, retaining unavailable flags instead of inventing healthy results."""
    result={'total':None,'online':None,'offline':None,'other':None,'alerts':None,'incidents':None,
            'attention':[],'events':[],'unavailable':[]}
    try:connection=connect()
    except Exception:
        result['unavailable']=['Thiết bị','Cảnh báo','Sự cố'];return result
    try:
        try:
            counts=connection.execute("SELECT LOWER(TRIM(COALESCE(status,''))),COUNT(*) FROM network_devices GROUP BY LOWER(TRIM(COALESCE(status,'')))").fetchall()
            result['total']=sum(row[1] for row in counts)
            result['online']=sum(row[1] for row in counts if row[0]=='online')
            result['offline']=sum(row[1] for row in counts if row[0]=='offline')
            result['other']=result['total']-result['online']-result['offline']
            for row in connection.execute("SELECT name,ip,device_type,status FROM network_devices WHERE LOWER(TRIM(COALESCE(status,'')))<>'online' ORDER BY updated_at DESC LIMIT 8"):
                result['attention'].append(('Thiết bị',row[1] or row[0] or '—',str(row[3] or 'Chưa xác định')+' · '+str(row[2] or 'Chưa phân loại')))
        except Exception:result['unavailable'].append('Thiết bị')
        try:
            result['alerts']=connection.execute("SELECT COUNT(*) FROM alerts WHERE LOWER(TRIM(COALESCE(status,'')))<>'closed'").fetchone()[0]
            for row in connection.execute("SELECT created_at,severity,ip,alert_type,message FROM alerts WHERE LOWER(TRIM(COALESCE(status,'')))<>'closed' ORDER BY id DESC LIMIT 8"):
                result['events'].append((row[0] or '—',row[1] or 'Cảnh báo',row[2] or '—',row[4] or row[3] or ''))
                if len(result['attention'])<12:result['attention'].append((row[1] or 'Cảnh báo',row[2] or '—',row[4] or row[3] or ''))
        except Exception:result['unavailable'].append('Cảnh báo')
        try:
            result['incidents']=connection.execute("SELECT COUNT(*) FROM incidents WHERE LOWER(TRIM(COALESCE(status,''))) NOT IN ('closed','resolved')").fetchone()[0]
            incidents=[(row[0] or '—',row[1] or 'Sự cố',row[2] or '—',row[3] or '') for row in connection.execute("SELECT last_seen,severity,host,title FROM incidents WHERE LOWER(TRIM(COALESCE(status,''))) NOT IN ('closed','resolved') ORDER BY id DESC LIMIT 6")]
            result['events']=sorted(result['events']+incidents,key=lambda row:str(row[0]),reverse=True)[:14]
        except Exception:result['unavailable'].append('Sự cố')
    finally:connection.close()
    return result


def button(parent,text,command,accent=False):
    widget=tk.Button(parent,text=text,command=command,bg='#21444F' if accent else PANEL2,fg=CYAN if accent else TEXT,
        activebackground='#2B5360',activeforeground='white',relief='flat',bd=0,padx=14,pady=8,
        font=('Segoe UI',10,'bold' if accent else 'normal'),cursor='hand2',highlightthickness=1,highlightbackground=BORDER)
    return widget


def label(parent,text='',**options):
    defaults={'bg':parent.cget('bg'),'fg':TEXT,'font':('Segoe UI',10),'anchor':'w','justify':'left'}
    defaults.update(options)
    return tk.Label(parent,text=text,**defaults)


class DarkDashboard:
    def __init__(self,app):
        self.app=app;self.closed=False;self.after_id=None;self.tick=0;self.snapshot={};self.columns=None;self.wide=None
        self.frame=tk.Frame(app.content,bg=BG);self.frame.pack(fill='both',expand=True)
        self.frame.bind('<Destroy>',self.destroy,add='+')
        # Native scroll container keeps all cards/actions reachable on small displays.
        self.canvas=tk.Canvas(self.frame,bg=BG,highlightthickness=0)
        scrollbar=ttk.Scrollbar(self.frame,orient='vertical',command=self.canvas.yview,style='NOC.Vertical.TScrollbar')
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side='left',fill='both',expand=True);scrollbar.pack(side='right',fill='y')
        self.body=tk.Frame(self.canvas,bg=BG)
        self.body_window=self.canvas.create_window((0,0),window=self.body,anchor='nw')
        self.canvas.bind('<Configure>',self.resize)
        self.body.bind('<Configure>',lambda event:self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<MouseWheel>',lambda event:self.canvas.yview_scroll(-int(event.delta/120),'units'))
        self.styles();self.build();self.install_wheel();self.refresh();self.poll()

    def install_wheel(self):
        # A page-specific bindtag lets labels/buttons scroll the page, while
        # Text/Treeview retain their own native wheel handling.
        self.wheel_tag='NOCScroll'+str(self.frame)
        def scroll(event):
            units=-1 if getattr(event,'num',None)==4 else (1 if getattr(event,'num',None)==5 else -int(event.delta/120))
            self.canvas.yview_scroll(units,'units');return 'break'
        for sequence in ('<MouseWheel>','<Button-4>','<Button-5>'):
            self.frame.bind_class(self.wheel_tag,sequence,scroll)
        def attach(widget):
            if widget.winfo_class() not in ('Text','Treeview','TScrollbar'):
                widget.bindtags((self.wheel_tag,)+widget.bindtags())
            for child in widget.winfo_children():attach(child)
        attach(self.body)

    def styles(self):
        style=ttk.Style(self.frame)
        style.configure('NOC.TFrame',background=PANEL)
        style.configure('NOC.Treeview',background=PANEL,fieldbackground=PANEL,foreground=TEXT,rowheight=31,borderwidth=0,font=('Segoe UI',9))
        style.configure('NOC.Treeview.Heading',background=PANEL2,foreground=MUTED,relief='flat',padding=(8,9),font=('Segoe UI',9,'bold'))
        style.map('NOC.Treeview',background=[('selected','#254553')],foreground=[('selected','white')])
        style.map('NOC.Treeview.Heading',background=[('active','#254553')])
        for name in ('Vertical','Horizontal'):
            style.configure('NOC.'+name+'.TScrollbar',background=BORDER,troughcolor=BG,bordercolor=BG,arrowcolor=MUTED)
        style.configure('NOC.Horizontal.TProgressbar',background=CYAN,troughcolor=BG,bordercolor=BORDER,lightcolor=CYAN,darkcolor=CYAN)

    def build(self):
        app=self.app
        heading=tk.Frame(self.body,bg=BG);heading.pack(fill='x',padx=20,pady=(18,12))
        label(heading,'One-Click NOC',font=('Segoe UI',22,'bold')).pack(side='left')
        self.time_label=label(heading,fg=MUTED,font=('Segoe UI',9));self.time_label.pack(side='right')
        self.hero=tk.Canvas(self.body,height=82,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
        self.hero.pack(fill='x',padx=20,pady=(0,14));self.hero.bind('<Configure>',self.draw_hero)
        self.hero_action=button(self.hero,'◎  Trung tâm NOC',app.show_noc_dashboard,True)
        self.hero_action.place(relx=1,rely=.5,anchor='e',x=-16)
        self.metrics=tk.Frame(self.body,bg=BG);self.metrics.pack(fill='x',padx=16)
        self.cards=[];self.values={}
        for title,key,note,color in [('Thiết bị','total','Tất cả thiết bị',CYAN),('Online','online','Đang hoạt động',GREEN),('Offline','offline','Cần kiểm tra',RED),('Cảnh báo mở','alerts','Chưa đóng',PINK),('Sự cố mở','incidents','Chưa xử lý xong',PINK)]:
            card=tk.Frame(self.metrics,bg=PANEL,highlightthickness=1,highlightbackground=BORDER);self.cards.append(card)
            label(card,title,fg=MUTED).pack(anchor='w',padx=16,pady=(13,2))
            self.values[key]=tk.StringVar(value='—')
            if key=='total':
                ring_row=tk.Frame(card,bg=PANEL);ring_row.pack(fill='both',expand=True)
                self.donut=tk.Canvas(ring_row,width=104,height=104,bg=PANEL,highlightthickness=0);self.donut.pack(side='left',padx=5,pady=2)
                legend=tk.Frame(ring_row,bg=PANEL);legend.pack(side='left',fill='x',expand=True,padx=(0,8))
                for text,tint in [('● Online',GREEN),('● Offline',RED),('● Khác',PINK)]:label(legend,text,fg=tint,font=('Segoe UI',8)).pack(anchor='w',pady=2)
            else:
                label(card,textvariable=self.values[key],fg=color,font=('Segoe UI',29,'bold')).pack(anchor='w',padx=16)
                label(card,note,fg=MUTED,font=('Segoe UI',9)).pack(anchor='w',padx=16,pady=(0,12))
        self.status_row=tk.Frame(self.body,bg=BG);self.status_row.pack(fill='x',padx=20,pady=14)
        self.audit=tk.Frame(self.status_row,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
        audit_top=tk.Frame(self.audit,bg=PANEL);audit_top.pack(fill='x',padx=14,pady=(12,3))
        label(audit_top,'▦  Daily Audit Windows',font=('Segoe UI',12,'bold')).pack(side='left')
        button(audit_top,'Mở Audit',app.show_daily_audit).pack(side='right')
        self.audit_label=label(self.audit,fg=MUTED,wraplength=450);self.audit_label.pack(fill='x',padx=14,pady=(0,12))
        self.connection=tk.Frame(self.status_row,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
        connection_text=tk.Frame(self.connection,bg=PANEL);connection_text.pack(side='left',fill='both',expand=True,pady=12,padx=14)
        label(connection_text,'Trạng thái thiết bị',font=('Segoe UI',11,'bold')).pack(anchor='w')
        self.legend=label(connection_text,fg=MUTED);self.legend.pack(anchor='w',pady=4)
        self.agent=label(connection_text,fg=CYAN,wraplength=260,font=('Segoe UI',9));self.agent.pack(fill='x')
        # Existing one-click audit workflow lives in a foldable panel.
        quick_header=tk.Frame(self.body,bg=BG);quick_header.pack(fill='x',padx=20,pady=(0,9))
        self.quick_toggle=button(quick_header,'＋  Kiểm tra IP / Excel',self.toggle_quick,True);self.quick_toggle.pack(side='left')
        button(quick_header,'Trung tâm NOC',app.show_noc_dashboard).pack(side='left',padx=8)
        self.updated=label(quick_header,fg=MUTED,font=('Segoe UI',9));self.updated.pack(side='right')
        self.quick_header=quick_header
        self.quick=tk.Frame(self.body,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
        self.quick_open=False
        self.build_quick()
        self.tables=tk.Frame(self.body,bg=BG);self.tables.pack(fill='both',expand=True,padx=16,pady=(0,16))
        self.attention_box,self.attention=self.table(self.tables,'Cần chú ý',[('kind','Loại',110),('target','Thiết bị / IP',150),('detail','Chi tiết',300)],app.show_alerts)
        self.events_box,self.events=self.table(self.tables,'Sự cố & cảnh báo gần đây',[('time','Thời gian',150),('level','Mức',80),('target','Đích',120),('detail','Nội dung',310)],app.show_incident_center)
        self.notice=label(self.body,fg=MUTED,wraplength=850,font=('Segoe UI',9));self.notice.pack(fill='x',padx=20,pady=(0,14))

    def build_quick(self):
        from modules.responsive_layout import FlowRow
        app=self.app
        label(self.quick,'Nhập IP cần kiểm tra hoặc nạp Excel',font=('Segoe UI',11,'bold')).pack(anchor='w',padx=14,pady=(12,6))
        app.quick_ip_text=tk.Text(self.quick,height=3,width=1,bg=BG,fg=TEXT,insertbackground=CYAN,relief='flat',font=('Consolas',10),wrap='word')
        app.quick_ip_text.pack(fill='x',padx=14)
        app.quick_excel_path='';app.quick_email_var=tk.BooleanVar(value=True);app.quick_authorized_var=tk.BooleanVar(value=False)
        actions=tk.Frame(self.quick,bg=PANEL);actions.pack(fill='x',padx=14,pady=9)
        app.quick_run_btn=button(actions,'KIỂM TRA TOÀN BỘ',app._quick_run_all,True)
        checkbox_options=dict(bg=PANEL,fg=TEXT,selectcolor=BG,activebackground=PANEL,activeforeground=TEXT,highlightthickness=0,font=('Segoe UI',9))
        widgets=[button(actions,'Chọn Excel IP',app._quick_choose_excel),app.quick_run_btn,
            tk.Checkbutton(actions,text='Gửi Email khi xong',variable=app.quick_email_var,**checkbox_options),
            tk.Checkbutton(actions,text='Tôi có quyền kiểm tra IP',variable=app.quick_authorized_var,**checkbox_options)]
        FlowRow(actions,widgets,row_style='NOC.TFrame')
        app.quick_status_var=tk.StringVar(value='Sẵn sàng · Dán IP hoặc chọn Excel')
        status=label(self.quick,textvariable=app.quick_status_var,fg=CYAN,wraplength=750,font=('Segoe UI',9));status.pack(fill='x',padx=14)
        self.quick.bind('<Configure>',lambda event:status.configure(wraplength=max(220,event.width-32)))
        app.quick_progress=ttk.Progressbar(self.quick,mode='determinate',style='NOC.Horizontal.TProgressbar');app.quick_progress.pack(fill='x',padx=14,pady=(8,12))

    def table(self,parent,title,columns,command):
        box=tk.Frame(parent,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
        heading=tk.Frame(box,bg=PANEL);heading.pack(fill='x',padx=12,pady=(10,8))
        label(heading,title,font=('Segoe UI',12,'bold')).pack(side='left')
        button(heading,'Mở',command).pack(side='right')
        grid=tk.Frame(box,bg=PANEL);grid.pack(fill='both',expand=True,padx=10,pady=(0,10))
        grid.columnconfigure(0,weight=1);grid.rowconfigure(0,weight=1)
        tree=ttk.Treeview(grid,columns=[item[0] for item in columns],show='headings',height=7,style='NOC.Treeview')
        for key,title,width in columns:tree.heading(key,text=title);tree.column(key,width=width,minwidth=70,stretch=key=='detail')
        ys=ttk.Scrollbar(grid,orient='vertical',command=tree.yview,style='NOC.Vertical.TScrollbar');xs=ttk.Scrollbar(grid,orient='horizontal',command=tree.xview,style='NOC.Horizontal.TScrollbar')
        tree.configure(yscrollcommand=ys.set,xscrollcommand=xs.set)
        tree.grid(row=0,column=0,sticky='nsew');ys.grid(row=0,column=1,sticky='ns');xs.grid(row=1,column=0,sticky='ew')
        tree.tag_configure('even',background=PANEL);tree.tag_configure('odd',background=PANEL2)
        return box,tree

    def toggle_quick(self):
        self.quick_open=not self.quick_open
        if self.quick_open:self.quick.pack(fill='x',padx=20,pady=(0,14),after=self.quick_header)
        else:self.quick.pack_forget()
        self.quick_toggle.configure(text=('−  ' if self.quick_open else '＋  ')+'Kiểm tra IP / Excel')

    def draw_hero(self,event):
        c=self.hero;c.delete('art');width=event.width
        # Circuit lines are decorative, not a traffic chart.
        for index,color in enumerate((CYAN,PINK,'#306879')):
            points=[]
            for step in range(17):
                x=145+step*max(1,width-370)/16;y=40+math.sin(step*.65+index)*17+index*3
                points.extend((x,y))
            c.create_line(*points,fill='#213440',width=9,smooth=True,tags='art')
            c.create_line(*points,fill=color,width=1,smooth=True,tags='art')
            for step in (2,6,11,14):
                x,y=points[step*2:step*2+2];c.create_oval(x-4,y-4,x+4,y+4,fill=PANEL,outline=color,tags='art')
        c.create_text(18,26,text='ONE-CLICK NOC',fill=TEXT,anchor='w',font=('Segoe UI',12,'bold'),tags='art')
        c.create_text(18,54,text='NETWORK OPERATIONS',fill=MUTED,anchor='w',font=('Segoe UI',8),tags='art')
        c.create_line(18,69,125,69,fill=CYAN,width=2,tags='art')

    def resize(self,event):
        width=event.width;self.canvas.itemconfigure(self.body_window,width=width)
        columns=dashboard_columns(width)
        if columns!=self.columns:
            for col in range(5):self.metrics.columnconfigure(col,weight=1 if col<columns else 0,uniform='cards' if col<columns else '')
            for index,card in enumerate(self.cards):card.grid(row=index//columns,column=index%columns,sticky='nsew',padx=4,pady=4)
            self.columns=columns
        wide=width>=1000
        if wide!=self.wide:
            for widget in (self.audit,self.connection,self.attention_box,self.events_box):widget.grid_forget()
            for parent in (self.status_row,self.tables):
                parent.columnconfigure(0,weight=1);parent.columnconfigure(1,weight=1 if wide else 0)
            self.audit.grid(row=0,column=0,sticky='nsew',padx=(0,4),pady=4)
            self.connection.grid(row=0 if wide else 1,column=1 if wide else 0,sticky='nsew',padx=(4,0) if wide else (0,4),pady=4)
            self.attention_box.grid(row=0,column=0,sticky='nsew',padx=4,pady=4)
            self.events_box.grid(row=0 if wide else 1,column=1 if wide else 0,sticky='nsew',padx=4,pady=4)
            self.wide=wide
        self.audit_label.configure(wraplength=max(220,(width//2 if wide else width)-80))
        self.notice.configure(wraplength=max(250,width-50))

    def refresh(self):
        snapshot=collect_snapshot();self.snapshot=snapshot
        for key,var in self.values.items():var.set('—' if snapshot[key] is None else str(snapshot[key]))
        for tree,rows,empty in ((self.attention,snapshot['attention'],'Không có mục cần chú ý trong dữ liệu hiện tại'),(self.events,snapshot['events'],'Chưa có cảnh báo hoặc sự cố đang mở')):
            tree.delete(*tree.get_children())
            if snapshot['unavailable']:empty='Dữ liệu chưa đầy đủ: '+', '.join(snapshot['unavailable'])
            if not rows:rows=[('—','—',empty)] if tree is self.attention else [('—','—','—',empty)]
            for index,row in enumerate(rows):tree.insert('','end',values=row,tags=('odd' if index%2 else 'even',))
        status,detail,_=self.app._daily_audit_dashboard_summary();self.audit_label.configure(text=status+' · '+detail)
        state,_=heartbeat_status(data_path('agent_status.json'));self.agent.configure(text='Giám sát nền: '+state)
        unavailable=snapshot['unavailable']
        self.notice.configure(text='Chưa đọc được dữ liệu: '+', '.join(unavailable) if unavailable else 'Dữ liệu thiết bị từ cơ sở dữ liệu giám sát · Tự làm mới mỗi 5 giây')
        self.updated.configure(text='Cập nhật '+datetime.now().strftime('%H:%M:%S'))
        self.draw_donut()

    def draw_donut(self):
        c=self.donut;c.delete('all');snap=self.snapshot;total=snap.get('total')
        c.create_oval(10,10,94,94,outline=BORDER,width=8)
        start=90
        if total:
            for key,color in (('online',GREEN),('offline',RED),('other',PINK)):
                extent=360*(snap[key] or 0)/total
                if extent:c.create_arc(10,10,94,94,start=start,extent=-extent,style='arc',outline=color,width=8)
                start-=extent
        c.create_text(52,47,text='—' if total is None else str(total),fill=TEXT,font=('Segoe UI',18,'bold'))
        c.create_text(52,68,text='thiết bị',fill=MUTED,font=('Segoe UI',8))
        self.legend.configure(text='Online '+str(snap.get('online') if snap.get('online') is not None else '—')+'  ·  Offline '+str(snap.get('offline') if snap.get('offline') is not None else '—')+'\nKhác / chưa rõ '+str(snap.get('other') if snap.get('other') is not None else '—'))

    def poll(self):
        if self.closed:return
        self.time_label.configure(text=datetime.now().strftime('%d/%m/%Y · %H:%M:%S'))
        self.app._quick_poll(schedule=False)
        self.tick+=1
        if self.tick%5==0:self.refresh()
        self.after_id=self.frame.after(1000,self.poll)

    def destroy(self,event):
        if event.widget is not self.frame:return
        self.closed=True
        if self.after_id is not None:
            try:self.frame.after_cancel(self.after_id)
            except tk.TclError:pass
        self.after_id=None
        for sequence in ('<MouseWheel>','<Button-4>','<Button-5>'):
            try:self.frame.unbind_class(self.wheel_tag,sequence)
            except tk.TclError:pass
