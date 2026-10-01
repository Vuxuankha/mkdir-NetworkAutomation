# NetworkAutomation 1.5.0 — Avatar và quản lý tài khoản

## Giao diện
- Góc phải Header có Avatar với hai ký tự đầu của tên tài khoản, tên đăng nhập, vai trò và menu thả xuống.
- Menu: **Hồ sơ cá nhân**, **Đổi mật khẩu**, **Nhật ký hoạt động**, **Đăng xuất**. Bấm Avatar hoặc tên tài khoản để mở. Khi cửa sổ nhỏ, tên được thu gọn nhưng menu vẫn hiện.
- Sidebar → **QUẢN TRỊ → Quản lý tài khoản** dành cho Admin. Màn hình có tìm kiếm, thêm, sửa tên đăng nhập/vai trò/trạng thái, đặt lại mật khẩu, xóa có xác nhận và làm mới.
- Biểu mẫu tài khoản có cuộn; hàng nút Lưu/Hủy nằm ngoài vùng cuộn. Ctrl+Enter để lưu, Esc để đóng. Lỗi nhập dữ liệu giữ biểu mẫu mở để sửa.

## Tài khoản và phân quyền
- **Admin:** quản lý tài khoản; xem nhật ký hoạt động của tất cả tài khoản.
- **Operator:** vai trò dành cho kỹ thuật viên vận hành/giám sát theo các menu hiện có.
- **Viewer:** xem các màn hình giám sát theo các menu hiện có.
- Operator và Viewer dùng menu cá nhân để xem hồ sơ, đổi mật khẩu và xem nhật ký của chính tài khoản; các thao tác quản lý tài khoản luôn kiểm tra lại vai trò/trạng thái trong database.
- Đổi mật khẩu cá nhân cần mật khẩu hiện tại và xác nhận mật khẩu mới. Admin có thể đặt lại mật khẩu của tài khoản khác. Mật khẩu mới có 8–256 ký tự, được băm PBKDF2 và không được ghi vào nhật ký.
- Không thể xóa, khóa hoặc hạ quyền tài khoản đang đăng nhập; các thay đổi luôn giữ ít nhất một Admin hoạt động. Xóa/khóa/hạ quyền Admin kiểm tra trong cùng transaction với thao tác ghi.
- Nếu database chưa có tài khoản, phiên thiết lập local-admin chỉ tạo tài khoản đầu tiên là Admin đang hoạt động. Sau khi tạo, giao diện chuyển ngay sang tài khoản Admin mới. Những lần mở sau phải đăng nhập.
- Database có tài khoản nhưng tất cả bị khóa sẽ không tự mở lại quyền local-admin. Mục Đăng xuất quay về màn hình đăng nhập; phiên thiết lập không tự mở lại khi đăng xuất.

## Đăng xuất và tác vụ nền
Đăng xuất dừng lịch và yêu cầu các engine nền của ứng dụng dừng, chờ các worker được theo dõi hoàn tất, ghi sự kiện Đăng xuất rồi hủy cửa sổ phiên cũ. Màn hình đăng nhập tiếp theo dùng cây giao diện và timer mới. Khi còn tác vụ đang chạy, giao diện hiển thị “Đang kết thúc phiên”. Dịch vụ Windows được cài riêng có vòng đời độc lập.

## Cập nhật trên Windows 11
1. Đóng ứng dụng, sao lưu thư mục chương trình và dữ liệu hiện tại.
2. Giải nén ZIP vào thư mục riêng. Chép mã nguồn và metadata build mới vào thư mục chương trình đang dùng.
3. Giữ nguyên database, `.credential.key`, `data_location.json`, cấu hình, bản sao lưu và báo cáo hiện tại. **Không chép đè thư mục database từ ZIP lên dữ liệu hiện tại.**
4. Chạy `START_WINDOWS.bat`. Nếu chưa có tài khoản, mở QUẢN TRỊ → Quản lý tài khoản → Thêm tài khoản để tạo Admin đầu tiên.
5. Muốn chạy EXE mới: dựng lại bằng `BUILD_WINDOWS.bat` trên Windows. ZIP này chứa mã nguồn, không phải EXE đã biên dịch.

Các file chương trình thay đổi: `main.py`, `modules/accounts.py` (mới), `modules/account_ui.py` (mới), `modules/nms_v5.py`, `modules/nms_v6.py`, `modules/nms_v4.py`, `modules/auto_audit_scheduler.py`; VERSION, thông tin phiên bản và cấu hình bộ cài cũng được nâng lên 1.5.0.

## Kiểm tra
111 unittest và 11 nhóm regression đạt trên Linux. 17 kiểm thử mới bao gồm CRUD với SQLite tạm, phân quyền Operator/Viewer, tài khoản bị khóa, phiên thiết lập hết hiệu lực, bảo vệ tài khoản đang đăng nhập, hai Admin cùng xóa tài khoản, đổi/đặt lại mật khẩu, phạm vi nhật ký, lỗi lưu giữ biểu mẫu mở, dừng worker và quay về đăng nhập với phiên mới.

Chưa chạy giao diện thật trên Windows hoặc kiểm tra DPI Windows thực vì môi trường hiện tại không có display. Chạy `py -3 tests/ui_accounts_smoke.py` trên Windows để kiểm tra menu, biểu mẫu ở 500×530/360×300 với các mức Tk scaling, thêm/sửa/xóa vào database tạm, mật khẩu, vai trò Viewer và đăng xuất. Script dùng dữ liệu tạm và tắt các engine mạng; Tk scaling không thay thế hoàn toàn kiểm tra DPI Windows thực.

Chức năng sửa Thêm/Sửa thiết bị ở bản 1.4.1 được giữ trong bản này. Không thêm lại AI.
