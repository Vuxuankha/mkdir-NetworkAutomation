"""Responsive ttk layout for the persistent assistant controller."""
import tkinter as tk
from tkinter import ttk, simpledialog
from tkinter.scrolledtext import ScrolledText
from modules.responsive_layout import FlowRow,ScrollablePanel

BG='#F3F4F6';INK='#172033';BLUE='#2563EB';MUTED='#64748B'


def build(controller):
    c=controller
    w=c.window=tk.Toplevel(c.app.root);w.title('Network Automation · Trợ lý AI');w.geometry('960x780');w.minsize(640,640)
    w.configure(bg=BG);w.protocol('WM_DELETE_WINDOW',w.withdraw)
    style=ttk.Style(w)
    style.configure('AI.TFrame',background=BG)
    style.configure('AI.Card.TFrame',background='white')
    style.configure('AI.TLabel',background=BG,foreground=INK,font=('Segoe UI',10))
    style.configure('AI.Title.TLabel',background=BG,foreground=INK,font=('Segoe UI',21,'bold'))
    style.configure('AI.Muted.TLabel',background=BG,foreground=MUTED,font=('Segoe UI',10))
    style.configure('AI.Primary.TButton',padding=(18,9),font=('Segoe UI',10,'bold'),foreground='white',background=BLUE)
    style.map('AI.Primary.TButton',background=[('disabled','#94A3B8'),('active','#1D4ED8')])
    style.configure('AI.TButton',padding=(10,7),font=('Segoe UI',10))
    style.configure('AI.TCheckbutton',background=BG,font=('Segoe UI',10))
    shell=ttk.Frame(w,style='AI.TFrame',padding=16);shell.pack(fill='both',expand=True)
    header=ttk.Frame(shell,style='AI.TFrame');header.pack(fill='x',pady=(0,14))
    ttk.Label(header,text='Trợ lý vận hành',style='AI.Title.TLabel').pack(anchor='w')
    description=ttk.Label(header,text='Hỏi đáp, kiểm tra mạng và theo dõi tác vụ trong cùng một cửa sổ.',style='AI.Muted.TLabel',wraplength=820)
    description.pack(anchor='w',pady=(3,0))
    config=ttk.Frame(shell,style='AI.TFrame');config.pack(fill='x',pady=(0,12))
    from modules import ai_preferences
    preferences=ai_preferences.load()
    c.provider=tk.StringVar(value=preferences['provider']);c.model=tk.StringVar(value=preferences['models'][preferences['provider']]);c.use_tools=tk.BooleanVar(value=True);c.autonomous=tk.BooleanVar(value=False)
    ttk.Label(config,text='Nhà cung cấp',style='AI.TLabel').grid(row=0,column=0,sticky='w')
    ttk.Label(config,text='Model',style='AI.TLabel').grid(row=0,column=1,sticky='w',padx=(12,0))
    provider_choice=ttk.Combobox(config,textvariable=c.provider,values=('OpenAI','Gemini'),state='readonly',width=14)
    provider_choice.grid(row=1,column=0,sticky='ew',pady=4);provider_choice.bind('<<ComboboxSelected>>',c.change_provider)
    ttk.Entry(config,textvariable=c.model).grid(row=1,column=1,sticky='ew',padx=(12,0),pady=4)
    config.columnconfigure(1,weight=1)
    tool_check=ttk.Checkbutton(config,text='Cho AI gọi kiểm tra',variable=c.use_tools,style='AI.TCheckbutton');tool_check.grid(row=2,column=0,sticky='w',pady=(5,0))
    auto_check=ttk.Checkbutton(config,text='Tự hoàn thành và lưu báo cáo',variable=c.autonomous,style='AI.TCheckbutton');auto_check.grid(row=2,column=1,sticky='w',padx=(12,0),pady=(5,0))
    c.tabs=ttk.Notebook(shell);c.tabs.pack(fill='both',expand=True)
    chat_page=ttk.Frame(c.tabs,padding=12,style='AI.Card.TFrame');history_page=ttk.Frame(c.tabs,padding=12,style='AI.Card.TFrame')
    c.tabs.add(chat_page,text='  Hội thoại  ');c.tabs.add(history_page,text='  Lịch sử tác vụ  ')
    settings_tab=ttk.Frame(c.tabs)
    c.tabs.add(settings_tab,text='  Cấu hình AI  ')
    settings_page=ScrollablePanel(settings_tab).body
    ttk.Label(settings_page,text='Cấu hình kết nối',font=('Segoe UI',15,'bold')).pack(anchor='w',pady=(0,12))
    config_note=ttk.Label(settings_page,text='Chọn nhà cung cấp và nhập model ở thanh phía trên. Mỗi nhà cung cấp có model lưu riêng.',wraplength=500);config_note.pack(anchor='w',pady=6)
    c.key_label=ttk.Label(settings_page,text=ai_preferences.key_status(c.provider.get()),wraplength=500)
    c.key_label.pack(anchor='w',pady=8)
    settings_actions=ttk.Frame(settings_page);settings_actions.pack(fill='x',pady=8)
    FlowRow(settings_actions,[ttk.Button(settings_actions,text='Lưu cấu hình',command=c.save_ai_config),ttk.Button(settings_actions,text='Kiểm tra API',command=c.test_ai_connection)])
    cost_note=ttk.Label(settings_page,text='Kiểm tra API gửi một câu hỏi ngắn, có thể phát sinh phí. API key tiếp tục lấy từ biến môi trường, không ghi vào file cấu hình.',wraplength=500);cost_note.pack(anchor='w',pady=10)

    settings_page.bind('<Configure>',lambda event:[label.configure(wraplength=max(200,event.width-24)) for label in (config_note,c.key_label,cost_note)],add='+')

    c.chat=ScrolledText(chat_page,wrap='word',height=12,bg='white',fg=INK,relief='flat',font=('Segoe UI',10),padx=12,pady=12,state='disabled')
    chat_page.columnconfigure(0,weight=1);chat_page.rowconfigure(0,weight=1)
    c.chat.grid(row=0,column=0,sticky='nsew')
    c.chat.tag_configure('user',foreground=BLUE,font=('Segoe UI',10,'bold'),spacing1=10,spacing3=5)
    c.chat.tag_configure('ai',foreground=INK,spacing1=8,spacing3=12)
    c.chat.tag_configure('tool',foreground=MUTED,font=('Consolas',9),spacing1=5,spacing3=7)
    c.chat.configure(state='normal');c.chat.insert('end','Trợ lý AI\n','user');c.chat.insert('end','Nhập mục tiêu bên dưới hoặc chọn tác vụ gợi ý. Kết quả kiểm tra sẽ xuất hiện tại đây.\n','ai');c.chat.configure(state='disabled')
    prompt_label=ttk.Label(chat_page,text='Nội dung gửi AI · không nhập mật khẩu hoặc API key',foreground=MUTED,background='white',wraplength=750);prompt_label.grid(row=1,column=0,sticky='w',pady=(10,4))
    c.prompt=ScrolledText(chat_page,height=4,wrap='word',bg='#F8FAFC',fg=INK,relief='solid',bd=1,font=('Segoe UI',10),padx=10,pady=8)
    c.prompt.grid(row=2,column=0,sticky='ew');c.prompt.bind('<Control-Return>',lambda event:(c.send(),'break')[1])
    suggestions=ttk.Frame(chat_page,style='AI.Card.TFrame');suggestions.grid(row=3,column=0,sticky='ew',pady=8)
    suggestion_buttons=[]
    for label,text in [('Kiểm tra thiết bị','Kiểm tra các thiết bị đã khai báo, tổng hợp cảnh báo và nêu bước xử lý.'),('Camera','Kiểm tra camera đã khai báo và tóm tắt kết quả kết nối.'),('Tổng quan','Tổng hợp cảnh báo và sự cố gần đây, ưu tiên mục cần xử lý.')]:
        suggestion_buttons.append(ttk.Button(suggestions,text=label,style='AI.TButton',command=lambda value=text:c.template(value)))
    FlowRow(suggestions,suggestion_buttons)
    actions=ttk.Frame(chat_page,style='AI.Card.TFrame');actions.grid(row=4,column=0,sticky='ew',pady=(0,5))
    context_button=ttk.Button(actions,text='Lấy dữ liệu trang',style='AI.TButton',command=c.context)
    image_button=ttk.Button(actions,text='Chọn ảnh',style='AI.TButton',command=c.choose_image)
    c.send_button=ttk.Button(actions,text='Gửi yêu cầu',style='AI.Primary.TButton',command=c.send)
    stop_button=ttk.Button(actions,text='Dừng',style='AI.TButton',command=c.cancel)
    more_button=ttk.Menubutton(actions,text='Khác',style='AI.TButton')
    more_menu=tk.Menu(more_button,tearoff=False)
    def quick_ping():
        host=simpledialog.askstring('Ping IP','IP / hostname cần kiểm tra:',parent=w)
        if host:c.host.set(host);c.ping()
    more_menu.add_command(label='Ping IP',command=quick_ping)
    more_menu.add_command(label='Kiểm tra camera',command=c.cameras)
    more_menu.add_command(label='Xóa hội thoại',command=c.clear)
    more_menu.add_separator()
    for label,text in [('Kiểm tra thiết bị','Kiểm tra các thiết bị đã khai báo, tổng hợp cảnh báo và nêu bước xử lý.'),('Tổng quan','Tổng hợp cảnh báo và sự cố gần đây.')]:
        more_menu.add_command(label=label,command=lambda value=text:c.template(value))
    more_button.configure(menu=more_menu)
    # Primary actions stay first; optional commands are also accessible via Khác.
    FlowRow(actions,[c.send_button,stop_button,context_button,image_button,more_button])
    quick=ttk.Frame(chat_page,style='AI.Card.TFrame');quick.grid(row=5,column=0,sticky='ew',pady=(6,0))
    c.host=tk.StringVar();host_entry=ttk.Entry(quick,textvariable=c.host,width=17)
    ping_button=ttk.Button(quick,text='Ping IP',command=c.ping)
    camera_button=ttk.Button(quick,text='Kiểm tra camera',command=c.cameras)
    clear_button=ttk.Button(quick,text='Xóa hội thoại',command=c.clear)
    FlowRow(quick,[host_entry,ping_button,camera_button,clear_button])
    c.image_label=ttk.Label(chat_page,text='Chưa chọn ảnh',foreground=MUTED,background='white');c.image_label.grid(row=6,column=0,sticky='w',pady=(6,0))
    toolbar=ttk.Frame(history_page,style='AI.Card.TFrame');toolbar.pack(fill='x',pady=(0,10))
    ttk.Button(toolbar,text='Làm mới',style='AI.TButton',command=c.refresh_tasks).pack(side='left')
    ttk.Button(toolbar,text='Mở báo cáo',style='AI.TButton',command=c.open_report).pack(side='left',padx=8)
    c.task_list=ttk.Treeview(history_page,columns=('time','objective','state','steps'),show='headings',height=8)
    for name,label,width in [('time','Tạo lúc',145),('objective','Mục tiêu',350),('state','Trạng thái',150),('steps','Bước',55)]:
        c.task_list.heading(name,text=label);c.task_list.column(name,width=width,minwidth=45,stretch=name=='objective')
    table_frame=ttk.Frame(history_page);table_frame.pack(fill='both',expand=True)
    # Move the tree into a grid controlled container using an explicit geometry parent.
    c.task_list.grid(in_=table_frame,row=0,column=0,sticky='nsew')
    table_frame.rowconfigure(0,weight=1);table_frame.columnconfigure(0,weight=1)
    vertical=ttk.Scrollbar(table_frame,orient='vertical',command=c.task_list.yview)
    horizontal=ttk.Scrollbar(table_frame,orient='horizontal',command=c.task_list.xview)
    c.task_list.configure(yscrollcommand=vertical.set,xscrollcommand=horizontal.set)
    vertical.grid(row=0,column=1,sticky='ns');horizontal.grid(row=1,column=0,sticky='ew')
    history_note=ttk.Label(history_page,text='Báo cáo lưu trên máy; tác vụ đang chạy không tự tiếp tục sau khi thoát ứng dụng.',background='white',foreground=MUTED,wraplength=730)
    history_note.pack(anchor='w',pady=10)
    c.status=tk.StringVar(value='Sẵn sàng · API key lấy từ môi trường Windows')
    footer=ttk.Frame(shell,style='AI.TFrame');footer.pack(fill='x',pady=(12,0))
    c.progress=ttk.Progressbar(footer,mode='indeterminate',length=100);c.progress.pack(side='right',padx=(12,0))
    status_label=ttk.Label(footer,textvariable=c.status,style='AI.Muted.TLabel',wraplength=660)
    status_label.pack(side='left',fill='x',expand=True)
    footer.bind('<Configure>',lambda event:status_label.configure(wraplength=max(250,event.width-130)))
    def resize(event):
        if event.widget is not w:return
        width=event.width
        description.configure(wraplength=max(300,width-40))
        prompt_label.configure(wraplength=max(280,width-80))
        c.image_label.configure(wraplength=max(280,width-80),justify='left')
        history_note.configure(wraplength=max(280,width-80))
        c.key_label.configure(wraplength=max(280,width-80))
        if width<760:
            auto_check.grid(row=3,column=0,columnspan=2,sticky='w',padx=0,pady=(3,0))
        else:
            auto_check.grid(row=2,column=1,columnspan=1,sticky='w',padx=(12,0),pady=(5,0))
        if width<760 or event.height<720:
            quick.grid_remove();suggestions.grid_remove()
        else:
            quick.grid();suggestions.grid()
        c.chat.configure(height=6 if event.height<740 else 12)
    w.bind('<Configure>',resize,add='+')
    c.refresh_tasks()
