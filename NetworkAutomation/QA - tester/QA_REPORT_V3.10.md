# QA REPORT - Network Automation NMS v3.10

## Phạm vi nâng cấp
- Device Dependencies: khai báo quan hệ cha/con giữa thiết bị.
- Root Cause Analysis: tương quan cảnh báo mất kết nối theo dependency graph.
- Alert Suppression metadata: đánh dấu cảnh báo phụ thuộc mà không xóa alert gốc.
- Root Cause Engine: tự chạy nền và cập nhật sự cố gốc.
- Service Impact: gom thiết bị theo dịch vụ và đánh giá Hoạt động / Suy giảm / Gián đoạn.

## Kết quả kiểm thử tự động
- Compile toàn bộ Python: **PASS**.
- Migration database v3.10: **PASS**.
- Mã hóa Credential + xác thực mật khẩu: **PASS**.
- Alert Engine cũ: **PASS**.
- Device Profile: **PASS**.
- Site/Group/Maintenance: **PASS**.
- SLA/Incident/Capacity: **PASS**.
- Dependency/RCA/Service Impact: **PASS**.
- Import ứng dụng: **PASS**.

## GUI smoke test
Khởi tạo tuần tự toàn bộ các hàm `show_*` thực tế dưới Tkinter/Xvfb với quyền Admin: **43/43 màn hình PASS**.

## Kiểm thử chức năng v3.10
1. Tạo 2 thiết bị QA dạng Core -> Access.
2. Tạo dependency Core là cha của Access.
3. Tạo cảnh báo Offline cho cả Core và Access.
4. Chạy RCA và xác nhận cảnh báo Access được tương quan về Core: **PASS**.
5. Tạo managed service chứa Access là thành viên bắt buộc.
6. Xác nhận service chuyển sang **Gián đoạn** khi Access/Root Cause đang lỗi: **PASS**.

## Giới hạn cần kiểm thử với hạ tầng thật
- Chiều dependency nhập từ topology cần người quản trị xác nhận vì liên kết vật lý không luôn đồng nghĩa với phụ thuộc nghiệp vụ.
- RCA hiện tập trung vào cảnh báo connectivity (Offline/Down/Ping/Unreachable); các loại RCA sâu như BGP, STP, WAN circuit hoặc application dependency cần profile/rule bổ sung.
- Chức năng không tự xóa hoặc đóng alert phụ thuộc; suppression được lưu riêng để bảo toàn lịch sử và phục vụ audit.
