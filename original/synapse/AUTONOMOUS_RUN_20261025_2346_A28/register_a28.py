"""Idempotent, fail-closed A28 evidence event in existing DataCenter card."""
from __future__ import annotations
import hashlib
import json
import sqlite3
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
CENTER=HERE.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-dchr-a28-field-calibration-gate-20261025-2346"
FILES=(
    "field_calibration_gate.py","test_field_calibration_gate.py",
    "independent_crosscheck.py","FIELD_CALIBRATION_PROTOCOL_SK.md",
    "FIELD_GATE_EVIDENCE.json","INDEPENDENT_QA.json","TEST_LOG.txt",
    "example_synthetic/paired.csv","example_synthetic/metadata.json",
    "register_a28.py",
)
FLAGS=("STOP","STOP.flag","STOP.txt",".STOP","PAUSE","PAUSE.flag",
       "PAUSE.txt",".PAUSE","STOP_MANAGED_WORKERS.txt")
ROOTS=(HERE,HERE.parent,CENTER,CENTER/"agent_knowledge",
       Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def register():
    for root in ROOTS:
        for flag in FLAGS:
            if (root/flag).exists():
                raise RuntimeError("STOP_ACTIVE "+str(root/flag))
    for name in FILES:
        if not (HERE/name).is_file():
            raise RuntimeError("MISSING "+name)
    log=(HERE/"TEST_LOG.txt").read_text(encoding="utf-8-sig")
    if "Ran 23 tests" not in log or not log.rstrip().endswith("OK"):
        raise RuntimeError("UNIT_TEST_NOT_PASS")
    report=json.loads((HERE/"FIELD_GATE_EVIDENCE.json").read_text(encoding="utf8"))
    qa=json.loads((HERE/"INDEPENDENT_QA.json").read_text(encoding="utf8"))
    if (report["source_class"]!="SYNTHETIC_TEST" or report["release_allowed"]
        or report["sample_count"]!=32 or qa["status"]!="PASS" or qa["checks"]!=16
        or qa["field_calibration_verified"]):
        raise RuntimeError("EVIDENCE_NOT_FAIL_CLOSED")
    if report["csv_sha256"]!=sha(HERE/"example_synthetic/paired.csv"):
        raise RuntimeError("SOURCE_CSV_CHANGED")
    if report["metadata_sha256"]!=sha(HERE/"example_synthetic/metadata.json"):
        raise RuntimeError("METADATA_CHANGED")
    a27=HERE.parent/"AUTONOMOUS_RUN_20261025_2252_A27"/"metrology_psd_hardening.py"
    if qa["a27_sha256"]!=sha(a27):
        raise RuntimeError("A27_CHANGED")
    manifest={name:sha(HERE/name) for name in FILES}
    mf=HERE/"SHA256_MANIFEST.json"
    if mf.exists():
        if json.loads(mf.read_text(encoding="utf8"))!=manifest:
            raise RuntimeError("MANIFEST_CONFLICT")
    else:
        mf.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf8")
    payload={
        "scope":"isolated_A28_field_calibration_residual_covariance_readiness_gate",
        "artifact_directory":str(HERE),
        "evidence_sha256":manifest["FIELD_GATE_EVIDENCE.json"],
        "source_code_sha256":manifest["field_calibration_gate.py"],
        "manifest_sha256":sha(mf),
        "qa":"23/23 unit tests PASS, 16 independent checks PASS, py_compile PASS, 32 synthetic paired readings",
        "finding":"Operational covariance cannot identify sensor-error covariance; new fail-closed intake requires paired reference readings and certificate hashes, separates residual bias from variability",
        "decision":"SYNTHETIC_ONLY_NOT_FIELD_VERIFIED; release_allowed=false",
        "limits":"Only synthetic fixture; certificate file SHA is not issuer authentication; no field measurements, production edits or SCADA control",
        "next_step":"Obtain traceable matched field reference measurements, independently authenticate calibration, evaluate holdout heat-meter agreement; owner-review A27 PSD integration",
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
            existing=db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",
                                (TASK,ACTOR)).fetchall()
            if len(existing)>1: raise RuntimeError("DUPLICATE_EVENT")
            if existing:
                if json.loads(existing[0][1])!=payload:
                    raise RuntimeError("EVENT_PAYLOAD_CONFLICT")
                event_id,action=existing[0][0],"EXISTING_EVENT"
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
        if json.loads(out.read_text(encoding="utf8"))!=result:
            raise RuntimeError("REGISTRY_RESULT_CONFLICT")
    else:
        out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    return result


if __name__=="__main__":
    r=register()
    print(json.dumps({k:r[k] for k in ("task_id","event_id","action","evidence_sha256")}))
