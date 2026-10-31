"""Fail-closed distribution gate for historical research source archives.

Read-only manifest/path audit; never extract or print confidential contents.
This does NOT determine copyright ownership or guarantee secrets are absent.
"""
from __future__ import annotations
import argparse
import collections
import json
from pathlib import Path
import re
import zipfile

SENSITIVE = {
    "browser_qa_profile": re.compile(r"(?i)(?:^|/)(?:CHROME_QA_ISOLATED|User Data|browser-profile)(?:/|$)"),
    "browser_state_file": re.compile(r"(?i)(?:^|/)(?:Cookies(?:-journal)?|Login Data|Web Data|Local State|History|Visited Links|Session Storage)(?:/|$)"),
    "credentials_file": re.compile(r"(?i)(?:^|/)(?:secrets?\.json|credentials(?:\.[^/]*)?|\.env(?:\.[^/]*)?|id_rsa|id_ed25519|[^/]*\.pem|[^/]*\.p12)(?:/|$)"),
}
MEDIA_SUFFIXES = {".pdf", ".pptx", ".docx"}
LICENSE_FILES = {"LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE",
                 "LICENCE.md", "COPYING", "COPYING.txt"}


def audit_manifest(source):
    path = Path(source)
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        if manifest.get("format") != "dchr-source-archive-v1":
            raise ValueError("Unsupported source archive format")
        files = manifest.get("files")
        if not isinstance(files, list):
            raise ValueError("Source manifest missing files")
        counters = collections.Counter()
        roots = set()
        for entry in files:
            value = entry["root"] + "/" + entry["path"]
            roots.add(entry["root"])
            for code, pattern in SENSITIVE.items():
                if pattern.search(value):
                    counters[code] += 1
            if Path(entry["path"]).suffix.lower() in MEDIA_SUFFIXES:
                counters["documents_media_needing_rights_review"] += 1
            if Path(entry["path"]).name.lower().startswith("license"):
                counters["license_named_files"] += 1
        return {
            "asset": path.name,
            "records": len(files),
            "root_aliases": len(roots),
            "manifest_errors": len(manifest.get("errors", [])),
            "restricted_path_categories": {name: int(counters[name]) for name in SENSITIVE},
            "documents_media_needing_rights_review": counters["documents_media_needing_rights_review"],
            "license_named_files": counters["license_named_files"],
        }


def audit(checkout, archives):
    checkout = Path(checkout)
    matched_licenses = sorted(p.name for p in checkout.iterdir()
                              if p.is_file() and p.name in LICENSE_FILES)
    findings = []
    if not matched_licenses:
        findings.append("PROJECT_LICENSE_UNSPECIFIED")
    entries = [audit_manifest(name) for name in archives]
    if any(sum(a["restricted_path_categories"].values()) for a in entries):
        findings.append("SENSITIVE_ARCHIVE_PATHS")
    if any(a["documents_media_needing_rights_review"] for a in entries):
        findings.append("MEDIA_REDISTRIBUTION_RIGHTS_NOT_VERIFIED")
    if any(a["manifest_errors"] for a in entries):
        findings.append("SOURCE_ARCHIVE_ERRORS")
    if not entries:
        findings.append("NO_RELEASE_ASSETS_AUDITED")
    return {
        "schema": "dchr-release-compliance-v1",
        "status": "BLOCKED_EXTERNAL_DISTRIBUTION" if findings else "REQUIRES_HUMAN_CLEARANCE",
        "project_license_files": matched_licenses,
        "findings": findings,
        "assets": entries,
        "checks_are_limited_to": "Declared paths and metadata, not source-content secrets, ownership or legal advice",
        "credential_values_exposed": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--archive", action="append", default=[], type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--gate", action="store_true",
                        help="Return nonzero if external distribution is not affirmatively cleared")
    args = parser.parse_args()
    result = audit(args.checkout, args.archive)
    payload = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.report:
        if args.report.exists():
            parser.error("Report destination exists; choose a new file")
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload, encoding="utf-8")
    print(payload)
    if args.gate:
        # Manifest/path automation cannot grant distribution rights by itself.
        raise SystemExit(2)


if __name__ == "__main__":
    main()
