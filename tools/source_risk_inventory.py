"""LOCAL-ONLY, privacy-redacted full C130 content and path risk inventory.

Reads every unique ZIP object with bounded chunks, verifies declared SHA256,
never exports text matches or raw file names, and emits aggregate JSON plus
hashed-path CSV. This is NOT a clearance decision or automated redaction.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import tempfile
import time
import zipfile

SCHEMA="dchr-c130-full-content-classification-v1"
ALLOWED_FORMAT="dchr-source-archive-v1"
CONTENT_PATTERNS={
    "token_signature":re.compile(rb"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|AKIA[0-9A-Z]{16})"),
    "private_key_marker":re.compile(rb"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
    "user_home_path":re.compile(rb"(?i)(?:[a-z]:[\\/]+users[\\/]|/home/[a-zA-Z0-9_-]+/)"),
    "email_like":re.compile(rb"(?i)\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b"),
    "credential_assignment":re.compile(rb"(?i)\b(?:password|api[_-]?key|client[_-]?secret|access[_-]?token)\b\s*[=:]\s*['\x22][^'\x22\r\n]{6,}"),
}
PATH_PATTERNS={
    "browser_profile":re.compile(r"(?i)(?:^|/)(?:CHROME_QA_ISOLATED|User Data|browser-profile)(?:/|$)"),
    "browser_state":re.compile(r"(?i)(?:^|/)(?:Cookies(?:-journal)?|Login Data|Web Data|Local State|History|Visited Links|Session Storage)(?:/|$)"),
    "credential_filename":re.compile(r"(?i)(?:^|/)(?:secrets?\.json|credentials(?:\.[^/]*)?|\.env(?:\.[^/]*)?|id_rsa|id_ed25519|[^/]*\.pem|[^/]*\.p12)(?:/|$)"),
    "possible_personal_data":re.compile(r"(?i)(?:^|/)(?:profile|users?|private|account|session|personal|contacts)(?:/|$)"),
}
DOCUMENT_EXTENSIONS={".pdf",".pptx",".docx",".xlsx"}
SOURCE_EXTENSIONS={".m",".py",".c",".cpp",".h",".hpp",".slx",".json",".csv",".mat"}
HIGH_RISK={"token_signature","private_key_marker","credential_assignment","browser_state","browser_profile","credential_filename"}

def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def classify_chunks(chunks):
    found=set()
    hasher=hashlib.sha256()
    size=0
    tail=b""
    for chunk in chunks:
        hasher.update(chunk)
        size+=len(chunk)
        view=tail+chunk
        for name,rg in CONTENT_PATTERNS.items():
            if name not in found and rg.search(view):
                found.add(name)
        tail=view[-512:]
    return hasher.hexdigest(),size,found

def classify_path(root,relative):
    name=root+"/"+relative
    found={key for key,pat in PATH_PATTERNS.items() if pat.search(name)}
    ext=PurePosixPath(relative).suffix.lower()
    if ext in DOCUMENT_EXTENSIONS:
        found.add("third_party_rights_review")
    if ext in SOURCE_EXTENSIONS:
        found.add("source_provenance_review")
    if ext in {".bin",".mat",".slx",".sqlite",".db"}:
        found.add("opaque_or_binary_content_review")
    return found,ext

def validate_manifest(z):
    names=z.namelist()
    if len(set(names))!=len(names):
        raise ValueError("Duplicate ZIP member")
    manifest=json.loads(z.read("manifest.json"))
    if manifest.get("format")!=ALLOWED_FORMAT or manifest.get("errors"):
        raise ValueError("Unsupported or incomplete C130 source manifest")
    entries=manifest.get("files")
    if not isinstance(entries,list):
        raise ValueError("Manifest files missing")
    unique={}
    for e in entries:
        value=e["sha256"]
        if not re.fullmatch(r"[0-9a-f]{64}",value):
            raise ValueError("Invalid digest")
        n=e.get("bytes")
        if not isinstance(n,int) or n<0:
            raise ValueError("Invalid size")
        if value in unique and unique[value]!=n:
            raise ValueError("Conflicting file size for same digest")
        unique[value]=n
    if int(manifest.get("object_count",-1))!=len(unique):
        raise ValueError("Manifest unique-object count mismatch")
    actual_members=set(names)
    expected_members={"manifest.json"}|{"objects/"+digest for digest in unique}
    if actual_members!=expected_members:
        raise ValueError("Archive object members mismatch manifest")
    return entries,unique

def scan_assets(archives, report_file, index_file, progress_file=None):
    archives=[Path(a) for a in archives]
    report_file=Path(report_file)
    index_file=Path(index_file)
    if report_file.exists() or index_file.exists():
        raise FileExistsError("Do not overwrite an existing audit")
    report_file.parent.mkdir(parents=True,exist_ok=True)
    if report_file.parent!=index_file.parent:
        raise ValueError("Keep audit artifacts together")
    aggregate=collections.Counter()
    per_asset=[]
    root_stats={}
    risky_by_path=collections.Counter()
    per_object_risks=collections.Counter()
    all_objects_seen=set()
    started=time.monotonic()
    temp_index=index_file.with_suffix(index_file.suffix+".partial")
    if temp_index.exists():
        raise FileExistsError(temp_index)
    try:
        with temp_index.open("w",encoding="utf-8",newline="") as index_stream:
            writer=csv.writer(index_stream)
            writer.writerow(["archive_name","root_id_sha256","path_id_sha256",
                             "suffix","declared_bytes","risk_flags"])
            for path in archives:
                print("AUDIT_START",path.name,flush=True)
                asset_count=collections.Counter()
                with zipfile.ZipFile(path) as z:
                    entries,objects=validate_manifest(z)
                    object_risks={}
                    for i,(digest,expected_size) in enumerate(objects.items(),1):
                        with z.open("objects/"+digest) as reader:
                            def chunks():
                                while block:=reader.read(1024*1024):
                                    yield block
                            actual,size,risks=classify_chunks(chunks())
                        if actual!=digest or size!=expected_size:
                            raise ValueError("Archive object hash/size mismatch")
                        object_risks[digest]=risks
                        all_objects_seen.add(digest)
                        for flag in risks:
                            per_object_risks[flag]+=1
                            asset_count["unique_objects_with_"+flag]+=1
                        asset_count["verified_objects"]+=1
                        asset_count["verified_uncompressed_bytes"]+=size
                        if progress_file and (i%250==0 or i==len(objects)):
                            state={"asset":path.name,"verified_objects":i,
                                   "total_objects":len(objects),
                                   "elapsed_seconds":round(time.monotonic()-started,1)}
                            Path(progress_file).write_text(json.dumps(state),encoding="utf-8")
                        if i%1000==0:
                            print("AUDIT_PROGRESS",path.name,i,"/",len(objects),flush=True)
                    for entry in entries:
                        root=entry["root"]
                        rel=entry["path"]
                        path_risks,ext=classify_path(root,rel)
                        risks=path_risks|object_risks[entry["sha256"]]
                        identifier=sha(root+"\0"+rel)
                        root_id=sha(root)
                        writer.writerow([path.name,root_id,identifier,
                                         ext,entry["bytes"],";".join(sorted(risks))])
                        aggregate["manifest_paths"]+=1
                        asset_count["manifest_paths"]+=1
                        if risks & HIGH_RISK:
                            aggregate["paths_with_high_risk_flag"]+=1
                            asset_count["paths_with_high_risk_flag"]+=1
                        if not risks:
                            aggregate["paths_with_no_recognized_risk_flag"]+=1
                        for flag in risks:
                            risky_by_path[flag]+=1
                            asset_count["paths_with_"+flag]+=1
                        if root_id not in root_stats:
                            root_stats[root_id]={"paths":0,"high_risk_paths":0,
                                                  "content_signature_path_count":0}
                        rec=root_stats[root_id]
                        rec["paths"]+=1
                        rec["high_risk_paths"]+=bool(risks & HIGH_RISK)
                        rec["content_signature_path_count"]+=bool(risks & set(CONTENT_PATTERNS))
                per_asset.append({"archive_name":path.name,
                                  "totals":dict(sorted(asset_count.items()))})
                print("AUDIT_ASSET_COMPLETE",path.name,
                      asset_count["manifest_paths"],asset_count["verified_objects"],flush=True)
        report={
            "schema":SCHEMA,
            "distribution_status":"BLOCKED_EXTERNAL_DISTRIBUTION",
            "source_archives":[p.name for p in archives],
            "verified_unique_object_digests_across_assets":len(all_objects_seen),
            "aggregate":dict(sorted(aggregate.items())),
            "risk_flag_path_counts":dict(sorted(risky_by_path.items())),
            "risk_flag_unique_object_instance_counts":dict(sorted(per_object_risks.items())),
            "root_statistics_by_sha256":dict(sorted(root_stats.items())),
            "assets":per_asset,
            "limitations":[
                "Raw matched values and source filenames are NEVER included in outputs",
                "Content pattern scanning detects only enumerated signatures; negative result is not release clearance",
                "False positives possible for emails, paths and credential-looking assignments",
                "Opaque binary/ZIP internal compressed content is not exhaustively decoded",
                "Per-file rights and ownership are unverified; license approval remains required",
                "Paths are SHA256-hashed for minimization; these hashes are still private review metadata",
            ],
            "content_excerpts_stored":False,
            "original_archives_modified":False,
        }
        report_file.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        temp_index.replace(index_file)
        print("AUDIT_PASS",report_file.name,index_file.name,
              aggregate["manifest_paths"],len(all_objects_seen),flush=True)
        return report
    except BaseException:
        if temp_index.exists():
            temp_index.unlink()
        raise

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive",action="append",type=Path,required=True)
    ap.add_argument("--report",type=Path,required=True)
    ap.add_argument("--index",type=Path,required=True)
    ap.add_argument("--progress",type=Path)
    ns=ap.parse_args()
    result=scan_assets(ns.archive,ns.report,ns.index,ns.progress)
    print("RISKS",json.dumps(result["risk_flag_path_counts"],sort_keys=True),flush=True)

if __name__=="__main__":
    main()
