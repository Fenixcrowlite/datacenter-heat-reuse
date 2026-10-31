"""Register one immutable, idempotent evidence event on existing DCHR card."""
import hashlib,json,sqlite3,time
from pathlib import Path
H=Path(__file__).parent
ROOT=H.parent.parent
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-constrained-storage-20261028-1252"
SOURCE=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\best_scenario_v2_timeseries.csv")
STATUS=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\STATUS_v86.json")
FILES=("constrained_storage.py","test_constrained_storage.py","independent_qa.py",
       "patch_site_caps.py","patch_thermal_sensitivity.py","patch_qa_thermal.py",
       "CONSTRAINED_SENSITIVITY.json","QA_INDEPENDENT.json","UNITTEST.log",
       "RUN.log","INDEPENDENT_QA.log","ENGINEERING_NOTE_SK.md",
       "verify_recorded_evidence.py","finalize.py")
NEXT=("Integrate storage dispatch with the original 100 MWh Simulink baseline, "
      "validate actual HP COP and electrical nameplate limits, temperature dynamics "
      "and hourly tariffs, then independently verify net economics.")

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def immutable(name,obj):
    p=H/name
    raw=(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
    if p.exists():
        if p.read_bytes()!=raw:raise RuntimeError("IMMUTABLE_CONFLICT "+name)
    else:
        with p.open("xb") as f:f.write(raw)
    return sha(p)
def stop_check():
    for root in (ROOT,Path(r"C:\Users\Lysda\Desktop\temp_coding"),
                 Path(r"C:\Users\Lysda\Desktop\EduMotionPipeline"),
                 Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse"),H):
        for name in ("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.flag"):
            if (root/name).exists():raise RuntimeError("STOP_ACTIVE "+str(root/name))
def main():
    stop_check()
    data=json.loads((H/"CONSTRAINED_SENSITIVITY.json").read_text(encoding="utf-8"))
    qa=json.loads((H/"QA_INDEPENDENT.json").read_text(encoding="utf-8"))
    assert data["source_sha256"]==sha(SOURCE) and data["rows"]==8760
    assert len(data["models"])==8 and len(data["thermal_sensitivity"])==5
    assert qa["status"]=="PASS" and qa["independent_decimal_hour_steps"]==26280
    assert qa["aggregate_years_checked"]==39 and qa["models_checked"]==13
    status=json.loads(STATUS.read_text(encoding="utf-8-sig"))
    assert status["full_primary_signoffs"]==0 and status["total_sources"]==31
    log=(H/"UNITTEST.log").read_bytes()
    log=log.decode("utf-16" if log.startswith(b"\xff\xfe") else "utf-8-sig")
    assert "Ran 20 tests" in log and "OK" in log and "FAILED" not in log
    assert all((H/f).is_file() for f in FILES)
    manifest_sha=immutable("SHA256_MANIFEST.json",{"count":len(FILES),
                           "files":{f:sha(H/f) for f in FILES}})
    selected=next(m for m in data["models"] if m["config"]["capacity_mwh"]==2500
                  and m["config"]["extra_hp_electric_mw"]==1.5)
    y=selected["year_results"][2]
    evidence={"scope":"DCHR_CONSTRAINED_SEASONAL_STORAGE_SENSITIVITY",
              "source_csv_sha256":sha(SOURCE),"status_v86_sha256":sha(STATUS),
              "artifact_directory":str(H),"manifest_sha256":manifest_sha,
              "qa":"20/20 unit tests; 39 annual energy balances; 26280 independent Decimal hour steps PASS",
              "synthetic_not_metered":True,"real_gas_savings_claimed":False,
              "production_modified":False,"primary_source_signoffs":0,
              "baseline_existing_storage_mwh":100,
              "reference_year3_thermal_coverage_mwh":y["delivered_mwh"],
              "reference_year3_extra_electric_mwh":y["additional_electric_mwh"],
              "next_step":NEXT}
    evidence_sha=immutable("EVIDENCE.json",evidence)
    payload={"scope":evidence["scope"],"artifact_directory":str(H),
             "evidence_sha256":evidence_sha,"manifest_sha256":manifest_sha,
             "qa":evidence["qa"],"synthetic_not_metered":True,
             "real_gas_savings_claimed":False,"production_modified":False,
             "primary_source_signoffs":0,"next_step":NEXT}
    with sqlite3.connect(ROOT/"tasks.sqlite3",timeout=10) as db:
        db.execute("PRAGMA busy_timeout=10000")
        assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
        db.execute("BEGIN IMMEDIATE")
        task=db.execute("SELECT project,status,worker_pid FROM tasks WHERE id=?",(TASK,)).fetchone()
        if not task or task[0]!="DataCenter Heat Reuse" or task[1] in ("done","cancelled") or task[2] is not None:
            raise RuntimeError("TASK_NOT_ELIGIBLE "+str(task))
        prior=db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND actor=? AND kind='evidence'",
                         (TASK,ACTOR)).fetchall()
        if prior:
            if len(prior)!=1 or json.loads(prior[0][1])!=payload:raise RuntimeError("EVENT_CONFLICT")
            event_id=prior[0][0];state="ALREADY_RECORDED"
        else:
            event_id=db.execute("INSERT INTO task_events(task_id,at,kind,actor,data_json) VALUES(?,?,?,?,?)",
                (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,ensure_ascii=False,sort_keys=True))).lastrowid
            state="RECORDED"
        db.commit()
        assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
    handoff=f"""# DCHR constrained storage | 2026-10-28

VERIFIED isolated 8760-hour synthetic sensitivity, 8 electric/capacity scenarios + 5 temperature/loss scenarios. Source SHA256 {sha(SOURCE)}; original CSV/Simulink/SCADA unchanged.
Reference 2500 MWh storage / 1.5 MW extra HP cap / 72 C / 0.025% hourly loss: theoretical year-3 gas heat coverage {y['delivered_mwh']:.3f} MWh; extra HP electricity {y['additional_electric_mwh']:.3f} MWh. NOT net gas savings; existing baseline already has 100 MWh storage.
QA: 20/20 unit PASS, 39 annual balances PASS, 26280 independent Decimal hour steps PASS; 0/31 primary-source signoffs.
Existing Synapse task {TASK}, evidence event #{event_id}, status remains queued, no worker.
Card: https://desktop-m9l3i4m.taila1c6bd.ts.net/?synapse_task={TASK}
Artifact: {H}
SHA256 manifest: {manifest_sha}
SHA256 evidence: {evidence_sha}
Live intake 2026-10-28 12:50-12:51 CET: SynapseMCP Web ping OK; RAM free 2.87 GiB; VRAM 1269/8188 MiB, GPU 2%; checked root STOP/PAUSE absent; Jarvice worktrees and existing processes observed, untouched.
No Codex sessions, new GPU workers, GUI/OAuth/secret edits, purchases, VRS or source-model modifications.
LIMITATIONS: uncalibrated COP inverse-lift model, assumed site/HP power caps, fixed storage temperature, no stratification, dispatch integration, tariffs or CAPEX. This is a counterfactual, not measured savings.
NEXT: {NEXT}
"""
    p=H/"FINAL_HANDOFF.md"
    if p.exists():
        if p.read_text(encoding="utf-8")!=handoff:raise RuntimeError("HANDOFF_CONFLICT")
    else:
        with p.open("x",encoding="utf-8") as f:f.write(handoff)
    immutable("REGISTRY_RESULT.json",{"event_id":event_id,"task_id":TASK,
              "evidence_sha256":evidence_sha,"manifest_sha256":manifest_sha,
              "handoff_sha256":sha(p)})
    print(json.dumps({"state":state,"event_id":event_id,"task_id":TASK,
                      "evidence_sha256":evidence_sha,"manifest_sha256":manifest_sha,
                      "handoff_sha256":sha(p)},ensure_ascii=False))
if __name__=="__main__":main()
