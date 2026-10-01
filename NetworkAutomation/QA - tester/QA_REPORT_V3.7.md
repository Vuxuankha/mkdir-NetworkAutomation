# QA REPORT - Network Automation NMS v3.7

## Phạm vi nâng cấp
- Device Profile theo hãng: Cisco, MikroTik, Ruijie/Reyee, Aruba/HPE, Generic HOST-RESOURCES.
- Tự nhận diện profile bằng SNMP `sysDescr` + `sysObjectID`.
- Gán profile thủ công/tự động cho `network_devices`.
- CPU/RAM SNMP có thể dùng **Theo hồ sơ thiết bị** và tự nạp OID profile khi kiểm tra SNMP.
- Lịch sao lưu bảo mật tự chọn lệnh backup theo profile thiết bị.
- Hỗ trợ thêm profile tùy chỉnh.

## Kết quả test tự động
- Compile toàn bộ source: PASS.
- Migration schema v3.7: PASS.
- Mã hóa Credential + hash mật khẩu: PASS.
- Alert engine: PASS.
- Nhận diện profile Cisco/MikroTik bằng chuỗi SNMP: PASS.
- Import ứng dụng: PASS.

## GUI smoke test
Đã khởi tạo lần lượt **35/35 màn hình** bằng Tkinter trong môi trường Xvfb: PASS, bao gồm màn hình mới **Hồ sơ thiết bị theo hãng**.

## Giới hạn cần test với thiết bị thật
- SNMP/LLDP/CDP end-to-end cần thiết bị lab thật và community hợp lệ.
- OID CPU/RAM thay đổi theo model/firmware. Ruijie và Aruba/HPE mặc định không ép OID CPU/RAM khi chưa chắc chắn.
- Lệnh backup/restore có thể khác theo OS/firmware; cần xác nhận trước khi dùng production.
