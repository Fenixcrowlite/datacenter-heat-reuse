"""A42 idempotent evidence append to EXISTING Synapse task; no worker creation."""
from __future__ import annotations
import hashlib,json,sqlite3,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
CENTER=HERE.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-a42-coupled-failsafe-20261026-1850"
SCENARIOS=("both","main_only","backup_only","neither")
COUNTER=("both","backup_only","neither")
FILES=["coupled_a42.py","counterfactual_a42.py","test_a42.py","validate_a42.m",
 "RESULTS_A42.json","COUNTERFACTUAL_A42.json","MATLAB_AUDIT_A42.json",
 "RUN_STDOUT.txt","COUNTERFACTUAL_STDOUT.txt","QA_CLEAN_STDERR.txt",
 "QA_CLEAN_STDOUT.txt","MATLAB_STDOUT.txt","MATLAB_STDERR.txt",
 "ENGINEERING_REPORT_RU.md"]+["TRACE_A42_"+s+".csv" for s in SCENARIOS]+[
 "TRACE_A42_COUNTERFACTUAL_"+s+".csv" for s in COUNTER]+["register_a42.py"]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save_once(path,text):
    if path.exists():
        if path.read_text(encoding="utf8")!=text:raise RuntimeError("EXISTING_FILE_CONFLICT "+str(path))
    else:path.write_text(text,encoding="utf8")

