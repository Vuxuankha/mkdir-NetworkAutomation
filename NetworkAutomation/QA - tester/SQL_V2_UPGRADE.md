# SQL v2 Upgrade

Bản này nâng lớp SQLite của NetworkAutomation theo hướng ổn định hơn cho NOC/monitoring.

## Thay đổi chính

- Bật WAL để đọc/ghi đồng thời tốt hơn giữa Dashboard, Scheduler, Monitoring và Notification.
- `busy_timeout=5000ms` để giảm lỗi `database is locked` khi nhiều worker ghi gần nhau.
- Bật `foreign_keys`, `synchronous=NORMAL`, `temp_store=MEMORY` và cache SQLite hợp lý.
- Thêm `schema_migrations` + `PRAGMA user_version` để quản lý phiên bản schema.
- Tự tạo backup DB trước lần nâng SQL schema đầu tiên vào `database/db_backups/`.
- Thêm index cho các truy vấn nóng: thiết bị/status, alerts, health/SNMP history, server monitor, audit log, backup, worker jobs, config audit.
- Thêm expression index cho trạng thái Dashboard (`LOWER(COALESCE(status,''))`).
- Chuẩn hóa các module chính dùng chung `database.db.get_connection()` thay vì mỗi module mở SQLite theo cấu hình riêng.
- Mục Stable Core / Database Health hiển thị thêm WAL, schema version, số index và dung lượng DB.
- Nút Tối ưu Database dùng `PRAGMA optimize` và VACUUM qua lớp database chung.

## Tương thích dữ liệu

Migration là non-destructive: không xóa bảng, không xóa record và không ép UNIQUE lên dữ liệu legacy. Các bảng cũ vẫn được giữ nguyên để các chức năng hiện hữu tiếp tục chạy.

## Kết quả kiểm thử

- Python compile: PASS
- Regression suite: PASS
- SQLite quick_check: `ok`
- Journal mode: `wal`
- Query plan cho Dashboard device status và lịch sử Server Monitor/Health đã sử dụng index mới.
