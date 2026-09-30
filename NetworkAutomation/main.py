import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import threading
import time
import ipaddress
import pandas as pd

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
from modules.ip_mac_manager import IPMacManagerPage
from modules.extra_pages import (
    NetworkDevicesPage,
    RemoteServicePage,
    BackupConfigPage,
    SchedulerPage,
    AlertsPage,
    ReportsPage,
    SystemLogsPage,
    SettingsPage,
    log_activity,
    get_setting,
    set_setting,
)
from modules.advanced_pages import (
    SNMPMonitorPage,
    NetworkTopologyPage,
    SSHAutomationPage,
    NotificationsPage,
    ensure_advanced_tables,
)
from modules.nms_v2 import (
    NOCDashboardPage, AutoDiscoveryPage, MultiPortMonitorPage, BackupSchedulerPage, NetworkHealthPage,
)
from modules.nms_v3 import ResourceMonitorPage, AdvancedPortMonitorPage, AlertRulesPage, HistoryChartsPage, ensure_v3_tables
from modules.nms_v4 import AutoTopologyPage, BackgroundAlertEngine, ensure_v4_tables
from modules.nms_v5 import (
    ensure_v5_tables, CredentialManagerPage, SecureBackupSchedulerPage,
    ConfigComparePage, UserRolePage, LoginDialog
)
from modules.nms_v6 import (
    ensure_v6_tables, audit, MonitoringService, MonitoringServicePage, AuditLogPage, RestoreConfigPage
)
from modules.nms_v7 import ensure_v7_tables, DeviceProfilesPage
from modules.nms_v8 import ensure_v8_tables, OrganizationPage, MaintenanceWindowsPage
from modules.nms_v9 import ensure_v9_tables, SLAAvailabilityPage, IncidentCenterPage, CapacityPlanningPage
from modules.nms_v10 import (
    ensure_v10_tables, RootCauseEngine, DeviceDependenciesPage,
    RootCauseAnalysisPage, ServiceImpactPage
)
from modules.nms_v11 import ensure_v11_tables, JobQueueEngine, StableCorePage
from modules.nms_v12 import ensure_v12_tables, SNMPv3CredentialsPage, VendorDriverPage, SecureSNMPDiagnosticsPage


from modules.auto_ip import AutomationEngine
from modules.auto_ip_page import AutoIPPage


