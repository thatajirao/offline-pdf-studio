from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from pdf2docx import Converter
from PIL import Image
from docx import Document
from docx.shared import Inches
from docx.enum.section import WD_SECTION
import fitz
import shutil
import subprocess
import os
import uuid
import re

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024
ROOT = Path(__file__).parent
WORK = ROOT / "work"
WORK.mkdir(exist_ok=True)


def clean_work():
    for path in WORK.iterdir():
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        except Exception:
            pass


def save_file_storage(file_storage):
    if not file_storage or not file_storage.filename:
        raise ValueError("Please choose a file.")
    original_name = secure_filename(file_storage.filename) or "document"
    target = WORK / f"{uuid.uuid4().hex}_{original_name}"
    file_storage.save(target)
    return target


def save_upload(field="file"):
    return save_file_storage(request.files.get(field))


def get_pdf_reader(path, password=""):
    reader = PdfReader(str(path), strict=False)
    was_encrypted = reader.is_encrypted

    if was_encrypted:
        if not password:
            raise ValueError("This PDF is password-protected. Enter its password and try again.")
        try:
            result = reader.decrypt(password)
        except Exception:
            result = 0
        if not result:
            raise ValueError("The PDF password is incorrect.")

    return reader, was_encrypted


def prepare_pdf(path, password=""):
    reader, was_encrypted = get_pdf_reader(path, password)
    if not was_encrypted:
        return path

    unlocked_path = WORK / f"{path.stem}_unlocked.pdf"
    writer = PdfWriter(clone_from=reader)
    with unlocked_path.open("wb") as output_file:
        writer.write(output_file)
    return unlocked_path


def libreoffice_path():
    candidates = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return shutil.which("soffice")


def find_ocrmypdf():
    found = shutil.which("ocrmypdf")
    if found:
        return found
    candidates = [
        Path.home() / ".local" / "bin" / "ocrmypdf.exe",
        Path.home() / ".local" / "bin" / "ocrmypdf",
    ]
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.append(Path(appdata) / "uv" / "bin" / "ocrmypdf.exe")
        candidates.append(Path(appdata) / "Python" / "Scripts" / "ocrmypdf.exe")
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def run_ocr(input_path, output_path, language="eng"):
    executable = find_ocrmypdf()
    if not executable:
        raise ValueError(
            "OCRmyPDF is not installed or is not on PATH. Follow the Windows OCR setup "
            "instructions in README.md, then restart Offline PDF Studio."
        )

    if not re.fullmatch(r"[a-z]{3}(?:\+[a-z]{3})*", language):
        raise ValueError("Use Tesseract language codes such as eng, tel or eng+tel.")

    command = [
        executable,
        "--skip-text",
        "--rotate-pages",
        "--deskew",
        "--language", language,
        "--output-type", "pdf",
        str(input_path),
        str(output_path)
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=900)
    if result.returncode != 0 or not output_path.exists():
        detail = (result.stderr or result.stdout or "OCR process failed.")[-1200:]
        raise RuntimeError(detail)
    return output_path


def ghostscript_path():
    for name in ("gswin64c.exe", "gswin32c.exe", "gs"):
        found = shutil.which(name)
        if found:
            return found

    install_root = Path(r"C:\Program Files\gs")
    if install_root.exists():
        candidates = list(install_root.glob("gs*/bin/gswin64c.exe"))
        def version_key(item):
            match = re.search(r"gs([0-9]+(?:\.[0-9]+)*)", str(item.parent.parent), re.IGNORECASE)
            return tuple(int(part) for part in match.group(1).split(".")) if match else (0,)
        candidates.sort(key=version_key, reverse=True)
        if candidates:
            return str(candidates[0])
    return None


def compress_with_ghostscript(input_path, output_path, quality="ebook"):
    executable = ghostscript_path()
    if not executable:
        raise ValueError(
            "Ghostscript was not found. Install 64-bit Ghostscript and restart the app. "
            "See README.md for setup instructions."
        )

    presets = {"small": "/screen", "ebook": "/ebook", "print": "/printer"}
    if quality not in presets:
        raise ValueError("Choose Small file, Balanced or Print quality.")

    command = [
        executable,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.5",
        f"-dPDFSETTINGS={presets[quality]}",
        "-dNOPAUSE",
        "-dBATCH",
        "-dSAFER",
        "-dQUIET",
        f"-sOutputFile={output_path}",
        str(input_path)
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=600)
    if result.returncode != 0 or not output_path.exists():
        detail = (result.stderr or result.stdout or "Ghostscript compression failed.")[-1200:]
        raise RuntimeError(detail)
    return output_path


