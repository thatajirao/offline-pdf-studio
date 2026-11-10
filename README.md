# Offline PDF Studio

A local-first PDF utility for Windows. It converts and organizes documents without uploading files to a cloud service.

## Features

- Word (DOC/DOCX), ODT and RTF to PDF (LibreOffice required)
- PDF to editable DOCX (best effort) or image-based DOCX (preserves appearance, not editable text)
- OCR for scanned PDFs and searchable PDF output (OCRmyPDF + Tesseract required)
- OCR preprocessing controls: orientation correction, deskew, selectable oversampling DPI, optional cleaning
- Merge multiple PDFs
- Extract selected pages
- Ghostscript PDF compression with Smallest, Balanced and Print presets
- Do not enlarge files: if Ghostscript output is not smaller, the original file is returned instead
- Rotate PDF pages
- Protect PDFs with AES-256 password encryption
- Unlock PDFs when you know the password
- Convert multiple images into one PDF

## Tech stack

Python, Flask, pypdf[crypto], pdf2docx, PyMuPDF, python-docx, Pillow, HTML, CSS and JavaScript.

## Requirements

- Windows 10/11, 64-bit recommended
- Python 3.10 or newer
- LibreOffice for Word-to-PDF
- Ghostscript 64-bit for PDF compression
- Tesseract 64-bit and OCRmyPDF for OCR
- Optional unpaper program if you enable the scan-cleaning option

## Install the main application

1. Install Python 3.10+ and LibreOffice.
2. Clone or download this repository.
3. Run `install.bat`.
4. Run `run.bat`.
5. Open http://127.0.0.1:5055.

## Enable OCR and stronger compression on Windows

OCRmyPDF's native Windows guide requires 64-bit Tesseract and uv, and recommends 64-bit Ghostscript. Use the [official OCRmyPDF Windows installation guide](https://ocrmypdf.readthedocs.io/en/latest/installation.html).

1. Run `install-ocr-tools.bat` to install Tesseract and uv with winget.
2. Install 64-bit Ghostscript using the [official Ghostscript releases](https://ghostscript.com/releases/).
3. Open a NEW PowerShell window and run:
   ```powershell
   uv tool install ocrmypdf
   ```
4. Verify:
   ```powershell
   tesseract --version
   tesseract --list-langs
   ocrmypdf --version
   gswin64c.exe -version
   ```
5. Restart Offline PDF Studio.

Install the Tesseract trained-data files for every language you select in the app. The options shown are English (`eng`), Telugu (`tel`), Hindi (`hin`), and combinations. A language option works only when its Tesseract language data is installed.

The optional `--clean` OCR preprocessing switch needs the `unpaper` program. If OCR reports that unpaper is missing, uncheck **Clean scan before OCR** and run OCR again. Orientation correction, deskewing and oversampling work without this optional cleaning switch.

## How to improve OCR results

- Start with a clean scan. A sharp 300 DPI scan is a good baseline for ordinary text; 400 DPI can help small print when the original contains enough detail.
- Use the correct Tesseract language or language combination.
- The app enables automatic page-rotation detection and deskewing.
- Try optional scan cleaning only for noisy backgrounds; inspect the output because cleaning can remove faint marks or content.
- Higher DPI increases processing time and memory use. Upsampling cannot recover detail missing from a blurry or low-resolution original.
- Tesseract-based OCR is not reliable for handwriting. For handwriting, evaluate a handwriting-specific recognition system.

OCRmyPDF adds a searchable text layer; it does not recreate the original Word formatting. See the [OCRmyPDF documentation on limitations and preprocessing](https://ocrmypdf.readthedocs.io/en/latest/introduction.html) and its [image-processing cookbook](https://ocrmypdf.readthedocs.io/en/latest/cookbook.html).

## PDF-to-DOCX: two different goals

### Editable DOCX

Uses pdf2docx to reconstruct text and layout. It can preserve common paragraphs and some tables, but complex columns, nested tables, unusual fonts, page decorations, and reading order may need manual correction. When a PDF is scanned, run OCR first to create a text layer.

Important maintenance note: the upstream pdf2docx project announced that Artifex no longer actively maintains it. Treat this converter as a best-effort component, keep it updated only after testing, and consider a separately tested layout-analysis engine for a future advanced conversion mode. [Upstream project status](https://github.com/ArtifexSoftware/pdf2docx).

A possible future engine is [PaddleOCR PP-StructureV3](https://www.paddleocr.ai/main/en/version3.x/pipeline_usage/PP-StructureV3.html), which offers document layout analysis, table recognition, and reading-order recovery. It has a substantially heavier model/runtime footprint and would need its own benchmark and offline packaging work; it is not included in the current app.

### Layout-faithful DOCX

Embeds each rendered PDF page as a full-page image in a Word document. This is useful when visual appearance is the priority. The text inside each page image cannot be edited as normal Word text or searched like native text.

## Compression behavior

Ghostscript's presets trade file size against visual quality:

- **Smallest file**: stronger downsampling and lower image quality.
- **Balanced**: a compromise for typical sharing.
- **Print quality**: preserves more image detail.

The app compares the output size with the input. If the recompressed file is not smaller, it returns the original PDF instead and tells you that no reduction was achieved. Always inspect image quality before replacing your source file.

## Password protection

- Enter the existing password to convert, merge, split, rotate, compress, or OCR a protected PDF.
- Use **Protect PDF** to encrypt a PDF using AES-256.
- Use **Unlock PDF** to remove encryption when you know a valid password.
- Passwords are not stored by this application.
- This software does not crack, bypass, or recover unknown passwords. Keep passwords in a password manager and maintain an authorized backup.

See [pypdf encryption and decryption documentation](https://pypdf.readthedocs.io/en/latest/user/encryption-decryption.html).

## Local processing and privacy

- Flask binds only to `127.0.0.1`, for use on the same computer.
- Documents are processed locally. There is no cloud upload or user account.
- Temporary files are stored in `work/`. Close the app and clear that folder to remove temporary files.
- Initial software/model downloads require internet access. After dependencies, language data and OCR models are installed, the app can be used offline.

## Licensing

This project does not bundle LibreOffice, Ghostscript, OCRmyPDF, Tesseract, unpaper, or model files. Before distributing an installer that includes third-party binaries, review each component's license. Ghostscript licensing in particular needs careful review if you redistribute it; see the [Ghostscript FAQ](https://ghostscript.com/faq/).

## License

No project license has been specified. Add a license file before redistributing this project.
