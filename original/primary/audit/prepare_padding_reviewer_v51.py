"""Version inherited independent equations, with exact original-MAT time proofs."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    text=(ROOT/'audit/verify_annual_sensitivity_v50.py').read_text().replace('v50','v51').replace('V50','V51').replace('0.42','0.51')
    text=text.replace('import collections, copy, csv, hashlib, json, math, shutil, sys, zipfile',
                      'import collections, copy, csv, hashlib, json, math, shutil, sys, zipfile, struct')
    text=text.replace("and not r['summary']['new_model']","and r['summary']['new_model']")
    # Exact binary span/clock reopening already independently exercised in v50.
    defect=(ROOT/'audit/verify_annual_sensitivity_defects_v50.py').read_text()
    a=defect.index("            with (folder/'binary_reopen'/(id+'_spans_hex.csv'))")
    b=defect.index('            indexed=collections.defaultdict(list)',a)
    marker='            indexed=collections.defaultdict(list)'
    text=text.replace(marker,defect[a:b]+marker)
    text=text.replace('bound=max(dec(starts[i][3]),dec(ends[i][3]))',
                      'bound=max(D.from_float(starts[i][3]),D.from_float(ends[i][3]))')
    text=text.replace('t=dec(z[1]);new_latch=int(z[25])',
                      "t=D.from_float(exact_spans[(i,slot)]);new_latch=int(z[25])\n                    check('binary_span_binding',f'{id}_{i}_{j}',near(z[1],t))")
    text=text.replace("model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx'",
                      "model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v51.slx'")
    text=text.replace("check('archive','accepted_hash',sha(model)==json.loads((ROOT/'STATUS_stateflow_v42.json').read_text())['model_sha256'])",
                      "check('archive','snapshot_hash',sha(model)==sha(folder/'source_snapshot/matlab/simulink/DCHR_Dispatch_Stateflow_v51.slx'))")
    text=text.replace("Annual_sensitivity_execution_v51_*.json","Stateflow_padding_execution_v51_*.json")
    # Reopening and matrix can have separate receipts. Their scopes stay explicit.
    text=text.replace("check('execution',path.name,'ANNUAL_SENSITIVITY_V51' in log and 'MAT_REOPEN_V51 complete' in log)",
                      "check('execution',path.name,any(tag in log for tag in ['ANNUAL_SENSITIVITY_V51','MAT_REOPEN_V51 complete','PADDING_REPAIR_V51']))")
    text=text.replace("    check('execution','receipt',bool(receipts))", "    check('execution','receipt',bool(receipts))\n    verify_repair(folder,check,selfchecks)")
    helpers='''
def exact_float(hex_value):
    return struct.unpack('>d',bytes.fromhex(hex_value))[0]

def verify_repair(folder,check,selfchecks):
    fixtures=json.loads((folder/'fixtures_v51.json').read_text())
    check('fixtures','all_six_modes',{int(v['dispatch'][0]) for v in fixtures}==set(range(6)))
    for item in fixtures + [json.loads((folder/(id+'_exact_seed_v51_evidence.json')).read_text()) for id in ('restart_49','on_05')]:
        c=item['case'];xs=c['inputs'];xs=xs if isinstance(xs[0],list) else [xs]
        segs=item['segments'];segs=segs if isinstance(segs[0],list) else [segs]
        for j,z in enumerate(segs):
            for kind,ok in physical(z,xs[0],c['p'],c['h']).items():check('repair_'+kind,f'{item["id"]}_{j}',ok)
        starts=list(map(exact_float,item['start_hex']));ends=list(map(exact_float,item['endpoint_hex']))
        check('repair_binary',item['id'],all(a==b for a,b in zip(starts[1:],ends[:-1])) and all(0<=v<=c['p'][1] for v in starts+ends) and item['strict_padding_identity'] and item['exact_handoff'])
        if 'reference' in item:
            check('MATLAB_reference',item['id'],all(near(a,b) or math.isnan(a) and math.isnan(b) for a,b in zip(item['dispatch'],item['reference'])))
    for id in ('restart_49','on_05'):
        old=json.loads((folder/(id+'_exact_seed_v42_evidence.json')).read_text())
        new=json.loads((folder/(id+'_exact_seed_v51_evidence.json')).read_text())
        check('exact_counterexample',id,old['expected_rejection'] and 'Zero-span segment has service.' in old['error_message'] and not new['error_message'] and new['padding_slots']>0)
    faults=json.loads((folder/'faults_v51.json').read_text())
    check('runtime_faults','all_observed',len(faults)==30 and all(v['rejected'] and v['phase']=='Execution' and v['error_message'] for v in faults))
    assertions=json.loads((folder/'repair_assertions_v51.json').read_text())
    check('repair_execution','harness',all(v['passed'] for v in assertions))
    spec=json.loads((folder/'spec.json').read_text())
    for item in spec['scenarios']:
        id=item['id'];rows_=rows(folder/'binary_reopen'/(id+'_padding_identity.csv'))
        check('annual_padding',id,len(rows_)==8760 and all(int(v['Identity']) and int(v['EnergyHandoff']) and int(v['ClockIdentity']) and int(v['MacroMemory']) and int(v['Bounds']) for v in rows_))
    selfchecks.append(dict(name='one_ULP_padding_identity',passed=exact_float('4049000000000001')!=exact_float('4049000000000000')))
'''
    text=text.replace("if __name__=='__main__':",helpers+"\nif __name__=='__main__':")
    path=ROOT/'audit/verify_stateflow_padding_v51.py';assert not path.exists();path.write_text(text)
if __name__=='__main__':main()
