# NetworkAutomation 1.5.4 — sửa trạng thái Quản lý thiết bị

Ngày kiểm tra: 02/10/2026. Phạm vi: trạng thái Online/Offline của các thiết bị đã lưu khi mở ứng dụng, mở trang và kết nối lại LAN.

## Nguyên nhân đã xác nhận

Trang Quản lý thiết bị đọc bảng `devices`. Nút Làm mới trước đây chỉ đọc lại dữ liệu lưu, không kiểm tra mạng. MonitoringService hiện có cập nhật bảng `network_devices`, nên kết quả giám sát không đến bảng mà trang này sử dụng. Ảnh người dùng có 93 thiết bị với trạng thái và thời gian cũ.

## Bản sửa

- DevicePresenceMonitor khởi động cùng ứng dụng, kiểm tra IP trong `devices`, tối đa 16 ping đồng thời, có giới hạn thời gian cho từng tiến trình. Lượt kế tiếp bắt đầu 15 giây sau khi lượt trước kết thúc; vì vậy chu kỳ thực tế gồm thời gian kiểm tra cộng 15 giây.
- Mở trang hoặc bấm Làm mới yêu cầu lượt kiểm tra mới. Trong khi đang chạy, yêu cầu được gộp để tránh tạo nhiều lượt đồng thời.
- Giao diện nhận kết quả mỗi giây, giữ lựa chọn, vị trí cuộn, tìm kiếm và bộ lọc. Có cột Lần kiểm tra mạng và số lượng Unknown; xuất Excel có cả thời điểm kiểm tra.
- Trạng thái cũ từ phiên trước hiển thị Unknown cho đến khi có kết quả mới. Kết quả quá hạn cũng chuyển Unknown. Kết quả gắn với cả ID và IP để không ghi nhầm nếu thiết bị đổi IP hoặc bị xóa trong lúc kiểm tra.
- Online nghĩa là IP phản hồi ICMP. Offline nghĩa là không nhận phản hồi; firewall có thể chặn ping ngay cả khi thiết bị còn hoạt động. Unknown nghĩa là chưa có kết quả mới hoặc công cụ kiểm tra gặp lỗi. Không xác nhận nguồn điện, Internet hay dịch vụ SSH/HTTP chỉ bằng ping.
- Xử lý Windows trả exit code 0 cho “Destination host unreachable”: chỉ ghi Online khi có bằng chứng phản hồi ping.
- Lần cuối phát hiện chỉ được cập nhật bởi monitor khi có phản hồi Online; kiểm tra Offline không thay thời gian này. Không thay đổi schema DB.
- Worker không gọi Tk; khi đóng/đăng xuất, ứng dụng dừng kiểm tra và đợi worker kết thúc. Timer của trang bị hủy khi điều hướng.

## Kiểm chứng

- 169 unit/integration test đạt, gồm 14 test mới cho presence/ping; 11 nhóm regression đạt.
- 6 bài GUI đạt trên Linux/Xvfb, gồm 57 trang, tài khoản, trang hỗ trợ, credential, SSH cục bộ và bài Device Manager mới.
- Bài Device Manager chạy Tk thật với 93 bản ghi và kết quả LAN mô phỏng: startup Unknown, Offline 93, tự chuyển Online 1 / Offline 92 khi mô phỏng kết nối lại, thời điểm mới, giữ lựa chọn, lọc/tìm kiếm, xuất Excel, Làm mới, đổi trang, hủy timer và dừng worker. Không có lỗi callback Tk.
- Ping thực tế trong môi trường kiểm tra bị hệ điều hành từ chối quyền ICMP. Đã xác nhận lỗi này trả Unknown thay vì gán Offline. Chưa kiểm chứng phản hồi ICMP thật trên LAN người dùng, Windows hoặc thiết bị vật lý.
- Kiểm tra nâng cấp trên bản sao dữ liệu gốc: 93 `devices`, 93 `network_devices`, 3 tài khoản, 1 config backup được giữ nguyên; 2 giá trị mã hóa giải mã được; SQLite quick_check = ok; snapshot trước nâng cấp có khóa tương ứng. Không tác động dữ liệu gốc.
- Gói ZIP được giải nén lại để chạy release checks và 6 bài GUI; xác minh CRC, không tên trùng, các mục không sửa giữ CRC/kích thước, database và khóa gốc giữ nguyên byte. Log và bằng chứng nằm trong gói.

## Chạy bản sửa trên Windows

Các EXE/installer có sẵn trong ZIP là bản cũ và chưa được build lại trong môi trường Linux. Chạy `BUILD_WINDOWS.bat` để tạo `dist\NetworkAutomation\NetworkAutomation.exe` 1.5.4, hoặc `BUILD_INSTALLER.bat` sau khi đã build. Chạy EXE cũ sẽ không có bản sửa này. Có thể chạy mã nguồn bằng Python cùng requirements.txt để kiểm chứng trước.

Mở app trên máy kết nối LAN, vào Quản lý thiết bị, chờ lượt đầu hoàn tất và xem cột Lần kiểm tra mạng. Nếu tất cả Offline dù IP truy cập được, thử ping IP đó trên chính máy chạy app và kiểm tra firewall/VPN/route. Thiết bị chặn ICMP cần kiểm tra thêm dịch vụ phù hợp, không suy diễn là đã tắt.
