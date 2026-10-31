"""Idempotent existing-card evidence for source-backed synthetic N-1 envelope."""
from pathlib import Path
import hashlib,json,sqlite3,time
HERE=Path(__file__).resolve().parent
CENTER=HERE.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-a36b-dchr-reject-n1-20261026"
FILES=("reject_envelope.py","test_envelope.py","register_a36b.py",
       "RESULTS_N1.json","N1_ENVELOPE.csv","QA_TEST_LOG.txt","DCHR_REJECT_N1_RU.md")
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save_once(p,x):
    if p.exists():
        if json.loads(p.read_text(encoding="utf8"))!=x:
            raise RuntimeError("ARTIFACT_CONFLICT "+str(p))
    else:
        p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def main():
    for folder in (CENTER,CENTER/"recovery",HERE,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
        for name in ("STOP","STOP.flag","STOP.txt",".STOP","PAUSE","PAUSE.flag",".PAUSE","STOP_MANAGED_WORKERS.txt"):
            if (folder/name).exists():
                raise RuntimeError("STOP_ACTIVE "+str(folder/name))
    result=json.loads((HERE/"RESULTS_N1.json").read_text(encoding="utf8"))
    log=(HERE/"QA_TEST_LOG.txt").read_text(encoding="utf8")
    if "Ran 10 tests" not in log or "\nOK" not in log:
        raise RuntimeError("TESTS_NOT_PASS")
    if result["physical_release_allowed"] or len(result["scenarios"])!=6:
        raise RuntimeError("INVALID_RESULT")
    source=Path(result["source_v07"])
    if sha(source)!=result["source_v07_sha256"]:
        raise RuntimeError("SOURCE_CHANGED")
    both=result["scenarios"]["both_off"]
    if [both[k]["unsafe_intervals"] for k in ("both_available","main_only","backup_only","neither_available")]!=[0,171,358,576]:
        raise RuntimeError("UNEXPECTED_NUMBERS")
    evidence={
        "scope":"isolated_DCHR_A36B_v07_synthetic_reject_N1_capacity_envelope",
        "source_v07_sha256":result["source_v07_sha256"],
        "qa":"10/10 unit PASS; 24 scenario combinations (6 load scenarios x 4 reject availability)",
        "key_finding":"v07 explicitly defines scenario REJECT A=180kW, B=150kW; both OFF needs max 213.6295kW. N-1 main-only 171 unsafe intervals, backup-only 358 unsafe intervals; A+B 0.",
        "decision":"N1_SYNTHETIC_RISK_VERIFIED_PHYSICAL_RELEASE_BLOCKED",
        "limits":"scenario capacities not equipment certificates; IT-shedding, TES dynamics and thermal transients not recalculated",
        "next_step":"Model owner: integrate A/B reject availability, thermal limits, TES SOC and IT-shedding into owned Simulink/Stateflow; verify N-1 safety; obtain real rated capacities",
        "physical_release_allowed":False,
    }
    save_once(HERE/"EVIDENCE.json",evidence)
    for f in FILES:
        if not (HERE/f).is_file():
            raise RuntimeError("MISSING "+f)
    manifest={f:sha(HERE/f) for f in (*FILES,"EVIDENCE.json")}
    save_once(HERE/"SHA256_MANIFEST.json",manifest)
    payload={
        "scope":evidence["scope"],"artifact_directory":str(HERE),
        "evidence_sha256":sha(HERE/"EVIDENCE.json"),
        "manifest_sha256":sha(HERE/"SHA256_MANIFEST.json"),
        "qa":evidence["qa"],"key_finding":evidence["key_finding"],
        "decision":evidence["decision"],"limits":evidence["limits"],
        "next_step":evidence["next_step"],
    }
    with sqlite3.connect(CENTER/"tasks.sqlite3",timeout=6,isolation_level=None) as db:
        db.execute("pragma busy_timeout=6000")
        if db.execute("pragma quick_check").fetchone()[0]!="ok":
            raise RuntimeError("SQLITE")
        db.execute("begin immediate")
        try:
            state=db.execute("select status,stage,worker_pid,owner from tasks where id=?",(TASK,)).fetchone()
            if state!=("review","planned",None,"MATLAB/Stateflow QA"):
                raise RuntimeError("OWNERSHIP_CHANGED "+repr(state))
            found=db.execute("select id,data_json from task_events where task_id=? and actor=? and kind='evidence'",(TASK,ACTOR)).fetchall()
            if len(found)>1:
                raise RuntimeError("DUPLICATE_EVENT")
            if found:
                if json.loads(found[0][1])!=payload:
                    raise RuntimeError("EVENT_CONFLICT")
                event_id,action=found[0][0],"EXISTING_EVENT"
            else:
                event_id=db.execute("insert into task_events(task_id,at,kind,actor,data_json) values(?,?,?,?,?)",
                    (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,ensure_ascii=False))).lastrowid
                action="CREATED_EVENT"
            db.commit()
        except BaseException:
            db.rollback()
            raise
    save_once(HERE/"REGISTRY_RESULT.json",{"task_id":TASK,"event_id":event_id,**payload})
    print(json.dumps({"event_id":event_id,"action":action,
                      "evidence_sha256":payload["evidence_sha256"],
                      "manifest_sha256":payload["manifest_sha256"]},ensure_ascii=False))
if __name__=="__main__":
    main()
