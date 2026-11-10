from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from pdf2docx import Converter
from PIL import Image
import shutil, subprocess, os

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024
ROOT = Path(__file__).parent
WORK = ROOT / "work"
WORK.mkdir(exist_ok=True)

def clean_work():
    for p in WORK.iterdir():
        try:
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
        except Exception:
            pass

def save_upload(field="file"):
    f = request.files.get(field)
    if not f or not f.filename:
        raise ValueError("Please choose a file.")
    path = WORK / secure_filename(f.filename)
    f.save(path)
    return path

def libreoffice_path():
    candidates = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return shutil.which("soffice")

@app.get("/")
def home():
    return render_template("index.html")

@app.post("/api/word-to-pdf")
def word_to_pdf():
    clean_work()
    src = save_upload()
    if src.suffix.lower() not in [".doc", ".docx", ".odt", ".rtf"]:
        return jsonify(error="Upload a Word document (.doc or .docx), ODT or RTF file."), 400
    soffice = libreoffice_path()
    if not soffice:
        return jsonify(error="LibreOffice was not found. Install LibreOffice, then restart this app."), 400
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

@app.post("/api/pdf-to-word")
def pdf_to_word():
    clean_work()
    src = save_upload()
    if src.suffix.lower() != ".pdf":
        return jsonify(error="Upload a PDF file."), 400
    output = WORK / (src.stem + ".docx")
    try:
        cv = Converter(str(src))
        cv.convert(str(output), start=0, end=None)
        cv.close()
    except Exception as e:
        return jsonify(error=f"Conversion failed: {e}"), 500
    return send_file(output, as_attachment=True, download_name=output.name)

@app.post("/api/merge")
def merge():
    clean_work()
    uploads = request.files.getlist("files")
    if len(uploads) < 2:
        return jsonify(error="Select at least two PDF files."), 400
    writer = PdfWriter()
    try:
        for f in uploads:
            if not f.filename.lower().endswith(".pdf"):
                continue
            path = WORK / secure_filename(f.filename)
            f.save(path)
            writer.append(str(path))
        output = WORK / "merged.pdf"
        with output.open("wb") as fp:
            writer.write(fp)
    except Exception as e:
        return jsonify(error=f"Could not merge PDFs: {e}"), 400
    return send_file(output, as_attachment=True, download_name="merged.pdf")

@app.post("/api/split")
def split():
    clean_work()
    src = save_upload()
    if src.suffix.lower() != ".pdf":
        return jsonify(error="Upload a PDF file."), 400
    try:
        reader = PdfReader(str(src))
        raw = request.form.get("pages", "").strip()
        selected = []
        for part in raw.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                a, b = [int(x.strip()) for x in part.split("-", 1)]
                selected.extend(range(a - 1, b))
            else:
                selected.append(int(part) - 1)
        if not selected:
            return jsonify(error="Enter pages, e.g. 1-3,5,8-9."), 400
        if any(i < 0 or i >= len(reader.pages) for i in selected):
            return jsonify(error=f"Page number out of range. This PDF has {len(reader.pages)} pages."), 400
        writer = PdfWriter()
        for i in selected:
            writer.add_page(reader.pages[i])
        output = WORK / "split_pages.pdf"
        with output.open("wb") as fp:
            writer.write(fp)
    except Exception as e:
        return jsonify(error=f"Split failed: {e}"), 400
    return send_file(output, as_attachment=True, download_name="split_pages.pdf")

@app.post("/api/compress")
def compress():
    clean_work()
    src = save_upload()
    if src.suffix.lower() != ".pdf":
        return jsonify(error="Upload a PDF file."), 400
    try:
        reader = PdfReader(str(src))
        writer = PdfWriter()
        for page in reader.pages:
            page.compress_content_streams()
            writer.add_page(page)
        output = WORK / "compressed.pdf"
        with output.open("wb") as fp:
            writer.write(fp)
    except Exception as e:
        return jsonify(error=f"Compression failed: {e}"), 400
    return send_file(output, as_attachment=True, download_name="compressed.pdf")

@app.post("/api/rotate")
def rotate():
    clean_work()
    src = save_upload()
    if src.suffix.lower() != ".pdf":
        return jsonify(error="Upload a PDF file."), 400
    try:
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
    except Exception as e:
        return jsonify(error=f"Rotate failed: {e}"), 400
    return send_file(output, as_attachment=True, download_name="rotated.pdf")

@app.post("/api/images-to-pdf")
def images_to_pdf():
    clean_work()
    uploads = request.files.getlist("files")
    if not uploads:
        return jsonify(error="Select one or more images."), 400
    images = []
    try:
        for f in uploads:
            images.append(Image.open(f.stream).convert("RGB"))
        output = WORK / "images.pdf"
        images[0].save(output, "PDF", save_all=True, append_images=images[1:])
        for im in images:
            im.close()
    except Exception as e:
        return jsonify(error=f"Image conversion failed: {e}"), 400
    return send_file(output, as_attachment=True, download_name="images.pdf")

@app.errorhandler(413)
def too_large(_):
    return jsonify(error="File is too large. Maximum upload size is 500 MB."), 413

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5055, debug=False)
