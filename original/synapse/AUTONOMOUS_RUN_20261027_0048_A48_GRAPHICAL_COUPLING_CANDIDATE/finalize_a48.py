"""A48 fail-closed candidate checkpoint, not a MATLAB acceptance receipt."""
from pathlib import Path
import hashlib,json,sqlite3,subprocess,sys,time
HERE=Path(__file__).resolve().parent
CENTER=HERE.parent.parent
TASK="scc-3d9d172beb6e1b"
ACTOR="chatgpt-a48-graphical-coupling-source-candidate-20261027"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(path,txt):
    if path.exists() and path.read_text(encoding='utf-8-sig')!=txt:
        raise RuntimeError("ARTIFACT_CONFLICT "+str(path))
    if not path.exists():path.write_text(txt,encoding='utf-8')
def main():
    for root in [CENTER,CENTER/'recovery',HERE,Path(r'C:\Users\Lysda\Desktop\temp_coding'),Path(r'C:\Users\Lysda\Desktop\EduMotionPipeline')]:
        for f in ('STOP','STOP.flag','PAUSE','PAUSE.flag','.STOP','.PAUSE','devteam-daemon.stop'):
            if (root/f).exists():raise RuntimeError('STOP_ACTIVE '+str(root/f))
    test=subprocess.run([sys.executable,'-B',str(HERE/'test_a48.py')],capture_output=True,text=True,timeout=25)
    if test.returncode or 'Ran 7 tests' not in test.stderr or '\nOK' not in test.stderr:
        raise RuntimeError('QA_FAIL '+test.stdout+' '+test.stderr)
    replay=json.loads((HERE/'PARITY_PROBE.json').read_text(encoding='utf-8'))
    if replay['total_steps']!=4704 or replay['mismatches']!=0:raise RuntimeError('FSM_PARITY_FAIL')
    if (HERE/'DCHR_A48_Graphical_Closed_Loop.slx').exists():raise RuntimeError('UNVALIDATED_MODEL_PRESENT')
    build=HERE/'build_a48.m'
    code=build.read_text(encoding='utf-8')
    if 'A48_GRAPHICAL_COUPLED_PARITY_PASS' not in code:raise RuntimeError('WRONG_STATUS')
    evidence={'status':'A48_GRAPHICAL_SIMULINK_BUILD_SOURCE_CANDIDATE',
              'task_id':TASK,'source_builder_sha256':sha(build),
              'tests':'7/7 PASS','fsm_reference_steps':4704,'fsm_mismatches':0,
              'actual_matlab_run':False,'model_slx_exists':False,
              'actual_graphical_stateflow_connected':False,
              'resource_admission':'DEFERRED: free RAM 4.26 GiB; GPU 39% in live precheck',
              'synthetic':True,'physical_release':False,
              'next_step':'When RAM headroom and GPU owner permit: run build_a48.m in MATLAB R2026a, fix compilation/timing issues, verify 7x672 full numerical and transition parity, update this task.'}
    put(HERE/'EVIDENCE.json',json.dumps(evidence,indent=2,ensure_ascii=False)+'\n')
    files=['prepare_a48.py','build_a48.m','test_a48.py','SOURCE_CANDIDATE.json','PARITY_PROBE.json','EVIDENCE.json']
    manifest={n:sha(HERE/n) for n in files}
    put(HERE/'SHA256_MANIFEST.json',json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    handoff=f"""# A48 checkpoint — 2026-10-27 00:xx CET
Task: {TASK} (existing card, review)
Scope: {HERE}
Status: SOURCE_CANDIDATE_VERIFIED, EXECUTABLE_SLX_NOT_BUILT.
Created a separate MATLAB build_a48.m that copies graphical Stateflow A44 chart, feeds its mode to the A46 thermal plant, removes the plant's duplicated FSM, adds 900 s delayed temperature/IT-power feedback and uses the A47 signal adapter. Original A44/A46 SLX unchanged.
QA: 7/7 Python static/regression tests PASS; A47 reference replay 4704/4704 state samples; 0 mismatches. This does NOT verify the generated model, wiring, algebraic-loop freedom in MATLAB, or 51744 numerical comparisons.
MATLAB R2026a exists but was NOT launched: measured RAM free 4.26 GiB and active GPU 39% at admission. No Codex, new workers, GPU jobs, GUI changes, VRS or physical equipment.
Source build SHA256: {sha(build)}
Evidence SHA256: {sha(HERE/'EVIDENCE.json')}
Manifest SHA256: {sha(HERE/'SHA256_MANIFEST.json')}
Next: check live STOP/ownership/RAM/GPU; run MATLAB -batch with isolated build_a48.m only if resources permit; inspect compiler and simulation outputs; fix discrepancies; 7x672 numeric+FSM parity, then new evidence in same card.
"""
    put(HERE/'FINAL_HANDOFF.md',handoff)
    payload={'scope':'A48_graphical_coupling_build_source_candidate',
             'artifact_directory':str(HERE),'build_sha256':sha(build),
             'evidence_sha256':sha(HERE/'EVIDENCE.json'),
             'manifest_sha256':sha(HERE/'SHA256_MANIFEST.json'),
             'handoff_sha256':sha(HERE/'FINAL_HANDOFF.md'),
             'qa':'7/7 Python tests; 4704/4704 A47 FSM reference; MATLAB NOT RUN',
             'model_slx_exists':False,'actual_graphical_stateflow_connected':False,
             'physical_release':False,'next_step':evidence['next_step']}
    db=sqlite3.connect(CENTER/'tasks.sqlite3',timeout=10,isolation_level=None)
    db.execute('PRAGMA busy_timeout=10000')
    if db.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise RuntimeError('DB_INTEGRITY')
    db.execute('BEGIN IMMEDIATE')
    try:
        row=db.execute('SELECT status,stage,worker_pid FROM tasks WHERE id=?',(TASK,)).fetchone()
        if row!=('review','planned',None):raise RuntimeError('TASK_OWNERSHIP_CHANGED '+repr(row))
        prior=db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND actor=? AND kind='evidence'",(TASK,ACTOR)).fetchall()
        if len(prior)>1:raise RuntimeError('DUPLICATE_EVENT')
        if prior:
            if json.loads(prior[0][1])!=payload:raise RuntimeError('EVENT_CONFLICT')
            event=prior[0][0]
        else:
            event=db.execute('INSERT INTO task_events(task_id,at,kind,actor,data_json) VALUES(?,?,?,?,?)',
                             (TASK,time.time(),'evidence',ACTOR,json.dumps(payload,ensure_ascii=False))).lastrowid
        db.commit()
    except BaseException:
        db.rollback();raise
    finally:db.close()
    put(HERE/'REGISTRY_RESULT.json',json.dumps({'event_id':event,'task_id':TASK,**payload},indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'status':'A48_SOURCE_CANDIDATE_VERIFIED','event_id':event,
                      'build_sha256':payload['build_sha256'],'evidence_sha256':payload['evidence_sha256'],
                      'handoff_sha256':payload['handoff_sha256'],'tests':7,'fsm_samples':4704,
                      'matlab_run':False},ensure_ascii=False))
if __name__=='__main__':main()
