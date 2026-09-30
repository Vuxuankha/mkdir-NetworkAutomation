@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    py -3 main.py
    goto finished
)
where python >nul 2>nul
if not errorlevel 1 (
    python main.py
    goto finished
)
echo Khong tim thay Python. Hay cai Python co Tkinter truoc.
:finished
if errorlevel 1 (
    echo.
    echo Neu thieu thu vien, chay: py -3 -m pip install -r requirements.txt
    echo Xem HUONG_DAN_AUTO_IP_EXCEL.md
    pause
)
endlocal
