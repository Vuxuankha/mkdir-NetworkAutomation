# NetworkAutomation v3.13 - Tự động IP/Excel

## Vị trí chức năng

Mở **TỰ ĐỘNG HÓA > Tự động IP/Excel** trên menu bên trái. Menu có thanh cuộn.
Đây là một màn hình riêng, không thay thế các màn hình cũ. Chỉ Admin/Operator được chạy.

Ba tab: **Nhập IP / Chạy**, **Hồ sơ kết nối**, **Lịch sử / Báo cáo**.
Luồng mới không tự chạy khi mở ứng dụng. Các dịch vụ nền cũ giữ chính sách cũ.

## Khởi động trên Windows

Giải nén và mở Terminal/CMD trong thư mục chứa main.py.
Cài Python có Tkinter, sau đó cài thư viện và chạy:

```bat
py -3 -m pip install -r requirements.txt
py -3 main.py
```

Sau khi đã cài thư viện, có thể nhấp đúp `START_WINDOWS.bat`.
File BAT không tự cài thư viện, không tự quét mạng. Đây là bộ mã nguồn Python, không phải file EXE.
Máy chạy phải có tuyến kết nối/VPN đến các thiết bị.

## Cấu hình một lần

1. Vào tab **Hồ sơ kết nối**, tạo hoặc sửa hồ sơ `Default`.
   - `assigned`: dùng Credential SNMPv3 đã gán cho thiết bị; nếu chưa gán thì dùng SNMP profile v2c đã lưu. Không thử ngẫu nhiên nhiều tài khoản.
   - `off`: không truy cập SNMP.
   - `v2c`: nhập Community và port. Community của hồ sơ mới được mã hóa trong database.
   - `v3`: chọn Credential từ **HỆ THỐNG > Credential SNMPv3**. Port, username, Auth, Privacy và context dùng theo Credential đó.
2. Quay lại tab **Nhập IP / Chạy**, chọn hồ sơ mặc định, các tác vụ và **Lưu lựa chọn**.
3. Đánh dấu xác nhận quyền quản trị. Bật **Tự chạy sau khi nạp IP/Excel**.
   Sau đó nhập Excel hoặc dán IP và bấm **Nạp IP**, luồng sẽ tự bắt đầu.

Chỉ Admin được lưu hồ sơ. Ô xác nhận quyền không được ghi nhớ sau khi rời màn hình.
Để tự chạy ngay khi chọn Excel, đánh dấu xác nhận trước. Nếu chưa xác nhận, file chỉ được nạp chứ chưa quét.
Không sửa Credential/driver trong khi đang chạy.

## Excel và danh sách IP

Mẫu: `templates/IP_List_Mau.xlsx`. IP trong mẫu chỉ để minh họa; thay bằng IP của bạn.
Sheet `IP_List` được ưu tiên; nếu không có thì đọc sheet đầu tiên.
Dòng 1 là tiêu đề, dữ liệu từ dòng 2.

| Cột | Yêu cầu |
|---|---|
| IP | Bắt buộc. Nhận một IPv4/IPv6 cụ thể mỗi dòng. |
| Ten_thiet_bi | Không bắt buộc. Dùng khi thêm thiết bị mới; không ghi đè nhãn cũ. |
| Ho_so | Không bắt buộc. Tên phải trùng hồ sơ đã lưu; trống = hồ sơ mặc định. |

Tên cột tiếng Việt `Địa chỉ IP`, `Tên thiết bị`, `Hồ sơ` cũng được nhận.
Không đưa mật khẩu vào file. Tối đa 2048 IP/lượt và 8 MB/file .xlsx.
Không nhận .xls, CIDR/dải IP, hostname, IPv6 scope ID, multicast/broadcast, công thức trong cột đầu vào.
IP trùng giữ bản ghi đầu tiên và báo số bỏ qua. Có dòng sai thì từ chối cả file để bạn sửa trước.
Nạp danh sách mới thay danh sách của luồng này; không xóa thiết bị cũ trong NMS.

## Tác vụ thực hiện

- Ghi nhận IP vào danh sách thiết bị, loại trùng. Ping và TCP chạy độc lập với SNMP.
- Đọc SNMP v2c/v3: sysName, sysDescr, sysObjectID, uptime; chọn driver, giữ driver đã gán thủ công.
- Đọc CPU/RAM theo OID của driver. Driver thiếu OID hoặc thiết bị không hỗ trợ sẽ báo SKIP/WARN, không tự đoán RAM/CPU.
- Đọc IF-MIB, counter 64-bit khi có, fallback 32-bit; tính lưu lượng từ hai mẫu hợp lệ. Không báo 0 bps thay cho mẫu chưa đủ; counter reset/tràn không được biến thành lưu lượng ảo.
- Đọc LLDP và CDP khi driver chỉ định. Chỉ nối topology khi tên/IP láng giềng khớp duy nhất thiết bị đã quản lý. Không suy đoán sơ đồ từ IP.
- Đánh giá quy tắc cảnh báo, đồng bộ sự cố/RCA bằng engine hiện có. Engine này dùng phạm vi dữ liệu chung của NMS, không chỉ IP vừa nhập. Không tự tạo ngưỡng/SLA/quan hệ phụ thuộc.
- Xuất báo cáo .xlsx sau mỗi lượt, gồm cả lượt bị dừng. Báo cáo không chứa Credential.

