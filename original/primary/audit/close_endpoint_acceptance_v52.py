"""Close resumed acceptance only after both independent reviewers and batches pass."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
import finalize_endpoint_protocol_v52 as finalize

ROOT=Path(__file__).resolve().parents[1]
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    path=sorted(folder.glob('endpoint_binary_QA_v52_*.json'))[-1]
    extra=json.loads(path.read_text())
    assert extra['actual_failed']==extra['reviewer_selfchecks_failed']==0
    qa_path=sorted(folder.glob('independent_QA_v52_*.json'))[-1]
    qa=json.loads(qa_path.read_text())
    assert qa['actual_failed']==qa['reviewer_selfchecks_failed']==0
    tags={'PADDING_REPAIR_V52','ANNUAL_SENSITIVITY_V52','MAT_REOPEN_V52 complete','ENDPOINT_BINARY_V52'}
    observed=set();receipts=[]
    for p in sorted((ROOT/'audit').glob('Stateflow_padding_execution_v52_*.json')):
        receipt=json.loads(p.read_text(encoding='utf-8-sig'))
        if folder.relative_to(ROOT).as_posix() not in receipt['command']:continue
        if receipt['exit_code']!=0:continue
        log=(ROOT/receipt['log_path']).read_text(encoding='utf-8-sig',errors='replace')
        observed.update(tag for tag in tags if tag in log);receipts.append(p.relative_to(ROOT).as_posix())
    assert observed==tags,(tags-observed)
    finalize.main()
    stamp=datetime.now(timezone.utc).isoformat()
    for name in ('STATUS_v52.json','STATUS_stateflow_v52.json'):
        p=ROOT/name;status=json.loads(p.read_text())
        status.update(binary_endpoint_qa=path.relative_to(ROOT).as_posix(),binary_endpoint_actual_passed=extra['actual_passed'],binary_endpoint_actual_failed=0,
            binary_endpoint_selfchecks_passed=extra['reviewer_selfchecks_passed'],binary_endpoint_selfchecks_failed=0,
            acceptance_batch_receipts=receipts,continuation_timestamp_utc=stamp,
            candidate_model_preexisted_this_run=True,new_model_built_this_run=False)
        p.write_text(json.dumps(status,indent=2)+'\n')
    note=f'\n\nAcceptance continuation {stamp}: the saved v52 candidate and builder already existed at run start. This run resumed implementation acceptance in a fresh immutable evidence folder, completing actual six-mode/fault/annual execution and original-MAT exports. Separate exact-binary/70-digit ODE QA {extra["actual_passed"]}/0, reviewer self-checks {extra["reviewer_selfchecks_passed"]}/0. Evidence: {path.relative_to(ROOT).as_posix()}. Its 72-ULP equation budget includes the existing 64-ULP normalization allowance and eight ULPs for comparison to exact arithmetic; no production tolerance was changed. Both original one-ULP padding counterexamples and host/compiled-state diagnostics are retained.\n'
    for name in ('audit/TES_endpoint_protocol_results_v52.md','MASTER_STAGEBOARD_v52.md','MASTER_STAGEBOARD_stateflow_v52.md','automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md'):
        with (ROOT/name).open('a',encoding='utf-8') as f:f.write(note)
    print('RESUMED_ACCEPTANCE_V52 CLOSED',len(receipts),'successful batch receipts')
if __name__=='__main__':main()
