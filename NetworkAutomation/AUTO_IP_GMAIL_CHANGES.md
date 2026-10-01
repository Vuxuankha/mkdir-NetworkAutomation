# Auto IP/Excel - Gmail report

## Thay đổi
- Thêm tùy chọn **Gửi Gmail/Email sau khi chạy xong** ngay trên màn hình Tự động IP/Excel.
- Có thể nhập email nhận riêng; để trống sẽ dùng `Email To` trong Notification Center.
- Tái sử dụng SMTP username/password đã cấu hình trong Notification Center; không lưu thêm mật khẩu ở module Auto IP.
- Khi bật gửi email, app luôn tạo báo cáo Excel và đính kèm, kể cả khi tác vụ `Báo cáo Excel` đang tắt.
- Nội dung email tóm tắt lượt chạy: thời gian, trạng thái, số IP và số OK/WARN/ERROR/SKIP.
- Hỗ trợ nhiều người nhận, phân cách bằng dấu phẩy hoặc dấu chấm phẩy.
- Nếu SMTP chưa cấu hình, bước gửi mail được đánh dấu `SKIP`; nếu SMTP lỗi, đánh dấu `ERROR`; lượt chạy chính vẫn hoàn tất.

## Gmail
Cấu hình tại Notification Center:
- SMTP Host: `smtp.gmail.com`
- SMTP Port: `587`
- SMTP Username: địa chỉ Gmail gửi thư
- SMTP Password: App Password khi tài khoản yêu cầu xác minh 2 bước
- Email To: địa chỉ mặc định nhận báo cáo
