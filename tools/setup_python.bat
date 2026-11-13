@echo off
REM Shared by start_gripcheck.bat and check_device.bat: makes sure Python and the packages are ready.
REM First run creates .venv in the repo folder and installs requirements.txt (a few minutes). Later runs skip it.
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if defined PY %PY% --version >nul 2>nul || set "PY="
if not defined PY (
  echo Python is not installed.
  echo Install Python 3.12 from https://www.python.org/downloads/ and tick "Add python.exe to PATH",
  echo then double-click this file again.
  exit /b 1
)
if exist ".venv\Scripts\python.exe" exit /b 0
echo First run: installing the Python packages. This takes a few minutes...
%PY% -m venv .venv || exit /b 1
".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
".venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt || exit /b 1
echo Packages installed.
exit /b 0
