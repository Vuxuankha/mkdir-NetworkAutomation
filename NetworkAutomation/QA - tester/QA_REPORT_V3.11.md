# QA REPORT v3.11 - Stable Core & Worker Engine

## Phạm vi nâng cấp
- Worker Queue đa luồng cho tác vụ mạng, có retry và exponential backoff.
- Chống trạng thái Online/Offline chập chờn: mặc định 3 lần lỗi liên tiếp mới Offline, 2 lần thành công mới Online.
- Màn hình Sức khỏe hệ thống: Database, Worker, thiết bị và hàng đợi.
- SQLite quick_check, PRAGMA optimize + VACUUM.
- Backup SQLite an toàn bằng SQLite Backup API, tự giữ số bản gần nhất.
- Lịch sử worker job và system health trong database.

## Kết quả QA
- Compile toàn bộ: PASS.
- Regression v3.11: 10/10 nhóm PASS.
- Migration v3.11: PASS, không yêu cầu xóa database cũ.
- Stable Core/Worker: PASS.
- Database quick_check + backup: PASS.
- Debounce trạng thái 3 lỗi -> Offline, 2 OK -> Online: PASS.
- GUI smoke test: 44/44 màn hình PASS.

## Giới hạn kiểm thử
Không có thiết bị Cisco/MikroTik/Ruijie/Aruba thật trong môi trường QA, vì vậy SNMP/SSH/LLDP/CDP end-to-end trên thiết bị vật lý chưa được xác nhận. Worker engine hiện là nền tảng dùng chung; các module mạng cũ sẽ được chuyển dần sang queue để giảm rủi ro thay đổi lớn trong một phiên bản.
