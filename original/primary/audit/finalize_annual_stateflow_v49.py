"""Publish local checkpoint only after actual batch and independent QA pass."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'results/annual_stateflow_v49_20261010T224401_242369Z'
r=json.loads((folder/'annual_stateflow_v49.json').read_text());qp=sorted(folder.glob('independent_QA_v49_*.json'))[-1];q=json.loads(qp.read_text())
assert r['summary']['harness_failed']==q['actual_failed']==q['reviewer_selfchecks_failed']==0
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');now=datetime.now(timezone.utc).isoformat()
next_task=('Execute a matched annual sensitivity matrix on saved v42 at fixed 85C condenser/source/load and identical initial inventory. Vary delivery cutoff, resolved restart band and ON/OFF dwell separately; retain runtime domain/event-budget failures and independently verify actual ports, dwell, inventory and energy reports. Compare each with the paired v48 loss-first policy and report usable inventory K-Ecut, terminal inventory and joint policy differences without attributing them to numerical error. Use this evidence to decide whether an additive variable-temperature TES/HP interface is justified. Primary equipment calibration, auxiliaries and measured physical validation remain open.')
annual=next(x for x in r['stateflow'] if x['id']=='annual_8760h');e=annual['report']['energy'];pe=r['paired_report']['energy']
limits=[
    'Actual saved model remains version 0.42 and its accepted SLX hash is unchanged; v49 versions the explicit annual input adapter and executed harness, not a new SLX/controller.',
    'Original weather-scheduled condenser/delivery boundary is unsupported by a fixed cutoff/tank maximum. All 8760 rows are explicitly rejected for the specified tank; no annual simulation of that boundary is claimed.',
    'Fixed 85C condenser, 85C tank maximum, 80C delivery cutoff, 48 MWh restart, 0.25h ON/OFF dwell and 20C ambient are synthetic engineering assumptions, not primary equipment calibration. Zero condenser/tank approach is permitted by the reduced model but has no finite-HX/hydraulic validation.',
    'Nominal 50 MWh tank has only 3.8461538462 MWh above the 80C cutoff. Cold initial E=0 is initially unusable. Passive heat loss can cool below cutoff; discharge cannot cross it.',
    'Static preflight checks every input with saved v42 physical-domain validation but does not guarantee state-dependent event progress or clock/event budgets for unexecuted scenarios. Adapter scope is the weather/Carnot boundary only.',
    'Annual trajectory executes modes 2,3,4,5; all six required modes are executed in separate preserved six-case fixtures. Annual transitions and positive segments are actual trace counts, not six-mode annual coverage.',
    'Physical segments execute within macro timesteps through 64 bounded Stateflow slots, not at solver-clock event times. Normal-mode HP planner uses host MATLAB calls; standalone generated-code deployment is not tested.',
    'Independent QA is same-agent algorithmic/evidence QA with 60-digit Decimal equations and independent physical-time sums from serialized numeric traces. It is not independent personnel, binary-interval proof for all arithmetic domains, measured physical validation or article replication.',
    'Paired v48 comparison holds HP lift/source/demand fixed and matches passive retention only. Temperature cutoff/usable inventory, active-port integration and hysteresis/dwell differ jointly. Cost/CO2 use equal actually delivered service; policy differences are not isolated causal effects or an economic optimum.',
    'Initial/terminal inventory provenance/value, auxiliaries, pumping, network transients, CAPEX and calibrated weather/load/equipment maps remain unspecified. Full primary signoffs remain 0/31; no new research-text claim this run.',
    'Sandbox MATLAB startup failed before project execution and is retained. Normal local retry passed all 61 MATLAB checks. Inherited Stateflow shadow warnings remain.',
    'Initial independent review had three evidence-check failures: JSON-versus-CSV exact equality, a legitimate unnamed MATLAB assert, and a preserved pre-existing unaccepted draft derivation. Revised QA uses numeric serialization tolerance, retained rejection messages and a hashed explicit draft revision record; original numeric/model evidence is unchanged and first failed QA remains preserved.'
]
s=dict(version='0.49',timestamp_utc=now,inherits='STATUS_v48.json',stateflow_inherits='STATUS_stateflow_v42.json',
    checkpoint='Explicit annual input/domain adapter and actual saved-v42 full-year Stateflow execution',
    result='PASS_SCOPED_ACTUAL_ANNUAL_STATEFLOW_WITH_EXPLICIT_ENGINEERING_BOUNDARY',model_version='0.42',new_model=False,
    saved_model='matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx',model_sha256=hashlib.sha256((ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx').read_bytes()).hexdigest(),
    model_executed_this_run=True,annual_stateflow_executed=True,result_directory=folder.relative_to(ROOT).as_posix(),independent_qa=qp.relative_to(ROOT).as_posix(),
    matlab_version=r['metadata']['matlab_version'],stateflow_version=r['metadata']['stateflow_version'],stateflow_license_observed=bool(r['metadata']['stateflow_license_test']),
    harness_passed=r['summary']['harness_passed'],harness_failed=0,matlab_batch_exit_code=0,annual_intervals=8760,saved_model_intervals=q['saved_intervals'],
    positive_segments=q['positive_segments'],annual_positive_segments=annual['positive_segments'],six_modes_executed=True,annual_modes=q['annual_modes'],
    actual_annual_mode_transitions=q['annual_mode_transitions'],actual_latch_transitions=q['actual_latch_transitions'],
    annual_admitted_rows=r['summary']['fixed_admitted_rows'],native_scheduled_rejected_rows=r['summary']['scheduled_rejected_rows'],adapter_domain_rejections=len(r['faults']),
    independent_actual_passed=q['actual_passed'],independent_actual_failed=0,reviewer_selfchecks_passed=q['reviewer_selfchecks_passed'],reviewer_selfchecks_failed=0,
    max_independent_macro_residual_MWh=q['max_independent_macro_residual_MWh'],successful_receipts=q['successful_receipts'],preserved_artifacts=q['breakdown']['preservation'],
    actual_annual_energy=e,paired_loss_first_energy=pe,joint_policy_delta_MWh=q['joint_policy_delta_MWh'],
    full_primary_signoffs=0,total_sources=31,primary_article_replication=False,independent_physical_validation='NOT_TESTED',limitations=limits,next_actionable_task=next_task)
def write_new(path,value):
    assert not path.exists(),f'Preserve {path}'
    path.write_text(value if isinstance(value,str) else json.dumps(value,indent=2)+'\n',encoding='utf-8')
write_new(ROOT/'STATUS_v49.json',s)
table='| Actual integrated quantity | Saved v42 annual | Paired loss-first v48 |\n|---|---:|---:|\n'
for key in ['heat_demand_MWh','total_delivered_MWh','unmet_heat_MWh','hp_heat_MWh','hp_electric_MWh','gas_heat_MWh','storage_charge_MWh','storage_discharge_MWh','hp_heating_COP_integrated']:
    table+=f"| {key} | {e[key]:.9f} | {pe[key]:.9f} |\n"
text=(f'# Actual annual saved-Stateflow results — v49\n\n{now}. Scoped implementation acceptance PASS.\n\n'
    f'MATLAB {s["harness_passed"]}/0; independent actual {q["actual_passed"]}/0 and five separate reviewer self-checks. '
    f'Actual annual saved v42: 8760 intervals/{annual["positive_segments"]} positive segments/{q["annual_mode_transitions"]} thermal-mode transitions. '
    f'Annual modes {q["annual_modes"]}; all six modes passed in six actual acceptance fixtures. '
    f'Three-day cold prefix72 plus six fixtures gives total {q["saved_intervals"]} intervals/{q["positive_segments"]} positive segments. '
    f'{q["actual_latch_transitions"]} actual latch changes checked. Maximum independent macro first-law residual {q["max_independent_macro_residual_MWh"]:.8g} MWh.\n\n'
    'All 8760 direct seasonal condenser rows reject the specified fixed tank. Explicit separately admitted 85C condenser supports original scheduled delivery up to80C; this is a new engineering boundary, not calibration. '
    'The full original scenario is unsupported in the fixed-temperature model. Static admissibility is distinguished from actual trajectory acceptance.\n\n'+table+
    f'\nStateflow unmet minus paired v48 unmet is {e["unmet_heat_MWh"]-pe["unmet_heat_MWh"]:.9f} MWh. '
    'Both comparisons use actual delivered service. The tank cutoff reduces usable inventory; the controller also cycles HP and trades storage losses/electricity against boiler/unmet. '
    'These are joint policy effects, not a claim of improvement or an isolated integration-error estimate.\n\n'
    'Evidence: STATUS_v49.json; spec.json, immutable source_snapshot and snapshot_revisions_v49.json; original SimulationOutputs/MAT, reopened exports, numeric dispatch/segment/clock traces, reports; timestamped execution receipts/logs; independent QA JSON and reviewer source snapshots. '
    f'{s["preserved_artifacts"]} prior artifact hashes and accepted SLX CRC/hash pass. Initial sandbox startup and first failed independent review remain saved. '
    'No controller/model/numeric artifact changed to obtain revised independent acceptance. Pre-existing unaccepted derivation draft is preserved in the first source snapshot, with a hashed final revision record.\n\n'
    'Limitations:\n\n'+''.join('- '+v+'\n' for v in limits)+f'\nNext actionable task: {next_task}\n')
write_new(ROOT/'audit/Annual_stateflow_results_v49.md',text)
write_new(ROOT/'MASTER_STAGEBOARD_v49.md',f'# v49 actual annual Stateflow handoff\n\n{now}. Scoped annual saved-v42 execution PASS; model release remains0.42. No new SLX.\n\nMATLAB61/0; independent{q["actual_passed"]}/0; five separate reviewer self-checks. Annual8760 intervals/{annual["positive_segments"]} positive segments/{q["annual_mode_transitions"]} thermal transitions; modes2–5 in annual, all six in fixtures. 8760 native rows explicitly rejected; 8760 fixed85C rows admitted. Paired policy increases unmet by{e["unmet_heat_MWh"]-pe["unmet_heat_MWh"]:.6f} MWh, a joint cutoff/dwell/storage effect.\n\nEvidence: STATUS_v49.json; audit/Annual_stateflow_derivation_v49.md; audit/Annual_stateflow_results_v49.md; {folder.relative_to(ROOT).as_posix()}; {qp.relative_to(ROOT).as_posix()}.\n\nNext actionable task: {next_task}\n\nRun complete; stop with this handoff.\n')
with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:
    f.write(f'\n\n## {now} — v49 actual annual saved-Stateflow adapter and execution\n\n'
        'Read latest STATUS/stageboard, STATEFLOW_ACCEPTANCE, research frontier, progress, existing annual/HP/TES/report code and saved-v42 builder/planner/guards before changes. Confirmed original versioned-model acceptance; followed v48 handoff.\n\n'
        'Implemented additive adapt_annual_stateflow_v49, static row preflight and explicit tank/cutoff/lift/dwell policy. Derived direct seasonal boundary incompatibility and preserved all8760 rejections. Admitted separately declared fixed85C condenser scenario, executed actual72h cold gate then saved-v42 annual8760h, and reopened original MAT/SimulationOutputs. Compared actual annual traces with same-lift paired v48 loss-first dispatch as distinct control/storage policies. No new SLX or controller alteration.\n\n'
        f'Pass/fail: MATLAB61/0; independent actual{q["actual_passed"]}/0; reviewer mutations5/0; ten adapter rejections; total8838 actual intervals/{q["positive_segments"]} positive segments/all six modes across fixtures. Annual18495 positive segments/{q["annual_mode_transitions"]} thermal-mode transitions; {q["actual_latch_transitions"]} actual HP latch transitions; first law residual{q["max_independent_macro_residual_MWh"]:.8g}MWh. {s["preserved_artifacts"]} prior artifact hashes and accepted SLX hash/CRC preserved.\n\n'
        'Files created/updated: matlab/+dchr/adapt_annual_stateflow_v49.m; matlab/run_annual_stateflow_v49.m; matlab/export_annual_stateflow_v49.m; audit/prepare_annual_stateflow_v49.py, run_annual_stateflow_v49.ps1, verify_annual_stateflow_v49.py, finalize_annual_stateflow_v49.py, check_annual_stateflow_release_v49.py; v49 derivation/results/status/stageboard; timestamped logs/receipts, source/preservation snapshots, preflight tables, actual MAT/traces/reopened exports, comparison reports and independent QA. Pre-existing unaccepted v49 derivation draft revised and retained in original snapshot with hashed revision record. Shared progress/acceptance ledgers appended only. No Jarvice/unrelated files, user settings, scheduled tasks, agent runner, secrets or publication touched.\n\n'
        'Failures retained: sandbox MATLAB fatal startup occurred before project execution; normal local retry passed61/0. Initial independent QA258632pass/3fail exposed exact CSV/JSON comparison, unnamed legitimate clock assert and obsolete draft snapshot. Corrected reviewer evidence handling, preserved failed QA and reviewer source, reran to258635/0; model, MATLAB production and numeric artifacts unchanged. Inherited Stateflow shadow warnings remain.\n\n'
        'Remaining limitations:\n\n'+''.join('- '+v+'\n' for v in limits)+f'\nNext actionable task: {next_task}\nEvidence: {folder.relative_to(ROOT).as_posix()}; {qp.relative_to(ROOT).as_posix()}. Stop this coherent run with handoff.\n')
with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
    f.write(f'\n\n## Actual annual saved-v42 acceptance — {now} / checkpoint v49\n\n'
        f'No new SLX: saved0.42 actually executes8760 annual intervals/18495 positive segments plus72h cold prefix and six mode fixtures. MATLAB61/0; independent actual{q["actual_passed"]}/0; five reviewer self-checks; ten adapter rejections. Annual mode coverage2–5; all six required modes in fixtures. Native seasonal condenser/fixed-tank boundary is explicitly unsupported; separate85C condenser is synthetic engineering, not equipment calibration. Paired cutoff/dwell/storage policies increase unmet by{e["unmet_heat_MWh"]-pe["unmet_heat_MWh"]:.6f}MWh. STATUS_v49 and audit/Annual_stateflow_results_v49.md are authoritative; model hash and prior evidence preserved. Primary calibration/physical validation remain open. Next: matched cutoff/restart/dwell sensitivity.\n')
files=set(ROOT.glob('audit/*v49*'))|set(ROOT.glob('automation/logs/*v49*'))|{ROOT/'STATUS_v49.json',ROOT/'MASTER_STAGEBOARD_v49.md',ROOT/'matlab/+dchr/adapt_annual_stateflow_v49.m',ROOT/'matlab/run_annual_stateflow_v49.m',ROOT/'matlab/export_annual_stateflow_v49.m'}
files.update(p for p in folder.rglob('*') if p.is_file() and 'local_build' not in p.parts)
manifest=dict(timestamp_utc=now,excludes='Mutable append-only progress/acceptance ledgers and generated local_build caches.',files=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(files) if p.is_file()])
mp=ROOT/'audit'/('Annual_stateflow_manifest_v49_'+stamp+'.json');write_new(mp,manifest)
print(json.dumps(dict(status='STATUS_v49.json',manifest=mp.relative_to(ROOT).as_posix(),sealed_files=len(manifest['files']),actual_annual_unmet_MWh=e['unmet_heat_MWh'],paired_unmet_MWh=pe['unmet_heat_MWh']),indent=2))
