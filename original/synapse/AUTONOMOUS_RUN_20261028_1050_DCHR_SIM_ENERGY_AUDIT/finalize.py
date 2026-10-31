"""Idempotent scoped evidence for existing DCHR task; no production edits."""
from __future__ import annotations
import datetime as dt,hashlib,json,sqlite3,time
from pathlib import Path
H=Path(__file__).resolve().parent
CENTER=H.parent.parent
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-sim-energy-audit-20261028-1050"
FILES=["dchr_sim_energy_audit.py","test_sim_energy_audit.py","independent_qa.py",
       "SIM_ENERGY_AUDIT.json","QA_INDEPENDENT.json","ENGINEERING_FINDINGS_SK.md",
       "UNITTEST.log","RUN.log","INDEPENDENT_QA.log","finalize.py"]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def immutable(name,obj):
    p=H/name
    raw=(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf-8")
    if p.exists():
        if p.read_bytes()!=raw:raise RuntimeError("IMMUTABLE_CONFLICT "+name)
    else:
        with p.open("xb") as f:f.write(raw)
    return sha(p)
def main():
    for f in [CENTER/"STOP",CENTER/"PAUSE",CENTER/"STOP.txt",
              Path(r"C:\Users\Lysda\Desktop\temp_coding\STOP"),
              Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\STOP")]:
        if f.exists():raise RuntimeError("STOP_ACTIVE "+str(f))
    qa=json.loads((H/"QA_INDEPENDENT.json").read_text(encoding="utf-8"))
    audit=json.loads((H/"SIM_ENERGY_AUDIT.json").read_text(encoding="utf-8"))
    status_path=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\STATUS_v86.json")
    status=json.loads(status_path.read_text(encoding="utf-8-sig"))
    assert status["full_primary_signoffs"]==0 and status["total_sources"]==31
    assert qa["status"]=="PASS" and qa["rows_checked"]==8760 and qa["energy_fields_checked"]==9
    assert qa["curtailed_intervals"]==4587
    assert audit["rows"]==8760 and audit["data_class"]=="SIMULATED_MODEL_OUTPUT_NOT_METERED"
    assert audit["ERF"] is audit["REF"] is audit["WUE"] is None
    assert sha(audit["source_path"])==audit["source_sha256"]
    assert "Ran 13 tests" in (H/"UNITTEST.log").read_text(encoding="utf-8")
    assert "OK" in (H/"UNITTEST.log").read_text(encoding="utf-8")
    run_bytes=(H/"RUN.log").read_bytes()
    run_text=run_bytes.decode("utf-16") if run_bytes.startswith(b"\xff\xfe") else run_bytes.decode("utf-8")
    assert '"rows": 8760' in run_text
    assert all((H/f).is_file() for f in FILES)
    manifest_sha=immutable("SHA256_MANIFEST.json",{"count":len(FILES),"files":{f:sha(H/f) for f in FILES}})
    next_step=("Obtain authenticated measured E_DC/E_IT/E_REUSE/E_RES/W_IN with explicit "
               "measurement boundaries; reconcile heat-pump electricity and DC perimeter; "
               "only then calculate regulatory metrics. Keep primary source signoffs 0/31.")
    ev={"scope":"DCHR_EXISTING_SIMULATION_ANNUAL_ENERGY_AND_CURTAILMENT_AUDIT",
        "artifact_directory":str(H),"source_csv_sha256":audit["source_sha256"],
        "source_status_v86_sha256":sha(status_path),
        "qa":"13/13 unit tests PASS; 8760/8760 hourly records and 9 energy totals independently PASS",
        "curtailed_intervals":4587,"curtailed_heat_mwh":audit["integrated_mwh"]["Curtailed_HP_Heat_MW"],
        "simulated_pue":audit["PUE_simulated"],"measured_data":False,
        "ERF_certified":False,"primary_signoffs":0,"production_modified":False,
        "manifest_sha256":manifest_sha,"next_step":next_step}
    evidence_sha=immutable("EVIDENCE.json",ev)
    payload={"scope":ev["scope"],"artifact_directory":str(H),
             "source_csv_sha256":ev["source_csv_sha256"],
             "qa":ev["qa"],"curtailed_intervals":4587,
             "evidence_sha256":evidence_sha,"manifest_sha256":manifest_sha,
             "measured_data":False,"primary_signoffs":0,"production_modified":False,
             "next_step":next_step}
    with sqlite3.connect(CENTER/"tasks.sqlite3",timeout=10) as db:
        db.row_factory=sqlite3.Row
        db.execute("PRAGMA busy_timeout=10000")
        assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
        db.execute("BEGIN IMMEDIATE")
        task=db.execute("SELECT id,project,status,worker_pid FROM tasks WHERE id=?",(TASK,)).fetchone()
        if not task or task["project"]!="DataCenter Heat Reuse" or task["status"] in ("done","cancelled") or task["worker_pid"] is not None:
            raise RuntimeError("TASK_NOT_ELIGIBLE")
        prior=db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND actor=? AND kind='evidence'",(TASK,ACTOR)).fetchall()
        if prior:
            if len(prior)!=1 or json.loads(prior[0]["data_json"])!=payload:raise RuntimeError("EVENT_CONFLICT")
            event_id=prior[0]["id"];state="ALREADY_RECORDED"
        else:
            event_id=db.execute("INSERT INTO task_events(task_id,at,kind,actor,data_json) VALUES(?,?,?,?,?)",
              (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,ensure_ascii=False,sort_keys=True))).lastrowid
            state="RECORDED"
        db.commit()
        assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
    handoff=("# DCHR simulation energy audit | 2026-10-28 10:50 CET\n\n"
       "VERIFIED isolated annual simulation audit; 8760 rows, 13/13 unit tests PASS, "
       "independent float-based 9/9 energy totals PASS. No source CSV or production edits.\n\n"
       "DISCOVERY: naive HP_Heat=HP_Source_Used+HP_Electric failed in 4587 hours "
       "because HP_Heat is potential output; correct identities are "
       "HP_Heat_Used=HP_Source_Used+HP_Electric and "
       "HP_Heat=HP_Heat_Used+Curtailed_HP_Heat. "
       "Both now 0/8760 violations, regression test added.\n\n"
       "SIMULATED PUE ~1.2, curtailed heat 22545.421 MWh (~32.414% of potential), "
       "NOT metered/certified. ERF/REF/WUE deliberately unavailable; 0/31 primary signoffs.\n"
       f"Source SHA256: {audit['source_sha256']}\n"
       f"Evidence SHA256: {evidence_sha}\nManifest SHA256: {manifest_sha}\n"
       f"Existing Synapse task {TASK}, evidence event #{event_id}; task remains queued.\n"
       "Live snapshot at intake 10:47 CET: RAM free 7.34 GB, VRAM 733/8188 MiB; "
       "STOP absent in checked roots, existing workers/worktrees not touched. "
       "No Codex, GPU jobs, GUI, VRS, OAuth, external publication or expenses.\n"
       f"NEXT: {next_step}\n")
    hp=H/"FINAL_HANDOFF.md"
    if hp.exists():
        if hp.read_text(encoding="utf-8")!=handoff:raise RuntimeError("HANDOFF_CONFLICT")
    else:hp.write_text(handoff,encoding="utf-8")
    immutable("REGISTRY_RESULT.json",{"event_id":event_id,"task_id":TASK,
       "state":"RECORDED_OR_VERIFIED","evidence_sha256":evidence_sha,
       "manifest_sha256":manifest_sha,"handoff_sha256":sha(hp)})
    print(json.dumps({"state":state,"event_id":event_id,"evidence_sha256":evidence_sha,
       "manifest_sha256":manifest_sha,"handoff_sha256":sha(hp)}))
if __name__=="__main__":main()
