# NetworkAutomation 1.3.2 — giao diện và cấu hình AI

## Thay đổi
- Quét mạng: hàng điều khiển, bộ lọc và thông số tiến độ xuống dòng theo chiều rộng khả dụng; thanh tiến độ nằm riêng. Bảng kết quả có cuộn ngang/dọc đặt cạnh bảng.
- Wi-Fi, camera, SSH, cài đặt: biểu mẫu hai cột chuyển thành một cột khi hẹp; nhóm nút tự xuống dòng. Có cuộn dọc cho trang thấp và cuộn trong vùng kết quả văn bản. Bảng camera có cuộn ngang/dọc.
- Trợ lý AI: thêm tab **Cấu hình AI**. Nhà cung cấp và model vẫn nhập ở phía trên cửa sổ; bấm **Lưu cấu hình** để giữ lựa chọn khi mở lại ứng dụng. OpenAI/Gemini lưu model riêng. Trang AI trong mục Wi-Fi/Camera dùng model OpenAI đã lưu khi mở trang.
- **Kiểm tra API** gửi một câu hỏi ngắn đến nhà cung cấp/model đang chọn, hiển thị thành công hoặc lỗi. Có thể phát sinh phí API. Không chạy công cụ mạng trong phép thử này.
- API key tiếp tục lấy từ biến môi trường `OPENAI_API_KEY` / `GEMINI_API_KEY`. Cấu hình chỉ ghi nhà cung cấp/model vào `ai_preferences.json` ở thư mục dữ liệu. Sau khi đặt biến môi trường Windows, mở lại app để nhận key.
- Tác vụ AI tự hoàn thành: hiển thị công cụ, mục tiêu hiện tại và số lượng hoàn thành/tổng số; lưu tiến độ vào bản ghi tác vụ. Không thay đổi phạm vi được duyệt hoặc tự chạy lệnh SSH.

Đây là bố cục responsive cho desktop Tkinter. Những trang cũ ngoài các mục nêu trên vẫn cần rà soát riêng. Giám sát camera trong chương trình vẫn là kiểm tra kết nối TCP; chưa có điều khiển PTZ hoặc phân tích video trực tiếp.

## Cập nhật Windows 11 bằng START_WINDOWS.bat
1. Đóng ứng dụng và dừng dịch vụ giám sát nếu đã cài. Sao lưu thư mục đang sử dụng.
2. Giải nén bản mới vào thư mục riêng. Chép các file mã nguồn mới vào thư mục chương trình hiện tại.
3. Giữ nguyên `database`, `.credential.key`, `data_location.json` nếu có, cấu hình cá nhân, báo cáo và bản sao lưu trên máy. **Không chép đè thư mục database từ ZIP lên dữ liệu hiện tại.**
4. Chạy `START_WINDOWS.bat`. Mở AI → Cấu hình AI, chọn nhà cung cấp, nhập model tài khoản có quyền dùng, lưu cấu hình rồi kiểm tra API nếu muốn.
5. Nếu dùng dịch vụ, khởi động lại dịch vụ sau khi cập nhật xong.

ZIP cung cấp mã nguồn; không có EXE dựng sẵn cho bản này. Muốn dùng EXE mới, chạy `BUILD_WINDOWS.bat` trên Windows.

## Kiểm thử
104 unittest và 11 nhóm regression đạt trên Linux; kiểm tra cú pháp và tính toàn vẹn ZIP đạt. Các kiểm thử mới kiểm tra model lưu riêng theo nhà cung cấp, không lưu key, file hỏng/ghi thất bại không mất lựa chọn cũ, tiến độ tác vụ và việc hủy không báo hoàn thành.

Chưa render/chạy GUI thật do môi trường kiểm thử không có display; chưa xác nhận Windows 11/DPI 125–150%, API hoặc camera thật. Có hai script GUI không gọi API/mạng thật, dùng dữ liệu tạm riêng:
- `py -3 tests/ui_assistant_smoke.py`: cửa sổ AI, thu nhỏ/phóng to, tab cấu hình, lưu model và API giả lập.
- `py -3 tests/ui_pages_smoke.py`: mở/thu nhỏ các trang quét mạng, Wi-Fi/camera, SSH, cài đặt.

Các script GUI này chưa được chạy trong môi trường hiện tại. Trên máy Windows, nên thử thêm DPI 100%, 125%, 150%, nội dung dài và cuộn đến các nút cuối trang; báo lỗi nếu nút bị che hoặc bảng không cuộn được.
