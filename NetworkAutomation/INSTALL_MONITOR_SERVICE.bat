@echo off
setlocal
cd /d "%~dp0"
net session >nul 2>&1
if errorlevel 1 (
  echo Hay chay file nay bang Run as administrator.
  pause
  exit /b 1
)
where py >nul 2>&1
if errorlevel 1 goto fail
py -3 -m pip install -r requirements.txt -r requirements-service.txt || goto fail
py -3 windows_service.py --startup auto install || goto fail
sc failure NetworkAutomationMonitor reset= 86400 actions= restart/60000/restart/60000/restart/60000
py -3 windows_service.py start || goto fail
echo Da cai dich vu. Xem UPDATE_1.1.0.md de kiem tra du lieu va quyen truy cap.
pause
exit /b 0
:fail
echo Cai dich vu that bai. Xem loi phia tren va UPDATE_1.1.0.md.
pause
exit /b 1
