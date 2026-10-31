"""Decode archived SLX/Office ZIP containers without exposing their contents.

Private supplementary stage of C130 risk inventory, working on the unique
objects whose logical source path ends with slx/docx/pptx/xlsx.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

from .source_risk_inventory import CONTENT_PATTERNS, ALLOWED_FORMAT

NESTED_TYPES={".slx",".pptx",".docx",".xlsx"}
MAX_NESTED_BYTES=32*1024*1024
MAX_MEMBER_BYTES=10*1024*1024
MAX_MEMBERS=5000
META=re.compile(rb"(?is)<(?:dc:creator|cp:lastModifiedBy)\b[^>]*>\s*[^<\s][^<]*<")
def scan_nested_bytes(data):
    findings=set()
    if len(data)>MAX_NESTED_BYTES:
        return {"nested_size_limit"}
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            infos=archive.infolist()
            if len(infos)>MAX_MEMBERS or sum(i.file_size for i in infos)>MAX_NESTED_BYTES*8:
                return {"nested_expansion_limit"}
            folded=set()
            for info in infos:
                path=info.filename
                segments=path.replace("\\","/").split("/")
                if path.startswith("/") or "\\" in path or any(seg in (".","..") for seg in segments):
                    findings.add("nested_unsafe_path")
                case=path.casefold()
                if case in folded:
                    findings.add("nested_case_alias")
                folded.add(case)
                if info.create_system==3 and ((info.external_attr>>16)&0o170000)==0o120000:
                    findings.add("nested_symlink")
                if info.file_size>MAX_MEMBER_BYTES:
                    findings.add("nested_oversize_member")
                    continue
                if info.is_dir():
                    continue
                with archive.open(info) as reader:
                    tail=b""
                    while chunk:=reader.read(1024*1024):
                        block=tail+chunk
                        for category,pattern in CONTENT_PATTERNS.items():
                            if pattern.search(block):
                                findings.add("nested_"+category)
                        if META.search(block):
                            findings.add("nested_creator_metadata")
                        tail=block[-512:]
    except (zipfile.BadZipFile,RuntimeError,NotImplementedError,OverflowError):
        findings.add("nested_unreadable")
    return findings

def audit(archives,output):
    output=Path(output)
    if output.exists():
        raise FileExistsError(output)
    summary=collections.Counter()
    per_archive=[]
    risk_objects=[]
    for path in archives:
        path=Path(path)
        with zipfile.ZipFile(path) as z:
            manifest=json.loads(z.read("manifest.json"))
            if manifest.get("format")!=ALLOWED_FORMAT or manifest.get("errors"):
                raise ValueError("Wrong source archive")
            selected=collections.defaultdict(list)
            for item in manifest["files"]:
                if Path(item["path"]).suffix.lower() in NESTED_TYPES:
                    selected[item["sha256"]].append(item)
            count=collections.Counter()
            for digest,entries in selected.items():
                body=z.read("objects/"+digest)
                if hashlib.sha256(body).hexdigest()!=digest:
                    raise ValueError("Corrupt compressed-model object")
                found=scan_nested_bytes(body)
                count["unique_nested_containers_verified"]+=1
                count["logical_paths_covered"]+=len(entries)
                count["nested_uncompressed_zip_bytes"]+=len(body)
                for flag in found:
                    count["unique_objects_"+flag]+=1
                    count["logical_paths_"+flag]+=len(entries)
                    summary[flag]+=len(entries)
                if found:
                    risk_objects.append({"archive":path.name,"object_sha256":digest,
                                         "logical_paths":len(entries),"findings":sorted(found)})
            per_archive.append({"asset":path.name,"counts":dict(sorted(count.items()))})
    report={"schema":"dchr-c130-nested-container-risk-v1",
            "distribution_status":"BLOCKED_EXTERNAL_DISTRIBUTION",
            "per_archive":per_archive,
            "nested_flag_logical_path_counts":dict(sorted(summary.items())),
            "flagged_object_records":risk_objects,
            "raw_names_or_matching_values_stored":False,
            "limitations":"Checks supported ZIP/SLX/Office members up to configured limits; encrypted/non-ZIP and malformed content require human review. Not a release approval."}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive",type=Path,action="append",required=True)
    p.add_argument("--report",type=Path,required=True)
    x=p.parse_args()
    report=audit(x.archive,x.report)
    for row in report["per_archive"]:
        print("SCANNED",row["asset"],row["counts"])
    print("FLAGGED_COUNTS",report["nested_flag_logical_path_counts"])

if __name__=="__main__":
    main()
