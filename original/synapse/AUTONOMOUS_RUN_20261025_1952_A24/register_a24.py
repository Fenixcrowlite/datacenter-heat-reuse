"""Idempotent evidence in existing DataCenter Synapse card. Never change task status."""
import hashlib,json,sqlite3,time
from pathlib import Path
from dchr_lineage_audit import ROOT, sha
from scada_api_link import fetch,check

HERE=Path(__file__).resolve().parent
CENTER=HERE.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-dchr-a24-static-lineage-20261025-1952"
FLAGS=("STOP","STOP.flag","STOP.txt",".STOP","PAUSE","PAUSE.flag","PAUSE.txt",".PAUSE","STOP_MANAGED_WORKERS.txt")
CHECK_DIRS=[HERE,CENTER,CENTER/"recovery",CENTER/"agent_knowledge",
            ROOT,ROOT/"scada_v09",ROOT/"matlab"/"pool_measurement_v08",
            ROOT/"results"/"pool_measurement_v08",
            Path(r"C:\Users\Lysda\Desktop\temp_coding"),
            Path(r"C:\Users\Lysda\Desktop\EduMotionPipeline")]
FILES=("dchr_lineage_audit.py","scada_api_link.py","test_dchr_lineage_audit.py",
       "test_scada_api_link.py","DCHR_LINEAGE_EVIDENCE.json","SCADA_LINEAGE_LINK.json",
       "TEST_LOG.txt","QA_REPORT.md","register_a24.py")

def run():
    for root in CHECK_DIRS:
        for flag in FLAGS:
            if (root/flag).exists():raise RuntimeError("STOP_ACTIVE "+str(root/flag))
    for n in FILES:
        if not (HERE/n).is_file():raise RuntimeError("MISSING "+n)
    log=(HERE/"TEST_LOG.txt").read_text(encoding="utf-8-sig")
    if "Ran 25 tests" not in log or not log.rstrip().endswith("OK"):
        raise RuntimeError("QA_TESTS_NOT_PASS")
    lineage=json.loads((HERE/"DCHR_LINEAGE_EVIDENCE.json").read_text(encoding="utf-8"))
    link=json.loads((HERE/"SCADA_LINEAGE_LINK.json").read_text(encoding="utf-8"))
    if (lineage["status"]!="PASS_STATIC_LINEAGE_NO_MATLAB_REEXECUTION" or
        lineage["rows_verified"]!=5376 or len(lineage["cases"])!=8 or
        lineage["source_class"]!="D_SYNTHETIC" or len(lineage["model_sha256"])!=3 or
        link["status"]!="PASS_LIVE_SCADA_SHA_LINK" or link["scenario_count"]!=8):
        raise RuntimeError("QA_EVIDENCE_INVALID")
    for case in lineage["cases"]:
        name=case["scenario"]
        files={
            "raw_D_sha256":ROOT/"results"/"pool_measurement_v08"/"source_D"/name/"recorded_measured_schema_D.csv",
            "stage_sha256":ROOT/"results"/"pool_measurement_v08"/"staged_D"/name/"normalized_measurements_v07.csv",
            "v07_sha256":ROOT/"results"/"pool_redundancy_v07"/f"scenar_{name}_SK.csv",
            "v08_csv_sha256":ROOT/"results"/"pool_measurement_v08"/f"sim_v08_{name}_SK.csv"}
        for key,path in files.items():
            if sha(path)!=case[key]:raise RuntimeError("SOURCE_CHANGED "+str(path))
    for rel,expected in lineage["model_sha256"].items():
        if sha(ROOT/rel)!=expected:raise RuntimeError("MODEL_CHANGED "+rel)
    if sha(ROOT/"matlab"/"pool_measurement_v08"/"spusti_merania_replay_v08_sk.m")!=lineage["generating_matlab_script_sha256"]:
        raise RuntimeError("GENERATOR_CHANGED")
    if check(fetch(),lineage)["source_sha256"]!=link["source_sha256"]:
        raise RuntimeError("LIVE_SCADA_CHANGED")
    hashes={n:sha(HERE/n) for n in FILES}
    (HERE/"SHA256_MANIFEST.json").write_text(json.dumps(hashes,indent=2)+"\n",encoding="utf-8")
    payload={"scope":"independent_v07_to_D_v08_SCADA_lineage_readonly",
             "artifact_directory":str(HERE),
             "evidence_sha256":hashes["DCHR_LINEAGE_EVIDENCE.json"],
             "scada_link_sha256":hashes["SCADA_LINEAGE_LINK.json"],
             "qa_report_sha256":hashes["QA_REPORT.md"],
             "manifest_sha256":sha(HERE/"SHA256_MANIFEST.json"),
             "qa":"25/25 mutation tests PASS; 8 scenarios; 5376 row lineage; 8 live SCADA SHA; 3 model SHA; py_compile PASS",
             "finding":"Verified D_SYNTHETIC v07 -> raw D -> 8 significant digit staging -> v08 CSV -> live SCADA SHA lineage",
             "limits":"No original MATLAB run receipt, physical measurement, calibration, standards signoff or hardware safety acceptance",
             "next_step":"Read-only inventory of MATLAB v08 execution receipts, then independently validate physical parameters against primary sources"}
    with sqlite3.connect(CENTER/"tasks.sqlite3",timeout=5,isolation_level=None) as db:
        db.execute("PRAGMA busy_timeout=5000")
        if db.execute("PRAGMA quick_check").fetchone()[0]!="ok":raise RuntimeError("REGISTRY_CORRUPT")
        db.execute("BEGIN IMMEDIATE")
        try:
            state=db.execute("SELECT status,stage FROM tasks WHERE id=?",(TASK,)).fetchone()
            if state!=("review","planned"):raise RuntimeError("TASK_STATE_CHANGED "+repr(state))
            rows=db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",(TASK,ACTOR)).fetchall()
            if len(rows)>1:raise RuntimeError("DUPLICATE")
            if rows:
                if json.loads(rows[0][1])!=payload:raise RuntimeError("ACTOR_COLLISION")
                event_id,action=rows[0][0],"EXISTING_EVENT"
            else:
                event_id=db.execute("INSERT INTO task_events(task_id,at,kind,actor,data_json) VALUES(?,?,?,?,?)",
                    (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,ensure_ascii=False))).lastrowid
                action="CREATED_EVENT"
            db.commit()
        except Exception:
            db.rollback();raise
    result={"task_id":TASK,"event_id":event_id,"action":action,**payload}
    (HERE/"REGISTRY_RESULT.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"task_id":TASK,"event_id":event_id,"action":action,"evidence_sha256":payload["evidence_sha256"]}))
if __name__=="__main__":run()