Sao lưu SSH và thông báo được cung cấp nhưng **mặc định tắt**.
Sao lưu cần Credential, driver, lệnh đọc được cho phép và host key đã xác minh. Không chạy `save_command`, `write memory`, `reload`, restore hoặc lệnh tùy ý.
Danh sách lệnh backup cho phép: `show running-config`, `/export terse`, `display current-configuration`, `show configuration`.
Thiết bị phải hỗ trợ SSH exec; thiết bị chỉ hỗ trợ shell tương tác/paging có thể không backup được qua luồng này.
Không tự chấp nhận host key lạ. Sau khi xác minh fingerprint, dùng `~/.ssh/known_hosts` hoặc `database/known_hosts` theo định dạng OpenSSH.
File backup có thể chứa thông tin nhạy cảm của thiết bị; quản lý quyền truy cập thư mục.

Thông báo dùng cấu hình Email/Telegram hiện có. Trong bản gốc, secret thông báo được lưu trong phiên; có thể phải nhập lại sau khi mở ứng dụng.
Chỉ gửi cảnh báo mới được tạo trong bước đánh giá và thuộc IP của đợt này, tối đa 50 cảnh báo/lượt; không phải hàng đợi gửi tin bền vững.

## Tiến độ, dừng và chạy lặp

Mặc định 4 worker, timeout 2 giây, SNMP retry 1, tối đa 128 cổng/IP, ngân sách tác vụ mạng 120 giây/IP.
IP có nhiều cổng hoặc phản hồi chậm có thể chỉ thu được một phần. Giới hạn này có thể được sửa trong `Options` trong mã nguồn.
Retry trên giao diện áp dụng cho SNMP; không tự retry lệnh SSH.
Bật **Lặp định kỳ** để chạy tiếp; chu kỳ tính từ khi lượt trước hoàn tất, không chồng lịch.
Bấm **Dừng**: không bắt đầu tác vụ mới; tác vụ đang chờ mạng cần kết thúc hoặc timeout.
Chuyển sang menu khác không dừng luồng. Thoát ứng dụng sẽ yêu cầu dừng và chờ worker.
Bản này chưa cài Windows Service, không chạy khi đóng ứng dụng/tắt máy; cũng không tự tiếp tục sau mất điện.
Chỉ mở một phiên ứng dụng trên cùng database. Không chạy hai bản cũ/mới cùng lúc.
Dịch vụ Ping nền cũ có thể thu thập cùng IP; cân nhắc chọn một nơi thu thập Ping để tránh trùng mẫu.

## Đọc kết quả

`OK`: tác vụ hoàn tất. `WARN`: cần kiểm tra/kết quả một phần. `SKIP`: thiếu điều kiện. `ERROR`: lỗi. `CANCEL`: dừng theo yêu cầu.
**Đã xong lượt / Completed không có nghĩa tất cả tác vụ thành công.** Nhấp đúp dòng kết quả để xem dữ liệu.
Giao diện giữ tối đa 5.000 dòng hiển thị/lượt. Xuất Excel để xem đầy đủ.
Báo cáo: `reports/auto_ip/`. Backup: `backups/auto_ip/`. Báo cáo hiện tại có thể xuất ngay cả khi chưa xong (snapshot tại thời điểm xuất).
Lịch sử riêng lưu trong các bảng `autoip_*`. Bản này chưa tự dọn lịch sử/báo cáo riêng; kiểm tra dung lượng nếu chạy lâu ngày.

## Kiểm thử và giới hạn xác nhận

34 bài kiểm thử mới và 11 kiểm tra hồi quy gốc đã đạt. Đã mở giao diện Tk ảo và thử chọn tab, nhập IP, chạy, dừng, đổi trang, xem lịch sử và xuất Excel.
Giao tiếp thiết bị trong bộ test dùng mô phỏng. Môi trường tạo bản cập nhật chưa có pysnmp/paramiko và không cài được do không kết nối kho gói. Chưa xác nhận kết nối SNMPv3/SSH thật hoặc giao diện trên Windows của bạn.
Nên thử trước 1-2 IP, giữ backup/thông báo tắt, kiểm tra Credential và driver, rồi mới nạp danh sách lớn.

```bat
py -3 -m unittest discover -s tests -v
```

Bộ test mới dùng database/thư mục tạm, không dùng IP/mật khẩu thật. `tests/ui_smoke.py` dùng Pillow và Xvfb cho môi trường QA Linux, không phải bước cần thiết để dùng ứng dụng.

## Tài liệu API tham khảo

- PySNMP 7.1 (GET/GETNEXT, asyncio): https://docs.lextudio.com/pysnmp/v7.1/docs/api-reference
- Tkinter event loop/threading: https://docs.python.org/3.12/library/tkinter.html

Các URL này là tài liệu API, không phải bằng chứng đã kiểm thử trên thiết bị của bạn.
