"""Fail-closed immutable evidence + idempotent existing-card registration."""
import datetime as dt, hashlib, json, sqlite3, time
from pathlib import Path
H=Path(__file__).resolve().parent
ROOT=H.parent.parent
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-stratified-tank-gate-20261028-1451"
SOURCE=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\best_scenario_v2_timeseries.csv")
STATUS=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\STATUS_v86.json")
FILES=("stratified_tank.py","test_stratified_tank.py","independent_qa.py",
       "STRATIFIED_TANK_RESULTS.json","QA_INDEPENDENT.json","ENGINEERING_NOTE_SK.md",
       "UNITTEST.log","RUN.log","INDEPENDENT_QA.log","finalize.py")
NEXT="Compare against existing 100 MWh Simulink dispatch boundary in isolated MATLAB test; validate UA/COP/return temperature, equipment, tariffs and 31 primary sources."
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def immutable(name,obj):
    p=H/name
    raw=(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf-8")
    if p.exists():
        if p.read_bytes()!=raw:raise RuntimeError("IMMUTABLE_CONFLICT "+name)
    else:
        with p.open("xb") as f:f.write(raw)
    return sha(p)
def stop_check():
    for root in (ROOT,ROOT/"recovery",Path(r"C:\Users\Lysda\Desktop\temp_coding"),
                 Path(r"C:\Users\Lysda\Desktop\EduMotionPipeline"),
                 Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse"),H):
        for name in ("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.flag",".STOP",".PAUSE"):
            if (root/name).exists():raise RuntimeError("STOP_ACTIVE "+str(root/name))
def main():
    stop_check()
    result=json.loads((H/"STRATIFIED_TANK_RESULTS.json").read_text(encoding="utf-8"))
    qa=json.loads((H/"QA_INDEPENDENT.json").read_text(encoding="utf-8"))
    assert sha(SOURCE)==result["source_sha256"]=="8125719923bae97901f37cf0f5354df77b46544df0477f863172255748873f25"
    assert result["source_rows"]==8760 and len(result["case_results"])==5
    assert all(len(c["yearly"])==3 for c in result["case_results"])
    assert qa["status"]=="PASS" and qa["independent_annual_energy_ledgers"]==15
    assert qa["independent_electric_source_splits"]==15 and qa["independent_cylinder_ua_checks"]==5
    assert qa["independent_final_profile_energy_checks"]==5
    assert result["synthetic_not_metered"] is True and result["primary_source_signoffs"]==0
    status=json.loads(STATUS.read_text(encoding="utf-8-sig"))
    assert status["full_primary_signoffs"]==0 and status["total_sources"]==31
    unit=(H/"UNITTEST.log").read_text(encoding="utf-8-sig")
    assert "Ran 21 tests" in unit and "\nOK" in unit and "FAILED" not in unit
    assert all((H/f).is_file() for f in FILES)
    manifest_sha=immutable("SHA256_MANIFEST.json",{"count":len(FILES),"files":{f:sha(H/f) for f in FILES}})
    cases=result["case_results"]
    summary=[{"volume_m3":c["config"]["volume_m3"],"charge_temp_c":c["config"]["charge_temp_c"],
              "ua_kw_per_k":c["config"]["ua_kw_per_k"],
              "year3_delivered_mwh":round(c["yearly"][2]["delivered_mwh"],3),
              "year3_extra_electric_mwh":round(c["yearly"][2]["added_electric_mwh"],3)}
             for c in cases]
    evidence={"scope":"DCHR_STRATIFIED_WATER_TANK_DYNAMIC_ENERGY_GATE",
      "artifact_directory":str(H),"source_sha256":sha(SOURCE),"status_v86_sha256":sha(STATUS),
      "manifest_sha256":manifest_sha,"qa":"21/21 unit PASS; 15 annual independent ledgers, 15 electric splits, 5 UA geometries, 5 profiles PASS",
      "synthetic_not_metered":True,"primary_source_signoffs":0,
      "simulink_integrated":False,"production_modified":False,
      "incremental_savings_claimed":False,"case_summary":summary,"next_step":NEXT}
    evidence_sha=immutable("EVIDENCE.json",evidence)
    payload={k:evidence[k] for k in ("scope","artifact_directory","manifest_sha256","qa",
             "synthetic_not_metered","primary_source_signoffs","simulink_integrated",
             "production_modified","incremental_savings_claimed","next_step")}
    payload["evidence_sha256"]=evidence_sha
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
                (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,ensure_ascii=False,sort_keys=True))).lastrowid
            state="RECORDED"
        db.commit()
        assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
    handoff=H/"FINAL_HANDOFF.md"
    if not handoff.exists():
        stamp=dt.datetime.now().astimezone().isoformat(timespec="seconds")
        lines=[
          "# DCHR stratified tank dynamic energy gate | "+stamp,"",
          "VERIFIED isolated 8-layer / 8-substep per hour stratified water-tank counterfactual on 8760 SYNTHETIC hours, 3 repeated years.",
          "Source SHA256 "+sha(SOURCE)+". Existing Simulink 100 MWh baseline not modified.",
          "Five cases: 10,000 and 305,485.8 m3, 72/80 C, U=0.15 W/m2/K assumed cylinder h=10m, plus lossless 10,000 m3 control.",
          "Year3 delivered MWh / extra electric MWh: "+", ".join(f"{x['volume_m3']}m3@{x['charge_temp_c']}C={x['year3_delivered_mwh']}/{x['year3_extra_electric_mwh']}" for x in summary),
          "QA 21/21 unit PASS; independent 15/15 annual energy ledgers, 15/15 electric splits, 5/5 UA geometry, 5/5 profile energy PASS.",
          "Existing Synapse task "+TASK+"; evidence event #"+str(event_id)+"; task remains queued, no worker created.",
          "Card: https://desktop-m9l3i4m.taila1c6bd.ts.net/?synapse_task="+TASK,
          "Artifact: "+str(H),"SHA256 manifest: "+manifest_sha,"SHA256 evidence: "+evidence_sha,
          "Live intake 2026-10-28 14:51 CET: primary SynapseMCP Web ping OK, RAM free 2.23 GiB, GPU 1282/8188 MiB 0%, STOP/PAUSE not found in inspected roots, existing Jarvice and Codex worktrees observed and untouched.",
          "No new Codex, GPU jobs, workers, VRS, OAuth, GUI, purchases or production source edits.",
          "LIMITATIONS: synthetic data; assumed U/UA, mixing, return 35 C, COP derating and 10 m geometry; not incremental gas savings; no validated equipment, no MATLAB integration, 0/31 primary source signoffs.",
          "NEXT: "+NEXT,""
        ]
        with handoff.open("x",encoding="utf-8") as f:f.write("\n".join(lines))
    immutable("REGISTRY_RESULT.json",{"task_id":TASK,"event_id":event_id,
      "manifest_sha256":manifest_sha,"evidence_sha256":evidence_sha,
      "handoff_sha256":sha(handoff)})
    print(json.dumps({"state":state,"task_id":TASK,"event_id":event_id,
      "manifest_sha256":manifest_sha,"evidence_sha256":evidence_sha,
      "handoff_sha256":sha(handoff)}))
if __name__=="__main__":main()
