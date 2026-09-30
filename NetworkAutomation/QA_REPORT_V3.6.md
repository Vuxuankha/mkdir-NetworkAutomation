# QA REPORT - Network Automation NMS v3.6

Ngày kiểm thử: 2026-09-30

## Kết quả tự động
- Compile toàn bộ source: PASS
- Migration bảng v3.6 (`audit_log`, `monitoring_settings`, `restore_history`): PASS
- Fernet encrypt/decrypt + PBKDF2 password verify: PASS
- Alert engine smoke test: PASS
- Import ứng dụng: PASS
- GUI smoke test v3.6 dưới virtual display: PASS
- Khởi tạo tuần tự toàn bộ 34 màn hình `show_*`: 34/34 PASS

## Phạm vi chưa thể xác nhận end-to-end trong môi trường test
- SSH backup/restore trên router/switch thật.
- SNMP/LLDP/CDP với model thiết bị thực tế của người dùng.
- Telegram/SMTP/RDP/Telnet tới dịch vụ bên ngoài.

Các luồng trên đã được kiểm tra import, UI và xử lý lỗi, nhưng cần test lab với thiết bị thật trước production.

## Lưu ý Restore
Restore là thao tác có thể làm mất kết nối. v3.6 giới hạn cho Admin, yêu cầu xác nhận và tạo safety backup trước khi gửi cấu hình. Cú pháp restore hiện theo CLI kiểu Cisco (`configure terminal`, `end`, `write memory`); thiết bị hãng khác cần profile restore riêng ở bản sau.
