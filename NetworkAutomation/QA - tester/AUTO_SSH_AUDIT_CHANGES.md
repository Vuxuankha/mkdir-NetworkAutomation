# Auto SSH Configuration Audit

## Luồng mới
1. Mở **Baseline & Security**.
2. Bấm **SSH → Audit**.
3. Chọn thiết bị đã được gán credential SSH/Backup.
4. Ứng dụng chạy lệnh read-only `show running-config`.
5. Running-config được so với Configuration Baseline và chạy Security Posture.
6. Kết quả được lưu vào `config_audit_history`.
7. Configuration drift và Security Posture mức HIGH được đưa vào bảng `alerts` để xuất hiện trên NOC Dashboard.

## An toàn
- Không tự sửa cấu hình thiết bị.
- Không tự tạo baseline khi chưa có baseline đã được người vận hành xác minh.
- Credential tiếp tục dùng cơ chế mã hóa hiện có.
- Alert giống hệt đang mở sẽ không được tạo lặp.
- Lệnh mặc định là `show running-config`; người vận hành có thể đổi lệnh read-only phù hợp vendor.

## File mới
- `modules/auto_config_audit.py`

## File cập nhật
- `modules/security_audit.py`
