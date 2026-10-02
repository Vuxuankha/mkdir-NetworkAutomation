# Báo cáo kiểm tra lại — NetworkAutomation 1.5.1

Ngày kiểm tra: 02/10/2026. Đầu vào: `mkdir-NetworkAutomation (2).zip`, VERSION.txt ghi **1.5.0**. Bản sửa trong báo cáo này được tạo trực tiếp từ file đó. Các tính năng bảo mật/sao lưu của bản 2.0.0 đã bàn giao trước đây không có trong đầu vào này.

## Kết quả

| Hạng mục | Kết quả thực tế |
|---|---|
| Unit test trên gói gốc | 136 test: 131 đạt, 2 thất bại, 3 lỗi |
| Unit test sau sửa | **121/121 đạt**: 111 test chức năng đang dùng và 10 test hồi quy mới |
| Test AI cũ | 25 test thuộc các module AI đã bị gỡ khỏi ứng dụng được chuyển sang `legacy_disabled_ai`; không tính là test đạt của bản phát hành |
| Regression | **11/11 đạt**: compile, schema, mã hóa/mật khẩu, alert, profile, site/group, SLA/incident, dependency/service, worker core, SNMPv3/driver, import main |
| Regression không đụng dữ liệu vận hành | Đạt: DB đang mở WAL được giữ nguyên byte và giữ nguyên dữ liệu sau khi chạy regression |
| Migration bản sao dữ liệu tải lên | Đạt: giữ số dòng thiết bị, tài khoản, credential và config backup; DB quick_check ok; credential giải mã được bằng khóa cũ |
| Snapshot nâng cấp 1.5.1 | Đạt: một snapshot trước nâng cấp, giữ khóa credential |
| Dependency check | Đã cài requirements.txt; import được toàn bộ pandas/openpyxl/Paramiko/cryptography/PySNMP/Tkinter; `pip check` không phát hiện dependency hỏng |
| Giao diện trực quan và DPI | Chưa kiểm chứng: môi trường không có display |
| Windows EXE/Setup/Service, thiết bị mạng thật | Chưa chạy nghiệm thu tại đây |

Số lượng test sau sửa giảm vì các test AI cũ được lưu trữ theo đúng phạm vi phát hành ghi trong README 1.4/1.5 và REMOVE_OLD_AI_MODULES.bat. Không sửa assertion để biến một chức năng còn sử dụng bị lỗi thành test đạt. Mã/test cũ vẫn được giữ trong thư mục lưu trữ.

## Lỗi đã sửa

| ID | Lỗi và tác động | Cách sửa |
|---|---|---|
| QA-01 | Test Gemini gọi hàm đã bỏ; mã AI cũ mâu thuẫn tiêu chí bản không AI và giao diện tối | Chuyển 6 module và 5 file test/UI AI cũ sang `legacy_disabled_ai`, giữ nguyên nội dung để tra cứu |
| QA-02 | Callback Server Monitor dùng `self.current_user` không tồn tại → AttributeError khi có hoạt động | Gọi callback `self.add_activity` của ứng dụng |
| QA-03 | Worker Server Monitor gọi Tk.after và callback giao diện; lambda lỗi giữ biến `exc` đã hết phạm vi → lỗi GUI hoặc NameError | Worker chỉ gửi dữ liệu/chuỗi lỗi vào queue; main thread poll rồi cập nhật UI |
| QA-04 | Bấm Chạy kiểm tra nhiều lần sinh nhiều worker; rời trang vẫn tiếp tục toàn bộ danh sách | Cờ busy, vô hiệu hóa nút lúc chạy, stop event khi tree bị hủy, dừng trước target kế tiếp |
| QA-05 | Đóng/đăng xuất không đợi worker Server Monitor hoàn tất | Theo dõi worker và đợi trước khi hủy root; tác vụ đang kiểm tra một target được phép kết thúc trong timeout hiện có |
| QA-06 | HTTP cổng 443 và HTTPS cổng 80 bị bỏ port vì dùng chung danh sách 80/443; IPv6 URL thiếu ngoặc | Chọn cổng mặc định theo protocol và bọc IPv6 bằng dấu ngoặc vuông |
| QA-07 | Form Server Monitor chấp nhận cổng ngoài 1–65535, protocol bất kỳ hoặc URL thay cho host | Kiểm tra host/port/protocol trước khi ghi DB |
| QA-08 | regression_test.py dùng database đang chạy, copy DB không bao gồm WAL rồi copy ngược; đường snapshot cố định | Chạy child process với thư mục dữ liệu tạm; snapshot chỉ ở thư mục tạm riêng |
| QA-09 | Build chỉ chạy regression, bỏ qua các unit test đang thất bại; compile cả môi trường/build không cần thiết | Build gọi tools/run_release_checks.py để chạy unit + regression trên dữ liệu tạm, bỏ môi trường/build khi compile |
| QA-10 | Test mô phỏng có thể đạt dù máy thiếu Paramiko/PySNMP vì các đường import SSH/SNMP chưa được thực thi | Runner kiểm tra import dependency bắt buộc trước khi chạy unit/regression; thiếu thư viện thì trả lỗi rõ ràng |

