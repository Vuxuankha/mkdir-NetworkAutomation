# Network Automation v1.0 for Windows

## Mục tiêu bản v1.0

- Chạy như ứng dụng Windows GUI, không có cửa sổ CMD khi mở app.
- Các probe nền như Ping/ARP/PowerShell chạy ẩn, không nháy console.
- Vẫn lưu stdout/stderr/lỗi vào `%LOCALAPPDATA%\NetworkAutomation\logs`.
- Database, credential key, reports và backups nằm trong `%LOCALAPPDATA%\NetworkAutomation`, không ghi vào `Program Files`.
- Uninstall/cập nhật ứng dụng không tự xóa dữ liệu vận hành.
- PyInstaller build dạng **onedir** để khởi động nhanh và ổn định hơn onefile với pandas/openpyxl/cryptography.
- Inno Setup tạo `NetworkAutomation_Setup_v1.0.0.exe`, shortcut Start Menu/Desktop và uninstall chuẩn Windows.

## Build trên Windows

1. Cài Python 64-bit (khuyến nghị 3.11-3.13).
2. Giải nén source vào một thư mục ngắn, ví dụ `C:\Build\NetworkAutomation`.
3. Chạy `BUILD_WINDOWS.bat`.
4. Script tự tạo virtualenv, cài dependencies, chạy compile + regression test và build EXE.
5. Nếu máy có Inno Setup 6, script tạo luôn `release\NetworkAutomation_Setup_v1.0.0.exe`.

Nếu chưa có Inno Setup, EXE vẫn nằm tại:

`dist\NetworkAutomation\NetworkAutomation.exe`

Sau khi cài Inno Setup 6, chạy `BUILD_INSTALLER.bat`.

## Dữ liệu runtime

Bản cài đặt dùng:

- Database: `%LOCALAPPDATA%\NetworkAutomation\database\network_automation.db`
- Credential key: `%LOCALAPPDATA%\NetworkAutomation\database\.credential.key`
- Log: `%LOCALAPPDATA%\NetworkAutomation\logs\network_automation.log`
- Console capture: `%LOCALAPPDATA%\NetworkAutomation\logs\console_capture.log`
- Reports: `%LOCALAPPDATA%\NetworkAutomation\reports`
- Backups: `%LOCALAPPDATA%\NetworkAutomation\backups`

Không xóa `.credential.key` nếu database còn chứa credential mã hóa.

## Chuyển dữ liệu từ bản cũ

Trước lần chạy đầu tiên của bản EXE, có thể copy thư mục `database` của bản cũ cạnh `NetworkAutomation.exe`. App sẽ copy `network_automation.db`, `.credential.key` và `known_hosts` sang AppData nếu đích chưa tồn tại. App không ghi đè dữ liệu AppData đã có.

Một cách an toàn hơn là tự copy hai file sau khi đóng app:

- `database\network_automation.db`
- `database\.credential.key`

vào `%LOCALAPPDATA%\NetworkAutomation\database\`.

## CMD/console

`NetworkAutomation.spec` đặt `console=False`, nên EXE chỉ hiện GUI. Các lệnh nền được gọi bằng `CREATE_NO_WINDOW` trên Windows. Các chức năng mà người dùng chủ động yêu cầu mở terminal tương tác (ví dụ SSH/Telnet terminal) vẫn có thể mở cửa sổ riêng theo đúng mục đích.

## Chẩn đoán lỗi

Nếu app không mở hoặc một callback lỗi, xem:

`%LOCALAPPDATA%\NetworkAutomation\logs\network_automation.log`

Nếu thư viện bên thứ ba có `print()` trong bản windowed, output được giữ tại `console_capture.log` thay vì mất hoàn toàn.
