# Báo cáo test thực tế — NetworkAutomation 1.5.3

Ngày: 02/10/2026. Đầu vào: ZIP 1.5.2 đã bàn giao, được tải lại và kiểm tra đầy đủ. SHA-256 đầu vào: `1d1c2539bb18fba38fde81293d80f0de6dc87b0158b4d39c2af8e1477772d4a8`; 213.209.839 byte, 15.933 entry, không lỗi CRC.

## Kết quả

| Hạng mục | Bằng chứng thực tế |
|---|---|
| Baseline 1.5.2 | 141/141 unit test + 11/11 regression đạt |
| Test SSH mới trước sửa | 9 test: 2 đạt, 4 thất bại, 3 lỗi; gồm SSH transport cục bộ thật |
| Trước sửa GUI | Hai bài UI bị SIGSEGV; test tài khoản đạt. Sau khi xử lý layout, bài 57 trang còn báo callback gọi label đã hủy; form credential làm mất khoảng trắng mật khẩu |
| Trước sửa đóng ứng dụng | Tái hiện root bị hủy khi worker SSH còn chạy |
| Sau sửa 1.5.3 | **155/155 unit test + 11/11 regression đạt**; giữ toàn bộ 141 test cũ, thêm 14 test |
| UI toàn bộ trang | **57/57 trang** dựng/mở ở 1400×800 và 800×600; theme/dialog tối và 3 tab extension đạt, không callback lỗi |
| UI tài khoản | Tạo/sửa/xóa, phân quyền, đổi mật khẩu, adoption Admin, phạm vi Viewer, đăng xuất và footer ở các mức scale 1.33/1.67/2.0 đạt |
| UI bố cục | Trang extension/SSH/settings/scan đạt kiểm tra containment ở 1200×850, 1000×700 và 800×600 |
| UI credential | Form modal giữ nguyên mật khẩu có khoảng trắng đầu/cuối; encrypt/decrypt round trip đạt |
| UI SSH | Trang SSH thực hiện kết nối tới server cục bộ, xác thực mật khẩu chính xác, hiển thị kết quả qua queue, ghi hoạt động và theo dõi worker hoàn tất |
| SSH / sao lưu tích hợp | Client và server Paramiko thật trên loopback; config đúng nội dung, lỗi exit code/rỗng bị từ chối, hai bản cùng giây khác file, stderr 2,3 MB không gây kẹt |
| Lỗi ghi file | Giả lập lỗi flush/replace: không tạo bản sao thành công; đích cũ giữ nguyên; không để lại file tạm |
| Migration bản sao DB gốc | Giữ 93 thiết bị, 3 tài khoản, 0 credential SSH và 1 config backup; quick_check ok; 2 giá trị mã hóa cũ giải mã được |
| Snapshot 1.5.3 | Một snapshot, chứa đúng khóa cũ; dữ liệu gốc trong ZIP được giữ nguyên byte |
| Dependency | Import dependency bắt buộc và pip check đạt |

Các bài GUI chạy với Tk trên **Linux/Xvfb**, có widget và vòng lặp sự kiện thật. Điều này bổ sung bằng chứng giao diện; không phải nghiệm thu Windows. SSH dùng server thử nghiệm cục bộ, không truy cập thiết bị vận hành hay dịch vụ ngoài.

## Các sửa đổi

