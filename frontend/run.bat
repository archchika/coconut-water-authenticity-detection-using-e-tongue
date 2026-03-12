@echo off
set "NODE_DIR=C:\Program Files\nodejs"
set "NPM=%NODE_DIR%\npm.cmd"
if not exist "%NPM%" (
  echo Node.js not found at %NODE_DIR%. Install from https://nodejs.org
  exit /b 1
)
cd /d "%~dp0"
if not exist "node_modules" (
  echo Installing dependencies...
  call "%NPM%" install
)
call "%NPM%" run dev
pause
