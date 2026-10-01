# NetworkAutomation 1.2.0 — trợ lý toàn ứng dụng và Gemini

- Nút Trợ lý AI góc phải dưới ngoài vùng nội dung, mở được từ màn hình chính và mọi trang. Khung chat là cửa sổ riêng (Toplevel), chưa phải panel nằm trong trang. Đóng cửa sổ sẽ ẩn, giữ hội thoại trong phiên; thoát ứng dụng mất hội thoại.
- Chọn OpenAI hoặc Gemini, nhập model có quyền dùng. Key đọc từ OPENAI_API_KEY hoặc GEMINI_API_KEY trong môi trường Windows; khởi động lại app sau khi đặt. Không lưu key vào mã nguồn.
- Có ảnh JPEG/PNG/WebP chọn thủ công; model cần hỗ trợ ảnh. Gemini dùng generateContent, header x-goog-api-key. API chưa được thử bằng key thật.
- Trước gửi có xác nhận nhà cung cấp. Nội dung hội thoại giới hạn và ảnh hiện chọn được gửi tới nhà cung cấp. Nút Xóa hội thoại xóa bộ nhớ chat tại ứng dụng.
- Dữ liệu trang hiện tại: Quét mạng lấy tối đa 100 kết quả; Wi-Fi/Camera/AI lấy 20 mẫu lịch sử. Các trang khác chỉ lấy tên trang và yêu cầu bạn dán kết quả. Không tự lấy credential/config nhạy cảm.
- Nút Ping IP và Kiểm tra camera thực hiện kiểm tra cục bộ, trả vào ô nhập để bạn xem trước khi gửi AI. Đây là công cụ do người dùng bấm; chưa có AI tự chọn/call tool từ câu lệnh tự nhiên.
- AI chưa xử lý tự động toàn bộ chức năng của chương trình; chưa chạy SSH thay đổi cấu hình, reboot, PTZ hoặc playback. Không tuyên bố hỗ trợ mọi thao tác.
- Tab Trợ lý AI cũ vẫn dành cho OpenAI. Lựa chọn Gemini nằm trong cửa sổ Trợ lý AI toàn ứng dụng.

## Cập nhật
Dừng service, đóng ứng dụng, sao lưu dữ liệu rồi chép mã nguồn mới; giữ database/.credential.key và data_location.json của bạn, không chép đè database trong ZIP. Chạy START_WINDOWS.bat. Thiết lập GEMINI_API_KEY giống OPENAI_API_KEY trong User variables Windows; nhập model chính xác từ tài khoản Google AI Studio.

## Kiểm thử
76 unittest và 11 nhóm regression đạt trên Linux. Kiểm tra ZIP/cú pháp. Chưa kiểm tra giao diện Windows, Gemini/OpenAI API thật, thiết bị thật hoặc EXE. Cần thử bản này trên Windows 11 trước vận hành.
Tài liệu Gemini: https://ai.google.dev/api/generate-content
