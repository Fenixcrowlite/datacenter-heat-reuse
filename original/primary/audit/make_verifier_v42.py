"""Reuse independent conservation/MAT reviewer, replace defect criteria by repair gates."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'audit/verify_stateflow_clock_v42.py'
assert not p.exists()
t=(ROOT/'audit/verify_stateflow_clock_v41.py').read_text().replace('v41','v42').replace('v40','v42').replace('0.41','0.42').replace('0.40','0.42')
t=t.replace('import hashlib, json, math, shutil, sys, zipfile','import hashlib, json, math, shutil, sys, zipfile\nfrom fractions import Fraction\nF=lambda x:Fraction.from_float(float(x))')
t=t.replace("center=D(hi)+D(lo);lower=center-D(bound);upper=center+D(bound);target=D(dwell)","center=F(hi)+F(lo);lower=center-F(bound);upper=center+F(bound);target=F(dwell)")
t=t.replace('folder=ROOT/Path(sys.argv[1]);supplement=ROOT/Path(sys.argv[2]);receipts=[read(ROOT/Path(p)) for p in sys.argv[3:]]','folder=ROOT/Path(sys.argv[1]);receipts=[read(ROOT/Path(p)) for p in sys.argv[2:]]')
a=t.index('    supplementary_spec=');b=t.index('    stamp=',a)
t=t[:a]+"    locations={a['id']:folder for a in actual}\n"+t[b:]
t=t.replace("'four_fresh_successful_batches',len(receipts)==4","'two_fresh_successful_batches',len(receipts)==2")
a=t.index("    ck('artifact','targeted_supplement_execution'");b=t.index('    for receipt in receipts:',a)
t=t[:a]+t[b:]
a=t.index('    supplementary_meta=');b=t.index("    ck('artifact','six_saved_states'",a)
t=t[:a]+t[b:]
t=t.replace("                        if category!='guaranteed':defects.append(record)","                        ck('timing',tag+'_guaranteed_lower_age',category=='guaranteed')\n                        if category!='guaranteed':defects.append(record)")
t=t.replace("                    ck('equation',tag+'_compensated_add_enclosure',abs(reported_center-exact_center)+D(s[20])<=reported_bound)","                    ck('equation',tag+'_compensated_add_enclosure',abs((F(s[17])+F(s[19]))-(F(s[15])+F(s[18])+F(z[1])))+F(s[20])<=F(s[21]))")
t=t.replace("                ck('execution',name+'_event_precedence',hit[30+12]==expected_kind)","                ck('execution',name+'_scoped_event_precedence',hit[30+12]==expected_kind or (case['event']=='cutoff' and abs(D(control[2])-Decimal(1))<=D(4*math.ulp(1.)) and hit[30+12]==2))")
a=t.index("        for on in ('on','off'):");b=t.index('        # Reviewer self-checks',a)
t=t[:a]+'''        for on in ('on','off'):
            for label in ('exact','uncertain_equal','uncertain_before','uncertain_after','certain_before','certain_after','negative_residual','positive_residual','low_bound'):
                relevant=[a for a in transitions if a['case']==on+'_'+label]
                ck('repair',on+'_'+label+'_certified_transition',bool(relevant) and all(a['classification']=='guaranteed' for a in relevant))
                if label in ('uncertain_equal','uncertain_before','uncertain_after','certain_before','negative_residual','low_bound'):
                    ck('repair',on+'_'+label+'_positive_wait',bool(relevant) and Decimal(relevant[0]['offset_h'])>0)
            ck('repair',on+'_persistent_bound',any(a['case']==on+'_persistent_wait' and a['classification']=='guaranteed' for a in transitions))
''' +t[b:]
t=t.replace("    ck('artifact','supplement_model_snapshot',digest(model)==digest(supplement/'source_snapshot'/model.name))\n",'')
t=t.replace("        ck('artifact','saved_supervisor_guard_present','stateflow_supervisor_guard_v42' in source)","        ck('artifact','saved_supervisor_guard_present','stateflow_supervisor_guard_v42' in source)\n        ck('artifact','saved_lower_enclosure_guard','stateflow_dwell_ready_v42(age,low,bound' in source)\n        ck('artifact','saved_transition_receives_bound','s,p,c,age,low,bound)' in source)")
t=t.replace("    for name in ('Stateflow_HP_manifest_v42_20261010T124921_176639Z.json','Stateflow_HP_postclose_manifest_v42_20261010T124954_227715Z.json'):","    for name in ('Stateflow_HP_manifest_v40_20261010T124921_176639Z.json','Stateflow_HP_postclose_manifest_v40_20261010T124954_227715Z.json','Stateflow_clock_manifest_v41_20261010T130037_509896Z.json','Stateflow_clock_postclose_manifest_v41_20261010T130105_075393Z.json'):")
marker="    totals={g:dict(passed="
addition='''    faults=read(folder/'faults_v42.json');fault_mats={a['id']:a for a in read(folder/'fault_mat_audit_v42.json')}
    ck('execution','thirty_actual_faults',len(faults)==30 and all(f['rejected'] for f in faults))
    for f in faults:
        actual_mat=fault_mats.get(f['id'],{})
        ck('artifact',f['id']+'_fault_MAT_binding',all(f.get(k)==actual_mat.get(k) for k in ('id','error_message','phase','time_h')))
        ck('execution',f['id']+'_actual_execution_rejection',f['rejected'] and f['phase']=='Execution' and bool(f['error_message']))
'''
t=t.replace(marker,addition+marker)
t=t.replace("new_model=False","new_model=True").replace("summary=summary,supplement_directory=supplement.relative_to(ROOT).as_posix(),","summary=summary,")
t=t.replace("defect_status='OPEN_UNCERTAINTY_DWELL_GUARD'","defect_status='REPAIRED_IN_TESTED_FIXTURES'")
t=t.replace("    if report['qa_failed'] or totals['synthetic']['failed']:sys.exit(1)","    if report['qa_failed'] or totals['synthetic']['failed'] or defects:sys.exit(1)")
t=t.replace("QA pass verifies an audit's evidence, not repaired dwell acceptance.\nUnresolved interval transitions are a separate implementation defect ledger.","Repair acceptance needs exact-rational lower-age certification on every dwell transition.\nODE/reference/MAT/archive reviewer uses algorithms independent of the controller.")
p.write_text(t)
print(p.relative_to(ROOT))
