"""Close v36 only after actual saved-model execution and independent QA.

All previous artifacts are preserved. Mutable project ledgers are appended.
"""
import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rel(path):return str(Path(path).resolve().relative_to(ROOT))
def save(path,value):
    assert not path.exists(),path
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def readrows(path):
    with path.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def main():
    ap=argparse.ArgumentParser()
    for arg in ['folder','qa','build_receipt','execution_receipt','export_receipt']:ap.add_argument(arg)
    args=ap.parse_args();folder=Path(args.folder).resolve();qa_path=Path(args.qa).resolve()
    receipt_paths=[Path(getattr(args,n)).resolve() for n in ['build_receipt','execution_receipt','export_receipt']]
    receipts=[load(p) for p in receipt_paths]
    qa=load(qa_path);summary=load(folder/'summary_v36.json');snap=folder/'source_snapshot'
    spec=load(snap/'spec/cases.json');equations=load(snap/'spec/equation_checks.json')
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v36.slx'
    checks=[]
    def ck(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    ck('three actual MATLAB exits',all(r['exit_code']==0 for r in receipts))
    ck('build receipt', 'build_dispatch_stateflow_v36' in receipts[0]['command'])
    ck('execution receipt','run_stateflow_admissibility_v36' in receipts[1]['command'])
    ck('separate export receipt','export_stateflow_admissibility_v36' in receipts[2]['command'])
    ck('versions',summary['version']==summary['model_version']==qa['version']==qa['model_version']=='0.36')
    required={'numeric','artifact','partition','faults','time','archive','legacy','synthetic','preservation'}
    ck('all required independent QA sections',set(qa['counts'])==required)
    for group in required:
        count=qa['counts'].get(group,{})
        ck(group+' passed',isinstance(count.get('passed'),int) and count['passed']>0 and count.get('failed')==0)
        cc=qa['checks'].get(group,[])
        ck(group+' counts bound',count.get('passed')==len(cc) and all(c.get('passed') is True for c in cc))
    ck('equations',equations['failed']==0 and equations['passed']>=500 and all(c['passed'] for c in equations['checks']))
    ck('saved model',digest(model)==qa['model_sha256']==digest(snap/model.name))
    ck('exact reviewer',digest(ROOT/'audit/verify_stateflow_v36.py')==qa['reviewer_sha256']==digest(snap/'verify_stateflow_v36.py'))
    for path in snap.glob('*'):
        if path.is_file() and path.suffix in ['.py','.m']:
            current=ROOT/'audit'/path.name if path.suffix=='.py' else ROOT/'matlab/simulink'/path.name
            if not current.is_file():current=ROOT/'matlab/+dchr/+components'/path.name
            ck(path.name+' source binding',current.is_file() and digest(path)==digest(current))
    tt=readrows(folder/'trace_v36.csv');ss=readrows(folder/'segments_v36.csv');aa=readrows(folder/'assertions_v36.csv')
    ck('actual MATLAB assertions',summary['failed']==0 and summary['passed']==len(aa) and all(r['passed'] in ['1','true'] for r in aa))
    ck('actual trace counts',summary['scenarios']==len(spec['cases'])==51 and summary['intervals']==len(tt) and len(ss)==64*len(tt))
    ck('positive segments',summary['positive_segments']==sum(float(r['Duration_h'])>0 for r in ss))
    ck('six executed modes',{int(float(r['Mode'])) for r in ss if float(r['Duration_h'])>0}==set(range(6)))
    ck('all actual clock faults rejected',summary['actual_fault_trials']==summary['faults_rejected']==4 and summary['faults_incorrectly_accepted']==0)
    ck('all actual general faults rejected',summary['runtime_fault_trials']==summary['runtime_faults_rejected']==30)
    ck('all actual dimensional faults rejected',summary['extended_fault_trials']==summary['extended_faults_rejected']==21)
    log=(ROOT/receipts[1]['log_path']).read_text(encoding='utf-8-sig',errors='replace')
    ck('executed output receipt binding','AUDIT_OUTPUT='+str(folder) in log)
    ck('cleanup not invalid','Invalid or deleted object' not in log)
    residual=max(abs(float(r['System_Balance_Residual_MWh'])) for r in tt)
    ck('reported residual',abs(residual-summary['max_abs_balance_residual_MWh'])<=1e-14*max(1e-15,residual))
    for kind,field in [('physical_validation','physical_validation'),('article_replication','article_replication')]:
        ck(kind+' honest',summary[field] is False and qa[field] is False)
    now=datetime.now(timezone.utc);tag=now.strftime('%Y%m%dT%H%M%S_%fZ')
    completion=ROOT/'audit'/f'Stateflow_completion_QA_v36_{tag}.json'
    save(completion,dict(timestamp_utc=now.isoformat(),passed=sum(c['passed'] for c in checks),
        failed=sum(not c['passed'] for c in checks),checks=checks,
        evidence_class='completion_source_receipt_scope_bindings_not_additional_model_tests'))
    assert all(c['passed'] for c in checks),completion
    next_task=('Audit near-boundary numerical admissibility and the remaining host HP/domain validation: '
        'exercise restart/capacity separation near energy ulps, short segments and long persistent ages with held and changing inputs; '
        'derive a supported resolution/parameter domain and reject unsupported cases before extending any physical claims. '
        'Preserve v36 acceptance and v34/v35 counterexamples; keep primary equipment assumptions uncalibrated.')
    limits=[
        'Implementation acceptance of finite tested fixtures only; numerical stress capacities are not plausible installations.',
        'Time budget capped at 1e-8 h; direct admissibility probes do not establish deployment at arbitrary ages or sensor timing accuracy.',
        'Binding OFF dwell can leave unmet demand; ON dwell has capacity/input safety overrides.',
        'Normal-mode host planner; up to 64 analytic physical-time segments share macro solver timestamps, no solver-clock event scheduler or standalone code generation.',
        'No measured/calibrated physical validation, stratification/hydraulics, startup/cycling-loss model or primary article replication; full article signoffs remain 0/31.',
        'Nonfatal Stateflow formal-argument shadow warnings remain visible. Independent QA is algorithm/artifact QA, not separate human/agent review.',
        'Unchanged inherited HP/domain/component routines still require their own numerical-domain audit.'
    ]
    status=dict(version='0.36',inherits='STATUS_stateflow_v35.json',research_inherits='STATUS_v25.json',
        timestamp_utc=now.isoformat(),checkpoint='Executed dimensional-tolerance Stateflow release',
        stateflow_acceptance='PASS_IMPLEMENTATION_ONLY',model_version='0.36',new_model=True,
        generated_model=rel(model),model_sha256=digest(model),controller_defect='v35 dimensioned-clock defect repaired for all tested scales',
        result_directory=rel(folder),independent_qa=rel(qa_path),completion_qa=rel(completion),
        build_receipt=rel(receipt_paths[0]),execution_receipt=rel(receipt_paths[1]),mat_export_receipt=rel(receipt_paths[2]),
        execution_log=receipts[1]['log_path'],matlab_batch_exit_code=0,
        scenarios=summary['scenarios'],intervals=summary['intervals'],positive_segments=summary['positive_segments'],
        segment_slots=len(ss),matlab_checks_passed=summary['passed'],matlab_checks_failed=0,
        actual_runtime_fault_trials=55,actual_runtime_faults_rejected=55,
        direct_time_component_probes=34,independent_check_breakdown=qa['counts'],
        equation_checks_passed=equations['passed'],equation_checks_failed=0,
        previous_immutable_entries_preserved=qa['previous_unique_entries'],max_abs_balance_residual_MWh=residual,
        full_primary_signoffs=0,total_sources=31,primary_article_replication=False,
        independent_physical_validation='NOT_TESTED',limitations=limits,next=next_task)
    status_path=ROOT/'STATUS_stateflow_v36.json';save(status_path,status)
    text=f'''# v36 executed dimensional-tolerance Stateflow repair

UTC {now.isoformat()}. Implementation acceptance PASS; physical validation not tested.

New saved v36: {summary['scenarios']} scenarios / {summary['intervals']} intervals /
{summary['positive_segments']} positive segments / six modes. MATLAB {summary['passed']}/{summary['passed']} PASS;
55/55 actual runtime faults rejected. Independent QA has zero failures;
{equations['passed']} equation checks pass. All four .01 h clock corruptions and
all four forced early restarts reject independently of TES scale. v34/v35 preserved.

Evidence: STATUS_stateflow_v36.json; audit/TES_dimensional_tolerances_derivation_v36.md;
audit/TES_dimensional_tolerances_results_v36.md; {rel(qa_path)}.

Next: {next_task}
'''
    stage=ROOT/'MASTER_STAGEBOARD_stateflow_v36.md';assert not stage.exists();stage.write_text(text,encoding='utf-8')
    result=ROOT/'audit/TES_dimensional_tolerances_results_v36.md';assert not result.exists()
    result.write_text(f'''# v36 saved-Stateflow execution results

{text.splitlines()[2]}

MATLAB R2026a Update 5 executed the saved new model: {summary['passed']} assertions,
zero failures; {summary['scenarios']} scenarios, {summary['intervals']} intervals,
{summary['positive_segments']} positive segments and {len(ss)} slots. Six modes
are observed. A separate MATLAB batch re-exported the saved SimulationOutputs.

The v35 .01 h clock-corruption counterexample now rejects at 10, 1e4, 1e6 and
1e9 MWh. The .24 h versus .25 h guard probes reject at every scale. Actual
host-planner mutations force early restart at each scale and are rejected by
the runtime authorization gate. Power (.01 MW), COP (.01), temperature (.01 K)
and offset (.01 h) mutations reject at all four scales. A 1e9 h initial clock
is rejected for insufficient declared resolution. Together with the inherited
30 general faults, there are 55 actual runtime rejections. Thirty additional
ON/OFF boundary/helper probes and four early-guard probes are component tests.

Independent QA breakdown: `{json.dumps(qa['counts'])}`. Equation checks:
{equations['passed']} PASS. {qa['previous_unique_entries']} prior immutable entries
retain their hashes and sizes. The saved SLX functions, guarded states and
memory connections bind to the current sources and executed snapshot.
Six representative cases compare actual saved v32 flows/energy; COP and HP-OFF
request conventions remain explicit. Held-input closed-cycle and changing-input
partition comparisons use the observed traces, not just expected vectors.

Maximum absolute clean balance residual: {residual:.12g} MWh. This maximum is
from numerical stress; an energy cancellation allowance is never used for
time, power, temperature or COP. Numeric traces retain individual residuals.

Evidence: `{rel(folder)}`, `{rel(qa_path)}`, `{rel(completion)}`.
Build/execution/export observed zero-exit receipts:
`{rel(receipt_paths[0])}`, `{rel(receipt_paths[1])}`, `{rel(receipt_paths[2])}`.

Initial sandbox startup failed before testing. The first compile and first
simulation exposed vector concatenation errors in the new tolerance code;
they were repaired, with logs/source snapshots retained. No warnings were
hidden by settings changes. No new equipment value or primary article
equation was adopted.

Remaining limits:

'''+''.join(f'- {s}\n' for s in limits)+f'\nNext actionable task: {next_task}\n',encoding='utf-8')
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
        f.write(f'\n\n## Dimensional-tolerance repair acceptance — {now.isoformat()} / v36\n\n'
            f'New saved v36: {summary["scenarios"]} scenarios/{summary["intervals"]} intervals/{summary["positive_segments"]} positive segments/six modes; '
            f'{summary["passed"]} MATLAB assertions, 55 actual runtime rejections, {equations["passed"]} independent equation checks, independent QA zero failures. '
            'The v35 clock/guard defect is repaired at all four tested scales, including actual forced early-restart rejection. '
            'v34/v35 and all prior immutable evidence are preserved. Authoritative status/stageboard v36 and dimensional-tolerance derivation/results record implementation acceptance only; physical validation/article replication remain open.\n')
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:
        f.write(f'\n\n## {now.isoformat()} — v36 executed dimensional-tolerance Stateflow repair\n\n'
            'Read current status/stageboard, acceptance, frontier, progress, production and independent-reference code before changes. '
            'Implemented additive actual v36 model with separate MWh/MW/K/COP/hour budgets, explicit physical-time precision rejection, guard and monitor repair. '
            'Unified prior v34 acceptance and v35 changing-input/scale counterexamples; retained independent Decimal/bisection and RK4 evidence.\n\n'
            f'Pass/fail: MATLAB build, simulation and separate MAT export exit 0; {summary["passed"]}/{summary["passed"]} assertions PASS; '
            f'{summary["scenarios"]} scenarios/{summary["intervals"]} intervals/{summary["positive_segments"]} positive segments/six modes. '
            f'55/55 actual runtime faults reject; 34 direct time probes PASS; equations {equations["passed"]}/{equations["passed"]} PASS; '
            f'independent QA {json.dumps(qa["counts"])}; {qa["previous_unique_entries"]} prior immutable entries preserved. '
            f'Max balance residual {residual:.12g} MWh (stress scale). Sandbox startup, compile and initial simulation failures retained and repaired.\n\n'
            'Files created: matlab/simulink/*v36.m and DCHR_Dispatch_Stateflow_v36.slx; audit v36 source generators, specification/reviewer/finalizer/runner, derivation/results; '
            'fresh MAT/CSV/source traces, QA, status/stageboard, timestamped receipts/logs and manifest. Existing progress/acceptance ledgers appended only.\n\n'
            'Finding: .01 h allocator-clock corruption and .24/.25 h guards reject at every tested energy scale; actual forced early restarts also reject. '
            'Power/COP/temperature/offset injections reject scale-independently; unsupported clock resolution fails explicitly. '
            'Six cases agree with verified saved v32 flows/energy; held-input and changing-input partition tests agree for finite fixtures.\n\n'
            'Remaining limitations: '+' '.join(limits)+'\n\nNext actionable task: '+next_task+'\n\n'
            'Run stops at a coherent implementation acceptance and handoff. No Jarvice/unrelated files, user settings, scheduler, agent runner, secrets or external publication changed.\n')
    paths=set(folder.rglob('*'))|set((ROOT/'audit').glob('*v36*'))|set((ROOT/'matlab/simulink').glob('*v36*'))
    paths|={status_path,stage,result,completion,qa_path,*receipt_paths}
    for rp,r in zip(receipt_paths,receipts):paths.add(ROOT/r['log_path'])
    paths|={p for p in (ROOT/'automation/logs').glob('*v36*.log') if not p.name.startswith('stateflow_finalize_v36_')}
    for p in list(paths):
        if p.is_dir():paths.update(p.rglob('*'))
    manifest=ROOT/'audit'/f'Stateflow_manifest_v36_{tag}.json'
    files=[dict(path=rel(p),sha256=digest(p),bytes=p.stat().st_size) for p in sorted(paths) if p.is_file() and p.suffix!='.pyc']
    save(manifest,dict(timestamp_utc=now.isoformat(),files=files,exclusions=['mutable acceptance/progress ledgers','active finalizer log','later post-close artifacts']))
    print('STATUS='+rel(status_path));print('MANIFEST='+rel(manifest));print('COMPLETION_QA='+rel(completion))

if __name__=='__main__':main()
