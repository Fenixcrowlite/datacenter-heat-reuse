"""Replay-safe read-only verification of the existing A28 registry event.

The one-shot register_a28.py wrote action=CREATED_EVENT to its local receipt,
so a second call incorrectly raised REGISTRY_RESULT_CONFLICT despite finding
the same event. Do not rewrite the historical receipt or event: compare their
stable fields instead. No database mutation occurs here.
"""
from __future__ import annotations
import hashlib
import json
import sqlite3
from pathlib import Path

HERE=Path(__file__).resolve().parent
CENTER=HERE.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-dchr-a28-field-calibration-gate-20261025-2346"


def check():
    receipt=json.loads((HERE/"REGISTRY_RESULT.json").read_text(encoding="utf8"))
    manifest=json.loads((HERE/"SHA256_MANIFEST.json").read_text(encoding="utf8"))
    for name,expected in manifest.items():
        actual=hashlib.sha256((HERE/name).read_bytes()).hexdigest()
        if actual!=expected: raise RuntimeError("MANIFEST_MISMATCH "+name)
    with sqlite3.connect("file:"+str(CENTER/"tasks.sqlite3")+"?mode=ro",uri=True) as db:
        if db.execute("PRAGMA quick_check").fetchone()[0]!="ok":
            raise RuntimeError("SQLITE_INTEGRITY")
        rows=db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",
                        (TASK,ACTOR)).fetchall()
        if len(rows)!=1: raise RuntimeError("EVENT_COUNT_NOT_ONE")
        event_id,payload=rows[0][0],json.loads(rows[0][1])
    if receipt["event_id"]!=event_id or receipt["task_id"]!=TASK:
        raise RuntimeError("RECEIPT_ID_CONFLICT")
    if receipt["action"]!="CREATED_EVENT":
        raise RuntimeError("UNEXPECTED_HISTORIC_RECEIPT")
    for key,value in payload.items():
        if receipt.get(key)!=value:
            raise RuntimeError("EVENT_PAYLOAD_CONFLICT "+key)
    if payload["manifest_sha256"]!=hashlib.sha256((HERE/"SHA256_MANIFEST.json").read_bytes()).hexdigest():
        raise RuntimeError("MANIFEST_SHA_CONFLICT")
    return {"status":"PASS","event_id":event_id,"action":"EXISTING_EVENT",
            "event_count":1,"manifest_files_verified":len(manifest),
            "one_shot_replay_defect":"original register_a28.py receipt action differs on replay; no DB duplicate",
            "database_modified":False}


if __name__=="__main__":
    result=check()
    p=HERE/"REPLAY_VERIFY.json"
    if p.exists():
        if json.loads(p.read_text(encoding="utf8"))!=result:
            raise RuntimeError("REPLAY_RESULT_CONFLICT")
    else:
        p.write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    print("REPLAY_SAFE_PASS",result["event_id"],result["manifest_files_verified"])
