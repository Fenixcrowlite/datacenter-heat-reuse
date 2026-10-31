"""Fail-closed, idempotent evidence registration on existing DCHR Synapse card."""
import datetime as dt
import hashlib
import json
import sqlite3
import time
from pathlib import Path

H=Path(__file__).resolve().parent
ROOT=H.parent.parent
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-water-volume-gate-20261028-1357"
SOURCE=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\best_scenario_v2_timeseries.csv")
STATUS=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\STATUS_v86.json")
FILES=("storage_volume_gate.py","test_storage_volume_gate.py","independent_qa.py",
       "STORAGE_VOLUME_FEASIBILITY.json","QA_INDEPENDENT.json","ENGINEERING_NOTE_SK.md",
       "UNITTEST.log","RUN.log","INDEPENDENT_QA.log","QA_INITIAL_FAIL.log","finalize.py")
NEXT=("Add temperature-dependent SOC/stratification and return-temperature dynamics in isolated "
      "model; compare against existing 100 MWh Simulink baseline; validate equipment, tariffs and 31 sources.")

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
    for root in (ROOT,Path(r"C:\Users\Lysda\Desktop\temp_coding"),
                 Path(r"C:\Users\Lysda\Desktop\EduMotionPipeline"),
                 Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse"),H):
        for name in ("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.flag"):
            if (root/name).exists():raise RuntimeError("STOP_ACTIVE "+str(root/name))

def main():
    stop_check()
    result=json.loads((H/"STORAGE_VOLUME_FEASIBILITY.json").read_text(encoding="utf-8"))
    qa=json.loads((H/"QA_INDEPENDENT.json").read_text(encoding="utf-8"))
    assert sha(SOURCE)==result["source"]["source_sha256"]=="8125719923bae97901f37cf0f5354df77b46544df0477f863172255748873f25"
    assert result["source"]["rows"]==8760 and len(result["cases"])==64
    assert qa["status"]=="PASS" and qa["cases_checked"]==64 and qa["geometry_reconstructions"]==56
    status=json.loads(STATUS.read_text(encoding="utf-8-sig"))
    assert status["full_primary_signoffs"]==0 and status["total_sources"]==31
    unit=(H/"UNITTEST.log").read_bytes()
    unit=unit.decode("utf-16" if unit.startswith(b"\xff\xfe") else "utf-8-sig",errors="replace")
    assert "Ran 16 tests" in unit and "OK" in unit and "FAILED" not in unit
    assert all((H/f).is_file() for f in FILES)
    manifest_sha=immutable("SHA256_MANIFEST.json",{"count":len(FILES),"files":{f:sha(H/f) for f in FILES}})
    ref=next(x for x in result["cases"] if (x["capacity_mwh"],x["hot_c"],x["supply_statistic"])==(2500,72,"max"))
    evidence={"scope":"DCHR_WATER_VOLUME_PHYSICAL_FEASIBILITY_GATE",
              "artifact_directory":str(H),"source_sha256":sha(SOURCE),
              "status_v86_sha256":sha(STATUS),"manifest_sha256":manifest_sha,
              "qa":"16/16 unit PASS; 64/64 independent Decimal scenarios; 56 geometry and 3 retention checks PASS",
              "initial_qa_failure_preserved":True,
              "reference_ideal_volume_m3":ref["ideal_water_volume_m3"],
              "reference_hot_c":72,"reference_max_supply_c":result["source"]["max_c"],
              "synthetic_not_metered":True,"equipment_validated":False,
              "primary_source_signoffs":0,"production_modified":False,
              "incremental_gas_savings_claimed":False,"next_step":NEXT}
    evidence_sha=immutable("EVIDENCE.json",evidence)
    payload={k:evidence[k] for k in ("scope","artifact_directory","manifest_sha256","qa",
              "synthetic_not_metered","equipment_validated","primary_source_signoffs",
              "production_modified","incremental_gas_savings_claimed","next_step")}
    payload["evidence_sha256"]=evidence_sha
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
        timestamp=dt.datetime.now().astimezone().isoformat(timespec="seconds")
        content=(f"# DCHR water-volume physical feasibility gate | {timestamp}\n\n"
          f"VERIFIED isolated calculation from 8760 SYNTHETIC hours. Source SHA256 {sha(SOURCE)}. "
          f"Reference 2500 MWh / 72 C / maximum supply {result['source']['max_c']:.5f} C / HX 3 K: "
          f"optimistic water volume {ref['ideal_water_volume_m3']:.1f} m3. "
          f"10 m equivalent diameter {ref['ideal_geometry_10m']['equivalent_single_cylinder_diameter_m']:.1f} m. "
          f"Original constant-temperature SOC does not physically model cooling during discharge.\n"
          f"Loss assumption 0.025% per hour gives 180-day retention {result['retention']['180d']:.3%}; not measured UA.\n"
          f"QA 16/16 unit PASS, independent 64/64 Decimal PASS, 56 geometry checks, 3 retention checks. "
          f"Initial too-strict absolute Decimal tolerance failure preserved and corrected with relative tolerance.\n"
          f"Existing task {TASK}; evidence event #{event_id}; task stays queued, no live worker.\n"
          f"Card: https://desktop-m9l3i4m.taila1c6bd.ts.net/?synapse_task={TASK}\n"
          f"Artifact: {H}\nSHA256 manifest: {manifest_sha}\nSHA256 evidence: {evidence_sha}\n"
          f"Live intake 2026-10-28 13:51-13:57 CET: primary SynapseMCP Web ping OK; RAM free 2.07 GiB initially, "
          f"1.53 GiB before finalize; GPU 1373/8188 MiB 2%; root STOP/PAUSE absent; "
          f"existing Codex processes and worktrees observed and untouched.\n"
          f"No new Codex, GPU jobs, worker, GUI/OAuth/secret changes, purchases, VRS or production source modifications.\n"
          f"LIMITATIONS: ideal constant water properties, no stratification, no actual tank dimensions, "
          f"0/31 primary source signoffs, existing 100 MWh baseline, no verified economics or real savings.\n"
          f"NEXT: {NEXT}\n")
        with handoff.open("x",encoding="utf-8") as f:f.write(content)
    immutable("REGISTRY_RESULT.json",{"task_id":TASK,"event_id":event_id,
              "manifest_sha256":manifest_sha,"evidence_sha256":evidence_sha,
              "handoff_sha256":sha(handoff)})
    print(json.dumps({"state":state,"event_id":event_id,"task_id":TASK,
        "evidence_sha256":evidence_sha,"manifest_sha256":manifest_sha,
        "handoff_sha256":sha(handoff)}))
if __name__=="__main__":main()
