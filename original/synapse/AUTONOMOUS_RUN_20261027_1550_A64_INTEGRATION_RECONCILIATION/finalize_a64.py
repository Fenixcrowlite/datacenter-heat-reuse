"""A64 reproducible finalizer: QA -> evidence -> manifest -> handoff -> existing task event."""
from datetime import datetime
import hashlib,json,re,sqlite3,subprocess,sys,time
from pathlib import Path
D=Path(__file__).resolve().parent
CENTER=D.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-a64-integration-reconciliation-20261027-1550"
FILES=("a64_reconcile.py","test_a64.py","independent_qa_a64.py","finalize_a64.py",
       "A64_TECHNICKY_PROTOKOL_SK.md","QA_A64_CLEAN.txt","INDEPENDENT_QA_A64.json",
       "OUTPUT/comparison.json","OUTPUT/comparison.html","EVIDENCE_A64.json")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def once(p,data):
    if p.exists():
        if p.read_text(encoding="utf-8")!=data:raise RuntimeError("IMMUTABLE_ARTIFACT_CONFLICT:"+str(p))
    else:p.write_text(data,encoding="utf-8")
def guard():
    for root in (CENTER,CENTER.parent/"temp_coding",CENTER.parent/"EduMotionPipeline",CENTER/"recovery",D):
        for name in ("STOP","PAUSE","STOP.flag","PAUSE.flag"):
            if (root/name).exists():raise RuntimeError("STOP_PAUSE:"+str(root/name))
def run(args):
    p=subprocess.run([sys.executable,*args],cwd=D,capture_output=True,text=True,timeout=45)
    if p.returncode:raise RuntimeError("QA_FAILED "+repr(args)+" "+p.stdout[-800:]+p.stderr[-1200:])
    return p
