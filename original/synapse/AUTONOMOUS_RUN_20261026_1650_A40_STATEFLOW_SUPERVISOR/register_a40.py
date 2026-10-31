"""Idempotent existing-card evidence for A40. Never launches workers."""
from __future__ import annotations
import hashlib,json,sqlite3,time,zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
CENTER=HERE.parent.parent
TASK='scc-3d9d172beb6e1b'
ACTOR='chatgpt-a40-dchr-stateflow-supervisor-20261026-1650'
SOURCE=HERE.parent/'AUTONOMOUS_RUN_20261026_1054_A38_TES_N1_INTEGRATION'
FILES=['run_a40.m','DCHR_A40_Safety_Controller.slx','MATLAB_RESULT.json',
 'MATLAB_STDOUT.txt','MATLAB_STDERR.txt','MATLAB_PID.txt',
 'STATEFLOW_TRACE.csv','STATEFLOW_TRACE_both.csv',
 'STATEFLOW_TRACE_backup_only.csv','STATEFLOW_TRACE_neither.csv',
 'verify_a40.py','QA_LOG.txt','ENGINEERING_REPORT_RU.md','register_a40.py']
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save_once(p,content):
    if p.exists():
        assert p.read_text(encoding='utf-8')==content,('EXISTING_CONFLICT',p)
    else: p.write_text(content,encoding='utf-8')
def main():
    for root in (CENTER,CENTER/'recovery',HERE,CENTER.parent/'EduMotionPipeline'):
        for n in ('STOP','STOP.flag','STOP.txt','.stop','.STOP','PAUSE','PAUSE.flag','STOP_MANAGED_WORKERS.txt'):
            assert not (root/n).exists(),('STOP_ACTIVE',root,n)
    for name in FILES:
        assert (HERE/name).is_file(),('MISSING',name)
    qa=(HERE/'QA_LOG.txt').read_text(encoding='utf-8-sig')
    assert 'Ran 9 tests' in qa and qa.rstrip().endswith('OK'),'QA_FAILED'
    assert (HERE/'MATLAB_STDERR.txt').stat().st_size==0,'MATLAB_STDERR'
    stdout=(HERE/'MATLAB_STDOUT.txt').read_text(encoding='utf-8-sig')
    assert 'A40_STATEFLOW_SIM_PASS samples=672' in stdout
    for name in ('both','backup_only','neither'):
        assert f'A40_SCENARIO_PASS {name} ' in stdout
    with zipfile.ZipFile(HERE/'DCHR_A40_Safety_Controller.slx') as z:
        assert z.testzip() is None
        chart=z.read('simulink/stateflow/chart_24.xml')
        assert b'TES_FULL' in chart and b'CRITICAL' in chart
    result=json.loads((HERE/'MATLAB_RESULT.json').read_text(encoding='utf-8'))
    assert result['status']=='STATEFLOW_SIM_PASS'
    assert result['physical_release'] is False and result['samples']==672
    assert result['scenario_mode_counts']=={
      'main_only':[226,153,36,257], 'both':[276,0,0,396],
      'backup_only':[189,166,207,110], 'neither':[96,0,576,0]}
    input_names=['trace_main_only_no_shed.csv','trace_both_no_shed.csv',
      'trace_backup_only_no_shed.csv','trace_neither_no_shed.csv']
    source_hashes={n:sha(SOURCE/n) for n in input_names}
    evidence={
      'scope':'A40_real_Stateflow_4_mode_isolated_synthetic_supervisor',
      'status':'STATEFLOW_OPEN_LOOP_SIM_VERIFIED',
      'matlab':'R2026a','scenarios':4,'samples_per_scenario':672,
      'independent_oracle_comparisons':2688,'python_tests':'9/9 PASS',
      'states':4,'transitions_including_default':11,
      'source_trace_sha256':source_hashes,
      'model_sha256':sha(HERE/'DCHR_A40_Safety_Controller.slx'),
      'matlab_result_sha256':sha(HERE/'MATLAB_RESULT.json'),
      'hardware_interface':False,'physical_release_allowed':False,
      'critical_note':'shedCeilingFraction is a synthetic ceiling, never an actuator command',
      'limitations':'open-loop A38 traces; no physical feedback, branch switching delays or sensor validation',
      'next_step':'Integrate Stateflow mode into isolated A38 thermal closed loop; dynamic IT shedding and REJECT A/B delays; 672-step energy/thermal parity; do not touch production v85 SLX'}
    save_once(HERE/'EVIDENCE.json',json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
    manifest={n:sha(HERE/n) for n in FILES+['EVIDENCE.json']}
    save_once(HERE/'SHA256_MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    payload={
      'scope':evidence['scope'],'artifact_directory':str(HERE),
      'evidence_sha256':sha(HERE/'EVIDENCE.json'),
      'manifest_sha256':sha(HERE/'SHA256_MANIFEST.json'),
      'model_sha256':evidence['model_sha256'],
      'qa':'MATLAB/Stateflow R2026a 4x672 PASS, Python 9/9 PASS, oracle 2688/2688 exact modes',
      'status':'STATEFLOW_OPEN_LOOP_SIM_VERIFIED_CLOSED_LOOP_NOT_DONE',
      'release_status':'PHYSICAL_RELEASE_BLOCKED',
      'next_step':evidence['next_step']}
    db=sqlite3.connect(CENTER/'tasks.sqlite3',timeout=8,isolation_level=None)
    db.execute('pragma busy_timeout=8000')
    assert db.execute('pragma quick_check').fetchone()[0]=='ok'
    db.execute('begin immediate')
    try:
        state=db.execute('select status,stage,worker_pid,owner from tasks where id=?',(TASK,)).fetchone()
        assert state==('review','planned',None,'MATLAB/Stateflow QA'),('TASK_CHANGED',state)
        rows=db.execute('select id,data_json from task_events where task_id=? and actor=? and kind=?',
                        (TASK,ACTOR,'evidence')).fetchall()
        assert len(rows)<=1,'DUPLICATE_EVENTS'
        if rows:
            assert json.loads(rows[0][1])==payload,'EVENT_CONFLICT'
            event,action=rows[0][0],'EXISTING_EVENT'
        else:
            event=db.execute('insert into task_events(task_id,at,kind,actor,data_json) values(?,?,?,?,?)',
                (TASK,time.time(),'evidence',ACTOR,json.dumps(payload,ensure_ascii=False))).lastrowid
            action='CREATED_EVENT'
        db.commit()
    except BaseException:
        db.rollback();raise
    finally: db.close()
    receipt={'action':action,'task_id':TASK,'event_id':event,**payload}
    path=HERE/'REGISTRY_RESULT.json'
    if path.exists():
        old=json.loads(path.read_text(encoding='utf-8'))
        assert {k:v for k,v in old.items() if k!='action'}=={k:v for k,v in receipt.items() if k!='action'}
    else:
        save_once(path,json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'action':action,'task':TASK,'event':event,
       'evidence_sha256':payload['evidence_sha256'],
       'manifest_sha256':payload['manifest_sha256']},ensure_ascii=False))
if __name__=='__main__':main()
