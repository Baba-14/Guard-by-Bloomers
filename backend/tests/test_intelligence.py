import io
import json
import unittest

from openpyxl import Workbook

from backend.app.intelligence import analyse_content, deidentify, normalize_phone, normalize_url
from backend.app.intelligence_routes import parse_upload


class IntelligenceServiceTests(unittest.TestCase):
    def test_analysis_is_composable_and_non_persistent(self):
        result = analyse_content("message", "Urgent: send your OTP immediately")
        self.assertIn(result.level, ("Caution", "High Risk"))
        self.assertIn("OTP requested", result.signals)
        self.assertIn("text_model", result.components)

    def test_deidentification_removes_direct_contact_data(self):
        content, changed = deidentify("Email ama@example.com or call 024 123 4567")
        self.assertTrue(changed)
        self.assertNotIn("ama@example.com", content)
        self.assertNotIn("024 123 4567", content)

    def test_normalizers(self):
        self.assertEqual(normalize_phone("024-123-4567"), "+233241234567")
        self.assertEqual(normalize_url("EXAMPLE.COM/path."), "https://example.com/path")

    def test_csv_and_json_imports(self):
        csv_rows = parse_upload("items.csv", b"content,label\nhello,legitimate\n")
        json_rows = parse_upload("items.json", json.dumps([{"content": "test"}]).encode())
        self.assertEqual(csv_rows[0]["label"], "legitimate")
        self.assertEqual(json_rows[0]["content"], "test")

    def test_xlsx_import(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(["content", "label"])
        sheet.append(["sample", "uncertain"])
        payload = io.BytesIO()
        workbook.save(payload)
        rows = parse_upload("items.xlsx", payload.getvalue())
        self.assertEqual(rows[0]["content"], "sample")


if __name__ == "__main__":
    unittest.main()
