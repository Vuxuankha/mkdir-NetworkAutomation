# Hướng dẫn sử dụng Network Automation NMS - Bản tiếng Việt

## Khởi động
1. Cài Python 3.10 trở lên.
2. Chạy `pip install -r requirements.txt`.
3. Chạy `python main.py`.

## Các chức năng
- **Tổng quan / NOC:** xem nhanh thiết bị, trạng thái và cảnh báo.
- **Tự động phát hiện / Quét mạng:** tìm các host đang hoạt động trong subnet.
- **Giám sát Ping:** kiểm tra online/offline, độ trễ cơ bản.
- **Quản lý IP/MAC:** theo dõi ánh xạ IP, MAC, hostname và ghi chú.
- **Thiết bị mạng:** quản lý router, switch, AP, firewall và thiết bị khác.
- **Giám sát SNMP:** đọc sysName, uptime, trạng thái và lưu lượng interface qua SNMP v2c.
- **Giám sát nhiều cổng:** kiểm tra nhiều ifIndex của switch cùng lúc.
- **Sức khỏe mạng:** kiểm tra độ trễ, mất gói, sysName, uptime và sysDescr.
- **Sơ đồ mạng:** quản lý và hiển thị liên kết giữa các thiết bị.
- **Tự động hóa SSH:** chạy mẫu lệnh và sao lưu running-config.
- **Truy cập từ xa:** kiểm tra TCP port và mở SSH/Telnet/RDP/Web.
- **Sao lưu cấu hình / Lịch sao lưu:** lưu cấu hình và tự động sao lưu SSH theo lịch.
- **Lịch tác vụ:** chạy Ping, kiểm tra TCP và cảnh báo định kỳ khi ứng dụng đang mở.
- **Cảnh báo:** quản lý cảnh báo, xác nhận và đóng cảnh báo.
- **Thông báo:** cấu hình Telegram và SMTP Email.
- **Báo cáo:** xuất Excel/CSV.
- **Nhật ký hệ thống:** tra cứu hoạt động của ứng dụng.
- **Cài đặt:** cấu hình subnet, timeout, chu kỳ giám sát và thư mục xuất.

## Lưu ý SNMP
Thiết bị cần bật SNMP v2c và cho phép máy chạy phần mềm truy cập UDP/161. Community mặc định thường là `public`, nhưng nên dùng community riêng trong mạng thực tế.

## Lưu ý SSH
SSH Automation cần tài khoản hợp lệ trên thiết bị. Mật khẩu của lịch sao lưu chỉ được giữ trong RAM của phiên chạy và phải nhập lại sau khi mở lại chương trình.

## Giao diện thanh chức năng v3.2

Thanh bên đã được gom thành các nhóm nhỏ để dễ sử dụng:

- **Tổng quan**: Tổng quan, Trung tâm giám sát NOC.
- **Khám phá & Giám sát**: Tự động phát hiện, Quét mạng, Giám sát Ping, Sức khỏe mạng, SNMP, Giám sát nhiều cổng.
- **Quản lý mạng**: Quản lý thiết bị, IP/MAC, Thiết bị mạng, Sơ đồ mạng.
- **Tự động hóa**: SSH, Truy cập từ xa, Sao lưu cấu hình, Lịch sao lưu, Lịch tác vụ.
- **Cảnh báo & Báo cáo**: Cảnh báo, Thông báo, Báo cáo, Nhật ký hệ thống.
- **Hệ thống**: Cài đặt.

Bấm vào tên một nhóm để **thu gọn / mở rộng** các chức năng bên trong.

Chức năng **Tự căn chỉnh kích thước** đã được loại bỏ. Cửa sổ trở về kích thước mặc định 1400×800 và người dùng có thể tự kéo thay đổi kích thước cửa sổ như bình thường.

## Nâng cấp v3.3
- **CPU / RAM SNMP:** đọc CPU bằng preset Cisco IOS hoặc HOST-RESOURCES-MIB; RAM hỗ trợ OID tùy chỉnh vì OID bộ nhớ khác nhau giữa hãng/model.
- **Giám sát cổng nâng cao:** xem trạng thái, tên cổng, tốc độ, lỗi IN/OUT và discard IN/OUT; dữ liệu được lưu vào SQLite.
- **Quy tắc cảnh báo:** đặt ngưỡng CPU, RAM, mất gói, độ trễ hoặc lỗi cổng; nút “Đánh giá ngay” tạo cảnh báo nếu ngưỡng bị vi phạm.
- **Biểu đồ lịch sử:** xem Traffic IN/OUT, CPU hoặc RAM theo 24 giờ, 7 ngày và 30 ngày từ dữ liệu đã thu thập.

