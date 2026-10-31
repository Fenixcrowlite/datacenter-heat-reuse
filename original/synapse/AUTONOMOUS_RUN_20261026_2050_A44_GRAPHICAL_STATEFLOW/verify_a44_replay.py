"""Read-only, idempotent replay check for A44 event 1243 and immutable evidence."""
import hashlib,json,sqlite3
from pathlib import Path
HERE=Path(__file__).resolve().parent
CENTER=HERE.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-a44-graphical-stateflow-20261026-2050"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
    manifest=json.loads((HERE/"SHA256_MANIFEST.json").read_text(encoding="utf8"))
    for name,expected in manifest.items():
        if sha(HERE/name)!=expected: raise RuntimeError("HASH_MISMATCH "+name)
    rec=json.loads((HERE/"REGISTRY_RESULT.json").read_text(encoding="utf8"))
    db=sqlite3.connect("file:"+str((CENTER/"tasks.sqlite3").as_posix())+"?mode=ro",uri=True)
    try:
        assert db.execute("pragma quick_check").fetchone()[0]=="ok"
        ev=db.execute("select id,data_json from task_events where task_id=? and actor=? and kind='evidence'",
                      (TASK,ACTOR)).fetchall()
        if len(ev)!=1: raise RuntimeError("NOT_EXACTLY_ONE_EVENT")
        if ev[0][0]!=rec["event_id"]: raise RuntimeError("EVENT_ID_CONFLICT")
        payload=json.loads(ev[0][1])
        for k,v in payload.items():
            if rec.get(k)!=v: raise RuntimeError("EVENT_PAYLOAD_MISMATCH "+k)
        if sha(HERE/"EVIDENCE.json")!=payload["evidence_sha256"]: raise RuntimeError("EVIDENCE_SHA")
        if sha(HERE/"SHA256_MANIFEST.json")!=payload["manifest_sha256"]: raise RuntimeError("MANIFEST_SHA")
        state=db.execute("select status,stage,worker_pid from tasks where id=?",(TASK,)).fetchone()
        if state!=("review","planned",None): raise RuntimeError("OWNERSHIP_CHANGED")
        return {"status":"EXISTING_EVENT_VERIFIED","event_id":ev[0][0],"files":len(manifest),
                "handoff_sha256":sha(HERE/"FINAL_HANDOFF.md")}
    finally: db.close()
if __name__=="__main__":
    print(json.dumps(verify()))
