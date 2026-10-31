"""Offline acquisition gates; synthetic in-memory fixtures are not paper evidence."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import unittest

import fitz

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("acquisition_v14", ROOT / "audit" / "Marcinichen_acquisition_v14.py")
acquisition = importlib.util.module_from_spec(spec)
spec.loader.exec_module(acquisition)


def fixture(title=acquisition.TITLE, doi=acquisition.DOI):
    with fitz.open() as doc:
        page = doc.new_page()
        page.insert_text((30, 30), title + "\n" + doi)
        doc.new_page().insert_text((30, 30), "SYNTHETIC ACQUISITION TEST FIXTURE; NOT ARTICLE EVIDENCE")
        # A legal PDF comment provides size without persisting a synthetic source.
        return doc.tobytes() + b"\n%" + b"fixture " * 600 + b"\n"


class AcquisitionGateTests(unittest.TestCase):
    def test_html_denied_page_rejected(self):
        with self.assertRaises(ValueError):
            acquisition.inspect_candidate(b"<html>429 Too Many Requests</html>" * 200)

    def test_spoofed_pdf_magic_rejected(self):
        with self.assertRaises(ValueError):
            acquisition.inspect_candidate(b"%PDF invalid access page" + b"x" * 5000)

    def test_small_truncated_candidate_rejected(self):
        with self.assertRaises(ValueError):
            acquisition.inspect_candidate(b"%PDF tiny")

    def test_oversized_candidate_rejected(self):
        with self.assertRaises(ValueError):
            acquisition.inspect_candidate(b"%PDF" + b"x" * acquisition.MAX_BYTES)

    def test_wrong_doi_rejected(self):
        with self.assertRaises(ValueError):
            acquisition.inspect_candidate(fixture(doi="10.0000/wrong"))

    def test_wrong_title_rejected(self):
        with self.assertRaises(ValueError):
            acquisition.inspect_candidate(fixture(title="unrelated article"))

    def test_identity_pass_does_not_claim_equation_or_table_validation(self):
        result = acquisition.inspect_candidate(fixture())
        self.assertEqual(result["page_count"], 2)
        self.assertEqual(result["identity_gate"], "TITLE_AND_DOI_MATCH")
        self.assertFalse(result["equations_verified"])
        self.assertFalse(result["temperature_tables_verified"])


if __name__ == "__main__":
    started = datetime.now(timezone.utc)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AcquisitionGateTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    report = {"started_utc": started.isoformat(), "finished_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "OFFLINE_SYNTHETIC_ACQUISITION_GATES_ONLY", "primary_text_verified": False,
              "tests_run": result.testsRun, "failed": len(result.failures), "errors": len(result.errors),
              "passed": result.testsRun - len(result.failures) - len(result.errors)}
    out = ROOT / "audit" / f"Marcinichen_acquisition_v14_tests_{started.strftime('%Y%m%dT%H%M%S%fZ')}.json"
    with out.open("x", encoding="utf-8") as target:
        json.dump(report, target, indent=2)
    print("EVIDENCE", out.relative_to(ROOT))
    raise SystemExit(0 if result.wasSuccessful() else 1)
