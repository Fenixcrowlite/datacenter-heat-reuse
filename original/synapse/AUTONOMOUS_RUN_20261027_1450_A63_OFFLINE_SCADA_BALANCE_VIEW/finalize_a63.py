"""A63 finalizer: fresh QA, immutable evidence, SHA manifest and idempotent existing-task event."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import time

D=Path(__file__).resolve().parent
CENTER=D.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-a63-offline-scada-balance-20261027-1450"
A62=D.parent/"AUTONOMOUS_RUN_20261027_1405_A62_SIGNED_LOSS_EXPORT"
FILES=("a63_offline_dashboard.py","test_a63.py","independent_qa_a63.py",
       "browser_smoke_a63.py","finalize_a63.py","A63_ANALYSIS_CONTRACT_SK.md",
       "QA_A63_CLEAN.txt","QA_SCRIPT_A63.js","INDEPENDENT_QA_A63.json",
       "BROWSER_QA_A63.json","OUTPUT/dashboard.html","OUTPUT/metrics.json",
       "OUTPUT/sources.json","EVIDENCE_A63.json")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def once(path, text):
    if path.exists():
        if path.read_text(encoding="utf-8") != text:
            raise RuntimeError("IMMUTABLE_ARTIFACT_CONFLICT:"+str(path))
    else:
        path.write_text(text,encoding="utf-8")


def guard():
    for root in (CENTER,CENTER.parent/"temp_coding",CENTER.parent/"EduMotionPipeline"):
        for name in ("STOP","PAUSE","STOP.flag","PAUSE.flag"):
            if (root/name).exists():
                raise RuntimeError("STOP_OR_PAUSE:"+str(root/name))


def run(script):
    p=subprocess.run([sys.executable,script],cwd=D,text=True,capture_output=True,timeout=40)
    if p.returncode:
        raise RuntimeError(script+": "+p.stdout[-600:]+p.stderr[-1000:])
    return p.stdout.strip()


def main():
    guard()
    assert A62.is_dir()
    unit=subprocess.run([sys.executable,"-m","unittest","-v","test_a63"],
                        cwd=D,capture_output=True,text=True,timeout=40)
    if unit.returncode or not re.search(r"Ran 11 tests in [0-9.]+s",unit.stderr) or "\nOK" not in unit.stderr:
        raise RuntimeError("UNIT_TESTS_FAILED:"+unit.stderr[-1000:])
    clean=re.sub(r"Ran 11 tests in [0-9.]+s","Ran 11 tests in <variable>s",unit.stderr)
    once(D/"QA_A63_CLEAN.txt",clean)
    independent=json.loads(run("independent_qa_a63.py"))
    browser=json.loads(run("browser_smoke_a63.py"))
    assert independent["decimal_checks"]==12102 and browser["cards_rendered"]==6
    assert browser["svg_polylines"]==7
    report=json.loads((D/"INDEPENDENT_QA_A63.json").read_text(encoding="utf-8"))
    assert report["qa"]=="PASS" and report["node_js_syntax"]=="PASS"
    assert report["source_kind"]=="derived_simulation" and report["physical_release"] is False
    assert report["dashboard_sha256"]==sha(D/"OUTPUT/dashboard.html")
    evidence={
        "scope":"A63_offline_SCADA_signed_loss_energy_dashboard",
        "task_id":TASK,"artifact_directory":str(D),
        "dashboard":str(D/"OUTPUT/dashboard.html"),
        "status":"VERIFIED_SYNTHETIC_OFFLINE_VIEW",
        "unit_tests":"11/11 PASS",
        "independent_decimal_checks":"12102/12102 PASS",
        "node_js_syntax":"PASS","headless_chrome":"6 cards, 7 SVG polylines PASS",
        "source_kind":"derived_simulation","physical_release":False,
        "upstream_files_modified":False,
        "a62_v08_sha256":sha(A62/"OUTPUT_V08_SIGNED/analysis_with_signed_losses.csv"),
        "a62_v09_sha256":sha(A62/"OUTPUT_V09_SIGNED/analysis_with_signed_losses.csv"),
        "next_step":"Add an isolated explicit A60 trapezoid vs A62 discrete integration comparison to the offline view; acquire real calibrated telemetry before physical acceptance."
    }
    once(D/"EVIDENCE_A63.json",json.dumps(evidence,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    manifest={name:sha(D/name) for name in FILES}
    once(D/"SHA256_MANIFEST_A63.json",json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    handoff=(
        "# A63 offline SCADA energy dashboard | "+datetime.now().astimezone().isoformat(timespec="seconds")+"\n"
        "Primary SynapseMCP Web live; STOP/PAUSE checked; existing DataCenter task review/planned, no task worker.\n"
        "New isolated self-contained OUTPUT/dashboard.html with two scenario selectors and 3 SVG plots (temperature, signed heat flows, discrete energy).\n"
        "Actual A62 v08/v09 inputs: 672 rows each; 91 negative signed-loss samples each, correctly interpreted as ambient heat gain.\n"
        "QA: 11/11 unit tests, 12102/12102 independent Decimal-to-HTML field checks, Node syntax PASS, isolated headless Chrome 6 metric cards + 7 SVG curves PASS.\n"
        "Source kind DERIVED_SIMULATION, physical_release=false. No physical certification or real telemetry.\n"
        "No Codex, new workers, GPU tasks, shared GUI changes, STOP/OAuth changes, VRS or foreign-branch edits.\n"
        "Evidence SHA256: "+sha(D/"EVIDENCE_A63.json")+"\n"
        "Manifest SHA256: "+sha(D/"SHA256_MANIFEST_A63.json")+"\n"
        "NEXT: "+evidence["next_step"]+"\n"
    )
    if not (D/"FINAL_HANDOFF.md").exists():
        once(D/"FINAL_HANDOFF.md",handoff)
    payload={
        "scope":evidence["scope"],"artifact_directory":str(D),
        "dashboard":evidence["dashboard"],
        "evidence_sha256":sha(D/"EVIDENCE_A63.json"),
        "manifest_sha256":sha(D/"SHA256_MANIFEST_A63.json"),
        "handoff_sha256":sha(D/"FINAL_HANDOFF.md"),
        "QA":"11/11 unittest; 12102/12102 independent Decimal; Node syntax; Chrome 6 cards/7 curves",
        "source_kind":"derived_simulation","physical_release":False,
        "next_step":evidence["next_step"]
    }
    guard()
    db=sqlite3.connect(CENTER/"tasks.sqlite3",timeout=15,isolation_level=None)
    db.execute("PRAGMA busy_timeout=15000")
    if db.execute("PRAGMA quick_check").fetchone()[0]!="ok":
        raise RuntimeError("REGISTRY_INTEGRITY_FAILED")
    db.execute("BEGIN IMMEDIATE")
    try:
        state=db.execute("SELECT status,stage,worker_pid FROM tasks WHERE id=?",(TASK,)).fetchone()
        if state!=("review","planned",None):
            raise RuntimeError("TASK_STATE_CHANGED:"+repr(state))
        found=db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND actor=? AND kind='evidence'",
                         (TASK,ACTOR)).fetchall()
        if len(found)>1:
            raise RuntimeError("DUPLICATE_EVENT")
        if found:
            if json.loads(found[0][1])!=payload:
                raise RuntimeError("EVENT_CONFLICT")
            event_id=found[0][0]
        else:
            event_id=db.execute("INSERT INTO task_events(task_id,at,kind,actor,data_json) VALUES(?,?,?,?,?)",
                                (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,ensure_ascii=False))).lastrowid
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()
    once(D/"REGISTRY_RESULT_A63.json",json.dumps({"event_id":event_id,"task_id":TASK,**payload},
                                                 ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"event_id":event_id,"evidence_sha256":payload["evidence_sha256"],
                      "handoff_sha256":payload["handoff_sha256"],"manifest_entries":len(manifest)}))


if __name__=="__main__":
    main()
