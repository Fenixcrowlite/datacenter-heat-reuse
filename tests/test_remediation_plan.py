import csv
from pathlib import Path
import tempfile
import unittest

from tools.remediation_plan import disposition,write_plan


class RemediationPlanTests(unittest.TestCase):
    def test_no_auto_cleared_state(self):
        samples=[
            ({"browser_profile"},".bin","P0_QUARANTINE_CANDIDATE"),
            ({"user_home_path"},".py","P1_IDENTITY_REVIEW"),
            (set(),".slx","P2_NESTED_METADATA_REVIEW"),
            ({"opaque_or_binary_content_review"},".bin","P3_OPAQUE_OR_RIGHTS_REVIEW"),
            ({"source_provenance_review"},".m","P4_SOURCE_PROVENANCE_REVIEW"),
            (set(),".txt","P5_UNREVIEWED_NO_CLEARANCE"),
        ]
        for flags,ext,expected in samples:
            with self.subTest(expected=expected):
                self.assertEqual(expected,disposition(flags,ext))

    def test_queue_is_redacted_and_no_release_approval(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            index=root/"input.csv"
            with index.open("w",encoding="utf-8",newline="") as f:
                w=csv.writer(f)
                w.writerow(["archive_name","root_id_sha256","path_id_sha256",
                            "suffix","declared_bytes","risk_flags"])
                w.writerow(["source.zip","a"*64,"b"*64,".py","30","email_like"])
                w.writerow(["source.zip","a"*64,"c"*64,".slx","12",""])
                w.writerow(["source.zip","d"*64,"e"*64,".bin","2","browser_state"])
            result=write_plan(index,root/"queue.csv",root/"report.json")
            self.assertEqual(3,result["classified_paths"])
            self.assertEqual(0,result["automatically_approved_for_external_release"])
            self.assertEqual(1,result["disposition_counts"]["P0_QUARANTINE_CANDIDATE"])
            with (root/"queue.csv").open(encoding="utf-8",newline="") as f:
                rows=list(csv.DictReader(f))
            self.assertEqual(3,len(rows))
            self.assertTrue(all(len(r["path_id_sha256"])==64 for r in rows))
            with self.assertRaises(FileExistsError):
                write_plan(index,root/"queue.csv",root/"report.json")

    def test_bad_hash_and_unknown_flag_rejected_without_final_output(self):
        for wrong in ("not_a_hash", "b"*64):
            with self.subTest(wrong=wrong),tempfile.TemporaryDirectory() as td:
                root=Path(td)
                index=root/"input.csv"
                with index.open("w",encoding="utf-8",newline="") as f:
                    w=csv.writer(f)
                    w.writerow(["archive_name","root_id_sha256","path_id_sha256",
                                "suffix","declared_bytes","risk_flags"])
                    w.writerow(["source.zip","a"*64,wrong,".m","12",
                                "secret_unknown_flag" if wrong!="not_a_hash" else "email_like"])
                with self.assertRaisesRegex(ValueError,"hash|Unknown"):
                    write_plan(index,root/"queue.csv",root/"report.json")
                self.assertFalse((root/"queue.csv").exists())
                self.assertFalse((root/"report.json").exists())


if __name__=="__main__":
    unittest.main()
