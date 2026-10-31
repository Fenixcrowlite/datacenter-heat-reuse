"""Read-only, repeatable post-registration verification. Does NOT rerun v1 finalize."""
import hashlib
import json
import sqlite3
from pathlib import Path

H=Path(__file__).resolve().parent
ROOT=H.parent.parent
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-seasonal-mismatch-20261028-1150"

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def verify():
    manifest=json.loads((H/"SHA256_MANIFEST.json").read_text(encoding="utf-8"))
    assert len(manifest["files"])==manifest["count"]==10
    for file,expected in manifest["files"].items():
        assert sha(H/file)==expected,("MANIFEST_HASH_CHANGED",file)
    evidence=json.loads((H/"EVIDENCE.json").read_text(encoding="utf-8"))
    result=json.loads((H/"REGISTRY_RESULT.json").read_text(encoding="utf-8"))
    assert result["evidence_sha256"]==sha(H/"EVIDENCE.json")
    assert result["manifest_sha256"]==sha(H/"SHA256_MANIFEST.json")
    assert result["handoff_sha256"]==sha(H/"FINAL_HANDOFF.md")
    assert evidence["source_csv_sha256"]==json.loads((H/"SEASONAL_MISMATCH.json").read_text(encoding="utf-8"))["source_sha256"]
    with sqlite3.connect(ROOT/"tasks.sqlite3",timeout=10) as db:
        assert db.execute("pragma integrity_check").fetchone()[0]=="ok"
        task=db.execute("select project,status,worker_pid from tasks where id=?",(TASK,)).fetchone()
        assert task and task[0]=="DataCenter Heat Reuse" and task[2] is None
        events=db.execute("select id,data_json from task_events where task_id=? and actor=? and kind='evidence'",(TASK,ACTOR)).fetchall()
        assert len(events)==1
        event_id,payload=events[0]
        assert event_id==result["event_id"]==1384
        payload=json.loads(payload)
        assert payload["evidence_sha256"]==result["evidence_sha256"]
        assert payload["manifest_sha256"]==result["manifest_sha256"]
        assert payload["primary_source_signoffs"]==0
        assert payload["real_gas_savings_claimed"] is False
    return {"status":"PASS","files_sha256_verified":10,
            "event_id":event_id,"event_duplicates":0,
            "sqlite_integrity":"ok","source_class":"SIMULATED_NOT_METERED",
            "read_only":True}

if __name__=="__main__":
    print(json.dumps(verify(),sort_keys=True))
