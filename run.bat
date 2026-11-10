@echo off
title Offline PDF Studio
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run install.bat first.
  pause
  exit /b 1
)
call .venv\Scripts\activate
start "" http://127.0.0.1:5055
python app.py
pause
