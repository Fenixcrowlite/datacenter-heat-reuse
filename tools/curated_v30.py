"""Create a strictly scoped, LOCAL-ONLY v30 research evidence archive from C130.

Never modifies the original C130 asset. This is a byte-preserved allowlisted
scientific subset, NOT rights clearance, not a publication-safe release.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import zipfile

from .snapshot import restore, safe_relative

FORMAT = "dchr-source-archive-v1"
EXPECTED_SOURCE_SHA256 = "3eecbe7e2c7bae487d3c9d083e23520566ae863edac060130aaab424a07c9880"
SOURCE_PREFIX = "results/stateflow_v30_20261009T212727142Z/source_snapshot/"
SOURCE_FILES = (
    "DCHR_Dispatch_Stateflow_v28.slx",
    "DCHR_Dispatch_Stateflow_v30.slx",
    "build_dispatch_stateflow_v30.m",
    "dchr_stateflow_hp_v30.m",
    "export_stateflow_mat_audit_v30.m",
    "heat_pump_step_v14.m",
    "run_stateflow_acceptance_v30.m",
    "run_stateflow_faults_v30.m",
    "simulate_dispatch_v30.m",
    "stateflow_allocate_v30.m",
    "stateflow_choose_mode_v30.m",
    "stateflow_contract_gate_v30.m",
    "stateflow_reference_v30.py",
    "storage_kernel_v30.m",
    "storage_parameters_v30.m",
    "storage_step_v30.m",
    "spec/cases.json",
    "spec/equation_qa.json",
    "spec/vectors.csv",
)
# The original fault/audit fixtures contain home-directory identifiers.
# Keep them in restricted private research history; do NOT transfer them.
BENCHMARK_FILES = (
    "v30_native_cases.json", "v30_native_trace.csv",
)
RESTRICTED_BENCHMARK_FILES = (
    "v30_native_faults.json", "v30_native_fault_audit.json",
)
PATTERNS = {
    "email": re.compile(rb"(?i)[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}"),
    "user_home": re.compile(rb"(?i)[a-z]:[\\/]+users[\\/]|/home/[a-zA-Z0-9_-]+/"),
    "github_token": re.compile(rb"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})"),
    "private_key": re.compile(rb"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
    "credential_assignment": re.compile(rb"(?i)(?:password|api[_-]?key|client[_-]?secret|access[_-]?token)\s*[=:]\s*[\x22\x27][^\x22\x27\r\n]{6,}"),
    "personal_metadata": re.compile(rb"(?i)(?:hostname|lastModifiedBy)\s*[=:]\s*[\x22\x27][^\x22\x27\r\n]{2,}"),
}
EXCLUDED_NAMING = re.compile(r"(?i)(?:cookies|login data|local state|secrets\.json|credential|\.env|history|browser.?profile|chrome_qa)")
MAX_SOURCE_BYTES = 2_000_000
MAX_NESTED_UNCOMPRESSED = 30_000_000


def hash_bytes(data):
    return hashlib.sha256(data).hexdigest()


def hash_file(path):
    sha=hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024*1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def check_content(data, label):
    """Fail closed; never print or return any matched content."""
    if len(data)>MAX_SOURCE_BYTES:
        raise ValueError("Candidate exceeds maximum permitted size: "+label)
    if any(p.search(data) for p in PATTERNS.values()):
        raise ValueError("Potential confidential content in allowlisted candidate: "+label)
    if label.endswith(".slx"):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as nested:
                infos=nested.infolist()
                if len(infos)>500 or sum(info.file_size for info in infos)>MAX_NESTED_UNCOMPRESSED:
                    raise ValueError("Excessive embedded SLX content: "+label)
                names=set()
                for info in infos:
                    if info.is_dir():
                        continue
                    name=info.filename
                    safe_relative(name)
                    folded=name.casefold()
                    if folded in names:
                        raise ValueError("Duplicate or case-aliased SLX member: "+label)
                    names.add(folded)
                    # A MATLAB .slx is an ordinary zip; symlink entries are not expected.
                    if info.create_system==3 and (info.external_attr >> 16) & 0o170000 == 0o120000:
                        raise ValueError("Symbolic link in SLX: "+label)
                    if EXCLUDED_NAMING.search(name):
                        raise ValueError("Sensitive nested SLX filename: "+label)
                    inner=nested.read(info)
                    if any(p.search(inner) for p in PATTERNS.values()):
                        raise ValueError("Potential confidential nested SLX content: "+label)
        except zipfile.BadZipFile as exc:
            raise ValueError("Invalid Stateflow SLX: "+label) from exc


def select_manifest_entries(manifest):
    if manifest.get("format") != FORMAT or manifest.get("errors"):
        raise ValueError("Untrusted or incomplete source manifest")
    wanted=set(SOURCE_FILES)
    matched={}
    for entry in manifest["files"]:
        if entry.get("root") != "primary":
            continue
        path=entry.get("path","")
        if not isinstance(path,str) or not path.startswith(SOURCE_PREFIX):
            continue
        rel=path[len(SOURCE_PREFIX):]
        if rel in wanted:
            if rel in matched:
                raise ValueError("Duplicate source candidate")
            if EXCLUDED_NAMING.search(rel):
                raise ValueError("Sensitive filename on source allowlist")
            matched[rel]=entry
    if set(matched)!=wanted:
        raise ValueError("Historical source snapshot is missing approved files")
    return matched


def build(source_zip, benchmarks, output, *, expected_source_sha=EXPECTED_SOURCE_SHA256):
    source_zip,benchmarks,output=Path(source_zip),Path(benchmarks),Path(output)
    if output.exists() or output.with_suffix(output.suffix+".partial").exists():
        raise FileExistsError(output)
    if hash_file(source_zip)!=expected_source_sha:
        raise ValueError("Historical archive hash mismatch; stop")
    output.parent.mkdir(parents=True,exist_ok=True)
    contents={}
    with zipfile.ZipFile(source_zip) as source:
        manifest=json.loads(source.read("manifest.json"))
        selected=select_manifest_entries(manifest)
        for rel in SOURCE_FILES:
            item=selected[rel]
            sha=item["sha256"]
            if not re.fullmatch(r"[0-9a-f]{64}",sha):
                raise ValueError("Source object digest format mismatch")
            data=source.read("objects/"+sha)
            if len(data)!=item["bytes"] or hash_bytes(data)!=sha:
                raise ValueError("Source snapshot checksum mismatch: "+rel)
            check_content(data,rel)
            contents["source/"+rel]=data
    for name in BENCHMARK_FILES:
        path=benchmarks/name
        if path.is_symlink() or not path.is_file():
            raise ValueError("Benchmark is missing or symlink: "+name)
        data=path.read_bytes()
        check_content(data,name)
        contents["benchmarks/"+name]=data
    manifest={
        "format":FORMAT,
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "roots":["review_v30"],
        "distribution_status":"PRIVATE_REVIEW_NO_EXTERNAL_SHARING",
        "source_cutoff":"2026-10-31 C130",
        "provenance":{"original_asset_name":source_zip.name,
                      "original_asset_sha256":expected_source_sha,
                      "selection":"exact 19-file native MATLAB v30 source snapshot and 2 numeric benchmark fixtures; diagnostic fault records excluded for local path disclosure"},
        "files":[],
        "excluded":[],
        "errors":[],
    }
    objects={}
    for rel,data in sorted(contents.items()):
        sha=hash_bytes(data)
        if sha not in objects:
            objects[sha]=data
        manifest["files"].append({
            "root":"review_v30","path":rel,"sha256":sha,
            "bytes":len(data),"capture":"allowlisted-byte-verified",
        })
    manifest["object_count"]=len(objects)
    manifest["logical_bytes"]=sum(len(x) for x in contents.values())
    partial=output.with_suffix(output.suffix+".partial")
    try:
        with zipfile.ZipFile(partial,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for sha,data in sorted(objects.items()):
                z.writestr("objects/"+sha,data)
            z.writestr("manifest.json",json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2))
        verification=verify(partial)
        partial.replace(output)
    except BaseException:
        if partial.exists():
            partial.unlink()
        raise
    return {"archive":str(output),"sha256":hash_file(output),"bytes":output.stat().st_size,**verification}


def verify(archive):
    with zipfile.ZipFile(archive) as z:
        names=z.namelist()
        if len(names)!=len(set(names)):
            raise ValueError("Duplicate ZIP entries in curated archive")
        manifest=json.loads(z.read("manifest.json"))
        if manifest.get("format")!=FORMAT or manifest.get("distribution_status")!="PRIVATE_REVIEW_NO_EXTERNAL_SHARING":
            raise ValueError("Restricted review status missing")
        files=manifest.get("files")
        if not isinstance(files,list) or len(files)!=len(SOURCE_FILES)+len(BENCHMARK_FILES):
            raise ValueError("Unexpected selected file count")
        expected={"source/"+name for name in SOURCE_FILES}|{"benchmarks/"+name for name in BENCHMARK_FILES}
        actual=set()
        objects=set()
        for entry in files:
            if entry.get("root")!="review_v30" or entry.get("path") not in expected or entry["path"] in actual:
                raise ValueError("Unexpected or duplicate review file")
            actual.add(entry["path"])
            sha=entry["sha256"]
            if not re.fullmatch(r"[0-9a-f]{64}",sha):
                raise ValueError("Invalid review digest")
            obj="objects/"+sha
            info=z.getinfo(obj)
            if info.file_size!=entry["bytes"]:
                raise ValueError("Review object size mismatch")
            data=z.read(obj)
            if hash_bytes(data)!=sha:
                raise ValueError("Review object SHA mismatch")
            check_content(data,entry["path"])
            objects.add(obj)
        if actual!=expected or set(z.namelist())!=objects|{"manifest.json"}:
            raise ValueError("Unexpected archive contents")
        if len(objects)!=manifest["object_count"]:
            raise ValueError("Object count mismatch")
    return {"files":len(files),"verified_objects":len(objects),
            "distribution_status":"PRIVATE_REVIEW_NO_EXTERNAL_SHARING"}


def attest(archive, recipient):
    """Independently hash every restored file, rejecting extra files."""
    checked=verify(archive)
    recipient=Path(recipient).resolve()
    with zipfile.ZipFile(archive) as z:
        manifest=json.loads(z.read("manifest.json"))
    expected=set()
    for item in manifest["files"]:
        rel=safe_relative(item["root"])/safe_relative(item["path"])
        expected.add(rel.as_posix())
        file=recipient.joinpath(*rel.parts)
        if file.is_symlink() or not file.is_file():
            raise ValueError("Missing file or symlink in restored recipient")
        if file.stat().st_size!=item["bytes"] or hash_file(file)!=item["sha256"]:
            raise ValueError("Recipient on-disk size/SHA mismatch")
    actual=set()
    for file in recipient.rglob("*"):
        if file.is_symlink():
            raise ValueError("Unexpected symlink in recipient")
        if file.is_file():
            actual.add(file.relative_to(recipient).as_posix())
    if actual!=expected:
        raise ValueError("Extra or missing files in restored recipient")
    return {**checked,"on_disk_hash_verified":len(expected),
            "unexpected_files":0,"recipient":str(recipient)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="command",required=True)
    b=sub.add_parser("build")
    b.add_argument("--source",type=Path,required=True)
    b.add_argument("--benchmarks",type=Path,required=True)
    b.add_argument("--out",type=Path,required=True)
    v=sub.add_parser("verify")
    v.add_argument("archive",type=Path)
    u=sub.add_parser("restore")
    u.add_argument("archive",type=Path)
    u.add_argument("target",type=Path)
    a=sub.add_parser("attest")
    a.add_argument("archive",type=Path)
    a.add_argument("recipient",type=Path)
    args=parser.parse_args()
    if args.command=="build": result=build(args.source,args.benchmarks,args.out)
    elif args.command=="verify": result=verify(args.archive)
    elif args.command=="attest": result=attest(args.archive,args.recipient)
    else:
        checked=verify(args.archive)
        if args.target.exists():
            raise FileExistsError(args.target)
        output=restore(args.archive,args.target)
        result={**checked,**output}
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
