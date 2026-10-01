# Notification Center
- Telegram Bot Token và SMTP Password được mã hóa bằng khóa credential cục bộ.
- Bật/tắt riêng Telegram và Email SMTP.
- Lọc sự kiện: Device Offline, Configuration Drift, Security HIGH, Daily Audit WARN/HIGH.
- Cooldown chống gửi trùng, mặc định 60 phút.
- Auto SSH Audit chỉ gửi khi tạo alert Drift/Security mới.
- Daily Audit gửi khi WARN/HIGH hoặc audit thất bại.
- Có Test Telegram/Test Email và bảng notification_log trong database.
