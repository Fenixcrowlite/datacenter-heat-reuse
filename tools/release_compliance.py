"""Fail-closed distribution gate for historical research source archives.

Read-only manifest/path audit; never extract or print confidential contents.
This does NOT determine copyright ownership or guarantee secrets are absent.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
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
PINNED_C130_ARCHIVES = {
    "heat-reuse-source-2026-10-30.zip":
        "3eecbe7e2c7bae487d3c9d083e23520566ae863edac060130aaab424a07c9880",
    "heat-reuse-supplement-2026-10-31.zip":
        "56787a7fb97f08aa50dc05c0dd87a52f5653ec1d3cd2e90b045186e15c8538f5",
    "heat-reuse-scientific-qa-correction-2026-10-31.zip":
        "3f78994f2f85790b0e81ea6ede400a397f7a14de0fe96334518267f807d617a6",
}


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


def audit(checkout, archives, *, full_content=None, nested_content=None):
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
    content_attestation = None
    if full_content is not None:
        raw = Path(full_content).read_bytes()
        result = json.loads(raw)
        expected = [e["asset"] for e in entries]
        if (result.get("schema") != "dchr-c130-full-content-classification-v1"
            or result.get("distribution_status") != "BLOCKED_EXTERNAL_DISTRIBUTION"
            or result.get("source_archives") != expected
            or result.get("aggregate",{}).get("manifest_paths") != sum(e["records"] for e in entries)
            or result.get("verified_unique_object_digests_across_assets",0) < 1):
            raise ValueError("Full content scan does not match the selected archives")
        risk=result.get("risk_flag_path_counts",{})
        if not isinstance(risk,dict) or any(not isinstance(v,int) or v<0 for v in risk.values()):
            raise ValueError("Invalid redacted full content risk counts")
        # A filename-matched report can be stale. Confirm the exact immutable
        # research source ZIP bytes independently before using the content audit.
        verified_archive_hashes = {}
        for source in archives:
            source=Path(source)
            expected_digest=PINNED_C130_ARCHIVES.get(source.name)
            if expected_digest:
                with source.open("rb") as stream:
                    actual_digest=hashlib.file_digest(stream,"sha256").hexdigest()
                if actual_digest!=expected_digest:
                    raise ValueError("C130 source archive SHA256 does not match pinned original")
                verified_archive_hashes[source.name]=actual_digest
        content_attestation={
            "pinned_archive_sha256_confirmed":verified_archive_hashes,
            "report_sha256":hashlib.sha256(raw).hexdigest(),
            "verified_object_digests":result["verified_unique_object_digests_across_assets"],
            "high_risk_path_count":result["aggregate"].get("paths_with_high_risk_flag"),
            "home_path_matches":risk.get("user_home_path",0),
            "email_like_matches":risk.get("email_like",0),
            "credential_style_assignments":risk.get("credential_assignment",0),
            "content_excerpts_included":False,
        }
        if content_attestation["home_path_matches"] or content_attestation["email_like_matches"]:
            findings.append("CONTENT_IDENTITY_REVIEW_REQUIRED")
        if content_attestation["credential_style_assignments"]:
            findings.append("CREDENTIAL_STYLE_CONTENT_REVIEW_REQUIRED")
    nested_attestation=None
    if nested_content is not None:
        raw=Path(nested_content).read_bytes()
        result=json.loads(raw)
        if (result.get("schema")!="dchr-c130-nested-container-risk-v1"
            or result.get("distribution_status")!="BLOCKED_EXTERNAL_DISTRIBUTION"
            or [a["asset"] for a in result.get("per_archive",[])]!=[e["asset"] for e in entries]):
            raise ValueError("Nested document scan does not match selected archives")
        observations=result.get("nested_flag_logical_path_counts",{})
        nested_attestation={
            "report_sha256":hashlib.sha256(raw).hexdigest(),
            "creator_metadata_paths":observations.get("nested_creator_metadata",0),
            "other_flagged_nested_path_counts":sum(v for k,v in observations.items() if k!="nested_creator_metadata"),
            "raw_creator_values_included":False,
        }
        if nested_attestation["creator_metadata_paths"]:
            findings.append("NESTED_CREATOR_METADATA_REVIEW_REQUIRED")
    return {
        "schema": "dchr-release-compliance-v1",
        "status": "BLOCKED_EXTERNAL_DISTRIBUTION" if findings else "REQUIRES_HUMAN_CLEARANCE",
        "project_license_files": matched_licenses,
        "findings": findings,
        "assets": entries,
        "full_content_attestation": content_attestation,
        "nested_content_attestation": nested_attestation,
        "checks_are_limited_to": "Pattern-based source and optional content review, not comprehensive decoding, source ownership or legal advice",
        "credential_values_exposed": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--archive", action="append", default=[], type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--full-content-report", type=Path,
                        help="Local redacted full-object content scan report")
    parser.add_argument("--nested-report", type=Path,
                        help="Local redacted compressed-model inner XML scan report")
    parser.add_argument("--gate", action="store_true",
                        help="Return nonzero if external distribution is not affirmatively cleared")
    args = parser.parse_args()
    result = audit(args.checkout, args.archive,
                   full_content=args.full_content_report,
                   nested_content=args.nested_report)
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
