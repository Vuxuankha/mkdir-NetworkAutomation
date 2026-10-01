# Auto IP/Excel - gửi báo cáo qua Gmail/Email

Đã bổ sung tùy chọn **Gửi Gmail/Email sau khi chạy xong** trên màn hình Tự động IP/Excel.

## Cách dùng
1. Mở **Notification Center**.
2. Cấu hình SMTP. Với Gmail thường dùng `smtp.gmail.com`, port `587`, SMTP Username là địa chỉ Gmail.
3. Tại màn hình **Tự động IP/Excel**, bật **Gửi Gmail/Email sau khi chạy xong**.
4. Nhập Email nhận, hoặc để trống để dùng mục **Email To** của Notification Center.
5. Chạy danh sách IP. Sau khi từng lượt hoàn tất, app tạo file Excel và đính kèm vào email.

## Lưu ý Gmail
Nếu tài khoản Google bật xác minh 2 bước, SMTP thường cần **App Password** thay cho mật khẩu đăng nhập Google. Mật khẩu SMTP được lưu mã hóa bằng cơ chế credential hiện có của app.

## Hành vi
- Nếu bật gửi email, file Excel sẽ được tạo kể cả khi checkbox Báo cáo Excel đang tắt.
- Nếu chưa cấu hình SMTP/người nhận, job vẫn hoàn tất và bước gửi mail hiện `SKIP`; không làm hỏng toàn bộ lượt chạy.
- Nếu SMTP lỗi, bước gửi mail hiện `ERROR`; báo cáo vẫn được giữ trong thư mục reports.
- Nếu bật lặp định kỳ, mỗi chu kỳ hoàn tất sẽ gửi một email.
