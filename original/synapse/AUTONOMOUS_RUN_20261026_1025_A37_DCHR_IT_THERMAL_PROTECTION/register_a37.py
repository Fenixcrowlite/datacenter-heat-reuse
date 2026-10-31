"""Idempotent evidence registration into EXISTING DCHR task, no new worker."""
from pathlib import Path
import hashlib,json,sqlite3,time
HERE=Path(__file__).resolve().parent
CENTER=HERE.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-a37-dchr-it-thermal-n1-20261026"
V07=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\matlab\pool_redundancy_v07\fyzikalne_ochrany_v07.txt")
V08=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\pool_measurement_v08\sim_v08_zdravy_SK.csv")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save_once(path,obj):
    if path.exists():
        if json.loads(path.read_text(encoding="utf8"))!=obj:
            raise RuntimeError("ARTIFACT_CONFLICT "+str(path))
    else:
        path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def main():
    for folder in [CENTER,CENTER/"recovery",HERE,V07.parent.parent.parent]:
        for name in ["STOP","STOP.flag","STOP.txt",".STOP",".stop","PAUSE","PAUSE.flag","PAUSE.txt",".PAUSE",".pause","STOP_MANAGED_WORKERS.txt"]:
            if (folder/name).exists():
                raise RuntimeError("STOP_ACTIVE "+str(folder/name))
    result=json.loads((HERE/"RESULTS_A37.json").read_text(encoding="utf8"))
    qa=json.loads((HERE/"INDEPENDENT_QA.json").read_text(encoding="utf8"))
    log=(HERE/"TEST_LOG.txt").read_text(encoding="utf8")
    if result["physical_release_allowed"] or qa["status"]!="PASS" or qa["rows"]!=8064 or qa["decimal_invariant_checks"]!=104832:
        raise RuntimeError("QA_NOT_ACCEPTED")
    if "Ran 16 tests" not in log or "OK" not in log:
        raise RuntimeError("UNIT_TESTS_NOT_ACCEPTED")
    if len(result["cases"])!=12 or sha(V07)!=result["source_v07_sha256"] or sha(V08)!=result["source_v08_sha256"]:
        raise RuntimeError("PROVENANCE_CHANGED")
    for item in result["cases"].values():
        if sha(HERE/item["trace"])!=item["trace_sha256"]:
            raise RuntimeError("TRACE_CHANGED")
    evidence={
        "scope":"isolated_DCHR_A37_v07_N1_IT_thermal_inertia_sensitivity",
        "qa":"16/16 unit PASS; 8064 trace rows, 104832 independent Decimal checks PASS; 4 A36B energy crosschecks",
        "source_v07_sha256":result["source_v07_sha256"],
        "source_v08_sha256":result["source_v08_sha256"],
        "key_finding":"v07 thermal law: backup-only no-shed max 61.46C; hypothetical 40% IT shedding with 15kW/step ramp-up max 33.17C; neither reject available still max 93.86C, all 576 post-fault intervals alarm.",
        "decision":"N1_THERMAL_RISK_SYNTHETIC_VERIFIED_PHYSICAL_RELEASE_BLOCKED",
        "limits":"synthetic capacities and curtailment assumptions, no actual IT service model, TES/HP feedback, equipment safety, or real hardware control",
        "next_step":"Owner to integrate thermal law, real shedding response, TES SOC and REJECT A/B faults into isolated MATLAB/Stateflow; obtain equipment ratings and field validation.",
        "physical_release_allowed":False,
    }
    save_once(HERE/"EVIDENCE.json",evidence)
    files=["thermal_n1.py","run_a37.py","test_a37.py","independent_qa.py",
           "TEST_LOG.txt","RUN_LOG.json","INDEPENDENT_QA_LOG.txt",
           "RESULTS_A37.json","INDEPENDENT_QA.json","DCHR_A37_THERMAL_RU.md",
           "HANDOFF.md","EVIDENCE.json","register_a37.py"]
    files+=sorted(x["trace"] for x in result["cases"].values())
    manifest={f:sha(HERE/f) for f in files}
    save_once(HERE/"SHA256_MANIFEST.json",manifest)
    payload={"scope":evidence["scope"],"artifact_directory":str(HERE),
             "evidence_sha256":sha(HERE/"EVIDENCE.json"),
             "manifest_sha256":sha(HERE/"SHA256_MANIFEST.json"),
             "qa":evidence["qa"],"key_finding":evidence["key_finding"],
             "decision":evidence["decision"],"limits":evidence["limits"],
             "next_step":evidence["next_step"]}
    with sqlite3.connect(CENTER/"tasks.sqlite3",timeout=6,isolation_level=None) as db:
        db.execute("pragma busy_timeout=6000")
        if db.execute("pragma quick_check").fetchone()[0]!="ok":
            raise RuntimeError("SQLITE_INTEGRITY")
        db.execute("begin immediate")
        try:
            state=db.execute("select status,stage,worker_pid,owner from tasks where id=?",(TASK,)).fetchone()
            if state!=("review","planned",None,"MATLAB/Stateflow QA"):
                raise RuntimeError("OWNERSHIP_CHANGED "+repr(state))
            matches=db.execute("select id,data_json from task_events where task_id=? and actor=? and kind='evidence'",(TASK,ACTOR)).fetchall()
            if len(matches)>1:
                raise RuntimeError("DUPLICATE_EVENTS")
            if matches:
                if json.loads(matches[0][1])!=payload:
                    raise RuntimeError("EVENT_CONFLICT")
                event_id,action=matches[0][0],"EXISTING_EVENT"
            else:
                event_id=db.execute("insert into task_events(task_id,at,kind,actor,data_json) values(?,?,?,?,?)",
                    (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,ensure_ascii=False))).lastrowid
                action="CREATED_EVENT"
            db.commit()
        except BaseException:
            db.rollback();raise
    save_once(HERE/"REGISTRY_RESULT.json",{"task_id":TASK,"event_id":event_id,**payload})
    print(json.dumps({"event_id":event_id,"action":action,
                      "evidence_sha256":payload["evidence_sha256"],
                      "manifest_sha256":payload["manifest_sha256"]},ensure_ascii=False))
if __name__=="__main__":
    main()
