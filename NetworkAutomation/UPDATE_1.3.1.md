# NetworkAutomation 1.3.1 — giao diện co giãn (responsive)

## Thay đổi
- Cửa sổ chính cho phép thu nhỏ tới 800×600. Thanh trên luôn có Menu, tên trang và Trợ lý AI.
- Dưới 1150px, thanh bên mặc định thu gọn để dành chỗ cho nội dung. Bấm Menu để mở lại; chọn mục sẽ thu gọn. Trên cửa sổ rộng mặc định hiện thanh bên. Lựa chọn ẩn/hiện của bạn được giữ trong cùng chế độ rộng/hẹp.
- Tiêu đề và mô tả trang tự ngắt dòng theo bề rộng.
- Cửa sổ AI thu nhỏ tới 640×640. Nhóm nút được xếp lại theo kích thước thực tế của chữ/nút, thay vì chỉ dùng chiều rộng cố định.
- Các nút Gửi/Dừng nằm trước nhóm thao tác phụ. Checkbox tự hoàn thành chuyển xuống dòng riêng ở cửa sổ hẹp.
- Khi cửa sổ AI hẹp hoặc thấp, hàng gợi ý và kiểm tra nhanh được thu lại; các thao tác Ping/Camera/Xóa/Gợi ý vẫn có trong menu Khác.
- Bảng lịch sử tác vụ có cuộn ngang/dọc; mô tả, trạng thái và tên ảnh dài được xử lý theo chiều rộng khả dụng.
- Tác vụ đang chạy không bị khởi động lại khi đổi kích thước cửa sổ.

Đây là responsive cho ứng dụng desktop Tkinter, không phải giao diện web/mobile. Áp dụng trực tiếp cho khung chính, tiêu đề và trợ lý AI; chưa chuyển mọi biểu mẫu/trang cũ có bố cục cố định sang responsive. Những trang đó vẫn cần rà soát ở màn hình nhỏ/DPI cao.

## Cập nhật Windows 11
Dừng service, đóng GUI, sao lưu dữ liệu; chép mã nguồn mới, giữ database/.credential.key và data_location.json hiện tại. Không chép đè database từ ZIP. Chạy START_WINDOWS.bat.
Thử phóng to/thu nhỏ cửa sổ chính và AI; bấm Menu/Khác khi cửa sổ nhỏ.

## Kiểm thử
96 unittest và 11 nhóm regression đạt trên Linux; cú pháp/ZIP đạt. Kiểm thử bổ sung: hàng nút tự xuống dòng, font lớn/DPI làm nút rộng hơn, bề rộng 0 và quy tắc thanh bên giữ lựa chọn người dùng.
Chưa có display để render/kiểm tra hình ảnh giao diện thực, chưa thử Windows 11/DPI 125–150%. Script `py -3 tests/ui_assistant_smoke.py` kiểm tra GUI thực tại các kích thước 1200×850, 960×780, 800×640, 640×700; chưa chạy script đó trong môi trường này.
Không có EXE dựng sẵn; API/camera thật vẫn cần kiểm tra trên máy của bạn.
