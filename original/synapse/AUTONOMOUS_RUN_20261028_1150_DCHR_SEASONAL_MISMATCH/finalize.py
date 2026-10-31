"""Record immutable, idempotent evidence on the existing DCHR task only."""
from __future__ import annotations
import hashlib
import json
import sqlite3
import time
from pathlib import Path

H=Path(__file__).resolve().parent
ROOT=H.parent.parent
TASK="scc-2aab24704c2bd0"
ACTOR="chatgpt-dchr-seasonal-mismatch-20261028-1150"
SOURCE=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\best_scenario_v2_timeseries.csv")
STATUS=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\STATUS_v86.json")
FILES=("seasonal_heat_shift.py","test_seasonal_heat_shift.py","independent_qa.py",
       "SEASONAL_MISMATCH.json","ENGINEERING_NOTE_SK.md","RUN.log",
       "UNITTEST.log","INDEPENDENT_QA.log","QA_INDEPENDENT.json","finalize.py")

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def immutable(name,data):
    path=H/name
    raw=(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf-8")
    if path.exists():
        if path.read_bytes()!=raw:raise RuntimeError("IMMUTABLE_CONFLICT "+name)
    else:
        with path.open("xb") as out:out.write(raw)
    return sha(path)

def main():
    for root in (ROOT,Path(r"C:\Users\Lysda\Desktop\temp_coding"),
                 Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse"),H):
        for name in ("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.flag"):
            if (root/name).exists():raise RuntimeError("STOP_ACTIVE "+str(root/name))
    result=json.loads((H/"SEASONAL_MISMATCH.json").read_text(encoding="utf-8"))
    qa=json.loads((H/"QA_INDEPENDENT.json").read_text(encoding="utf-8"))
    assert result["source_sha256"]==sha(SOURCE)
    assert result["rows"]==8760 and result["simultaneous_curtailment_gas_hours"]==0
    assert result["production_modified"] is False and result["primary_source_signoffs"]==0
    assert qa["status"]=="PASS" and qa["counterfactual_fields_checked"]==120
    assert qa["months_checked"]==12 and qa["source_rows"]==8760
    status=json.loads(STATUS.read_text(encoding="utf-8-sig"))
    assert status["full_primary_signoffs"]==0 and status["total_sources"]==31
    unit_bytes=(H/"UNITTEST.log").read_bytes()
    unit=unit_bytes.decode("utf-16" if unit_bytes.startswith(b"\xff\xfe") else "utf-8-sig")
    assert "Ran 15 tests" in unit and "OK" in unit and "FAILED" not in unit
    run_bytes=(H/"RUN.log").read_bytes()
    assert "8760" in run_bytes.decode("utf-16" if run_bytes.startswith(b"\xff\xfe") else "utf-8-sig")
    assert all((H/f).is_file() for f in FILES)
    manifest_sha=immutable("SHA256_MANIFEST.json",
                            {"count":len(FILES),"files":{f:sha(H/f) for f in FILES}})
    next_step=("Implement coupled seasonal thermal-storage sensitivity with actual "
               "HP electric demand/COP, MW charge-discharge limits, thermal losses, "
               "temperature constraints and independent physical QA; keep baseline immutable.")
    evidence={"scope":"DCHR_SEASONAL_HEAT_GAS_MISMATCH_AND_IDEAL_STORAGE_UPPER_BOUND",
              "source_csv_sha256":result["source_sha256"],
              "status_v86_sha256":sha(STATUS),
              "artifact_directory":str(H),"manifest_sha256":manifest_sha,
              "qa":"15/15 unittest PASS; 8760/8760 records, 12 months and 120 Decimal counterfactual fields independently PASS",
              "overlap_hours":0,"direct_same_hour_gas_displacement_upper_bound_mwh":0,
              "curtailed_potential_mwh":result["curtailed_potential_mwh"],
              "gas_heat_mwh":result["gas_heat_mwh"],
              "classification":result["classification"],
              "real_gas_savings_claimed":False,"production_modified":False,
              "primary_source_signoffs":0,"next_step":next_step}
    evidence_sha=immutable("EVIDENCE.json",evidence)
    payload={"scope":evidence["scope"],"artifact_directory":str(H),
             "evidence_sha256":evidence_sha,"manifest_sha256":manifest_sha,
             "qa":evidence["qa"],"overlap_hours":0,
             "real_gas_savings_claimed":False,"production_modified":False,
             "primary_source_signoffs":0,"next_step":next_step}
    with sqlite3.connect(ROOT/"tasks.sqlite3",timeout=10) as db:
        db.row_factory=sqlite3.Row
        db.execute("PRAGMA busy_timeout=10000")
        assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
        db.execute("BEGIN IMMEDIATE")
        task=db.execute("SELECT id,project,status,worker_pid FROM tasks WHERE id=?",(TASK,)).fetchone()
        if not task or task["project"]!="DataCenter Heat Reuse" or task["status"] in ("done","cancelled") or task["worker_pid"] is not None:
            raise RuntimeError("TASK_NOT_ELIGIBLE")
        prior=db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND actor=? AND kind='evidence'",
                         (TASK,ACTOR)).fetchall()
        if prior:
            if len(prior)!=1 or json.loads(prior[0]["data_json"])!=payload:
                raise RuntimeError("EVENT_CONFLICT")
            event_id=prior[0]["id"]
            state="ALREADY_RECORDED"
        else:
            event_id=db.execute("INSERT INTO task_events(task_id,at,kind,actor,data_json) VALUES(?,?,?,?,?)",
                (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,ensure_ascii=False,sort_keys=True))).lastrowid
            state="RECORDED"
        db.commit()
        assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
    handoff=f"""# DCHR seasonal mismatch | 2026-10-28 11:50 CET

VERIFIED isolated seasonal heat-vs-gas mismatch analysis on 8760 synthetic hourly records. Source SHA256 {result['source_sha256']}; original CSV and MATLAB model unchanged.

DISCOVERY: zero hours of simultaneous HP curtailment and gas heating. Curtailed potential {result['curtailed_potential_mwh']:.3f} MWh vs gas {result['gas_heat_mwh']:.3f} MWh. Direct same-hour gas displacement upper bound is 0 MWh; mismatch is seasonal.

Idealized buffer counterfactual: 100% efficient, unlimited charge/discharge power, no extra HP electricity, first synthetic year starts empty, following two years replay the same synthetic profile. This is a MATHEMATICAL UPPER BOUND, not feasible storage design, actual fuel savings, or incremental savings over existing 100 MWh model storage. See ENGINEERING_NOTE_SK.md for capacity table.

QA: 15/15 unit tests PASS; independent Decimal recomputation of 12 months, 8760 records, 120 storage fields PASS. Initial fixture bug fixed and retested; no remaining failures. SQLite integrity PASS.

SHA256 manifest: {manifest_sha}
SHA256 evidence: {evidence_sha}
Existing Synapse task {TASK}, evidence event #{event_id} ({state}); task stays queued.
Card: https://desktop-m9l3i4m.taila1c6bd.ts.net/?synapse_task={TASK}

Live intake: 2026-10-28 11:50 CET, SynapseMCP Web ping OK, RAM free 4.07 GiB, VRAM 1068/8188 MiB; STOP/PAUSE absent in checked roots; DCHR task queued with no worker PID, EduMotion task blocked. Existing Jarvice worktrees and worker processes observed, untouched. No Codex, GPU jobs, GUI, OAuth, VRS, public changes or expenses.

Limitations: original CSV timestamps have no timezone; synthetic source is not metered. HP_Heat curtailed is potential, not proven available without extra electricity. 0/31 primary source signoffs; ERF/REF/WUE unverified.

NEXT: {next_step}
"""
    hp=H/"FINAL_HANDOFF.md"
    if hp.exists():
        if hp.read_text(encoding="utf-8")!=handoff:raise RuntimeError("HANDOFF_CONFLICT")
    else:hp.write_text(handoff,encoding="utf-8")
    immutable("REGISTRY_RESULT.json",{"event_id":event_id,"task_id":TASK,
        "state":"RECORDED_OR_VERIFIED","evidence_sha256":evidence_sha,
        "manifest_sha256":manifest_sha,"handoff_sha256":sha(hp)})
    print(json.dumps({"state":state,"event_id":event_id,"task_id":TASK,
        "evidence_sha256":evidence_sha,"manifest_sha256":manifest_sha,
        "handoff_sha256":sha(hp)}))

if __name__=="__main__":main()
