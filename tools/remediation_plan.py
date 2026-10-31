"""LOCAL-ONLY C130 remediation queue from a hashed-path risk inventory.

No safe/approved category is ever produced; this is only an order for
authorized review before ANY external redistribution decision.
"""
from __future__ import annotations
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path
import re

FORM="dchr-c130-private-remediation-v1"
P0={"token_signature","private_key_marker","credential_assignment",
    "browser_state","browser_profile","credential_filename"}
P1={"user_home_path","email_like","possible_personal_data"}
P3={"opaque_or_binary_content_review","third_party_rights_review"}
P4={"source_provenance_review"}
NESTED_EXT={".slx",".docx",".pptx",".xlsx"}
ALLOWED=P0|P1|P3|P4
HASH=re.compile(r"[0-9a-f]{64}")

def disposition(flags,suffix):
    if flags&P0:
        return "P0_QUARANTINE_CANDIDATE"
    if flags&P1:
        return "P1_IDENTITY_REVIEW"
    if suffix in NESTED_EXT:
        return "P2_NESTED_METADATA_REVIEW"
    if flags&P3:
        return "P3_OPAQUE_OR_RIGHTS_REVIEW"
    if flags&P4:
        return "P4_SOURCE_PROVENANCE_REVIEW"
    return "P5_UNREVIEWED_NO_CLEARANCE"

def write_plan(index,output,summary):
    index,output,summary=map(Path,(index,output,summary))
    if output.exists() or summary.exists():
        raise FileExistsError("Never overwrite private review queues")
    if output.parent!=summary.parent:
        raise ValueError("Use same review destination for linked artifacts")
    if not output.parent.is_dir():
        raise FileNotFoundError(output.parent)
    pending=output.with_suffix(output.suffix+".partial")
    if pending.exists():
        raise FileExistsError(pending)
    counts=collections.Counter()
    digest=hashlib.sha256()
    with index.open("rb") as source:
        for chunk in iter(lambda: source.read(1024*1024), b""):
            digest.update(chunk)
    seen=set()
    try:
        with index.open(encoding="utf-8",newline="") as source, pending.open("w",encoding="utf-8",newline="") as target:
            reader=csv.DictReader(source)
            required={"archive_name","root_id_sha256","path_id_sha256","suffix","declared_bytes","risk_flags"}
            if set(reader.fieldnames or [])!=required:
                raise ValueError("Unexpected risk inventory schema")
            out=csv.writer(target)
            out.writerow(["archive_name","root_id_sha256","path_id_sha256",
                          "disposition","risk_categories"])
            for record in reader:
                root_id=record["root_id_sha256"]
                path_id=record["path_id_sha256"]
                if not HASH.fullmatch(root_id) or not HASH.fullmatch(path_id):
                    raise ValueError("Unredacted or invalid hash")
                key=(record["archive_name"],path_id)
                if key in seen:
                    raise ValueError("Duplicate source path")
                seen.add(key)
                flags={s for s in record["risk_flags"].split(";") if s}
                if not flags<=ALLOWED:
                    raise ValueError("Unknown risk flag; fail closed")
                result=disposition(flags,record["suffix"].lower())
                counts[result]+=1
                out.writerow([record["archive_name"],root_id,path_id,result,
                              ";".join(sorted(flags))])
        pending.replace(output)
    except BaseException:
        if pending.exists():
            pending.unlink()
        raise
    result={
        "schema":FORM,
        "distribution_status":"BLOCKED_EXTERNAL_DISTRIBUTION",
        "input_index_sha256":digest.hexdigest(),
        "classified_paths":sum(counts.values()),
        "disposition_counts":dict(sorted(counts.items())),
        "automatically_approved_for_external_release":0,
        "limitations":"Every category remains blocked for external sharing; manually verify ownership/privacy, binary containers and third-party licenses",
        "raw_paths_or_secret_values_written":False,
    }
    try:
        summary.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    except BaseException:
        if output.exists():
            output.unlink()
        raise
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--index",type=Path,required=True)
    ap.add_argument("--queue",type=Path,required=True)
    ap.add_argument("--report",type=Path,required=True)
    x=ap.parse_args()
    print(json.dumps(write_plan(x.index,x.queue,x.report),indent=2))

if __name__=="__main__":
    main()
