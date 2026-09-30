# QA REPORT - Network Automation NMS v3.9

## Phạm vi nâng cấp
- SLA & Độ sẵn sàng theo All / Device / Site / Group.
- Loại trừ mẫu SLA trong Maintenance Window.
- Trung tâm sự cố: gom cảnh báo theo Host, Acknowledge, Resolve, tự đóng khi alert đã phục hồi.
- Phân tích dung lượng: CPU, RAM, latency, packet loss, interface errors/discards và xu hướng.
- Regression test snapshot/restore database để không làm bẩn dữ liệu vận hành.

## Kết quả kiểm thử
- Compile toàn bộ Python: **PASS**.
- Migration v3.9: **PASS**.
- Mã hóa credential + xác thực mật khẩu: **PASS**.
- Alert Engine: **PASS**.
- Device Profile: **PASS**.
- Site / Group / Maintenance: **PASS**.
- SLA / Incident / Capacity logic: **PASS**.
- Kiểm tra scope All / Device / Site / Group: **PASS**.
- Import ứng dụng: **PASS**.
- GUI smoke test Admin: **39/39 màn hình PASS**.

## Giới hạn kiểm thử
Các chức năng cần thiết bị thật hoặc dịch vụ ngoài như SNMP theo từng model, LLDP/CDP, SSH backup/restore, Telegram/SMTP, RDP/Telnet vẫn cần kiểm tra end-to-end trong mạng lab của người dùng. QA hiện tại xác nhận schema, logic nội bộ, import và khởi tạo GUI; không giả định rằng thiết bị bên ngoài hỗ trợ protocol/OID/CLI cụ thể.

## Khuyến nghị trước production
1. Sao lưu thư mục `database/` và đặc biệt `.credential.key`.
2. Chạy `python regression_test.py` khi ứng dụng đang đóng.
3. Bật Monitoring Service đủ lâu để SLA/Capacity có dữ liệu đại diện.
4. Kiểm tra Maintenance Window đúng Site/Group trước khi dùng SLA làm báo cáo chính thức.
