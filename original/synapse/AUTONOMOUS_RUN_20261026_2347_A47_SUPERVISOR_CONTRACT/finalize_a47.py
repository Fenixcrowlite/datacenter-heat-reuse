"""Fail-closed A47 checkpoint and idempotent Synapse evidence registration."""
from pathlib import Path
import hashlib,json,sqlite3,subprocess,sys,time
HERE=Path(__file__).resolve().parent
CENTER=HERE.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-a47-graphical-supervisor-preintegration-contract-20261026"
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def put_once(path,data):
    if path.exists() and path.read_text(encoding="utf-8-sig")!=data:
        raise RuntimeError("ARTIFACT_CONFLICT "+str(path))
    if not path.exists():path.write_text(data,encoding="utf-8")
def main():
    scopes=[CENTER,CENTER/"recovery",HERE,Path(r"C:\Users\Lysda\Desktop\temp_coding"),
            Path(r"C:\Users\Lysda\Desktop\EduMotionPipeline"),
            Path(r"C:\Users\Lysda\Desktop\MicroFreelance_2026")]
    for scope in scopes:
        for flag in ("STOP","STOP.flag","PAUSE","PAUSE.flag",".STOP",".PAUSE","devteam-daemon.stop"):
            if (scope/flag).exists():raise RuntimeError("STOP_ACTIVE "+str(scope/flag))
    run=subprocess.run([sys.executable,"-m","unittest","discover","-s",str(HERE),"-p","test_a47.py","-v"],
                       capture_output=True,text=True,timeout=20)
    if run.returncode or "Ran 5 tests" not in run.stderr or "\nOK" not in run.stderr:
        raise RuntimeError("TEST_FAILURE "+run.stderr)
    report=json.loads((HERE/"PARITY_PROBE.json").read_text(encoding="utf-8-sig"))
    assert report["total_steps"]==4704 and report["mismatches"]==0
    assert len(report["cases"])==7
    summary="""# DataCenter A47: контракт интеграции графического Stateflow
Статус: VERIFIED для проверки логики состояний; НЕ является готовой интеграцией Simulink.
Источники: неизменённые A44 graphical Stateflow, A46 Simulink EMChart, семь CSV A45.
Синтетические данные, физический safety-case отсутствует.

## Подтверждённый интерфейс A44 → A46
- fault = (nominal_cap_W <= 0) OR (T_start_C >= 42).
- recover = (nominal_cap_W > 0) AND (T_start_C < 36).
- ramp_done = (previous_active_it_W + 15000 >= requested_qdc_W - 1e-8).
- Важно: requested_qdc_W берётся из INPUTS_A41.csv, а НЕ из active_it_W или qit_W.
- Состояния: ACTIVE=0, TRIP_PENDING=1, TRIPPED=2, RAMPING=3.
- Stateflow transition guards выполняются до during actions.
- Длительность шага 900 с; двухшаговое ожидание аварийного отключения.

## QA
7 × 672 = 4704 совпадений состояний A44 reference ↔ A45/A46.
5/5 независимых unittest PASS, включая 4 оригинальных сценария A44 и отрицательный контроль.
При неверном ramp_done (использование фактической IT вместо заданной) было 53 расхождения.
Исправленный адаптер даёт 0 расхождений; исходные модели не изменены.

## Ограничения
Это Python pre-integration contract gate. Графическая диаграмма ещё НЕ подключена
к A46 Simulink. MATLAB/Simulink в этом запуске НЕ запускались.
Нужен A48: отдельная A44-equivalent Chart в новом SLX, убрать FSM из EMChart,
замкнуть обратную связь, проверить 7×672 численных траекторий и переходы.
"""
    put_once(HERE/"ENGINEERING_REPORT_RU.md",summary)
    evidence={
        "status":"A47_GRAPHICAL_FSM_CONTRACT_PARITY_PASS",
        "task_id":TASK,"source":"A44 reference + A45 traces + A46 state contract",
        "samples":4704,"cases":7,"state_mismatches":0,"unittest":"5/5 PASS",
        "negative_control_initial_mismatches":53,
        "source_model_sha256":report["source_sha256"],
        "physical_release":False,"actual_graphical_chart_connected":False,
        "matlab_run_this_checkpoint":False,
        "next_step":"A48 build isolated Simulink with A44 graphical Chart replacing EMChart FSM; 7x672 full numeric parity"
    }
    put_once(HERE/"EVIDENCE.json",json.dumps(evidence,indent=2,ensure_ascii=False)+"\n")
    names=("parity_probe.py","test_a47.py","PARITY_PROBE.json","ENGINEERING_REPORT_RU.md","EVIDENCE.json")
    manifest={n:sha(HERE/n) for n in names}
    put_once(HERE/"SHA256_MANIFEST.json",json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
    handoff=f"""# A47 handoff — 2026-10-26
Scope: {HERE}
Task: {TASK} (existing DataCenter card, no new worker)
Status: A47 pre-integration FSM contract VERIFIED, actual A44 Chart ↔ A46 SLX wiring NOT DONE.
Tests: 5/5 PASS, seven synthetic 672-step traces, 4704/4704 FSM state parity.
Negative control: wrong ramp_done using active IT caused 53 mismatches; corrected requested qdc gives 0.
Source model SHA: A44 {report['source_sha256']['A44']}; A46 {report['source_sha256']['A46']}.
Evidence SHA256: {sha(HERE/'EVIDENCE.json')}
Manifest SHA256: {sha(HERE/'SHA256_MANIFEST.json')}
No MATLAB or GPU jobs, no Codex, no shared GUI, no production model changes, VRS skipped.
Next: A48 wire a separate graphical Stateflow chart into a copy of A46, remove duplicated EMChart FSM, 7x672 numeric+transition parity, then independent MATLAB QA.
"""
    put_once(HERE/"FINAL_HANDOFF.md",handoff)
    payload={"scope":"A47_graphical_supervisor_preintegration_contract",
             "artifact_directory":str(HERE),
             "evidence_sha256":sha(HERE/"EVIDENCE.json"),
             "manifest_sha256":sha(HERE/"SHA256_MANIFEST.json"),
             "handoff_sha256":sha(HERE/"FINAL_HANDOFF.md"),
             "qa":"5/5 unittest; 4704/4704 FSM states; 53-mismatch negative control",
             "graphical_stateflow_connected":False,"physical_release":False,
             "next_step":evidence["next_step"]}
    db=sqlite3.connect(CENTER/"tasks.sqlite3",timeout=10,isolation_level=None)
    db.execute("PRAGMA busy_timeout=10000")
    if db.execute("PRAGMA quick_check").fetchone()[0]!="ok":raise RuntimeError("SQLITE_INTEGRITY")
    db.execute("BEGIN IMMEDIATE")
    try:
        row=db.execute("SELECT status,stage,worker_pid FROM tasks WHERE id=?",(TASK,)).fetchone()
        if row!=("review","planned",None):raise RuntimeError("OWNERSHIP_CHANGED "+repr(row))
        old=db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND actor=? AND kind='evidence'",(TASK,ACTOR)).fetchall()
        if len(old)>1:raise RuntimeError("DUPLICATE")
        if old:
            if json.loads(old[0][1])!=payload:raise RuntimeError("EVENT_CONFLICT")
            eid=old[0][0]
        else:
            eid=db.execute("INSERT INTO task_events(task_id,at,kind,actor,data_json) VALUES(?,?,?,?,?)",
                           (TASK,time.time(),"evidence",ACTOR,json.dumps(payload,ensure_ascii=False))).lastrowid
        db.commit()
    except BaseException:
        db.rollback();raise
    finally:db.close()
    put_once(HERE/"REGISTRY_RESULT.json",json.dumps({"event_id":eid,"task_id":TASK,**payload},indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":"A47_CONTRACT_PASS","event_id":eid,"test_count":5,
                      "state_samples":4704,"mismatches":0,
                      "evidence_sha256":payload["evidence_sha256"],
                      "handoff_sha256":payload["handoff_sha256"]},ensure_ascii=False))
if __name__=="__main__":main()
