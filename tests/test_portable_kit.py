"""Synthetic adversarial tests for the full offline kit build/verify/unpack path."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock
import zipfile

from tools.portable_kit import ASSETS, build, verify, unpack, MANIFEST_MEMBER


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
        run("add", "README.md")
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


if __name__ == "__main__":
    unittest.main()
