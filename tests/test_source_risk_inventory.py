"""Risk inventory does not reveal matched values or disclose filename paths."""
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from tools.source_risk_inventory import (
    SCHEMA, classify_chunks, classify_path, scan_assets,
)


class SourceRiskInventoryTests(unittest.TestCase):
    @staticmethod
    def source(path, records):
        objects={}
        files=[]
        for root,rel,body in records:
            digest=hashlib.sha256(body).hexdigest()
            objects[digest]=body
            files.append({"root":root,"path":rel,"bytes":len(body),"sha256":digest})
        with zipfile.ZipFile(path,"w") as z:
            z.writestr("manifest.json",json.dumps({
                "format":"dchr-source-archive-v1","files":files,
                "errors":[],"object_count":len(objects)}))
            for digest,data in objects.items():
                z.writestr("objects/"+digest,data)
        return path

    def test_streaming_boundary_identifies_risk_without_values(self):
        token=b"ghp_"+b"A"*33
        body=b"filler-"+token
        digest,size,risks=classify_chunks([body[:9],body[9:14],body[14:]])
        self.assertEqual(hashlib.sha256(body).hexdigest(),digest)
        self.assertEqual(len(body),size)
        self.assertIn("token_signature",risks)

    def test_real_archive_style_scan_redacts_paths_and_values(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            token=b"ghp_"+b"S"*37
            archive=self.source(root/"source.zip",[
                ("primary","browser/CHROME_QA_ISOLATED/Default/Network/Cookies",
                 b"private binary content"),
                ("primary","runtime/secrets.json",b'{"credential":"'+token+b'"}'),
                ("primary","models/sample.m",b"function f()\nend\n"),
                ("primary","report/conference.pdf",b"dummy pdf"),
            ])
            report_path=root/"report.json"
            index_path=root/"index.csv"
            result=scan_assets([archive],report_path,index_path)
            self.assertEqual(SCHEMA,result["schema"])
            self.assertEqual(4,result["aggregate"]["manifest_paths"])
            self.assertGreaterEqual(result["risk_flag_path_counts"]["token_signature"],1)
            self.assertGreaterEqual(result["risk_flag_path_counts"]["credential_filename"],1)
            self.assertGreaterEqual(result["risk_flag_path_counts"]["browser_profile"],1)
            report=report_path.read_bytes()
            index=index_path.read_bytes()
            for secret in (b"secrets.json",b"Cookies",token,b"CHROME_QA_ISOLATED"):
                self.assertNotIn(secret,report)
                self.assertNotIn(secret,index)
            with index_path.open(encoding="utf-8",newline="") as f:
                rows=list(csv.DictReader(f))
            self.assertEqual(4,len(rows))
            self.assertTrue(all(len(row["path_id_sha256"])==64 for row in rows))
            with self.assertRaises(FileExistsError):
                scan_assets([archive],report_path,index_path)

    def test_corrupt_object_fails_without_report_or_inventory(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            path=self.source(root/"source.zip",[("primary","model.py",b"expected")])
            with zipfile.ZipFile(path) as z:
                members={name:z.read(name) for name in z.namelist()}
            member=next(name for name in members if name.startswith("objects/"))
            members[member]=b"tampered"
            wrong=root/"corrupt.zip"
            with zipfile.ZipFile(wrong,"w") as z:
                for name,data in members.items():
                    z.writestr(name,data)
            report=root/"report.json";index=root/"index.csv"
            with self.assertRaisesRegex(ValueError,"hash/size"):
                scan_assets([wrong],report,index)
            self.assertFalse(report.exists());self.assertFalse(index.exists())

    def test_conflicting_digest_metadata_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            archive=self.source(root/"source.zip",[
                ("primary","a.txt",b"duplicate"),
                ("primary","b.txt",b"duplicate"),
            ])
            with zipfile.ZipFile(archive) as z:
                entries={name:z.read(name) for name in z.namelist()}
            manifest=json.loads(entries["manifest.json"])
            manifest["files"][1]["bytes"]=999
            entries["manifest.json"]=json.dumps(manifest).encode()
            bad=root/"conflict.zip"
            with zipfile.ZipFile(bad,"w") as z:
                for name,data in entries.items():
                    z.writestr(name,data)
            with self.assertRaisesRegex(ValueError,"Conflicting"):
                scan_assets([bad],root/"report.json",root/"index.csv")


if __name__=="__main__":
    unittest.main()
