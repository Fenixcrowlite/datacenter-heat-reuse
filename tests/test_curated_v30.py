"""Private v30 evidence extraction: source-allowlist and privacy regressions."""
from pathlib import Path
import hashlib
import io
import json
import tempfile
import unittest
import zipfile

from tools.curated_v30 import (
    BENCHMARK_FILES, SOURCE_FILES, SOURCE_PREFIX,
    attest, build, check_content, hash_file, select_manifest_entries, verify,
)
from tools.snapshot import restore


class CuratedV30Tests(unittest.TestCase):
    @staticmethod
    def make_source(root, *, extra=False, tamper=False):
        objects={}
        entries=[]
        for name in SOURCE_FILES:
            if name.endswith(".slx"):
                stream=io.BytesIO()
                with zipfile.ZipFile(stream,"w") as z:
                    z.writestr("simulink/model.xml","<stateflow>safe</stateflow>")
                data=stream.getvalue()
            else:
                data=(name+"\nSynthetic fixture, not native MATLAB\n").encode()
            sha=hashlib.sha256(data).hexdigest()
            objects[sha]=data
            entries.append({"root":"primary","path":SOURCE_PREFIX+name,
                            "sha256":sha,"bytes":len(data),"capture":"file-bytes"})
        if extra:
            secret=b"THIS_CONTENT_MUST_NOT_LEAK_IN_SELECTED_SET"
            sha=hashlib.sha256(secret).hexdigest()
            objects[sha]=secret
            entries.append({"root":"primary","path":"runtime/secrets.json",
                            "sha256":sha,"bytes":len(secret),"capture":"file-bytes"})
        manifest={"format":"dchr-source-archive-v1","files":entries,
                  "errors":[],"roots":["primary"]}
        archive=root/"C130-research.zip"
        with zipfile.ZipFile(archive,"w") as z:
            z.writestr("manifest.json",json.dumps(manifest))
            for sha,data in objects.items():
                z.writestr("objects/"+sha,(b"modified-object" if tamper and sha==entries[0]["sha256"] else data))
        return archive

    @staticmethod
    def make_benchmarks(root):
        directory=root/"benchmarks"
        directory.mkdir()
        for name in BENCHMARK_FILES:
            (directory/name).write_text("Synthetic numerical reference: "+name)
        return directory

    def test_build_verify_and_restore_byte_identical_private_subset(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            source=self.make_source(root,extra=True)
            benchmarks=self.make_benchmarks(root)
            output=root/"curated.zip"
            record=build(source,benchmarks,output,expected_source_sha=hash_file(source))
            self.assertEqual(21,record["files"])
            self.assertEqual("PRIVATE_REVIEW_NO_EXTERNAL_SHARING",
                             verify(output)["distribution_status"])
            with zipfile.ZipFile(output) as z:
                manifest=json.loads(z.read("manifest.json"))
                self.assertEqual(21,len(manifest["files"]))
                self.assertFalse(any("secrets.json" in r["path"] for r in manifest["files"]))
                self.assertNotIn(b"THIS_CONTENT_MUST_NOT_LEAK_IN_SELECTED_SET",
                                 b"".join(z.read(i) for i in z.namelist()))
            recipient=root/"recipient"
            restored=restore(output,recipient)
            self.assertEqual(21,restored["verified_files"])
            self.assertEqual(21,attest(output,recipient)["on_disk_hash_verified"])
            self.assertEqual((recipient/"review_v30/benchmarks"/BENCHMARK_FILES[0]).read_bytes(),
                             (benchmarks/BENCHMARK_FILES[0]).read_bytes())

    def test_fails_closed_when_restricted_benchmark_contains_local_home(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            source=self.make_source(root)
            benchmarks=self.make_benchmarks(root)
            (benchmarks/BENCHMARK_FILES[0]).write_text(r"C:\Users\PrivateProfile\secret")
            out=root/"must-not-exist.zip"
            with self.assertRaisesRegex(ValueError,"Potential confidential content"):
                build(source,benchmarks,out,expected_source_sha=hash_file(source))
            self.assertFalse(out.exists())

    def test_source_object_integrity_checked(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            source=self.make_source(root,tamper=True)
            benchmarks=self.make_benchmarks(root)
            with self.assertRaisesRegex(ValueError,"checksum mismatch"):
                build(source,benchmarks,root/"rejected.zip",
                      expected_source_sha=hash_file(source))
            self.assertFalse((root/"rejected.zip").exists())

    def test_nested_slx_scanned_for_secret_and_noncanonical_path(self):
        for member,body in (
            ("simulink/data.xml",b"user=someone@example.org"),
            ("simulink/../bad.xml",b"content"),
        ):
            with self.subTest(member=member):
                stream=io.BytesIO()
                with zipfile.ZipFile(stream,"w") as z:
                    z.writestr(member,body)
                with self.assertRaisesRegex(ValueError,"confidential|Noncanonical"):
                    check_content(stream.getvalue(),"DCHR_Dispatch_Stateflow_v30.slx")

    def test_nested_slx_case_alias_rejected(self):
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,"w") as z:
            z.writestr("simulink/model.XML",b"a")
            z.writestr("simulink/MODEL.xml",b"b")
        with self.assertRaisesRegex(ValueError,"case-aliased"):
            check_content(stream.getvalue(),"DCHR_Dispatch_Stateflow_v30.slx")

    def test_missing_source_rejected_and_existing_output_preserved(self):
        entries=[{"root":"primary","path":SOURCE_PREFIX+SOURCE_FILES[0]}]
        with self.assertRaisesRegex(ValueError,"missing approved"):
            select_manifest_entries({"format":"dchr-source-archive-v1",
                                     "files":entries,"errors":[]})
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            source=self.make_source(root)
            benchmarks=self.make_benchmarks(root)
            out=root/"existing.zip"
            out.write_bytes(b"preserve-me")
            with self.assertRaises(FileExistsError):
                build(source,benchmarks,out,expected_source_sha=hash_file(source))
            self.assertEqual(b"preserve-me",out.read_bytes())

    def test_attestation_rejects_on_disk_modification_and_extra_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            source=self.make_source(root)
            benchmarks=self.make_benchmarks(root)
            archive=root/"bundle.zip"
            build(source,benchmarks,archive,expected_source_sha=hash_file(source))
            recipient=root/"receiver"
            restore(archive,recipient)
            (recipient/"review_v30/benchmarks"/BENCHMARK_FILES[0]).write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError,"mismatch"):
                attest(archive,recipient)
            with zipfile.ZipFile(archive) as z:
                m=json.loads(z.read("manifest.json"))
                match=next(f for f in m["files"] if f["path"]=="benchmarks/"+BENCHMARK_FILES[0])
                (recipient/"review_v30/benchmarks"/BENCHMARK_FILES[0]).write_bytes(
                    z.read("objects/"+match["sha256"]))
            (recipient/"EXTRA.txt").write_text("foreign")
            with self.assertRaisesRegex(ValueError,"Extra"):
                attest(archive,recipient)

    def test_raw_fault_audit_excluded_from_allowlist(self):
        self.assertEqual(("v30_native_cases.json","v30_native_trace.csv"),BENCHMARK_FILES)
        self.assertNotIn("v30_native_faults.json",BENCHMARK_FILES)
        self.assertNotIn("v30_native_fault_audit.json",BENCHMARK_FILES)


if __name__=="__main__":
    unittest.main()
