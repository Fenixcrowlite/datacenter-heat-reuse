"""Immutable manifest + idempotent evidence event in existing DataCenter Synapse task."""
from __future__ import annotations
import datetime as dt, hashlib, json, sqlite3, time
from pathlib import Path
H=Path(__file__).resolve().parent;SCC=H.parent.parent
DCHR=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")
TASK="scc-2aab24704c2bd0";ACTOR="chatgpt-dchr-c36-provenance-20261028-1754"
FILES=["c36_audit.py","independent_qa_c36.py","C36_PROVENANCE_RESULTS.json","C36_ENGINEERING_NOTE_SK.md","QA_INDEPENDENT_C36.json","finalize_c36.py"]
NEXT="Export the Warm45_Storage100 v2 timeseries into a NEW isolated filename, never overwrite best_scenario_v2_timeseries.csv; then compare same-boundary v1/v2/Stateflow 10 MWh and physical stratified tank. No MATLAB run or model parity claimed yet."
def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()
def immutable(name,data):
    p=H/name;raw=(json.dumps(data,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    if p.exists():
        if p.read_bytes()!=raw:raise RuntimeError("IMMUTABLE_CONFLICT "+name)
    else:
        with p.open("xb") as f:f.write(raw)
    return sha(p)
def guard():
    for root in (SCC,SCC/"recovery",SCC/"Continuity",DCHR,H):
        for name in ("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.flag",".STOP",".PAUSE"):
            if (root/name).exists():raise RuntimeError("STOP_ACTIVE "+str(root/name))
def main():
    guard()
    data=json.loads((H/"C36_PROVENANCE_RESULTS.json").read_text(encoding="utf-8"))
    qa=json.loads((H/"QA_INDEPENDENT_C36.json").read_text(encoding="utf-8"))
    assert data["scope"]=="DCHR_C36_100MWH_PROVENANCE_AND_MISLABEL"
    assert data["v2_timeseries_actual_scenario"]=="Liquid35_LowTempDH"
    assert data["v2_best_coverage_scenario"]=="Warm45_Storage100"
    assert data["v1_100mwh"]["trace"]["rows"]==8760 and data["v2_100mwh"]["trace"]["rows"]==8760
    assert qa["status"]=="PASS" and qa["tests"]==14 and qa["failed"]==0
    assert all((H/f).is_file() for f in FILES)
    manifest_sha=immutable("SHA256_MANIFEST_C36.json",{"files":{f:sha(H/f) for f in FILES},"count":len(FILES)})
    evidence={"scope":data["scope"],"artifact_directory":str(H),"manifest_sha256":manifest_sha,
        "qa":"14/14 independent tests PASS; 17520 hourly records replayed, 140160 Decimal dispatch checks; 11 source hashes",
        "actual_v2_csv_scenario":"Liquid35_LowTempDH","max_coverage_v2_scenario":"Warm45_Storage100",
        "annual_gas_difference_mwh":data["v2_gas_difference_mwh"],
        "v1_100mwh_source":data["source_hashes"]["v1_driver"],"v2_100mwh_source":data["source_hashes"]["v2_driver"],
        "physical_validation":False,"v85_10mwh_parity":False,"matlab_executed":False,
        "primary_source_signoffs":0,"next_step":NEXT}
    evidence_sha=immutable("EVIDENCE_C36.json",evidence)
    payload=dict(evidence,evidence_sha256=evidence_sha)
    guard()
    with sqlite3.connect(SCC/"tasks.sqlite3",timeout=10) as db:
        db.execute("PRAGMA busy_timeout=10000")
        assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
        db.execute("BEGIN IMMEDIATE")
        row=db.execute("SELECT project,status,worker_pid FROM tasks WHERE id=?",(TASK,)).fetchone()
        if not row or row[0]!="DataCenter Heat Reuse" or row[1] in ("done","cancelled") or row[2] is not None:
            raise RuntimeError("TASK_NOT_ELIGIBLE "+str(row))
        prior=db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND actor=? AND kind='evidence'",(TASK,ACTOR)).fetchall()
        if prior:
            if len(prior)!=1 or json.loads(prior[0][1])!=payload:raise RuntimeError("EVENT_CONFLICT")
            event_id,state=prior[0][0],"ALREADY_RECORDED"
        else:
            event_id=db.execute("INSERT INTO task_events(task_id,at,kind,actor,data_json) VALUES(?,?,?,?,?)",
                (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,sort_keys=True,ensure_ascii=False))).lastrowid
            state="RECORDED"
        db.commit()
        assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
    handoff=H/"FINAL_HANDOFF.md"
    if not handoff.exists():
        lines=[
            "# DCHR C36: 100 MWh provenance and v2 scenario filename mismatch",
            "Verified local: "+dt.datetime.now().astimezone().isoformat(timespec="seconds"),"",
            "FOUND: original MATLAB run_experiment.m and run_experiment_v2.m explicitly configure 100 MWh energy-only storage.",
            "FOUND: run_experiment_v2.m exports O{end} to best_scenario_v2_timeseries.csv; O{end} is Liquid35_LowTempDH.",
            "This is NOT the highest-coverage scenario Warm45_Storage100 in scenario_summary_v2.csv.",
            f"Annual gas difference (last vs highest-coverage) = {data['v2_gas_difference_mwh']:.9f} MWh.",
            "Independently replayed 8760+8760 CSV hourly storage states; 140160 Decimal dispatch checks, 14/14 separate QA tests PASS.",
            "v85 10 MWh cases are different from early 100 MWh assumptions; no tank volume or temperature validation.",
            "No MATLAB execution, no source edits, no GUI, no new Codex/GPU workers, no VRS, no OAuth changes.",
            f"Existing task {TASK}, evidence event #{event_id}; remains queued, no worker.",
            "Card: https://desktop-m9l3i4m.taila1c6bd.ts.net/?synapse_task="+TASK,
            "Artifact: "+str(H),
            "SHA256 manifest: "+manifest_sha,
            "SHA256 evidence: "+evidence_sha,
            "Primary-source signoffs 0/31. Next: "+NEXT,""
        ]
        with handoff.open("x",encoding="utf-8") as f:f.write("\n".join(lines))
    immutable("REGISTRY_RESULT_C36.json",{"task_id":TASK,"event_id":event_id,"manifest_sha256":manifest_sha,"evidence_sha256":evidence_sha,"handoff_sha256":sha(handoff)})
    print(json.dumps({"state":state,"event_id":event_id,"task_id":TASK,"manifest_sha256":manifest_sha,"evidence_sha256":evidence_sha,"handoff_sha256":sha(handoff)},ensure_ascii=False))
if __name__=="__main__":main()
