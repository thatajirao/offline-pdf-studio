@echo off
title Offline PDF Studio - Setup
cd /d "%~dp0"
echo =====================================
echo       OFFLINE PDF STUDIO SETUP
echo =====================================
where py >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.10 or newer from python.org.
  pause
  exit /b 1
)
py -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
echo Setup finished.
echo IMPORTANT: Install LibreOffice for Word-to-PDF conversion.
pause
