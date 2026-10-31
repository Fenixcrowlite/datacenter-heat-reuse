"""Independent, read-only A42 final QA. Does not alter registry or source."""
from __future__ import annotations
import hashlib,json,sqlite3
from pathlib import Path
HERE=Path(__file__).resolve().parent
DB=HERE.parent.parent/"tasks.sqlite3"
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-a42-coupled-failsafe-20261026-1850"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    manifest=json.loads((HERE/"SHA256_MANIFEST.json").read_text(encoding="utf8"))
    errors=[name for name,digest in manifest.items() if not (HERE/name).is_file() or sha(HERE/name)!=digest]
    assert not errors,("SHA_MISMATCH",errors)
    with sqlite3.connect(f"file:{DB.as_posix()}?mode=ro",uri=True) as db:
        assert db.execute("pragma quick_check").fetchone()[0]=="ok"
        events=db.execute("select id,data_json from task_events where task_id=? and actor=? and kind='evidence'",
            (TASK,ACTOR)).fetchall()
        assert len(events)==1,("EVENT_COUNT",len(events))
        eid,payload=events[0][0],json.loads(events[0][1])
        assert payload["manifest_sha256"]==sha(HERE/"SHA256_MANIFEST.json")
        assert payload["evidence_sha256"]==sha(HERE/"EVIDENCE.json")
        assert payload["physical_release_allowed"] is False
        state=db.execute("select status,stage,worker_pid from tasks where id=?",(TASK,)).fetchone()
        assert state==("review","planned",None),("TASK_STATE",state)
    audit=json.loads((HERE/"MATLAB_AUDIT_A42.json").read_text(encoding="utf8"))
    assert audit["status"]=="MATLAB_INDEPENDENT_NUMERIC_AUDIT_PASS"
    assert audit["samples"]==4704
    assert all(c["acceptance"]=="PASS" for c in audit["cases"].values())
    assert "Ran 14 tests" in (HERE/"QA_CLEAN_STDERR.txt").read_text(encoding="utf8")
    result=dict(status="FINAL_VERIFY_PASS",sha256_files=len(manifest),
        event_id=eid,event_count=len(events),sqlite="ok",
        task_status="review/planned",matlab_rows=4704,python_tests=14,
        handoff_sha256=sha(HERE/"FINAL_HANDOFF.md"))
    print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