Lưu ý: CPU/RAM không có một OID duy nhất dùng cho mọi hãng. Nếu preset không phù hợp, nhập OID của đúng model vào phần OID tùy chỉnh.

## Nâng cấp v3.4

### Tự dựng Topology LLDP/CDP
Vào **Quản lý mạng → Tự dựng Topology LLDP/CDP**. Nhập SNMP Community rồi bấm **Phát hiện LLDP/CDP**. Chức năng đọc bảng láng giềng LLDP và Cisco CDP qua SNMP v2c. Nếu tên láng giềng khớp với tên/IP của thiết bị đã quản lý, liên kết được tự thêm vào **Sơ đồ mạng**. Thiết bị phải bật LLDP/CDP và cho phép SNMP đọc MIB tương ứng.

### Alert Rules chạy nền
Quy tắc cảnh báo hiện được đánh giá tự động khoảng mỗi 60 giây khi ứng dụng đang mở. Hệ thống lưu trạng thái từng rule theo từng host để tránh tạo cảnh báo lặp liên tục. Khi chỉ số trở về ngưỡng bình thường, cảnh báo Rule đang mở của host đó được đóng tự động. Nút **Đánh giá ngay** vẫn dùng được để kiểm tra thủ công.

### Port Down / Up và lịch sử sự cố
Có thể tạo rule dựa trên các chỉ số hiện có. Trạng thái vi phạm/phục hồi được lưu trong `alert_rule_state`; bảng `alerts` tiếp tục là lịch sử sự cố. Giám sát cổng nâng cao lưu trạng thái và counter SNMP vào `interface_samples` để phục vụ điều tra lịch sử.

## Nâng cấp v3.5 - Bảo mật, Credential, Backup và phân quyền

### 1. Quản lý Credential
- Vào **Hệ thống → Quản lý Credential**.
- Tạo credential loại **SSH** hoặc **SNMPv2c**.
- Mật khẩu/community được mã hóa bằng Fernet trước khi lưu vào SQLite.
- Có thể gán credential cho từng thiết bị theo mục đích SSH / SNMP / Backup.
- Có nút **Kiểm tra SSH** để xác nhận credential trước khi dùng.

> Khóa mã hóa nằm trong `database/.credential.key`. Không chia sẻ file này. Nếu mất khóa, các mật khẩu đã mã hóa sẽ không giải mã lại được.

### 2. Lịch sao lưu bảo mật
- Vào **Tự động hóa → Lịch sao lưu bảo mật**.
- Chọn thiết bị và credential SSH đã tạo.
- Đặt lệnh backup, ví dụ `show running-config`, cùng chu kỳ phút.
- Chương trình dùng credential mã hóa, không yêu cầu nhập lại mật khẩu mỗi lần mở ứng dụng.
- Backup được lưu vào thư mục `backups/` và đồng thời ghi lịch sử vào database.

### 3. So sánh cấu hình
- Vào **Tự động hóa → So sánh cấu hình**.
- Chọn hai bản backup A và B.
- Bấm **So sánh** để xem khác biệt theo dạng unified diff: dòng `-` là nội dung cũ, dòng `+` là nội dung mới.

### 4. Người dùng & Phân quyền
- Vào **Hệ thống → Người dùng & Phân quyền**.
- Có 3 vai trò:
  - **Admin**: toàn quyền, gồm credential, user và cài đặt.
  - **Operator**: vận hành, quản lý thiết bị, backup, SSH, cảnh báo; không quản lý user/credential/cài đặt.
  - **Viewer**: chỉ truy cập các màn hình giám sát, topology, cảnh báo và báo cáo.
- Mật khẩu người dùng được băm PBKDF2-SHA256, không lưu mật khẩu gốc.
- Khi chưa có tài khoản, ứng dụng chạy ở chế độ **local-admin** để bạn tạo Admin đầu tiên. Từ lần mở sau, nếu có tài khoản hoạt động, chương trình sẽ yêu cầu đăng nhập.

## Bản vá v3.5.1 - SNMP và kiểm thử ổn định

### Kiểm tra SNMP trước khi đọc CPU/RAM
Trong **Khám phá & Giám sát → CPU / RAM SNMP**, bản v3.5.1 có thêm nút **Kiểm tra SNMP**.

Chức năng này đọc các OID chuẩn `sysDescr`, `sysObjectID`, `sysUpTime` và `sysName` để xác nhận thiết bị có phản hồi SNMP v2c hay không. Nếu thiết bị phản hồi, chương trình hiển thị tên hệ thống, mô tả, uptime và thử nhận diện hãng. Với Cisco hoặc máy dùng HOST-RESOURCES-MIB phù hợp, chương trình tự chọn preset CPU tương ứng.

