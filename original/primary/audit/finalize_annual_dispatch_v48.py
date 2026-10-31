"""Package scoped v48 implementation acceptance; never overwrite old evidence."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
folder=(ROOT/Path(sys.argv[1])).resolve();assert folder.is_relative_to(ROOT/'results')
r=json.loads((folder/'annual_dispatch_v48.json').read_text())
qp=sorted(folder.glob('independent_QA_v48_*.json'))[-1];q=json.loads(qp.read_text())
assert r['summary']['harness_failed']==q['actual_failed']==q['reviewer_selfchecks_failed']==0
now=datetime.now(timezone.utc);timestamp=now.isoformat();stamp=now.strftime('%Y%m%dT%H%M%S_%fZ')
relative=folder.relative_to(ROOT).as_posix();qa=qp.relative_to(ROOT).as_posix()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def create(path,text):
    assert not path.exists(),str(path);path.write_text(text,encoding='utf-8')
limitations=[
    'Annual v48 is MATLAB dispatch with retained legacy loss-first Euler TES, not an annual Stateflow execution or physical equivalence with saved v42.',
    'Saved v42 freshly executes 63 intervals/71 positive segments/all six modes and 47 transitions; no new SLX, controller, model workspace or accepted model hash is changed.',
    'Independent QA uses same-agent 60-digit Decimal closed-form roots and ODE/inventory algorithms, not independent personnel or measured physical validation.',
    'Results are synthetic engineering scenarios. Reservoir COP proxies, capture/HX factors, TES loss/efficiency, weather/load and prices/emissions have no equipment-specific primary calibration here.',
    'Operating-cutoff v40 intentionally differs from legacy upward COP clamp outside the matched domain; zero-penalty compatibility is tested on one matched no-storage fixture, not every legacy configuration.',
    'HP request-maximality is a greedy interval policy, not global economic optimality. No HP latch/dwell, TES temperature cutoff, hydraulics, network transient or active-port exact TES integration in the annual adapter.',
    'Initial/terminal inventory provenance/value, auxiliary electric loads, CAPEX and source-attributed waste heat remain unspecified. Comparisons use equal actually delivered service, not full-demand savings credit.',
    'Standard finite input fixtures are certified; extreme/subnormal annual arithmetic domains and alternate polynomial HP/disabled HX combinations beyond fixtures are not comprehensively certified.',
    'Initial sandbox MATLAB startup failure and first 74-pass/1-fail run are retained. The first cutoff fixture specified COP minimum 4 below operating COP 4.0619156; corrected to 4.1. No production controller repair was needed after that fixture failure. Inherited saved-Stateflow shadow warnings remain.',
    'No new primary-text claim, paper replication or source signoff; full primary signoffs remain 0/31. Historical consumers remain preserved.'
]
next_task=('Design and test an additive annual saved-v42 input adapter with explicit TES temperature/cutoff parameters and HP hysteresis/dwell policy. Preflight all 8760 source/sink/delivery inputs against the actual model contract before running it; document unsupported regimes rather than inventing equipment calibration. Execute an initial multi-day sequence with independent port, event, inventory and report QA, then extend to actual annual execution if admissible. Compare exact/event TES with v48 loss-first traces as distinct policies; never relabel v48 MATLAB results as annual Stateflow. Primary equipment calibration, auxiliary loads and inventory valuation remain open.')
status=dict(version='0.48',timestamp_utc=timestamp,inherits='STATUS_v47.json',stateflow_inherits='STATUS_stateflow_v42.json',
    checkpoint='Corrected actual source-constrained annual MATLAB dispatch with fresh saved-Stateflow comparisons',
    result='PASS_SCOPED_ANNUAL_MATLAB_REPAIR_AND_SAVED_STATEFLOW_QA',model_version='0.42',new_model=False,model_executed_this_run=True,
    saved_model='matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx',model_sha256=sha(ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx'),
    result_directory=relative,independent_qa=qa,matlab_version=r['metadata']['matlab_version'],stateflow_version=r['metadata']['stateflow_version'],
    stateflow_license_observed=bool(r['metadata']['stateflow_license_test']),harness_passed=r['summary']['harness_passed'],harness_failed=0,matlab_batch_exit_code=0,
    annual_scenarios=len(r['annual']),annual_intervals=r['summary']['annual_intervals'],matched_fixture_intervals=9,
    saved_model_scenarios=len(r['stateflow']),saved_model_intervals=q['saved_Stateflow_intervals'],positive_segments=q['breakdown']['stateflow_ODE'],six_modes_executed=True,
    actual_period_mode_transitions=q['actual_period_mode_transitions'],annual_domain_rejections=len(r['faults']),annual_nonmaximal_intervals=q['annual_nonmaximal_intervals'],
    independent_actual_passed=q['actual_passed'],independent_actual_failed=0,independent_breakdown=q['breakdown'],reviewer_selfchecks_passed=4,reviewer_selfchecks_failed=0,
    successful_receipts=q['successful_receipts'],max_independent_first_law_residual_MWh=q['max_independent_first_law_residual_MWh'],preserved_artifacts=q['breakdown']['preservation'],
    annual_deltas=q['deltas'],annual_stateflow_executed=False,legacy_consumers_changed=False,full_primary_signoffs=0,total_sources=31,
    primary_article_replication=False,independent_physical_validation='NOT_TESTED',defect_status='V47_NONMAXIMAL_HP_REPAIRED_IN_SCOPED_ADDITIVE_V48',limitations=limitations,next_actionable_task=next_task)
create(ROOT/'STATUS_v48.json',json.dumps(status,indent=2)+'\n')
rows=[]
for a,d in zip(r['annual'],q['deltas']):
    e=a['report']['energy'];old=a['legacy_report']['energy']
    rows.append(f"| {a['cfg']['backup']['max_heat_MW']:g} | {old['unmet_heat_MWh']:.6f} | {e['unmet_heat_MWh']:.6f} | {d['unmet_reduction_MWh']:.6f} | {d['gas_heat_reduction_MWh']:.6f} |")
result=f'''# Corrected annual HP dispatch results — v48

{timestamp}. Scoped implementation acceptance PASS. The v47 nonmaximal-output
defect is repaired in additive `simulate_system_v48`; v13/v2 and all SLX baselines
remain preserved. Annual v48 is a MATLAB controller with legacy loss-first TES.
Accepted actual Stateflow remains v42, executed afresh for matched comparisons.
No new model or annual Stateflow acceptance is claimed.

Three complete 8760-hour trajectories were recomputed from the same seeded
weather/load inputs and zero starting TES. This is realized redispatch within
synthetic screening assumptions, not a sum of static capability credits.

| Boiler cap MW | Legacy unmet MWh | v48 unmet MWh | Unmet reduction MWh | Gas reduction MWh |
|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

All three trajectories produce HP heat {r['annual'][0]['report']['energy']['hp_heat_MWh']:.6f} MWh.
Relative to the matching legacy run, HP heat increases
{q['deltas'][0]['HP_heat_delta_MWh']:.6f} MWh and HP electricity increases
{q['deltas'][0]['HP_electric_delta_MWh']:.6f} MWh. Finite boiler limits determine
how increased nonboiler delivery splits between reduced unmet demand and gas.
At 20 MW backup both controllers supply all demand; delivered-heat delta is
zero within aggregate CSV/report rounding (about 1e-9 MWh).

v45/v46 actual-port period reports and equal-delivered-service comparisons are
saved per scenario. Under inherited synthetic prices/emissions, the difference
of these comparator metrics is about EUR {q['deltas'][0]['opex_difference_delta_EUR']:.6f}
and {q['deltas'][0]['CO2_difference_delta_t']:.6f} t CO2. At constrained backup the
two runs deliver different service amounts; these metric differences are not a
direct same-service comparison of the two controllers or market/calibration claims.

Validation: MATLAB {status['harness_passed']}/0 failures; 26,280 annual intervals
plus nine matched fixture intervals; 12 actual annual-domain rejections.
Actual saved-v42 execution: 10 scenarios, 63 intervals, 71 positive segments,
all six modes, 47 mode transitions in the 48-hour sequence. Three matched
no-storage cases verify source-limited output, zero-penalty compatibility and
the intentional operating-cutoff distinction. Independent 60-digit Decimal
root/inventory/ODE QA: {q['actual_passed']}/0; four separate reviewer mutations
detected. Annual nonmaximal outputs: zero. Maximum independent first-law
residual: {q['max_independent_first_law_residual_MWh']:.6g} MWh. MAT reopening,
CSV/report equality, saved SLX hash/CRC, 1100 preservation hashes and source
snapshots pass. Algorithmic independence is same-agent, not independent personnel.

Evidence: `{relative}`; `{qa}`; receipts
`{q['successful_receipts'][0]}`; `audit/Annual_dispatch_derivation_v48.md`.
Failed startup and first cutoff-fixture run remain in the earlier v48 result
folder and timestamped logs/receipts. The 4.0 cutoff fixture stayed ON because
operating COP was 4.0619156; changing its intended cutoff to 4.1 produced the
correct OFF case. No numerical traces from that run were overwritten.

Limitations:

{chr(10).join('- '+x for x in limitations)}

Next actionable task: {next_task}
'''
create(ROOT/'audit/Annual_dispatch_results_v48.md',result)
stage=f'''# v48 annual dispatch implementation handoff

{timestamp}. Scoped repair PASS. New annual MATLAB adapter uses verified HP
step v40 and explicitly retains legacy loss-first TES. Saved actual Stateflow
remains v42 and was freshly executed; no annual Stateflow/new SLX claim.

MATLAB {status['harness_passed']}/0; independent {q['actual_passed']}/0; four separate
reviewer mutations; 12 domain rejections; 26,280 full-year intervals plus nine
matched fixture intervals. Actual saved-v42: 63 intervals/all six modes/47
transitions. Corrected annual output has zero nonmaximal intervals. At 2 MW
backup, unmet heat falls by {q['deltas'][1]['unmet_reduction_MWh']:.6f} MWh on synthetic inputs.

Evidence: STATUS_v48.json; audit/Annual_dispatch_derivation_v48.md;
audit/Annual_dispatch_results_v48.md; {relative}; {qa}.

Next actionable task: {next_task}

Run complete; stop with this handoff.
'''
create(ROOT/'MASTER_STAGEBOARD_v48.md',stage)
progress=f'''

## {timestamp} — v48 source-constrained annual MATLAB repair

Read latest STATUS/stageboard, STATEFLOW_ACCEPTANCE, research frontier, progress,
annual v13/v2 and HP/TES/reporting components plus saved-v42 builder/controller
before edits. Existing versioned Stateflow acceptance was confirmed; preserved
and executed saved v42 afresh with independent QA. Followed v47 defect handoff.

Implemented additive simulate_system_v48 with actual source-constrained HP step
v40, demand plus admissible TES charge request, explicit operating cutoff,
finite boiler/unmet, TES inventory/loss ports and first-law assertions. Retained
legacy loss-first TES to isolate the HP correction. Recomputed three 8760-hour
trajectories and passed actual ports through v45/v46 reports. At 2 MW backup,
unmet falls {q['deltas'][1]['unmet_reduction_MWh']:.6f} MWh; this is synthetic realized
dispatch, not static capability credit or physical validation.

Pass/fail: MATLAB {status['harness_passed']}/0; annual 26,280 intervals plus nine matched
fixture intervals; 12 runtime domain rejections; saved v42 10 scenarios/63
intervals/71 positive segments/all six modes/47 transitions. Independent
actual {q['actual_passed']}/0; four separately labelled reviewer mutations. Independent
Decimal roots, inventory recurrence and ODE checks, actual energy/cost/CO2
report integration, original MAT reopening, CSV/JSON equality, SLX CRC/hash,
1100 preserved-artifact hashes and source snapshots. Zero corrected nonmaximal
outputs; max first-law residual {q['max_independent_first_law_residual_MWh']:.6g} MWh.

Files created: matlab/+dchr/simulate_system_v48.m; matlab/run_annual_dispatch_v48.m;
matlab/export_annual_dispatch_v48.m; audit/prepare_annual_dispatch_v48.py,
run_annual_dispatch_v48.ps1, verify_annual_dispatch_v48.py,
finalize_annual_dispatch_v48.py; derivation/results, STATUS_v48.json,
MASTER_STAGEBOARD_v48.md; versioned spec/preservation/snapshots/annual and
matched MAT/CSVs, SimulationOutputs/dispatch/segment traces, reports/MAT reopen,
independent QA and timestamped logs/receipts. Shared progress/acceptance ledgers
appended only. No old component/model/evidence or historical consumer changed.
No Jarvice/unrelated files, settings, scheduled tasks, agent runner, secrets or
external publication touched.

Failures retained: sandbox MATLAB startup failed before project execution;
local retry first ran 74 PASS/1 FAIL because cutoff fixture minimum4.0 was below
its operating COP4.0619156. Corrected synthetic fixture to4.1, created a fresh
result directory, reran all relevant tests, obtained75/0. Production adapter
unchanged. Inherited Stateflow shadow warnings remain. Earlier evidence and
source snapshot remain immutable.

Limitations: {chr(10).join('- '+x for x in limitations)}

Next actionable task: {next_task}
Evidence: {relative}; {qa}. Stop this coherent run with handoff.
'''
with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:f.write(progress)
with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
    f.write(f'''\n\n## Corrected annual MATLAB checkpoint — {timestamp} / v48

Saved v42 freshly executes 63 intervals/71 positive segments/all six modes/47
transitions. Additive v48 annual MATLAB adapter recomputes26,280 intervals with
source-constrained HP and explicitly retained loss-first TES. MATLAB75/0,
independent actual106795/0 and four reviewer mutations; zero corrected
nonmaximal outputs. No new SLX or annual Stateflow accepted. Physical validation
and primary calibration remain OPEN. STATUS_v48.json and
audit/Annual_dispatch_results_v48.md are authoritative. Next: explicit annual
saved-v42 input/domain adapter before actual annual Stateflow execution.
''')
paths=[ROOT/'STATUS_v48.json',ROOT/'MASTER_STAGEBOARD_v48.md',ROOT/'audit/Annual_dispatch_derivation_v48.md',ROOT/'audit/Annual_dispatch_results_v48.md']
paths.extend(p for p in folder.rglob('*') if p.is_file() and 'local_build' not in p.parts)
paths.extend(p for p in (ROOT/'matlab').rglob('*v48*') if p.is_file())
paths.extend(p for p in (ROOT/'audit').glob('*v48*') if p.is_file())
paths.extend(p for p in (ROOT/'automation/logs').glob('*v48*') if p.is_file())
manifest=ROOT/'audit'/('Annual_dispatch_manifest_v48_'+stamp+'.json')
create(manifest,json.dumps(dict(timestamp_utc=timestamp,version='0.48',files=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(set(paths))]),indent=2)+'\n')
print(json.dumps(dict(status='PASS',manifest=manifest.relative_to(ROOT).as_posix(),status_file='STATUS_v48.json',independent_qa=qa),indent=2))
