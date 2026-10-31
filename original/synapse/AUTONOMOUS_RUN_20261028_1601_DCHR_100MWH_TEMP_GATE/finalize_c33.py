"""C33 immutable evidence and idempotent registration in existing DCHR task."""
import datetime as dt,hashlib,json,sqlite3,time
from pathlib import Path
H=Path(__file__).resolve().parent
ROOT=H.parent.parent
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-c33-100mwh-temp-gate-20261028-1601"
NEXT="Inspect the actual 100 MWh Simulink state/dispatch/temperature definition, then compare identical boundary conditions; validate OEM COP/UA and primary sources."
FILES=["compare_100mwh.py","independent_qa_c33.py","C33_100MWH_GATE_RESULTS.json",
       "QA_INDEPENDENT_C33.json","C33_ENGINEERING_NOTE_SK.md","RUN.log","QA_RUN.log","finalize_c33.py"]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def immutable(name,obj):
    p=H/name;raw=(json.dumps(obj,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode("utf-8")
    if p.exists():
        if p.read_bytes()!=raw:raise RuntimeError("IMMUTABLE_CONFLICT "+name)
    else:
        with p.open("xb") as f:f.write(raw)
    return sha(p)
def stop_check():
    for root in (ROOT,ROOT/"recovery",ROOT/"Continuity",Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse"),H):
        for name in ("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.flag",".STOP",".PAUSE"):
            if (root/name).exists():raise RuntimeError("STOP_ACTIVE "+str(root/name))
def main():
    stop_check()
    r=json.loads((H/"C33_100MWH_GATE_RESULTS.json").read_text(encoding="utf-8"))
    qa=json.loads((H/"QA_INDEPENDENT_C33.json").read_text(encoding="utf-8"))
    assert r["scope"]=="DCHR_C33_100MWH_TEMPERATURE_GATE_EQUIVALENCE"
    assert qa["status"]=="PASS" and qa["passed"]==28 and qa["failed"]==0
    assert len(r["cases"])==4 and r["source_rows"]==8760
    assert r["simulink_baseline_compared_dynamically"] is False
    assert r["incremental_gas_savings_verified"] is False
    assert r["primary_source_signoffs"]==0
    assert all((H/f).is_file() for f in FILES)
    manifest_sha=immutable("SHA256_MANIFEST_C33.json",{"count":len(FILES),"files":{f:sha(H/f) for f in FILES}})
    evidence={"scope":"DCHR_C33_100MWH_TEMPERATURE_GATE_EQUIVALENCE",
       "artifact_directory":str(H),"manifest_sha256":manifest_sha,
       "source_data_sha256":r["source_data_sha256"],"source_model_sha256":r["source_model_sha256"],
       "qa":"28/28 independent Decimal/energy/geometry/SHA checks PASS",
       "synthetic_not_metered":True,"simulink_baseline_compared_dynamically":False,
       "incremental_gas_savings_verified":False,"primary_source_signoffs":0,
       "volume_72c_nominal_m3":round(r["cases"][0]["volume_m3"],2),
       "volume_72c_gate_m3":round(r["cases"][1]["volume_m3"],2),
       "volume_80c_nominal_m3":round(r["cases"][2]["volume_m3"],2),
       "volume_80c_gate_m3":round(r["cases"][3]["volume_m3"],2),
       "next_step":NEXT}
    evidence_sha=immutable("EVIDENCE_C33.json",evidence)
    payload=dict(evidence);payload["evidence_sha256"]=evidence_sha
    stop_check()
    with sqlite3.connect(ROOT/"tasks.sqlite3",timeout=10) as db:
        db.execute("PRAGMA busy_timeout=10000")
        assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
        db.execute("BEGIN IMMEDIATE")
        task=db.execute("SELECT project,status,worker_pid FROM tasks WHERE id=?",(TASK,)).fetchone()
        if not task or task[0]!="DataCenter Heat Reuse" or task[1] in ("done","cancelled") or task[2] is not None:
            raise RuntimeError("TASK_NOT_ELIGIBLE "+str(task))
        prior=db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND actor=? AND kind='evidence'",(TASK,ACTOR)).fetchall()
        if prior:
            if len(prior)!=1 or json.loads(prior[0][1])!=payload:raise RuntimeError("EVENT_CONFLICT")
            event_id=prior[0][0];state="ALREADY_RECORDED"
        else:
            event_id=db.execute("INSERT INTO task_events(task_id,at,kind,actor,data_json) VALUES(?,?,?,?,?)",
                (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,sort_keys=True,ensure_ascii=False))).lastrowid
            state="RECORDED"
        db.commit()
        assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
    handoff=H/"FINAL_HANDOFF.md"
    if not handoff.exists():
        lines=[
          "# DCHR C33 100MWh temperature gate | "+dt.datetime.now().astimezone().isoformat(timespec="seconds"),"",
          "VERIFIED independent thermodynamic reinterpretation of 100MWh rating using unchanged C31 synthetic 8-layer model.",
          "Max synthetic DH supply 61.95185C; HX approach 3K; reference gate 64.95185C.",
          "For 72C: 100MWh nominal 35C return requires 2327.69m3; gate requires 12219.43m3.",
          "For 80C: nominal 1913.88m3; gate 5723.25m3.",
          "Year3 delivered heat (MWh) for four cases: 79.63, 416.99, 83.97, 251.18. Not incremental savings.",
          "Independent QA 28/28 PASS, Decimal/UA/energy residual/SHA. 8760 SYNTHETIC hours, three repeated years.",
          "Existing task "+TASK+" event #"+str(event_id)+"; no new task/worker.",
          "Card: https://desktop-m9l3i4m.taila1c6bd.ts.net/?synapse_task="+TASK,
          "Artifact: "+str(H),"SHA256 manifest: "+manifest_sha,"SHA256 evidence: "+evidence_sha,
          "No Codex, GPU jobs, workers, VRS, OAuth, GUI, shared Simulink source or production edits.",
          "LIMITATIONS: existing Simulink 100MWh rating not yet matched dynamically, no metered validation, 0/31 source signoffs.",
          "NEXT: "+NEXT,""]
        with handoff.open("x",encoding="utf-8") as f:f.write("\n".join(lines))
    immutable("REGISTRY_RESULT_C33.json",{"task_id":TASK,"event_id":event_id,
        "manifest_sha256":manifest_sha,"evidence_sha256":evidence_sha,
        "handoff_sha256":sha(handoff)})
    print(json.dumps({"state":state,"task_id":TASK,"event_id":event_id,
       "manifest_sha256":manifest_sha,"evidence_sha256":evidence_sha,
       "handoff_sha256":sha(handoff)},ensure_ascii=False))
if __name__=="__main__":main()
