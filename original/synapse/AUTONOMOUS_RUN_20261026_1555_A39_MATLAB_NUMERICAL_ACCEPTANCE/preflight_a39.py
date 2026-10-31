"""A39 preflight for isolated MATLAB numerical acceptance; read-only."""
from pathlib import Path
import sqlite3, json, hashlib, time, subprocess, csv
HERE=Path(__file__).resolve().parent
CENTER=HERE.parent.parent
A38=HERE.parent/'AUTONOMOUS_RUN_20261026_1054_A38_TES_N1_INTEGRATION'
A36=HERE.parent/'AUTONOMOUS_RUN_20261026_0744_A36_DCHR_REDISPATCH_REFERENCE'
V08=Path(r'C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\pool_measurement_v08\sim_v08_zdravy_SK.csv')
TASK='scc-3d9d172beb6e1b'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    roots=[CENTER,CENTER/'recovery',HERE,V08.parent.parent.parent,
           Path(r'C:\Users\Lysda\Desktop\temp_coding\telegram_codex_bot\logs')]
    for root in roots:
        for name in ('STOP','STOP.flag','STOP.txt','.stop','.STOP','PAUSE','PAUSE.flag','PAUSE.txt','STOP_MANAGED_WORKERS.txt'):
            if (root/name).exists():raise RuntimeError('STOP_ACTIVE: '+str(root/name))
    for name in ('dchr_a38_step.m','dchr_a38_replay_acceptance.m','RESULTS_A38.json'):
        if not (A38/name).is_file():raise RuntimeError('MISSING_A38 '+name)
    upstream=json.loads((A38/'RESULTS_A38.json').read_text(encoding='utf8'))
    assert sha(V08)==upstream['upstream']['v08_sha256'],'V08_SHA_MISMATCH'
    assert sha(A36/'scenario_both_off.csv')==upstream['upstream']['a36_csv_sha256'],'A36_SHA_MISMATCH'
    assert upstream['samples']==672 and len(upstream['cases'])==12
    for c in upstream['cases'].values():
        assert sha(A38/c['trace'])==c['sha256'],'A38_TRACE_MISMATCH'
    db=sqlite3.connect('file:'+str(CENTER/'tasks.sqlite3').replace('\\','/')+'?mode=ro',uri=True)
    assert db.execute('pragma quick_check').fetchone()[0]=='ok'
    state=db.execute('select status,stage,worker_pid,owner from tasks where id=?',(TASK,)).fetchone()
    assert state==('review','planned',None,'MATLAB/Stateflow QA'),('TASK_CHANGED',state)
    count=db.execute('select count(*) from task_events where task_id=? and actor=? and kind=?',
                     (TASK,'chatgpt-a39-dchr-matlab-acceptance-20261026-1555','evidence')).fetchone()[0]
    assert count==0,'A39_EVENT_ALREADY_EXISTS'
    db.close()
    with V08.open(encoding='utf-8-sig',newline='') as f: assert sum(1 for _ in csv.DictReader(f))==672
    r={'status':'PREFLIGHT_PASS','checked_at_epoch':time.time(),
       'task_id':TASK,'task_state':state,'prior_a39_events':count,
       'source_v08_sha256':sha(V08),'source_a36_sha256':sha(A36/'scenario_both_off.csv'),
       'a38_step_sha256':sha(A38/'dchr_a38_step.m'),
       'a38_acceptance_sha256':sha(A38/'dchr_a38_replay_acceptance.m'),
       'cases':12,'samples_per_case':672,'expected_comparisons':80640}
    (HERE/'PREFLIGHT.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8')
    print(json.dumps(r,indent=2))
if __name__=='__main__':main()
