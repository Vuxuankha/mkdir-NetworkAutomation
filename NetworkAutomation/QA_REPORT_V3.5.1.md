# Báo cáo kiểm thử Network Automation NMS v3.5.1

Ngày kiểm thử: 2026-09-30

## Phạm vi đã kiểm thử

- Compile toàn bộ source Python.
- Migration database cũ/mới và các bảng NMS.
- Khởi tạo lần lượt 30 màn hình chức năng dưới quyền Admin.
- CRUD thiết bị, tìm kiếm, lọc trạng thái, thống kê, upsert kết quả quét.
- Mã hóa/giải mã Credential bằng Fernet.
- Hash/xác thực mật khẩu PBKDF2-SHA256 và đăng nhập đúng/sai.
- Parse Ping Windows bằng dữ liệu mô phỏng Online/Offline.
- Network Scan bằng Ping/Hostname/MAC mô phỏng.
- SNMP timeout: chuyển từ `timed out` sang thông báo tiếng Việt có nguyên nhân UDP/161.
- Luồng CPU/RAM SNMP bằng thiết bị Cisco mô phỏng: phát hiện thiết bị, tự chọn preset, đọc CPU.
- Alert Rules: chuyển trạng thái bình thường -> vi phạm -> phục hồi, tạo/đóng cảnh báo đúng.
- Kiểm tra schema trên database đi kèm project sau migration.

## Lỗi phát hiện và đã sửa

1. Callback Tkinter dùng biến exception sau `except`, gây `NameError` trên Python 3.14.
2. NOC Dashboard có thể mở trước khi bảng `snmp_profiles` được tạo.
3. Database cũ có thể thiếu `alerts.severity`.
4. Alert Rules dùng `Connection.rowcount` thay vì `Cursor.rowcount` khi đóng cảnh báo.
5. `LoginDialog` đã có nhưng chưa được gọi trong luồng khởi động chính.
6. SNMP timeout chỉ hiện thông báo `timed out`, không giúp phân biệt Ping với SNMP.

## Kết quả tự động

- Smoke test giao diện: 30/30 màn hình khởi tạo thành công.
- Bộ test lõi: PASS toàn bộ các ca kiểm thử đã thực hiện.
- Compile: PASS.

## Những phần cần thiết bị thật để kiểm thử end-to-end

Các luồng sau đã được kiểm tra cấu trúc code/giao diện và các phần logic có thể mô phỏng, nhưng để xác nhận 100% cần môi trường mạng thật:

- SNMP v2c với đúng OID CPU/RAM theo model Cisco/MikroTik/Ruijie/Aruba/HPE.
- LLDP/CDP walk trên switch/router thật.
- SSH Automation và Secure Backup với thiết bị thật.
- Remote RDP/Telnet/SSH bằng client Windows thật.
- Telegram/SMTP bằng token/tài khoản thật.
- Topology nhiều switch và traffic counter thực tế.

Khi test thực địa, nên dùng một VLAN/lab riêng trước, bật SNMP read-only và một tài khoản SSH hạn chế quyền nếu có thể.
