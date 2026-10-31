"""Read-only, repeatable artifact + registry verification."""
import hashlib,json,sqlite3
from pathlib import Path
H=Path(__file__).parent
ROOT=H.parent.parent
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-constrained-storage-20261028-1252"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify():
    manifest=json.loads((H/"SHA256_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["count"]==len(manifest["files"])
    for f,digest in manifest["files"].items():
        assert sha(H/f)==digest,("SHA_MISMATCH",f)
    evidence=json.loads((H/"EVIDENCE.json").read_text(encoding="utf-8"))
    assert evidence["manifest_sha256"]==sha(H/"SHA256_MANIFEST.json")
    assert evidence["source_csv_sha256"]=="8125719923bae97901f37cf0f5354df77b46544df0477f863172255748873f25"
    assert evidence["primary_source_signoffs"]==0
    assert evidence["production_modified"] is False
    with sqlite3.connect(ROOT/"tasks.sqlite3",timeout=10) as db:
        assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
        task=db.execute("SELECT project,status,worker_pid FROM tasks WHERE id=?",(TASK,)).fetchone()
        assert task and task[0]=="DataCenter Heat Reuse"
        rows=db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND actor=? AND kind='evidence'",
                        (TASK,ACTOR)).fetchall()
        assert len(rows)==1,("EVENT_COUNT",len(rows))
        event_id,payload=rows[0]
        data=json.loads(payload)
        assert data["evidence_sha256"]==sha(H/"EVIDENCE.json")
        assert data["manifest_sha256"]==sha(H/"SHA256_MANIFEST.json")
        assert data["artifact_directory"]==str(H)
    handoff=(H/"FINAL_HANDOFF.md").read_text(encoding="utf-8")
    assert f"event #{event_id}" in handoff
    return {"status":"PASS","manifest_files":manifest["count"],"event_id":event_id,
            "task":TASK,"task_status":task[1],"event_count":1,
            "evidence_sha256":sha(H/"EVIDENCE.json"),"handoff_sha256":sha(H/"FINAL_HANDOFF.md")}
if __name__=="__main__":print(json.dumps(verify(),ensure_ascii=False))
