"""Close v28 only from executed MATLAB, independent QA and preserved baselines."""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def rel(path): return path.resolve().relative_to(ROOT).as_posix()
def write(path,value):
    with path.open('x',encoding='utf-8') as out:
        json.dump(value,out,indent=2,allow_nan=False); out.write('\n')
def csvrows(path):
    with path.open(newline='',encoding='utf-8-sig') as out: return list(csv.DictReader(out))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--result-dir',type=Path,required=True)
    p.add_argument('--qa',type=Path,required=True)
    p.add_argument('--receipt',type=Path,required=True)
    a=p.parse_args(); directory=a.result_dir.resolve()
    assert directory.is_relative_to(ROOT/'results')
    summary_path=directory/'acceptance_summary_v28.json'
    summary,qa,receipt=map(read,[summary_path,a.qa,a.receipt])
    assert Path(summary['output_directory']).resolve()==directory
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v28.slx'
    baseline=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v24.slx'
    prior=read(ROOT/'STATUS_stateflow_v27.json')
    assert sha(baseline)==prior['model_sha256']
    assert summary['version']=='0.28' and summary['failed']==0 and summary['passed']==summary['checks']
    assert summary['stateflow_executed'] and summary['simulink_executed']
    assert summary['modes_observed']==list(range(6))
    assert qa['failed']==0 and qa['trace_qa']['failed']==0 and qa['structure']['failed']==0
    assert qa['experiments_qa']['failed']==0 and qa['runtime_rejections']['failed']==0
    assert qa['acceptance_integrity']['failed']==0
    assert qa['self_test']['failed']==qa['generic_rejection_schema_self_test']['failed']==0
    assert qa['self_test']['synthetic_only'] and qa['generic_rejection_schema_self_test']['synthetic_only']
    assert qa['model_sha256']==sha(model) and qa['verifier_sha256']==sha(ROOT/'audit/verify_stateflow_trace_v28.py')
    assert qa['trace_sha256']==sha(directory/'stateflow_trace_v28.csv')
    assert qa['experiments_sha256']==sha(directory/'storage_timestep_experiments_v28.csv')
    assert qa['rejections_sha256']==sha(directory/'runtime_rejections_v28.json')
    assert qa['vectors_sha256']==sha(ROOT/'audit/stateflow_qa_vectors_v28.csv')
    assert qa['acceptance_summary_sha256']==sha(summary_path)
    assert qa['domain_spec_sha256']==sha(ROOT/'audit/stateflow_domain_cases_v28.json')
    assert qa['supplemental_input_metadata_sha256']==sha(ROOT/'audit/dispatch_reference_vectors_v18.csv')
    assert qa['reused_generic_rejection_verifier_sha256']==sha(ROOT/'audit/verify_stateflow_runtime_v24.py')
    for filename,expected_hash in qa['experiments_qa']['actual_trace_sha256'].items():
        assert sha(directory/filename)==expected_hash,filename
    evidence_aliases={'preserved_model_v24':baseline,'new_model_v28':model}
    for filename,expected_hash in qa['acceptance_integrity']['evidence_sha256'].items():
        assert sha(evidence_aliases.get(filename,directory/filename))==expected_hash,filename
    for filename,expected_hash in qa['reviewed_source_sha256'].items():
        assert sha(ROOT/'matlab/simulink'/filename)==expected_hash,filename
    assert receipt['matlab_batch_exit_code']==0
    assert receipt['result_directory']==rel(directory)
    assert receipt['model_sha256_before']==receipt['model_sha256_after']==sha(model)
    assert receipt['baseline_sha256_before']==receipt['baseline_sha256_after']==sha(baseline)
    assert sha(ROOT/receipt['log_file'])==receipt['log_sha256']
    assert sha(ROOT/receipt['console_file'])==receipt['console_sha256']
    assert f'ACCEPTANCE_OUTPUT={directory}' in (ROOT/receipt['log_file']).read_text(encoding='utf-8-sig',errors='replace')
    assertions=csvrows(directory/'stateflow_assertions_v28.csv')
    assert len(assertions)==summary['checks'] and all(r['passed'] in ['1','true'] for r in assertions)
    exassert=csvrows(directory/'storage_experiment_assertions_v28.csv')
    assert len(exassert)==summary['loss_experiments']['checks'] and all(r['passed'] in ['1','true'] for r in exassert)
    assert summary['runtime_invalid_cases_rejected']==summary['runtime_invalid_cases']==46
    assert summary['loss_experiments']['failed']==0
    # Snapshots tie final source to the actual run, independently of embedded-source QA.
    for snapshot in (directory/'source_snapshot').iterdir():
        if snapshot.suffix=='.m':
            matches=list((ROOT/'matlab').rglob(snapshot.name)); assert len(matches)==1
            assert sha(snapshot)==sha(matches[0]), snapshot.name
        else:
            assert sha(snapshot)==sha(ROOT/'audit'/snapshot.name),snapshot.name
    oldmanifest=read(ROOT/'audit/Stateflow_temporal_manifest_v27_20261009T082057_601462Z.json')
    oldfiles=oldmanifest['files']
    preserved=[]
    for row in oldfiles:
        path=ROOT/row['path']
        assert sha(path)==row['sha256'],row['path']
        preserved.append(row['path'])
    derivations=sorted((ROOT/'audit').glob('TES_derivation_checks_v28_*.json'))
    assert derivations and read(derivations[-1])['failed']==0
    now=datetime.now(timezone.utc); stamp=now.strftime('%Y%m%dT%H%M%S_%fZ')
    sections={k:v for k,v in qa.items() if isinstance(v,dict) and 'passed' in v}
    qa_count=sum(v['passed'] for v in sections.values())
    # Both numerical-oracle and generic rejection-schema self-tests are synthetic.
    # Use the evidence flag so future self-test sections cannot inflate model QA.
    actual_count=sum(v['passed'] for v in sections.values() if not v.get('synthetic_only',False))
    with ZipFile(model) as archive:
        model_xml=ET.fromstring(archive.read('simulink/blockdiagram.xml'))
    model_formats=[entry.text for entry in model_xml.iter('P') if entry.get('Name')=='ModelVersionFormat']
    assert len(model_formats)==1
    limits=[
        'Exponential retention is exact only for passive constant-coefficient zero-equilibrium/ambient-referenced energy.',
        'Active ports retain loss-first splitting; fresh charge loses no standing heat in its current interval. First-order timestep error is measured.',
        'Usable energy above a delivery temperature cutoff requires an ambient offset and cutoff events; current scalar model has no temperature state.',
        'New continuous_loss_rate_per_h is a rate coefficient, not a measured hourly fractional loss. All sensitivity parameters are scenario assumptions.',
        'Cadau primary Eq (4) is partially verified; its implementation has at least two nodes. No article reproduction or equipment calibration.',
        'Normal-mode host MATLAB HP adapter; standalone code generation, equipment faults, hysteresis/dwell, sensors and hydraulic/network/fuel/auxiliary models remain untested.',
        'Variable part-load v18 scenarios have reference/equivalent-baseline parity and independently checked laws; closed-form output predictions cover fixed-COP cases.',
        'v26 monitor-corruption and v27 delayed fault tests were executed on v24; they are not rerun evidence for v28.',
        'Nonfatal Stateflow allocator-output shadow warnings remain in v24/v28 execution logs.',
        'No measured-system physical validation; full primary signoffs remain 0/31.'
    ]
    next_task=('Derive and independently test a temperature/cutoff-aware TES model with the ambient-loss offset and exact constant-flow integration; '
               'specify saturation/cutoff events before a new Stateflow version. Preserve v24 and v28 baselines.')
    status=dict(version='0.28',inherits='STATUS_stateflow_v27.json',research_inherits='STATUS_v25.json',
        checkpoint='Executed versioned Stateflow exponential standing retention and timestep sensitivity',timestamp_utc=now.isoformat(),
        stateflow_acceptance='PASS',matlab_version=summary['matlab_version'],matlab_batch_exit_code=0,
        generated_model=rel(model),model_version='0.28',model_sha256=sha(model),preserved_v24_sha256=sha(baseline),
        model_version_semantics='Project release and filename/helper suffix; distinct from saved Simulink internal version format',
        project_model_release='0.28',saved_simulink_model_version_format=model_formats[0],
        model_modified_this_run=False,recovery_of_unfinished_v28=True,execution_receipt=rel(a.receipt),
        result_directory=rel(directory),independent_qa=rel(a.qa),matlab_checks_passed=summary['passed'],matlab_checks_failed=0,
        experiment_checks_passed=summary['loss_experiments']['passed'],experiment_cases=summary['loss_experiments']['cases'],
        runtime_domain_rejections=summary['runtime_invalid_cases_rejected'],scenarios=summary['scenarios'],intervals=summary['intervals'],
        max_abs_balance_residual_MWh=summary['max_abs_balance_residual_MWh'],
        temporal_acceptance_v28='NOT_TESTED',monitor_corruption_acceptance_v28='NOT_TESTED',
        independent_checks_passed=qa_count,independent_actual_checks_passed=actual_count,independent_checks_failed=0,
        independent_breakdown={k:dict(passed=v['passed'],failed=v['failed'],synthetic_only=v.get('synthetic_only',False)) for k,v in sections.items()},
        derivation_checks_passed=read(derivations[-1])['passed'],primary_text_verified_this_run=False,
        inherited_primary_text_review='audit/TES_standing_loss_primary_v28.md',primary_source_signoffs=0,
        total_sources=31,primary_paper_replication=False,independent_physical_validation='NOT_TESTED',standalone_codegen=False,
        limitations=limits,next=next_task)
    write(ROOT/'STATUS_stateflow_v28.json',status)
    experiments=csvrows(directory/'storage_timestep_experiments_v28.csv')
    table='|Case|Scheme|dt (h)|Terminal (MWh)|Continuous exact (MWh)|Absolute error (MWh)|\n|---|---|---:|---:|---:|---:|\n'
    for r in experiments:
        table+=f"|{r['scenario_id']}|{r['scheme']}|{r['dt_h']}|{float(r['terminal_MWh']):.9g}|{float(r['exact_continuous_MWh']):.9g}|{float(r['abs_error_MWh']):.9g}|\n"
    report=(f"# v28 executed Stateflow storage comparison\n\nUTC {now.isoformat()}. PASS: {summary['passed']}/{summary['checks']} MATLAB dispatch assertions, "
        f"{summary['loss_experiments']['passed']} experiment assertions, {summary['runtime_invalid_cases_rejected']} domain rejections and "
        f"{actual_count} independent evidence checks. {qa_count-actual_count} separate reviewer self-tests are not simulation evidence. "
        f"Executed {summary['scenarios']} scenarios/{summary['intervals']} intervals and all six modes; maximum system residual "
        f"{summary['max_abs_balance_residual_MWh']:.12g} MWh. Saved v24 is unchanged.\n\n"
        "The new production parameter is `storage.continuous_loss_rate_per_h` (h^-1). v28 replaces passive linear retention with exp(-lambda*dt), "
        "while preserving loss-first port allocation. Primary text review, independent RK4 derivation, units and the usable-energy offset defect are recorded in "
        "[TES_standing_loss_primary_v28.md](TES_standing_loss_primary_v28.md). The result is implementation acceptance of an explicit reduced assumption.\n\n"
        "Actual v24/v28 comparisons use the explicitly converted legacy fraction `(1-exp(-lambda*dt))/dt` for parity. A separate sensitivity compares both methods "
        "at the same numerical coefficient .04/h for a 24 h synthetic horizon. Passive exponential results agree with the exact semigroup. "
        "Active charging still overestimates simultaneous continuous energy; refinement reduces that error. These are not observed tank parameters.\n\n"+table+
        f"\nEvidence: `{rel(directory)}`, independent QA `{rel(a.qa)}`, batch log `{receipt['log_file']}`. "
        "Earlier v28 primary-text/derivation evidence and the saved model were inherited from unfinished work. "
        "The first earlier acceptance failed on the final rejection's mixed-cell JSON setup; its repaired rerun stopped without a summary and its interruption cause is unverified. "
        "This run preserved both attempts, retained a fresh sandbox startup failure, and completed a fresh automatically approved local MATLAB acceptance. "
        "Independent QA now requires every supplemental scenario interval and separates both synthetic self-test sections from actual evidence.\n\n"+
        '\n'.join('- '+x for x in limits)+f'\n\nNext: {next_task}\n')
    with (ROOT/'audit/TES_Stateflow_results_v28.md').open('x',encoding='utf-8') as out: out.write(report)
    stage=(f"# v28 Stateflow exponential standing-loss acceptance\n\nPASS: {summary['passed']}/{summary['checks']} MATLAB assertions, "
        f"{summary['loss_experiments']['passed']} experiment assertions, 46/46 actual domain rejections, {actual_count} independent evidence checks "
        f"and {qa_count-actual_count} separate reviewer self-tests. New saved model `matlab/simulink/DCHR_Dispatch_Stateflow_v28.slx` executed all six modes. "
        "v24 and previous evidence preserved.\n\nResults and caveats: `audit/TES_Stateflow_results_v28.md`. Primary equation/units/offset audit: "
        "`audit/TES_standing_loss_primary_v28.md`. Exact passive decay; active loss-first splitting remains approximate. "
        "No source replication, calibrated equipment or measured-system validation; signoffs 0/31.\n\n"
        f"Evidence: `{rel(directory)}`, `{rel(a.qa)}`, `{receipt['log_file']}`.\n\n"
        "Reproduce: `matlab -batch \"addpath('matlab','matlab/simulink'); run_stateflow_acceptance_v28;\"`. "
        "Builder refuses an existing versioned model. Run `audit/verify_stateflow_trace_v28.py --help` for independent trace/experiment/model/domain QA.\n\n"
        f"Next: {next_task}\n")
    with (ROOT/'MASTER_STAGEBOARD_stateflow_v28.md').open('x',encoding='utf-8') as out: out.write(stage)
    progress=(f"\n\n## {now.isoformat()} — v28 executed exponential TES Stateflow\n\nRead latest STATUS/stageboards, frontier, acceptance and relevant code. "
        "Resumed the unfinished v28 implementation and reviewed its saved model, component/reference/adapter/chart/gate/harness sources before execution. "
        "Inherited the existing Cadau primary Eq (4) review, reduced-equation derivation and recorded 14-check evidence; no new primary-text verification is claimed this run. "
        "Completed actual acceptance, strengthened independent supplemental-interval completeness and corrected synthetic QA classification. All saved models are unchanged.\n\n"
        f"Pass/fail: MATLAB batch exit 0; {summary['passed']}/{summary['checks']} dispatch assertions PASS; "
        f"{summary['loss_experiments']['passed']} experiment assertions PASS; 46/46 domain rejections; independent actual {actual_count} PASS, "
        f"self-tests {qa_count-actual_count} PASS; inherited derivation {status['derivation_checks_passed']} PASS. Fresh sandbox startup FAIL before simulation; authorized local execution PASS. "
        "Earlier first acceptance failed on heterogeneous JSON setup cell indexing; the already repaired earlier rerun stopped without a summary, cause unverified. "
        "All earlier evidence retained. All six modes and high-rate valid cases executed; timestep experiments expose active split bias despite exact passive cooling.\n\n"
        "Files changed: audit independent verifier and checkpoint finalizer; new independent review/report, "
        f"STATUS_stateflow_v28.json, MASTER_STAGEBOARD_stateflow_v28.md, `{rel(directory)}` numeric CSVs/SimulationOutput MATs/source snapshots, "
        "timestamped logs and manifest. Mutable progress/acceptance ledgers appended.\n\n"+
        'Remaining limitations: '+' '.join(limits)+f'\n\nNext actionable task: {next_task}\n\n'
        'Run stops at a coherent implementation/research/sensitivity checkpoint. Scheduler, agent runner, user settings, Jarvice and unrelated files were not changed; no external publication.\n')
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as out: out.write(progress)
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as out:
        out.write(f"\n\n## Exponential-retention version acceptance — {now.isoformat()} / v28\n\nActual new saved v28 model passes "
            f"{summary['passed']} MATLAB dispatch assertions, 46 actual domain rejections, {summary['loss_experiments']['passed']} experiment assertions "
            f"and {actual_count} independent evidence checks. Original v14 and accepted v24 preserved. Passive decay is exact only for the reduced constant-coefficient "
            "ambient-reference assumption; active port integration remains loss-first. Authoritative checkpoint: STATUS_stateflow_v28.json and "
            "MASTER_STAGEBOARD_stateflow_v28.md; detailed caveats audit/TES_Stateflow_results_v28.md. No article replication or physical validation.\n")
    files=set()
    for rootdir in [ROOT/'matlab',ROOT/'audit',ROOT/'automation/logs',ROOT/'sources/papers']:
        files.update(path for path in rootdir.rglob('*v28*') if path.is_file() and '__pycache__' not in path.parts)
    files.update(path for path in directory.rglob('*') if path.is_file() and not {'cache','codegen'}.intersection(path.relative_to(directory).parts))
    files.update([ROOT/'STATUS_stateflow_v28.json',ROOT/'MASTER_STAGEBOARD_stateflow_v28.md',a.qa.resolve(),a.receipt.resolve(),ROOT/receipt['log_file'],
        baseline,ROOT/'audit/dispatch_reference_vectors_v18.csv',ROOT/'audit/verify_stateflow_runtime_v24.py'])
    manifest=dict(version='0.28',timestamp_utc=now.isoformat(),prior_manifest_preserved_count=len(preserved),
        preserved_baseline_sha256=sha(baseline),mutable_exclusions=['automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md'],
        files=[dict(path=rel(path),sha256=sha(path),bytes=path.stat().st_size) for path in sorted(files)])
    manifestpath=ROOT/'audit'/f'Stateflow_manifest_v28_{stamp}.json'; write(manifestpath,manifest)
    check=[dict(path=row['path'],passed=sha(ROOT/row['path'])==row['sha256'] and (ROOT/row['path']).stat().st_size==row['bytes']) for row in manifest['files']]
    integrity=dict(timestamp_utc=now.isoformat(),manifest=rel(manifestpath),passed=sum(x['passed'] for x in check),failed=sum(not x['passed'] for x in check),prior_preserved=len(preserved),checks=check)
    integritypath=ROOT/'audit'/f'stateflow_integrity_v28_{stamp}.json'; write(integritypath,integrity)
    assert integrity['failed']==0
    logpath=ROOT/'automation/logs'/f'stateflow_integrity_v28_{stamp}.log'
    with logpath.open('x',encoding='utf-8') as out: out.write(json.dumps({k:v for k,v in integrity.items() if k!='checks'},indent=2)+'\n')
    print(json.dumps(dict(status='PASS',matlab=summary['passed'],independent_actual=actual_count,reviewer_selftests=qa_count-actual_count,
        manifest=rel(manifestpath),integrity=rel(integritypath),immutable_files=integrity['passed'],prior_preserved=len(preserved)),indent=2))

if __name__=='__main__': main()
