"""Independent exact-rational reviewer and adversarial reviewer self-checks."""
import copy,json,sys
from hp_partition_v79 import ROOT,stamp,dump,sha
from hp_partition_checks_v79 import hp_checks
from energy_checks_v78 import energy_checks
from earliest_closed_form_v73 import rows

folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
r=json.loads((folder/'report.json').read_text());b=json.loads((folder/'branch_report.json').read_text())
checks=[]
def check(name,ok):checks.append(dict(name=name,passed=bool(ok)))
for f in b['faults']:
    base=next(x for x in r['runs'] if x['id']==f['base_id'])
    bad=copy.deepcopy(base);bad['trace']=f['trace'];cs=hp_checks(bad)
    check(f['id']+'_exact_bypass',rows(f['trace'])==rows(f['expected_trace'])==rows(f['legacy_trace']))
    check(f['id']+'_v78_energy_QA',all(c['passed'] for c in energy_checks(bad)))
    check(f['id']+'_independent_HP_rejection',any(not c['passed'] for c in cs))
    check(f['id']+'_actual_expected_assertion',f['runtime_rejected'] and f['expected_text'] in f['error_text'])
    check(f['id']+'_log',(folder/(f['id']+'_runtime_fault.txt')).read_text()==f['error_text']+'\n')
    old=rows(base['trace'])[0];new=rows(f['trace'])[0]
    check(f['id']+'_exact_changed_columns',[i+1 for i,(x,y) in enumerate(zip(old,new)) if x!=y]==f['columns'])
    if f['base_id']=='HP_only':
        check('compressor_fault_source_bound_still_overlaps',all(c['passed'] for c in cs if c['name'].endswith('_source_partition')))
        check('compressor_fault_work_disjoint',any(not c['passed'] for c in cs if c['name'].endswith('_work_partition')))
check('MATLAB_branch_all',b['summary']['failed']==0 and all(c['passed'] for c in b['checks']))
check('original_branch_MAT_present',(folder/'hp_branches_v79.mat').stat().st_size>1000)
selfchecks=[]
base=next(x for x in r['runs'] if x['id']=='HP_only')
for label,cols in [('source',[133,134]),('work',[135,136])]:
    bad=copy.deepcopy(base);z=rows(bad['trace'])[0];z[cols[0]]=z[cols[1]]=0
    selfchecks.append(dict(name='zero_'+label+'_detected',passed=any(not c['passed'] for c in hp_checks(bad))))
bad=copy.deepcopy(base);z=rows(bad['trace'])[0]
z[133:137]=[0,z[132],0,z[132]]
selfchecks.append(dict(name='wide_hulls_overlap_accepted_scope_witness',passed=all(c['passed'] for c in hp_checks(bad))))
result=dict(evidence_class='EXACT_RATIONAL_HP_RUNTIME_BRANCH_QA',checks=checks,reviewer_selfchecks=selfchecks,
    report_sha256=sha(folder/'report.json'),branch_sha256=sha(folder/'branch_report.json'),
    reviewer_sha256=sha(ROOT/'audit/verify_hp_branches_v79.py'),
    summary=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)))
name='branch_QA_v79_'+stamp();dump(folder/(name+'.json'),result)
print(json.dumps(dict(summary=result['summary'],reviewer_selfchecks=selfchecks,failed=[c for c in checks if not c['passed']])));
sys.exit(int(result['summary']['failed']>0 or not all(c['passed'] for c in selfchecks)))
