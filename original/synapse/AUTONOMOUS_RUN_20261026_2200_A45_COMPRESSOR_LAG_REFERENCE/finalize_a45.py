"""Idempotent DataCenter A45 evidence in existing Synapse task."""
import hashlib
import json
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
CENTER=HERE.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-a45-dchr-compressor-lag-reference-20261026"
SCENARIOS=("both","main_only","backup_only","neither",
           "CF_both","CF_backup_only","CF_neither")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def once(p,s):
    if p.exists():
        if p.read_text(encoding="utf8")!=s:raise RuntimeError("ARTIFACT_CONFLICT "+str(p))
    else:p.write_text(s,encoding="utf8")

def main():
    scopes=(CENTER,CENTER/"recovery",HERE,
            Path(r"C:\Users\Lysda\Desktop\temp_coding"),
            Path(r"C:\Users\Lysda\Desktop\temp_coding\telegram_codex_bot"),
            Path(r"C:\Users\Lysda\Desktop\temp_coding\telegram_codex_bot\logs"))
    for root in scopes:
        for flag in ("STOP","STOP.flag","PAUSE","PAUSE.flag",".STOP",".PAUSE","devteam-daemon.stop"):
            if (root/flag).exists():raise RuntimeError("STOP_ACTIVE "+str(root/flag))
    run=subprocess.run([sys.executable,"-m","unittest","discover","-s",str(HERE),
                        "-p","test_a45.py","-q"],capture_output=True,text=True,timeout=30)
    if run.returncode or "Ran 12 tests" not in run.stderr or "OK" not in run.stderr:
        raise RuntimeError("UNITTEST_FAIL "+run.stderr)
    from verify_a45 import audit
    decimal=audit()
    if decimal["balance_checks"]!=18816:raise RuntimeError("DECIMAL_COUNT_MISMATCH")
    report=json.loads((HERE/"RESULTS_A45.json").read_text(encoding="utf8"))
    if len(report["cases"])!=7:raise RuntimeError("SCENARIOS_MISSING")
    for case in SCENARIOS:
        if report["cases"][case]["sha256"]!=sha(HERE/("TRACE_A45_"+case+".csv")):
            raise RuntimeError("TRACE_SHA_MISMATCH "+case)
    text="""# DataCenter A45 | synthetic HP compressor source-capacity lag

A new Python-only isolated coupled reference extends A43 finite-trip thermal
simulation with first-order startup/ramp dynamics of available heat-pump
evaporator extraction. The recurrence is exact for zero-order-held targets:
C[k+1] = C[k] + (1-exp(-900/tau))*(Qtarget[k]-C[k]).
Actual HP extraction is min(Qtarget, C[k+1]). Compressor electricity and
condenser heat are recalculated from actual extraction and synthetic COP.
TES, IT, REJECT and user balances are recomputed, not patched post-hoc.

Seven synthetic 672-step scenarios completed; 12/12 Python tests PASS;
18,816 independent Decimal balance checks PASS across 4,704 intervals.
Tau=0 reproduces A43 for 3 tested scenarios/115 samples each.
This is a reference model only, NOT A45 Simulink integration and NOT
physical compressor identification. Compressor internal thermal storage,
coastdown electricity and real HP minimum-on/off limits remain absent.
Physical release BLOCKED; all parameters assumed.

Next: wire A44 graphical chart to this closed-loop reference in a new
isolated Simulink model, implement equivalent HP lag there, compare
7x672 trajectories and transitions, and independently QA any divergence.
"""
    once(HERE/"ENGINEERING_REPORT_RU.md",text)
    evidence=dict(status="A45_PYTHON_COMPRESSOR_LAG_REFERENCE_QA_PASS",
                  task_id=TASK,physical_release=False,simulink_integrated=False,
                  matlab_executed=False,scenarios=7,steps_per_scenario=672,
                  python_tests="12/12 PASS",decimal_balance_checks=18816,
                  max_temp_C={n:report["cases"][n]["max_temperature_C"] for n in SCENARIOS},
                  upstream_a43_sha256="7e2cf8fe09b11ae923726e088825bf73477583e1c2e8888bb42987b130d73af2",
                  next_step="A46 isolated Simulink graphical Stateflow + HP lag integration and 7x672 parity")
    once(HERE/"EVIDENCE.json",json.dumps(evidence,indent=2,ensure_ascii=False)+"\n")
    files=("compressor_a45.py","finite_trip_a45.py","prepare_a45.py","test_a45.py",
           "verify_a45.py","finalize_a45.py","RESULTS_A45.json","DECIMAL_AUDIT_A45.json",
           "ENGINEERING_REPORT_RU.md","EVIDENCE.json",*("TRACE_A45_"+x+".csv" for x in SCENARIOS))
    manifest={name:sha(HERE/name) for name in files}
    once(HERE/"SHA256_MANIFEST.json",json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
    payload=dict(scope="DCHR_A45_python_compressor_lag_coupled_reference",
                 artifact_directory=str(HERE),evidence_sha256=sha(HERE/"EVIDENCE.json"),
                 manifest_sha256=sha(HERE/"SHA256_MANIFEST.json"),
                 qa="12/12 unittest PASS; 18816 Decimal checks PASS; 7x672 synthetic",
                 physical_release=False,simulink_integrated=False,
                 next_step=evidence["next_step"])
    db=sqlite3.connect(CENTER/"tasks.sqlite3",timeout=10,isolation_level=None)
    db.execute("PRAGMA busy_timeout=10000")
    if db.execute("PRAGMA quick_check").fetchone()[0]!="ok":raise RuntimeError("DB_BAD")
    db.execute("BEGIN IMMEDIATE")
    try:
        row=db.execute("select status,stage,worker_pid from tasks where id=?",(TASK,)).fetchone()
        if row!=("review","planned",None):raise RuntimeError("OWNERSHIP_CHANGED "+repr(row))
        old=db.execute("select id,data_json from task_events where task_id=? and actor=? and kind='evidence'",
                       (TASK,ACTOR)).fetchall()
        if len(old)>1:raise RuntimeError("DUPLICATE")
        if old:
            if json.loads(old[0][1])!=payload:raise RuntimeError("EVENT_PAYLOAD_CONFLICT")
            eid=old[0][0]
        else:
            eid=db.execute("insert into task_events(task_id,at,kind,actor,data_json) values(?,?,?,?,?)",
                           (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,ensure_ascii=False))).lastrowid
        db.commit()
    except BaseException:
        db.rollback();raise
    finally:db.close()
    receipt=dict(event_id=eid,task_id=TASK,**payload)
    once(HERE/"REGISTRY_RESULT.json",json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")
    handoff=f"""# DataCenter A45 handoff

Python coupled HP source-lag model, 7 x 672 scenarios, 12/12 tests and
18,816 Decimal checks PASS. NO Simulink/Stateflow integration in A45.
Existing task {TASK}, evidence event {eid}.
Evidence SHA256: {payload['evidence_sha256']}
Manifest SHA256: {payload['manifest_sha256']}
Next: {evidence['next_step']}
"""
    once(HERE/"FINAL_HANDOFF.md",handoff)
    print(json.dumps(dict(event_id=eid,task_id=TASK,evidence_sha256=payload["evidence_sha256"],
                          manifest_sha256=payload["manifest_sha256"],
                          handoff_sha256=sha(HERE/"FINAL_HANDOFF.md"),qa="PASS")))

if __name__=="__main__":main()
