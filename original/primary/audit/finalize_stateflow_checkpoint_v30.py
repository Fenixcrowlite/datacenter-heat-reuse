"""Close only executed, independently reviewed v30 evidence; no publication."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def relative(path):return path.resolve().relative_to(ROOT).as_posix()
def create(path,value):
    with path.open('x',encoding='utf-8') as f:f.write(value)
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('result_directory',type=Path);ap.add_argument('qa_report',type=Path)
    ap.add_argument('execution_log',type=Path);args=ap.parse_args()
    folder=args.result_directory.resolve();qa_path=args.qa_report.resolve();log=args.execution_log.resolve()
    for p in (folder,qa_path,log):relative(p) # enforce project-only paths
    summary=json.loads((folder/'acceptance_summary_v30.json').read_text());qa=json.loads(qa_path.read_text())
    assert summary['failed']==0 and summary['passed']==summary['checks']==1334
    assert summary['scenarios']==23 and summary['intervals']==69 and summary['modes_observed']==list(range(6))
    assert summary['faults']['failed']==0 and summary['faults']['rejected']==summary['faults']['cases']==18
    assert summary['actual_saved_model_executed'] is True
    assert qa['failed']==0 and Path(qa['result_directory']).as_posix()==relative(folder)
    required={'actual_numeric','static_saved_model','artifact_and_runtime_bindings','synthetic_reviewer_checks'}
    assert set(qa['sections'])==required
    for name,s in qa['sections'].items():
        assert s['evidence_class']==name and type(s['passed']) is int and s['passed']>0 and s['failed']==0
        assert len(s['checks'])==s['passed'] and all(c['passed'] is True for c in s['checks'])
    assert qa['verifier_sha256']==sha(ROOT/'audit/verify_stateflow_v30.py')
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v30.slx'
    assert qa['model_sha256']==sha(model)==sha(folder/'source_snapshot'/model.name)
    # Both markers in the selected completed batch prove acceptance + MAT export.
    text=log.read_text(encoding='utf-8',errors='replace')
    assert 'ACCEPTANCE_OUTPUT='+str(folder) in text and 'MAT_AUDIT_OUTPUT='+str(folder/'mat_audit_v30.json') in text
    assert 'MATLAB_EXIT=0' in log.with_suffix('.exit.log').read_text()
    previous=ROOT/'audit/Stateflow_fault_manifest_v29_20261009T204014_224631Z.json'
    prior=json.loads(previous.read_text())
    for entry in prior['files']:
        p=ROOT/entry['path'];assert p.stat().st_size==entry['bytes'] and sha(p)==entry['sha256'],entry['path']
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');utc=datetime.now(timezone.utc).isoformat()
    equation=json.loads((folder/'source_snapshot/spec/equation_qa.json').read_text())
    assert equation['failed']==0 and equation['passed']==364
    counts={n:s['passed'] for n,s in qa['sections'].items()}
    limits=[
        'Exact solution is restricted to constant ambient/heat capacity/loss coefficient and uniformly held power. No stratification, hydraulic tank connections or measured calibration.',
        'Endpoint throttling is a conservative interval controller. No full-power cutoff/capacity event pulses; constrained dispatch can change with timestep.',
        'Condenser must support tank maximum and delivery must not exceed cutoff; reservoir proxies neglect approach temperatures and detailed exergy.',
        'Normal-mode host MATLAB HP calls; standalone generated code, sensor/equipment faults, hysteresis, dwell and cycling remain untested.',
        'Fault coverage is 12 finite domain, 2 delayed finite and 4 output-corruption cases. No full v29 fault-matrix claim for v30; delayed NaN/Inf timing is untested.',
        'Stateflow helper-output/parameter shadow warnings are retained in logs. Implementation acceptance does not establish physical validation or article replication.',
        'Sample at StopTime represents a complete following interval; timestamps are sample starts, not continuous event integration.',
        'Full primary source signoffs remain 0/31. Cadau article evidence inherited; EnergyPlus engineering documentation newly re-opened, no article results or parameter values adopted.'
    ]
    next_task='Derive a full-power TES cutoff/capacity event controller and independently compare delivered heat against the uniform v30 policy at coarse/fine timesteps before adding another Stateflow version. Preserve v24/v28/v30.'
    status=dict(version='0.30',inherits='STATUS_stateflow_v29.json',research_inherits='STATUS_v25.json',
        timestamp_utc=utc,checkpoint='Executed temperature-aware exact constant-flow TES Stateflow v30',
        stateflow_acceptance='PASS',generated_model=relative(model),model_version='0.30',model_sha256=sha(model),
        result_directory=relative(folder),independent_qa=relative(qa_path),execution_log=relative(log),
        matlab_batch_exit_code=0,matlab_version=summary['matlab_version'],scenarios=23,intervals=69,
        matlab_checks_passed=1334,matlab_checks_failed=0,fault_rejections=18,equation_checks_passed=364,
        independent_check_breakdown=counts,independent_checks_failed=0,
        max_abs_balance_residual_MWh=summary['max_abs_balance_residual_MWh'],
        previous_manifest_preserved_count=len(prior['files']),standalone_codegen=False,
        primary_article_replication=False,independent_physical_validation='NOT_TESTED',full_primary_signoffs=0,
        total_sources=31,limitations=limits,next=next_task)
    status_path=ROOT/'STATUS_stateflow_v30.json';board=ROOT/'MASTER_STAGEBOARD_stateflow_v30.md'
    assert not status_path.exists() and not board.exists()
    create(status_path,json.dumps(status,indent=2)+'\n')
    board_text=(f'# v30: executed temperature-aware exact-flow Stateflow\n\n'
        f'PASS: 1334/1334 MATLAB assertions; 23 scenarios / 69 intervals / all six modes; 18/18 actual fault rejections. '
        f'Independent equation QA 364/364 PASS; evidence QA counts {counts}; zero failures.\n\n'
        f'Model: `{relative(model)}`. Physical state is ambient-referenced sensible energy, with explicit heat capacity, temperature and delivery cutoff. '
        f'Active held-power integration is exact under the stated constant-coefficient assumptions; endpoint powers are throttled before integration.\n\n'
        f'Evidence: `{relative(folder)}`, `{relative(qa_path)}`, `{relative(log)}`. '
        f'Derivation and primary-evidence boundary: `audit/TES_temperature_exact_flow_derivation_v30.md`. '
        f'Actual v28/v30 charging and discharging comparisons confirm the predicted split bias over h=2,1,0.5,0.25 hours.\n\n'
        f'Reproduce: `matlab -batch "addpath(\'matlab\',\'matlab/simulink\'); outputDir=run_stateflow_acceptance_v30(\'audit/stateflow_spec_v30_20261009T212412_569508Z\'); export_stateflow_mat_audit_v30(outputDir);"`, '
        f'then `python -X utf8 audit/verify_stateflow_v30.py <fresh-result-directory>`. Builder refuses to overwrite the saved release.\n\n'
        +'\n'.join('- '+item for item in limits)+f'\n\nNext: {next_task}\n')
    create(board,board_text)
    # Preserve every old attempt; new package lists immutable sources/evidence/logs.
    paths=set(p for p in folder.rglob('*') if p.is_file() and not {'cache','codegen'}.intersection(p.relative_to(folder).parts))
    paths.update(p for p in (ROOT/'matlab').rglob('*v30.m'))
    paths.update((model,status_path,board,qa_path,Path(__file__).resolve(),ROOT/'audit/verify_stateflow_v30.py',
                  ROOT/'audit/stateflow_reference_v30.py',ROOT/'audit/TES_temperature_exact_flow_derivation_v30.md',
                  ROOT/'audit/TES_Stateflow_results_v30.md'))
    paths.update(p for p in (ROOT/'automation/logs').glob('*v30*') if p.is_file() and 'checkpoint_close' not in p.name)
    paths.update(p for specfolder in (ROOT/'audit').glob('stateflow_spec_v30_*') for p in specfolder.rglob('*') if p.is_file())
    manifest=dict(version='0.30',timestamp_utc=utc,prior_manifest=relative(previous),prior_manifest_preserved_count=len(prior['files']),
        mutable_exclusions=['automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md','active closure console'],
        files=[dict(path=relative(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(paths)])
    manifest_path=ROOT/'audit'/f'Stateflow_manifest_v30_{stamp}.json';create(manifest_path,json.dumps(manifest,indent=2)+'\n')
    note=(f'\n\n## {utc} — v30 actual temperature/cutoff and exact active-flow Stateflow\n\n'
        f'Read current STATUS/stageboards v25/v29, acceptance, frontier, primary TES audit and unfinished v30 sources before editing. '
        f'Completed new versioned builder/model, temperature-aware exact TES, separate MATLAB reference, independent Decimal/analytic-HP oracle, actual acceptance/fault/comparison harness, read-only MAT audit, ZIP/XML evidence review and immutable closure. '
        f'Repaired missing adapter initial temperature, consistent zero-rate numerical limit and two test-fixture/assertion defects. Saved baseline models are preserved.\n\n'
        f'Pass/fail: MATLAB build exit 0; final acceptance/export exit 0; 1334/1334 assertions, 23 scenarios/69 intervals/all six modes; 18/18 runtime rejections; '
        f'364/364 independent equation checks. Independent evidence categories {counts}, zero failures; synthetic reviewer checks remain separate. '
        f'Maximum absolute interval residual {summary["max_abs_balance_residual_MWh"]:.6g} MWh. '
        f'Initial sandbox startup FAIL before simulation; authorized local execution PASS. First batch rejected invalid zero-capacity delivery fixture; '
        f'second full batch 1332/1334 exposed empty-vector orientation in one-interval memory assertions; corrected and freshly rerun. '
        f'Every previous attempt/log/snapshot retained. Read-only exporter was extended before its invocation; exact executed exporter has a separate source snapshot. '
        f'Nonfatal helper shadow warnings retained.\n\n'
        f'Files: new/updated additive matlab/*v30.m components/reference and matlab/simulink/*v30.m builder/adapter/chooser/allocator/gate/harness/exporter; '
        f'`{relative(model)}`; audit/stateflow_reference_v30.py, audit/verify_stateflow_v30.py, audit/finalize_stateflow_checkpoint_v30.py, '
        f'audit/TES_temperature_exact_flow_derivation_v30.md; independent specs/QA, `{relative(folder)}`, timestamped automation/logs; '
        f'STATUS_stateflow_v30.json, MASTER_STAGEBOARD_stateflow_v30.md, `{relative(manifest_path)}`. Mutable progress and acceptance ledgers appended.\n\n'
        +'Remaining limits: '+' '.join(limits)+f'\n\nNext actionable task: {next_task}\n\n'
        f'Run stops at this coherent implementation/QA gate. No scheduler, runner, user settings, Jarvice, unrelated files or external publication changed.\n')
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:f.write(note)
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
        f.write(f'\n\n## Temperature/cutoff exact-flow acceptance — {utc} / v30\n\nNew saved v30 model executes all six modes and passes 1334 MATLAB assertions, 18 actual runtime fault rejections, 364 independent equation checks and independent artifact/trace QA. Authoritative checkpoint: STATUS_stateflow_v30.json and MASTER_STAGEBOARD_stateflow_v30.md. Baselines preserved. Exact held-power integration and explicit temperature/cutoff bounds are implementation acceptance only; calibrated/hydraulic/event-driven physical validation remains open.\n')
    # Check immutable package immediately after mutable ledger edits.
    for e in manifest['files']:
        p=ROOT/e['path'];assert sha(p)==e['sha256'] and p.stat().st_size==e['bytes']
    print(json.dumps(dict(status=relative(status_path),manifest=relative(manifest_path),
                         immutable_files_verified=len(manifest['files']),prior_files_preserved=len(prior['files'])),indent=2))
    return 0
if __name__=='__main__':raise SystemExit(main())
