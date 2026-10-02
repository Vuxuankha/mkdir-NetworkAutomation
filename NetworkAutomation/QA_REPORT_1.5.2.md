# Kiểm tra lại lần hai — NetworkAutomation 1.5.2

Ngày: 02/10/2026. Đầu vào là chính ZIP 1.5.1 đã bàn giao, tải lại và xác minh đầy đủ trước khi sửa. SHA-256 đầu vào: `f79f767b11ac449efefa527bee56f740ae73d2c8afeb80a51a5b27b05405fe0d`. ZIP có 15.923 entry, không lỗi CRC. Đây là bản cập nhật từ 1.5.1; không phải bản 2.0.0 trước đây.

## Kết quả kiểm chứng

| Kiểm tra | Kết quả |
|---|---|
| Bộ test 1.5.1 trước sửa | 121/121 unit test và 11/11 regression đạt |
| 14 tình huống bổ sung ban đầu | 2 đạt, 8 thất bại, 4 lỗi; chưa tính là test đạt |
| Tạo snapshot đồng thời trước sửa | Tái hiện 6 snapshot cho cùng một bản phát hành thay vì 1 |
| Sau sửa 1.5.2 | **141/141 unit test + 11/11 regression đạt** |
| Phạm vi test mới | 20 test mới; giữ toàn bộ 121 test đang dùng của 1.5.1 |
| Đồng thời nhiều tiến trình | 6 tiến trình dùng cùng một khóa hoàn chỉnh; snapshot nâng cấp chỉ tạo 1 lần; khóa tác vụ chặn tiến trình khác và nhả khi kết thúc |
| Migration bản sao dữ liệu gốc | Giữ nguyên 93 thiết bị, 3 tài khoản, 0 credential SSH và 1 config backup; SQLite quick_check = ok |
| Mã hóa dữ liệu gốc | Giải mã được 2 giá trị mã hóa hiện có; khóa cũ giữ nguyên; snapshot 1.5.2 chứa đúng khóa đó |
| Dependency | Import dependency bắt buộc đạt; pip check không phát hiện dependency hỏng |
| GUI và Windows EXE/Setup/Service | Chưa nghiệm thu: môi trường Linux không có display/Windows |
| Thiết bị mạng thật | Chưa kiểm chứng; các test SSH/monitor dùng mô phỏng, không kết nối thiết bị vận hành |

## Lỗi đã xử lý

