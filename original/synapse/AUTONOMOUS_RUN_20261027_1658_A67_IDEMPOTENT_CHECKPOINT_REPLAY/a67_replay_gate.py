"""Read-only, fail-closed replay gate for previously registered Synapse evidence."""
from pathlib import Path
import hashlib,json,sqlite3
from contextlib import closing
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def audit(directory, registry, task_id, actor, prefix):
    d=Path(directory)
    if not d.is_dir():raise ValueError("MISSING_ARTIFACT_DIR")
    manifest_path=d/f"SHA256_MANIFEST_{prefix}.json"
    evidence_path=d/f"EVIDENCE_{prefix}.json"
    handoff_path=d/"FINAL_HANDOFF.md"
    if not all(p.is_file() for p in (manifest_path,evidence_path,handoff_path)):
        raise ValueError("MISSING_EVIDENCE")
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest,dict) or not manifest:
        raise ValueError("EMPTY_MANIFEST")
    verified=0
    for rel,expected in manifest.items():
        if (not isinstance(rel,str) or Path(rel).is_absolute()
            or ".." in Path(rel).parts or not isinstance(expected,str) or len(expected)!=64):
            raise ValueError("UNSAFE_MANIFEST")
        f=(d/rel).resolve()
        if not f.is_relative_to(d.resolve()) or not f.is_file() or sha(f)!=expected:
            raise ValueError("HASH_MISMATCH:"+rel)
        verified+=1
    evidence=json.loads(evidence_path.read_text(encoding="utf-8"))
    if evidence.get("task_id")!=task_id or evidence.get("physical_release") is not False:
        raise ValueError("EVIDENCE_PROVENANCE")
    with closing(sqlite3.connect(f"file:{Path(registry).resolve().as_posix()}?mode=ro",uri=True)) as db:
        rows=db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND actor=? AND kind='evidence'",(task_id,actor)).fetchall()
        if len(rows)!=1:raise ValueError("EVENT_COUNT:"+str(len(rows)))
        event_id,payload=rows[0]
        data=json.loads(payload)
        if (data.get("evidence_sha256")!=sha(evidence_path)
            or data.get("manifest_sha256")!=sha(manifest_path)
            or data.get("handoff_sha256")!=sha(handoff_path)
            or data.get("task_id",task_id)!=task_id
            or data.get("physical_release") is not False):
            raise ValueError("EVENT_HASH_MISMATCH")
    return {"status":"ALREADY_RECORDED","event_id":event_id,"verified_files":verified,
            "evidence_sha256":sha(evidence_path),"manifest_sha256":sha(manifest_path),
            "handoff_sha256":sha(handoff_path),"mutations":0}
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("directory",type=Path)
    p.add_argument("registry",type=Path)
    p.add_argument("task_id")
    p.add_argument("actor")
    p.add_argument("prefix")
    a=p.parse_args()
    print(json.dumps(audit(a.directory,a.registry,a.task_id,a.actor,a.prefix),sort_keys=True))
