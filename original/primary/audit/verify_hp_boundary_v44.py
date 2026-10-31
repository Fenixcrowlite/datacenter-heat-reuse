"""Independent exact-rational QA of MATLAB ports and boundary ratios.

Does not import preparation or production equations. Reviewer selfchecks use
deliberately corrupted copies, separately counted from observed evidence.
"""
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime, timezone
import hashlib, json, math, sys

ROOT=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def near(a,b):
    return math.isfinite(a) and abs(F(str(a))-b)<=F('2e-12')*max(F(1),abs(b))
def row_valid(v,row):
    # Invert cooling efficiency to obtain independent compressor work.
    tl,lift,eta,ql,r,alpha=map(lambda x:F(str(x)),v)
    L=tl+F('273.15'); H=L+lift
    wc=ql*(H-L)/(eta*L); wa=r*wc; wt=wc+wa
    qh=ql+wc+alpha*wa
    expected=[eta*L/(H-L),wc,wa,qh,wt,ql/wt,qh/wt,
              (wc+alpha*wa)/wt,(1+alpha*r)/(1+r),H/(H-L)]
    return [near(a,b) for a,b in zip(row[6:],expected)]
def main():
    folder=(ROOT/Path(sys.argv[1])).resolve()
    assert folder.is_relative_to(ROOT/'results')
    checks=[]; synthetic=[]
    def check(kind,name,passed): checks.append(dict(kind=kind,name=name,passed=bool(passed)))
    spec=json.loads((folder/'spec.json').read_text())
    report=json.loads((folder/'boundary_v44.json').read_text())
    exported=json.loads((folder/'mat_reexport_v44.json').read_text())
    check('MAT','separate_reopen_matrix',report['matrix']==exported['matrix'])
    check('MAT','separate_reopen_report',report==exported['report'])
    check('MAT','separate_reopen_spec',spec==exported['spec'])
    check('execution','observed_harness',report['passed']==2648 and report['failed']==0)
    check('execution','count',len(spec['vectors'])==len(report['matrix'])==report['vector_count']==486)
    check('scope','synthetic_not_calibrated',spec['fixture_class']=='ENGINEERING_SYNTHETIC_NOT_EQUIPMENT_DATA' and not report['new_model'])
    for i,(v,row) in enumerate(zip(spec['vectors'],report['matrix'])):
        check('numeric',f'inputs_{i}',v==row[:6])
        for j,ok in enumerate(row_valid(v,row)): check('equation',f'port_ratio_{i}_{j}',ok)
        ql,wc,wa,qh,wt,ec,hc=row[3],row[7],row[8],row[9],row[10],row[11],row[12]
        alpha=row[5]
        check('energy',f'first_law_{i}',near(qh,F(str(ql))+F(str(wc))+F(str(alpha))*F(str(wa))))
        check('energy',f'electrical_boundary_{i}',near(wt,F(str(wc))+F(str(wa))))
        check('equation',f'gap_enclosure_{i}',alpha-2e-12<=hc-ec<=1+2e-12)
    # Compare same lift independently using the actually executed rows.
    pairs={}
    for row in report['matrix']:
        key=tuple(row[1:6]); pairs.setdefault(key,[]).append(row)
    for key,rows in pairs.items():
        rows.sort(key=lambda r:r[0])
        check('two_axes',str(key),len(rows)==3 and rows[0][6]<rows[1][6]<rows[2][6])
        expected=F(str(key[1]))*F(30)/F(str(key[0]))
        check('two_axes','difference_'+str(key),near(rows[2][6]-rows[0][6],expected))
    for item in json.loads((folder/'preservation.json').read_text()):
        p=ROOT/item['path'];check('preservation',item['path'],p.is_file() and p.stat().st_size==item['bytes'] and sha(p)==item['sha256'])
    successful=[]
    for path in ROOT.glob('audit/HP_boundary_execution_v44_*.json'):
        receipt=json.loads(path.read_text(encoding='utf-8-sig'))
        if folder.name in receipt['command'] and receipt['exit_code']==0:
            log=(ROOT/receipt['log_path']).read_text(encoding='utf-8-sig')
            check('execution',str(path.name),'BOUNDARY_V44 vectors=486 passed=2648 failed=0' in log and 'MAT_REEXPORT_V44 rows=486' in log)
            successful.append(str(path.relative_to(ROOT)))
    check('execution','at_least_one_successful_batch',len(successful)>=1)
    obs=json.loads((folder/'source_observations_v44.json').read_text())
    check('source','upstream_not_verified',obs['upstream_primary_text_verified'] is False and obs['coefficients_acquired'] is False)
    check('source','local_visual_locator',obs['local_visual_review']['pages']==[8,27] and obs['local_visual_review']['pdf_sha256']==sha(ROOT/'sources/papers/20_Verzino_Varna_2026.pdf'))
    for name in ['run_hp_boundary_v44.m','export_hp_boundary_v44.m']:
        check('artifact',name,sha(folder/'source_snapshot'/name)==sha(ROOT/'matlab/simulink'/name))
    # Reviewer mutation checks: thermal credit, compressor power, missing axis.
    v=spec['vectors'][0]; row=report['matrix'][0]
    for idx in [7,9,13]:
        bad=list(row);bad[idx]+=1
        synthetic.append(dict(name=f'corrupted_column_{idx}_detected',passed=not all(row_valid(v,bad))))
    wrong=list(v);wrong[0]+=30
    synthetic.append(dict(name='temperature_axis_corruption_detected',passed=not all(row_valid(wrong,row))))
    passed=sum(x['passed'] for x in checks); failed=len(checks)-passed
    sp=sum(x['passed'] for x in synthetic);sf=len(synthetic)-sp
    summary=dict(version='0.44',timestamp_utc=datetime.now(timezone.utc).isoformat(),
                 actual_passed=passed,actual_failed=failed,reviewer_selfchecks_passed=sp,
                 reviewer_selfchecks_failed=sf,successful_receipts=successful,
                 checks=checks,reviewer_selfchecks=synthetic,
                 independence='Different algorithm in same agent, not independent personnel',
                 result='PASS_SCOPED_BOUNDARY_QA' if failed+sf==0 else 'FAIL')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    path=folder/f'independent_QA_v44_{stamp}.json'; path.write_text(json.dumps(summary,indent=2)+'\n')
    print(f'INDEPENDENT_ACTUAL {passed} PASS / {failed} FAIL; REVIEWER_SELFCHECK {sp} PASS / {sf} FAIL')
    print('QA='+str(path.relative_to(ROOT)))
    sys.exit(int(failed+sf>0))
if __name__=='__main__': main()
