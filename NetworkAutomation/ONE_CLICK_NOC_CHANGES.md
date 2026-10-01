# One-Click NOC

## Mục tiêu
Trang chủ trở thành điểm vào duy nhất cho kiểm tra hàng loạt: dán IP hoặc chọn Excel, xác nhận quyền quản trị, bấm **KIỂM TRA TOÀN BỘ**.

## Pipeline
- Ping
- TCP ports theo cấu hình Auto IP/Excel
- SNMP/driver nếu hồ sơ hỗ trợ
- CPU/RAM nếu driver/SNMP hỗ trợ
- Interface/lưu lượng nếu SNMP hỗ trợ
- LLDP/CDP topology nếu hỗ trợ
- Alert/incident post-processing
- Notification Center
- Xuất Excel
- Tùy chọn gửi Gmail/Email khi hoàn tất

Các bước thiếu credential/SNMP/driver được ghi SKIP/WARN, không làm hỏng toàn bộ lượt chạy.

## Trang chủ
- Ô dán nhiều IP
- Chọn file `.xlsx`
- Hiển thị số IP đã nạp
- Xác nhận quyền kiểm tra
- Tùy chọn gửi Gmail/Email khi hoàn tất
- Một nút KIỂM TRA TOÀN BỘ
- Progress và trạng thái chạy trực tiếp trên trang chủ
- Dashboard NOC cũ vẫn nằm ngay bên dưới

## An toàn
- Không tự thay đổi cấu hình thiết bị.
- Không tự tạo credential.
- Không tự biến running-config thành baseline.
- Dùng engine Auto IP/Excel hiện có để giữ lịch sử/report tương thích.
