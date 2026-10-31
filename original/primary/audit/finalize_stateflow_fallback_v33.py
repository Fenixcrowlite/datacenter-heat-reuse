"""Close the executed fallback defect checkpoint without altering model v32."""
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
from stateflow_fallback_v33 import ROOT, sha, save, stamp
from verify_stateflow_completion_v32 import readcsv

def main(folder,qa_path):
    folder=folder.resolve();qa_path=qa_path.resolve()
    qa=json.loads(qa_path.read_text());s=json.loads((folder/'summary_v33.json').read_text())
    rc=json.loads((ROOT/qa['receipt']).read_text(encoding='utf-8-sig'))
    assert qa['failed']==s['failed']==rc['exit_code']==0
    assert qa['model_sha256']==sha(ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v32.slx')
    for item in json.loads((folder/'source_snapshot/spec/preservation.json').read_text()):
        p=ROOT/item['path'];assert p.stat().st_size==item['bytes'] and sha(p)==item['sha256'],item['path']
    now=datetime.now(timezone.utc).isoformat();tag=stamp()
    rows=readcsv(folder/'fallback_sensitivity_v33.csv');pulse=[r for r in rows if r['family']=='unavailable_tail']
    assert len(pulse)==5 and all(float(r['unmet_MWh'])>6 for r in pulse)
    assert int(pulse[-1]['HP_state_changes'])>int(pulse[0]['HP_state_changes'])
    d=json.loads((folder/'source_snapshot/spec/dwell_example.json').read_text())
    evidence=dict(timestamp_utc=now,primary_engineering_documentation=[
        dict(url='https://bigladdersoftware.com/epx/docs/9-5/engineering-reference/water-thermal-tanks-includes-water-heaters.html',
             evidence='primary_text_verified',locator='Mixed Water Thermal Tank / Energy Balance and Water Heater Control Algorithm',
             adopted='constant-coefficient solution/inverse method only; no parameter values'),
        dict(url='https://www.mathworks.com/help/stateflow/ug/using-temporal-logic-in-state-actions-and-transitions.html',
             evidence='primary_software_text_verified_R2026b_page',locator='Define Time Delays / Best Practices for Temporal Logic',
             adopted='timing design caution only; no new temporal API executed')],
        research_discovery=[
        dict(url='https://www.mdpi.com/1996-1073/13/17/4339',doi='10.3390/en13174339',
             evidence='search_index_only_NOT_full_text_verified',full_text_attempt='HTTP 429 via web retrieval',
             adopted_equations_or_values=False),
        dict(url='https://doi.org/10.1016/j.renene.2024.121409',doi='10.1016/j.renene.2024.121409',
             evidence='search_index_only_NOT_full_text_verified',full_text_attempt='inaccessible Elsevier redirect via web retrieval',
             adopted_equations_or_values=False)],full_primary_signoffs=0,total_sources=31,
        inherited_primary_article='audit/TES_standing_loss_primary_v28.md')
    source_path=ROOT/'audit'/f'Stateflow_fallback_sources_v33_{tag}.json';save(source_path,evidence)
    limitations=[
        'Checkpoint v33 executes unchanged saved model v32; no new SLX or corrected production controller.',
        'Capacity-tail TES-service defect remains open despite passing implementation/oracle assertions.',
        'Four-hour, five-family, five-timestep assumed sensitivity study; no universal optimizer or policy-superiority claim.',
        'Proposed hysteresis/dwell equations and RK4 example are not an executed Stateflow policy or calibrated equipment requirement.',
        'Iterator segments share macro solver time; physical-hour timers and seconds-based Stateflow temporal logic need explicit unit handling.',
        'Normal-mode host planner; standalone code generation, stratification, hydraulics, calibration and physical validation remain untested.',
        'v32 six-mode/fault acceptance inherited; v33 does not add equipment faults, cycling losses, delayed nonfinite faults or runtime corruption coverage.',
        'Independent algorithm/artifact QA is not separate human/agent review or paper replication; full primary signoffs remain 0/31.',
        'New research candidates were search-index discovery only; full-text retrieval failed and no equations/values were adopted.'
    ]
    nxt='Implement additive Stateflow model v34 with persistent HP hysteresis/dwell latch, explicit physical-duration timers, TES service during HP OFF and a bounded multi-event integrator; test exact-capacity initialization, changing inputs, finite backup, cutoff safety, timer units and timestep partitions against the preserved v32 counterexample.'
    status=dict(version='0.33',inherits='STATUS_stateflow_v32.json',research_inherits='STATUS_v25.json',timestamp_utc=now,
        checkpoint='Executed saved-v32 capacity-fallback sensitivity and independently derived restart/dwell constraints',
        experiment_acceptance='PASS',stateflow_acceptance_inherited='PASS_v32',model_version='0.32',new_model=False,
        generated_model='matlab/simulink/DCHR_Dispatch_Stateflow_v32.slx',model_sha256=qa['model_sha256'],
        controller_defect='CONFIRMED_OPEN: capacity tail leaves usable TES idle while demand is unmet',
        result_directory=str(folder.relative_to(ROOT)),independent_qa=str(qa_path.relative_to(ROOT)),
        execution_receipt=qa['receipt'],execution_log=rc['log_path'],matlab_batch_exit_code=rc['exit_code'],
        scenarios=s['scenarios'],intervals=s['intervals'],segments=s['segments'],matlab_checks_passed=s['passed'],matlab_checks_failed=0,
        independent_check_breakdown=qa['categories'],equation_checks_passed=qa['equation_checks_passed'],equation_checks_failed=0,
        previous_immutable_entries_preserved=qa['previous_entries_preserved'],
        max_abs_balance_residual_MWh=s['max_abs_balance_residual_MWh'],
        full_primary_signoffs=0,total_sources=31,primary_article_replication=False,independent_physical_validation='NOT_TESTED',
        limitations=limitations,next=nxt)
    report='# v33: executed capacity fallback defect and sensitivity\n\n'
    report+=f'UTC: {now}. Checkpoint v33 executes the unchanged accepted model v32. '
    report+=f"MATLAB {s['passed']}/{s['passed']} assertions PASS over 25 scenarios, 310 intervals and 620 segment slots; "
    report+=f"maximum balance residual {s['max_abs_balance_residual_MWh']:.8g} MWh. Independent equations: {qa['equation_checks_passed']}/643 PASS.\n\n"
    report+='**Confirmed open controller defect:** when loss-replacement HP request falls below its assumed part-load COP cutoff, '
    report+='the capacity tail disables HP and TES discharge. Demand remains unmet although TES starts the tail at capacity above the delivery cutoff. '
    report+='At an initial capacity sample, the same unavailable HP permits discharge; that branch difference has executed evidence. '
    report+='These successful reproduction assertions establish a defect, not corrected-controller acceptance.\n\n'
    report+='For the low-load unavailable-tail fixture (4 h, E0=9.9 MWh, D=3 MW, backup=.5 MW):\n\n'
    report+='| Macro step (h) | End TES (MWh) | HP electricity (MWh) | Unmet (MWh) | HP availability changes |\n|---:|---:|---:|---:|---:|\n'
    for r in pulse:report+=f"| {float(r['dt_h']):g} | {float(r['endpoint_MWh']):.6f} | {float(r['electric_MWh']):.6f} | {float(r['unmet_MWh']):.6f} | {r['HP_state_changes']} |\n"
    report+='\nAvailability changes count adjacent ordered positive-duration HP states reconstructed from analytic segments; '
    report+='they are not measured compressor cycles or solver-clock transitions. Finer macro steps increase modeled switching and '
    report+='do not remove unmet demand in this fixture. Initial-capacity unmet varies non-monotonically over the tested steps '
    report+='(2.219359, 1.605507, 3.811313, 5.020353, 5.648135 MWh).\n\n'
    report+='Controls: feasible modulation holds the tank at 10 MWh, with 4.460839839 MWh HP electricity and zero unmet across '
    report+='all five tested steps. Constant-COP source shortage at initial capacity gives E(4)=8.681280184 MWh and electricity '
    report+='2/3 MWh across all steps. Passive cooling gives E(4)=6.703200460 MWh. Under fixed inputs, monotonic source extraction '
    report+='proves that reaching capacity with admitted high HP load cannot create a source shortage at a smaller admitted '
    report+='loss-replacement load; minimum-load unavailability and initial-state source shortage are distinct.\n\n'
    report+=f"Independent QA categories: `{qa['categories']}`; zero failures. {qa['previous_entries_preserved']} unique earlier immutable entries retained. "
    report+='Separate MAT re-export binds table values/times/memory to saved SimulationOutput; SLX archive graph review binds the six-state chart and iterator. '
    report+='Synthetic corruption checks are separate from actual numeric checks.\n\n'
    report+=f"Derived candidate only: assuming minimum ON/OFF .25 h and OFF TES delivery 3 MW, restart energy {d['proposed_restart_MWh']:.9f} MWh "
    report+=f"gives ON {d['on_duration_h']:.9f} h and OFF .25 h. RK4 independently checks both endpoints. "
    report+='See `TES_capacity_fallback_derivation_v33.md` for feasibility bounds, timing units and multi-event requirements. '
    report+='No new SLX or physical compressor policy is claimed.\n\n'
    report+='Observed failed attempts preserved: sandbox MATLAB startup failed before model execution; local authorized retry passed. '
    report+='First reviewer used the obsolete nonhierarchical chart-name check; it was replaced with the accepted v32 completion reviewer. '
    report+='Second reviewer reached packaging but rejected relative-path handling; absolute paths were fixed. '
    report+='Both logs and original snapshots remain. Exact successful reviewer has its own timestamped QA source snapshot.\n\n'
    report+=f"Evidence: `{folder.relative_to(ROOT)}`, `{qa_path.relative_to(ROOT)}`, `{qa['receipt']}`, `{source_path.relative_to(ROOT)}`.\n\n"
    report+='Research candidates were discovered through search, but MDPI returned 429 and Elsevier redirected to an inaccessible page. '
    report+='No new article equation, dwell value or signoff adopted. Primary engineering documentation is distinguished from article evidence.\n\n'
    report+='Remaining limitations:\n\n'+''.join('- '+v+'\n' for v in limitations)+'\nNext: '+nxt+'\n'
    for path in [ROOT/'STATUS_stateflow_v33.json',ROOT/'MASTER_STAGEBOARD_stateflow_v33.md',ROOT/'audit/TES_capacity_fallback_results_v33.md']:
        assert not path.exists(),f'Preserve existing {path}'
    save(ROOT/'STATUS_stateflow_v33.json',status)
    (ROOT/'audit/TES_capacity_fallback_results_v33.md').write_text(report,encoding='utf-8')
    board=f"# v33: saved-v32 fallback audit\n\n{now}. Experiment PASS; production controller defect CONFIRMED OPEN. Model remains v32; no new SLX.\n\n"
    board+=f"25 scenarios / 310 intervals / 620 slots; 16200 MATLAB assertions; 643 equation checks; independent QA `{qa['categories']}`, zero failures.\n\n"
    board+='Capacity tail can leave usable TES idle while demand is unmet. Low-load hold cutoff produces macro-step-sensitive service and HP availability pulses. '
    board+='Source shortage at initial capacity is distinct; feasible hold/passive/source-limited controls are invariant across the tested constant-input partitions.\n\n'
    board+=f"Evidence: `audit/TES_capacity_fallback_results_v33.md`, `audit/TES_capacity_fallback_derivation_v33.md`, `{folder.relative_to(ROOT)}`, `{qa_path.relative_to(ROOT)}`.\n\n"
    board+='No calibrated/physical validation, article replication, new fault acceptance or standalone code generation. Full primary signoffs 0/31.\n\nNext: '+nxt+'\n'
    (ROOT/'MASTER_STAGEBOARD_stateflow_v33.md').write_text(board,encoding='utf-8')
    progress=f"\n\n## {now} — v33 executed saved-v32 capacity-fallback defect audit\n\n"
    progress+='Read current Stateflow/research status/stageboards, acceptance/frontier/progress and relevant production/independent sources before edits. '
    progress+='Created a targeted saved-model harness and independent fixtures; derived a second logarithmic pulse recurrence, source-feasibility theorem '
    progress+='and explicit hysteresis/dwell constraints. Reopened primary EnergyPlus/MathWorks documentation; searched primary research candidates '
    progress+='but full-text retrieval failed (429/inaccessible redirect). No new paper equations/values/signoffs adopted.\n\n'
    progress+=f"Pass/fail: MATLAB retry exit 0; 16200/16200 assertions, 25 scenarios/310 intervals/620 slots; equations 643/643; QA {qa['categories']}, zero failures; "
    progress+=f"max residual {s['max_abs_balance_residual_MWh']:.8g} MWh; {qa['previous_entries_preserved']} earlier unique immutable entries preserved. "
    progress+='Sandbox startup failed before simulations. Two reviewer failures (obsolete chart-path checker, relative report paths) repaired and freshly rerun; '
    progress+='logs/snapshots retained. Saved v32 model, builder and production planner unchanged.\n\n'
    progress+='Finding: a capacity tail with unavailable low-load HP disables TES service despite usable heat. Low-load fixture unmet falls '
    progress+='7.384494 to 6.291047 MWh as h falls 2 to .125 h while reconstructed availability changes rise 3 to 63; no zero-unmet convergence '
    progress+='or physical compressor-cycle claim. Exact-capacity initialization instead discharges and produces nonmonotonic sensitivity. '
    progress+='Source-limited/passive/feasible-hold controls and alternate recurrence/RK4 agree independently.\n\n'
    progress+='Files: new audit/stateflow_fallback_v33.py, verify_stateflow_fallback_v33.py, finalize_stateflow_fallback_v33.py, '
    progress+='run_stateflow_fallback_v33.ps1; matlab/simulink/run_stateflow_fallback_v33.m and export_stateflow_fallback_mat_v33.m; '
    progress+='derivation/results/source-discovery reports, independent specs/QA and timestamped logs/receipts; '
    progress+=f"`{folder.relative_to(ROOT)}`, STATUS_stateflow_v33.json, MASTER_STAGEBOARD_stateflow_v33.md and manifest. Mutable progress/acceptance appended.\n\n"
    progress+='Remaining limitations: open production service defect; no new SLX/policy acceptance. Candidate dwell times are engineering assumptions; '
    progress+='physical-hour timers and seconds-based temporal logic are unresolved for future deployment. Two-slot iterator cannot represent arbitrary '
    progress+='cycles. Constant one-node plant/HP screening, normal host planner; no calibrated, hydraulic, stratified, equipment-fault, standalone-codegen '
    progress+='or paper-replication claims. Independent QA is algorithm/artifact review, not separate human/agent review. Full primary signoffs 0/31.\n\n'
    progress+='Next actionable task: '+nxt+'\n\nRun stops at this coherent documented defect/derivation handoff. '
    progress+='No Jarvice/unrelated files, user settings, scheduler, agent runner, secrets or external publication changed.\n'
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:f.write(progress)
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
        f.write(f'\n\n## Capacity-fallback defect audit — {now} / checkpoint v33\n\n'
            'Saved v32 executed afresh: 25 scenarios/310 intervals/620 slots; 16200 MATLAB assertions and 643 equation checks pass with independent QA. '
            'No new SLX; v32 implementation acceptance remains. Capacity-tail TES-service defect is CONFIRMED OPEN, with timestep sensitivity '
            'and a derived candidate restart/dwell handoff. This checkpoint reproduces a defect; it does not accept a corrected controller. '
            'See STATUS_stateflow_v33.json and audit/TES_capacity_fallback_results_v33.md. Physical validation/article replication remain untested.\n')
    # Include completed logs, failed attempts and snapshots; omit generated caches
    # and the active finalizer console, which closes after this script returns.
    files=set(p for p in folder.rglob('*') if p.is_file() and not any(v in ('cache','codegen') for v in p.relative_to(folder).parts))
    for p in (ROOT/'audit').glob('*v33*'):
        if p.is_file():files.add(p)
        elif p.is_dir():files.update(q for q in p.rglob('*') if q.is_file())
    files.update((ROOT/'matlab/simulink').glob('*v33.m'))
    files.update(p for p in (ROOT/'automation/logs').glob('*v33*') if 'finalize' not in p.name)
    files.update([ROOT/'STATUS_stateflow_v33.json',ROOT/'MASTER_STAGEBOARD_stateflow_v33.md'])
    manifest=ROOT/'audit'/f'Stateflow_fallback_manifest_v33_{tag}.json'
    save(manifest,dict(version='0.33',timestamp_utc=now,previous_entries_preserved=qa['previous_entries_preserved'],
        mutable_exclusions=['automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md','active finalizer console','generated caches'],
        files=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)]))
    print(json.dumps(dict(status='STATUS_stateflow_v33.json',manifest=str(manifest.relative_to(ROOT)),
        immutable_entries=len(files),controller_defect='CONFIRMED_OPEN',experiment='PASS')))
    return 0

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('qa',type=Path);a=p.parse_args()
    raise SystemExit(main(a.folder,a.qa))
