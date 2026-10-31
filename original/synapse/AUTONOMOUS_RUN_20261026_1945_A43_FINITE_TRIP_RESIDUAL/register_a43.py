"""Idempotent A43 evidence append to existing Synapse card, fail closed."""
from __future__ import annotations
import hashlib
import json
import sqlite3
import time
import zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
CENTER=HERE.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-a43-finite-trip-20261026-1945"
CASES=("both","main_only","backup_only","neither","CF_both","CF_backup_only","CF_neither")
FILES=["finite_trip_a43.py","test_a43.py","verify_a43.py","validate_a43.m",
    "build_a43.m","DCHR_A43_Finite_Trip_Closed_Loop.slx",
    "RESULTS_A43.json","MATLAB_AUDIT_A43.json","SIMULINK_A43_RESULT.json",
    "ENGINEERING_REPORT_RU.md","LIVE_STATE_A43.json",
    "RUN_STDOUT.txt","RUN_STDERR.txt","QA_FINAL_STDOUT.txt","QA_FINAL_STDERR.txt",
    "MATLAB_STDOUT.txt","MATLAB_STDERR.txt","SIMULINK_STDOUT.txt","SIMULINK_STDERR.txt",
    "register_a43.py"]+["TRACE_A43_"+x+".csv" for x in CASES]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def once(path,content):
    if path.exists():
        if path.read_text(encoding="utf8")!=content:
            raise RuntimeError("EXISTING_ARTIFACT_CONFLICT "+str(path))
    else:
        path.write_text(content,encoding="utf8")

