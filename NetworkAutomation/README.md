# NetworkAutomation 1.5.0

Ứng dụng Windows quản lý và giám sát mạng, giao diện tối thống nhất. Bản 1.4.0 đã gỡ toàn bộ chức năng AI.

## Chạy mã nguồn trên Windows 11
- Cài Python 64-bit và thư viện bằng `py -3 -m pip install -r requirements.txt`.
- Chạy `START_WINDOWS.bat` từ thư mục chương trình.
- Tài khoản và menu Avatar: `UPDATE_1.5.0.md`.
- Chi tiết sửa lỗi Thêm/Sửa thiết bị: `UPDATE_1.4.1.md`. Hướng dẫn giao diện: `UPDATE_1.4.0.md`.
- Dựng EXE: `BUILD_WINDOWS.bat`; dựng bộ cài: `BUILD_INSTALLER.bat`.

## Chức năng
- Tổng quan NOC, quản lý thiết bị, IP/MAC, khám phá mạng và ping.
- Giám sát cổng, tài nguyên, SNMP v2/v3, Application/Server, Wi-Fi và camera.
- Sơ đồ mạng, cảnh báo, sự cố, SLA, phụ thuộc thiết bị và ảnh hưởng dịch vụ.
- Tự động IP/Excel, SSH, sao lưu cấu hình, Daily Audit Windows và baseline/security.
- Báo cáo, nhật ký, hồ sơ thiết bị, tài khoản/phân quyền và quản trị dịch vụ.

## Dữ liệu và cập nhật
Giữ nguyên database đang dùng, khóa `.credential.key` và `data_location.json` nếu có. Không chép đè database từ ZIP lên dữ liệu hiện tại. Khi chép mã nguồn mới lên thư mục cũ, có thể chạy `REMOVE_OLD_AI_MODULES.bat` để dọn các file mã AI đã bỏ.

Thư mục dữ liệu được xác định bởi `NETWORK_AUTOMATION_DATA_DIR`, hoặc `data_location.json`, hoặc mặc định của ứng dụng. Hướng dẫn Windows: `WINDOWS_V1_RELEASE.md`. Cài giám sát nền: `UPDATE_1.1.0.md`, `INSTALL_MONITOR_SERVICE.bat`; cần Python/pywin32 và cấu hình dữ liệu nhất quán.

## Kiểm tra giao diện
`py -3 tests/ui_all_pages_smoke.py` mở 57 trang ở kích thước 1400×800 và 800×600 với dữ liệu tạm và các engine nền bị tắt. Chỉ dựng giao diện; không bấm lệnh kiểm tra/SSH hay sửa thiết bị thật. Script chưa được chạy trong môi trường không có display tại đây.

`py -3 tests/ui_accounts_smoke.py` kiểm tra menu cá nhân, tạo/sửa/phân quyền tài khoản trong database tạm, các hộp nhập ở cửa sổ nhỏ và thao tác đăng xuất. Chưa chạy GUI tại môi trường hiện tại.