def main():
    for root in (CENTER,CENTER/"recovery",HERE):
        for name in ("STOP","STOP.flag","PAUSE","PAUSE.flag",".STOP","STOP_MANAGED_WORKERS.txt"):
            if (root/name).exists():raise RuntimeError("STOP_ACTIVE "+str(root/name))
    for n in FILES:
        if not (HERE/n).is_file():raise RuntimeError("MISSING "+n)
    qa=(HERE/"QA_CLEAN_STDERR.txt").read_text(encoding="utf8")
    if "Ran 14 tests" not in qa or not qa.rstrip().endswith("OK"):
        raise RuntimeError("QA_NOT_PASS")
    matlab=(HERE/"MATLAB_STDOUT.txt").read_text(encoding="utf8")
    if "A42_MATLAB_ALL_PASS 4704" not in matlab:
        raise RuntimeError("MATLAB_NOT_PASS")
    if (HERE/"MATLAB_STDERR.txt").stat().st_size:
        raise RuntimeError("MATLAB_STDERR_NONEMPTY")
    audit=json.loads((HERE/"MATLAB_AUDIT_A42.json").read_text(encoding="utf8"))
    if audit["status"]!="MATLAB_INDEPENDENT_NUMERIC_AUDIT_PASS" or audit["samples"]!=4704 or audit["matlab_simulink_model_built"]:
        raise RuntimeError("AUDIT_INVALID")
    result=json.loads((HERE/"RESULTS_A42.json").read_text(encoding="utf8"))
    if result["physical_release_allowed"] or result["hardware_control"] or len(result["cases"])!=4:
        raise RuntimeError("MODEL_RELEASE_INVALID")
    cf=json.loads((HERE/"COUNTERFACTUAL_A42.json").read_text(encoding="utf8"))
    if cf["cases"]["neither"]["fault_period_unmet_kWh"]<10000:
        raise RuntimeError("COUNTERFACTUAL_MISSING_SHORTFALL")
    source=HERE.parent/"AUTONOMOUS_RUN_20261026_1751_A41_CLOSED_LOOP_SIM"/"INPUTS_A41.csv"
    if sha(source)!=result["a41_input_sha256"]:
        raise RuntimeError("SOURCE_CHANGED")
    evidence=dict(status="SYNTHETIC_COUPLED_PYTHON_AND_MATLAB_NUMERIC_AUDIT_PASS",
      physical_release_allowed=False,hardware_control=False,
      artifact_directory=str(HERE),existing_task_id=TASK,
      source_a41_input_sha256=sha(source),python_source_sha256=sha(HERE/"coupled_a42.py"),
      matlab_validator_sha256=sha(HERE/"validate_a42.m"),
      matlab_audit_sha256=sha(HERE/"MATLAB_AUDIT_A42.json"),
      report_sha256=sha(HERE/"ENGINEERING_REPORT_RU.md"),
      qa="14/14 Python unittest PASS; 10752 Decimal balance expressions; MATLAB R2026a 7x672=4704 rows PASS",
      cases=4,counterfactual_cases=3,sensitivity_cases=9,
      caveat="Synthetic reference, no A42 Simulink/Stateflow model; ideal IT trip, unverified COP/equipment, physical release blocked",
      next_step="A43 isolated Simulink/Stateflow model, finite IT trip delay and residual heat, 7x672 Python/MATLAB parity; source equipment parameters")
    save_once(HERE/"EVIDENCE.json",json.dumps(evidence,ensure_ascii=False,indent=2)+"\n")
    manifest={n:sha(HERE/n) for n in FILES+["EVIDENCE.json"]}
    save_once(HERE/"SHA256_MANIFEST.json",json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    payload=dict(scope="A42_isolated_coupled_IT_HP_TES_REJECT_failsafe",
      artifact_directory=str(HERE),evidence_sha256=sha(HERE/"EVIDENCE.json"),
      manifest_sha256=sha(HERE/"SHA256_MANIFEST.json"),
      qa=evidence["qa"],status=evidence["status"],
      physical_release_allowed=False,caveat=evidence["caveat"],next_step=evidence["next_step"])
    db=sqlite3.connect(CENTER/"tasks.sqlite3",timeout=10,isolation_level=None)
    db.execute("pragma busy_timeout=10000")
    if db.execute("pragma quick_check").fetchone()[0]!="ok":raise RuntimeError("SQLITE_CORRUPT")
    db.execute("begin immediate")
    try:
        state=db.execute("select status,stage,worker_pid,owner from tasks where id=?",(TASK,)).fetchone()
        if state!=("review","planned",None,"MATLAB/Stateflow QA"):
            raise RuntimeError("TASK_OWNERSHIP_CHANGED "+str(state))
        existing=db.execute("select id,data_json from task_events where task_id=? and actor=? and kind='evidence'",(TASK,ACTOR)).fetchall()
        if len(existing)>1:raise RuntimeError("DUPLICATE_EVENTS")
        if existing:
            if json.loads(existing[0][1])!=payload:raise RuntimeError("EVENT_CONFLICT")
            event_id,action=existing[0][0],"EXISTING_EVENT"
        else:
            event_id=db.execute("insert into task_events(task_id,at,kind,actor,data_json) values(?,?,?,?,?)",
                (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,ensure_ascii=False))).lastrowid
            action="CREATED_EVENT"
        db.commit()
    except BaseException:
        db.rollback();raise
    finally:db.close()
    receipt=dict(action=action,event_id=event_id,task_id=TASK,**payload)
    if (HERE/"REGISTRY_RESULT.json").exists():
        old=json.loads((HERE/"REGISTRY_RESULT.json").read_text(encoding="utf8"))
        if {k:v for k,v in old.items() if k!="action"}!={k:v for k,v in receipt.items() if k!="action"}:
            raise RuntimeError("RECEIPT_CONFLICT")
    else:save_once(HERE/"REGISTRY_RESULT.json",json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
    handoff=f"""# A42 verified handoff | 2026-10-26 | DESKTOP-M9L3I4M

## What changed
Created isolated Python coupled IT/HP/TES/REJECT simulator with idealized zero-capacity IT trip, sensor-lag/thermal-mass sensitivity and counterfactual pool/DH loads. No production edits or new worker. VRS skipped.

## Verified evidence
Python unittest 14/14 PASS; 10,752 independent Decimal balance expressions.
MATLAB R2026a independent CSV numerical audit 7x672=4,704 samples PASS; no new SLX built.
A41 source input SHA256: {sha(source)}
A42 Python source SHA256: {sha(HERE/'coupled_a42.py')}
MATLAB audit SHA256: {sha(HERE/'MATLAB_AUDIT_A42.json')}
Evidence SHA256: {payload['evidence_sha256']}
Manifest SHA256: {payload['manifest_sha256']}
Report: {HERE/'ENGINEERING_REPORT_RU.md'}
Existing Synapse task: {TASK}, event {event_id}, action {action}.
Card: https://desktop-m9l3i4m.taila1c6bd.ts.net/?synapse_task={TASK}

## Findings
Full REJECT loss with ideal IT trip has no simulated IT overheating but halts IT; counterfactual pool 60 kW + district 100 kW incurs 11,520 kWh unmet over 72 h.
Cold standby B (30 min) still reaches 42.62 C, exceeding assumed 42 C threshold; NOT a safety approval.
Physical validation BLOCKED: COP, REJECT ratings, thermal inertia, real trip delay and residual heat unverified.

## Safety and ownership
Read AGENTS, INDEX, personal kernel and 2026-10-21 night handoff. SynapseMCP Web authenticated and enabled. STOP checked in scoped roots before write and registry commit. Registry status remains review/planned, no worker PID. No Codex, GPU, OAuth, GUI, VRS or other owners modified.

## Exact next step
A43: isolated MATLAB/Simulink/Stateflow finite-trip-latency model, residual IT heat and compressor/REJECT dynamics; compare 7x672 traces to independent Python reference and report threshold excursions. Do not touch production model or issue hardware commands.
"""
    save_once(HERE/"FINAL_HANDOFF.md",handoff)
    print(json.dumps(dict(action=action,event_id=event_id,task_id=TASK,
      evidence_sha256=payload["evidence_sha256"],
      handoff_sha256=sha(HERE/"FINAL_HANDOFF.md"),
      manifest_entries=len(manifest)),ensure_ascii=False))

if __name__=="__main__":main()