Metadata VERSION.txt, version_info.txt, installer và tài liệu được đồng bộ thành 1.5.1. Không thay dữ liệu vận hành trong ZIP bằng dữ liệu test. Bản EXE/Setup có sẵn trong ZIP gốc, nếu có, là sản phẩm build cũ: cần build lại từ code 1.5.1 để dùng các bản sửa này.

## Các điểm còn cần xử lý trước khi coi là bản dùng production đã nghiệm thu

1. Một số luồng SSH còn dùng `AutoAddPolicy`; chúng tự chấp nhận host key lạ. Đây là điểm bảo mật chưa sửa trong bản QA này, cần chuyển sang kiểm tra host key và quy trình đăng ký khóa đã xác minh.
2. Đăng nhập 1.5.1 vẫn chưa có giới hạn thử sai/khóa tạm; không có timeout/thu hồi phiên như bản 2.0.0.
3. Quyền ở nhiều trang cũ dựa vào vai trò trong session/menu. Account backend đã kiểm tra quyền DB, nhưng toàn bộ các thao tác khác cần kiểm thử ma trận Admin/Operator/Viewer riêng.
4. Khôi phục cấu hình thiết bị ở module cũ gửi lệnh shell theo thời gian chờ cố định; chưa có bằng chứng xác nhận thiết bị áp dụng thành công. Cần nghiệm thu theo hãng/firmware.
5. Một số module cũ khác cũng còn callback Tk từ worker. Bản QA này sửa và kiểm thử riêng Server Monitor, không khẳng định toàn bộ ứng dụng đã xử lý xong an toàn luồng GUI.
6. Cần chạy UI smoke trên Windows có desktop, build/cài EXE, kiểm tra service và thử thiết bị thật. Không suy ra kết quả đó từ unit test mô phỏng.

## Chạy lại trên máy Windows

Đóng ứng dụng và dừng service trước khi chép code mới. Giữ nguyên database, `.credential.key`, known_hosts, reports, backups và cấu hình đường dẫn dữ liệu. Không chép database của một cài đặt khác lên dữ liệu đang dùng.

```bat
py -3 -m pip install -r requirements.txt
py -3 tools/run_release_checks.py
py -3 tests/ui_accounts_smoke.py
py -3 tests/ui_all_pages_smoke.py
```

`tools/run_release_checks.py` và `regression_test.py` dùng dữ liệu tạm. Các UI smoke hiện có tắt engine nền và dùng dữ liệu tạm, cần máy có Tk/display. Mã AI cũ được lưu trữ, không chạy lại các test đó như một phần release hiện tại.

Chạy BUILD_WINDOWS.bat để dựng lại EXE, rồi BUILD_INSTALLER.bat khi cần Setup. Với thư mục cũ còn chứa module/test AI trước khi cập nhật, dùng REMOVE_OLD_AI_MODULES.bat đã có trong dự án sau khi sao lưu. Nhật ký test trước/sau nằm trong QA_BASELINE_20261002.txt và QA_TEST_OUTPUT_1.5.1.txt.

Môi trường đã kiểm tra: Linux/Python 3.12. Dependency versions thực tế ghi trong QA_ENVIRONMENT_1.5.1.txt. Kết luận: các test đang sử dụng đã đạt sau sửa; chưa đủ bằng chứng để xác nhận EXE Windows, thiết bị thật hoặc bảo mật toàn diện đã nghiệm thu.
