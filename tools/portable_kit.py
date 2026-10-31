"""Build/verify/extract an offline, versioned DCHR transfer kit.

Combines a tracked Git commit with the three immutable C130 source archive
assets without changing any of them. The recipient only needs Python 3.11+.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

FORMAT = "dchr-offline-kit-v1"
ASSETS = {
    "heat-reuse-source-2026-10-30.zip": (
        464100930, "3eecbe7e2c7bae487d3c9d083e23520566ae863edac060130aaab424a07c9880"),
    "heat-reuse-supplement-2026-10-31.zip": (
        72538624, "56787a7fb97f08aa50dc05c0dd87a52f5653ec1d3cd2e90b045186e15c8538f5"),
    "heat-reuse-scientific-qa-correction-2026-10-31.zip": (
        169500, "3f78994f2f85790b0e81ea6ede400a397f7a14de0fe96334518267f807d617a6"),
}
CODE_MEMBER = "code/repository.zip"
MANIFEST_MEMBER = "kit-manifest.json"
# Only the runnable application, tests, documentation and the MATLAB source
# needed for numerical source-backed tests. The historical research sources
# are supplied separately as the three immutable C130 archives.
CODE_PATHS = (
    ".dockerignore", ".gitattributes", ".github", ".gitignore",
    "Dockerfile", "README.md", "compose.yaml", "datasets",
    "docs", "heat_reuse", "manifests", "models", "original/primary/matlab",
    "pyproject.toml", "tests", "tools", "web",
)
FORBIDDEN_PARTS = {
    ".git", ".env", ".venv", "cookies", "cookies-journal",
    "local state", "login data", "web data", "chrome_qa_isolated",
    "browser-profile", "credentials", "id_rsa",
}
def review_source_archive(path):
    with zipfile.ZipFile(path) as source:
        names = source.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate application archive entries")
        for name in names:
            parts = name.rstrip("/").split("/")
            if (name.startswith("/") or "\\" in name or
                    any(part in ("", ".", "..") for part in parts)):
                raise ValueError("Unsafe application archive path: " + name)
            lowered = [part.casefold() for part in parts]
            if any(part in FORBIDDEN_PARTS or part.startswith(".env.") for part in lowered):
                if not name.endswith(".env.example"):
                    raise ValueError("Browser/credential artifact in application: " + name)
            in_scope = any(name == allowed or name.startswith(allowed + "/")
                           for allowed in CODE_PATHS)
            # git archive emits parent directory entries for a selected nested path.
            parent_marker = name.endswith("/") and any(
                allowed.startswith(name) for allowed in CODE_PATHS)
            if not (in_scope or parent_marker):
                raise ValueError("Unexpected source outside application allowlist: " + name)
    return len(names)

def digest_stream(file):
    sha = hashlib.sha256()
    size = 0
    while data := file.read(2 * 1024 * 1024):
        size += len(data)
        sha.update(data)
    return size, sha.hexdigest()

def digest(path):
    with Path(path).open("rb") as handle:
        return digest_stream(handle)

def build(checkout, archives, destination):
    checkout, archives, destination = map(Path, (checkout, archives, destination))
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.with_suffix(destination.suffix + ".partial").exists():
        raise FileExistsError(destination)
    validator = destination.parent / "verify_portable_kit.py"
    validator_bytes = Path(__file__).read_bytes()
    if validator.exists() and validator.read_bytes() != validator_bytes:
        raise FileExistsError("An unrelated recipient validator exists: " + str(validator))
    sha = subprocess.run(["git", "-C", str(checkout), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True).stdout.strip()
    branch = subprocess.run(["git", "-C", str(checkout), "branch", "--show-current"],
        capture_output=True, text=True, check=True).stdout.strip()
    if not branch.startswith("codex/") or len(sha) != 40:
        raise ValueError("Kit must be built from an explicit review branch commit")
    with tempfile.TemporaryDirectory(prefix="dchr-kit-") as td:
        code = Path(td) / "repository.zip"
        # Never archive the whole Git tree: legacy research history includes
        # QA browser directories that must not be shipped as application files.
        tracked = subprocess.run(["git", "-C", str(checkout), "ls-tree",
            "-r", "--name-only", sha], capture_output=True, text=True, check=True).stdout.splitlines()
        include = [allowed for allowed in CODE_PATHS if any(
            item == allowed or item.startswith(allowed + "/") for item in tracked)]
        if not include or "README.md" not in include:
            raise ValueError("Application tree lacks README")
        subprocess.run(["git", "-C", str(checkout), "archive",
            "--format=zip", "-o", str(code), sha, "--", *include], check=True)
        selected_files = review_source_archive(code)
        code_size, code_sha = digest(code)
        if not zipfile.is_zipfile(code):
            raise ValueError("Git source snapshot is not a ZIP")
        manifest = {
            "format": FORMAT,
            "commit": sha,
            "branch": branch,
            "source_cutoff": "2026-10-31 C130",
            "application_member": CODE_MEMBER,
            "application_tracked_paths": selected_files,
            "application_allowlist": list(CODE_PATHS),
            "assets": [{"member": CODE_MEMBER, "bytes": code_size,
                        "sha256": code_sha, "role": "current-review-code"}],
            "notes": "Private review candidate; source C130 archives are immutable and separate from review-branch code. No Docker image is included.",
        }
        for name, (size, expected) in ASSETS.items():
            file = archives / name
            if not file.is_file() or digest(file) != (size, expected):
                raise ValueError("Research release asset has wrong hash or size: " + name)
            manifest["assets"].append({"member": "sources/" + name,
                "bytes": size, "sha256": expected, "role": "immutable-c130-source"})
        partial = destination.with_suffix(destination.suffix + ".partial")
        try:
            with zipfile.ZipFile(partial, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as z:
                z.writestr(MANIFEST_MEMBER, json.dumps(manifest, sort_keys=True, indent=2) + "\n")
                z.write(code, CODE_MEMBER)
                for name in ASSETS:
                    z.write(archives / name, "sources/" + name)
            verified = verify(partial)
            if verified["commit"] != sha:
                raise ValueError("Bundle commit mismatch")
            partial.replace(destination)
            if not validator.exists():
                validator.write_bytes(validator_bytes)
        except BaseException:
            # Do not present a partially built kit under the final name.
            if partial.exists():
                partial.unlink()
            raise
    return {"bundle": str(destination), "sha256": digest(destination)[1],
            "bytes": destination.stat().st_size, **verified}

def verify(bundle):
    bundle = Path(bundle)
    with zipfile.ZipFile(bundle) as z:
        listed = z.namelist()
        if len(listed) != len(set(listed)):
            raise ValueError("Duplicate bundle ZIP entry")
        if MANIFEST_MEMBER not in listed:
            raise ValueError("Missing bundle manifest")
        manifest = json.loads(z.read(MANIFEST_MEMBER))
        if manifest.get("format") != FORMAT:
            raise ValueError("Unsupported bundle format")
        expected_members = {MANIFEST_MEMBER}
        records = manifest.get("assets")
        if not isinstance(records, list) or len(records) != 4:
            raise ValueError("Expected code archive plus three C130 assets")
        if manifest.get("application_member") != CODE_MEMBER:
            raise ValueError("Unexpected application member")
        if not isinstance(manifest.get("commit"), str) or len(manifest["commit"]) != 40 or any(c not in "0123456789abcdef" for c in manifest["commit"]):
            raise ValueError("Invalid Git revision")
        for entry in records:
            member = entry.get("member")
            if member not in {CODE_MEMBER, *("sources/" + n for n in ASSETS)} or member in expected_members:
                raise ValueError("Unexpected or duplicated kit asset")
            expected_members.add(member)
            if member != CODE_MEMBER:
                if (entry["bytes"], entry["sha256"]) != ASSETS[member.split("/")[-1]]:
                    raise ValueError("Changed C130 source contract")
            if entry.get("bytes", -1) < 0 or not isinstance(entry.get("sha256"), str) or len(entry["sha256"]) != 64:
                raise ValueError("Invalid asset metadata")
            info = z.getinfo(member)
            if info.file_size != entry["bytes"]:
                raise ValueError("Bundle member size mismatch: " + member)
            with z.open(info) as contents:
                actual = digest_stream(contents)
            if actual != (entry["bytes"], entry["sha256"]):
                raise ValueError("Bundle member hash mismatch: " + member)
        if set(listed) != expected_members:
            raise ValueError("Unexpected files in kit")
    return {"commit": manifest["commit"], "assets_verified": 4,
            "source_assets_verified": 3, "format": FORMAT}

def unpack(bundle, target):
    """Create a new recipient kit directory. Never replace an existing target."""
    bundle, target = Path(bundle), Path(target).absolute()
    if target.exists():
        raise FileExistsError(target)
    checked = verify(bundle)
    if target.parent.is_dir() is False:
        raise FileNotFoundError(target.parent)
    stage = target.with_name(target.name + ".incomplete")
    if stage.exists():
        raise FileExistsError(stage)
    stage.mkdir()
    try:
        with zipfile.ZipFile(bundle) as z:
            for member in (CODE_MEMBER, *("sources/" + n for n in ASSETS)):
                output = stage.joinpath(*member.split("/"))
                output.parent.mkdir(parents=True, exist_ok=True)
                with z.open(member) as source, output.open("xb") as dest:
                    shutil.copyfileobj(source, dest, 2 * 1024 * 1024)
        # The bundle was verified before the copy; verify disk copies too.
        for member in (CODE_MEMBER, *("sources/" + n for n in ASSETS)):
            with zipfile.ZipFile(bundle) as z:
                manifest = json.loads(z.read(MANIFEST_MEMBER))
            asset = next(a for a in manifest["assets"] if a["member"] == member)
            if digest(stage / member) != (asset["bytes"], asset["sha256"]):
                raise ValueError("Recipient disk copy verification failed: " + member)
        stage.rename(target)
    except BaseException:
        # Keep the incomplete directory for forensics; never give it the ready name.
        raise
    return {"target": str(target), **checked}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--checkout", required=True)
    b.add_argument("--archives", required=True)
    b.add_argument("--out", required=True)
    v = sub.add_parser("verify")
    v.add_argument("bundle")
    u = sub.add_parser("unpack")
    u.add_argument("bundle")
    u.add_argument("target")
    args = parser.parse_args()
    if args.cmd == "build":
        result = build(args.checkout, args.archives, args.out)
    elif args.cmd == "verify":
        result = verify(args.bundle)
    else:
        result = unpack(args.bundle, args.target)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
