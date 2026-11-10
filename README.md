# Offline PDF Studio

A local-first PDF utility web app for Windows. Convert and organize documents without sending files to a cloud service.

## Features
- Word (DOC/DOCX), ODT and RTF to PDF (LibreOffice required)
- PDF to editable DOCX
- Merge multiple PDFs
- Extract selected pages (example: 1-3,5,8-9)
- Compress PDF content streams
- Rotate PDF pages
- Convert multiple images into a single PDF

## Tech stack
Python, Flask, pypdf, pdf2docx, Pillow, HTML, CSS and JavaScript.

## Requirements
- Windows 10/11
- Python 3.10 or newer
- LibreOffice for Word-to-PDF conversion

## Run locally
1. Clone or download this repository.
2. Install Python 3.10+ and LibreOffice.
3. Run `install.bat`.
4. Run `run.bat`.
5. Open http://127.0.0.1:5055.

The Flask server binds to 127.0.0.1, so it is intended for use on the same computer.

## Privacy and offline use
Documents are processed by the local application and are not uploaded to a hosted service. Package installation requires internet access initially; once installed, the app can be used offline. The UI uses system fallback fonts and does not require remote font downloads.

Temporary files are stored in the local `work/` directory. Close the app and clear that folder to remove temporary working files.

## Limitations
- PDF-to-DOCX conversion may not preserve complex layouts, tables, columns, or scanned pages perfectly.
- OCR for scanned PDFs is not included in this version.
- PDF content-stream compression may not significantly reduce scanned/image-heavy PDFs.
- Password-protected PDF handling is not implemented.

## License
No license has been specified yet. Add a license file before redistributing this project.
