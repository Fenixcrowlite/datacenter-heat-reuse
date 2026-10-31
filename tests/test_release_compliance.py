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

    def test_incorporates_redacted_full_and_nested_scan_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            archive=self.source_archive(root/"research.zip",["model.slx"])
            full=root/"full.json"
            nested=root/"nested.json"
            full.write_text(json.dumps({
                "schema":"dchr-c130-full-content-classification-v1",
                "distribution_status":"BLOCKED_EXTERNAL_DISTRIBUTION",
                "source_archives":["research.zip"],
                "aggregate":{"manifest_paths":1,"paths_with_high_risk_flag":1},
                "verified_unique_object_digests_across_assets":1,
                "risk_flag_path_counts":{"user_home_path":1,"credential_assignment":1}
            }))
            nested.write_text(json.dumps({
                "schema":"dchr-c130-nested-container-risk-v1",
                "distribution_status":"BLOCKED_EXTERNAL_DISTRIBUTION",
                "per_archive":[{"asset":"research.zip"}],
                "nested_flag_logical_path_counts":{"nested_creator_metadata":1}
            }))
            result=audit(root,[archive],full_content=full,nested_content=nested)
            self.assertIn("CONTENT_IDENTITY_REVIEW_REQUIRED",result["findings"])
            self.assertIn("CREDENTIAL_STYLE_CONTENT_REVIEW_REQUIRED",result["findings"])
            self.assertIn("NESTED_CREATOR_METADATA_REVIEW_REQUIRED",result["findings"])
            self.assertEqual(1,result["full_content_attestation"]["verified_object_digests"])
            self.assertNotIn("model.slx",json.dumps(result))

    def test_pinned_release_with_replaced_bytes_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            name="heat-reuse-source-2026-10-30.zip"
            archive=self.source_archive(root/name,["model.m"])
            full=root/"full.json"
            full.write_text(json.dumps({
                "schema":"dchr-c130-full-content-classification-v1",
                "distribution_status":"BLOCKED_EXTERNAL_DISTRIBUTION",
                "source_archives":[name],
                "aggregate":{"manifest_paths":1},
                "verified_unique_object_digests_across_assets":1,
                "risk_flag_path_counts":{}
            }))
            with self.assertRaisesRegex(ValueError,"pinned original"):
                audit(root,[archive],full_content=full)

    def test_wrong_full_report_file_count_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            archive=self.source_archive(root/"research.zip",["model.m"])
            full=root/"full.json"
            full.write_text(json.dumps({
                "schema":"dchr-c130-full-content-classification-v1",
                "distribution_status":"BLOCKED_EXTERNAL_DISTRIBUTION",
                "source_archives":["research.zip"],
                "aggregate":{"manifest_paths":500},
                "verified_unique_object_digests_across_assets":1,
                "risk_flag_path_counts":{}
            }))
            with self.assertRaisesRegex(ValueError,"does not match"):
                audit(root,[archive],full_content=full)

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