def render_pdf_as_image_docx(pdf_path, output_path):
    """Create a visually faithful DOCX with each PDF page embedded as an image."""
    pdf = fitz.open(str(pdf_path))
    if pdf.page_count == 0:
        raise ValueError("The PDF contains no pages.")

    document = Document()
    for index, page in enumerate(pdf):
        if index > 0:
            section = document.add_section(WD_SECTION.NEW_PAGE)
        else:
            section = document.sections[0]

        width_inches = page.rect.width / 72
        height_inches = page.rect.height / 72
        section.page_width = Inches(width_inches)
        section.page_height = Inches(height_inches)
        section.top_margin = Inches(0)
        section.bottom_margin = Inches(0)
        section.left_margin = Inches(0)
        section.right_margin = Inches(0)

        pixmap = page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8), alpha=False)
        image_path = WORK / f"page_{index + 1}.png"
        pixmap.save(str(image_path))

        paragraph = document.add_paragraph()
        paragraph.paragraph_format.space_before = Inches(0)
        paragraph.paragraph_format.space_after = Inches(0)
        paragraph.add_run().add_picture(
            str(image_path),
            width=Inches(width_inches),
            height=Inches(height_inches)
        )

    document.save(str(output_path))
    pdf.close()
    return output_path


@app.get("/")
def home():
    return render_template("index.html")


@app.post("/api/word-to-pdf")
def word_to_pdf():
    clean_work()
    try:
        src = save_upload()
        if src.suffix.lower() not in [".doc", ".docx", ".odt", ".rtf"]:
            return jsonify(error="Upload a DOC, DOCX, ODT or RTF document."), 400

        soffice = libreoffice_path()
        if not soffice:
            return jsonify(error="LibreOffice was not found. Install LibreOffice and restart the app."), 400

        outdir = WORK / "converted"
        outdir.mkdir()
        result = subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(outdir), str(src)],
            capture_output=True, text=True, timeout=180
        )
        output = outdir / (src.stem + ".pdf")
        if result.returncode != 0 or not output.exists():
            return jsonify(error="Conversion failed: " + (result.stderr or result.stdout)[-500:]), 500
        return send_file(output, as_attachment=True, download_name=output.name)
    except Exception as exc:
        return jsonify(error=str(exc)), 400


@app.post("/api/pdf-to-word")
def pdf_to_word():
    clean_work()
    try:
        src = save_upload()
        if src.suffix.lower() != ".pdf":
            return jsonify(error="Upload a PDF file."), 400

        src = prepare_pdf(src, request.form.get("password", ""))
        conversion_style = request.form.get("conversion_style", "editable")
        ocr_requested = request.form.get("ocr") == "yes"

        if ocr_requested:
            ocr_path = WORK / "ocr_ready.pdf"
            run_ocr(src, ocr_path, request.form.get("language", "eng"))
            src = ocr_path
        elif conversion_style != "visual":
            with fitz.open(str(src)) as check_pdf:
                extracted_chars = sum(
                    len(re.sub(r"\s+", "", page.get_text("text")))
                    for page in check_pdf
                )
                page_count = check_pdf.page_count
            if extracted_chars < max(20, page_count * 8):
                raise ValueError(
                    "This PDF appears to be scanned or has very little selectable text. "
                    "Enable 'Run OCR first' and choose the correct language, then convert again."
                )

        output = WORK / "converted.docx"
        if conversion_style == "visual":
            render_pdf_as_image_docx(src, output)
        else:
            converter = Converter(str(src))
            try:
                converter.convert(str(output), start=0, end=None)
            finally:
                converter.close()

        return send_file(output, as_attachment=True, download_name="converted.docx")
    except Exception as exc:
        return jsonify(error=f"PDF-to-Word conversion failed: {exc}"), 400


@app.post("/api/merge")
def merge():
    clean_work()
    try:
        uploads = request.files.getlist("files")
        if len(uploads) < 2:
            return jsonify(error="Select at least two PDF files."), 400

        password = request.form.get("password", "")
        writer = PdfWriter()
        added = 0
        for file_storage in uploads:
            if not file_storage.filename or not file_storage.filename.lower().endswith(".pdf"):
                continue
            path = save_file_storage(file_storage)
            path = prepare_pdf(path, password)
            writer.append(str(path))
            added += 1

        if added < 2:
            return jsonify(error="Select at least two valid PDF files."), 400

        output = WORK / "merged.pdf"
        with output.open("wb") as fp:
            writer.write(fp)
        return send_file(output, as_attachment=True, download_name="merged.pdf")
    except Exception as exc:
        return jsonify(error=f"Could not merge PDFs: {exc}"), 400


@app.post("/api/split")
def split():
    clean_work()
    try:
        src = save_upload()
        if src.suffix.lower() != ".pdf":
            return jsonify(error="Upload a PDF file."), 400
        src = prepare_pdf(src, request.form.get("password", ""))

        reader = PdfReader(str(src))
        raw = request.form.get("pages", "").strip()
        selected = []
        for part in raw.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                start, end = [int(value.strip()) for value in part.split("-", 1)]
                if start > end:
                    raise ValueError("Page ranges must start before they end.")
                selected.extend(range(start - 1, end))
            else:
                selected.append(int(part) - 1)

        if not selected:
            return jsonify(error="Enter pages, e.g. 1-3,5,8-9."), 400
        if any(index < 0 or index >= len(reader.pages) for index in selected):
            return jsonify(error=f"Page number out of range. This PDF has {len(reader.pages)} pages."), 400

        writer = PdfWriter()
        for index in selected:
            writer.add_page(reader.pages[index])
        output = WORK / "split_pages.pdf"
        with output.open("wb") as fp:
            writer.write(fp)
        return send_file(output, as_attachment=True, download_name="split_pages.pdf")
    except Exception as exc:
        return jsonify(error=f"Could not extract pages: {exc}"), 400


