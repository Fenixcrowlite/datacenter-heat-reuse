"""Finalize the scoped defect checkpoint after actual execution and QA."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1]
folder=(ROOT/Path(sys.argv[1])).resolve();assert folder.is_relative_to(ROOT/'results')
report=json.loads((folder/'hp_annual_v47.json').read_text());s=report['summary']
qa_path=sorted(folder.glob('independent_QA_v47_*.json'))[-1];qa=json.loads(qa_path.read_text())
assert s['harness_failed']==qa['actual_failed']==qa['reviewer_selfchecks_failed']==0
assert qa['successful_receipts'] and qa['annual_nonmaximal_intervals']>0
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');now=datetime.now(timezone.utc).isoformat()
def rel(p):return p.relative_to(ROOT).as_posix()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_new(p,text):assert not p.exists(),p;p.write_text(text,encoding='utf-8')
next_task=(
    'Implement additive simulate_system_v48 using verified heat_pump_step_v40 for actual source-constrained HP output, '
    'with demand plus admissible TES charge request. Preserve v13/v2, saved Stateflow v42 and v46/v47 evidence. '
    'Initially keep the legacy TES loss-first law explicitly labelled to isolate the HP dispatch correction; '
    'do not claim equivalence to v42 exact/event TES. Recompute the entire 8760-interval dispatch and inventory trajectory, '
    'not a static capability-gap credit. Verify source limits, HP/request maximality, TES recurrence, boiler cap, unmet heat '
    'and first-law closure independently. Compare matched constant-input/no-storage cases with actual saved v42 execution; '
    'include zero-penalty compatibility and operating-cutoff domain distinctions. Feed corrected actual ports to v45/v46 '
    'period reports and equal-delivered-service comparison. Only then plan an actual annual Stateflow adapter/execution. '
    'Equipment-specific primary calibration, auxiliary loads and inventory valuation remain open.')
limitations=[
    'This checkpoint confirms an annual-reference nonmaximal HP dispatch defect; no corrected annual controller or new SLX is accepted.',
    'Fresh saved v42 execution is eight single-interval scenarios/all six modes, not annual Stateflow or a new transition-coverage campaign.',
    'Source-feasibility proof is restricted to nominal COP >= minimum >1, nonnegative source/request, valid capacity and penalty in [0,1). Arbitrary legacy configs are not certified.',
    'Closed-form comparisons restrict to a=C0*(1-r)>=cop_min: legacy upward COP clamp differs from v40 operating cutoff outside this domain.',
    '220.77157909264 MWh is static extra HP capability on the preserved legacy starting-inventory/request sequence; it is not realizable annual delivered heat, savings or a revised unmet-demand result.',
    'Annual v13 retains loss-first lumped TES, reservoir temperature proxies and synthetic weather/load/economic assumptions. Physical equivalence with saved v42 is not claimed.',
    'Independent QA uses same-agent 60-digit Decimal analytic roots/ODE expressions, not independent personnel or measured physical validation.',
    'Inherited Stateflow argument-shadow warnings and one sandbox MATLAB startup failure are retained. No user settings or runtime configuration changed.',
    'No new literature claim or source signoff: code-derived engineering equations only, full primary signoffs remain 0/31. Equipment map calibration, auxiliaries and inventory value remain unspecified.'
]
status=dict(version='0.47',timestamp_utc=now,inherits='STATUS_v46.json',stateflow_inherits='STATUS_stateflow_v42.json',
    checkpoint='Annual nominal-COP HP source-feasibility and maximality defect audit',
    result='PASS_AUDIT_NONMAXIMAL_ANNUAL_HP_DISPATCH_DEFECT_OPEN',model_version='0.42',new_model=False,
    model_executed_this_run=True,saved_model='matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx',
    model_sha256=sha(ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx'),result_directory=rel(folder),independent_qa=rel(qa_path),
    matlab_version=report['metadata']['matlab_version'],stateflow_version=report['metadata']['stateflow_version'],
    stateflow_license_observed=bool(report['metadata']['stateflow_license_test']),
    harness_passed=s['harness_passed'],harness_failed=s['harness_failed'],matlab_batch_exit_code=0,
    saved_model_scenarios=s['saved_scenarios'],saved_model_intervals=s['saved_intervals'],six_modes_executed=True,
    annual_reference_intervals=s['annual_intervals'],component_probes=s['component_probes'],
    source_feasibility_violations=qa['annual_source_feasibility_violations'],nonmaximal_annual_intervals=qa['annual_nonmaximal_intervals'],
    static_extra_capability_MWh=qa['static_extra_capability_MWh'],max_interval_gap_MW=qa['max_interval_capability_gap_MW'],
    independent_actual_passed=qa['actual_passed'],independent_actual_failed=qa['actual_failed'],
    independent_breakdown=qa['breakdown'],reviewer_selfchecks_passed=qa['reviewer_selfchecks_passed'],reviewer_selfchecks_failed=qa['reviewer_selfchecks_failed'],
    successful_receipts=qa['successful_receipts'],max_independent_balance_residual_MWh=qa['max_independent_balance_residual_MWh'],
    preserved_artifacts=len(json.loads((folder/'preservation.json').read_text())),legacy_consumers_changed=False,
    full_primary_signoffs=0,total_sources=31,primary_article_replication=False,independent_physical_validation='NOT_TESTED',
    defect_status='OPEN_ANNUAL_V13_NONMAXIMAL_HP_DISPATCH',limitations=limitations,next=next_task)
write_new(ROOT/'STATUS_v47.json',json.dumps(status,indent=2)+'\n')
example=qa['first_opportunity']
table='| Source MW | Legacy maximum MW | Saved v42 MW | Independent analytic maximum MW | Gap MW |\n|---:|---:|---:|---:|---:|\n'
for a in qa['source_comparisons']:
    table+='| '+' | '.join(f"{a[k]:.12g}" for k in ['source_MW','legacy_max_MW','saved_v42_MW','analytic_max_MW','difference_MW'])+' |\n'
results=f'''# Annual HP capability audit results — v47

{now}. Annual-reference nonmaximal HP dispatch defect CONFIRMED OPEN.
No new model/controller release. Actual accepted model remains v42.
Evidence: `{rel(folder)}`. Independent QA: `{rel(qa_path)}`.

Fresh MATLAB {status['matlab_version']}: 8760 annual v13 intervals, 72 component
vectors and eight actual saved-v42 scenarios/all six modes. MATLAB
{s['harness_passed']} PASS / 0 FAIL. Independent actual checks {qa['actual_passed']}
PASS / 0 FAIL; four separate synthetic reviewer mutations detected.
Stateflow license was observed. `ver('Stateflow')` returned an empty array;
no standalone toolbox-version value is fabricated. Inherited argument-shadow
warnings are present. Initial sandbox startup failure exit1 is retained;
the identical authorized local batch completed outside the sandbox exit0.

The annual trace has zero source-feasibility violations but
{qa['annual_nonmaximal_intervals']} nonmaximal-output intervals. Lower operating
COP needs MORE compressor work and LESS source extraction for fixed output;
the nominal-COP potential is conservative in the documented domain. Analytic
source-constraint inversion identifies additional capability at that same
starting inventory/request. Static gap {qa['static_extra_capability_MWh']:.12g}
MWh; largest interval gap {qa['max_interval_capability_gap_MW']:.12g} MW.
These are diagnostics, not annual delivery or economic savings.

Concrete first-interval counterexample ({example['time']}): source
{example['source_MW']:.12g} MW; legacy output {example['legacy_output_MW']:.12g} MW;
source unused {example['source_unused_MW']:.12g} MW. Independent maximum is
{example['analytic_max_MW']:.12g} MW, a {example['extra_capability_MW']:.12g} MW
gap while the historical trace supplies {example['legacy_gas_MW']:.12g} MW
boiler heat and records {example['legacy_unmet_MW']:.12g} MW unmet heat.

Matched HP comparisons use no charging/discharging and constant input, so TES
policy does not explain the output gap. Both actual saved-v42 outputs match
the independent 60-digit analytic root:

{table}
Independent QA reopens original annual/probe/SimulationOutput MATs and compares
all exported numeric CSV bytes and report JSON. Annual source/nominal/operating
COP, request, HP potential/output, service and TES recurrence are independently
recomputed. Eight actual segment traces pass ODE, HP/source/service allocation,
SOC/port bounds, mode authority, interval partition and first-law checks.
Maximum independent saved-segment residual
{qa['max_independent_balance_residual_MWh']:.12g} MWh. All
{status['preserved_artifacts']} preserved artifact hashes pass, as do accepted
SLX hash/archive checks and execution snapshots. Reviewer mutations of output,
source use, penalty and nominal COP are detected separately from actual checks.

No primary paper equation or empirical map is claimed. This run resolves a
code-derived engineering assumption; source signoffs remain 0/31. Accepted v42
was tested, not rebuilt or overwritten. No Jarvice/unrelated files, settings,
scheduled tasks, agent runner, secrets or external publication touched.

Limitations:

'''+''.join('- '+a+'\n' for a in limitations)+f'\nNext actionable task: {next_task}\n\nRun complete; stop with this handoff.\n'
write_new(ROOT/'audit/HP_annual_results_v47.md',results)
stage=f'''# v47 annual HP defect handoff

{now}. Scoped audit PASS; annual v13 HP output nonmaximality OPEN.
Fresh annual 8760 intervals: zero source violations, {qa['annual_nonmaximal_intervals']}
nonmaximal outputs; static extra capability {qa['static_extra_capability_MWh']:.12g} MWh.
This is not actual extra delivered heat or savings. Accepted saved v42 freshly
executes eight intervals/all six modes and matches analytic source-limited roots.
No new SLX or corrected annual dispatch is accepted.

MATLAB {s['harness_passed']}/0; independent actual {qa['actual_passed']}/0;
four reviewer mutations; {status['preserved_artifacts']} preserved hashes.
Same-agent algorithmic QA; physical validation and primary calibration OPEN.

Evidence: STATUS_v47.json; audit/HP_annual_derivation_v47.md;
audit/HP_annual_results_v47.md; {rel(folder)}; {rel(qa_path)}.

Next actionable task: {next_task}

Run complete; stop with this handoff.
'''
write_new(ROOT/'MASTER_STAGEBOARD_v47.md',stage)
progress=f'''

## {now} — v47 annual HP feasibility/maximality defect audit

Read latest STATUS/stageboard, STATEFLOW_ACCEPTANCE, research frontier, progress,
annual v13/v2/components, v42 builder/controller and v46 reporting before edits.
Accepted versioned Stateflow was already implemented/tested; preserved and
executed it afresh before any unrelated research work. Followed v46 handoff.

Derived the conservative source-use inequality and independent source-constraint
quadratic. Zero source-overdraw violations in fresh annual evidence, but
{qa['annual_nonmaximal_intervals']} nonmaximal intervals. Static capability gap
{qa['static_extra_capability_MWh']:.12g} MWh; no delivered-heat/savings claim.
Actual saved-v42 source-limited cases match independent analytic roots and use
more source than legacy potential. Documented annual dispatch defect OPEN.

Pass/fail: MATLAB {s['harness_passed']}/0; annual 8760 intervals; 72 probes;
eight actual saved-v42 intervals/all six modes. Independent actual
{qa['actual_passed']}/0 and four separate reviewer mutations. Original MATs
reopened, CSVs/JSON compared, independent Decimal root/ODE and annual recurrence,
SLX/hash/snapshot/receipt and {status['preserved_artifacts']} preservation checks.
Sandbox startup exit1 retained; identical local batch retry exit0. Inherited
Stateflow argument-shadow warnings remain. No tests failed after startup.

Files created: matlab/run_hp_annual_audit_v47.m, export_hp_annual_v47.m;
audit/prepare_hp_annual_v47.py, run_hp_annual_v47.ps1, verify_hp_annual_v47.py,
finalize_hp_annual_v47.py, check_hp_annual_release_v47.py; derivation/results,
STATUS_v47.json, MASTER_STAGEBOARD_v47.md; versioned spec/preservation/snapshots,
annual/probe CSVs and MATs, eight SimulationOutputs and dispatch/segment CSVs,
MAT reopening, independent QA, timestamped logs/receipts/manifest/postclose.
Only shared progress and acceptance ledgers appended. No model, old MATLAB
component, historical consumer or evidence overwritten. No Jarvice/unrelated
files, settings, tasks, agent runner, secrets or external publication touched.

Remaining limitations: annual corrected dispatch is not implemented; static
capability is not realized delivery; annual Stateflow not executed; legacy
upward COP clamp/cutoff distinction outside matched domain; old TES policy;
same-agent independent algorithms, no calibrated physical validation or paper
replication, full primary signoffs0/31, auxiliaries/inventory value unspecified.

Next actionable task: {next_task}
Evidence: {rel(folder)}; {rel(qa_path)};
audit/HP_annual_results_v47.md. Stop this coherent run with handoff.
'''
with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:f.write(progress)
with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
    f.write(f'\n\n## Annual HP source/maximality audit — {now} / checkpoint v47\n\n'
        f'Saved v42 freshly executes eight intervals/all six modes with matched analytic HP comparisons. '
        f'MATLAB {s["harness_passed"]}/0 and independent actual {qa["actual_passed"]}/0 plus four reviewer mutations. '
        f'Separate 8760-interval annual v13 has zero source-limit violations but {qa["annual_nonmaximal_intervals"]} '
        f'nonmaximal outputs; defect OPEN. No new SLX, corrected annual controller or annual Stateflow accepted. '
        f'STATUS_v47.json and audit/HP_annual_results_v47.md are authoritative; prior v42 acceptance preserved.\n')
paths=set(folder.rglob('*'))
paths.update(ROOT.glob('audit/*v47*'));paths.update([ROOT/'matlab/run_hp_annual_audit_v47.m',ROOT/'matlab/export_hp_annual_v47.m',ROOT/'STATUS_v47.json',ROOT/'MASTER_STAGEBOARD_v47.md'])
paths.update((ROOT/'automation/logs').glob('*v47*'))
paths={p for p in paths if p.is_file() and not p.is_relative_to(folder/'local_build')}
manifest=dict(version='0.47',timestamp_utc=now,result_directory=rel(folder),files=[
    dict(path=rel(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(paths)])
manifest_path=ROOT/'audit'/('HP_annual_manifest_v47_'+stamp+'.json')
write_new(manifest_path,json.dumps(manifest,indent=2)+'\n')
print('FINALIZED='+rel(manifest_path))
