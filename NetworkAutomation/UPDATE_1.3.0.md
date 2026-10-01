# NetworkAutomation 1.3.0 — giao diện và tác vụ AI

## Giao diện
- Trợ lý vận hành có bố cục riêng, chữ Segoe UI, tab Hội thoại/Lịch sử tác vụ, vùng đọc có thanh cuộn và ô nhập tách biệt.
- Phân biệt câu hỏi, trả lời AI và kết quả công cụ bằng màu/kiểu chữ; vùng hội thoại chỉ đọc.
- Nút gợi ý Kiểm tra thiết bị / Camera / Tổng quan. Ctrl+Enter gửi; chọn/bỏ ảnh, lấy dữ liệu trang, Dừng và Xóa hội thoại có vị trí riêng.
- Thanh tiến độ khi đang xử lý; khóa nút gửi để tránh gửi trùng. Ô nhập vẫn giữ nội dung mới bạn gõ trong khi đợi.
- Nút AI luôn hiện tại góc phải dưới. Chat giữ trong phiên khi ẩn cửa sổ/chuyển trang.
- Bảng chung cao hàng 34px, tiêu đề thoáng và màu chọn rõ hơn; thanh bên đánh dấu mục được chọn. Giữ các trang chức năng hiện có, không thiết kế lại toàn bộ từng trang.

## AI tự hoàn thành kiểm tra
- Bật “Tự hoàn thành và lưu báo cáo”, nhập mục tiêu rồi duyệt phạm vi một lần. Không cần duyệt lại từng bước nằm trong phạm vi; nếu tắt chế độ này thì vẫn duyệt từng công cụ như 1.2.1.
- Công cụ bổ sung ping_devices kiểm tra tối đa 50 thiết bị đã khai báo. Có sẵn ping_ip, check_cameras, read_summary, check_wifi.
- Phạm vi chụp tại lúc duyệt: tối đa 50 thiết bị, 20 camera; IP đã đăng ký trong 100 dòng thiết bị gần nhất/20 camera hoặc IP literal ghi rõ trong mục tiêu. 1.1.1.1 được thêm làm IP kiểm tra Internet. Không cho model tự mở rộng IP ngoài danh sách. Gateway trống dùng route mặc định của Windows, được bao gồm trong phạm vi duyệt.
- Danh sách thiết bị/camera chụp tại lúc duyệt; thay đổi đăng ký sau đó không mở rộng batch đang chạy.
- Tối đa 6 lượt API/10 yêu cầu công cụ, ngưỡng 5 phút trước khi bắt đầu bước/lượt tiếp theo. Tác vụ đang chạy có thể chờ timeout của nó sau ngưỡng. Không lặp cùng công cụ/tham số.
- Lưu task.json và report.txt trong reports/ai_tasks/<task-id>. Có nhật ký bước, kết quả và trạng thái. Khi lỗi/hủy vẫn cố lưu các bước đã hoàn tất. Tab lịch sử có nút mở báo cáo.
- “Đã tổng hợp” nghĩa AI đã trả báo cáo, không chứng minh toàn bộ mục tiêu đã giải quyết hoặc thiết bị được sửa. Nếu công cụ báo lỗi/từ chối hoặc không chạy bước nào, trạng thái “Cần xem lại”.
- Không tự sửa cấu hình, không chạy SSH/shell/reboot/PTZ, không gửi email và không tự gọi AI từ Windows Service. Khi đóng ứng dụng, tác vụ bị hủy; không tự tiếp tục sau mở lại. JSON tác vụ cũ đang chạy được ghi chú có thể bị gián đoạn.

## Windows 11
1. Dừng service và đóng ứng dụng, sao lưu dữ liệu gồm database/.credential.key.
2. Chép mã nguồn mới vào thư mục hiện tại, giữ dữ liệu và data_location.json; không chép đè database từ ZIP.
3. Chạy START_WINDOWS.bat. Mở AI, chọn OpenAI/Gemini, nhập model có quyền dùng/function calling. Key lấy từ OPENAI_API_KEY hoặc GEMINI_API_KEY trong môi trường Windows.
4. Thử “Kiểm tra các thiết bị đã khai báo và tổng hợp cảnh báo”. Bật chế độ tự hoàn thành nếu muốn AI làm nhiều bước trong phạm vi đã duyệt.
5. Cài dịch vụ nền theo hướng dẫn cũ nếu cần. BAT chỉ mở GUI.

## Kiểm tra / giới hạn
90 unittest và 11 nhóm regression đạt trên Linux; ZIP/cú pháp đạt. API dùng mock. Có kiểm thử phạm vi, IP ngoài phạm vi, batch từ snapshot, báo cáo khi hoàn tất/lỗi/hủy, trạng thái cần xem lại và chống lặp công cụ.
Chưa có môi trường hiển thị để kiểm tra giao diện thực; chưa thử Windows 11/EXE/API thật hoặc thiết bị thật. Kèm tests/ui_assistant_smoke.py để chạy kiểm tra bố cục tại Windows: `py -3 tests/ui_assistant_smoke.py`. Script này không gọi API, kiểm tra kích thước 960x780 và 800x640, vùng nhập/nút gửi, tab lịch sử, giữ cửa sổ và dữ liệu trang. Chưa chạy được script GUI trong môi trường hiện tại.
Gói là mã nguồn/build kit; chưa có EXE mới.