def main():
    guard()
    pre={v:json.loads((D/"OUTPUT/comparison.json").read_text(encoding="utf-8"))["scenarios"][v]["a60_csv_sha256"] for v in ("V08","V09")}
    assert len(pre)==2
    run(["a64_reconcile.py"])
    u=run(["-m","unittest","-v","test_a64"])
    if not re.search(r"Ran 12 tests in [0-9.]+s",u.stderr) or "\nOK" not in u.stderr:
        raise RuntimeError("UNEXPECTED_UNIT_OUTPUT")
    clean=re.sub(r"Ran 12 tests in [0-9.]+s","Ran 12 tests in <variable>s",u.stderr)
    once(D/"QA_A64_CLEAN.txt",clean)
    qa=run(["independent_qa_a64.py"])
    independent=json.loads(qa.stdout)
    assert independent["status"]=="PASS" and independent["decimal_checks"]==8107
    assert independent["html_sha256"]==sha(D/"OUTPUT/comparison.html")
    report=json.loads((D/"OUTPUT/comparison.json").read_text(encoding="utf-8"))
    assert all(report["scenarios"][v]["a60_csv_sha256"]==pre[v] for v in pre)
    for v in pre:
        x=report["scenarios"][v]
        assert x["source_kind"]=="derived_simulation" and x["physical_release"] is False
    evidence={
      "scope":"A64_A60_trapezoid_vs_A62_discrete_reconciliation",
      "task_id":TASK,"artifact_directory":str(D),
      "report_html":str(D/"OUTPUT/comparison.html"),
      "source_kind":"derived_simulation","physical_release":False,
      "status":"VERIFIED_SYNTHETIC_NUMERICAL_COMPARISON",
      "unit_tests":"12/12 PASS","independent_decimal_checks":"8107/8107 PASS",
      "a60_v08_sha256":pre["V08"],"a60_v09_sha256":pre["V09"],
      "a62_v08_sha256":report["scenarios"]["V08"]["a62_csv_sha256"],
      "a62_v09_sha256":report["scenarios"]["V09"]["a62_csv_sha256"],
      "pool_delta_v08_kWh":report["scenarios"]["V08"]["channels"]["Q_pool_W"]["discrete_minus_trapezoid_kWh"],
      "pool_delta_v09_kWh":report["scenarios"]["V09"]["channels"]["Q_pool_W"]["discrete_minus_trapezoid_kWh"],
      "upstream_files_modified":False,
      "next_step":"Use the isolated A64 report alongside A63; obtain calibrated physical telemetry and verify UTC/channel identity before A55-A58 physical acceptance."
    }
    once(D/"EVIDENCE_A64.json",json.dumps(evidence,indent=2,ensure_ascii=False,sort_keys=True)+"\n")
    manifest={f:sha(D/f) for f in FILES}
    once(D/"SHA256_MANIFEST_A64.json",json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    handoff=(
      "# A64 integration reconciliation | "+datetime.now().astimezone().isoformat(timespec="seconds")+"\n"
      "Primary SynapseMCP Web live at start; STOP/PAUSE checked in governed scope. Existing DataCenter task remains review/planned, no worker.\n"
      "New offline OUTPUT/comparison.html and OUTPUT/comparison.json compare 5 power channels for v08/v09.\n"
      "A60 trapezoid: 671 x 900s = 167.75h. A62 discrete: 672 x 900s = 168h.\n"
      "Pool delta v08 = "+evidence["pool_delta_v08_kWh"]+" kWh; v09 = "+evidence["pool_delta_v09_kWh"]+" kWh.\n"
      "Verified algebraic decomposition into last rectangle and slope correction, with endpoint identity.\n"
      "QA 12/12 unit tests; 8107/8107 independent Decimal checks; 10 source SHA cross-checks and provenance guards.\n"
      "All inputs DERIVED_SIMULATION; no physical calibration, no SCADA live link, physical_release=false.\n"
      "No Codex, new workers, GPU tasks, VRS, shared GUI, OAuth or foreign-branch changes.\n"
      "Evidence SHA256: "+sha(D/"EVIDENCE_A64.json")+"\n"
      "Manifest SHA256: "+sha(D/"SHA256_MANIFEST_A64.json")+"\n"
      "NEXT: "+evidence["next_step"]+"\n"
    )
    once(D/"FINAL_HANDOFF.md",handoff)
    payload={
      "scope":evidence["scope"],"artifact_directory":str(D),"report_html":evidence["report_html"],
      "evidence_sha256":sha(D/"EVIDENCE_A64.json"),"manifest_sha256":sha(D/"SHA256_MANIFEST_A64.json"),
      "handoff_sha256":sha(D/"FINAL_HANDOFF.md"),
      "QA":"12/12 unittest; 8107/8107 independent Decimal; source SHA/provenance PASS",
      "source_kind":"derived_simulation","physical_release":False,"next_step":evidence["next_step"]
    }
    guard()
    db=sqlite3.connect(CENTER/"tasks.sqlite3",timeout=15,isolation_level=None)
    db.execute("PRAGMA busy_timeout=15000")
    if db.execute("PRAGMA quick_check").fetchone()[0]!="ok":raise RuntimeError("DB_INTEGRITY")
    db.execute("BEGIN IMMEDIATE")
    try:
        state=db.execute("SELECT status,stage,worker_pid FROM tasks WHERE id=?",(TASK,)).fetchone()
        if state!=("review","planned",None):raise RuntimeError("TASK_STATE_CHANGED:"+repr(state))
        found=db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND actor=? AND kind='evidence'",(TASK,ACTOR)).fetchall()
        if len(found)>1:raise RuntimeError("DUPLICATE_EVENTS")
        if found:
            if json.loads(found[0][1])!=payload:raise RuntimeError("EVENT_CONFLICT")
            event_id=found[0][0]
        else:
            event_id=db.execute("INSERT INTO task_events(task_id,at,kind,actor,data_json) VALUES(?,?,?,?,?)",
              (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,ensure_ascii=False))).lastrowid
        db.commit()
    except BaseException:
        db.rollback();raise
    finally:db.close()
    once(D/"REGISTRY_RESULT_A64.json",json.dumps({"event_id":event_id,"task_id":TASK,**payload},indent=2,ensure_ascii=False,sort_keys=True)+"\n")
    print(json.dumps({"event_id":event_id,"unit_tests":12,"independent_checks":8107,
      "evidence_sha256":payload["evidence_sha256"],"handoff_sha256":payload["handoff_sha256"],"manifest_entries":len(manifest)}))
if __name__=="__main__":main()
