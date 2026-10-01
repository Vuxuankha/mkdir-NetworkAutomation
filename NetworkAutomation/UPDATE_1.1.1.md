# NetworkAutomation 1.1.1 — cải thiện ổn định

Dành cho cách chạy mã nguồn trên Windows 11 bằng START_WINDOWS.bat. Chưa xác nhận vận hành trên Windows thật.

## Thay đổi
- Khóa tiến trình agent theo thư mục dữ liệu: Windows dùng msvcrt byte lock, Linux dùng flock. Khóa được hệ điều hành giải phóng khi tiến trình thoát; không cần xóa file agent.lock khi crash. Chỉ ngăn trùng các agent dùng CÙNG thư mục dữ liệu, không ngăn worker giám sát cũ trong GUI.
- Heartbeat ghi nguyên tử, cập nhật mỗi 10 giây, độc lập với thời gian một lượt quét. Tab Giám sát nền phân biệt khởi tạo/chạy/chờ/lỗi/dừng. Quá 35 giây không cập nhật sẽ báo mất heartbeat; vẫn cần kiểm tra Windows Services.
- Hiển thị đường dẫn dữ liệu đang dùng để chẩn đoán GUI/service dùng nhầm database.
- File data_location.json đặt cạnh main.py hoặc EXE pin đường dẫn dữ liệu. NETWORK_AUTOMATION_DATA_DIR ưu tiên cao hơn file JSON. Không đổi tự động hoặc chép đè database.
- Wi-Fi không đọc được interface hoặc quét mạng xung quanh vẫn có thể ping gateway/Internet. Nhiều adapter/VPN: nên nhập gateway cụ thể; tự chọn gateway chưa đảm bảo thuộc adapter Wi-Fi.
- Đóng/chuyển trang Wi-Fi/Camera/AI hủy callback polling, báo dừng cho tác vụ Wi-Fi. Tác vụ API đang gửi vẫn hoàn tất hoặc timeout; không cập nhật trang đã bị hủy. Không hoàn tiền/lùi yêu cầu API đã gửi.
- Giữ camera theo kết nối TCP/RTSP chuẩn. Imou Life / IPC-DK2 chưa được xác nhận model đầy đủ; không có nhận diện tự động, PTZ hoặc playback mới.

## Cập nhật từ 1.1.0
1. Dừng Network Automation Monitor trong services.msc nếu đã cài. Đóng GUI và agent thủ công.
2. Sao lưu toàn bộ thư mục dữ liệu gồm database và .credential.key. Chép mã nguồn mới vào thư mục cũ, GIỮ dữ liệu hiện tại; không chép database trong ZIP đè lên dữ liệu của bạn.
3. Cài thư viện nếu cần: py -3 -m pip install -r requirements.txt
4. Chạy START_WINDOWS.bat. Vào Wi-Fi / Camera / AI → Giám sát nền, xem đường dẫn dữ liệu.
5. Start service lại sau khi cập nhật. Lịch sử/heartbeat chỉ có khi agent hoặc service chạy; BAT chỉ khởi động GUI.

## Pin dữ liệu chung (tùy chọn)
Nếu mã nguồn ở C:\NetworkAutomation và database đang ở C:\NetworkAutomation\database, chạy:
```
py -3 CONFIGURE_DATA_PATH.py --data-dir C:\NetworkAutomation
```
--data-dir là THƯ MỤC CHA của database, không phải database.
Dừng/khởi động lại cả GUI và service sau thay đổi. Nếu dùng EXE về sau, chép data_location.json cạnh EXE để EXE đọc cùng dữ liệu. Tài khoản service cần quyền đọc/ghi thư mục đã chọn. Nếu đã đặt biến môi trường NETWORK_AUTOMATION_DATA_DIR, nó sẽ ghi đè lựa chọn JSON; kiểm tra cả môi trường của người dùng và hệ thống.
Công cụ chỉ ghi đường dẫn; KHÔNG chuyển database, báo cáo hoặc khóa. Nếu chuyển sang thư mục mới phải chép toàn bộ dữ liệu khi mọi tiến trình đã dừng, rồi mới pin đường dẫn.

## Kiểm thử
73 unittest đạt và 11 nhóm regression đạt trên Linux. Test mới: hai tiến trình tranh khóa, nhả khóa, heartbeat mới/cũ/dừng/hỏng, Wi-Fi không có adapter vẫn kiểm tra IP, hủy callback khi đóng trang.
Chưa kiểm thử thực tế: Windows byte lock/service, netsh, GUI mới, Imou camera, OpenAI API thật, EXE và chạy lâu 24–72 giờ. Các test không chứng minh bản này đã ổn định hoàn toàn trên Windows. Không có EXE dựng sẵn.
Xem UPDATE_1.1.0.md để cài service, cấu hình OpenAI và camera.
