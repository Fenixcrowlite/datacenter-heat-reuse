"""C37 immutable evidence + idempotent event on existing Synapse task."""
from __future__ import annotations
import datetime as dt,hashlib,json,sqlite3,time
from pathlib import Path
H=Path(__file__).resolve().parent
SCC=H.parent.parent
DCHR=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-c37-v2-python-replay-20261028-1858"
FILES=["c37_replay.py","independent_qa_c37.py","compare_c37.py",
       "Warm45_Storage100_v2_PYTHON_REPLAY.csv","C37_REPLAY_RESULTS.json",
       "QA_INDEPENDENT_C37.json","C37_COMPARISON.json",
       "C37_ENGINEERING_NOTE_SK.md","finalize_c37.py"]
NEXT=("Run a native MATLAB v2 Warm45_Storage100 export to a new isolated CSV, "
      "compare 8760 rows against C37 replay, then establish same-boundary Stateflow v85 "
      "10 MWh and stratified-tank parity. Do not overwrite original results.")
def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()
def immutable(name,obj):
    p=H/name
    raw=(json.dumps(obj,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    if p.exists():
        if p.read_bytes()!=raw:raise RuntimeError("IMMUTABLE_CONFLICT "+name)
    else:
        with p.open("xb") as f:f.write(raw)
    return sha(p)
def guard():
    for root in (SCC,SCC/"recovery",SCC/"Continuity",DCHR,H):
        for n in ("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.flag",".STOP",".PAUSE"):
            if (root/n).exists():raise RuntimeError("STOP_ACTIVE "+str(root/n))
def main():
    guard()
    d=json.loads((H/"C37_REPLAY_RESULTS.json").read_text(encoding="utf-8"))
    qa=json.loads((H/"QA_INDEPENDENT_C37.json").read_text(encoding="utf-8"))
    cmp=json.loads((H/"C37_COMPARISON.json").read_text(encoding="utf-8"))
    assert d["scope"]=="DCHR_C37_V2_PYTHON_REPLAY" and d["hours"]==8760
    assert qa["status"]=="PASS" and qa["decimal_storage_balances"]==8760
    assert qa["source_oracle_comparisons"]==192720
    assert cmp["rows"]==8760 and abs(cmp["delta_v2_minus_v1"]["gas_MWh"]-129.13228872)<1e-6
    assert d["physical_validation"] is False and d["v85_stateflow_parity"] is False
    assert sha(H/"Warm45_Storage100_v2_PYTHON_REPLAY.csv")==d["output_sha256"]
    assert sha(DCHR/"results"/"best_scenario_v2_timeseries.csv")==d["source_v2_oracle_sha256"]
    assert all((H/f).is_file() for f in FILES)
    manifest_sha=immutable("SHA256_MANIFEST_C37.json",
                           {"files":{f:sha(H/f) for f in FILES},"count":len(FILES)})
    evidence={"scope":d["scope"],"artifact_directory":str(H),"manifest_sha256":manifest_sha,
              "qa":"192720 oracle comparisons; 8760/8760 independent Decimal storage balances; six annual checks PASS",
              "hours":8760,"v2_gas_MWh":d["annual"]["GasHeat_MWh"],
              "v2_hp_electric_MWh":d["annual"]["HPElectric_MWh"],
              "v2_minus_v1_gas_MWh":cmp["delta_v2_minus_v1"]["gas_MWh"],
              "csv_sha256":d["output_sha256"],"matlab_executed":False,
              "synthetic":True,"physical_validation":False,"stateflow_parity":False,
              "primary_source_signoffs":0,"next_step":NEXT}
    evidence_sha=immutable("EVIDENCE_C37.json",evidence)
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
            "# DCHR C37 — Warm45_Storage100 v2 hourly Python replay",
            "Verified local: "+dt.datetime.now().astimezone().isoformat(timespec="seconds"),"",
            "Recovered source equations and reconstructed an isolated 8760-hour v2 Warm45_Storage100 CSV.",
            "Validation: 192720 hourly comparisons to Liquid35 v2 MATLAB CSV, max abs error 8.53e-14.",
            "Independent QA: 8760/8760 Decimal storage balances, 6 annual sums PASS.",
            "Warm45 v2 gas: %.9f MWh; HP electricity: %.9f MWh."%(d["annual"]["GasHeat_MWh"],d["annual"]["HPElectric_MWh"]),
            "Warm45 v2 minus v1 gas: %.9f MWh; architecture differs, not measured savings."%cmp["delta_v2_minus_v1"]["gas_MWh"],
            "Original OneDrive CSV/MATLAB/SLX unchanged. No MATLAB run; no Stateflow/physical parity.",
            "No new Codex/GPU worker, no VRS, OAuth or shared GUI modifications.",
            "Existing task "+TASK+" evidence event #"+str(event_id)+"; task remains queued, no worker.",
            "Card: https://desktop-m9l3i4m.taila1c6bd.ts.net/?synapse_task="+TASK,
            "Artifact: "+str(H),
            "CSV SHA256: "+d["output_sha256"],
            "SHA256 manifest: "+manifest_sha,
            "SHA256 evidence: "+evidence_sha,
            "Primary source signoffs 0/31. Next: "+NEXT,""]
        with handoff.open("x",encoding="utf-8") as f:f.write("\n".join(lines))
    immutable("REGISTRY_RESULT_C37.json",{"task_id":TASK,"event_id":event_id,
       "manifest_sha256":manifest_sha,"evidence_sha256":evidence_sha,
       "handoff_sha256":sha(handoff)})
    print(json.dumps({"state":state,"event_id":event_id,"task_id":TASK,
       "manifest_sha256":manifest_sha,"evidence_sha256":evidence_sha,
       "handoff_sha256":sha(handoff)},ensure_ascii=False))
if __name__=="__main__":main()
