# Auto Audit Scheduler

- Thêm scheduler audit SSH cấu hình hằng ngày trong Baseline & Security.
- Cấu hình: bật/tắt, giờ HH:MM, 1-8 kết nối song song, lệnh read-only.
- Chỉ chạy thiết bị đã gán SSH credential.
- Pipeline: running-config -> baseline drift -> security posture -> audit history -> NOC alerts.
- Có nút Chạy ngay và bảng `auto_audit_runs` lưu lịch sử đợt chạy.
- Chống alert trùng kế thừa từ auto_config_audit.
- Không tự thay đổi cấu hình và không tự tạo baseline.
