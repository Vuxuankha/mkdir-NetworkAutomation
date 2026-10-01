# NetworkAutomation 1.4.1 — sửa cửa sổ Thêm/Sửa thiết bị

## Nguyên nhân
Cửa sổ cũ bị khóa ở 450×400. Biểu mẫu, tiêu đề và khoảng cách chiếm hết chiều cao, khiến hàng nút Lưu/Hủy bị đẩy ra ngoài vùng nhìn thấy. Ảnh lỗi cho thấy chỉ có biểu mẫu, không thấy nút lưu. Cửa sổ Sửa dùng cùng bố cục nên cũng được sửa.

## Sửa lỗi
- Dùng chung biểu mẫu Thêm/Sửa, cho phép thay đổi kích thước.
- Cửa sổ mở ở tối đa 560×580 theo kích thước màn hình, tối thiểu 380×300; biểu mẫu có cuộn.
- Hàng nút **Lưu / Hủy** nằm ngoài vùng cuộn, luôn được dành chỗ ở đáy cửa sổ.
- `Ctrl+Enter` để lưu, `Esc` để đóng.
- IP trống/sai hoặc IP trùng hiển thị lỗi và giữ dữ liệu đã nhập để sửa lại.
- Lỗi ghi database giữ cửa sổ mở, bật lại nút Lưu và ghi chi tiết vào nhật ký.
- Sau khi lưu thành công, cập nhật danh sách thiết bị qua bộ quản lý hiện có. Bộ lọc hiện tại tiếp tục áp dụng.

Không có thay đổi schema database hoặc tái bật chức năng AI.

## Cập nhật từ bản 1.4.0 trên Windows
1. Đóng ứng dụng, sao lưu thư mục đang dùng.
2. Giải nén bản 1.4.1 riêng rồi chép mã nguồn mới vào thư mục chương trình.
3. Giữ nguyên database, `.credential.key`, `data_location.json`, cấu hình và báo cáo hiện tại. **Không chép đè thư mục database từ ZIP.**
4. Chạy `START_WINDOWS.bat`, mở Quản lý thiết bị → Thêm thiết bị. Nhập IP → bấm Lưu.

File sửa chính là `main.py` và module mới `modules/device_dialog.py`; cần chép cả hai cùng lúc. VERSION và metadata build cũng được nâng lên 1.4.1. ZIP là mã nguồn; muốn EXE mới cần chạy `BUILD_WINDOWS.bat` trên Windows.

## Kiểm thử
94 unittest và 11 nhóm regression đạt trên Linux. Kiểm thử mới dùng SQLite tạm để xác nhận thêm/sửa thiết bị thật, IP trùng không ghi đè, kiểm tra IP trước khi ghi, lỗi lưu giữ biểu mẫu mở và cho phép thử lại. Cú pháp/ZIP và việc giữ dữ liệu từ gói 1.4.0 được kiểm tra khi đóng gói.

Chưa chạy GUI thực trên Windows vì môi trường hiện tại không có display. Script `py -3 tests/ui_device_dialog_smoke.py` kiểm tra vị trí nút tại 560×580, 450×400, 380×300, các hệ số Tk scaling tương ứng 100/125/150%, thêm/sửa vào database tạm và callback làm mới danh sách. Script này chưa thực thi tại đây; Tk scaling không thay thế hoàn toàn kiểm tra DPI Windows thực.
