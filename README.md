# Offline PDF Studio

A local-first PDF utility web app for Windows. Convert and organize documents without uploading files to a cloud service.

## Features

- Word (DOC/DOCX), ODT and RTF to PDF (LibreOffice required)
- PDF to editable DOCX (best effort) or layout-faithful image-based DOCX
- OCR for scanned PDFs and searchable PDF output (OCRmyPDF + Tesseract required)
- Merge multiple PDFs
- Extract selected pages (example: `1-3,5,8-9`)
- Compress image-heavy PDFs with Ghostscript quality presets
- Rotate PDF pages
- Protect PDFs with AES-256 password encryption
- Unlock PDFs when you know the password
- Convert multiple images into one PDF

## Tech stack

Python, Flask, pypdf, pdf2docx, PyMuPDF, python-docx, Pillow, HTML, CSS and JavaScript.

## Requirements

- Windows 10/11, 64-bit recommended
- Python 3.10 or newer for the main application
- LibreOffice for Word-to-PDF conversion
- Ghostscript 64-bit for PDF compression and as an OCRmyPDF dependency/recommended helper
- Tesseract OCR and OCRmyPDF for scanned-PDF OCR

The app itself runs locally at `127.0.0.1`. No PDF is uploaded to a hosted server.

## Install the main application

1. Install Python 3.10+ and LibreOffice.
2. Download or clone this repository.
3. Run `install.bat`.
4. Run `run.bat`.
5. Open [http://127.0.0.1:5055](http://127.0.0.1:5055).

## Enable OCR and stronger compression on Windows

OCRmyPDF's current Windows installation guide requires 64-bit Tesseract, uv, and Ghostscript (Ghostscript is recommended and is used by this project's compression feature). Follow the official [OCRmyPDF Windows installation instructions](https://ocrmypdf.readthedocs.io/en/latest/installation.html).

Typical setup:

1. Install Tesseract and uv from an Administrator or normal PowerShell window with:
   ```powershell
   winget install -e --id tesseract-ocr.tesseract
   winget install -e --id astral-sh.uv
   ```
2. Install 64-bit Ghostscript from the [official Ghostscript releases page](https://ghostscript.com/releases/).
3. Close and reopen PowerShell so updated PATH entries are available.
4. Install OCRmyPDF:
   ```powershell
   uv tool install ocrmypdf
   ```
5. Confirm the tools are available:
   ```powershell
   tesseract --version
   tesseract --list-langs
   ocrmypdf --version
   ```
6. Restart Offline PDF Studio.

Tesseract's standard Windows installer instructions are linked from the [Tesseract documentation](https://tesseract-ocr.github.io/tessdoc/Installation.html). Install the language data you need. The app offers English (`eng`), Telugu (`tel`), Hindi (`hin`) and combinations, but a language works only when its Tesseract trained-data file is installed.

## How the conversion modes work

### Editable DOCX

Uses pdf2docx to reconstruct paragraphs and layout from the PDF's text and positioning. For scanned PDFs, enable **Run OCR first**. OCR helps recover text, but exact fonts, columns, tables, and complex layouts may still need manual correction. PDF-to-Word is a reconstruction process, not a perfect reversal of the original Word file.

### Layout-faithful DOCX

Embeds each rendered PDF page as an image in a Word document. It is intended to preserve the page's visual appearance, but the page text is not directly editable as Word text. Use this mode when appearance matters more than editing individual words.

## Compression quality

Ghostscript's presets trade image quality for file size:

- **Smallest file**: more aggressive downsampling; inspect images and small text carefully.
- **Balanced**: a compromise for typical sharing.
- **Print quality**: larger output with more image detail.

Compression is not guaranteed to make every PDF smaller. Some PDFs may already be optimized, and some files may become larger after rewriting. Keep the original and compare both file size and visual quality before deleting it.

## Password-protected PDFs

- Enter the existing password to convert, merge, split, rotate, compress or OCR a protected PDF.
- Use **Protect PDF** to encrypt a PDF with a new AES-256 password.
- Use **Unlock PDF** to remove encryption when you know a valid password.
- This application does not recover, crack or bypass unknown passwords. It cannot decrypt a file without the required password.

## Privacy and temporary files

- Flask binds only to `127.0.0.1`, so the app is intended for use on the same computer.
- Documents are processed locally; there is no cloud upload or user account.
- Temporary documents are stored in `work/`. Close the app and clear that folder to remove temporary files.
- Do not use this tool as a substitute for secure document handling on shared or compromised computers.

## Limitations

- OCR quality depends on scan resolution, skew, language data, handwriting, and document condition.
- OCR does not restore the original document's exact formatting.
- Image-based DOCX preserves appearance but is not text-editable.
- Ghostscript compression may reduce quality and may not make every file smaller.
- Password protection requires the correct existing password; there is no password recovery feature.

## Licensing note

Before distributing an installer that bundles Ghostscript, review the [Ghostscript licensing FAQ](https://ghostscript.com/faq/) and choose an appropriate license. This repository does not bundle Ghostscript, Tesseract, OCRmyPDF or LibreOffice.

## License

No project license has been specified. Add a license file before redistributing this project.
