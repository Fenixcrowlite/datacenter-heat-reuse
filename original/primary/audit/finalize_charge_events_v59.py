from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    report=json.loads((folder/'report.json').read_text());sf=json.loads((folder/'stateflow/report.json').read_text())
    qp=sorted(folder.glob('independent_QA_v59_*.json'))[-1];qa=json.loads(qp.read_text())
    sp=sorted((folder/'stateflow').glob('independent_QA_v57_*.json'))[-1];sq=json.loads(sp.read_text())
    assert all(v['summary']['failed']==0 for v in [report,sf,qa,sq])
    assert qa['reviewer_selfchecks']['failed']==0 and all(v['passed'] for v in sq['reviewer_selfchecks'])
    assert qa['regimes']==10 and sq['counts']['mode_coverage']==list(range(6))
    assert qa['status_counts']['ISOLATED_EVENT_BLOCKED']>0 and qa['status_counts']['HORIZON_UNRESOLVED_BLOCKED']>0
    assert all(not v['event']['memory_handoff_authorized'] and not v['event']['event_transition_authorized'] for v in report['runs'])
    for rec in json.loads((folder/'preservation.json').read_text()):assert sha(ROOT/rec['path'])==rec['sha256']
    for rec in json.loads((folder/'source_hashes.json').read_text()):assert sha(ROOT/rec['path'])==rec['sha256']==sha(folder/'source_snapshot'/rec['path'])
    stamp=datetime.now(timezone.utc).isoformat();relative=folder.relative_to(ROOT).as_posix()
    next_task=('Implement an additive correlated event record that retains the exact branch/limiter manifold, incoming trajectory and time/energy/source/work/loss/HP-clock enclosures; support interval initial inventory and exactly equivalent persistent limiter ties. Execute the v59 nonrepresentable branch/hot-flow fixture across the event without midpoint/snap/reset or service credit for unresolved time. Then integrate a new continuously tank-linked Stateflow model preserving v57 compiled finite-water guards and v52 cutoff/restart/dwell, with actual six-mode/fault/reference and original-MAT independent QA. Preserve v52-v59; no unchanged annual-matrix reruns. Primary equipment calibration remains OPEN.')
    status=dict(version='0.59',timestamp_utc=stamp,inherits='STATUS_v58.json',result='EVENT_ISOLATION_PASS_CORRELATED_STATEFLOW_HANDOFF_BLOCKED',
        model_version='0.57',new_model=False,saved_model='matlab/simulink/DCHR_Dispatch_Stateflow_v57.slx',model_sha256=sq['model_sha256'],
        model_executed_this_run=True,coupled_stateflow_acceptance=False,finite_water_stateflow_acceptance='INHERITED_V57_AND_FRESHLY_REEXECUTED',
        matlab_version=sf['metadata']['matlab_version'],stateflow_license_observed=sf['metadata']['stateflow_license_test'],
        stateflow_version=sf['metadata']['stateflow_version'],sfroot_class=sf['metadata']['sfroot_class'],chart_count=sf['metadata']['chart_count'],
        event_matlab_passed=report['summary']['passed'],event_matlab_failed=report['summary']['failed'],event_runs=qa['cases'],event_regimes=qa['regimes'],
        event_status_counts=qa['status_counts'],certified_crossing_counts=qa['certified_crossing_counts'],
        stateflow_matlab_passed=sf['summary']['passed'],stateflow_matlab_failed=sf['summary']['failed'],actual_scenarios=len(sf['cases']),
        actual_runtime_fault_rejections=sum(v['rejected'] for v in sf['faults']),reference_comparisons=len(sf['references']),
        independent_event_passed=qa['summary']['passed'],independent_event_failed=qa['summary']['failed'],
        independent_stateflow_passed=sq['summary']['passed'],independent_stateflow_failed=sq['summary']['failed'],
        event_reviewer_selfchecks=qa['reviewer_selfchecks'],stateflow_reviewer_selfchecks=len(sq['reviewer_selfchecks']),
        stateflow_counts=sq['counts'],original_event_binary_values=qa['binary_values'],exact_branch_endpoint_MWh=qa['exact_branch_endpoint_MWh'],
        adjacent_binary64_energy_MWh=qa['adjacent_binary64_energy_MWh'],
        defect_status='NONREPRESENTABLE_BRANCH_ENDPOINT_PERSISTENT_EQUIVALENT_LIMITER_TIE_AND_CORRELATED_HANDOFF_OPEN',
        full_primary_signoffs=0,total_sources=31,primary_article_replication=False,independent_physical_validation='NOT_TESTED',
        result_directory=relative,independent_event_qa=qp.relative_to(ROOT).as_posix(),independent_stateflow_qa=sp.relative_to(ROOT).as_posix(),
        derivation='audit/Charge_event_protocol_derivation_v59.md',
        limitations=['No new SLX or continuously coupled controller. v59 certifies pre-event prefixes/event windows; one-sided mathematical policy is specified, correlated representation and executable Stateflow handoff remain OPEN.',
            'Conditional binary64 round-to-nearest/gradual-underflow outward arithmetic, |kt|<=1; maximum128 bisections. Uncertain signs/adjacent times stop refinement. No user-specified event-width accuracy guarantee.',
            'Fixed-regime continuation beyond the first event is only a root-isolation diagnostic. Physical port energy is integrated on half the certified prefix; no post-event service credit or scalar memory handoff.',
            'Exact symbolic event lies strictly between adjacent doubles; persistent branch/hot-flow/request equality needs equivalent-limiter handling. Current scalar strict APIs reject both adjacent continuations.',
            'Synthetic finite-water/HP/TES assumptions; no equipment maps, finite UA/hydraulics, measured calibration or article replication. No new primary literature this run; inherited signoffs0/31.',
            'Same-agent independent Fraction/120-/160-digit algorithms and original-MAT QA; independent personnel/physical validation not performed. Reviewer mutations are separate synthetic self-checks.',
            'Saved v57 held-macro boundary/normal-mode host planner/64 slots and inherited shadow warnings remain. Stateflow license/charts/execution observed; version list is empty.',
            'Development evidence retained: sandbox MATLAB startup failure and missing nested batch receipt caught by Stateflow QA. Receipt packaging repaired; stationary-equivalence derivation clarified before final sealed-source execution.'],
        next_actionable_task=next_task)
    for name in ['STATUS_v59.json','STATUS_stateflow_v59.json']:
        path=ROOT/name;assert not path.exists();path.write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    text=f'''# Event-isolation checkpoint v59 — correlated Stateflow handoff blocked

UTC {stamp}. Accepted saved plant remains **0.57**; no new SLX or continuously coupled controller accepted.

New event isolator: {qa['cases']} runs / ten charge regimes,
MATLAB {report['summary']['passed']} PASS / 0 FAIL,
independent exact-Fraction/120-/160-digit/original-MAT QA {qa['summary']['passed']} PASS / 0 FAIL,
five separate reviewer mutations. Status counts: {json.dumps(qa['status_counts'])}.
Branch/capacity and four distinct limiter crossing types are certified.
Simultaneous branch/hot-flow windows retain both contenders; uncertain signs do not authorize a side.

Blocking defect: exact branch energy {qa['exact_branch_endpoint_MWh']} MWh lies
strictly between adjacent doubles {qa['adjacent_binary64_energy_MWh']}.
The post-branch request/hot-flow tie persists; both scalar continuations reject.
One-sided mathematical policy specified; correlated energy/time/clock handoff remains OPEN.

Saved v57 actually reexecuted {len(sf['cases'])} scenarios / {sq['counts']['intervals']} intervals /
{sq['counts']['positive_segments']} positive segments / all six modes;
MATLAB {sf['summary']['passed']} PASS / 0 FAIL, twelve actual runtime fault rejections,
six verified v30 references; independent QA {sq['summary']['passed']} PASS / 0 FAIL,
seven separate reviewer mutations. Prior models, sources and status hashes preserved.

Evidence: `{relative}`. Derivation/protocol: `audit/Charge_event_protocol_derivation_v59.md`.
No primary calibration, measured physical validation or article replication accepted.
Development startup/receipt errors are retained separately from final sealed-source evidence.

Next actionable task: {next_task}
'''
    for name in ['MASTER_STAGEBOARD_v59.md','MASTER_STAGEBOARD_stateflow_v59.md','audit/Charge_event_protocol_results_v59.md']:
        path=ROOT/name;assert not path.exists();path.write_text(text,encoding='utf-8')
    progress=f'''\n\n## {stamp} — v59 event isolation and concrete correlated Stateflow endpoint blocker

Read STATUS/stageboard/Stateflow acceptance/research frontier/progress and v54–v58
component/builder/harness/reviewer code before changes. Implemented additive outward
eight-guard first-event isolation, certified pre-event prefix and contender grouping.
Independent analytic log-time roots/energy/port integration use Fraction and 120/160
decimal digits on original reopened MAT binary exports. Specified one-sided equality,
equivalent persistent limiter and correlated time/energy/HP-clock handoff requirements.

Event MATLAB {report['summary']['passed']} PASS/0 FAIL; {qa['cases']} runs/ten regimes;
independent {qa['summary']['passed']}/0 and five separate reviewer mutations.
Actual saved v57: MATLAB {sf['summary']['passed']}/0, {sq['counts']['intervals']} intervals,
all six modes, twelve actual runtime rejections, six v30 references; independent
{sq['summary']['passed']}/0 and seven separate reviewer mutations. Timestamped batch/
reviewer logs, numeric traces, original MATs and immutable source snapshot retained
in `{relative}`. All prior MATLAB/model/status/stageboard hashes unchanged.
Development evidence `results/charge_events_v59_20261011T114519_963980Z` preserved:
sandbox startup failure and nested-receipt QA failure. Receipt workflow repaired;
the separate 115010 development snapshot is retained after a stationary-equivalence
derivation clarification; no production numerical change was made for that clarification.
final evidence comes from fresh sealed-source batch and independent reviewers.

Files: matlab/+dchr/+components/charge_event_window_v59.m,
matlab/run_charge_events_v59.m; audit/prepare/run/verify/finalize_charge_events_v59,
Charge_event_protocol_derivation/results, STATUS_v59/STATUS_stateflow_v59 and
MASTER_STAGEBOARD_v59/stateflow_v59. Shared acceptance/progress appended only.
No Jarvice/unrelated files, settings, schedules, runner, secrets or publication touched.

Scope/blocker: no new SLX or corrected continuous-coupled Stateflow acceptance.
Exact branch endpoint {qa['exact_branch_endpoint_MWh']} lies between adjacent doubles;
post-branch request/hot-flow equality persists. The scalar API cannot retain the
event constraint and rejects both adjacent continuations. Only physical prefix
ports are integrated; post-event continuation is diagnostic. Transition/memory
handoff flags remain false. Conditional arithmetic/span and no event-width guarantee;
same-agent independent algorithms; synthetic physics/primary calibration/measured
validation OPEN, inherited signoffs0/31. Saved v57 scope/warnings remain explicit.

Next actionable task: {next_task}
Stop after this coherent prerequisite/blocker checkpoint and clear handoff.
'''
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as stream:stream.write(progress)
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as stream:
        stream.write(f'\n\n## Event-isolation / correlated-handoff blocker — {stamp} / checkpoint v59\n\nNo new SLX. Actual saved v57 executes six modes, twelve runtime faults and six v30 references; MATLAB{sf["summary"]["passed"]}/0, independent{sq["summary"]["passed"]}/0. New v59 event isolator: {qa["cases"]} runs/ten regimes, MATLAB{report["summary"]["passed"]}/0, independent{qa["summary"]["passed"]}/0 plus five separate mutations. Simultaneous contender/equality protocol specified. Exact branch threshold between adjacent doubles and persistent limiter tie are concrete scalar/correlated-handoff blockers. No event transition or coupled controller accepted. STATUS_stateflow_v59 and derivation/results authoritative; calibration/article replication/physical validation remain OPEN.\n')
    evidence=[p for p in folder.rglob('*') if p.is_file() and 'local_build' not in p.parts]
    release=[ROOT/n for n in ['STATUS_v59.json','STATUS_stateflow_v59.json','MASTER_STAGEBOARD_v59.md','MASTER_STAGEBOARD_stateflow_v59.md','audit/Charge_event_protocol_results_v59.md','automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md']]
    mp=ROOT/'audit'/('Charge_event_protocol_manifest_v59_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')+'.json')
    manifest=dict(version='0.59',timestamp_utc=stamp,files=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in evidence+release])
    mp.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    assert all(sha(ROOT/v['path'])==v['sha256'] for v in manifest['files'])
    print(json.dumps(dict(result=status['result'],manifest=mp.relative_to(ROOT).as_posix(),files=len(manifest['files']))))
if __name__=='__main__':main()