Nếu Ping được nhưng SNMP không phản hồi, chương trình sẽ báo rõ: thiết bị không phản hồi SNMP UDP/161 và gợi ý kiểm tra SNMP đã bật, community và firewall. Đây là tình huống khác với lỗi kết nối IP.

### Sửa lỗi Python 3.14
Đã sửa các callback Tkinter giữ biến exception qua `lambda`, tránh lỗi `NameError: cannot access free variable` trên Python 3.14.

### Sửa migration và Alert Rules
- Toàn bộ schema NMS được migrate trước khi mở các màn hình.
- Bảng `alerts` tự bổ sung cột `severity` nếu database cũ chưa có.
- Sửa lỗi đếm số cảnh báo phục hồi trong Alert Rules.
- Đăng nhập đã được nối vào luồng khởi động thực tế: chưa có user thì dùng `local-admin`; đã có user thì hiện màn hình đăng nhập.

## Nâng cấp v3.6 - Ổn định vận hành

### Dịch vụ giám sát nền
Vào **Hệ thống > Dịch vụ giám sát nền**. Worker nền sẽ định kỳ Ping các thiết bị trong **Thiết bị mạng**, lưu độ trễ/mất gói vào lịch sử, cập nhật Online/Offline và kích hoạt Alert Rules. Có thể chọn chu kỳ từ 15 giây và số ngày giữ dữ liệu. Dữ liệu cũ trong health/interface/SNMP samples được dọn tự động.

### Nhật ký Audit
Vào **Cảnh báo & Báo cáo > Nhật ký Audit** (Admin). Hệ thống ghi phiên mở/đóng ứng dụng và các hoạt động được các module gửi về callback, kèm tài khoản, vai trò, trang và thời gian.

### Khôi phục cấu hình
Vào **Tự động hóa > Khôi phục cấu hình** (chỉ Admin). Chọn một backup để xem trước. Khi khôi phục, chương trình yêu cầu xác nhận, tạo **safety backup** cấu hình hiện tại qua SSH trước, sau đó mới gửi cấu hình đã chọn. Vì cú pháp cấu hình khác nhau giữa các hãng, hãy thử trên thiết bị lab trước khi dùng production.

### Regression test
Chạy `python regression_test.py` để kiểm tra compile, migration v3.6, mã hóa/mật khẩu, Alert Engine và import ứng dụng sau mỗi lần nâng cấp.

## Nâng cấp v3.7 - Hồ sơ thiết bị theo hãng

Vào **Quản lý mạng → Hồ sơ thiết bị theo hãng** để gán profile cho từng thiết bị.

Hệ thống có sẵn profile cho **Cisco IOS/IOS-XE, MikroTik RouterOS, Ruijie/Reyee, Aruba/HPE và Generic HOST-RESOURCES**. Có thể chọn thiết bị rồi bấm **Tự nhận diện SNMP** để đọc `sysDescr/sysObjectID` và gán profile phù hợp, hoặc gán thủ công.

Profile được dùng để:
- nạp OID CPU/RAM phù hợp hơn trong **CPU / RAM SNMP**;
- tự điền lệnh backup khi tạo **Lịch sao lưu bảo mật**;
- lưu kiểu discovery LLDP/CDP theo hãng;
- làm nền cho các bản sau khi triển khai command template/restore theo từng hệ điều hành mạng.

Bạn có thể bấm **Thêm hồ sơ tùy chỉnh** nếu model/firmware sử dụng OID khác. OID CPU/RAM không được tự đoán cho những hãng/model chưa có MIB chắc chắn, để tránh hiển thị số liệu sai.

## Nâng cấp v3.8 - Site / Nhóm / VLAN và Lịch bảo trì

### Site / Nhóm / VLAN
Vào **Quản lý mạng → Site / Nhóm / VLAN** để tổ chức thiết bị theo địa điểm, nhóm nghiệp vụ, VLAN và tags.

- **Thêm Site**: tạo địa điểm như Trụ sở, Chi nhánh 1, Phòng máy.
- **Thêm nhóm**: nhóm thiết bị như Core, Access, Camera, Server, Wi-Fi.
- **Gán Site / Nhóm**: gán từng thiết bị vào Site và nhóm.
- **Sửa VLAN / Tags**: thêm VLAN hoặc nhãn để dễ tìm và phân loại.

### Lịch bảo trì
Vào **Cảnh báo & Báo cáo → Lịch bảo trì** để tạo khoảng thời gian bảo trì theo:

