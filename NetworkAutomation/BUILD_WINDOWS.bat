@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo  Network Automation v1.0 - Windows Build
echo ============================================================

where py >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Khong tim thay Python Launcher ^(py.exe^).
  echo Cai Python 3.11/3.12/3.13 64-bit, sau do chay lai file nay.
  pause
  exit /b 1
)

if not exist ".venv-build\Scripts\python.exe" (
  echo [1/6] Tao moi truong build...
  py -3 -m venv .venv-build || goto :fail
)

call ".venv-build\Scripts\activate.bat" || goto :fail

echo [2/6] Cai/cap nhat thu vien...
python -m pip install --upgrade pip || goto :fail
python -m pip install -r requirements.txt -r requirements-build.txt || goto :fail

echo [3/6] Compile + regression test...
python -m compileall -q . || goto :fail
python regression_test.py || goto :fail

echo [4/6] Don thu muc build cu...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [5/6] Tao NetworkAutomation.exe ^(GUI, khong console^)...
pyinstaller --clean --noconfirm NetworkAutomation.spec || goto :fail

if not exist "dist\NetworkAutomation\NetworkAutomation.exe" goto :fail

echo [6/6] EXE da tao thanh cong.
echo     dist\NetworkAutomation\NetworkAutomation.exe

echo.
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%ISCC%" (
  echo Phat hien Inno Setup. Dang tao Setup.exe...
  "%ISCC%" "installer\NetworkAutomation.iss" || goto :fail
  echo.
  echo Setup: release\NetworkAutomation_Setup_v1.5.0.exe
) else (
  echo Inno Setup 6 chua duoc cai. EXE van da build thanh cong.
  echo Cai Inno Setup 6 va chay BUILD_INSTALLER.bat de tao Setup.exe.
)

echo.
echo BUILD HOAN TAT.
pause
exit /b 0

:fail
echo.
echo [ERROR] Build that bai. Xem thong bao phia tren.
pause
exit /b 1
