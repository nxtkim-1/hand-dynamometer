@echo off
REM One-minute check of the dynamometer: hands off, squeeze, let go. Double-click this file.
REM Close the Arduino Serial Monitor first.
cd /d "%~dp0"
call tools\setup_python.bat || goto end
echo.
".venv\Scripts\python.exe" software\check_device.py %*
:end
pause
