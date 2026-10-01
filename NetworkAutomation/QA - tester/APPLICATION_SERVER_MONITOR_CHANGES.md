# Application / Server Monitor

## Da tich hop
- Them menu `GIAM SAT -> Application / Server`.
- Quan ly target theo Name, Host/IP, Application, Port, Protocol va Windows Service tuy chon.
- Kiem tra agentless TCP/HTTP/HTTPS tu may NOC.
- Preset/phan loai phu hop SQL Server, IIS/HTTP, HTTPS, MySQL, PostgreSQL, DNS, DHCP, Apache/Nginx.
- Neu target la chinh may Windows dang chay ung dung: doc them CPU, RAM, Disk va Windows Service bang PowerShell/CIM.
- Luu lich su ket qua vao SQLite (`server_monitor_targets`, `server_monitor_results`).
- DOWN/WARN duoc dua vao Notification Center, co cooldown chong gui trung.
- Khong restart service, khong thay doi server.

## Gioi han ban dau
- CPU/RAM/Disk/Windows Service chi doc chi tiet tren local Windows host. Remote host hien kiem tra agentless theo TCP/HTTP(S).
- De doc tai nguyen Windows Server tu xa, nen bo sung WinRM/PowerShell Remoting o ban tiep theo va quan ly credential bang Credential Manager hien co.
- DNS/DHCP ban dau la availability/port check, chua thuc hien protocol transaction day du.

## Kiem thu
- Python compile: PASS
- Regression test: PASS
- Server Monitor self-test: PASS
