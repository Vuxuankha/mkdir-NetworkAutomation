# NetworkAutomation 1.0.1 — 01/10/2026

## Thay đổi
- Quét mạng lấy IP theo iterator; chỉ giữ tối đa 2 × số luồng tác vụ chờ thay vì tạo toàn bộ subnet trong RAM.
- Dừng quét kiểm tra mỗi 100 ms và hủy tác vụ chưa chạy. Tác vụ đang chạy vẫn cần hoàn tất; reverse DNS phụ thuộc bộ phân giải của hệ điều hành.
- Ping có deadline tiến trình, làm tròn lên timeout Linux; ARP có timeout 3 giây.
- SSH lấy dữ liệu Tkinter trên luồng giao diện; worker trả kết quả qua Queue. Ngăn chạy trùng và bỏ cập nhật khi trang đã bị hủy.
- SSH dùng runner có deadline và đọc đồng thời stdout/stderr; sao lưu dùng tên file an toàn.
- Log ứng dụng xoay vòng 5 MiB × 4 file. console_capture.log giữ cơ chế cũ.
- SQLite busy_timeout tôn trọng timeout do người gọi truyền vào.
- Đồng bộ phiên bản nguồn, thông tin Windows và installer thành 1.0.1.

## Cách dùng
Giải nén, cài thư viện bằng `py -3 -m pip install -r requirements.txt`, chạy START_WINDOWS.bat.
Nếu cập nhật bản đang dùng: đóng ứng dụng, sao lưu database (gồm .credential.key và known_hosts), rồi chép các file mã nguồn mới vào thư mục cũ. Giữ database của bạn.
BUILD_WINDOWS.bat tạo EXE mới trên Windows; BUILD_INSTALLER.bat tạo bộ cài khi đã có Inno Setup.
ZIP này là bản mã nguồn và build kit. Không chứa EXE/Setup cũ để tránh chạy nhầm phiên bản.

## Kiểm tra
53 unittest đạt; 11 nhóm regression đạt trên Linux. Chưa thử giao diện Windows, build EXE hoặc kết nối SSH/SNMP tới thiết bị thật.
Không nâng phiên bản thư viện khi chưa kiểm tra tương thích.
