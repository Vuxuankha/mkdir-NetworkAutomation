# QA REPORT v3.12 - SNMPv3 & Vendor Driver Engine

## Phạm vi nâng cấp
- Schema SNMPv3 credential và gán credential theo thiết bị.
- Mã hóa Auth/Privacy password bằng Fernet.
- SNMPv3 GET qua pysnmp, có compatibility path cho API mới và API cũ.
- Vendor Driver Engine và nhận diện Cisco/MikroTik/Ruijie/Aruba-HPE/Generic.
- Chẩn đoán SNMP v2c/v3 và lưu lịch sử chẩn đoán.
- Driver tùy chỉnh, OID CPU/RAM, backup/save command và LLDP/CDP mode.

## Kết quả QA
- Compile toàn bộ source: PASS.
- Regression v3.12: 11/11 nhóm PASS.
- Migration database v3.12: PASS, không yêu cầu xóa database cũ.
- Seed 5 vendor driver mặc định: PASS.
- Nhận diện Cisco bằng sysObjectID/sysDescr: PASS.
- Nhận diện MikroTik bằng sysObjectID/sysDescr: PASS.
- Mã hóa/giải mã Auth và Privacy secret: PASS.
- Gán driver theo thiết bị: PASS.
- Gán SNMPv3 credential theo thiết bị: PASS.
- Import ứng dụng: PASS.
- GUI smoke test: 47/47 màn hình PASS.

## Giới hạn kiểm thử
Môi trường QA không có router/switch thật và không có SNMP agent SNMPv3 đang hoạt động, vì vậy xác thực end-to-end AuthPriv với Cisco/MikroTik/Ruijie/Aruba vật lý chưa được xác nhận. Logic SNMPv3 đã được kiểm tra ở mức import/schema/credential/driver và đường gọi được thiết kế cho `pysnmp>=7.1`.

Khi triển khai thực tế, cần đảm bảo thuật toán Auth/Privacy được thiết bị hỗ trợ. Một số firmware chỉ hỗ trợ SHA/AES128 hoặc MD5/DES; một số thiết bị không hỗ trợ SHA2/AES256.
