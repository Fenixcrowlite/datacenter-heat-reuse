"""Safe idempotent A43 registry entry point, preserving event 1238 and its manifest.

Original register_a43.py successfully created event but had a non-idempotent
handoff template on replay. This wrapper checks existing evidence read-only
and delegates only when the event does not yet exist.
"""
from __future__ import annotations
import hashlib
import json
import sqlite3
from pathlib import Path

HERE=Path(__file__).resolve().parent
CENTER=HERE.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-a43-finite-trip-20261026-1945"

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def replay():
    for root in (CENTER,CENTER/"recovery",HERE):
        for flag in ("STOP","STOP.flag","PAUSE","PAUSE.flag",".STOP",".PAUSE"):
            if (root/flag).exists():
                raise RuntimeError("STOP_ACTIVE")
    db=sqlite3.connect(f"file:{(CENTER/'tasks.sqlite3').as_posix()}?mode=ro",uri=True)
    try:
        if db.execute("pragma quick_check").fetchone()[0]!="ok":
            raise RuntimeError("SQLITE_CORRUPT")
        events=db.execute("select id,data_json from task_events where task_id=? and actor=? and kind='evidence'",(TASK,ACTOR)).fetchall()
        if len(events)>1:
            raise RuntimeError("DUPLICATE_EVENTS")
        if not events:
            import register_a43
            register_a43.main()
            return "CREATED_EVENT"
        event_id,payload=events[0]
        p=json.loads(payload)
        receipt=json.loads((HERE/"REGISTRY_RESULT.json").read_text(encoding="utf8"))
        if receipt["event_id"]!=event_id or receipt["task_id"]!=TASK:
            raise RuntimeError("RECEIPT_ID_MISMATCH")
        for k,v in p.items():
            if receipt.get(k)!=v:
                raise RuntimeError("RECEIPT_PAYLOAD_MISMATCH "+k)
        if sha(HERE/"EVIDENCE.json")!=p["evidence_sha256"]:
            raise RuntimeError("EVIDENCE_CHANGED")
        if sha(HERE/"SHA256_MANIFEST.json")!=p["manifest_sha256"]:
            raise RuntimeError("MANIFEST_CHANGED")
        manifest=json.loads((HERE/"SHA256_MANIFEST.json").read_text(encoding="utf8"))
        for f,digest in manifest.items():
            if sha(HERE/f)!=digest:
                raise RuntimeError("FILE_CHANGED "+f)
        task=db.execute("select status,stage,worker_pid from tasks where id=?",(TASK,)).fetchone()
        if task!=("review","planned",None):
            raise RuntimeError("TASK_OWNERSHIP_CHANGED")
        return f"EXISTING_EVENT_VERIFIED {event_id} files={len(manifest)}"
    finally:
        db.close()

if __name__=="__main__":
    print(replay())
