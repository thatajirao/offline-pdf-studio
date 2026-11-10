import io
import unittest

from pypdf import PdfReader, PdfWriter

from app import app


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


if __name__ == "__main__":
    unittest.main()