class NetworkAutomationApp:

    def __init__(self, root, session_user=None):

        self.root = root
        self.session_user = session_user or {"username": "local-admin", "role": "Admin", "bootstrap": True}
        self.current_role = self.session_user.get("role", "Viewer")
        # Khởi tạo/migrate toàn bộ schema trước khi bất kỳ màn hình nào đọc dữ liệu.
        ensure_advanced_tables()
        ensure_v3_tables()
        ensure_v4_tables()
        ensure_v5_tables()
        ensure_v6_tables()
        ensure_v7_tables()
        ensure_v8_tables()
        ensure_v9_tables()
        ensure_v10_tables()
        ensure_v11_tables()
        ensure_v12_tables()

        self.root.title(
            "Công cụ Tự động hóa Mạng"
        )

        self.root.geometry(
            "1400x800"
        )

        self.root.minsize(
            980,
            600
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

        # v3.4: tự động đánh giá Alert Rules nền mỗi 60 giây.
        self.background_alert_engine = BackgroundAlertEngine(self.root, self.add_activity)
        self.monitoring_service = MonitoringService(self.root, self.add_activity)
        self.job_queue_engine = JobQueueEngine()
        self.root_cause_engine = RootCauseEngine(self.root, self.add_activity)
        audit(self.session_user.get('username'), self.current_role, 'Mở ứng dụng', 'Network Automation', 'Khởi tạo phiên làm việc')
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)

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

        # Phần tiêu đề cố định phía trên.
        title = tk.Label(
            self.sidebar,
            text=f"NETWORK\nAUTOMATION\n\n{self.session_user.get('username','')} • {self.current_role}",
            bg="#111827",
            fg="white",
            font=("Segoe UI", 16, "bold"),
            justify="left"
        )
        title.pack(padx=20, pady=(20, 12), anchor="w")

        # Menu có thanh cuộn để vẫn dùng được trên màn hình thấp.
        menu_area = tk.Frame(self.sidebar, bg="#111827")
        menu_area.pack(fill="both", expand=True)

        self.sidebar_canvas = tk.Canvas(
            menu_area, bg="#111827", highlightthickness=0, bd=0
        )
        sidebar_scroll = tk.Scrollbar(
            menu_area, orient="vertical", command=self.sidebar_canvas.yview
        )
        self.sidebar_menu = tk.Frame(self.sidebar_canvas, bg="#111827")
        self.sidebar_menu.bind(
            "<Configure>",
            lambda e: self.sidebar_canvas.configure(
                scrollregion=self.sidebar_canvas.bbox("all")
            )
        )
        self._sidebar_window = self.sidebar_canvas.create_window(
            (0, 0), window=self.sidebar_menu, anchor="nw"
        )
        self.sidebar_canvas.bind(
            "<Configure>",
            lambda e: self.sidebar_canvas.itemconfigure(
                self._sidebar_window, width=e.width
            )
        )
        self.sidebar_canvas.configure(yscrollcommand=sidebar_scroll.set)
        self.sidebar_canvas.pack(side="left", fill="both", expand=True)
        sidebar_scroll.pack(side="right", fill="y")

        # Nhóm chức năng theo nghiệp vụ để thanh bên gọn và dễ tìm hơn.
        # Mỗi nhóm có thể thu gọn / mở rộng độc lập.
        menu_groups = [
            ("TỔNG QUAN", [
                ("Tổng quan", self.show_dashboard),
                ("Trung tâm giám sát NOC", self.show_noc_dashboard),
                ("SLA & Độ sẵn sàng", self.show_sla_availability),
            ]),
            ("KHÁM PHÁ & GIÁM SÁT", [
                ("Tự động phát hiện", self.show_auto_discovery),
                ("Quét mạng", self.show_network_scan),
                ("Giám sát Ping", self.show_ping_monitor),
                ("Sức khỏe mạng", self.show_network_health),
                ("Giám sát SNMP", self.show_snmp_monitor),
                ("Chẩn đoán SNMP v2c/v3", self.show_secure_snmp_diagnostics),
                ("CPU / RAM SNMP", self.show_resource_monitor),
                ("Giám sát cổng nâng cao", self.show_advanced_port_monitor),
                ("Giám sát nhiều cổng", self.show_multi_port_monitor),
                ("Biểu đồ lịch sử", self.show_history_charts),
                ("Phân tích dung lượng", self.show_capacity_planning),
            ]),
            ("QUẢN LÝ MẠNG", [
                ("Quản lý thiết bị", self.show_device_manager),
                ("Quản lý IP / MAC", self.show_ip_mac_manager),
                ("Thiết bị mạng", self.show_network_devices),
                ("Hồ sơ thiết bị theo hãng", self.show_device_profiles),
                ("Vendor Driver Engine", self.show_vendor_drivers),
                ("Site / Nhóm / VLAN", self.show_organization),
                ("Sơ đồ mạng", self.show_network_topology),
                ("Tự dựng Topology LLDP/CDP", self.show_auto_topology),
                ("Phụ thuộc thiết bị", self.show_device_dependencies),
                ("Dịch vụ & Mức ảnh hưởng", self.show_service_impact),
            ]),
            ("TỰ ĐỘNG HÓA", [
                ("Tự động IP/Excel", self.show_auto_ip),
                ("Tự động hóa SSH", self.show_ssh_automation),
                ("Truy cập từ xa", self.show_remote_service),
                ("Sao lưu cấu hình", self.show_backup_config),
                ("Lịch sao lưu bảo mật", self.show_secure_backup_scheduler),
                ("So sánh cấu hình", self.show_config_compare),
                ("Lịch tác vụ", self.show_scheduler),
                ("Khôi phục cấu hình", self.show_restore_config),
            ]),
            ("CẢNH BÁO & BÁO CÁO", [
                ("Cảnh báo", self.show_alerts),
                ("Quy tắc cảnh báo", self.show_alert_rules),
                ("Lịch bảo trì", self.show_maintenance_windows),
                ("Trung tâm sự cố", self.show_incident_center),
                ("Phân tích nguyên nhân gốc", self.show_root_cause_analysis),
                ("Thông báo", self.show_notifications),
                ("Báo cáo", self.show_reports),
                ("Nhật ký hệ thống", self.show_system_logs),
                ("Nhật ký Audit", self.show_audit_log),
            ]),
            ("HỆ THỐNG", [
                ("Quản lý Credential", self.show_credential_manager),
                ("Credential SNMPv3", self.show_snmpv3_credentials),
                ("Người dùng & Phân quyền", self.show_user_roles),
                ("Cài đặt", self.show_settings),
                ("Dịch vụ giám sát nền", self.show_monitoring_service),
                ("Sức khỏe hệ thống", self.show_stable_core),
            ]),
        ]

        # Phân quyền menu theo vai trò đăng nhập.
        if self.current_role == "Viewer":
            allowed = {
                "Tổng quan", "Trung tâm giám sát NOC", "Quét mạng", "Giám sát Ping",
                "Sức khỏe mạng", "Giám sát SNMP", "Chẩn đoán SNMP v2c/v3", "CPU / RAM SNMP",
                "Giám sát cổng nâng cao", "Giám sát nhiều cổng", "Biểu đồ lịch sử",
                "Sơ đồ mạng", "Tự dựng Topology LLDP/CDP", "Cảnh báo", "Báo cáo", "Nhật ký hệ thống",
                "SLA & Độ sẵn sàng", "Phân tích dung lượng", "Trung tâm sự cố",
                "Phụ thuộc thiết bị", "Dịch vụ & Mức ảnh hưởng", "Phân tích nguyên nhân gốc", "Vendor Driver Engine"
            }
            menu_groups = [(g, [(t,c) for t,c in items if t in allowed]) for g,items in menu_groups]
            menu_groups = [(g,items) for g,items in menu_groups if items]
        elif self.current_role == "Operator":
            blocked = {"Quản lý Credential", "Credential SNMPv3", "Người dùng & Phân quyền", "Cài đặt", "Khôi phục cấu hình", "Nhật ký Audit", "Dịch vụ giám sát nền"}
            menu_groups = [(g, [(t,c) for t,c in items if t not in blocked]) for g,items in menu_groups]
            menu_groups = [(g,items) for g,items in menu_groups if items]

        self.sidebar_groups = {}

        def toggle_group(group_name):
            info = self.sidebar_groups[group_name]
            frame = info["frame"]
            button = info["button"]
            if info["expanded"]:
                frame.pack_forget()
                info["expanded"] = False
                button.configure(text=f"▸  {group_name}")
            else:
                # Giữ frame ngay sau tiêu đề nhóm tương ứng.
                frame.pack(fill="x", after=button)
                info["expanded"] = True
                button.configure(text=f"▾  {group_name}")

        for group_name, items in menu_groups:
            header = tk.Button(
                self.sidebar_menu,
                text=f"▾  {group_name}",
                bg="#0B1220",
                fg="#93C5FD",
                activebackground="#172033",
                activeforeground="white",
                relief="flat",
                bd=0,
                anchor="w",
                padx=14,
                pady=7,
                font=("Segoe UI", 9, "bold"),
                cursor="hand2",
            )
            header.pack(fill="x", pady=(4, 0))

            group_frame = tk.Frame(self.sidebar_menu, bg="#111827")
            group_frame.pack(fill="x")

            self.sidebar_groups[group_name] = {
                "button": header,
                "frame": group_frame,
                "expanded": True,
            }
            header.configure(command=lambda name=group_name: toggle_group(name))

            for text, command in items:
                button = tk.Button(
                    group_frame,
                    text=text,
                    command=command,
                    bg="#111827",
                    fg="#D1D5DB",
                    activebackground="#1F2937",
                    activeforeground="white",
                    relief="flat",
                    bd=0,
                    anchor="w",
                    padx=28,
                    pady=6,
                    font=("Segoe UI", 9),
                    cursor="hand2",
                )
                button.pack(fill="x")

    # ======================================================
    # COMMON
    # ======================================================

    def clear_content(self):

        if hasattr(self, "auto_ip_page"):
            self.auto_ip_page.destroy()
            del self.auto_ip_page

        if hasattr(self, "scheduler_page"):
            try:
                self.scheduler_page.destroy()
            except Exception:
                pass
            try:
                del self.scheduler_page
            except Exception:
                pass

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

        try:
            log_activity("Application", message)
        except Exception:
            pass
        try:
            audit(self.session_user.get("username"), self.current_role, "Hoạt động", self.current_page or "Ứng dụng", message)
        except Exception:
            pass

    # ======================================================
    # DASHBOARD
    # ======================================================

    def show_dashboard(self):

        self.current_page = "Tổng quan"

        self.clear_content()

        self.set_page_title(
            "Network Automation Tool\nIT Infrastructure Management System\nVersion 3.10"
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
                "Cảnh báo",
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
            text="Hoạt động gần đây",
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

        self.current_page = "Quét mạng"

        self.clear_content()

        self.set_page_title(
            "Quét mạng",
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
            text="Mạng:",
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
            get_setting("default_network", "192.168.1.0/24")
        )

        self.network_entry.pack(
            side="left",
            pady=18
        )

        self.scan_button = tk.Button(
            control,
            text="Quét mạng",
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
            text="Dừng quét",
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
            text="Sẵn sàng",
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
            text="Tìm kiếm:",
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
            text="Trạng thái:",
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
            text="Sắp xếp:",
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
                "Địa chỉ IP",
                "Thời lượng",
                "Thời gian"
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
            text="Thời gian"
        )

        self.scan_table.heading(
            "ip",
            text="Địa chỉ IP"
        )

        self.scan_table.heading(
            "hostname",
            text="Tên máy"
        )

        self.scan_table.heading(
            "mac",
            text="Địa chỉ MAC"
        )

        self.scan_table.heading(
            "status",
            text="Trạng thái"
        )

        self.scan_table.heading(
            "duration",
            text="Thời lượng"
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

        elif sort_type == "Địa chỉ IP":

            filtered_results.sort(
                key=ip_sort_key
            )

        elif sort_type == "Thời lượng":

            filtered_results.sort(
                key=lambda result: (
                    duration_sort_key(result),
                    ip_sort_key(result)
                )
            )

        elif sort_type == "Thời gian":

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

        self.current_page = "Quản lý thiết bị"

        self.clear_content()

        self.set_page_title(
            "Quản lý thiết bị",
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
            text="Tìm kiếm:",
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
            text="Trạng thái:",
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
            text="Làm mới",
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

        # Nút Xuất Excel
        export_excel_button = tk.Button(
            toolbar,
            text="Xuất Excel",
            command=self.export_devices_excel,
            bg="#059669",
            fg="white",
            activebackground="#047857",
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
        export_excel_button.pack(
            side="left",
            padx=5
        )

        add_button = tk.Button(
            toolbar,
            text="Thêm thiết bị",
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
            selectmode="extended"  # Cho phép chọn nhiều dòng
        )

        self.device_table.heading(
            "id",
            text="ID"
        )

        self.device_table.heading(
            "ip",
            text="Địa chỉ IP"
        )

        self.device_table.heading(
            "hostname",
            text="Tên máy"
        )

        self.device_table.heading(
            "mac",
            text="Địa chỉ MAC"
        )

        self.device_table.heading(
            "status",
            text="Trạng thái"
        )

        self.device_table.heading(
            "duration",
            text="Thời lượng"
        )

        self.device_table.heading(
            "first_seen",
            text="Phát hiện lần đầu"
        )

        self.device_table.heading(
            "last_seen",
            text="Lần cuối phát hiện"
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
            text="Sửa thiết bị",
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
            text="Xóa mục đã chọn",
            command=self.delete_selected_devices,
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

        select_all_button = tk.Button(
            button_frame,
            text="Chọn tất cả",
            command=self.select_all_devices,
            bg="#4B5563",
            fg="white",
            activebackground="#374151",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=15,
            pady=8,
            cursor="hand2",
            font=(
                "Segoe UI",
                10
            )
        )

        select_all_button.pack(
            side="left",
            padx=10
        )
        
        deselect_button = tk.Button(
            button_frame,
            text="Bỏ chọn",
            command=self.deselect_all_devices,
            bg="#6B7280",
            fg="white",
            activebackground="#4B5563",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=15,
            pady=8,
            cursor="hand2",
            font=(
                "Segoe UI",
                10
            )
        )
        deselect_button = tk.Button(
                    button_frame,
                    text="Bỏ chọn",
                    command=self.deselect_all_devices,
                    bg="#6B7280",
                    fg="white",
                    activebackground="#4B5563",
                    activeforeground="white",
                    relief="flat",
                    bd=0,
                    padx=15,
                    pady=8,
                    cursor="hand2",
                    font=(
                        "Segoe UI",
                        10
                    )
                )
        deselect_button.pack(
            side="left",
            padx=5
        )
        
        self.refresh_device_manager()

    # ======================================================
    # EXPORT DEVICES TO EXCEL
    # ======================================================

    def export_devices_excel(self):
        """Hàm xuất danh sách thiết bị từ bảng Device Manager ra file Excel"""
        if self.device_table is None:
            messagebox.showwarning("Xuất Excel", "Không tìm thấy bảng thiết bị.")
            return

        children = self.device_table.get_children()
        if not children:
            messagebox.showwarning("Xuất Excel", "Không có dữ liệu thiết bị nào để xuất.")
            return

        # Thu thập dữ liệu đang hiển thị trên bảng
        export_data = []
        for item_id in children:
            values = self.device_table.item(item_id, "values")
            if values:
                export_data.append({
                    "ID": values[0],
                    "Địa chỉ IP": values[1],
                    "Tên máy": values[2],
                    "Địa chỉ MAC": values[3],
                    "Trạng thái": values[4],
                    "Thời lượng": values[5],
                    "Phát hiện lần đầu": values[6],
                    "Lần cuối phát hiện": values[7]
                })

        if not export_data:
            messagebox.showwarning("Xuất Excel", "Danh sách dữ liệu trống.")
            return

        # Mở hộp thoại chọn nơi lưu file
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile=f"devices_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            title="Lưu file Excel danh sách thiết bị"
        )

        if not file_path:
            return

        try:
            df = pd.DataFrame(export_data)
            df.to_excel(file_path, index=False)
            messagebox.showinfo("Xuất Excel", f"Xuất file Excel thành công!\nĐã lưu tại:\n{file_path}")
            self.add_activity(f"Exported {len(export_data)} devices to Excel: {file_path}")
        except Exception as error:
            messagebox.showerror("Export Error", f"Không thể xuất file Excel:\n{error}")
            self.add_activity(f"Export Excel error: {error}")

    # ======================================================
    # DEVICE FILTER
    # ======================================================

    def _normalize_device_record(self, device):

        if isinstance(device, dict):
            raw = dict(device)

        else:
            try:
                raw = dict(device)
            except Exception:
                raw = None

        if raw is None:
            try:
                return {
                    "id": device[0],
                    "ip": device[1],
                    "hostname": device[2],
                    "mac": device[3],
                    "status": device[4],
                    "duration": device[5],
                    "first_seen": device[6],
                    "last_seen": device[7],
                }
            except Exception:
                return None

        def first_value(*keys, default=None):
            for key in keys:
                if key in raw:
                    value = raw.get(key)
                    if value is not None and str(value).strip().lower() not in ("", "none", "null"):
                        return value
            return default

        return {
            "id": first_value("id", "device_id"),
            "ip": first_value(
                "ip",
                "ip_address",
                "ip_addr",
                "address",
                default=""
            ),
            "hostname": first_value(
                "hostname",
                "host_name",
                "name",
                "device_name",
                default=""
            ),
            "mac": first_value(
                "mac",
                "mac_address",
                "mac_addr",
                default=""
            ),
            "status": first_value(
                "status",
                "state",
                default="Unknown"
            ),
            "duration": first_value(
                "duration",
                "response_time",
                "latency"
            ),
            "first_seen": first_value(
                "first_seen",
                "created_at",
                "first_seen_at",
                default=""
            ),
            "last_seen": first_value(
                "last_seen",
                "updated_at",
                "last_seen_at",
                default=""
            ),
        }

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
            keyword = self.device_search_var.get().strip().lower()

        status_filter = "All"
        if self.device_status_filter_var is not None:
            status_filter = self.device_status_filter_var.get()

        try:
            raw_devices = get_all_devices() or []

            all_devices = []
            for row in raw_devices:
                device = self._normalize_device_record(row)
                if device is not None:
                    all_devices.append(device)

            total = len(all_devices)
            online = sum(
                1 for d in all_devices
                if str(d.get("status", "")).lower() == "online"
            )
            offline = sum(
                1 for d in all_devices
                if str(d.get("status", "")).lower() == "offline"
            )

            devices = all_devices

            if keyword:
                devices = [
                    d for d in devices
                    if keyword in str(d.get("ip", "")).lower()
                    or keyword in str(d.get("hostname", "")).lower()
                    or keyword in str(d.get("mac", "")).lower()
                ]

            if status_filter != "All":
                wanted = status_filter.lower()
                devices = [
                    d for d in devices
                    if str(d.get("status", "")).lower() == wanted
                ]

        except Exception as error:
            self.device_summary_label.config(
                text=f"Database Error: {error}"
            )
            return

        for item in self.device_table.get_children():
            self.device_table.delete(item)

        for index, device in enumerate(devices):

            status_text = str(device.get("status") or "Unknown")

            if status_text.lower() == "online":
                tag = "online"
            elif status_text.lower() == "offline":
                tag = "offline"
            else:
                tag = "unknown"

            duration = device.get("duration")
            if duration in (None, ""):
                duration_text = "-"
            else:
                try:
                    duration_text = f"{float(duration):.2f} s"
                except Exception:
                    duration_text = str(duration)

            device_id = device.get("id")
            iid = str(device_id) if device_id is not None else f"row_{index}"

            if self.device_table.exists(iid):
                iid = f"{iid}_{index}"

            self.device_table.insert(
                "",
                "end",
                iid=iid,
                values=(
                    device_id if device_id is not None else "",
                    device.get("ip") or "",
                    device.get("hostname") or "",
                    device.get("mac") or "",
                    status_text,
                    duration_text,
                    device.get("first_seen") or "",
                    device.get("last_seen") or "",
                ),
                tags=(tag,)
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
            "Thêm thiết bị"
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
            text="Thêm thiết bị mới",
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
            text="Tên máy",
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
            text="Địa chỉ MAC",
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
            text="Trạng thái",
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
                    "Thêm thiết bị",
                    result.get(
                        "message",
                        "Cannot add device."
                    ),
                    parent=dialog
                )

        tk.Button(
            button_frame,
            text="Lưu",
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
            text="Hủy",
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

    def get_selected_device_ids(self):
        """Lấy danh sách ID của tất cả các dòng đang được chọn"""
        if self.device_table is None:
            return []

        selection = self.device_table.selection()
        if not selection:
            return []

        ids = []
        for item_id in selection:
            try:
                values = self.device_table.item(item_id, "values")
                if values and values[0]:
                    ids.append(int(values[0]))
            except Exception:
                try:
                    ids.append(int(item_id))
                except Exception:
                    pass
        return ids

    def get_selected_device_id(self):
        """Lấy ID của dòng đầu tiên được chọn (dùng cho Edit)"""
        ids = self.get_selected_device_ids()
        return ids[0] if ids else None

    def select_all_devices(self):
        """Chọn tất cả các thiết bị trên bảng"""
        if self.device_table is not None:
            children = self.device_table.get_children()
            self.device_table.selection_set(children)

    def deselect_all_devices(self):
        """Bỏ chọn tất cả"""
        if self.device_table is not None:
            selected = self.device_table.selection()
            if selected:
                self.device_table.selection_remove(selected)

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
                "Sửa thiết bị",
                "Please select a device."
            )

            return

        device = device_manager.get_device(
            device_id
        )
        if device is not None:
            device = self._normalize_device_record(device)

        if device is None:

            messagebox.showerror(
                "Sửa thiết bị",
                "Device not found."
            )

            self.refresh_device_manager()

            return

        dialog = tk.Toplevel(
            self.root
        )

        dialog.title(
            "Sửa thiết bị"
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
            text="Sửa thiết bị",
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
            str(device.get("ip") or "")
        )

        ip_entry.grid(
            row=1,
            column=0,
            padx=15,
            pady=(0, 10)
        )

        tk.Label(
            form,
            text="Tên máy",
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
            text="Địa chỉ MAC",
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
            text="Trạng thái",
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
                    "Sửa thiết bị",
                    result.get(
                        "message",
                        "Cannot update device."
                    ),
                    parent=dialog
                )

        tk.Button(
            button_frame,
            text="Lưu",
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
            text="Hủy",
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

    def delete_selected_devices(self):
        """Xóa hàng loạt các thiết bị đang được chọn"""
        device_ids = self.get_selected_device_ids()

        if not device_ids:
            messagebox.showwarning(
                "Delete Devices",
                "Vui lòng chọn ít nhất một thiết bị để xóa."
            )
            return

        confirm = messagebox.askyesno(
            "Delete Devices",
            f"Bạn có chắc muốn xóa {len(device_ids)} thiết bị đã chọn không?"
        )

        if not confirm:
            return

        success_count = 0
        fail_count = 0

        for device_id in device_ids:
            try:
                result = device_manager.remove_device(device_id)
                if result and result.get("success"):
                    success_count += 1
                else:
                    fail_count += 1
            except Exception:
                fail_count += 1

        self.add_activity(f"Deleted {success_count} devices in bulk.")
        self.refresh_device_manager()

        if fail_count > 0:
            messagebox.showwarning(
                "Delete Devices",
                f"Đã xóa thành công {success_count} thiết bị, thất bại {fail_count} thiết bị."
            )
        else:
            messagebox.showinfo(
                "Delete Devices",
                f"Đã xóa thành công {success_count} thiết bị đã chọn."
            )

    # ======================================================
    # PING MONITOR
    # ======================================================

    def show_ping_monitor(self):

        self.current_page = "Giám sát Ping"

        self.clear_content()

        self.set_page_title(
            "Giám sát Ping",
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
            "192.168.2.3\n"
            "192.168.2.10\n"
            "192.168.2.20"
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
            text="Ping tất cả",
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
            text="Bắt đầu Ping tự động",
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

        # Nút mới: Tải IP từ Device Manager
        load_devices_button = tk.Button(
            button_frame,
            text="Nạp từ thiết bị",
            command=self.load_ips_from_device_manager,
            bg="#4B5563",
            fg="white",
            activebackground="#374151",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=15,
            pady=8,
            cursor="hand2",
            font=(
                "Segoe UI",
                10
            )
        )
        load_devices_button.pack(
            side="left",
            padx=10
        )

        self.interval_var = tk.StringVar(
            value=get_setting("ping_interval_sec", "5")
        )

        tk.Label(
            button_frame,
            text="Chu kỳ:",
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
            text="Xóa",
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
            text="Sẵn sàng",
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
            text="Thời gian"
        )

        self.ping_table.heading(
            "ip",
            text="Địa chỉ IP"
        )

        self.ping_table.heading(
            "status",
            text="Trạng thái"
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

    def load_ips_from_device_manager(self):
        """Hàm xử lý lấy danh sách IP từ cơ sở dữ liệu (Device Manager) điền vào ô Ping"""
        try:
            raw_devices = get_all_devices() or []
            ips = []
            for row in raw_devices:
                device = self._normalize_device_record(row)
                if device and device.get("ip"):
                    ip = str(device.get("ip")).strip()
                    if ip and ip not in ips:
                        ips.append(ip)

            if not ips:
                messagebox.showwarning(
                    "Load Devices",
                    "Không tìm thấy IP nào trong Device Manager."
                )
                return

            self.ping_entry.delete("1.0", tk.END)
            self.ping_entry.insert("1.0", "\n".join(ips))

            self.ping_status_label.config(
                text=f"Đã tải {len(ips)} IP từ Device Manager."
            )
            self.add_activity(f"Loaded {len(ips)} IPs from Device Manager into Ping Monitor.")
        except Exception as error:
            messagebox.showerror(
                "Error",
                f"Không thể tải IP từ Device Manager: {error}"
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
            text="Dừng Ping tự động",
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
                        text="Bắt đầu Ping tự động",
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

    def show_ip_mac_manager(self):

        self.current_page = "Quản lý IP / MAC"
        self.clear_content()
        self.set_page_title(
            "Quản lý IP / MAC",
            "Phát hiện, theo dõi và ghi chú ánh xạ IP/MAC trong mạng LAN"
        )
        self.ip_mac_manager_page = IPMacManagerPage(
            self.content,
            activity_callback=self.add_activity
        )

    def show_noc_dashboard(self):
        self.clear_content(); self.current_page = "Trung tâm giám sát NOC"
        self.set_page_title("Trung tâm giám sát NOC", "Tổng quan vận hành thiết bị, cảnh báo và giám sát SNMP")
        self.noc_dashboard_page = NOCDashboardPage(self.content, activity_callback=self.add_activity)

    def show_auto_discovery(self):
        self.clear_content(); self.current_page = "Tự động phát hiện"
        self.set_page_title("Tự động phát hiện", "Tìm thiết bị trực tuyến và thêm vào danh sách quản lý")
        self.auto_discovery_page = AutoDiscoveryPage(self.content, activity_callback=self.add_activity)

    def show_multi_port_monitor(self):
        self.clear_content(); self.current_page = "Giám sát nhiều cổng"
        self.set_page_title("Giám sát nhiều cổng", "Theo dõi nhiều cổng switch bằng SNMP v2c")
        self.multi_port_monitor_page = MultiPortMonitorPage(self.content, activity_callback=self.add_activity)

    def show_resource_monitor(self):
        self.clear_content(); self.current_page = "CPU / RAM SNMP"
        self.set_page_title("CPU / RAM SNMP", "Theo dõi tài nguyên thiết bị bằng OID SNMP theo hãng hoặc OID tùy chỉnh")
        self.resource_monitor_page = ResourceMonitorPage(self.content, activity_callback=self.add_activity)

    def show_advanced_port_monitor(self):
        self.clear_content(); self.current_page = "Giám sát cổng nâng cao"
        self.set_page_title("Giám sát cổng nâng cao", "Trạng thái, tốc độ, lỗi và discard trên từng interface")
        self.advanced_port_monitor_page = AdvancedPortMonitorPage(self.content, activity_callback=self.add_activity)

    def show_alert_rules(self):
        self.clear_content(); self.current_page = "Quy tắc cảnh báo"
        self.set_page_title("Quy tắc cảnh báo", "Tự động tạo cảnh báo khi chỉ số vượt ngưỡng đã đặt")
        self.alert_rules_page = AlertRulesPage(self.content, activity_callback=self.add_activity)

    def show_history_charts(self):
        self.clear_content(); self.current_page = "Biểu đồ lịch sử"
        self.set_page_title("Biểu đồ lịch sử", "Xem dữ liệu SNMP/CPU/RAM trong 24 giờ, 7 ngày hoặc 30 ngày")
        self.history_charts_page = HistoryChartsPage(self.content, activity_callback=self.add_activity)

    def show_network_health(self):
        self.clear_content(); self.current_page = "Sức khỏe mạng"
        self.set_page_title("Sức khỏe mạng", "Kiểm tra độ trễ, mất gói, uptime và thông tin SNMP của thiết bị")
        self.network_health_page = NetworkHealthPage(self.content, activity_callback=self.add_activity)

    def show_backup_scheduler(self):
        self.clear_content(); self.current_page = "Lịch sao lưu"
        self.set_page_title("Lịch sao lưu", "Lập lịch tự động sao lưu cấu hình qua SSH")
        self.backup_scheduler_page = BackupSchedulerPage(self.content, activity_callback=self.add_activity)

    def show_network_devices(self):

        self.current_page = "Thiết bị mạng"
        self.clear_content()
        self.set_page_title("Thiết bị mạng", "Quản lý router, switch, AP và các thiết bị hạ tầng")
        self.network_devices_page = NetworkDevicesPage(self.content, activity_callback=self.add_activity)


    def show_device_profiles(self):
        self.current_page = "Hồ sơ thiết bị theo hãng"
        self.clear_content()
        self.set_page_title("Hồ sơ thiết bị theo hãng", "Tự nhận diện Cisco/MikroTik/Ruijie/Aruba-HPE và áp dụng OID/lệnh backup phù hợp")
        self.device_profiles_page = DeviceProfilesPage(self.content, activity_callback=self.add_activity)


    def show_organization(self):
        self.current_page = "Site / Nhóm / VLAN"
        self.clear_content()
        self.set_page_title("Site / Nhóm / VLAN", "Tổ chức thiết bị theo địa điểm, nhóm nghiệp vụ, VLAN và tags")
        self.organization_page = OrganizationPage(self.content, activity_callback=self.add_activity)

    def show_maintenance_windows(self):
        self.current_page = "Lịch bảo trì"
        self.clear_content()
        self.set_page_title("Lịch bảo trì", "Tắt cảnh báo theo thiết bị, Site hoặc nhóm trong thời gian bảo trì")
        self.maintenance_windows_page = MaintenanceWindowsPage(self.content, activity_callback=self.add_activity)


    def show_sla_availability(self):
        self.clear_content(); self.current_page = "SLA & Độ sẵn sàng"
        self.set_page_title("SLA & Độ sẵn sàng", "Tính tỷ lệ sẵn sàng theo thiết bị, Site, nhóm và loại trừ thời gian bảo trì")
        self.sla_availability_page = SLAAvailabilityPage(self.content, activity_callback=self.add_activity, role=self.current_role)

    def show_capacity_planning(self):
        self.clear_content(); self.current_page = "Phân tích dung lượng"
        self.set_page_title("Phân tích dung lượng", "Tổng hợp CPU, RAM, latency, packet loss và lỗi cổng theo lịch sử giám sát")
        self.capacity_planning_page = CapacityPlanningPage(self.content, activity_callback=self.add_activity)

    def show_incident_center(self):
        self.clear_content(); self.current_page = "Trung tâm sự cố"
        self.set_page_title("Trung tâm sự cố", "Gom cảnh báo thành sự cố, xác nhận, theo dõi và đóng sự cố")
        self.incident_center_page = IncidentCenterPage(self.content, activity_callback=self.add_activity, role=self.current_role, username=self.session_user.get('username',''))

    def show_device_dependencies(self):
        self.clear_content(); self.current_page = "Phụ thuộc thiết bị"
        self.set_page_title("Phụ thuộc thiết bị", "Khai báo quan hệ cha/con để tương quan cảnh báo và xác định phạm vi ảnh hưởng")
        self.device_dependencies_page = DeviceDependenciesPage(self.content, activity_callback=self.add_activity, role=self.current_role)

    def show_service_impact(self):
        self.clear_content(); self.current_page = "Dịch vụ & Mức ảnh hưởng"
        self.set_page_title("Dịch vụ & Mức ảnh hưởng", "Gom thiết bị theo dịch vụ và đánh giá trạng thái Hoạt động / Suy giảm / Gián đoạn")
        self.service_impact_page = ServiceImpactPage(self.content, activity_callback=self.add_activity, role=self.current_role)

    def show_root_cause_analysis(self):
        self.clear_content(); self.current_page = "Phân tích nguyên nhân gốc"
        self.set_page_title("Phân tích nguyên nhân gốc", "Tương quan cảnh báo theo dependency để giảm bão cảnh báo và tìm thiết bị gốc gây sự cố")
        self.root_cause_analysis_page = RootCauseAnalysisPage(self.content, activity_callback=self.add_activity)


    def show_auto_ip(self):
        if self.current_role not in ("Admin", "Operator"):
            messagebox.showwarning("Phân quyền", "Chỉ Admin/Operator được chạy Tự động IP/Excel.")
            return
        self.clear_content()
        self.current_page = "Tự động IP/Excel"
        self.set_page_title("Tự động IP/Excel", "Chức năng riêng: nhập danh sách, chọn hồ sơ, chạy và theo dõi kết quả")
        if not hasattr(self, "auto_ip_engine"):
            self.auto_ip_engine = AutomationEngine()
        self.auto_ip_page = AutoIPPage(self.content, self.auto_ip_engine, self.session_user, self.add_activity)

    def show_secure_snmp_diagnostics(self):
        self.current_page = "Chẩn đoán SNMP v2c/v3"
        self.clear_content()
        self.set_page_title("Chẩn đoán SNMP v2c/v3", "Kiểm tra SNMPv2c/SNMPv3, nhận diện hãng và thử OID theo driver")
        self.secure_snmp_diagnostics_page = SecureSNMPDiagnosticsPage(self.content, activity_callback=self.add_activity)

    def show_vendor_drivers(self):
        self.current_page = "Vendor Driver Engine"
        self.clear_content()
        self.set_page_title("Vendor Driver Engine", "Driver theo hãng: nhận diện thiết bị, OID tài nguyên, backup và LLDP/CDP")
        self.vendor_driver_page = VendorDriverPage(self.content, activity_callback=self.add_activity)

    def show_snmpv3_credentials(self):
        if self.current_role != "Admin":
            messagebox.showwarning("Phân quyền", "Chỉ Admin được quản lý Credential SNMPv3.")
            return
        self.current_page = "Credential SNMPv3"
        self.clear_content()
        self.set_page_title("Credential SNMPv3", "Quản lý username, Auth/Privacy được mã hóa và gán cho thiết bị")
        self.snmpv3_credentials_page = SNMPv3CredentialsPage(self.content, activity_callback=self.add_activity)

    def show_snmp_monitor(self):

        self.current_page = "Giám sát SNMP"
        self.clear_content()
        self.set_page_title("Giám sát SNMP", "Giám sát SNMP v2c và biểu đồ lưu lượng cổng theo thời gian thực")
        self.snmp_monitor_page = SNMPMonitorPage(self.content, activity_callback=self.add_activity)

    def show_auto_topology(self):

        self.current_page = "Tự dựng Topology LLDP/CDP"
        self.clear_content()
        self.set_page_title("Tự dựng Topology LLDP/CDP", "Phát hiện láng giềng LLDP/CDP qua SNMP và tự thêm liên kết vào sơ đồ mạng")
        self.auto_topology_page = AutoTopologyPage(self.content, activity_callback=self.add_activity)

    def show_network_topology(self):

        self.current_page = "Sơ đồ mạng"
        self.clear_content()
        self.set_page_title("Sơ đồ mạng", "Hiển thị thiết bị và liên kết vật lý hoặc logic")
        self.network_topology_page = NetworkTopologyPage(self.content, activity_callback=self.add_activity)

    def show_ssh_automation(self):

        self.current_page = "Tự động hóa SSH"
        self.clear_content()
        self.set_page_title("Tự động hóa SSH", "Chạy mẫu lệnh và sao lưu cấu hình qua SSH")
        self.ssh_automation_page = SSHAutomationPage(self.content, activity_callback=self.add_activity)

    def show_notifications(self):

        self.current_page = "Thông báo"
        self.clear_content()
        self.set_page_title("Thông báo", "Cấu hình gửi cảnh báo qua Telegram và Email SMTP")
        self.notifications_page = NotificationsPage(self.content, activity_callback=self.add_activity)

    def show_remote_service(self):

        self.current_page = "Truy cập từ xa"
        self.clear_content()
        self.set_page_title("Truy cập từ xa", "Kiểm tra cổng quản trị và mở SSH, Telnet, RDP hoặc Web")
        self.remote_service_page = RemoteServicePage(self.content, activity_callback=self.add_activity)

    def show_backup_config(self):

        self.current_page = "Sao lưu cấu hình"
        self.clear_content()
        self.set_page_title("Sao lưu cấu hình", "Tạo và quản lý bản sao lưu cấu hình thiết bị mạng")
        self.backup_config_page = BackupConfigPage(self.content, activity_callback=self.add_activity)

    def show_scheduler(self):

        self.current_page = "Lịch tác vụ"
        self.clear_content()
        self.set_page_title("Lịch tác vụ", "Chạy định kỳ Ping, kiểm tra TCP và cảnh báo khi ứng dụng đang mở")
        self.scheduler_page = SchedulerPage(self.content, activity_callback=self.add_activity)

    def show_alerts(self):

        self.current_page = "Cảnh báo"
        self.clear_content()
        self.set_page_title("Cảnh báo", "Theo dõi thiết bị ngoại tuyến và cảnh báo vận hành")
        self.alerts_page = AlertsPage(self.content, activity_callback=self.add_activity)

    def show_reports(self):

        self.current_page = "Báo cáo"
        self.clear_content()
        self.set_page_title("Báo cáo", "Tạo báo cáo vận hành và xuất dữ liệu mạng")
        self.reports_page = ReportsPage(self.content, activity_callback=self.add_activity)

    def show_system_logs(self):

        self.current_page = "Nhật ký hệ thống"
        self.clear_content()
        self.set_page_title("Nhật ký hệ thống", "Tìm kiếm và xuất nhật ký hoạt động")
        self.system_logs_page = SystemLogsPage(self.content, activity_callback=self.add_activity)

    def show_settings(self):

        self.current_page = "Cài đặt"
        self.clear_content()
        self.set_page_title("Cài đặt", "Cấu hình mặc định cho quét mạng và giám sát")
        self.settings_page = SettingsPage(self.content, activity_callback=self.add_activity)

    def show_credential_manager(self):
        if self.current_role != "Admin":
            messagebox.showwarning("Phân quyền", "Chỉ Admin được quản lý Credential.")
            return
        self.current_page = "Quản lý Credential"
        self.clear_content()
        self.set_page_title("Quản lý Credential", "Lưu SSH/SNMP credential được mã hóa và gán cho từng thiết bị")
        self.credential_manager_page = CredentialManagerPage(self.content, activity_callback=self.add_activity)

    def show_secure_backup_scheduler(self):
        if self.current_role == "Viewer":
            messagebox.showwarning("Phân quyền", "Viewer không được chạy sao lưu cấu hình.")
            return
        self.current_page = "Lịch sao lưu bảo mật"
        self.clear_content()
        self.set_page_title("Lịch sao lưu bảo mật", "Tự động backup cấu hình SSH bằng credential đã mã hóa")
        self.secure_backup_scheduler_page = SecureBackupSchedulerPage(self.content, activity_callback=self.add_activity)

    def show_config_compare(self):
        self.current_page = "So sánh cấu hình"
        self.clear_content()
        self.set_page_title("So sánh cấu hình", "So sánh hai phiên bản backup và hiển thị thay đổi dạng diff")
        self.config_compare_page = ConfigComparePage(self.content, activity_callback=self.add_activity)

    def show_user_roles(self):
        if self.current_role != "Admin":
            messagebox.showwarning("Phân quyền", "Chỉ Admin được quản lý người dùng và phân quyền.")
            return
        self.current_page = "Người dùng & Phân quyền"
        self.clear_content()
        self.set_page_title("Người dùng & Phân quyền", "Quản lý tài khoản Admin / Operator / Viewer")
        self.user_role_page = UserRolePage(self.content, activity_callback=self.add_activity)

    def show_monitoring_service(self):
        self.current_page = "Dịch vụ giám sát nền"
        self.clear_content(); self.set_page_title("Dịch vụ giám sát nền", "Thu thập Ping/latency/packet loss định kỳ và tự dọn lịch sử")
        MonitoringServicePage(self.content, self.monitoring_service, self.session_user)

    def show_stable_core(self):
        self.current_page = "Sức khỏe hệ thống"
        self.clear_content(); self.set_page_title("Stable Core & Worker Engine", "Worker Queue, chống cảnh báo chập chờn, kiểm tra và bảo trì Database")
        self.stable_core_page = StableCorePage(self.content, self.job_queue_engine, self.session_user)

    def show_audit_log(self):
        self.current_page = "Nhật ký Audit"
        self.clear_content(); self.set_page_title("Nhật ký Audit", "Theo dõi hành động quản trị theo tài khoản")
        AuditLogPage(self.content)

    def show_restore_config(self):
        self.current_page = "Khôi phục cấu hình"
        self.clear_content(); self.set_page_title("Khôi phục cấu hình", "Khôi phục có xác nhận và tạo safety backup trước khi thay đổi")
        RestoreConfigPage(self.content, self.session_user)

    def on_close(self):
        # Drain the new workflow without blocking Tk or abandoning its DB writes.
        if hasattr(self, "auto_ip_engine") and self.auto_ip_engine.running:
            self.auto_ip_engine.stop()
            self.root.title("Đang dừng Tự động IP/Excel...")
            self.root.after(250, self.on_close)
            return
        if hasattr(self, "auto_ip_page"):
            self.auto_ip_page.destroy()
        try: self.job_queue_engine.stop()
        except Exception: pass
        try: self.monitoring_service.stop()
        except Exception: pass
        try: self.background_alert_engine.stop()
        except Exception: pass
        try: self.root_cause_engine.stop()
        except Exception: pass
        try: audit(self.session_user.get('username'), self.current_role, 'Đóng ứng dụng', 'Network Automation', 'Kết thúc phiên làm việc')
        except Exception: pass
        self.root.destroy()

    def show_placeholder(self):

        self.current_page = "Sắp có"

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
            text="Sắp có",
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
    ensure_v5_tables()

    root = tk.Tk()
    root.withdraw()

    # Nếu chưa có tài khoản cục bộ, cho phép bootstrap bằng local-admin.
    # Sau khi Admin đầu tiên được tạo, những lần mở sau bắt buộc đăng nhập.
    session_user = LoginDialog(root).run()
    if session_user is None:
        root.destroy()
    else:
        root.deiconify()
        app = NetworkAutomationApp(root, session_user=session_user)
        root.mainloop()
