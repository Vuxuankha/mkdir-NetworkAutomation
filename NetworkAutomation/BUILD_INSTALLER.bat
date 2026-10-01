@echo off
setlocal
cd /d "%~dp0"
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
  echo Khong tim thay Inno Setup 6.
  echo Cai Inno Setup 6 truoc, sau do chay lai.
  pause
  exit /b 1
)
if not exist "dist\NetworkAutomation\NetworkAutomation.exe" (
  echo Chua co EXE. Hay chay BUILD_WINDOWS.bat truoc.
  pause
  exit /b 1
)
"%ISCC%" "installer\NetworkAutomation.iss"
pause
