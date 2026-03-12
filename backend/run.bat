@echo off
REM Run Django dev server using venv Python (no PowerShell activation needed).
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Create venv first: py -m venv .venv  then  .venv\Scripts\pip install -r requirements.txt
  exit /b 1
)
.venv\Scripts\python.exe manage.py runserver
pause
