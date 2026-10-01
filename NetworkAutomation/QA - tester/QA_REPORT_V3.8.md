# QA REPORT - Network Automation NMS v3.8

## Phạm vi nâng cấp
- Quản lý Site cho thiết bị mạng.
- Quản lý nhóm thiết bị.
- Gán Site / Nhóm / VLAN / Tags cho từng thiết bị.
- Lịch bảo trì theo Device / Site / Group / All.
- Alert Rules tự bỏ qua thiết bị đang nằm trong lịch bảo trì có hiệu lực.
- Migration database tự tạo các bảng v3.8, không yêu cầu xóa database cũ.

## Kết quả test tự động
- Compile toàn bộ source: PASS.
- Regression test v3.8: PASS.
- Migration schema v3.8: PASS.
- Credential encryption + password hashing: PASS.
- Alert engine: PASS.
- Device Profile: PASS.
- Site/Group/Maintenance schema: PASS.
- Import ứng dụng: PASS.
- Phát hiện maintenance window đang hiệu lực: PASS.

## GUI smoke test
Đã khởi tạo tuần tự **36/36 màn hình** dưới Tkinter/Xvfb: PASS, bao gồm hai màn hình mới:
- Site / Nhóm / VLAN.
- Lịch bảo trì.

## Giới hạn cần test trên hệ thống thật
- SNMP/SSH/LLDP/CDP vẫn cần thiết bị lab thật để kiểm thử end-to-end.
- Lịch bảo trì v3.8 áp dụng cho Alert Rules nền; các cảnh báo được tạo thủ công hoặc từ module khác không tự động bị chặn.
- Site/Group/VLAN/Tags hiện là dữ liệu quản trị nội bộ của NMS, chưa tự đồng bộ VLAN từ switch.
