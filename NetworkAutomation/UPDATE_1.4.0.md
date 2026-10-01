# NetworkAutomation 1.4.0 — bỏ AI, đồng bộ giao diện tối

## Gỡ AI
- Bỏ nút AI nổi, nút Trợ lý AI trên thanh trên và AI Assistant trên dashboard.
- Bỏ tab AI ở Wi-Fi/Camera, lựa chọn nhà cung cấp/model, thử API, hội thoại, gọi công cụ và tác vụ AI.
- Loại khỏi gói mã nguồn sáu module AI cùng các kiểm thử riêng của tính năng này; xóa các hàm gọi OpenAI/Gemini khỏi module giám sát mở rộng.
- Chương trình không đọc key OpenAI/Gemini hoặc gọi các API đó nữa. Không cần thiết lập key để dùng bản này.
- Mục Giám sát → **Wi-Fi / Camera** giữ các tab Wi-Fi, Camera, Giám sát nền. Nút banner dashboard mở Trung tâm NOC.

## Giao diện các mục còn lại
Toàn bộ trang dùng hệ màu tối chung từ `modules/ui_theme.py`: nền xanh đen, thẻ/bảng tối, chữ sáng, cyan cho thao tác chính, hồng tím cho điểm nhấn; giữ màu trạng thái thành công/cảnh báo/lỗi dễ phân biệt.

Áp dụng cho khung chương trình, màn hình đăng nhập, menu, hub chức năng, biểu mẫu thiết bị/IP, SNMP, cổng, CPU/RAM, Application/Server, Wi-Fi/Camera, sơ đồ mạng, SSH, tự động IP/Excel, Daily Audit, baseline/security, backup, cảnh báo/sự cố, SLA, báo cáo, nhật ký và các mục quản trị. Cửa sổ con Tkinter và danh sách combobox dùng cùng mặc định màu; hộp chọn tệp/thông báo native Windows vẫn theo hệ điều hành.

20 file giao diện cũ đã chuyển từ màu cứng sang palette dùng chung; dashboard cũng dùng palette đó. Style ttk chung xử lý bảng, đầu cột, nút, entry, combobox readonly, checkbox, notebook, thanh cuộn và thanh tiến độ. Chữ và các nét mặc định trên biểu đồ/sơ đồ được chỉnh để hiển thị trên nền tối.

Đây là cập nhật màu sắc, style và tính nhất quán cho toàn bộ mục. Các bố cục co giãn đã có được giữ; những biểu mẫu cũ còn bố cục cố định chưa được viết lại toàn bộ trong bản này. Cần kiểm tra tiếp các màn hình đó ở kích thước nhỏ và DPI cao.

Hẹn giờ thuộc trang cũ được hủy khi chuyển mục; hẹn giờ dịch vụ/engine gắn với cửa sổ chính tiếp tục chạy. Các bộ máy quản lý mạng, camera, SSH và tự động hóa được giữ.

## Cập nhật Windows 11
1. Đóng GUI và dừng service nếu đã cài. Sao lưu thư mục chương trình/dữ liệu hiện tại.
2. Giải nén ZIP vào thư mục riêng, chép mã nguồn mới vào thư mục chương trình đang dùng.
3. **Giữ nguyên database, `.credential.key`, `data_location.json`, cấu hình cá nhân, báo cáo và backup. Không chép đè database từ ZIP.**
4. Nếu cập nhật bằng cách chép đè, chạy `REMOVE_OLD_AI_MODULES.bat` trong thư mục chương trình để xóa các file mã AI cũ. Script chỉ dọn các module/test/cache AI đã liệt kê, giữ dữ liệu cá nhân. File cấu hình/báo cáo AI cũ nếu có không được chương trình mới sử dụng.
5. Chạy `START_WINDOWS.bat`. Khởi động lại service nếu đang sử dụng.

ZIP là mã nguồn; chưa có EXE mới dựng sẵn. Dùng `BUILD_WINDOWS.bat` trên Windows nếu muốn EXE 1.4.0.

## Kiểm thử
87 unittest và 11 nhóm regression đạt trên Linux. Số unittest giảm vì đã bỏ các bài test dành riêng cho AI. Kiểm thử bổ sung xác nhận: không còn điểm gọi/API AI; Wi-Fi/camera/history vẫn có; các trang không còn nền sáng cứng; độ tương phản màu chữ/trạng thái; hủy hẹn giờ trang không hủy callback dịch vụ gốc. Cú pháp, cấu trúc ZIP và việc giữ nguyên dữ liệu của bản trước được kiểm tra khi đóng gói.

Chưa chạy/render GUI trên Windows 11 do môi trường hiện tại không có display; chưa xác nhận tất cả trang ở DPI 125–150%. Có script `py -3 tests/ui_all_pages_smoke.py` dựng 57 trang tại 1400×800 và 800×600, dùng database tạm riêng và tắt các engine nền. Script này chưa thực thi tại đây. Có thể chạy thêm `tests/ui_pages_smoke.py` và `tests/ui_dashboard_smoke.py` rồi kiểm tra các cửa sổ con trên máy Windows.
