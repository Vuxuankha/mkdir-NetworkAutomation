import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading
import time
import ipaddress

from modules.network_scan import scan_network
from modules.ping_check import ping_multiple

from database.db import (
    init_database,
    create_device,
    get_all_devices,
    get_device,
    get_device_by_ip,
    search_devices,
    get_devices_by_status,
    update_device,
    delete_device,
    delete_device_by_ip,
    get_device_statistics,
    save_devices,
)
from modules.device_manager import (
    device_manager
)


class NetworkAutomationApp:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "Network Automation Tool"
        )

        self.root.geometry(
            "1400x800"
        )

        self.root.minsize(
            1100,
            650
        )

        # ==================================================
        # VARIABLES
        # ==================================================

        self.current_page = None

        self.activity_logs = []

        # --------------------------------------------------
        # NETWORK SCAN
        # --------------------------------------------------

        self.scan_running = False
        self.scan_stop_event = None
        self.scan_thread = None

        self.scan_total = 0
        self.scan_completed = 0
        self.scan_online = 0
        self.scan_offline = 0

        self.scan_start_time = None

        # IP đang chạy
        self.scan_active_ips = {}

        # Timer cập nhật thời gian
        self.scan_timer_job = None

        # --------------------------------------------------
        # SCAN RESULTS
        # --------------------------------------------------

        self.scan_results = []

        # --------------------------------------------------
        # PING MONITOR
        # --------------------------------------------------

        self.auto_ping_running = False
        self.auto_ping_job = None
        self.ping_running = False

        # --------------------------------------------------
        # DEVICE MANAGER
        # --------------------------------------------------

        self.device_search_var = None
        self.device_status_filter_var = None
        self.device_table = None

        # ==================================================
        # STYLE
        # ==================================================

        self.setup_style()

        # ==================================================
        # MAIN LAYOUT
        # ==================================================

        self.create_layout()

        # ==================================================
        # DEFAULT PAGE
        # ==================================================

        self.show_dashboard()

    # ======================================================
    # STYLE
    # ======================================================

    def setup_style(self):

        style = ttk.Style()

        try:

            style.theme_use(
                "clam"
            )

        except Exception:

            pass

        style.configure(
            "Treeview",
            rowheight=28,
            font=(
                "Segoe UI",
                10
            )
        )

        style.configure(
            "Treeview.Heading",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        )

        style.configure(
            "TButton",
            font=(
                "Segoe UI",
                10
            )
        )

    # ======================================================
    # LAYOUT
    # ======================================================

    def create_layout(self):

        self.sidebar = tk.Frame(
            self.root,
            bg="#111827",
            width=230
        )

        self.sidebar.pack(
            side="left",
            fill="y"
        )

        self.sidebar.pack_propagate(
            False
        )

        self.content = tk.Frame(
            self.root,
            bg="#F3F4F6"
        )

        self.content.pack(
            side="right",
            fill="both",
            expand=True
        )

        self.create_sidebar()

    # ======================================================
    # SIDEBAR
    # ======================================================

    def create_sidebar(self):

        title = tk.Label(
            self.sidebar,
            text="NETWORK\nAUTOMATION",
            bg="#111827",
            fg="white",
            font=(
                "Segoe UI",
                16,
                "bold"
            ),
            justify="left"
        )

        title.pack(
            padx=20,
            pady=(25, 30),
            anchor="w"
        )

        menu_items = [

            (
                "Dashboard",
                self.show_dashboard
            ),

            (
                "Network Scan",
                self.show_network_scan
            ),

            (
                "Ping Monitor",
                self.show_ping_monitor
            ),

            ("Device Manager", self.show_device_manager),

            (
                "IP / MAC Manager",
                self.show_placeholder
            ),

            (
                "Network Devices",
                self.show_placeholder
            ),

            (
                "Remote Service",
                self.show_placeholder
            ),

            (
                "Backup Config",
                self.show_placeholder
            ),

            (
                "Scheduler",
                self.show_placeholder
            ),

            (
                "Alerts",
                self.show_placeholder
            ),

            (
                "Reports",
                self.show_placeholder
            ),

            (
                "System Logs",
                self.show_placeholder
            ),

            (
                "Settings",
                self.show_placeholder
            )
        ]

        for text, command in menu_items:

            button = tk.Button(
                self.sidebar,
                text=text,
                command=command,
                bg="#111827",
                fg="#D1D5DB",
                activebackground="#1F2937",
                activeforeground="white",
                relief="flat",
                bd=0,
                anchor="w",
                padx=20,
                pady=9,
                font=(
                    "Segoe UI",
                    10
                ),
                cursor="hand2"
            )

            button.pack(
                fill="x"
            )

    # ======================================================
    # COMMON
    # ======================================================

    def clear_content(self):

        if self.auto_ping_running:

            self.stop_auto_ping(
                silent=True
            )

        if self.scan_running:

            self.stop_scan()

        for widget in self.content.winfo_children():

            widget.destroy()

    def set_page_title(
        self,
        title,
        subtitle=""
    ):

        header = tk.Frame(
            self.content,
            bg="#F3F4F6"
        )

        header.pack(
            fill="x",
            padx=25,
            pady=(20, 10)
        )

        tk.Label(
            header,
            text=title,
            bg="#F3F4F6",
            fg="#111827",
            font=(
                "Segoe UI",
                22,
                "bold"
            )
        ).pack(
            anchor="w"
        )

        if subtitle:

            tk.Label(
                header,
                text=subtitle,
                bg="#F3F4F6",
                fg="#6B7280",
                font=(
                    "Segoe UI",
                    10
                )
            ).pack(
                anchor="w",
                pady=(3, 0)
            )

    def add_activity(self, message):

        time_text = datetime.now().strftime(
            "%H:%M:%S"
        )

        self.activity_logs.append(
            f"[{time_text}] {message}"
        )

    # ======================================================
    # DASHBOARD
    # ======================================================

    def show_dashboard(self):

        self.current_page = "Dashboard"

        self.clear_content()

        self.set_page_title(
            "Network Automation Tool",
            "IT Infrastructure Management System"
        )

        cards_frame = tk.Frame(
            self.content,
            bg="#F3F4F6"
        )

        cards_frame.pack(
            fill="x",
            padx=25,
            pady=20
        )

        try:

            stats = device_manager.statistics()

            total_devices = stats.get(
                "total",
                0
            )

            online_devices = stats.get(
                "online",
                0
            )

            offline_devices = stats.get(
                "offline",
                0
            )

        except Exception:

            total_devices = 0
            online_devices = 0
            offline_devices = 0

        cards = [

            (
                "Total Devices",
                str(total_devices)
            ),

            (
                "Online",
                str(online_devices)
            ),

            (
                "Offline",
                str(offline_devices)
            ),

            (
                "Alerts",
                "0"
            )
        ]

        for title, value in cards:

            card = tk.Frame(
                cards_frame,
                bg="white",
                bd=1,
                relief="solid"
            )

            card.pack(
                side="left",
                fill="both",
                expand=True,
                padx=6
            )

            tk.Label(
                card,
                text=title,
                bg="white",
                fg="#6B7280",
                font=(
                    "Segoe UI",
                    10
                )
            ).pack(
                anchor="w",
                padx=20,
                pady=(20, 5)
            )

            tk.Label(
                card,
                text=value,
                bg="white",
                fg="#111827",
                font=(
                    "Segoe UI",
                    24,
                    "bold"
                )
            ).pack(
                anchor="w",
                padx=20,
                pady=(0, 20)
            )

        activity = tk.Frame(
            self.content,
            bg="white",
            bd=1,
            relief="solid"
        )

        activity.pack(
            fill="both",
            expand=True,
            padx=31,
            pady=10
        )

        tk.Label(
            activity,
            text="Recent Activity",
            bg="white",
            fg="#111827",
            font=(
                "Segoe UI",
                14,
                "bold"
            )
        ).pack(
            anchor="w",
            padx=20,
            pady=15
        )

        log_text = tk.Text(
            activity,
            bg="white",
            fg="#374151",
            relief="flat",
            font=(
                "Consolas",
                10
            )
        )

        log_text.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 20)
        )

        for log in self.activity_logs[-100:]:

            log_text.insert(
                tk.END,
                log + "\n"
            )

        log_text.config(
            state="disabled"
        )

    # ======================================================
    # NETWORK SCAN PAGE
    # ======================================================

    def show_network_scan(self):

        self.current_page = "Network Scan"

        self.clear_content()

        self.set_page_title(
            "Network Scan",
            "Realtime network device scanner"
        )

        control = tk.Frame(
            self.content,
            bg="white",
            bd=1,
            relief="solid"
        )

        control.pack(
            fill="x",
            padx=25,
            pady=10
        )

        tk.Label(
            control,
            text="Network:",
            bg="white",
            fg="#374151",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        ).pack(
            side="left",
            padx=(20, 8),
            pady=18
        )

        self.network_entry = tk.Entry(
            control,
            width=25,
            font=(
                "Segoe UI",
                10
            )
        )

        self.network_entry.insert(
            0,
            "192.168.1.0/24"
        )

        self.network_entry.pack(
            side="left",
            pady=18
        )

        self.scan_button = tk.Button(
            control,
            text="Scan Network",
            command=self.start_scan,
            bg="#2563EB",
            fg="white",
            activebackground="#1D4ED8",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=18,
            pady=8,
            cursor="hand2",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        )

        self.scan_button.pack(
            side="left",
            padx=(15, 8)
        )

        self.stop_scan_button = tk.Button(
            control,
            text="Stop Scan",
            command=self.stop_scan,
            bg="#DC2626",
            fg="white",
            activebackground="#B91C1C",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=18,
            pady=8,
            cursor="hand2",
            font=(
                "Segoe UI",
                10,
                "bold"
            ),
            state="disabled"
        )

        self.stop_scan_button.pack(
            side="left",
            padx=8
        )

        self.scan_status_label = tk.Label(
            control,
            text="Ready",
            bg="white",
            fg="#6B7280",
            font=(
                "Segoe UI",
                10
            )
        )

        self.scan_status_label.pack(
            side="left",
            padx=15
        )

        progress_frame = tk.Frame(
            self.content,
            bg="white",
            bd=1,
            relief="solid"
        )

        progress_frame.pack(
            fill="x",
            padx=25,
            pady=(0, 10)
        )

        tk.Label(
            progress_frame,
            text="Đang kiểm tra:",
            bg="white",
            fg="#6B7280",
            font=(
                "Segoe UI",
                10
            )
        ).pack(
            side="left",
            padx=(20, 5),
            pady=15
        )

        self.scan_current_ip_label = tk.Label(
            progress_frame,
            text="-",
            bg="white",
            fg="#2563EB",
            font=(
                "Consolas",
                11,
                "bold"
            )
        )

        self.scan_current_ip_label.pack(
            side="left",
            padx=5
        )

        self.scan_progress_label = tk.Label(
            progress_frame,
            text="0 / 0",
            bg="white",
            fg="#111827",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        )

        self.scan_progress_label.pack(
            side="left",
            padx=(30, 5)
        )

        self.scan_percent_label = tk.Label(
            progress_frame,
            text="0%",
            bg="white",
            fg="#16A34A",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        )

        self.scan_percent_label.pack(
            side="left",
            padx=5
        )

        self.scan_active_label = tk.Label(
            progress_frame,
            text="Running: 0",
            bg="white",
            fg="#7C3AED",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        )

        self.scan_active_label.pack(
            side="left",
            padx=20
        )

        self.scan_ip_timer_label = tk.Label(
            progress_frame,
            text="IP Time: 0.00 s",
            bg="white",
            fg="#D97706",
            font=(
                "Consolas",
                10,
                "bold"
            )
        )

        self.scan_ip_timer_label.pack(
            side="left",
            padx=20
        )

        self.scan_total_timer_label = tk.Label(
            progress_frame,
            text="Total: 0.00 s",
            bg="white",
            fg="#374151",
            font=(
                "Consolas",
                10
            )
        )

        self.scan_total_timer_label.pack(
            side="left",
            padx=10
        )

        self.scan_progress = ttk.Progressbar(
            progress_frame,
            orient="horizontal",
            mode="determinate"
        )

        self.scan_progress.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(20, 20),
            pady=15
        )

        filter_frame = tk.Frame(
            self.content,
            bg="white",
            bd=1,
            relief="solid"
        )

        filter_frame.pack(
            fill="x",
            padx=25,
            pady=(0, 10)
        )

        tk.Label(
            filter_frame,
            text="Search:",
            bg="white",
            fg="#374151",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        ).pack(
            side="left",
            padx=(20, 8),
            pady=12
        )

        self.scan_search_var = tk.StringVar()

        self.scan_search_entry = tk.Entry(
            filter_frame,
            textvariable=self.scan_search_var,
            width=28,
            font=(
                "Segoe UI",
                10
            )
        )

        self.scan_search_entry.pack(
            side="left",
            pady=12
        )

        self.scan_search_entry.bind(
            "<KeyRelease>",
            lambda event: self.apply_scan_filters()
        )

        tk.Label(
            filter_frame,
            text="Status:",
            bg="white",
            fg="#374151",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        ).pack(
            side="left",
            padx=(25, 8)
        )

        self.scan_status_filter_var = tk.StringVar(
            value="All"
        )

        self.scan_status_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.scan_status_filter_var,
            values=(
                "All",
                "Online",
                "Offline"
            ),
            width=12,
            state="readonly"
        )

        self.scan_status_combo.pack(
            side="left"
        )

        self.scan_status_combo.bind(
            "<<ComboboxSelected>>",
            lambda event: self.apply_scan_filters()
        )

        tk.Label(
            filter_frame,
            text="Sort:",
            bg="white",
            fg="#374151",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        ).pack(
            side="left",
            padx=(25, 8)
        )

        self.scan_sort_var = tk.StringVar(
            value="Online first"
        )

        self.scan_sort_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.scan_sort_var,
            values=(
                "Online first",
                "Offline first",
                "IP Address",
                "Duration",
                "Time"
            ),
            width=18,
            state="readonly"
        )

        self.scan_sort_combo.pack(
            side="left"
        )

        self.scan_sort_combo.bind(
            "<<ComboboxSelected>>",
            lambda event: self.apply_scan_filters()
        )

        self.scan_summary_label = tk.Label(
            filter_frame,
            text="Total: 0 | Online: 0 | Offline: 0 | Showing: 0",
            bg="white",
            fg="#374151",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        )

        self.scan_summary_label.pack(
            side="right",
            padx=20
        )

        result_frame = tk.Frame(
            self.content,
            bg="white",
            bd=1,
            relief="solid"
        )

        result_frame.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=(0, 20)
        )

        columns = (
            "time",
            "ip",
            "hostname",
            "mac",
            "status",
            "duration"
        )

        self.scan_table = ttk.Treeview(
            result_frame,
            columns=columns,
            show="headings"
        )

        self.scan_table.heading(
            "time",
            text="Time"
        )

        self.scan_table.heading(
            "ip",
            text="IP Address"
        )

        self.scan_table.heading(
            "hostname",
            text="Hostname"
        )

        self.scan_table.heading(
            "mac",
            text="MAC Address"
        )

        self.scan_table.heading(
            "status",
            text="Status"
        )

        self.scan_table.heading(
            "duration",
            text="Duration"
        )

        self.scan_table.column(
            "time",
            width=90,
            anchor="center"
        )

        self.scan_table.column(
            "ip",
            width=150
        )

        self.scan_table.column(
            "hostname",
            width=230
        )

        self.scan_table.column(
            "mac",
            width=180
        )

        self.scan_table.column(
            "status",
            width=100,
            anchor="center"
        )

        self.scan_table.column(
            "duration",
            width=110,
            anchor="center"
        )

        scrollbar_y = ttk.Scrollbar(
            result_frame,
            orient="vertical",
            command=self.scan_table.yview
        )

        scrollbar_x = ttk.Scrollbar(
            result_frame,
            orient="horizontal",
            command=self.scan_table.xview
        )

        self.scan_table.configure(
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )

        self.scan_table.pack(
            side="top",
            fill="both",
            expand=True,
            padx=(15, 0),
            pady=(15, 0)
        )

        scrollbar_y.pack(
            side="right",
            fill="y",
            padx=(0, 15),
            pady=(15, 0)
        )

        scrollbar_x.pack(
            side="bottom",
            fill="x",
            padx=(15, 15),
            pady=(0, 15)
        )

        self.scan_table.tag_configure(
            "online",
            foreground="#16A34A"
        )

        self.scan_table.tag_configure(
            "offline",
            foreground="#DC2626"
        )

        self.scan_table.tag_configure(
            "running",
            foreground="#2563EB"
        )

    # ======================================================
    # APPLY SEARCH / FILTER / SORT
    # ======================================================

    def apply_scan_filters(self):

        if not hasattr(
            self,
            "scan_table"
        ):

            return

        try:

            if not self.scan_table.winfo_exists():

                return

        except tk.TclError:

            return

        search_text = ""

        if hasattr(
            self,
            "scan_search_var"
        ):

            search_text = (
                self.scan_search_var
                .get()
                .strip()
                .lower()
            )

        status_filter = "All"

        if hasattr(
            self,
            "scan_status_filter_var"
        ):

            status_filter = (
                self.scan_status_filter_var
                .get()
            )

        sort_type = "Online first"

        if hasattr(
            self,
            "scan_sort_var"
        ):

            sort_type = (
                self.scan_sort_var
                .get()
            )

        filtered_results = []

        for result in self.scan_results:

            ip = str(
                result.get(
                    "ip",
                    ""
                )
            )

            hostname = str(
                result.get(
                    "hostname",
                    ""
                )
            )

            mac = str(
                result.get(
                    "mac",
                    ""
                )
            )

            status = str(
                result.get(
                    "status",
                    ""
                )
            )

            if search_text:

                searchable = (
                    f"{ip} "
                    f"{hostname} "
                    f"{mac}"
                ).lower()

                if search_text not in searchable:

                    continue

            if (
                status_filter != "All"
                and status != status_filter
            ):

                continue

            filtered_results.append(
                result
            )

        def ip_sort_key(result):

            try:

                return ipaddress.ip_address(
                    result.get(
                        "ip",
                        "0.0.0.0"
                    )
                )

            except Exception:

                return ipaddress.ip_address(
                    "0.0.0.0"
                )

        def duration_sort_key(result):

            try:

                return float(
                    result.get(
                        "duration",
                        999999
                    )
                )

            except Exception:

                return 999999

        if sort_type == "Online first":

            filtered_results.sort(
                key=lambda result: (
                    result.get(
                        "status",
                        ""
                    ) != "Online",
                    ip_sort_key(result)
                )
            )

        elif sort_type == "Offline first":

            filtered_results.sort(
                key=lambda result: (
                    result.get(
                        "status",
                        ""
                    ) != "Offline",
                    ip_sort_key(result)
                )
            )

        elif sort_type == "IP Address":

            filtered_results.sort(
                key=ip_sort_key
            )

        elif sort_type == "Duration":

            filtered_results.sort(
                key=lambda result: (
                    duration_sort_key(result),
                    ip_sort_key(result)
                )
            )

        elif sort_type == "Time":

            filtered_results.sort(
                key=lambda result: (
                    result.get(
                        "time",
                        ""
                    ),
                    ip_sort_key(result)
                )
            )

        for item in self.scan_table.get_children():

            self.scan_table.delete(
                item
            )

        for result in filtered_results:

            status = result.get(
                "status",
                ""
            )

            if status == "Online":

                tag = "online"

            elif status == "Offline":

                tag = "offline"

            else:

                tag = "running"

            duration = result.get(
                "duration",
                0
            )

            try:

                duration_text = (
                    f"{float(duration):.2f} s"
                )

            except Exception:

                duration_text = "-"

            self.scan_table.insert(
                "",
                "end",
                values=(
                    result.get(
                        "time",
                        ""
                    ),
                    result.get(
                        "ip",
                        ""
                    ),
                    result.get(
                        "hostname",
                        ""
                    ),
                    result.get(
                        "mac",
                        ""
                    ),
                    status,
                    duration_text
                ),
                tags=(tag,)
            )

        total = len(
            self.scan_results
        )

        online = sum(
            1
            for result in self.scan_results
            if result.get("status") == "Online"
        )

        offline = sum(
            1
            for result in self.scan_results
            if result.get("status") == "Offline"
        )

        showing = len(
            filtered_results
        )

        self.scan_summary_label.config(
            text=(
                f"Total: {total} | "
                f"Online: {online} | "
                f"Offline: {offline} | "
                f"Showing: {showing}"
            )
        )

    # ======================================================
    # START SCAN
    # ======================================================

    def start_scan(self):

        if self.scan_running:

            return

        network = (
            self.network_entry
            .get()
            .strip()
        )

        if not network:

            self.scan_status_label.config(
                text="Please enter network."
            )

            return

        for item in self.scan_table.get_children():

            self.scan_table.delete(
                item
            )

        self.scan_results = []

        self.scan_search_var.set(
            ""
        )

        self.scan_status_filter_var.set(
            "All"
        )

        self.scan_sort_var.set(
            "Online first"
        )

        self.scan_total = 0
        self.scan_completed = 0
        self.scan_online = 0
        self.scan_offline = 0

        self.scan_active_ips = {}

        self.scan_start_time = (
            time.perf_counter()
        )

        self.scan_progress["value"] = 0

        self.scan_progress["maximum"] = 1

        self.scan_current_ip_label.config(
            text="-"
        )

        self.scan_progress_label.config(
            text="0 / 0"
        )

        self.scan_percent_label.config(
            text="0%"
        )

        self.scan_active_label.config(
            text="Running: 0"
        )

        self.scan_ip_timer_label.config(
            text="IP Time: 0.00 s"
        )

        self.scan_total_timer_label.config(
            text="Total: 0.00 s"
        )

        self.scan_summary_label.config(
            text=(
                "Total: 0 | "
                "Online: 0 | "
                "Offline: 0 | "
                "Showing: 0"
            )
        )

        self.scan_running = True

        self.scan_stop_event = (
            threading.Event()
        )

        self.scan_button.config(
            state="disabled"
        )

        self.stop_scan_button.config(
            state="normal"
        )

        self.scan_status_label.config(
            text=f"Preparing scan: {network}"
        )

        self.add_activity(
            f"Started network scan: {network}"
        )

        self.update_scan_timer()

        self.scan_thread = threading.Thread(
            target=self.scan_worker,
            args=(
                network,
                self.scan_stop_event
            ),
            daemon=True
        )

        self.scan_thread.start()

    # ======================================================
    # SCAN WORKER
    # ======================================================

    def scan_worker(
        self,
        network,
        stop_event
    ):

        try:

            results = scan_network(
                network,
                max_workers=50,
                timeout=1,
                stop_event=stop_event,
                callback=self.scan_callback
            )

            stopped = (
                stop_event.is_set()
            )

            self.root.after(
                0,
                self.scan_finished,
                stopped,
                results
            )

        except Exception as error:

            self.root.after(
                0,
                self.scan_error,
                str(error)
            )

    # ======================================================
    # SCAN CALLBACK
    # ======================================================

    def scan_callback(
        self,
        event
    ):

        event_type = event.get(
            "event"
        )

        if event_type == "total":

            total = event.get(
                "total",
                0
            )

            self.root.after(
                0,
                self.scan_set_total,
                total
            )

        elif event_type == "started":

            ip = event.get(
                "ip",
                ""
            )

            self.root.after(
                0,
                self.scan_host_started,
                ip
            )

        elif event_type == "completed":

            result = event.get(
                "result"
            )

            if result:

                self.root.after(
                    0,
                    self.scan_host_completed,
                    result
                )

    # ======================================================
    # SET TOTAL
    # ======================================================

    def scan_set_total(
        self,
        total
    ):

        if not self.scan_running:

            return

        self.scan_total = total

        self.scan_progress["maximum"] = max(
            total,
            1
        )

        self.scan_progress_label.config(
            text=f"0 / {total}"
        )

        self.scan_status_label.config(
            text=f"Scanning {total} IP addresses..."
        )

    # ======================================================
    # HOST STARTED
    # ======================================================

    def scan_host_started(
        self,
        ip
    ):

        if not self.scan_running:

            return

        self.scan_active_ips[ip] = (
            time.perf_counter()
        )

        self.scan_current_ip_label.config(
            text=ip
        )

        self.scan_active_label.config(
            text=(
                f"Running: "
                f"{len(self.scan_active_ips)}"
            )
        )

        self.scan_status_label.config(
            text=(
                f"Checking {ip}..."
            )
        )

    # ======================================================
    # HOST COMPLETED
    # ======================================================

    def scan_host_completed(
        self,
        result
    ):

        if not hasattr(
            self,
            "scan_table"
        ):

            return

        try:

            if not self.scan_table.winfo_exists():

                return

        except tk.TclError:

            return

        ip = result.get(
            "ip",
            ""
        )

        if ip in self.scan_active_ips:

            del self.scan_active_ips[ip]

        self.scan_completed += 1

        status = result.get(
            "status",
            ""
        )

        if status == "Online":

            self.scan_online += 1

        else:

            self.scan_offline += 1

        self.scan_results.append(
            result
        )

        try:

            save_devices(
                [result]
            )

        except Exception as error:

            self.add_activity(
                f"Database error {ip}: {error}"
            )

        self.apply_scan_filters()

        children = (
            self.scan_table.get_children()
        )

        if children:

            self.scan_table.see(
                children[-1]
            )

        self.update_scan_progress()

    # ======================================================
    # UPDATE PROGRESS
    # ======================================================

    def update_scan_progress(self):

        total = self.scan_total

        completed = self.scan_completed

        if total <= 0:

            percent = 0

        else:

            percent = (
                completed
                / total
                * 100
            )

        self.scan_progress["value"] = (
            completed
        )

        self.scan_progress_label.config(
            text=(
                f"{completed} / {total}"
            )
        )

        self.scan_percent_label.config(
            text=(
                f"{percent:.1f}%"
            )
        )

        self.scan_active_label.config(
            text=(
                f"Running: "
                f"{len(self.scan_active_ips)}"
            )
        )

        self.scan_status_label.config(
            text=(
                f"Scanning... "
                f"Online: {self.scan_online} | "
                f"Offline: {self.scan_offline}"
            )
        )

    # ======================================================
    # LIVE TIMER
    # ======================================================

    def update_scan_timer(self):

        if not self.scan_running:

            return

        if self.scan_start_time is not None:

            total_elapsed = (
                time.perf_counter()
                - self.scan_start_time
            )

            self.scan_total_timer_label.config(
                text=(
                    f"Total: "
                    f"{total_elapsed:.2f} s"
                )
            )

        current_ip = (
            self.scan_current_ip_label.cget(
                "text"
            )
        )

        if (
            current_ip
            and current_ip in self.scan_active_ips
        ):

            host_start = (
                self.scan_active_ips[
                    current_ip
                ]
            )

            host_elapsed = (
                time.perf_counter()
                - host_start
            )

            self.scan_ip_timer_label.config(
                text=(
                    f"IP Time: "
                    f"{host_elapsed:.2f} s"
                )
            )

        else:

            self.scan_ip_timer_label.config(
                text="IP Time: 0.00 s"
            )

        self.scan_timer_job = (
            self.root.after(
                100,
                self.update_scan_timer
            )
        )

    # ======================================================
    # FINISHED
    # ======================================================

    def scan_finished(
        self,
        stopped=False,
        results=None
    ):

        if not self.scan_running:

            return

        if results is not None:

            self.scan_results = results

        self.scan_running = False

        if self.scan_timer_job is not None:

            try:

                self.root.after_cancel(
                    self.scan_timer_job
                )

            except Exception:

                pass

            self.scan_timer_job = None

        self.scan_button.config(
            state="normal"
        )

        self.stop_scan_button.config(
            state="disabled"
        )

        total_time = 0

        if self.scan_start_time is not None:

            total_time = (
                time.perf_counter()
                - self.scan_start_time
            )

        self.scan_total_timer_label.config(
            text=(
                f"Total: "
                f"{total_time:.2f} s"
            )
        )

        self.scan_completed = len(
            self.scan_results
        )

        self.scan_online = sum(
            1
            for result in self.scan_results
            if result.get("status") == "Online"
        )

        self.scan_offline = sum(
            1
            for result in self.scan_results
            if result.get("status") == "Offline"
        )

        self.apply_scan_filters()

        if stopped:

            self.scan_status_label.config(
                text=(
                    f"Stopped | "
                    f"Scanned: "
                    f"{self.scan_completed} | "
                    f"Online: "
                    f"{self.scan_online} | "
                    f"Offline: "
                    f"{self.scan_offline}"
                )
            )

            self.add_activity(
                "Network scan stopped."
            )

        else:

            self.scan_status_label.config(
                text=(
                    f"Completed | "
                    f"Total: "
                    f"{self.scan_completed} | "
                    f"Online: "
                    f"{self.scan_online} | "
                    f"Offline: "
                    f"{self.scan_offline} | "
                    f"Time: "
                    f"{total_time:.2f}s"
                )
            )

            self.add_activity(
                "Network scan completed. "
                f"Total: {self.scan_completed}, "
                f"Online: {self.scan_online}, "
                f"Offline: {self.scan_offline}"
            )

        self.scan_current_ip_label.config(
            text="Finished"
        )

        self.scan_active_label.config(
            text="Running: 0"
        )

        self.scan_ip_timer_label.config(
            text="IP Time: 0.00 s"
        )

        self.scan_stop_event = None

        self.scan_thread = None

        self.scan_active_ips = {}

    # ======================================================
    # STOP SCAN
    # ======================================================

    def stop_scan(self):

        if not self.scan_running:

            return

        if self.scan_stop_event is not None:

            self.scan_stop_event.set()

        self.scan_status_label.config(
            text="Stopping scan..."
        )

        self.stop_scan_button.config(
            state="disabled"
        )

        self.add_activity(
            "Stopping network scan..."
        )

    # ======================================================
    # SCAN ERROR
    # ======================================================

    def scan_error(
        self,
        error
    ):

        self.scan_running = False

        if self.scan_timer_job is not None:

            try:

                self.root.after_cancel(
                    self.scan_timer_job
                )

            except Exception:

                pass

            self.scan_timer_job = None

        self.scan_stop_event = None

        self.scan_thread = None

        self.scan_button.config(
            state="normal"
        )

        self.stop_scan_button.config(
            state="disabled"
        )

        self.scan_status_label.config(
            text=f"Error: {error}"
        )

        self.add_activity(
            f"Network scan error: {error}"
        )

    # ======================================================
    # DEVICE MANAGER
    # ======================================================

    def show_device_manager(self):

        self.current_page = "Device Manager"

        self.clear_content()

        self.set_page_title(
            "Device Manager",
            "Manage network devices stored in database"
        )

        toolbar = tk.Frame(
            self.content,
            bg="white",
            bd=1,
            relief="solid"
        )

        toolbar.pack(
            fill="x",
            padx=25,
            pady=10
        )

        tk.Label(
            toolbar,
            text="Search:",
            bg="white",
            fg="#374151",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        ).pack(
            side="left",
            padx=(20, 8),
            pady=15
        )

        self.device_search_var = tk.StringVar()

        self.device_search_entry = tk.Entry(
            toolbar,
            textvariable=self.device_search_var,
            width=28,
            font=(
                "Segoe UI",
                10
            )
        )

        self.device_search_entry.pack(
            side="left",
            pady=15
        )

        self.device_search_entry.bind(
            "<KeyRelease>",
            lambda event: self.apply_device_filters()
        )

        tk.Label(
            toolbar,
            text="Status:",
            bg="white",
            fg="#374151",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        ).pack(
            side="left",
            padx=(25, 8)
        )

        self.device_status_filter_var = tk.StringVar(
            value="All"
        )

        self.device_status_combo = ttk.Combobox(
            toolbar,
            textvariable=self.device_status_filter_var,
            values=(
                "All",
                "Online",
                "Offline"
            ),
            width=12,
            state="readonly"
        )

        self.device_status_combo.pack(
            side="left"
        )

        self.device_status_combo.bind(
            "<<ComboboxSelected>>",
            lambda event: self.apply_device_filters()
        )

        refresh_button = tk.Button(
            toolbar,
            text="Refresh",
            command=self.refresh_device_manager,
            bg="#2563EB",
            fg="white",
            activebackground="#1D4ED8",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=15,
            pady=7,
            cursor="hand2",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        )

        refresh_button.pack(
            side="left",
            padx=15
        )

        add_button = tk.Button(
            toolbar,
            text="Add Device",
            command=self.add_device_dialog,
            bg="#16A34A",
            fg="white",
            activebackground="#15803D",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=15,
            pady=7,
            cursor="hand2",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        )

        add_button.pack(
            side="right",
            padx=(5, 20)
        )

        summary_frame = tk.Frame(
            self.content,
            bg="white",
            bd=1,
            relief="solid"
        )

        summary_frame.pack(
            fill="x",
            padx=25,
            pady=(0, 10)
        )

        self.device_summary_label = tk.Label(
            summary_frame,
            text="Total: 0 | Online: 0 | Offline: 0 | Showing: 0",
            bg="white",
            fg="#374151",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        )

        self.device_summary_label.pack(
            anchor="w",
            padx=20,
            pady=12
        )

        result_frame = tk.Frame(
            self.content,
            bg="white",
            bd=1,
            relief="solid"
        )

        result_frame.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=(0, 10)
        )

        columns = (
            "id",
            "ip",
            "hostname",
            "mac",
            "status",
            "duration",
            "first_seen",
            "last_seen"
        )

        self.device_table = ttk.Treeview(
            result_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        self.device_table.heading(
            "id",
            text="ID"
        )

        self.device_table.heading(
            "ip",
            text="IP Address"
        )

        self.device_table.heading(
            "hostname",
            text="Hostname"
        )

        self.device_table.heading(
            "mac",
            text="MAC Address"
        )

        self.device_table.heading(
            "status",
            text="Status"
        )

        self.device_table.heading(
            "duration",
            text="Duration"
        )

        self.device_table.heading(
            "first_seen",
            text="First Seen"
        )

        self.device_table.heading(
            "last_seen",
            text="Last Seen"
        )

        self.device_table.column(
            "id",
            width=60,
            anchor="center"
        )

        self.device_table.column(
            "ip",
            width=140
        )

        self.device_table.column(
            "hostname",
            width=200
        )

        self.device_table.column(
            "mac",
            width=180
        )

        self.device_table.column(
            "status",
            width=100,
            anchor="center"
        )

        self.device_table.column(
            "duration",
            width=100,
            anchor="center"
        )

        self.device_table.column(
            "first_seen",
            width=160
        )

        self.device_table.column(
            "last_seen",
            width=160
        )

        scrollbar_y = ttk.Scrollbar(
            result_frame,
            orient="vertical",
            command=self.device_table.yview
        )

        scrollbar_x = ttk.Scrollbar(
            result_frame,
            orient="horizontal",
            command=self.device_table.xview
        )

        self.device_table.configure(
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )

        self.device_table.pack(
            side="top",
            fill="both",
            expand=True,
            padx=(15, 0),
            pady=(15, 0)
        )

        scrollbar_y.pack(
            side="right",
            fill="y",
            padx=(0, 15),
            pady=(15, 0)
        )

        scrollbar_x.pack(
            side="bottom",
            fill="x",
            padx=(15, 15),
            pady=(0, 15)
        )

        self.device_table.tag_configure(
            "online",
            foreground="#16A34A"
        )

        self.device_table.tag_configure(
            "offline",
            foreground="#DC2626"
        )

        self.device_table.tag_configure(
            "unknown",
            foreground="#6B7280"
        )

        self.device_table.bind(
            "<Double-1>",
            self.on_device_double_click
        )

        button_frame = tk.Frame(
            self.content,
            bg="#F3F4F6"
        )

        button_frame.pack(
            fill="x",
            padx=25,
            pady=(0, 20)
        )

        edit_button = tk.Button(
            button_frame,
            text="Edit Device",
            command=self.edit_selected_device,
            bg="#2563EB",
            fg="white",
            activebackground="#1D4ED8",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=18,
            pady=8,
            cursor="hand2",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        )

        edit_button.pack(
            side="left"
        )

        delete_button = tk.Button(
            button_frame,
            text="Delete Device",
            command=self.delete_selected_device,
            bg="#DC2626",
            fg="white",
            activebackground="#B91C1C",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=18,
            pady=8,
            cursor="hand2",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        )

        delete_button.pack(
            side="left",
            padx=10
        )

        self.refresh_device_manager()

    # ======================================================
    # DEVICE FILTER
    # ======================================================

    def apply_device_filters(self):

        if self.device_table is None:

            return

        try:

            if not self.device_table.winfo_exists():

                return

        except tk.TclError:

            return

        keyword = ""

        if self.device_search_var is not None:

            keyword = (
                self.device_search_var
                .get()
                .strip()
            )

        status = "All"

        if self.device_status_filter_var is not None:

            status = (
                self.device_status_filter_var
                .get()
            )

        # IMPORTANT:
        # Network Scan saves devices through save_devices().
        # Device Manager must read from the same database source.
        # Do not depend on device_manager.search_and_filter() here,
        # because it can become out of sync with the database layer.

        try:
            devices = get_all_devices()

            if devices is None:
                devices = []

            # Normalize database rows to dictionaries when possible.
            normalized_devices = []

            for device in devices:
                if isinstance(device, dict):
                    normalized_devices.append(device)
                    continue

                # Support sqlite3.Row / mapping-like objects.
                try:
                    normalized_devices.append(dict(device))
                    continue
                except Exception:
                    pass

                # Support tuple/list rows as a last resort.
                try:
                    normalized_devices.append({
                        "id": device[0],
                        "ip": device[1],
                        "hostname": device[2],
                        "mac": device[3],
                        "status": device[4],
                        "duration": device[5],
                        "first_seen": device[6],
                        "last_seen": device[7],
                    })
                except Exception:
                    continue

            devices = normalized_devices

            # Apply search/status filtering in the UI layer.
            if keyword:
                keyword_lower = keyword.lower()

                devices = [
                    device for device in devices
                    if keyword_lower in str(
                        device.get("ip", "")
                    ).lower()
                    or keyword_lower in str(
                        device.get("hostname", "")
                    ).lower()
                    or keyword_lower in str(
                        device.get("mac", "")
                    ).lower()
                ]

            if status != "All":
                devices = [
                    device for device in devices
                    if str(
                        device.get("status", "")
                    ) == status
                ]

        except Exception as error:

            self.device_summary_label.config(
                text=f"Database Error: {error}"
            )

            return

        for item in self.device_table.get_children():

            self.device_table.delete(
                item
            )

        for device in devices:

            status_text = (
                device.get(
                    "status",
                    "Unknown"
                )
            )

            if status_text == "Online":

                tag = "online"

            elif status_text == "Offline":

                tag = "offline"

            else:

                tag = "unknown"

            duration = device.get(
                "duration"
            )

            if duration is None:

                duration_text = "-"

            else:

                try:

                    duration_text = (
                        f"{float(duration):.2f} s"
                    )

                except Exception:

                    duration_text = str(
                        duration
                    )

            self.device_table.insert(
                "",
                "end",
                iid=str(
                    device.get(
                        "id"
                    )
                ),
                values=(
                    device.get(
                        "id",
                        ""
                    ),

                    device.get(
                        "ip",
                        ""
                    ),

                    device.get(
                        "hostname",
                        ""
                    ),

                    device.get(
                        "mac",
                        ""
                    ),

                    status_text,

                    duration_text,

                    device.get(
                        "first_seen",
                        ""
                    ),

                    device.get(
                        "last_seen",
                        ""
                    )
                ),
                tags=(tag,)
            )

        # Calculate the summary from the exact records displayed above.
        # This keeps the counters consistent with the table and avoids
        # using a second statistics source that may be stale.
        total = len(devices)
        online = sum(
            1
            for device in devices
            if str(device.get("status", "")) == "Online"
        )
        offline = sum(
            1
            for device in devices
            if str(device.get("status", "")) == "Offline"
        )

        self.device_summary_label.config(
            text=(
                f"Total: {total} | "
                f"Online: {online} | "
                f"Offline: {offline} | "
                f"Showing: {len(devices)}"
            )
        )

    def refresh_device_manager(self):

        self.apply_device_filters()

    # ======================================================
    # ADD DEVICE DIALOG
    # ======================================================

    def add_device_dialog(self):

        dialog = tk.Toplevel(
            self.root
        )

        dialog.title(
            "Add Device"
        )

        dialog.geometry(
            "450x400"
        )

        dialog.resizable(
            False,
            False
        )

        dialog.transient(
            self.root
        )

        dialog.grab_set()

        frame = tk.Frame(
            dialog,
            bg="#F3F4F6"
        )

        frame.pack(
            fill="both",
            expand=True
        )

        title = tk.Label(
            frame,
            text="Add New Device",
            bg="#F3F4F6",
            fg="#111827",
            font=(
                "Segoe UI",
                18,
                "bold"
            )
        )

        title.pack(
            pady=(25, 20)
        )

        form = tk.Frame(
            frame,
            bg="white",
            bd=1,
            relief="solid"
        )

        form.pack(
            fill="x",
            padx=25
        )

        tk.Label(
            form,
            text="IP Address *",
            bg="white",
            fg="#374151"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=15,
            pady=(20, 5)
        )

        ip_entry = tk.Entry(
            form,
            width=35
        )

        ip_entry.grid(
            row=1,
            column=0,
            padx=15,
            pady=(0, 10)
        )

        tk.Label(
            form,
            text="Hostname",
            bg="white",
            fg="#374151"
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=15,
            pady=(5, 5)
        )

        hostname_entry = tk.Entry(
            form,
            width=35
        )

        hostname_entry.grid(
            row=3,
            column=0,
            padx=15,
            pady=(0, 10)
        )

        tk.Label(
            form,
            text="MAC Address",
            bg="white",
            fg="#374151"
        ).grid(
            row=4,
            column=0,
            sticky="w",
            padx=15,
            pady=(5, 5)
        )

        mac_entry = tk.Entry(
            form,
            width=35
        )

        mac_entry.grid(
            row=5,
            column=0,
            padx=15,
            pady=(0, 10)
        )

        tk.Label(
            form,
            text="Status",
            bg="white",
            fg="#374151"
        ).grid(
            row=6,
            column=0,
            sticky="w",
            padx=15,
            pady=(5, 5)
        )

        status_var = tk.StringVar(
            value="Online"
        )

        status_combo = ttk.Combobox(
            form,
            textvariable=status_var,
            values=(
                "Online",
                "Offline",
                "Unknown"
            ),
            width=32,
            state="readonly"
        )

        status_combo.grid(
            row=7,
            column=0,
            padx=15,
            pady=(0, 20)
        )

        button_frame = tk.Frame(
            frame,
            bg="#F3F4F6"
        )

        button_frame.pack(
            pady=20
        )

        def save_new_device():

            ip = ip_entry.get().strip()

            hostname = (
                hostname_entry
                .get()
                .strip()
            )

            mac = (
                mac_entry
                .get()
                .strip()
            )

            status = status_var.get()

            if not ip:

                messagebox.showwarning(
                    "Missing IP",
                    "Please enter IP Address.",
                    parent=dialog
                )

                return

            try:

                ipaddress.ip_address(
                    ip
                )

            except ValueError:

                messagebox.showerror(
                    "Invalid IP",
                    "IP Address không hợp lệ.",
                    parent=dialog
                )

                return

            result = device_manager.add_device(
                ip=ip,
                hostname=hostname,
                mac=mac,
                status=status
            )

            if result.get(
                "success"
            ):

                self.add_activity(
                    f"Added device: {ip}"
                )

                dialog.destroy()

                self.refresh_device_manager()

            else:

                messagebox.showerror(
                    "Add Device",
                    result.get(
                        "message",
                        "Cannot add device."
                    ),
                    parent=dialog
                )

        tk.Button(
            button_frame,
            text="Save",
            command=save_new_device,
            bg="#16A34A",
            fg="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        ).pack(
            side="left",
            padx=5
        )

        tk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            bg="#6B7280",
            fg="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(
            side="left",
            padx=5
        )

        ip_entry.focus()

    def get_selected_device_id(self):

        if self.device_table is None:

            return None

        selection = (
            self.device_table.selection()
        )

        if not selection:

            return None

        try:

            return int(
                selection[0]
            )

        except Exception:

            return None

    def on_device_double_click(
        self,
        event
    ):

        self.edit_selected_device()

    def edit_selected_device(self):

        device_id = (
            self.get_selected_device_id()
        )

        if device_id is None:

            messagebox.showwarning(
                "Edit Device",
                "Please select a device."
            )

            return

        device = device_manager.get_device(
            device_id
        )

        if device is None:

            messagebox.showerror(
                "Edit Device",
                "Device not found."
            )

            self.refresh_device_manager()

            return

        dialog = tk.Toplevel(
            self.root
        )

        dialog.title(
            "Edit Device"
        )

        dialog.geometry(
            "450x400"
        )

        dialog.resizable(
            False,
            False
        )

        dialog.transient(
            self.root
        )

        dialog.grab_set()

        frame = tk.Frame(
            dialog,
            bg="#F3F4F6"
        )

        frame.pack(
            fill="both",
            expand=True
        )

        tk.Label(
            frame,
            text="Edit Device",
            bg="#F3F4F6",
            fg="#111827",
            font=(
                "Segoe UI",
                18,
                "bold"
            )
        ).pack(
            pady=(25, 20)
        )

        form = tk.Frame(
            frame,
            bg="white",
            bd=1,
            relief="solid"
        )

        form.pack(
            fill="x",
            padx=25
        )

        tk.Label(
            form,
            text="IP Address *",
            bg="white",
            fg="#374151"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=15,
            pady=(20, 5)
        )

        ip_entry = tk.Entry(
            form,
            width=35
        )

        ip_entry.insert(
            0,
            device.get(
                "ip",
                ""
            )
        )

        ip_entry.grid(
            row=1,
            column=0,
            padx=15,
            pady=(0, 10)
        )

        tk.Label(
            form,
            text="Hostname",
            bg="white",
            fg="#374151"
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=15,
            pady=(5, 5)
        )

        hostname_entry = tk.Entry(
            form,
            width=35
        )

        hostname_entry.insert(
            0,
            device.get(
                "hostname"
            ) or ""
        )

        hostname_entry.grid(
            row=3,
            column=0,
            padx=15,
            pady=(0, 10)
        )

        tk.Label(
            form,
            text="MAC Address",
            bg="white",
            fg="#374151"
        ).grid(
            row=4,
            column=0,
            sticky="w",
            padx=15,
            pady=(5, 5)
        )

        mac_entry = tk.Entry(
            form,
            width=35
        )

        mac_entry.insert(
            0,
            device.get(
                "mac"
            ) or ""
        )

        mac_entry.grid(
            row=5,
            column=0,
            padx=15,
            pady=(0, 10)
        )

        tk.Label(
            form,
            text="Status",
            bg="white",
            fg="#374151"
        ).grid(
            row=6,
            column=0,
            sticky="w",
            padx=15,
            pady=(5, 5)
        )

        status_var = tk.StringVar(
            value=(
                device.get(
                    "status"
                )
                or "Unknown"
            )
        )

        status_combo = ttk.Combobox(
            form,
            textvariable=status_var,
            values=(
                "Online",
                "Offline",
                "Unknown"
            ),
            width=32,
            state="readonly"
        )

        status_combo.grid(
            row=7,
            column=0,
            padx=15,
            pady=(0, 20)
        )

        button_frame = tk.Frame(
            frame,
            bg="#F3F4F6"
        )

        button_frame.pack(
            pady=20
        )

        def save_edit():

            new_ip = (
                ip_entry
                .get()
                .strip()
            )

            hostname = (
                hostname_entry
                .get()
                .strip()
            )

            mac = (
                mac_entry
                .get()
                .strip()
            )

            status = (
                status_var
                .get()
            )

            if not new_ip:

                messagebox.showwarning(
                    "Invalid IP",
                    "IP Address không được để trống.",
                    parent=dialog
                )

                return

            try:

                ipaddress.ip_address(
                    new_ip
                )

            except ValueError:

                messagebox.showerror(
                    "Invalid IP",
                    "IP Address không hợp lệ.",
                    parent=dialog
                )

                return

            result = device_manager.edit_device(
                device_id=device_id,
                ip=new_ip,
                hostname=hostname,
                mac=mac,
                status=status
            )

            if result.get(
                "success"
            ):

                self.add_activity(
                    f"Updated device: {new_ip}"
                )

                dialog.destroy()

                self.refresh_device_manager()

            else:

                messagebox.showerror(
                    "Edit Device",
                    result.get(
                        "message",
                        "Cannot update device."
                    ),
                    parent=dialog
                )

        tk.Button(
            button_frame,
            text="Save",
            command=save_edit,
            bg="#2563EB",
            fg="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        ).pack(
            side="left",
            padx=5
        )

        tk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            bg="#6B7280",
            fg="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(
            side="left",
            padx=5
        )

        ip_entry.focus()

    def delete_selected_device(self):

        device_id = (
            self.get_selected_device_id()
        )

        if device_id is None:

            messagebox.showwarning(
                "Delete Device",
                "Please select a device."
            )

            return

        device = device_manager.get_device(
            device_id
        )

        if device is None:

            messagebox.showerror(
                "Delete Device",
                "Device not found."
            )

            self.refresh_device_manager()

            return

        ip = device.get(
            "ip",
            ""
        )

        hostname = device.get(
            "hostname",
            ""
        )

        confirm = messagebox.askyesno(
            "Delete Device",
            (
                "Bạn có chắc muốn xóa thiết bị này?\n\n"
                f"IP: {ip}\n"
                f"Hostname: {hostname}"
            )
        )

        if not confirm:

            return

        result = device_manager.remove_device(
            device_id
        )

        if result.get(
            "success"
        ):

            self.add_activity(
                f"Deleted device: {ip}"
            )

            self.refresh_device_manager()

        else:

            messagebox.showerror(
                "Delete Device",
                result.get(
                    "message",
                    "Cannot delete device."
                )
            )

    # ======================================================
    # PING MONITOR
    # ======================================================

    def show_ping_monitor(self):

        self.current_page = "Ping Monitor"

        self.clear_content()

        self.set_page_title(
            "Ping Monitor",
            "Monitor multiple IP addresses"
        )

        top = tk.Frame(
            self.content,
            bg="white",
            bd=1,
            relief="solid"
        )

        top.pack(
            fill="x",
            padx=25,
            pady=10
        )

        tk.Label(
            top,
            text="IP Addresses / Hosts:",
            bg="white",
            fg="#374151",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        ).pack(
            anchor="w",
            padx=20,
            pady=(15, 5)
        )

        self.ping_entry = tk.Text(
            top,
            height=5,
            font=(
                "Consolas",
                10
            )
        )

        self.ping_entry.pack(
            fill="x",
            padx=20
        )

        self.ping_entry.insert(
            "1.0",
            "192.168.1.1\n"
            "192.168.1.10\n"
            "192.168.1.20"
        )

        button_frame = tk.Frame(
            top,
            bg="white"
        )

        button_frame.pack(
            fill="x",
            padx=20,
            pady=15
        )

        self.ping_all_button = tk.Button(
            button_frame,
            text="Ping All",
            command=self.run_ping_all,
            bg="#2563EB",
            fg="white",
            relief="flat",
            bd=0,
            padx=15,
            pady=8,
            cursor="hand2",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        )

        self.ping_all_button.pack(
            side="left"
        )

        self.auto_ping_button = tk.Button(
            button_frame,
            text="Start Auto Ping",
            command=self.toggle_auto_ping,
            bg="#16A34A",
            fg="white",
            relief="flat",
            bd=0,
            padx=15,
            pady=8,
            cursor="hand2",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        )

        self.auto_ping_button.pack(
            side="left",
            padx=10
        )

        self.interval_var = tk.StringVar(
            value="5"
        )

        tk.Label(
            button_frame,
            text="Interval:",
            bg="white",
            fg="#374151"
        ).pack(
            side="left",
            padx=(10, 5)
        )

        self.interval_combo = ttk.Combobox(
            button_frame,
            textvariable=self.interval_var,
            values=(
                "1",
                "5",
                "10",
                "30"
            ),
            width=8,
            state="readonly"
        )

        self.interval_combo.pack(
            side="left"
        )

        clear_button = tk.Button(
            button_frame,
            text="Clear",
            command=self.clear_ping,
            bg="#6B7280",
            fg="white",
            relief="flat",
            bd=0,
            padx=15,
            pady=8,
            cursor="hand2"
        )

        clear_button.pack(
            side="left",
            padx=10
        )

        self.ping_status_label = tk.Label(
            button_frame,
            text="Ready",
            bg="white",
            fg="#6B7280"
        )

        self.ping_status_label.pack(
            side="left",
            padx=15
        )

        result_frame = tk.Frame(
            self.content,
            bg="white",
            bd=1,
            relief="solid"
        )

        result_frame.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=(0, 20)
        )

        columns = (
            "time",
            "ip",
            "status",
            "response"
        )

        self.ping_table = ttk.Treeview(
            result_frame,
            columns=columns,
            show="headings"
        )

        self.ping_table.heading(
            "time",
            text="Time"
        )

        self.ping_table.heading(
            "ip",
            text="IP Address"
        )

        self.ping_table.heading(
            "status",
            text="Status"
        )

        self.ping_table.heading(
            "response",
            text="Response"
        )

        self.ping_table.column(
            "time",
            width=120,
            anchor="center"
        )

        self.ping_table.column(
            "ip",
            width=200
        )

        self.ping_table.column(
            "status",
            width=150,
            anchor="center"
        )

        self.ping_table.column(
            "response",
            width=150,
            anchor="center"
        )

        scrollbar_y = ttk.Scrollbar(
            result_frame,
            orient="vertical",
            command=self.ping_table.yview
        )

        scrollbar_x = ttk.Scrollbar(
            result_frame,
            orient="horizontal",
            command=self.ping_table.xview
        )

        self.ping_table.configure(
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )

        self.ping_table.pack(
            side="top",
            fill="both",
            expand=True,
            padx=(15, 0),
            pady=(15, 0)
        )

        scrollbar_y.pack(
            side="right",
            fill="y",
            padx=(0, 15),
            pady=(15, 0)
        )

        scrollbar_x.pack(
            side="bottom",
            fill="x",
            padx=(15, 15),
            pady=(0, 15)
        )

        self.ping_table.tag_configure(
            "online",
            foreground="#16A34A"
        )

        self.ping_table.tag_configure(
            "offline",
            foreground="#DC2626"
        )

        self.ping_table.tag_configure(
            "error",
            foreground="#D97706"
        )

    def get_ping_ips(self):

        if not hasattr(
            self,
            "ping_entry"
        ):

            return []

        text = self.ping_entry.get(
            "1.0",
            tk.END
        )

        ips = []

        for line in text.splitlines():

            ip = line.strip()

            if ip and ip not in ips:

                ips.append(ip)

        return ips

    def run_ping_all(self):

        if self.ping_running:

            self.ping_status_label.config(
                text="A ping operation is already running."
            )

            return

        ips = self.get_ping_ips()

        if not ips:

            self.ping_status_label.config(
                text="No IP address."
            )

            return

        self.start_ping_thread(
            ips
        )

    def start_ping_thread(
        self,
        ips
    ):

        if self.ping_running:

            return

        self.ping_running = True

        self.ping_all_button.config(
            state="disabled"
        )

        self.ping_status_label.config(
            text=f"Pinging {len(ips)} hosts..."
        )

        thread = threading.Thread(
            target=self.ping_worker,
            args=(ips,),
            daemon=True
        )

        thread.start()

    def ping_worker(
        self,
        ips
    ):

        try:

            results = ping_multiple(
                ips,
                max_workers=50,
                timeout=1
            )

            self.root.after(
                0,
                self.display_ping_results,
                results
            )

        except Exception as error:

            self.root.after(
                0,
                self.ping_error,
                str(error)
            )

    def display_ping_results(
        self,
        results
    ):

        for item in self.ping_table.get_children():

            self.ping_table.delete(
                item
            )

        online = 0
        offline = 0
        errors = 0

        for result in results:

            status = result.get(
                "status",
                "Error"
            )

            response = result.get(
                "response"
            )

            if response is None:

                response_text = "-"

            else:

                response_text = (
                    f"{response} ms"
                )

            if status == "Online":

                online += 1
                tag = "online"

            elif status == "Offline":

                offline += 1
                tag = "offline"

            else:

                errors += 1
                tag = "error"

            self.ping_table.insert(
                "",
                "end",
                values=(
                    result.get(
                        "time",
                        datetime.now().strftime(
                            "%H:%M:%S"
                        )
                    ),

                    result.get(
                        "ip",
                        ""
                    ),

                    status,

                    response_text
                ),
                tags=(tag,)
            )

        self.ping_running = False

        self.ping_all_button.config(
            state="normal"
        )

        self.ping_status_label.config(
            text=(
                f"Total: {len(results)} | "
                f"Online: {online} | "
                f"Offline: {offline} | "
                f"Error: {errors}"
            )
        )

        self.add_activity(
            "Ping completed. "
            f"Total: {len(results)}, "
            f"Online: {online}, "
            f"Offline: {offline}"
        )

        if self.auto_ping_running:

            self.schedule_auto_ping()

    def ping_error(
        self,
        error
    ):

        self.ping_running = False

        self.ping_all_button.config(
            state="normal"
        )

        self.ping_status_label.config(
            text=f"Error: {error}"
        )

        self.add_activity(
            f"Ping error: {error}"
        )

        if self.auto_ping_running:

            self.schedule_auto_ping()

    def toggle_auto_ping(self):

        if self.auto_ping_running:

            self.stop_auto_ping()

        else:

            self.start_auto_ping()

    def start_auto_ping(self):

        ips = self.get_ping_ips()

        if not ips:

            self.ping_status_label.config(
                text="No IP address."
            )

            return

        self.auto_ping_running = True

        self.auto_ping_button.config(
            text="Stop Auto Ping",
            bg="#DC2626"
        )

        self.ping_status_label.config(
            text="Auto Ping running..."
        )

        self.add_activity(
            "Auto Ping started."
        )
 
        if not self.ping_running:

            self.start_ping_thread(
                ips
            )

    def stop_auto_ping(
        self,
        silent=False
    ):

        self.auto_ping_running = False

        if self.auto_ping_job is not None:

            try:

                self.root.after_cancel(
                    self.auto_ping_job
                )

            except Exception:

                pass

            self.auto_ping_job = None

        if hasattr(
            self,
            "auto_ping_button"
        ):

            try:

                if self.auto_ping_button.winfo_exists():

                    self.auto_ping_button.config(
                        text="Start Auto Ping",
                        bg="#16A34A"
                    )

            except tk.TclError:

                pass

        if not silent:

            if hasattr(
                self,
                "ping_status_label"
            ):

                try:

                    if self.ping_status_label.winfo_exists():

                        self.ping_status_label.config(
                            text="Auto Ping stopped."
                        )

                except tk.TclError:

                    pass

            self.add_activity(
                "Auto Ping stopped."
            )

    def schedule_auto_ping(self):

        if not self.auto_ping_running:

            return

        if self.auto_ping_job is not None:

            return

        try:

            interval = int(
                self.interval_var.get()
            )

        except Exception:

            interval = 5

        self.auto_ping_job = self.root.after(
            interval * 1000,
            self.auto_ping_tick
        )

    def auto_ping_tick(self):

        self.auto_ping_job = None

        if not self.auto_ping_running:

            return

        ips = self.get_ping_ips()

        if not ips:

            self.stop_auto_ping()

            return

        if self.ping_running:

            self.schedule_auto_ping()

            return

        self.start_ping_thread(
            ips
        )

    def clear_ping(self):

        if self.auto_ping_running:

            self.stop_auto_ping()

        for item in self.ping_table.get_children():

            self.ping_table.delete(
                item
            )

        self.ping_status_label.config(
            text="Cleared."
        )

        self.add_activity(
            "Ping monitor cleared."
        )

    def show_placeholder(self):

        self.current_page = "Coming Soon"

        self.clear_content()

        self.set_page_title(
            "Module",
            "This module is under development."
        )

        frame = tk.Frame(
            self.content,
            bg="white",
            bd=1,
            relief="solid"
        )

        frame.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=10
        )

        tk.Label(
            frame,
            text="Coming Soon",
            bg="white",
            fg="#6B7280",
            font=(
                "Segoe UI",
                20,
                "bold"
            )
        ).pack(
            expand=True
        )


if __name__ == "__main__":

    init_database()

    root = tk.Tk()

    app = NetworkAutomationApp(
        root
    )

    root.mainloop()