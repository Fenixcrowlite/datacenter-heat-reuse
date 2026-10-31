"""Synthetic adversarial tests for the full offline kit build/verify/unpack path."""
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock
import zipfile

from tools.portable_kit import ASSETS, build, verify, unpack, MANIFEST_MEMBER


@unittest.skipUnless(shutil.which("git"),
    "Git executable is required for producer-side packaging, not recipient verification")
class PortableKitTests(unittest.TestCase):
    def make_kit(self, root):
        repo = root / "git"
        source = root / "sources"
        repo.mkdir()
        source.mkdir()
        def run(*parts):
            return subprocess.run(["git", "-C", str(repo), *parts],
                                  check=True, capture_output=True)
        run("init", "-b", "codex/offline-kit-test")
        (repo / "README.md").write_text("Code only; no credentials.", encoding="utf-8")
        (repo / "original/synapse/browser/Default/Network").mkdir(parents=True)
        (repo / "original/synapse/browser/Default/Network/Cookies-journal").write_bytes(b"secret-sentinel")
        run("add", "README.md", "original/synapse")
        run("-c", "user.name=Kit Test", "-c", "user.email=kit@test.invalid",
            "commit", "-m", "synthetic kit candidate")
        fixtures = {}
        for name in ("a.zip", "b.zip", "c.zip"):
            content = (name * 9).encode("ascii")
            (source / name).write_bytes(content)
            fixtures[name] = (len(content), hashlib.sha256(content).hexdigest())
        destination = root / "kit.zip"
        with mock.patch.dict(ASSETS, fixtures, clear=True):
            result = build(repo, source, destination)
        return destination, fixtures, result

    def test_build_verify_and_extract_clean_recipient(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle, fixtures, result = self.make_kit(root)
            self.assertEqual(4, result["assets_verified"])
            with zipfile.ZipFile(bundle) as z:
                with zipfile.ZipFile(io.BytesIO(z.read("code/repository.zip"))) as code:
                    self.assertEqual(["README.md"], code.namelist())
            self.assertEqual((root / "verify_portable_kit.py").read_bytes(),
                             (Path(__file__).resolve().parents[1] / "tools/portable_kit.py").read_bytes())
            with mock.patch.dict(ASSETS, fixtures, clear=True):
                self.assertEqual(3, verify(bundle)["source_assets_verified"])
                recipient = root / "recipient"
                info = unpack(bundle, recipient)
                self.assertEqual(4, info["assets_verified"])
                self.assertTrue((recipient / "code/repository.zip").is_file())
                self.assertEqual((recipient / "sources/a.zip").read_bytes(), b"a.zip" * 9)
                with self.assertRaises(FileExistsError):
                    unpack(bundle, recipient)

    def test_corrupt_asset_detected_before_creating_recipient(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle, fixtures, _ = self.make_kit(root)
            with zipfile.ZipFile(bundle) as z:
                members = [(n, z.read(n)) for n in z.namelist()]
            # Replace one member but retain the manifest's original SHA.
            fake = root / "tampered.zip"
            with zipfile.ZipFile(fake, "w") as z:
                for name, body in members:
                    z.writestr(name, b"malicious-file" if name == "sources/a.zip" else body)
            with mock.patch.dict(ASSETS, fixtures, clear=True):
                with self.assertRaisesRegex(ValueError, "size mismatch|hash mismatch"):
                    unpack(fake, root / "recipient")
            self.assertFalse((root / "recipient").exists())

    def test_rejects_credential_path_inside_allowed_code_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            bundle, fixtures, _=self.make_kit(root)
            repo=root/"git"
            (repo/"tools").mkdir()
            (repo/"tools/Cookies-journal").write_bytes(b"no-personal-secrets-ever")
            subprocess.run(["git","-C",str(repo),"add","tools/Cookies-journal"],
                           check=True,capture_output=True)
            subprocess.run(["git","-C",str(repo),"-c","user.name=Kit Test",
                "-c","user.email=kit@test.invalid","commit","-m","should be refused"],
                check=True,capture_output=True)
            with mock.patch.dict(ASSETS,fixtures,clear=True):
                with self.assertRaisesRegex(ValueError,"Browser/credential artifact"):
                    build(repo,root/"sources",root/"refused.zip")
            self.assertFalse((root/"refused.zip").exists())

    def test_rejects_high_confidence_secret_in_allowed_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            _, fixtures, _=self.make_kit(root)
            repo=root/"git"
            (repo/"docs").mkdir()
            (repo/"docs/project_notes.txt").write_text(
                "token=github_pat_"+"X"*46,encoding="utf-8")
            subprocess.run(["git","-C",str(repo),"add","docs/project_notes.txt"],
                           check=True,capture_output=True)
            subprocess.run(["git","-C",str(repo),"-c","user.name=Kit Test",
                "-c","user.email=kit@test.invalid","commit","-m","secret test"],
                check=True,capture_output=True)
            with mock.patch.dict(ASSETS,fixtures,clear=True):
                with self.assertRaisesRegex(ValueError,"secret signature"):
                    build(repo,root/"sources",root/"refused.zip")
            self.assertFalse((root/"refused.zip").exists())

    def test_duplicate_member_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle, fixtures, _ = self.make_kit(root)
            bad = root / "duplicate.zip"
            with zipfile.ZipFile(bundle) as original, zipfile.ZipFile(bad, "w") as target:
                for info in original.infolist():
                    target.writestr(info.filename, original.read(info.filename))
                with mock.patch("warnings.warn"):
                    target.writestr(MANIFEST_MEMBER, original.read(MANIFEST_MEMBER))
            with mock.patch.dict(ASSETS, fixtures, clear=True):
                with self.assertRaisesRegex(ValueError, "Duplicate"):
                    verify(bad)


class GitFreeRecipientTests(unittest.TestCase):
    @staticmethod
    def synthetic_bundle(root, corrupt=False):
        # Generate an ordinary valid nested ZIP directly: no Git executable.
        codefile=io.BytesIO()
        with zipfile.ZipFile(codefile,"w") as z:
            z.writestr("README.md","portable Python only")
        code=codefile.getvalue()
        parts={"code/repository.zip":code}
        fake={}
        for name in ("a.zip","b.zip","c.zip"):
            payload=(name*5).encode("ascii")
            parts["sources/"+name]=payload
            fake[name]=(len(payload),hashlib.sha256(payload).hexdigest())
        items=[{"member":name,"bytes":len(payload),
                "sha256":hashlib.sha256(payload).hexdigest()}
               for name,payload in parts.items()]
        manifest={"format":"dchr-offline-kit-v1",
                  "commit":"a"*40,"branch":"codex/synthetic",
                  "application_member":"code/repository.zip",
                  "assets":items}
        target=root/"synthetic-kit.zip"
        with zipfile.ZipFile(target,"w") as z:
            z.writestr(MANIFEST_MEMBER,json.dumps(manifest))
            for name,payload in parts.items():
                z.writestr(name,b"corrupted" if corrupt and name=="sources/c.zip"
                           else payload)
        return target,fake

    def test_recipient_verifies_and_unpacks_without_git(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            bundle,assets=self.synthetic_bundle(root)
            with mock.patch.dict(ASSETS,assets,clear=True):
                self.assertEqual(4,verify(bundle)["assets_verified"])
                restored=unpack(bundle,root/"recipient")
            self.assertEqual("a"*40,restored["commit"])
            self.assertEqual((root/"recipient/sources/a.zip").read_bytes(),
                             b"a.zip"*5)
            self.assertTrue((root/"recipient/code/repository.zip").is_file())

    def test_recipient_rejects_tampered_asset_without_git_or_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            bundle,assets=self.synthetic_bundle(root,corrupt=True)
            with mock.patch.dict(ASSETS,assets,clear=True):
                with self.assertRaisesRegex(ValueError,"hash mismatch|size mismatch"):
                    unpack(bundle,root/"recipient")
            self.assertFalse((root/"recipient").exists())



if __name__ == "__main__":
    unittest.main()
