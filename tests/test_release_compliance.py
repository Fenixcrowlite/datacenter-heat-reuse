"""Check private-source disclosure risks without revealing secret contents."""
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from tools.release_compliance import audit, audit_manifest


class ReleaseComplianceTests(unittest.TestCase):
    @staticmethod
    def source_archive(where, files):
        with zipfile.ZipFile(where, "w") as target:
            target.writestr("manifest.json", json.dumps({
                "format": "dchr-source-archive-v1", "files": [
                    {"root": "primary", "path": name, "sha256": "0"*64, "bytes": 0}
                    for name in files
                ], "errors": []
            }))
        return where

    def test_secret_and_browser_paths_block_external_distribution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            files=[
                "source/model.m",
                "runtime/secrets.json",
                "qa/CHROME_QA_ISOLATED/Default/Network/Cookies-journal",
                "qa/CHROME_QA_ISOLATED/Default/History",
                "docs/supplied_document.pdf",
            ]
            archive=self.source_archive(root/"research.zip",files)
            report=audit(root,[archive])
            self.assertEqual("BLOCKED_EXTERNAL_DISTRIBUTION",report["status"])
            self.assertIn("PROJECT_LICENSE_UNSPECIFIED",report["findings"])
            self.assertIn("SENSITIVE_ARCHIVE_PATHS",report["findings"])
            self.assertIn("MEDIA_REDISTRIBUTION_RIGHTS_NOT_VERIFIED",report["findings"])
            self.assertEqual(1,report["assets"][0]["restricted_path_categories"]["credentials_file"])
            self.assertEqual(2,report["assets"][0]["restricted_path_categories"]["browser_state_file"])
            self.assertEqual(2,report["assets"][0]["restricted_path_categories"]["browser_qa_profile"])
            self.assertNotIn("secrets.json",json.dumps(report))
            self.assertNotIn("Cookies-journal",json.dumps(report))

    def test_clean_names_are_not_a_licensing_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"LICENSE").write_text("Test-only; not a real grant.")
            archive=self.source_archive(root/"safe.zip",["models/test_model.m","docs/notes.md"])
            report=audit(root,[archive])
            self.assertEqual("REQUIRES_HUMAN_CLEARANCE",report["status"])
            self.assertEqual([],report["findings"])
            self.assertEqual(["LICENSE"],report["project_license_files"])

    def test_archive_format_is_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            archive=root/"wrong.zip"
            with zipfile.ZipFile(archive,"w") as z:
                z.writestr("manifest.json",json.dumps({"format":"wrong","files":[]}))
            with self.assertRaisesRegex(ValueError,"format"):
                audit_manifest(archive)

    def test_no_assets_is_not_clearance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            report=audit(root,[])
            self.assertEqual("BLOCKED_EXTERNAL_DISTRIBUTION",report["status"])
            self.assertIn("NO_RELEASE_ASSETS_AUDITED",report["findings"])


if __name__ == "__main__":
    unittest.main()