1. **Mất khóa vẫn tự sinh khóa mới.** Dữ liệu cũ không thể giải mã bằng khóa mới nhưng chương trình vẫn tiếp tục. Bản sửa kiểm tra các cột `_enc` trong mọi bảng và các giá trị mã hóa trong settings; từ chối sinh khóa nếu vẫn còn ciphertext. Luồng giải mã không sinh khóa thay thế. Khóa sai định dạng không bị ghi đè.
2. **Tạo khóa lần đầu không có khóa đồng bộ.** Kiểm tra/tạo file rời nhau có nguy cơ hai tiến trình ghi khóa khác nhau. Nay dùng file lock, tạo file tạm có quyền riêng trên Linux, flush/fsync rồi thay file nguyên tử. Bài test nhiều tiến trình kiểm tra tất cả token bằng cùng khóa cuối cùng. Không tuyên bố đã tái hiện ổn định race này ở bản cũ.
3. **Lịch sao lưu chạy chồng.** Tác vụ SSH chưa xong nhưng next_run còn quá hạn, nên bấm hoặc tick tiếp theo có thể mở thêm worker. Đã tái hiện 3 lần gọi cho cùng một tác vụ. Nay khóa từng job được giữ đến khi ghi xong kết quả, dùng chung giữa trang và tiến trình; lượt chạy theo lịch kiểm tra lại enabled/next_run bên trong khóa.
4. **Worker sao lưu gọi Tk/activity callback trực tiếp.** Nay worker chỉ đưa thông báo vào queue, main thread cập nhật giao diện. Rời trang dừng lịch mới và bỏ kết quả giao diện đến muộn. Ứng dụng theo dõi worker sao lưu và đợi trước khi hủy root.
5. **Lỗi DB có thể làm lịch ngừng vĩnh viễn.** Tick luôn lập lịch lượt kế tiếp khi trang còn hoạt động. Khóa job được nhả kể cả khi SSH hoặc ghi DB thất bại, cho phép thử lại.
6. **HTTP trả lỗi bị ghi DOWN thay vì WARN.** HTTPError được xử lý thành WARN với mã HTTP và đóng response. Lỗi kết nối vẫn là DOWN. CPU/RAM/disk cao hoặc service stopped không làm mất mức DOWN của lỗi kết nối.
7. **Dữ liệu monitor lỗi có thể dừng cả lượt kiểm tra.** Kiểm tra port/protocol/host nằm trong khối xử lý lỗi của từng target. Giá trị tài nguyên không phải số, NaN hoặc ngoài 0–100 được bỏ qua. Host kèm port bị từ chối; IPv6 có ngoặc được chuẩn hóa.
8. **Snapshot nâng cấp chỉ khóa trong một tiến trình.** GUI/service hoặc nhiều phiên khởi động đồng thời có thể tạo trùng và tranh ghi marker. Đã tái hiện 6 snapshot và gặp lỗi trong bài test khởi động đồng thời. Nay file lock bảo vệ toàn bộ kiểm tra marker, backup và ghi marker giữa các tiến trình; lock tự nhả khi tiến trình kết thúc.

## Phạm vi và giới hạn

Không thay dữ liệu vận hành trong ZIP bằng database test. Các file ngoài danh sách sửa được giữ nguyên nội dung. Nhật ký QA 1.5.1 được giữ để tra cứu. EXE/Setup có sẵn là build cũ, **phải build lại từ code 1.5.2** để nhận bản sửa.

Các hạng mục chưa giải quyết trong bản kiểm tra này vẫn được ghi ở QA_REPORT_1.5.1.md: một số luồng SSH dùng AutoAddPolicy, đăng nhập chưa giới hạn thử sai/timeout phiên, quyền ở nhiều trang cũ chưa được kiểm tra lại trên toàn bộ thao tác, restore cấu hình còn cần xác nhận kết quả trên từng thiết bị, và các worker GUI khác chưa được rà/sửa toàn bộ. Không dùng số test đạt để kết luận ứng dụng đã nghiệm thu production hoặc có giá trị thương mại 100 triệu đồng.

## Chạy lại trên Windows

Đóng ứng dụng và dừng service trước khi cập nhật code; giữ dữ liệu và khóa của chính cài đặt đang dùng. Không chép database từ ZIP lên dữ liệu vận hành.

```bat
py -3 -m pip install -r requirements.txt
py -3 tools/run_release_checks.py
py -3 tests/ui_accounts_smoke.py
py -3 tests/ui_all_pages_smoke.py
```

Runner unit/regression dùng dữ liệu tạm. Hai UI smoke cần desktop/Tk; chưa chạy tại đây. Sau đó chạy BUILD_WINDOWS.bat/BUILD_INSTALLER.bat để build mới, kiểm thử cài đặt/service và thử nghiệm thiết bị thật trước nghiệm thu.

Nhật ký: QA_BASELINE_1.5.1_RECHECK.txt, QA_NEW_CASES_BEFORE_1.5.2.txt, QA_UPGRADE_RACE_BEFORE_1.5.2.txt, QA_TEST_OUTPUT_1.5.2.txt, QA_ENVIRONMENT_1.5.2.txt, QA_MIGRATION_1.5.2.json. QA_PACKAGED_TEST_OUTPUT_1.5.2.txt ghi lượt kiểm tra từ ZIP đóng gói. QA_PACKAGE_VERIFICATION_1.5.2.json ghi kết quả kiểm tra nội dung archive.