- Thiết bị cụ thể.
- Toàn bộ Site.
- Toàn bộ nhóm.
- Tất cả thiết bị.

Khi tùy chọn **Tắt cảnh báo Alert Rules trong thời gian bảo trì** được bật, Alert Engine sẽ không tạo cảnh báo mới cho thiết bị thuộc phạm vi đang bảo trì. Điều này giúp tránh cảnh báo giả khi nâng cấp firmware, thay switch, bảo trì điện hoặc thay đổi cấu hình có kế hoạch.

Thời gian nhập theo định dạng `YYYY-MM-DD HH:MM:SS`.

## Nâng cấp v3.9 - SLA, Trung tâm sự cố và Phân tích dung lượng

### SLA & Độ sẵn sàng
Vào **Tổng quan → SLA & Độ sẵn sàng** để tạo mục tiêu SLA cho toàn hệ thống, từng thiết bị, Site hoặc nhóm. Hệ thống tính tỷ lệ sẵn sàng từ dữ liệu `health_samples` và loại trừ các mẫu nằm trong **Lịch bảo trì** đang áp dụng. Kết quả có thể xuất CSV.

- **All**: tính cho toàn bộ thiết bị có IP.
- **Device**: nhập Host/IP hoặc Scope ID của thiết bị.
- **Site / Group**: dùng ID của Site hoặc nhóm đã tạo ở màn hình Site / Nhóm / VLAN.
- **Mục tiêu %**: ví dụ 99.0, 99.9 hoặc 99.99.
- **Chu kỳ ngày**: số ngày lịch sử dùng để tính SLA.

Thiết bị cần có dữ liệu giám sát nền để SLA có đủ mẫu. Nếu chưa có dữ liệu, trạng thái sẽ hiển thị **Chưa đủ dữ liệu** thay vì tự suy đoán.

### Trung tâm sự cố
Vào **Cảnh báo & Báo cáo → Trung tâm sự cố**. Chức năng **Đồng bộ cảnh báo** gom các cảnh báo của cùng Host thành một sự cố trong cửa sổ thời gian gần nhau. Sự cố có thể ở trạng thái **Open**, **Acknowledged** hoặc **Resolved**.

- **Xác nhận**: ghi nhận người đang xử lý sự cố.
- **Đóng sự cố**: đóng sự cố và các cảnh báo liên kết.
- Nếu tất cả cảnh báo liên kết đã được đóng bởi Alert Engine, sự cố sẽ tự chuyển sang Resolved khi đồng bộ lại.
- Viewer chỉ xem; Operator/Admin có thể xác nhận và đóng.

### Phân tích dung lượng
Vào **Khám phá & Giám sát → Phân tích dung lượng**. Nhập Host/IP và chọn 24 giờ, 7 ngày, 30 ngày hoặc 90 ngày. Hệ thống tổng hợp:

- CPU %.
- RAM %.
- Độ trễ.
- Mất gói.
- Tổng lỗi cổng và discard từ lịch sử interface.
- Xu hướng Tăng / Ổn định / Giảm dựa trên nửa đầu và nửa sau của chuỗi dữ liệu.

Đây là công cụ hỗ trợ capacity planning; kết luận phụ thuộc chất lượng và mật độ dữ liệu thu thập.

### Regression test v3.9
Chạy `python regression_test.py`. Bộ test tạo snapshot database trước khi kiểm thử và tự khôi phục database về trạng thái ban đầu sau khi xong, tránh để lại dữ liệu QA trong database vận hành.



## Nâng cấp v3.10 - Dependency, RCA và mức ảnh hưởng dịch vụ

### Phụ thuộc thiết bị
Vào **Quản lý mạng → Phụ thuộc thiết bị** để khai báo quan hệ cha/con giữa router, firewall, core switch, access switch, AP, server hoặc thiết bị khác. Thiết bị cha là thành phần mà thiết bị con phụ thuộc để kết nối hoặc cung cấp dịch vụ.

Có thể bấm **Nhập từ Sơ đồ mạng** để tạo nhanh quan hệ dependency từ các liên kết đã khai báo trong Topology. Sau khi nhập, nên kiểm tra lại chiều cha → con vì liên kết vật lý không phải lúc nào cũng phản ánh đúng dependency nghiệp vụ.

### Phân tích nguyên nhân gốc (RCA)
Vào **Cảnh báo & Báo cáo → Phân tích nguyên nhân gốc**. Hệ thống lấy các cảnh báo mất kết nối đang mở và so sánh với dependency graph. Nếu một thiết bị con mất kết nối đồng thời thiết bị cha của nó cũng đang lỗi, cảnh báo của thiết bị con được đánh dấu là **cảnh báo phụ thuộc** thay vì xem như một nguyên nhân độc lập.