@app.post("/api/compress")
def compress():
    clean_work()
    try:
        src = save_upload()
        if src.suffix.lower() != ".pdf":
            return jsonify(error="Upload a PDF file."), 400
        src = prepare_pdf(src, request.form.get("password", ""))

        output = WORK / "compressed.pdf"
        compress_with_ghostscript(src, output, request.form.get("quality", "ebook"))
        return send_file(output, as_attachment=True, download_name="compressed.pdf")
    except Exception as exc:
        return jsonify(error=f"PDF compression failed: {exc}"), 400


@app.post("/api/rotate")
def rotate():
    clean_work()
    try:
        src = save_upload()
        if src.suffix.lower() != ".pdf":
            return jsonify(error="Upload a PDF file."), 400
        src = prepare_pdf(src, request.form.get("password", ""))

        degrees = int(request.form.get("degrees", "90"))
        if degrees not in (90, 180, 270):
            raise ValueError("Choose 90, 180 or 270 degrees.")
        reader = PdfReader(str(src))
        writer = PdfWriter()
        for page in reader.pages:
            page.rotate(degrees)
            writer.add_page(page)
        output = WORK / "rotated.pdf"
        with output.open("wb") as fp:
            writer.write(fp)
        return send_file(output, as_attachment=True, download_name="rotated.pdf")
    except Exception as exc:
        return jsonify(error=f"Could not rotate PDF: {exc}"), 400


@app.post("/api/ocr")
def ocr_pdf():
    clean_work()
    try:
        src = save_upload()
        if src.suffix.lower() != ".pdf":
            return jsonify(error="Upload a PDF file."), 400
        src = prepare_pdf(src, request.form.get("password", ""))
        output = WORK / "searchable.pdf"
        run_ocr(src, output, request.form.get("language", "eng"))
        return send_file(output, as_attachment=True, download_name="searchable.pdf")
    except Exception as exc:
        return jsonify(error=f"OCR failed: {exc}"), 400


@app.post("/api/protect")
def protect_pdf():
    clean_work()
    try:
        src = save_upload()
        if src.suffix.lower() != ".pdf":
            return jsonify(error="Upload a PDF file."), 400

        new_password = request.form.get("new_password", "")
        confirmation = request.form.get("confirm_password", "")
        if len(new_password) < 6:
            return jsonify(error="Choose a password with at least 6 characters."), 400
        if new_password != confirmation:
            return jsonify(error="The new passwords do not match."), 400

        src = prepare_pdf(src, request.form.get("password", ""))
        reader = PdfReader(str(src))
        writer = PdfWriter(clone_from=reader)
        writer.encrypt(new_password, algorithm="AES-256-R5")

        output = WORK / "protected.pdf"
        with output.open("wb") as fp:
            writer.write(fp)
        return send_file(output, as_attachment=True, download_name="protected.pdf")
    except Exception as exc:
        return jsonify(error=f"Could not protect PDF: {exc}"), 400


@app.post("/api/unlock")
def unlock_pdf():
    clean_work()
    try:
        src = save_upload()
        if src.suffix.lower() != ".pdf":
            return jsonify(error="Upload a PDF file."), 400

        password = request.form.get("password", "")
        reader, was_encrypted = get_pdf_reader(src, password)
        writer = PdfWriter(clone_from=reader)
        output = WORK / "unlocked.pdf"
        with output.open("wb") as fp:
            writer.write(fp)
        return send_file(output, as_attachment=True, download_name="unlocked.pdf")
    except Exception as exc:
        return jsonify(error=f"Could not unlock PDF: {exc}"), 400


@app.post("/api/images-to-pdf")
def images_to_pdf():
    clean_work()
    images = []
    try:
        uploads = request.files.getlist("files")
        if not uploads:
            return jsonify(error="Select one or more images."), 400

        for file_storage in uploads:
            if file_storage.filename:
                images.append(Image.open(file_storage.stream).convert("RGB"))
        if not images:
            return jsonify(error="No valid images were selected."), 400

        output = WORK / "images.pdf"
        images[0].save(output, "PDF", save_all=True, append_images=images[1:])
        return send_file(output, as_attachment=True, download_name="images.pdf")
    except Exception as exc:
        return jsonify(error=f"Image conversion failed: {exc}"), 400
    finally:
        for image in images:
            image.close()


@app.errorhandler(413)
def too_large(_):
    return jsonify(error="File is too large. Maximum upload size is 500 MB."), 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5055, debug=False)
