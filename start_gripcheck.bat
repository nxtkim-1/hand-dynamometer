@echo off
REM GripCheck with the real dynamometer. Double-click this file.
REM Before: upload firmware/grip_firmware_tillaart, plug the Nano in by USB, close the Arduino Serial Monitor.
cd /d "%~dp0"
call tools\setup_python.bat || goto end
echo.
echo Starting GripCheck with the device. A browser tab opens at http://localhost:8000
echo The USB port is found automatically. Keep this window open; close it to stop GripCheck.
echo.
".venv\Scripts\python.exe" webapp.py --device
:end
pause
