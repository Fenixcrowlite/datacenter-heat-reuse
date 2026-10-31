"""Publish local checkpoints only after executed evidence and independent QA pass."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,csv,sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,s):
    assert not p.exists(),p
    p.write_text(s,encoding='utf-8')
def main():
    folder=ROOT/sys.argv[1];r=json.loads((folder/'annual_sensitivity_v52.json').read_text())
    qa_path=sorted(folder.glob('independent_QA_v52_*.json'))[-1];qa=json.loads(qa_path.read_text())
    checks=json.loads((folder/'repair_assertions_v52.json').read_text())
    assert qa['actual_failed']==qa['reviewer_selfchecks_failed']==r['summary']['harness_failed']==0
    assert all(v['passed'] for v in checks) and r['summary']['completed_annual_scenarios']==9
    stamp=datetime.now(timezone.utc).isoformat();spec=json.loads((folder/'spec.json').read_text());prior=ROOT/spec['v51_failed_evidence']
    failed=[json.loads((prior/(id+'_evidence.json')).read_text()) for id in [v['id'] for v in r['stateflow']]]
    diagnostic=json.loads((folder/'unaccepted_v51_protocol_diagnostic.json').read_text())
    diagnostic['mismatches']=diagnostic['mismatches'] if isinstance(diagnostic['mismatches'],list) else [diagnostic['mismatches']]
    assert all(not v['execution_success'] and 'Ordered event/energy handoff failure.' in v['error_message'] for v in failed)
    v51=dict(version='0.51',timestamp_utc=stamp,inherits='STATUS_v50.json',result='UNACCEPTED_HOST_COMPILED_ENDPOINT_HANDOFF_DEFECT',
        corrected_model_accepted=False,accepted_model_version='0.42',candidate_model='matlab/simulink/DCHR_Dispatch_Stateflow_v51.slx',
        candidate_model_sha256=sha(ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v51.slx'),six_modes_executed=True,
        exact_v50_seeds_repaired=2,annual_attempts=9,annual_completed=0,
        initial_harness_passed=19,initial_harness_failed=4,reviewed_physical_reference_passed=23,
        result_directory=prior.relative_to(ROOT).as_posix(),diagnostic= (folder/'unaccepted_v51_protocol_diagnostic.json').relative_to(ROOT).as_posix(),
        limitations=['No v51 acceptance: all nine annual attempts reject at exact energy handoff.','Initial reference harness conflated attempted HP request with OFF-latch request. Revised original-MAT physical comparison23/0; failed checks/log/source preserved.','Empty-matrix export failed after per-scenario MAT/JSON evidence was retained.','Diagnostic continuity relaxation is temporary/in-memory and explicitly not acceptance.'],
        next_actionable_task='Use explicit canonical endpoint protocol, independently retain ODE/first-law checks; test additive v52.')
    put(ROOT/'STATUS_v51.json',json.dumps(v51,indent=2)+'\n')
    put(ROOT/'MASTER_STAGEBOARD_v51.md','# v51 unaccepted endpoint handoff defect\n\nNine annual attempts reject; both exact v50 seeds and six simple modes pass. Saved v51 is preserved but not accepted. See STATUS_v51.json and the labelled binary diagnostic; additive v52 is the corrective task.\n')
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v52.slx'
    limitations=[
      'Scoped implementation acceptance. No measured physical validation or primary-paper replication; full primary signoffs remain0/31.',
      'Annual policies use deterministic synthetic inputs and fixed85C condenser/tank,20C ambient. Finite HX approach, equipment maps, auxiliaries, hydraulics and weather/load calibration remain open.',
      'Canonical positive endpoints are bounded within64 eps(max(1,capacity)); roundoff remains in first-law residual and is not physical loss/service. Zero-duration state/service/clock identity and macro memory remain exact.',
      '64 bounded intra-macro segments execute in normal mode with a host MATLAB planner; standalone generated-code deployment and universal numerical-domain proof are untested.',
      'Independent QA is algorithmic evidence review by the same agent using Decimal equations/exact binary decoding, not independent personnel.',
      'v51 is an unaccepted intermediate release; all original failed simulations/logs, prior models and v50 evidence are preserved. Temporary relaxed-gate v51 diagnostics never count as accepted simulations.',
      'v30 fixture comparison covers all physical columns; diagnostic attempted request differs when HP latch is OFF. Annual pairedv48 policy retains loss-first TES and differs jointly in cutoff/latch/integration.',
      'Initial sandbox MATLAB startup failed before project execution. Authorized local batches run; inherited Stateflow shadow warnings remain.',
      'Primary reference/calibration, CAPEX, pumping/network transients, terminal inventory valuation and multi-coordinate interactions remain unspecified.'
    ]
    next_task='Audit the primary evidence and derive a finite-temperature HP/TES interface with explicit condenser/evaporator versus reservoir/HX temperatures, tank delivery cutoff and auxiliary-energy boundary. Use source20 verified text/upstream62 provenance; distinguish inaccessible equipment-map calibration from engineering assumptions. Establish domain/energy equations and independent tests before proposing another model. Preserve accepted v52 and all failed/control evidence; do not repeat the annual matrix without a new change or unresolved defect.'
    status=dict(version='0.52',timestamp_utc=stamp,inherits='STATUS_v51.json',stateflow_inherits='STATUS_stateflow_v42.json',
        result='ACCEPTED_CANONICAL_ENDPOINT_PROTOCOL_WITH_EXECUTED_ANNUAL_MATRIX',corrected_model_accepted=True,defect_status='REPAIRED_IN_TESTED_FIXTURES',
        model_version='0.52',new_model=True,saved_model=model.relative_to(ROOT).as_posix(),model_sha256=sha(model),model_executed_this_run=True,
        attempted_annual_scenarios=9,completed_annual_scenarios=9,saved_model_intervals=r['summary']['saved_intervals'],positive_segments=r['summary']['positive_segments'],
        required_mode_coverage=list(range(6)),exact_seed_repairs=2,harness_passed=r['summary']['harness_passed'],harness_failed=0,
        focused_harness_passed=sum(v['passed'] for v in checks),focused_harness_failed=0,actual_runtime_fault_rejections=33,
        independent_actual_passed=qa['actual_passed'],independent_actual_failed=0,reviewer_selfchecks_passed=qa['reviewer_selfchecks_passed'],reviewer_selfchecks_failed=0,
        max_independent_macro_residual_MWh=qa['max_independent_macro_residual_MWh'],result_directory=folder.relative_to(ROOT).as_posix(),independent_qa=qa_path.relative_to(ROOT).as_posix(),
        matlab_version=r['metadata']['matlab_version'],stateflow_version=r['metadata']['stateflow_version'],stateflow_license_observed=bool(r['metadata']['stateflow_license_test']),
        full_primary_signoffs=0,total_sources=31,primary_article_replication=False,independent_physical_validation='NOT_TESTED',
        scenarios=qa['scenarios'],limitations=limitations,next_actionable_task=next_task)
    for path in ('STATUS_v52.json','STATUS_stateflow_v52.json'):put(ROOT/path,json.dumps(status,indent=2)+'\n')
    table='| Policy | Intervals | Unmet MWh | Delta baseline MWh | Terminal MWh |\n|---|---:|---:|---:|---:|\n'
    for v in qa['scenarios']:table+=f"| {v['id']} | {v['intervals']} | {v['unmet_MWh']:.6f} | {v['unmet_delta_baseline_MWh']:+.6f} | {v['terminal_inventory_MWh']:.6f} |\n"
    report=f'''# v52 canonical endpoint protocol results

{stamp}. Actual new saved model0.52 passes both exactv50 defect seeds, all six
required modes, six representative physical-output comparisons withv30,
33 actual runtime fault rejections and nine fresh8760-interval annual policies.
Focused MATLAB{status['focused_harness_passed']}/0; annual MATLAB{status['harness_passed']}/0;
independent actualQA{qa['actual_passed']}/0; reviewer self-checks{qa['reviewer_selfchecks_passed']}/0.
Maximum independent first-law residual{qa['max_independent_macro_residual_MWh']:.9g}MWh.

Exact origin instrumentation binds its plans bit-for-bit to the preservedv42
planner. Both original overshoots arise in capacity-maintenance tails with no
final remainder; this corrects the initial remainder-path hypothesis. A common
kernel repairs those two seeds inv51, but all nine annualv51 attempts reject:
shared host/compiled arithmetic is not bit-identical. The labelled diagnostic
records{len(diagnostic['mismatches'])} exact handoff mismatch(es) at interval{diagnostic['interval']},
under a temporary in-memory continuity relaxation solely to expose raw output.
It is not accepted model execution. V52 explicitly carries the canonical end
state and independently checks its ODE consistency before allocation adopts it.
Exact padding/clock/handoff/macro-memory assertions remain enforced and verified
from original MAT exports with independent binary decoding.

The firstv51 fixture harness had four false failures comparing attempted versus
latch-authorized HP request. Every physical output agrees withv30; the corrected
comparison excludes only request diagnostic column22. Original failed assertions,
logs, source and corrected23/0 original-MAT review remain preserved. The first
origin instrumentation matched plans but missed per-segment records due Windows
newline matching; the retained second version normalizes line endings and asserts
record counts. No prior simulation evidence or model is overwritten.

{table}

Evidence: {folder.relative_to(ROOT).as_posix()}; independent QA:
{qa_path.relative_to(ROOT).as_posix()}. Detailed derivations:
audit/TES_canonical_endpoint_derivation_v51.md and audit/TES_endpoint_protocol_derivation_v52.md.

Remaining limitations:

'''+''.join('- '+v+'\n' for v in limitations)+'\nNext actionable task: '+next_task+'\n'
    put(ROOT/'audit/TES_endpoint_protocol_results_v52.md',report)
    for path in ('MASTER_STAGEBOARD_v52.md','MASTER_STAGEBOARD_stateflow_v52.md'):
        put(ROOT/path,report)
    progress='\n\n## '+stamp+' — v51 defect audit and accepted v52 canonical endpoint protocol\n\n'
    progress+='Read STATUS/stageboardv50, acceptance ledger, research frontier, progress and actual builder/planner/gate/HP/TES/reference code before changes. Implemented/tested additive v51; preserved its confirmed host/compiled exact-handoff defect. Corrected via additive v52 explicit canonical endpoint protocol, retaining independent ODE/first-law checks and strict padding/clock/state identity.\n\n'
    progress+=f"Pass/fail: exactv50 seeds repaired2/2; six modes; focused MATLAB{status['focused_harness_passed']}/0;33 runtime faults; annual MATLAB{status['harness_passed']}/0,9 years/{status['saved_model_intervals']} intervals/{status['positive_segments']} positive segments; independent actual{qa['actual_passed']}/0; reviewer mutations{qa['reviewer_selfchecks_passed']}/0. Original v51 initial19/4 harness, reviewed23/0 physical-reference audit,9/9 annual rejections, empty-matrix export failure and sandbox startup failure retained. v51 relaxed-gate diagnostic is not acceptance.\n\n"
    files=sorted(p.relative_to(ROOT).as_posix() for p in list((ROOT/'matlab').rglob('*v51*'))+list((ROOT/'matlab').rglob('*v52*'))+list((ROOT/'audit').glob('*v51*'))+list((ROOT/'audit').glob('*v52*')) if p.is_file() and '__pycache__' not in p.parts)
    progress+='Files created/changed: '+', '.join(files)+'; STATUS/stageboardsv51/v52; new immutable result folders, numeric/binary/MAT traces, snapshots, timestamped logs/receipts and QA. Shared progress/acceptance ledgers appended. Prior sources/models/data preserved; no unrelated files, Jarvice, settings, schedules, runner, secrets or publication touched.\n\n'
    progress+='Remaining limitations:\n\n'+''.join('- '+v+'\n' for v in limitations)+'\nNext actionable task: '+next_task+'\n\nEvidence: '+status['independent_qa']+'. Stop this coherent run with handoff.\n'
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:f.write(progress)
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
        f.write(f"\n\n## Canonical endpoint protocol acceptance — {stamp} / v52\n\nNew actual savedv52 executes all six modes and9 annual policies/{status['saved_model_intervals']} intervals; two exactv50 repairs,33 runtime fault rejections, MATLABfocused{status['focused_harness_passed']}/0+annual{status['harness_passed']}/0, independent{qa['actual_passed']}/0+reviewer{qa['reviewer_selfchecks_passed']}/0. Unacceptedv51 host/compiled defect preserved; strict zero-span identity, exact energy handoff and macro memory retained. STATUS_stateflow_v52 and audit/TES_endpoint_protocol_results_v52.md authoritative. Scoped implementation only; no calibrated physical validation/article replication.\n")
    print('FINALIZED_V52',json.dumps({k:status[k] for k in ['model_version','saved_model_intervals','positive_segments','independent_actual_passed','max_independent_macro_residual_MWh']}))
if __name__=='__main__':main()
