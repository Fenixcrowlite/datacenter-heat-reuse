"""A44 fail-closed QA + one idempotent evidence event on an existing Synapse task."""
from __future__ import annotations
import hashlib
import json
import sqlite3
import subprocess
import sys
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CENTER = HERE.parent.parent
TASK = "scc-3d9d172beb6e1b"
ACTOR = "chatgpt-a44-graphical-stateflow-20261026-2050"
MODEL = "DCHR_A44_Graphical_Supervisor.slx"
CASES = ("nominal","short_fault","sustained_fault","interrupted_recovery")
FILES = ["reference_a44.py","test_a44.py","build_a44.m","finalize_a44.py",
         "REFERENCE_A44.json","MATLAB_A44_RESULT.json",MODEL,
         "MATLAB_RETRY_STDOUT.txt","MATLAB_RETRY_STDERR.txt"] + [
         "STIM_A44_" + x + ".csv" for x in CASES]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def put_once(path, text):
    if path.exists():
        if path.read_text(encoding="utf8") != text:
            raise RuntimeError("IMMUTABLE_ARTIFACT_CONFLICT " + str(path))
    else:
        path.write_text(text, encoding="utf8")

def main():
    for root in (CENTER,CENTER/"recovery",HERE,
                 HERE.parent/"AUTONOMOUS_RUN_20261026_1945_A43_FINITE_TRIP_RESIDUAL"):
        for flag in ("STOP","STOP.flag","PAUSE","PAUSE.flag",".STOP",".PAUSE"):
            if (root/flag).exists():
                raise RuntimeError("STOP_OR_PAUSE_ACTIVE " + str(root/flag))
    for f in FILES:
        if not (HERE/f).is_file():
            raise RuntimeError("MISSING_ARTIFACT " + f)
    result=json.loads((HERE/"MATLAB_A44_RESULT.json").read_text(encoding="utf8"))
    reference=json.loads((HERE/"REFERENCE_A44.json").read_text(encoding="utf8"))
    if (result["status"] != "A44_GRAPHICAL_STATEFLOW_PARITY_PASS" or
        result["comparisons"] != 5376 or result["state_count"] != 4 or
        result["transition_count"] != 7 or result["physical_release"] or
        result["hp_compressor_inertia_integrated"] or
        set(result["scenarios"]) != set(CASES) or reference["physical_release"]):
        raise RuntimeError("MATLAB_OR_RELEASE_GATE_FAILED")
    for case in CASES:
        if result["scenarios"][case]["samples"] != 672 or result["scenarios"][case]["mismatch"] != 0:
            raise RuntimeError("SCENARIO_PARITY_FAIL " + case)
    log=(HERE/"MATLAB_RETRY_STDOUT.txt").read_text(encoding="utf8")
    if "A44_ALL_PASS 5376" not in log or (HERE/"MATLAB_RETRY_STDERR.txt").stat().st_size:
        raise RuntimeError("MATLAB_LOG_NOT_PASS")
    with zipfile.ZipFile(HERE/MODEL) as z:
        if z.testzip() is not None:
            raise RuntimeError("SLX_CRC_ERROR")
        sf=[x for x in z.namelist() if x.startswith("simulink/stateflow/chart_") and x.endswith(".xml")]
        if len(sf)!=1:
            raise RuntimeError("NOT_GRAPHICAL_STATEFLOW")
        content=z.read(sf[0]).decode("utf8",errors="replace")
        for name in ("ACTIVE","TRIP_PENDING","TRIPPED","RAMPING"):
            if name not in content:
                raise RuntimeError("MISSING_GRAPHICAL_STATE " + name)
    py=subprocess.run([sys.executable,"-m","unittest","discover","-s",str(HERE),
                       "-p","test_a44.py","-q"],capture_output=True,text=True,timeout=25)
    if py.returncode or "Ran 8 tests" not in py.stderr or "OK" not in py.stderr:
        raise RuntimeError("PYTHON_QA_FAILED "+py.stderr[-2000:])
    report = """# A44: graphical Stateflow transition acceptance

This isolated Simulink SLX contains a real graphical Stateflow.Chart with four
states: ACTIVE, TRIP_PENDING, TRIPPED, RAMPING, and seven transitions including
the default transition. It was constructed and executed in MATLAB R2026a.

Four deterministic synthetic 672-sample sequences cover nominal operation,
a one-sample transient fault, sustained loss of capacity, and interrupted
recovery with repeated faults. The chart matched a separate Python reference
on all 5,376 state/alarm values. Eight Python regression tests pass.

A short transient is cancelled without shutdown. A sustained fault enters
TRIP_PENDING for two samples, then TRIPPED. Recovery requires qualification
and proceeds through RAMPING. This is a supervisor-only validation, not the
closed-loop heat balance from A43. The A43 model remains unchanged.

The first MATLAB attempt failed because Simulink From Workspace blocks did
not allow extrapolation. The isolated build was corrected to interpolate the
extended final sample; the second MATLAB run passed all cases.

IMPORTANT: all inputs and timings are synthetic. No compressor inertia,
HP ramp dynamics, real equipment I/O, measured shutdown latency, or safety
certification has been added. Physical release remains BLOCKED. The next
step is to integrate this chart with A43 thermal dynamics and implement an
energy-conserving compressor ramp/lag model, then repeat the seven A43 cases.
"""
    put_once(HERE/"ENGINEERING_REPORT_RU.md",report)
    evidence=dict(status="A44_GRAPHICAL_STATEFLOW_OPEN_LOOP_PARITY_PASS",
        physical_release=False,hardware_control=False,compressor_lag_integrated=False,
        model_sha256=sha(HERE/MODEL),model=str(HERE/MODEL),
        existing_task_id=TASK,comparisons=5376,scenarios=4,samples_per_scenario=672,
        state_count=4,transition_count=7,python_tests="8/8 PASS",
        upstream="A43 unchanged, not integrated",next_step="A45 connect graphical chart to A43 closed-loop thermal system; implement HP compressor startup lag with energy balances; rerun 7x672, independent QA")
    put_once(HERE/"EVIDENCE.json",json.dumps(evidence,indent=2,ensure_ascii=False)+"\n")
    manifest={f:sha(HERE/f) for f in FILES+["ENGINEERING_REPORT_RU.md","EVIDENCE.json"]}
    put_once(HERE/"SHA256_MANIFEST.json",json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
    payload=dict(scope="A44_isolated_graphical_stateflow_supervisor",
        artifact_directory=str(HERE),evidence_sha256=sha(HERE/"EVIDENCE.json"),
        manifest_sha256=sha(HERE/"SHA256_MANIFEST.json"),
        model_sha256=evidence["model_sha256"],
        qa="8/8 Python PASS; graphical Stateflow 4x672 samples; 5376/5376 state-alarm comparisons PASS",
        physical_release=False,compressor_lag_integrated=False,
        next_step=evidence["next_step"])
    db=sqlite3.connect(CENTER/"tasks.sqlite3",timeout=10,isolation_level=None)
    db.execute("pragma busy_timeout=10000")
    if db.execute("pragma quick_check").fetchone()[0]!="ok":
        raise RuntimeError("SQLITE_CHECK_FAILED")
    db.execute("begin immediate")
    try:
        task=db.execute("select status,stage,worker_pid,owner from tasks where id=?",(TASK,)).fetchone()
        if task!=("review","planned",None,"MATLAB/Stateflow QA"):
            raise RuntimeError("TASK_OWNERSHIP_CHANGED "+repr(task))
        events=db.execute("select id,data_json from task_events where task_id=? and actor=? and kind='evidence'",
                          (TASK,ACTOR)).fetchall()
        if len(events)>1:
            raise RuntimeError("DUPLICATE_EVENTS")
        if events:
            if json.loads(events[0][1])!=payload:
                raise RuntimeError("EVENT_CONFLICT")
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
    receipt=dict(event_id=event_id,task_id=TASK,**payload)
    put_once(HERE/"REGISTRY_RESULT.json",json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")
    handoff=f"""# A44 verified handoff | DESKTOP-M9L3I4M

A44 graphical Stateflow.Chart: 4 states, 7 transitions, isolated Simulink model.
MATLAB R2026a four scenarios x 672 intervals: 5376/5376 output comparisons PASS.
Python regression: 8/8 PASS. ZIP Stateflow chart and CRC independently checked.
First MATLAB run failed due to From Workspace extrapolation; fixed in owned script.
Synthetic, supervisor-only, not A43 closed-loop integration, no compressor lag or hardware I/O.

Model: {HERE/MODEL}
Model SHA256: {evidence["model_sha256"]}
Evidence SHA256: {payload["evidence_sha256"]}
Manifest SHA256: {payload["manifest_sha256"]}
Synapse existing task: {TASK}, event {event_id} ({action})
Card: https://desktop-m9l3i4m.taila1c6bd.ts.net/?synapse_task={TASK}
STOP exact flags absent in checked scopes during registration.
No new Codex/GPU worker or card; VRS excluded; shared GUI and production unchanged.
Next step: {evidence["next_step"]}
"""
    put_once(HERE/"FINAL_HANDOFF.md",handoff)
    print(json.dumps(dict(action=action,event_id=event_id,task_id=TASK,
        model_sha256=evidence["model_sha256"],
        evidence_sha256=payload["evidence_sha256"],
        manifest_sha256=payload["manifest_sha256"],
        handoff_sha256=sha(HERE/"FINAL_HANDOFF.md"),
        files=len(manifest)),ensure_ascii=False))

if __name__=="__main__":
    main()
