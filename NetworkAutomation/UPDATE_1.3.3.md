# NetworkAutomation 1.3.3 — dashboard theo ảnh mẫu

## Giao diện
Màn hình **Tổng quan / One-Click NOC** được viết lại bằng Tkinter theo bố cục và màu của ảnh mẫu: nền xanh đen, thanh trên và menu tối, mục đang chọn màu tím, điểm nhấn cyan/hồng, banner đường kết nối, vòng trạng thái, các thẻ Online/Offline/Cảnh báo/Sự cố, Daily Audit và hai bảng dữ liệu.

Đường nối phát sáng trong banner là họa tiết trang trí. Vòng trạng thái và các số liệu lấy từ cơ sở dữ liệu hiện tại, không dùng các con số minh họa trong ảnh. Chưa có biểu đồ lưu lượng thật vì dashboard chưa có nguồn dữ liệu băng thông phù hợp.

- Các bảng/thẻ làm mới mỗi 5 giây; thời gian hiển thị cập nhật mỗi giây.
- Thẻ tự xuống hàng khi hẹp; hai bảng chuyển thành một cột dưới 1000px bề rộng nội dung. Toàn trang có cuộn dọc; bảng có cuộn ngang/dọc.
- Banner có nút **AI Assistant**, thanh trên và nút AI nổi vẫn mở trợ lý hiện có.
- Bấm **Kiểm tra IP / Excel** để mở/thu phần nhập IP, nạp Excel, lựa chọn Email và xác nhận quyền kiểm tra. Các thao tác này tiếp tục dùng bộ máy One-Click cũ.
- **Daily Audit**, **Trung tâm NOC**, nút mở bảng Cảnh báo/Sự cố vẫn điều hướng đến các chức năng hiện có.
- Khi dữ liệu không đọc được, hiện dấu “—” và thông báo thiếu dữ liệu. Không mặc nhiên coi cơ sở dữ liệu lỗi là mạng khỏe.
- Bộ hẹn giờ của dashboard được dừng khi rời trang để tránh lặp cập nhật trên widget đã đóng.

Đây là triển khai native desktop bám bố cục/màu của ảnh, không cam kết khớp từng pixel với hiệu ứng đồ họa trong ảnh. Dashboard và thanh trên được thay đổi; các trang chức năng khác giữ bố cục hiện có. Không thêm thư viện giao diện mới.

## Cập nhật trên Windows 11
1. Đóng chương trình; dừng dịch vụ giám sát nếu đang chạy. Sao lưu thư mục hiện tại.
2. Giải nén bản mới vào thư mục riêng, chép mã nguồn mới vào thư mục ứng dụng hiện tại.
3. Giữ nguyên database, khóa `.credential.key`, `data_location.json`, cấu hình cá nhân, báo cáo và bản sao lưu của bạn. **Không chép đè thư mục database từ ZIP lên dữ liệu đang dùng.**
4. Chạy `START_WINDOWS.bat`, mở **Tổng quan** để xem dashboard mới.

ZIP cung cấp mã nguồn. Chưa có EXE dựng sẵn cho bản 1.3.3; cần dùng `BUILD_WINDOWS.bat` trên Windows để dựng EXE mới.

## Kiểm tra
110 unittest và 11 nhóm regression đạt trên Linux. Các kiểm thử mới xác nhận số lượng thiết bị theo trạng thái, sự kiện đang mở, thứ tự sự kiện, xử lý dữ liệu thiếu và các mốc xuống hàng. Cú pháp và tính toàn vẹn ZIP đạt; dữ liệu trong ZIP được giữ nguyên từ bản 1.3.2, không đưa dữ liệu kiểm thử vào gói.

Môi trường hiện tại không có display nên chưa chạy/render GUI thật, chưa xác nhận hình ảnh trên Windows 11/DPI 125–150%. Script `py -3 tests/ui_dashboard_smoke.py` dùng dữ liệu tạm, không chạy kiểm tra mạng hoặc API thật: kiểm tra cửa sổ 1400×800, 1024×768, 800×600, nút AI/One-Click, cuộn và việc dừng hẹn giờ. Script này chưa được thực thi tại đây.
