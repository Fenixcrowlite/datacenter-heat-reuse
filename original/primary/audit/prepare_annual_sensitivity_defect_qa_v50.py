"""Generate a scoped defect reviewer from the preserved full-matrix reviewer.

Only execution/receipt/scope handling changes. All independent equation,
physical-time, matrix/report and preservation checks are retained verbatim.
The original full-success reviewer remains preserved and is not used to accept
the failed variants. The generated Python source is separately sealed.
"""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'audit/verify_annual_sensitivity_v50.py').read_text()

def replace(old,new):
    global source
    assert source.count(old)==1,old
    source=source.replace(old,new)

replace('import collections, copy, csv, hashlib, json, math, shutil, sys, zipfile',
        'import collections, copy, csv, hashlib, json, math, shutil, struct, sys, zipfile')
replace("    check('execution', 'harness', r['summary']['harness_failed']==0 and all(x['passed'] for x in r['assertions']))",
"""    expected_failures={'restart_49_executed','on_05_executed'}
    check('execution','expected_matrix_defects',r['summary']['harness_failed']==2 and
          {v['name'] for v in r['assertions'] if not v['passed']}==expected_failures)
    isolated=json.loads((folder/'defect_replay/isolated_replays_v50.json').read_text())
    defects=json.loads((folder/'defect_evidence/defects_v50.json').read_text())
    check('defect_scope','two_actual_defects',{v['id'] for v in isolated}=={'restart_49','on_05'})""")
replace("    check('scope', 'matrix_nine', len(spec['scenarios'])==len(r['stateflow'])==len(r['matrix'])==9)",
        "    check('scope','nine_attempted_seven_completed',len(spec['scenarios'])==len(r['stateflow'])==9 and len(r['matrix'])==7)")
replace("        for item,definition,matrix in zip(r['stateflow'],spec['scenarios'],r['matrix']):",
"""        for item,definition in zip(r['stateflow'],spec['scenarios']):
            matrix=next((m for m in r['matrix'] if m['id']==item['id']),None)""")
replace("item['execution_success'] and policy==definition['policy'] and changed==wanted",
        "policy==definition['policy'] and changed==wanted")
replace("            ds=numeric(folder/(id+'_dispatch.csv'));ss=numeric(folder/(id+'_segments.csv'))",
"""            if not item['execution_success']:
                replay=next(v for v in isolated if v['id']==id)
                retained=next(v for v in defects if v['id']==id)
                check('runtime_defect',id,matrix is None and not item['report'] and replay['rejected'] and
                      'Zero-span segment has service.' in item['error_message'] and
                      'Zero-span segment has service.' in replay['error_message'])
                prefix=numeric(folder/'defect_evidence'/(id+'_prefix_dispatch.csv'))
                check('failed_prefix_scope',id,len(prefix)==retained['retained_dispatch_samples'] and
                      replay['interval']==len(prefix)+1 and all(near(v,w) for v,w in zip(replay['input'],xs[len(prefix)])) and
                      replay['initial_energy_MWh']==retained['candidate']['initial_energy_MWh'])
                for witness in replay['witnesses']:
                    # Decode exact IEEE doubles, avoiding the CSV's 15-digit
                    # serialization, which hides the one-ULP overshoot.
                    A,B,K,R=[struct.unpack('>d',bytes.fromhex(witness[key]))[0] for key in
                             ['input_energy_hex','output_energy_hex','capacity_hex','residual_hex']]
                    strict_zero=(A==B and R==0)
                    check('padding_binary_witness',f'{id}_{witness["slot"]}',
                          witness['span_h']==0 and witness['mode']==0 and
                          all(v==0 for v in witness['power_ports']+witness['loss_and_delivery']) and
                          A>K and A-K==math.ulp(K) and B==K and R==A-B and
                          not strict_zero and witness['padding_predicate'] is False and
                          near(witness['capacity_overshoot_MWh'],A-K))
                check('padding_witness_count',id,len(replay['witnesses'])==retained['candidate']['zero_slots'] and
                      all(not v['padding_predicate'] for v in replay['witnesses']) and
                      replay['positive_segments']+len(replay['witnesses'])==64)
                continue
            ds=numeric(folder/(id+'_dispatch.csv'));ss=numeric(folder/(id+'_segments.csv'))""")
old="""    receipts=[]
    for path in sorted((ROOT/'audit').glob('Annual_sensitivity_execution_v50_*.json')):
        receipt=json.loads(path.read_text(encoding='utf-8-sig'))
        if folder.relative_to(ROOT).as_posix() in receipt['command'] and receipt['exit_code']==0:
            log=(ROOT/receipt['log_path']).read_text(encoding='utf-8-sig',errors='replace')
            check('execution',path.name,'ANNUAL_SENSITIVITY_V50' in log and 'MAT_REOPEN_V50 complete' in log)
            receipts.append(path.relative_to(ROOT).as_posix())
    check('execution','receipt',bool(receipts))
    check('scope','all_annual_executed',total_intervals==9*8760 and r['summary']['completed_annual_scenarios']==9 and total_segments==r['summary']['positive_segments'])"""
new="""    receipts=[];matrix_receipts=[];export_receipts=[];replay_receipts=[]
    for path in sorted((ROOT/'audit').glob('Annual_sensitivity_execution_v50_*.json')):
        receipt=json.loads(path.read_text(encoding='utf-8-sig'))
        if folder.relative_to(ROOT).as_posix() not in receipt['command']:continue
        log=(ROOT/receipt['log_path']).read_text(encoding='utf-8-sig',errors='replace')
        rel=path.relative_to(ROOT).as_posix()
        if 'ANNUAL_SENSITIVITY_V50 pass=60 fail=2 completed=7' in log:
            check('execution',path.name,receipt['exit_code']==1);matrix_receipts.append(rel)
        if 'MAT_REOPEN_V50 complete' in log and 'DEFECT_INSPECTION_V50 complete' in log:
            check('execution',path.name,receipt['exit_code']==0);export_receipts.append(rel)
        if 'ISOLATED_REPLAY_V50 complete' in log:
            check('execution',path.name,receipt['exit_code']==0);replay_receipts.append(rel)
        if receipt['exit_code']==0:receipts.append(rel)
    check('execution','matrix_export_replay_receipts',bool(matrix_receipts) and bool(export_receipts) and bool(replay_receipts))
    check('scope','seven_actual_annual_two_failed',total_intervals==7*8760 and r['summary']['completed_annual_scenarios']==7 and total_segments==r['summary']['positive_segments'])"""
replace(old,new)
replace("positive_segments=total_segments,max_independent_macro_residual_MWh=float(maxres),scenarios=scenarios,successful_receipts=receipts,",
"positive_segments=total_segments,max_independent_macro_residual_MWh=float(maxres),scenarios=scenarios,documented_defects=isolated,matrix_failed_receipts=matrix_receipts,successful_receipts=receipts,")
target=ROOT/'audit/verify_annual_sensitivity_defects_v50.py'
assert not target.exists()
target.write_text(source,encoding='utf-8')
print(target.relative_to(ROOT).as_posix())
