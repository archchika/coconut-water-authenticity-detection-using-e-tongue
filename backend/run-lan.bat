@echo off
REM Django for ESP32 WiFi — listens on all interfaces (phone hotspot / LAN).
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Create venv first: py -m venv .venv  then  .venv\Scripts\pip install -r requirements.txt
  exit /b 1
)
set ALLOWED_HOSTS=localhost,127.0.0.1,10.216.217.31,10.234.124.31,192.168.137.1
echo Laptop Mobile Hotspot IP: 192.168.137.1
echo ESP32 POST URL: http://192.168.137.1:8000/api/esp32-reading/
echo.
echo Sketch WiFi: coconut / 12345678  (or your hotspot SSID)
echo Backend must be: runserver 0.0.0.0:8000  (not plain runserver)
echo.
.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