1. **Sao lưu không kiểm tra exit code và chấp nhận config rỗng.** Luồng secure backup dùng bộ đọc exec chung, kiểm tra mã trả về và từ chối stdout rỗng/whitespace trước khi tạo file hoặc ghi DB. Giữ hỗ trợ thiết bị không trả exit status (-1) như SSH runner cũ; không suy ra lệnh áp dụng cấu hình thành công từ trường hợp này.
2. **Đọc stdout trước stderr bị kẹt khi stderr đầy cửa sổ SSH.** Bộ đọc mới luân phiên lấy cả hai stream, giữ deadline và đóng channel trong finally. stdout và stderr được tách riêng để warning không lẫn vào file cấu hình. Output exec có giới hạn tổng 16 MiB; vượt giới hạn thì báo lỗi.
3. **Hai bản sao cùng thiết bị/cùng giây ghi đè cùng đường dẫn.** File mặc định được cấp tên duy nhất bằng mkstemp; hai bản được kiểm tra nội dung và bản ghi DB riêng biệt. Với đường dẫn đích chỉ định, ghi file tạm, flush/fsync rồi thay đích; lỗi ghi/thay file không làm mất đích cũ.
4. **Layout thay đổi grid ngay trong callback Configure làm Tk crash ở bài test này.** FlowRow gom các yêu cầu và áp dụng khi idle, đồng thời hủy callback chờ khi frame bị hủy. Bài test từng SIGSEGV đã chạy đạt với các assertion cũ được giữ nguyên. Chưa tái hiện riêng lỗi native này trên Windows.
5. **Callback resize trang tài khoản tồn tại sau khi label bị hủy.** Callback kiểm tra widget còn tồn tại và được gỡ đúng binding khi rời trang, giữ các binding khác của parent. Test 57 trang không còn invalid command name.
6. **Form credential tự strip mật khẩu.** Chỉ trim trường mô tả; mật khẩu/community giữ đúng chuỗi người dùng nhập, gồm khoảng trắng đầu/cuối.
7. **Đóng/đăng xuất không đợi worker trang SSH Automation.** Trang đăng ký thread với ứng dụng; shutdown đợi thread hoàn tất trước khi hủy root. Kết quả worker vẫn qua queue; worker không gọi Tk.

Metadata phiên bản/build/installer và README cập nhật thành 1.5.3. Nhật ký QA cũ được giữ để tra cứu. Không sửa assertion của các test đang dùng để làm mất lỗi.

## Những giới hạn còn lại

- EXE/Setup có sẵn trong ZIP là build cũ: **phải build lại từ source 1.5.3**. Chưa chạy Windows EXE/Setup/Service, DPI Windows hoặc thiết bị mạng thật.
- Một số luồng SSH còn AutoAddPolicy; cần quy trình xác minh host key. Đăng nhập vẫn chưa có khóa tạm/timeout phiên như bản 2.0.0 độc lập trước đây.
- Kiểm thử tài khoản không thay cho kiểm tra phân quyền ở mọi thao tác module cũ. Restore cấu hình cần xác nhận kết quả theo từng hãng/firmware.
- Bản sửa này xử lý secure backup và exec runner, FlowRow, account callback, credential form và worker của trang SSH Automation. Các luồng legacy backup/shell/worker khác chưa được chứng nhận toàn bộ.
- Các test vẫn có mô phỏng lỗi DB/file/timeout để kiểm tra xử lý lỗi. Traceback của lỗi được chủ động tiêm trong log unit không đồng nghĩa test thất bại; kết quả cuối cùng là OK.

Không kết luận giá trị thương mại 100 triệu đồng hoặc đã nghiệm thu production chỉ từ các kết quả này.

## Chạy lại

Đóng ứng dụng và dừng service khi cập nhật mã. Giữ database và khóa của cài đặt hiện tại; không chép database từ ZIP lên dữ liệu đang vận hành.

```bat
py -3 -m pip install -r requirements.txt
py -3 tools/run_release_checks.py
py -3 tests/ui_all_pages_smoke.py
py -3 tests/ui_accounts_smoke.py
py -3 tests/ui_pages_smoke.py
py -3 tests/ui_credentials_smoke.py
py -3 tests/ui_ssh_smoke.py
```

Unit/regression và UI smoke dùng dữ liệu tạm. Bài SSH mở server chỉ tại 127.0.0.1 trên cổng tạm. Các bài UI cần desktop/Tk. Sau đó build lại bằng BUILD_WINDOWS.bat/BUILD_INSTALLER.bat và nghiệm thu Windows, service, thiết bị thật.

Nhật ký kèm ZIP: QA_BASELINE_1.5.2_RECHECK.txt; QA_SSH_CASES_BEFORE_1.5.3.txt; QA_UI_*_BEFORE_1.5.3.txt; QA_CREDENTIAL_UI_BEFORE_1.5.3.txt; QA_SHUTDOWN_BEFORE_1.5.3.txt; QA_TEST_OUTPUT_1.5.3.txt; năm file QA_GUI_*_1.5.3.txt; QA_MIGRATION_1.5.3.json; QA_ENVIRONMENT_1.5.3.txt. QA_PACKAGED_TEST_OUTPUT_1.5.3.txt, QA_PACKAGED_GUI_*_1.5.3.txt và QA_PACKAGE_VERIFICATION_1.5.3.json ghi lượt kiểm tra từ gói bàn giao.
