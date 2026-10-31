"""Independent final evidence, registry and SHA verification for A24/A24B."""
import hashlib,json,sqlite3
from pathlib import Path

HERE=Path(__file__).resolve().parent
B=HERE.parent/"AUTONOMOUS_RUN_20261025_1952_A24B"
CENTER=HERE.parent.parent

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):h.update(chunk)
    return h.hexdigest()

def verify_folder(folder, expected_tests):
    manifest=json.loads((folder/"SHA256_MANIFEST.json").read_text(encoding="utf-8"))
    for n,expected in manifest.items():
        if sha(folder/n)!=expected:raise RuntimeError("SHA_FAIL "+str(folder/n))
    log=(folder/"TEST_LOG.txt").read_text(encoding="utf-8-sig")
    if f"Ran {expected_tests} tests" not in log or not log.rstrip().endswith("OK"):
        raise RuntimeError("QA_FAIL "+str(folder))
    return len(manifest)

def main():
    checked=verify_folder(HERE,25)+verify_folder(B,15)
    ids=(1152,1153)
    with sqlite3.connect(f"file:{(CENTER/'tasks.sqlite3').as_posix()}?mode=ro",uri=True) as db:
        if db.execute("PRAGMA quick_check").fetchone()[0]!="ok":raise RuntimeError("SQLITE_FAIL")
        rows=db.execute("SELECT id,task_id,actor,data_json FROM task_events WHERE id in (?,?)",ids).fetchall()
        if len(rows)!=2:raise RuntimeError("EVENT_MISSING")
        expected={
          1152:("scc-3d9d172beb6e1b","chatgpt-dchr-a24-static-lineage-20261025-1952",HERE/"DCHR_LINEAGE_EVIDENCE.json"),
          1153:("scc-d941595119d699","chatgpt-council-a24b-acoustic-activity-20261025-1952",B/"COUNCIL_ACOUSTIC_ACTIVITY.json")}
        for event,task,actor,payload in rows:
            tid,who,path=expected[event]
            if (task,actor)!=(tid,who) or json.loads(payload)["evidence_sha256"]!=sha(path):
                raise RuntimeError("EVENT_COLLISION "+str(event))
            if db.execute("SELECT count(*) FROM task_events WHERE task_id=? AND actor=? AND kind='evidence'",(tid,who)).fetchone()[0]!=1:
                raise RuntimeError("EVENT_DUPLICATE "+str(event))
        states=dict((r[0],(r[1],r[2])) for r in db.execute("SELECT id,status,stage FROM tasks WHERE id in (?,?)",
                    ("scc-3d9d172beb6e1b","scc-d941595119d699")))
        if states!={"scc-3d9d172beb6e1b":("review","planned"),"scc-d941595119d699":("queued","planned")}:
            raise RuntimeError("TASK_STATE_CHANGED")
    report={"status":"PASS","manifest_files_checked":checked,"tests_passed":40,
            "event_ids":list(ids),"event_count_unique":2,
            "task_states":states,"handoff_sha256":sha(HERE/"HANDOFF.md"),
            "lineage_evidence_sha256":sha(HERE/"DCHR_LINEAGE_EVIDENCE.json"),
            "acoustic_evidence_sha256":sha(B/"COUNCIL_ACOUSTIC_ACTIVITY.json")}
    (HERE/"FINAL_VERIFY.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))
if __name__=="__main__":main()
