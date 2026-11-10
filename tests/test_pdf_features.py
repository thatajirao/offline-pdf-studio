import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

from docx import Document
from pypdf import PdfReader, PdfWriter

from app import app, run_ocr


def make_blank_pdf():
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


class PdfFeatureTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_protect_then_unlock_pdf(self):
        source = make_blank_pdf()
        protected = self.client.post(
            "/api/protect",
            data={
                "file": (io.BytesIO(source), "sample.pdf"),
                "new_password": "test-pass-123",
                "confirm_password": "test-pass-123",
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(protected.status_code, 200)

        protected_reader = PdfReader(io.BytesIO(protected.data))
        self.assertTrue(protected_reader.is_encrypted)
        self.assertTrue(protected_reader.decrypt("test-pass-123"))

        unlocked = self.client.post(
            "/api/unlock",
            data={
                "file": (io.BytesIO(protected.data), "protected.pdf"),
                "password": "test-pass-123",
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(unlocked.status_code, 200)
        unlocked_reader = PdfReader(io.BytesIO(unlocked.data))
        self.assertFalse(unlocked_reader.is_encrypted)
        self.assertEqual(len(unlocked_reader.pages), 1)

    def test_wrong_pdf_password_is_rejected(self):
        writer = PdfWriter()
        writer.add_blank_page(width=300, height=300)
        writer.encrypt("correct-pass-123", algorithm="AES-256-R5")
        source = io.BytesIO()
        writer.write(source)

        response = self.client.post(
            "/api/unlock",
            data={
                "file": (io.BytesIO(source.getvalue()), "protected.pdf"),
                "password": "wrong-pass",
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("incorrect", response.get_json()["error"].lower())

    def test_scanned_pdf_is_flagged_before_editable_conversion(self):
        response = self.client.post(
            "/api/pdf-to-word",
            data={"file": (io.BytesIO(make_blank_pdf()), "scan.pdf")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("scanned", response.get_json()["error"].lower())

    def test_visual_docx_mode_returns_a_word_document(self):
        response = self.client.post(
            "/api/pdf-to-word",
            data={
                "file": (io.BytesIO(make_blank_pdf()), "page.pdf"),
                "conversion_style": "visual",
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200)
        document = Document(io.BytesIO(response.data))
        self.assertEqual(len(document.sections), 1)
        self.assertEqual(len(document.inline_shapes), 1)

    def test_compression_keeps_original_if_result_is_larger(self):
        source = make_blank_pdf()

        def fake_compressor(input_path, output_path, quality="ebook"):
            Path(output_path).write_bytes(Path(input_path).read_bytes() + (b"extra" * 100))

        with patch("app.compress_with_ghostscript", side_effect=fake_compressor):
            response = self.client.post(
                "/api/compress",
                data={"file": (io.BytesIO(source), "source.pdf"), "quality": "ebook"},
                content_type="multipart/form-data",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Compression-Result"), "unchanged")
        self.assertEqual(response.data, source)

    def test_compression_preserves_pdf_password(self):
        writer = PdfWriter()
        writer.add_blank_page(width=300, height=300)
        writer.encrypt("keep-this-pass", algorithm="AES-256-R5")
        protected_source = io.BytesIO()
        writer.write(protected_source)

        def fake_compressor(input_path, output_path, quality="ebook"):
            Path(output_path).write_bytes(make_blank_pdf())

        with patch("app.compress_with_ghostscript", side_effect=fake_compressor):
            response = self.client.post(
                "/api/compress",
                data={
                    "file": (io.BytesIO(protected_source.getvalue()), "protected.pdf"),
                    "password": "keep-this-pass",
                    "quality": "ebook",
                },
                content_type="multipart/form-data",
            )

        self.assertEqual(response.status_code, 200)
        result_reader = PdfReader(io.BytesIO(response.data))
        self.assertTrue(result_reader.is_encrypted)
        self.assertTrue(result_reader.decrypt("keep-this-pass"))

    def test_ocr_builds_oversampling_and_optional_clean_arguments(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "source.pdf"
            output = Path(temp_dir) / "output.pdf"
            source.write_bytes(make_blank_pdf())

            def fake_run(command, **kwargs):
                Path(command[-1]).write_bytes(make_blank_pdf())
                return SimpleNamespace(returncode=0, stderr="", stdout="")

            with patch("app.find_ocrmypdf", return_value="ocrmypdf"), patch(
                "app.subprocess.run", side_effect=fake_run
            ) as runner:
                run_ocr(source, output, "eng+tel", 400, True)

            command = runner.call_args.args[0]
            self.assertIn("--oversample", command)
            self.assertIn("400", command)
            self.assertIn("--clean", command)
            self.assertIn("eng+tel", command)

    def test_ocr_rejects_unsupported_resolution(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "source.pdf"
            output = Path(temp_dir) / "output.pdf"
            source.write_bytes(make_blank_pdf())
            with patch("app.find_ocrmypdf", return_value="ocrmypdf"):
                with self.assertRaisesRegex(ValueError, "200, 300, 400 or 600"):
                    run_ocr(source, output, "eng", 350, False)


if __name__ == "__main__":
    unittest.main()
