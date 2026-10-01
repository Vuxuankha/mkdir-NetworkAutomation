# NÂNG CẤP V3.12 -> V3.13

**Đóng ứng dụng trước khi sao chép. Sao lưu toàn bộ thư mục cũ.**

## Đang sử dụng bản cũ và muốn giữ dữ liệu mới nhất

Dùng gói `NetworkAutomation-v3.13-UPGRADE-Khong-Database.zip`.
Giải nén nội dung vào đúng thư mục hiện tại chứa main.py; cho phép thay file mã nguồn trùng tên.
Gói này không có database, không có khóa mã hóa, không xóa backup/báo cáo.
Cập nhật thư viện theo requirements.txt, sau đó chạy main.py như trước.

Không chép thư mục database của gói đầy đủ đè lên database đang dùng.
Giữ cùng nhau `database/network_automation.db` và `database/.credential.key`; mất khóa sẽ không giải mã được Credential.

## Muốn dùng một thư mục mới

Dùng `NetworkAutomation-NMS-v3.13-Auto-IP-Excel-VI.zip`, giải nén sang thư mục mới và mở main.py.
Database và khóa trong gói đầy đủ là bản nguyên trạng từ ZIP bạn đã gửi; không chứa thay đổi bạn làm sau lần gửi đó.
Gói đầy đủ có thể chứa thông tin mạng và Credential của bạn. Không chia sẻ công khai.

## Phạm vi thay đổi

- Thêm `modules/auto_ip.py`, `modules/auto_ip_page.py`, Excel mẫu, hướng dẫn và bộ kiểm thử.
- main.py: thêm import, mục menu riêng, mở trang và dừng worker khi thoát.
- requirements.txt: giới hạn pysnmp `>=7.1,<8` cho API mới; các thư viện khác giữ nguyên.
- Không sửa mã các module chức năng cũ.
- Khi mở chức năng mới lần đầu: thêm bảng autoip_*; với database mới thiếu cột alias cũ, bổ sung cột để engine RCA cũ đọc được. Không xóa bảng/dữ liệu.
- Khi bạn chạy luồng: thêm thiết bị và ghi mẫu giám sát vào NMS chung. Độc lập về giao diện/worker, không phải một database cách ly.

Đọc `HUONG_DAN_AUTO_IP_EXCEL.md` để cấu hình và sử dụng.
