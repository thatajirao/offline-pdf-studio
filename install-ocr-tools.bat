@echo off
title Offline PDF Studio - OCR tools setup
echo This helper installs Tesseract and uv using Windows Package Manager.
echo Ghostscript must be downloaded and installed separately.
echo.
where winget >nul 2>nul
if errorlevel 1 (
  echo winget was not found. Install App Installer from Microsoft Store or follow README.md manually.
  pause
  exit /b 1
)
winget install -e --id tesseract-ocr.tesseract
winget install -e --id astral-sh.uv
echo.
echo Next:
echo 1. Install 64-bit Ghostscript from https://ghostscript.com/releases/
echo 2. Close this window and open a NEW PowerShell window.
echo 3. Run: uv tool install ocrmypdf
echo 4. Check: tesseract --version
echo 5. Check: ocrmypdf --version
echo.
echo See README.md for language pack and troubleshooting details.
pause
