# NetworkAutomation 1.0.2 — 01/10/2026

## Thay đổi
- Tra hostname: tối đa 1 giây chờ/IP, 16 resolver DNS chạy đồng thời. Nếu resolver hệ điều hành bị kẹt, tác vụ daemon vẫn tồn tại nhưng không giữ quét mạng hoặc tắt ứng dụng; khi hết slot sẽ bỏ qua hostname.
- Checkbox “Tra hostname” trên màn hình Quét mạng; bỏ chọn để bỏ qua DNS.
- Sửa timeout ping ở màn hình Quét mạng từ 1 ms thành 1000 ms.
- Sao lưu trước lần khởi tạo database của mỗi phiên bản ứng dụng, trước migration: SQLite backup API giữ dữ liệu WAL đã commit, kiểm tra quick_check, kèm .credential.key và known_hosts nếu có.
- Snapshot lưu ở database/db_backups/pre_app_v1.0.2_...; khi chạy EXE nằm trong %LOCALAPPDATA%/NetworkAutomation/database/db_backups.
- Chỉ ghi marker sau sao lưu thành công. Nếu sao lưu thất bại, ứng dụng dừng khởi tạo để tránh nâng cấp không có bản dự phòng. Không tạo snapshot cho database hoàn toàn mới; lần mở tiếp theo sẽ tạo nếu chưa có marker.
- SSH có lựa chọn exec/shell và ô lệnh tắt phân trang. Ví dụ Cisco thường dùng “terminal length 0”; cần chọn lệnh phù hợp với thiết bị. Nếu phân trang vẫn bật, runner có thể hết thời gian chờ.
- Kế thừa tối ưu quét mạng, hàng đợi SSH, timeout ping/ARP và xoay vòng log của 1.0.1.

## Chạy / cập nhật
1. Đóng ứng dụng cũ, tự sao lưu thư mục database trước khi chép bản mới.
2. Nếu cập nhật thư mục hiện có: chép mã nguồn mới, giữ database, reports, backups và khóa của bạn. Không chép đè database bằng dữ liệu mẫu từ ZIP.
3. Cài thư viện: py -3 -m pip install -r requirements.txt
4. Chạy START_WINDOWS.bat.
5. Tạo EXE mới bằng BUILD_WINDOWS.bat trên Windows. ZIP không có EXE/Setup dựng sẵn.

## Khôi phục thủ công
- Đóng mọi phiên ứng dụng. Với EXE, dùng thư mục %LOCALAPPDATA%/NetworkAutomation/database; với mã nguồn dùng thư mục database bên cạnh main.py.
- Đổi tên toàn bộ thư mục database hiện tại thành database_before_restore để giữ dữ liệu mới và các file WAL/SHM. Tạo lại thư mục database trống.
- Chép network_automation.db và .credential.key, known_hosts (nếu snapshot có) từ CÙNG thư mục pre_app_v... vào database mới. Không ghép khóa khác với database; mật khẩu mã hóa sẽ không đọc được.
- Để phục hồi chính xác trước nâng cấp, chạy cùng mã nguồn phiên bản cũ. Mở bản mới sẽ tự sao lưu rồi áp dụng lại migration.
- Nếu snapshot không có khóa nhưng dữ liệu của bạn có mật khẩu mã hóa, cần dùng khóa gốc đã giữ trong database_before_restore.

## Kiểm thử và giới hạn
60 unittest đạt; 11 nhóm regression đạt trên Linux. Có test DNS chậm, DNS hết slot, tắt DNS, snapshot từ WAL, khóa mã hóa, sao lưu một lần/phiên bản, lỗi snapshot và database mới.
Chưa kiểm tra giao diện Windows, build EXE/Setup hoặc thiết bị SSH/SNMP thật. Tiến độ và Online/Offline có sẵn được giữ nguyên. Khôi phục ở phiên bản này là thao tác thủ công theo hướng dẫn trên.