Ví dụ: Core Switch mất kết nối làm 10 Access Switch phía sau đồng thời Offline. RCA sẽ giữ Core Switch là ứng viên nguyên nhân gốc và tương quan 10 cảnh báo Access Switch thành triệu chứng phụ thuộc. Alert gốc không bị xóa; trạng thái suppression được lưu riêng để vẫn giữ đầy đủ lịch sử.

Engine RCA tự chạy nền khoảng mỗi 60 giây và cũng có nút **Phân tích ngay**.

### Dịch vụ & Mức ảnh hưởng
Vào **Quản lý mạng → Dịch vụ & Mức ảnh hưởng** để tạo dịch vụ nghiệp vụ như Internet văn phòng, Camera, Wi-Fi, ERP hoặc Data Center. Sau đó gán các thiết bị thành viên.

- Nếu thiết bị thành viên **bắt buộc** bị Offline hoặc trở thành nguyên nhân gốc, dịch vụ hiển thị **Gián đoạn**.
- Nếu chỉ thiết bị không bắt buộc bị lỗi, dịch vụ hiển thị **Suy giảm**.
- Nếu các thành viên đều bình thường, dịch vụ hiển thị **Hoạt động**.

Chức năng này giúp chuyển từ góc nhìn “thiết bị nào hỏng” sang “dịch vụ nào đang bị ảnh hưởng”.

### Regression test v3.10
Chạy `python regression_test.py`. Ngoài các test cũ, v3.10 kiểm tra thêm migration dependency/RCA/service impact, tạo quan hệ cha-con, tương quan cảnh báo con với cảnh báo gốc và tính trạng thái dịch vụ.

## Nâng cấp v3.12 - SNMPv3 & Vendor Driver Engine

### Credential SNMPv3
Vào **Hệ thống → Credential SNMPv3**. Admin có thể tạo credential gồm username, security level, Auth protocol, Privacy protocol, Context name và port. Auth password/Privacy password được mã hóa bằng Fernet trong database và không hiển thị lại sau khi lưu.

- `noAuthNoPriv`: chỉ username, không xác thực/mã hóa.
- `authNoPriv`: xác thực nhưng không mã hóa payload.
- `authPriv`: xác thực và mã hóa; đây là mức nên dùng khi thiết bị hỗ trợ.

Có thể gán một credential SNMPv3 cho từng thiết bị để chuẩn bị cho các tác vụ SNMP bảo mật.

### Chẩn đoán SNMP v2c/v3
Vào **Khám phá & Giám sát → Chẩn đoán SNMP v2c/v3**.

1. Nhập IP/Host.
2. Chọn `v2c` và nhập Community, hoặc chọn `v3` và chọn Credential SNMPv3.
3. Bấm **Kiểm tra & nhận diện**.
4. Hệ thống đọc `sysName`, `sysDescr`, `sysObjectID`, `sysUpTime`.
5. Nếu nhận diện được hãng, hệ thống gán Vendor Driver tương ứng cho thiết bị đã có trong danh sách.
6. Nếu driver có OID CPU/RAM, hệ thống thử đọc thêm các OID này và hiển thị kết quả.

Nếu SNMPv3 báo lỗi, kiểm tra username, security level, Auth/Privacy protocol, password, Context name và UDP/161. Thiết bị và máy quản trị phải hỗ trợ cùng thuật toán.

### Vendor Driver Engine
Vào **Quản lý mạng → Vendor Driver Engine**. Driver mặc định gồm Cisco IOS/IOS-XE, MikroTik RouterOS, Ruijie/Reyee, Aruba/HPE và Generic HOST-RESOURCES.

Mỗi driver có thể lưu:
- chuỗi nhận diện `sysObjectID`;
- regex cho `sysDescr`;
- OID CPU/RAM;
- lệnh backup cấu hình;
- lệnh lưu cấu hình;
- chế độ LLDP/CDP;
- mức ưu tiên nhận diện.

Có thể tạo driver tùy chỉnh cho model/firmware riêng mà không sửa core application.

### Thư viện SNMPv3
v3.12 dùng `pysnmp>=7.1` cho SNMPv3. Nếu chưa cài dependency, chạy lại:

```bash
pip install -r requirements.txt
```

SNMPv2c cũ vẫn hoạt động bằng engine nội bộ, không bắt buộc phải chuyển toàn bộ thiết bị sang SNMPv3 ngay lập tức.
