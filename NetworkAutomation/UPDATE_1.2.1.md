# NetworkAutomation 1.2.1 — AI gọi công cụ kiểm tra từ chat

## Chức năng
- Trong Trợ lý AI toàn ứng dụng, bật “Cho AI gọi kiểm tra”. Nhập model hỗ trợ function calling thuộc OpenAI/Gemini. API key tiếp tục đọc từ môi trường Windows.
- Ví dụ: “Ping IP 192.168.1.1 và giải thích kết quả”, “Kiểm tra camera đã khai báo”, “Tổng hợp cảnh báo gần đây”, “Kiểm tra Wi-Fi, gateway 192.168.1.1, IP Internet 1.1.1.1”. IP chỉ là ví dụ, thay bằng thiết bị/mạng của bạn.
- Bốn công cụ: ping_ip (1 IP), check_cameras (tối đa 20 camera), read_summary (số thiết bị và 20 cảnh báo/sự cố/mẫu gần nhất), check_wifi (Windows, gateway có thể trống để tự tìm).
- AI chọn tên công cụ/tham số từ API function calling gốc. Chương trình kiểm tra tên và tham số, sau đó hiển thị hộp duyệt trên luồng giao diện. Chỉ thực hiện nếu bạn đồng ý. Kết quả được gửi tới nhà cung cấp AI để tổng hợp và hiện trong chat. Nếu từ chối, không chạy công cụ.
- Tối đa 4 lượt API và 6 yêu cầu công cụ/câu hỏi. Mỗi API timeout 60 giây; nhiều lượt có thể mất vài phút. Nút Dừng tác vụ hủy các lượt kế tiếp/chờ duyệt, không thu hồi yêu cầu đã gửi hoặc dừng ngay tiến trình ping/API đang chạy.
- Không chạy SQL, shell, SSH, reboot hoặc sửa cấu hình do model cung cấp. Chỉ có các công cụ đọc/kiểm tra đã khai báo. Camera chỉ kiểm tra TCP, không khẳng định có hình hoặc hỗ trợ PTZ.
- Không thêm AI vào service nền; AI vẫn được gọi khi bạn gửi chat.

## Dữ liệu trang hiện tại
Có adapter cho Tổng quan/NOC/Báo cáo; Quét mạng; Quản lý thiết bị/Thiết bị mạng; Cảnh báo; Trung tâm sự cố; SNMP/CPU-RAM/Biểu đồ/Sức khỏe mạng/Phân tích dung lượng; Wi-Fi/Camera/AI. Adapter đọc dữ liệu gần nhất trong database, không hứa lấy đầy đủ nội dung giao diện. Trang chưa hỗ trợ yêu cầu dán log thủ công.
Chỉ SELECT các cột cho phép; không đọc bảng settings/credential hoặc giải mã URL camera. Mẫu cũ thiếu cột được bỏ qua. Log/message vẫn có thể chứa thông tin nhạy cảm ngoài các mẫu che tự động, hãy xem trước khi gửi.

## Cài/cập nhật Windows 11
Dừng service và đóng GUI, sao lưu thư mục dữ liệu (gồm database và .credential.key), chép mã nguồn mới; giữ dữ liệu và data_location.json hiện tại. Không chép database của ZIP đè lên dữ liệu đang dùng. Chạy START_WINDOWS.bat; không cần thêm thư viện mới. Nếu thông báo model không hỗ trợ tools, bỏ chọn checkbox để dùng phân tích như 1.2.0 hoặc chọn model phù hợp tài khoản.

## Kiểm thử / giới hạn
84 unittest và 11 nhóm regression đạt trên Linux, ZIP/cú pháp đạt. Test thêm: OpenAI vòng công cụ/giữ reasoning, Gemini giữ thoughtSignature/id, từ chối không chạy, công cụ ngoài danh sách không chạy, giới hạn vòng gọi, hủy trước request, kiểm tra tham số/IP và không đọc bảng bí mật.
Chưa kiểm thử API thật, GUI Windows 11, card Wi-Fi/camera thật hoặc EXE. Chưa có điều khiển mọi chức năng, SSH thay đổi cấu hình, PTZ hoặc playback. Gói là mã nguồn, không EXE dựng sẵn.
Tài liệu: https://developers.openai.com/api/docs/guides/function-calling và https://ai.google.dev/gemini-api/docs/function-calling
