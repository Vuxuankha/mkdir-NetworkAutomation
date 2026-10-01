# v3.13 - Tự động IP/Excel

Chức năng riêng trong nhóm TỰ ĐỘNG HÓA. Xem **HUONG_DAN_AUTO_IP_EXCEL.md** và **NANG_CAP_V3.13.md**.

---

# Network Automation NMS v3.12 - SNMPv3 & Vendor Driver Engine

Ứng dụng NMS/Network Automation giao diện tiếng Việt. v3.12 kế thừa toàn bộ v3.11 Stable Core & Worker Engine và bổ sung bảo mật SNMPv3 cùng Vendor Driver Engine theo hãng.

## Chạy ứng dụng
```bash
pip install -r requirements.txt
python main.py
```

## Điểm mới v3.12
- Credential SNMPv3 mã hóa Auth/Privacy password bằng Fernet.
- Hỗ trợ security level: `noAuthNoPriv`, `authNoPriv`, `authPriv`.
- Hỗ trợ Auth MD5/SHA/SHA224/SHA256/SHA384/SHA512 và Privacy DES/AES128/AES192/AES256 tùy khả năng thiết bị và pysnmp.
- Màn hình **Chẩn đoán SNMP v2c/v3** để kiểm tra kết nối, đọc sysName/sysDescr/sysObjectID/uptime và nhận diện driver.
- **Vendor Driver Engine** cho Cisco, MikroTik, Ruijie/Reyee, Aruba/HPE và Generic HOST-RESOURCES.
- Tự nhận diện driver bằng `sysObjectID` hoặc regex `sysDescr`.
- Driver chứa OID CPU/RAM, lệnh backup/save và chế độ LLDP/CDP; có thể tạo driver tùy chỉnh.
- Gán credential SNMPv3 và driver theo từng thiết bị.
- Lưu lịch sử chẩn đoán SNMP để hỗ trợ troubleshooting.

Xem `HUONG_DAN_VI.md` và `QA_REPORT_V3.12.md` để biết chi tiết.

Daily Audit Windows integrated: Event Logs, resources, services, firewall, ports, Defender, accounts, patches, backup.
