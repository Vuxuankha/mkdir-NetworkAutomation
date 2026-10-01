# NetworkAutomation 1.1.0 — Wi-Fi / Camera / dịch vụ nền

Bản mã nguồn mở rộng; cần chạy thử trên Windows và thiết bị thực tế trước khi vận hành chính thức.

## Sử dụng giao diện
- Cài thư viện: `py -3 -m pip install -r requirements.txt`; chạy START_WINDOWS.bat.
- Vào GIÁM SÁT → Wi-Fi / Camera.
- Wi-Fi: đọc netsh wlan interfaces và mạng xung quanh (SSID, tín hiệu, kênh, tốc độ liên kết theo output Windows). Ping 4 mẫu tới gateway và IP Internet, tính mất gói/độ trễ. Tốc độ liên kết không phải phép đo băng thông Internet. Có thể tự nhập gateway để chọn đúng mạng khi máy có nhiều adapter/VPN. ICMP bị chặn không đồng nghĩa Internet bị mất.
- Camera: nhập tên/IP/cổng; URL RTSP và snapshot được mã hóa bằng khóa của ứng dụng. URL snapshot chỉ được lưu để cấu hình về sau, chưa tải ảnh tự động. Check kiểm tra TCP, không khẳng định camera có hình. Xem trực tiếp mở VLC đã cài trên máy; URL có tài khoản có thể hiện trong danh sách tiến trình VLC. Không có PTZ, playback hoặc tự dò ONVIF trong bản này.

## Cài giám sát nền Windows
1. Dùng Python 64-bit cài cho toàn máy, có Tkinter. Đặt toàn bộ thư mục mã nguồn tại vị trí cố định (ví dụ C:\NetworkAutomation), không xóa/di chuyển sau khi cài service. Không dùng Python chỉ cài trong profile cá nhân cho LocalSystem.
2. Giữ database đang dùng và .credential.key cùng nhau. Source app và service mặc định dùng database trong chính thư mục mã nguồn. Nếu dùng GUI EXE, đặt biến môi trường hệ thống NETWORK_AUTOMATION_DATA_DIR tới cùng thư mục dữ liệu mà service/GUI có quyền truy cập. Khởi động lại máy sau khi đặt biến môi trường hệ thống; không để service và EXE dùng hai database khác nhau.
3. Run as administrator INSTALL_MONITOR_SERVICE.bat. Nó cài dependencies + pywin32, service tự khởi động và cấu hình restart khi lỗi. Nếu service báo thiếu DLL/quyền, kiểm tra cài Python/pywin32 toàn máy; chưa xác nhận cài service trong môi trường Windows này.
4. Mở services.msc, tìm Network Automation Monitor, kiểm tra trạng thái Running. Có thể đổi tài khoản dịch vụ tại Log On; cấp tài khoản đó quyền đọc/ghi thư mục dữ liệu và mã nguồn. Wi-Fi có thể không truy cập được trong session dịch vụ; nếu vậy dùng kiểm tra thủ công ở giao diện, để tùy chọn nền Wi-Fi tắt.
5. Dịch vụ ping thiết bị trong network_devices, kiểm tra cổng camera và thu thập Wi-Fi khi bật. Chu kỳ: hoàn tất một lượt rồi chờ 60 giây (không phải mỗi thiết bị đúng 60 giây). Lưu tối đa 10.000 mẫu trong extension_history.
6. Cảnh báo trạng thái xấu khi đổi trạng thái dùng Notification Center có sẵn. Cần bật thông báo và cấu hình kênh; mặc định không gửi. Cảnh báo có cooldown. Kết quả giám sát agent nằm ở tab Giám sát nền, không cập nhật mọi dashboard/SNMP của chương trình cũ. Chưa chạy SSH audit hay SNMP trong service này.
7. Đóng GUI hoặc đăng xuất vẫn giữ service. Máy phải bật, không ngủ và kết nối tới thiết bị. Khi dừng/tắt máy, giám sát dừng. Heartbeat hiển thị thời gian lượt gần nhất; file tồn tại không bảo đảm dịch vụ còn chạy, hãy kiểm tra Services và thời gian heartbeat.

## Quản lý service
Chạy terminal Administrator trong thư mục chương trình:
```
py -3 windows_service.py stop
py -3 windows_service.py start
py -3 windows_service.py remove
```
Để thử agent không cài service: `py -3 monitor_agent.py`, Ctrl+C để dừng. Không chạy agent thủ công cùng service vì sẽ tạo mẫu và cảnh báo trùng.
Trước cập nhật mã nguồn: dừng service, đóng GUI, sao lưu dữ liệu, thay mã nguồn rồi start service. BUILD_WINDOWS.bat chỉ đóng gói GUI; service chạy từ mã nguồn/Python riêng.

## Kiểm thử
68 unittest và 11 nhóm regression đạt trên Linux; kiểm tra ZIP và cú pháp toàn bộ mã nguồn. OpenAI dùng mock (không có key), không phát sinh gọi API thật. Chưa kiểm thử GUI mới, Windows Service/netsh, VLC, camera thật và API thật. Không khẳng định bản này đã sẵn sàng vận hành trên Windows.

Tài liệu OpenAI đã tham khảo: https://developers.openai.com/api/docs/guides/images-vision
