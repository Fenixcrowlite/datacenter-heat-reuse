"""Idempotent evidence event in EXISTING DataCenter Synapse card."""
from pathlib import Path
import hashlib, json, sqlite3, time

HERE=Path(__file__).resolve().parent
CENTER=HERE.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-a36-dchr-redispatch-20261026"
ROOTS=(CENTER,CENTER/"recovery",HERE,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse"))
FLAGS=("STOP","STOP.flag","STOP.txt",".STOP","PAUSE","PAUSE.flag",".PAUSE","STOP_MANAGED_WORKERS.txt")
FILES=[
    "redispatch.py","test_redispatch.py","run_v08.py","independent_check.py",
    "verify_a36.py","register_a36.py","RESULTS.json","INDEPENDENT_QA.json",
    "QA_RESULT.json","DCHR_REDISPATCH_A36_RU.md",
    "scenario_baseline.csv","scenario_pool_off.csv","scenario_dh_off.csv",
    "scenario_both_off.csv","scenario_pool40_dh25.csv",
    "scenario_both_off_assumed_reject150.csv",
]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save_once(p,obj):
    if p.exists():
        if json.loads(p.read_text(encoding="utf8"))!=obj:
            raise RuntimeError("EXISTING_ARTIFACT_CONFLICT "+str(p))
    else:
        p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf8")

def main():
    for root in ROOTS:
        for f in FLAGS:
            if (root/f).exists():
                raise RuntimeError("STOP_ACTIVE "+str(root/f))
    qa=json.loads((HERE/"QA_RESULT.json").read_text(encoding="utf8"))
    results=json.loads((HERE/"RESULTS.json").read_text(encoding="utf8"))
    if qa["status"]!="PASS" or qa["unit_tests_passed"]!=17 or qa["independent_checks_passed"]!=20833:
        raise RuntimeError("QA_NOT_PASS")
    if results["physical_release_allowed"] or len(results["scenarios"])!=6:
        raise RuntimeError("INVALID_RESULTS")
    if sha(Path(results["source_path"]))!=results["source_sha256"]:
        raise RuntimeError("SOURCE_CHANGED")
    for name in FILES:
        if not (HERE/name).is_file():
            raise RuntimeError("MISSING "+name)
    evidence={
        "scope":"isolated_DCHR_A36_conservative_instantaneous_redispatch",
        "input":"sim_v08_zdravy_SK.csv (synthetic), 672 x 15min",
        "source_sha256":results["source_sha256"],
        "qa":"17/17 unit PASS; 20833 independent CSV checks PASS across 4032 intervals",
        "key_finding":"both branches OFF at hour 24: required REJECT max 213.6295 kW; illustrative assumed 150 kW reject limit produces 358 unsafe intervals and 2543.427491 kWh unhandled",
        "limitations":"not TES/Stateflow dynamic, reject rating unverified, HP COP proxy, no real field data",
        "decision":"ISOLATED_REFERENCE_VERIFIED_PHYSICAL_RELEASE_BLOCKED",
        "next_step":"Model owner to integrate energy-balanced redispatch with TES SOC, reject hardware limits, HP part-load curves and IT safety in owned Simulink/Stateflow copy; validate against 672 reference samples",
        "physical_release_allowed":False,
    }
    save_once(HERE/"EVIDENCE.json",evidence)
    manifest={name:sha(HERE/name) for name in FILES+["EVIDENCE.json"]}
    save_once(HERE/"SHA256_MANIFEST.json",manifest)
    payload={
        "scope":evidence["scope"],"artifact_directory":str(HERE),
        "evidence_sha256":sha(HERE/"EVIDENCE.json"),
        "manifest_sha256":sha(HERE/"SHA256_MANIFEST.json"),
        "qa":evidence["qa"],"decision":evidence["decision"],
        "key_finding":evidence["key_finding"],
        "limitations":evidence["limitations"],"next_step":evidence["next_step"],
    }
    with sqlite3.connect(CENTER/"tasks.sqlite3",timeout=6,isolation_level=None) as db:
        db.execute("pragma busy_timeout=6000")
        if db.execute("pragma quick_check").fetchone()[0]!="ok":
            raise RuntimeError("SQLITE_NOT_OK")
        db.execute("begin immediate")
        try:
            state=db.execute("select status,stage,worker_pid,owner from tasks where id=?",(TASK,)).fetchone()
            if state!=("review","planned",None,"MATLAB/Stateflow QA"):
                raise RuntimeError("OWNERSHIP_CHANGED "+repr(state))
            existing=db.execute("select id,data_json from task_events where task_id=? and actor=? and kind='evidence'",(TASK,ACTOR)).fetchall()
            if len(existing)>1:
                raise RuntimeError("DUPLICATE_EVENT")
            if existing:
                if json.loads(existing[0][1])!=payload:
                    raise RuntimeError("EVENT_CONFLICT")
                event_id,action=existing[0][0],"EXISTING_EVENT"
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
