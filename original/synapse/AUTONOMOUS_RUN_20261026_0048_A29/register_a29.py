"""Idempotent evidence registration in existing DataCenter task; no worker creation."""
from __future__ import annotations
import hashlib
import json
import sqlite3
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CENTER = HERE.parent.parent
TASK = "scc-3d9d172beb6e1b"
ACTOR = "chatgpt-dchr-a29-independent-heatmeter-holdout-20261026-0048"
FILES = (
    "holdout_heatmeter_gate.py", "test_holdout_heatmeter_gate.py",
    "independent_crosscheck.py", "VALIDACIA_TEPELNEHO_TOKU_SK.md",
    "TEST_LOG.txt", "INDEPENDENT_QA.json", "register_a29.py",
    "example_synthetic/cal.csv", "example_synthetic/cal_meta.json",
    "example_synthetic/cal_report.json", "example_synthetic/holdout.csv",
    "example_synthetic/holdout_meta.json", "example_synthetic/HOLDOUT_EVIDENCE.json",
)
FLAGS = ("STOP","STOP.flag","STOP.txt",".STOP","PAUSE","PAUSE.flag","PAUSE.txt",".PAUSE","STOP_MANAGED_WORKERS.txt")
ROOTS = (HERE, HERE.parent, CENTER, CENTER/"agent_knowledge",
         Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse"))

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def register():
    for root in ROOTS:
        for flag in FLAGS:
            if (root/flag).exists():
                raise RuntimeError("STOP_ACTIVE "+str(root/flag))
    for name in FILES:
        if not (HERE/name).is_file():
            raise RuntimeError("MISSING "+name)
    a28=HERE.parent/"AUTONOMOUS_RUN_20261025_2346_A28"
    old=json.loads((a28/"SHA256_MANIFEST.json").read_text(encoding="utf8"))
    if sha(a28/"field_calibration_gate.py")!=old["field_calibration_gate.py"]:
        raise RuntimeError("A28_SOURCE_CHANGED")
    log=(HERE/"TEST_LOG.txt").read_text(encoding="utf-8-sig")
    if "Ran 28 tests" not in log or not log.rstrip().endswith("OK"):
        raise RuntimeError("UNIT_TEST_NOT_PASS")
    qa=json.loads((HERE/"INDEPENDENT_QA.json").read_text(encoding="utf8"))
    report=json.loads((HERE/"example_synthetic/HOLDOUT_EVIDENCE.json").read_text(encoding="utf8"))
    if qa.get("status")!="PASS" or qa.get("checks")!=8 or qa.get("release_allowed") is not False:
        raise RuntimeError("INDEPENDENT_QA_FAIL")
    if report.get("source_class")!="SYNTHETIC_TEST" or report.get("release_allowed") is not False or report.get("sample_count")!=32:
        raise RuntimeError("SYNTHETIC_RELEASE_GUARD_FAIL")
    for key, file in (("calibration_report_sha256","cal_report.json"),
                      ("holdout_csv_sha256","holdout.csv"),
                      ("holdout_metadata_sha256","holdout_meta.json")):
        if report[key]!=sha(HERE/"example_synthetic"/file):
            raise RuntimeError("EVIDENCE_HASH_MISMATCH "+key)
    manifest={name:sha(HERE/name) for name in FILES}
    mf=HERE/"SHA256_MANIFEST.json"
    if mf.exists():
        if json.loads(mf.read_text(encoding="utf8"))!=manifest:
            raise RuntimeError("MANIFEST_CONFLICT")
    else:
        mf.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf8")
    payload={
        "scope":"isolated_A29_independent_heatmeter_holdout_and_A28_source_recomputation",
        "artifact_directory":str(HERE),
        "evidence_sha256":manifest["example_synthetic/HOLDOUT_EVIDENCE.json"],
        "source_code_sha256":manifest["holdout_heatmeter_gate.py"],
        "manifest_sha256":sha(mf),
        "a28_source_sha256":sha(a28/"field_calibration_gate.py"),
        "qa":"28/28 unit tests PASS; 8 independent finite-difference/energy/hash checks PASS; Python compilation PASS; 32 explicitly synthetic holdout points",
        "finding":"Independent meter holdout is time-disjoint from A28 calibration; raw A28 inputs and residual covariance independently recomputed; energy, bias, RMSE and pointwise propagated uncertainty cross-checked",
        "decision":"SYNTHETIC_ONLY_NOT_FIELD_VERIFIED; release_allowed=false",
        "limits":"No real paired sensor/reference measurements or independent heat-meter certificate; density/cp and meter uncertainty assumed; no physical release, SCADA or MATLAB production change",
        "next_step":"Acquire authenticated field calibration CSV and independent heat-meter holdout with verified certificate and separate interval; run A28/A29 and compare physics/uncertainty; retain fail-closed release",
    }
    with sqlite3.connect(CENTER/"tasks.sqlite3",timeout=5,isolation_level=None) as db:
        db.execute("PRAGMA busy_timeout=5000")
        if db.execute("PRAGMA quick_check").fetchone()[0]!="ok":
            raise RuntimeError("SQLITE_CHECK_FAILED")
        db.execute("BEGIN IMMEDIATE")
        try:
            state=db.execute("SELECT status,stage FROM tasks WHERE id=?",(TASK,)).fetchone()
            if state!=("review","planned"):
                raise RuntimeError("TASK_STATE_CHANGED "+repr(state))
            events=db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",(TASK,ACTOR)).fetchall()
            if len(events)>1:
                raise RuntimeError("DUPLICATE_EVENT")
            if events:
                if json.loads(events[0][1])!=payload:
                    raise RuntimeError("EVENT_PAYLOAD_CONFLICT")
                event_id,action=events[0][0],"EXISTING_EVENT"
            else:
                event_id=db.execute("INSERT INTO task_events(task_id,at,kind,actor,data_json) VALUES(?,?,?,?,?)",
                    (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,ensure_ascii=False))).lastrowid
                action="CREATED_EVENT"
            db.commit()
        except BaseException:
            db.rollback()
            raise
    result={"task_id":TASK,"event_id":event_id,"action":action,**payload}
    out=HERE/"REGISTRY_RESULT.json"
    if out.exists():
        previous=json.loads(out.read_text(encoding="utf8"))
        if {k:v for k,v in previous.items() if k!="action"}!={k:v for k,v in result.items() if k!="action"}:
            raise RuntimeError("REGISTRY_RESULT_CONFLICT")
    else:
        out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    return result

if __name__=="__main__":
    r=register()
    print(json.dumps({k:r[k] for k in ("task_id","event_id","action","evidence_sha256")}))
