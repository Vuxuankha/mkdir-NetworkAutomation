# UI/UX Dashboard Fix 1

Đã sửa 2 vấn đề từ ảnh kiểm tra thực tế:

1. **Quick Actions bị trống ở 3 ô đầu**
   - Nguyên nhân: dùng `tk.Button` làm container cho nhiều widget con; cách này không ổn định trên Tk/Windows.
   - Sửa: chuyển tile sang `tk.Frame`, bind click/hover/keyboard cho toàn bộ card.
   - Kết quả: icon, tiêu đề và mô tả hiển thị ổn định trên tất cả 4 tile.

2. **Network Health gây hiểu nhầm giữa Online/Offline và heartbeat**
   - Online/Offline lấy từ trạng thái thiết bị đã lưu trong CSDL.
   - Heartbeat chỉ phản ánh agent/service giám sát nền có đang sống hay không.
   - Sửa thông điệp heartbeat để phân biệt rõ: chưa khởi động, mất heartbeat, heartbeat lỗi, hoặc đang chạy.
   - Dashboard bổ sung dòng giải thích nguồn trạng thái để không hiểu rằng 85 Online đồng nghĩa service đang có heartbeat.

## Kiểm tra

- `python -m unittest tests.test_stability111 -v`: 5/5 đạt.
- `xvfb-run -a python tests/ui_dashboard_smoke.py`: đạt.
- `py_compile`: đạt cho `dark_dashboard.py` và `agent_runtime.py`.