def main():
    for folder in (CENTER,CENTER/"recovery",HERE,
                   HERE.parent/"AUTONOMOUS_RUN_20261026_1850_A42_COUPLED_FAILSAFE"):
        for name in ("STOP","STOP.flag","PAUSE","PAUSE.flag",".STOP",".PAUSE"):
            if (folder/name).exists():
                raise RuntimeError("STOP_ACTIVE "+str(folder/name))
    for f in FILES:
        if not (HERE/f).is_file():
            raise RuntimeError("MISSING "+f)
    qa_bytes=(HERE/"QA_FINAL_STDERR.txt").read_bytes()
    qa=qa_bytes.decode("utf-16" if qa_bytes.startswith(bytes.fromhex("fffe")) else "utf8",errors="replace")
    if "Ran 18 tests" not in qa or not qa.rstrip().endswith("OK"):
        raise RuntimeError("QA_NOT_PASS")
    if "A43_SIMULINK_ALL_PASS 51744" not in (HERE/"SIMULINK_STDOUT.txt").read_text(encoding="utf8"):
        raise RuntimeError("SIMULINK_LOG_NOT_PASS")
    if "A43_MATLAB_ALL_PASS 4704" not in (HERE/"MATLAB_STDOUT.txt").read_text(encoding="utf8"):
        raise RuntimeError("MATLAB_LOG_NOT_PASS")
    for name in ("RUN_STDERR.txt","MATLAB_STDERR.txt","SIMULINK_STDERR.txt"):
        if (HERE/name).stat().st_size:
            raise RuntimeError("STDERR_NONEMPTY "+name)
    a=json.loads((HERE/"MATLAB_AUDIT_A43.json").read_text(encoding="utf8"))
    s=json.loads((HERE/"SIMULINK_A43_RESULT.json").read_text(encoding="utf8"))
    p=json.loads((HERE/"RESULTS_A43.json").read_text(encoding="utf8"))
    live=json.loads((HERE/"LIVE_STATE_A43.json").read_text(encoding="utf8"))
    if a["status"]!="A43_MATLAB_INDEPENDENT_CSV_AUDIT_PASS" or a["samples"]!=4704:
        raise RuntimeError("MATLAB_AUDIT_FAIL")
    if s["status"]!="A43_SIMULINK_EMCHART_CLOSED_LOOP_PARITY_PASS" or s["numeric_comparisons"]!=51744:
        raise RuntimeError("SIMULINK_PARITY_FAIL")
    if set(s["scenarios"])!=set(CASES) or p["physical_release"] or s["physical_release"]:
        raise RuntimeError("SAFETY_OR_CASES_FAIL")
    if s["graphical_stateflow_chart_built"] or not s["state_machine_implemented_in_EMChart"]:
        raise RuntimeError("MODEL_KIND_MISMATCH")
    if live["stop_flags"] or live["matlab_process_count"]!=0:
        raise RuntimeError("LIVE_STATE_UNSAFE")
    with zipfile.ZipFile(HERE/"DCHR_A43_Finite_Trip_Closed_Loop.slx") as z:
        if z.testzip() is not None:
            raise RuntimeError("SLX_CORRUPT")
    evidence=dict(status="A43_SYNTHETIC_SIMULINK_EMCHART_CLOSED_LOOP_PARITY_PASS",
        physical_release=False,hardware_control=False,
        artifact_directory=str(HERE),existing_task_id=TASK,
        model_sha256=sha(HERE/"DCHR_A43_Finite_Trip_Closed_Loop.slx"),
        python_source_sha256=sha(HERE/"finite_trip_a43.py"),
        a42_source_sha256=p["a42_source_sha256"],input_sha256=p["input_sha256"],
        matlab_audit_sha256=sha(HERE/"MATLAB_AUDIT_A43.json"),
        simulink_result_sha256=sha(HERE/"SIMULINK_A43_RESULT.json"),
        qa="18/18 Python PASS; 18816 Decimal expressions; MATLAB CSV 4704; executable Simulink EMChart 4704 steps/51744 parity PASS",
        caveat="Synthetic assumptions: 30-min trip, 12% residual heat tau 1h, 60kW/15min REJECT recovery; no graphical Stateflow chart or compressor inertia, no hardware release",
        next_step="A44 independent graphical Stateflow transitions + compressor ramp/lag and measured parameter calibration; no production/hardware changes")
    once(HERE/"EVIDENCE.json",json.dumps(evidence,indent=2,ensure_ascii=False)+"\n")
    manifest={f:sha(HERE/f) for f in FILES+["EVIDENCE.json"]}
    once(HERE/"SHA256_MANIFEST.json",json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
    payload=dict(scope="A43_isolated_finite_trip_residual_thermal_simulink",
        artifact_directory=str(HERE),evidence_sha256=sha(HERE/"EVIDENCE.json"),
        manifest_sha256=sha(HERE/"SHA256_MANIFEST.json"),
        model_sha256=evidence["model_sha256"],qa=evidence["qa"],
        status=evidence["status"],physical_release=False,
        caveat=evidence["caveat"],next_step=evidence["next_step"])
    db=sqlite3.connect(CENTER/"tasks.sqlite3",timeout=10,isolation_level=None)
    db.execute("pragma busy_timeout=10000")
    if db.execute("pragma quick_check").fetchone()[0]!="ok":
        raise RuntimeError("SQLITE_CORRUPT")
    db.execute("begin immediate")
    try:
        state=db.execute("select status,stage,worker_pid,owner from tasks where id=?",(TASK,)).fetchone()
        if state!=("review","planned",None,"MATLAB/Stateflow QA"):
            raise RuntimeError("TASK_OWNERSHIP_CHANGED "+repr(state))
        events=db.execute("select id,data_json from task_events where task_id=? and actor=? and kind='evidence'",(TASK,ACTOR)).fetchall()
        if len(events)>1:
            raise RuntimeError("DUPLICATE_EVENT")
        if events:
            if json.loads(events[0][1])!=payload:
                raise RuntimeError("EVENT_PAYLOAD_CONFLICT")
            event_id,action=events[0][0],"EXISTING_EVENT"
        else:
            event_id=db.execute("insert into task_events(task_id,at,kind,actor,data_json) values(?,?,?,?,?)",
                (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,ensure_ascii=False))).lastrowid
            action="CREATED_EVENT"
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()
    receipt=dict(action=action,event_id=event_id,task_id=TASK,**payload)
    if (HERE/"REGISTRY_RESULT.json").exists():
        old=json.loads((HERE/"REGISTRY_RESULT.json").read_text(encoding="utf8"))
        if {k:v for k,v in old.items() if k!="action"}!={k:v for k,v in receipt.items() if k!="action"}:
            raise RuntimeError("RECEIPT_CONFLICT")
    else:
        once(HERE/"REGISTRY_RESULT.json",json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")
    handoff=f"""# A43 verified handoff | 2026-10-26 | DESKTOP-M9L3I4M

## Work performed
Isolated synthetic finite-trip IT/HP/TES/REJECT Python reference and an executable Simulink MATLAB Function (Stateflow.EMChart) closed loop. No graphical Stateflow chart, hardware I/O, production changes or Codex/GPU workers. VRS skipped.

## Verification
18/18 Python tests PASS; 18,816 independent Decimal balance expressions.
MATLAB R2026a numerical CSV audit: 7x672=4,704 PASS.
Executable Simulink EMChart: 7x672=4,704 steps, 51,744 Python parity comparisons PASS.
First Simulink attempt failed From Workspace extrapolation; patched own build script and reran successfully.
SLX SHA256: {evidence['model_sha256']}
Python SHA256: {evidence['python_source_sha256']}
Evidence SHA256: {payload['evidence_sha256']}
Manifest SHA256: {payload['manifest_sha256']}
Model: {HERE/'DCHR_A43_Finite_Trip_Closed_Loop.slx'}
Report: {HERE/'ENGINEERING_REPORT_RU.md'}

## Findings
With synthetic 30-minute trip and 12% residual heat, complete REJECT failure reaches 67.804 C versus 30 C in ideal A42; 42 C model threshold exceeded. Physical release BLOCKED: assumed trip delay, residual heat, COP, heat capacity, REJECT ramp, compressor dynamics not measured.

## Registry and ownership
Existing task {TASK}; event {event_id} ({action}); card:
https://desktop-m9l3i4m.taila1c6bd.ts.net/?synapse_task={TASK}
Task remains review/planned, worker_pid=None. STOP absent in six checked scopes at {live['observed_at']}, not a recursive audit.
Live RAM free {live['ram_free_gib']} GiB; GPU {live['gpu_raw']} MiB/percent; MATLAB processes {live['matlab_process_count']}; Jarvice PID 11572 alive={live['jarvice_pid_11572_alive']}, scheduled state={live['jarvice_task_state']}; worktrees {live['worktrees']}.
SynapseMCP Web ping verified at {live['synapsemcp_web_ping_verified']}.

## Exact next step
A44 in isolated scope: add graphical Stateflow statechart and compressor HP ramp/lag, then 7x672 parity/transition QA; separately obtain real equipment parameters for physical validation. No hardware commands or shared GUI edits.
"""
    once(HERE/"FINAL_HANDOFF.md",handoff)
    print(json.dumps(dict(action=action,event_id=event_id,task_id=TASK,
        model_sha256=evidence["model_sha256"],
        evidence_sha256=payload["evidence_sha256"],
        handoff_sha256=sha(HERE/"FINAL_HANDOFF.md"),
        manifest_entries=len(manifest)),ensure_ascii=False))

if __name__=="__main__":
    main()
