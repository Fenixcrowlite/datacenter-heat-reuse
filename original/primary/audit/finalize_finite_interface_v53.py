"""Close only a fully passing immutable component/interface checkpoint."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(path,value):
    assert not path.exists();path.write_text(json.dumps(value,indent=2)+'\n' if isinstance(value,(dict,list)) else value,encoding='utf-8')
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    qpath=sorted(folder.glob('independent_QA_v53_*.json'))[-1];q=json.loads(qpath.read_text())
    report=json.loads((folder/'report.json').read_text());reference=json.loads((folder/'reference_v53.json').read_text())
    assert q['actual_failed']==q['reviewer_selfchecks_failed']==report['summary']['failed']==reference['failed']==0
    assert q['report_sha256']==sha(folder/'report.json')
    assert q['intervals']==34 and q['required_modes']==list(range(6))
    assert any(v['kind']=='reference' and v['passed'] for v in q['checks'])
    assert any(v['kind']=='source_snapshot' and v['passed'] for v in q['checks'])
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v52.slx'
    inherited=json.loads((ROOT/'STATUS_v52.json').read_text());assert sha(model)==inherited['model_sha256']
    stamp=datetime.now(timezone.utc).isoformat();rel=folder.relative_to(ROOT).as_posix()
    next_task=('Derive a coupled tank-temperature/condenser interface with finite HX and variable-flow constraints before a new Stateflow model. '
        'Use explicit saturation versus water temperatures and prove admissible source/hot-flow/temperature/energy domains independently. '
        'Keep upstream62 equipment-map calibration OPEN until verified primary supplement and operating envelope are acquired. '
        'Preserve saved v52 and the v53 fixed-temperature controls; do not repeat unchanged annual matrices.')
    limitations=[
        'Synthetic steady fixed-saturation variable-flow boundary, not equipment calibration, article replication or measured physical validation; full primary signoffs0/31.',
        'Source20 local primary saturation definitions verified; upstream62 primary/supplement/coefficients inaccessible on attempted routes. Metadata/abstracts provide no equations.',
        'No new SLX/controller. Saved v52 remains0.52 and unchanged; actual focused new-interface simulations executed34 intervals, not an annual finite-interface acceptance.',
        'Water endpoint pinches and maximum heat-capacity rates are imposed feasibility constraints; UA, hydraulics, minimum/standby flow, capacity maps and pump laws are unvalidated.',
        'Fixed saturation axes/conversion across each scenario; a changing tank-linked condenser or factor requires a new interface, not silent generic annual reinterpretation.',
        'Auxiliary electricity is assumed proportional to compressor electricity and fully rejected for actual dispatch; thermal hot credit is explicitly rejected by adapter. No standby/auxiliary heat service claimed.',
        'Independent70-digit equations and original-MAT/binary handoff review by the same agent; not independent personnel or universal floating-point proof.',
        'Prior inherited bounded64-slot host planner, shadow warnings and normal-mode/standalone-code limits remain. Stateflow ver() is empty; license, charts and actual execution are directly observed.',
        'Initial new harness/reporting and reviewer errors are preserved. Corrected fresh execution and final QA pass; sandbox startup failure remains separately logged.'
    ]
    status=dict(version='0.53',timestamp_utc=stamp,inherits='STATUS_v52.json',result='ACCEPTED_SCOPED_FINITE_TEMPERATURE_BOUNDARY_AND_SAVED_V52_INTERFACE',
        model_version='0.52',new_model=False,saved_model=model.relative_to(ROOT).as_posix(),model_sha256=sha(model),
        model_executed_this_run=True,matlab_version=report['metadata']['matlab_version'],stateflow_license_observed=True,
        stateflow_version=report['metadata']['stateflow_version'],chart_count=report['metadata']['chart_count'],
        component_vectors=216,harness_passed=report['summary']['passed'],harness_failed=0,reference_passed=6,reference_failed=0,
        actual_domain_rejections=12,saved_model_intervals=q['intervals'],positive_segments=q['positive_segments'],latch_changes=q['latch_changes'],
        required_mode_coverage=q['required_modes'],independent_actual_passed=q['actual_passed'],independent_actual_failed=0,
        reviewer_selfchecks_passed=q['reviewer_selfchecks_passed'],reviewer_selfchecks_failed=0,
        max_independent_macro_residual_MWh=q['max_macro_residual_MWh'],result_directory=rel,independent_qa=qpath.relative_to(ROOT).as_posix(),
        full_primary_signoffs=0,total_sources=31,primary_article_replication=False,independent_physical_validation='NOT_TESTED',
        limitations=limitations,next_actionable_task=next_task)
    write(ROOT/'STATUS_v53.json',status)
    lines=['# v53 finite-temperature boundary and saved-v52 interface\n',
        f'UTC {stamp}. Scoped implementation PASS; saved model remains0.52, no new SLX.\n',
        f'MATLAB{report["summary"]["passed"]}/0; reference6/0;12 actual component/adapter domain rejections; '
        f'independent{q["actual_passed"]}/0 and separate reviewer mutations5/0. '
        f'Actual34 intervals/{q["positive_segments"]} positive segments/all six modes/{q["latch_changes"]} latch changes.\n',
        'Finite approaches reduce COP while source-limited condenser output increases because compressor work increases. '
        'The matched cases fix load6MW, evaporator budget4MW, all water temperatures, inventory and other assumptions; '
        'both evaporator and condenser approaches vary together. These are synthetic boundary sensitivities.\n',
        '| Symmetric approach K | Compressor COP | HP MW | Compressor MW | Boiler MW | Aux MWh over0.25h |\n|---|---:|---:|---:|---:|---:|\n']
    for c in report['cases'][6:9]:
        d=c['dispatch'];b=c['adapter']['boundary'];s=c['adapter']['boundary_spec']
        lines.append(f'| {s["evaporator_approach_K"]:g} | {b["cop_compressor"]:.6f} | {d[18]:.6f} | {d[19]:.6f} | {d[4]:.6f} | {c["aux_energy_MWh"]:.6f} |\n')
    lines+=['\nFinite hot-side fixture caps HP output2.56MW, uses boiler2MW and leaves unmet1.44MW; source capacity is not the binding limit. '
        'Auxiliary heat is entirely rejected; it receives no demand/storage credit.\n',
        '\nOriginal SimulationOutputs, numeric plans/segments/memory, report MATs/reopens, receipts, independent QA and source/preservation hashes retained. '
        'First attempt failed due new harness reshape/aux-column errors; corrected fresh run passes. '
        'Inherited controller is unchanged. Initial reviewer output-name shadow also repaired; original reviewer source/failed invocation retained.\n',
        '\nDerivation: audit/Finite_temperature_interface_derivation_v53.md. '
        f'Evidence: {rel}; independent QA: {qpath.relative_to(ROOT).as_posix()}.\n',
        '\nLimitations:\n\n']+['- '+v+'\n' for v in limitations]+['\nNext actionable task: '+next_task+'\n']
    content='\n'.join(lines);write(ROOT/'MASTER_STAGEBOARD_v53.md',content);write(ROOT/'audit/Finite_temperature_interface_results_v53.md',content)
    prefixes=[]
    append={ROOT/'automation/engineering_progress.md':
        f'\n\n## {stamp} — v53 finite-temperature boundary and saved-v52 interface\n\n'
        'Read STATUS/stageboardsv52, STATEFLOW_ACCEPTANCE, frontier, progress and actual builder/planner/HP/storage/adapter code before changes. '
        'Accepted actual v52 implementation already complete; followed explicit next interface derivation handoff. '
        'Visually reverified local source20 p8/p10; kept upstream62 equipment calibration OPEN with timestamped primary-access versus metadata distinctions.\n\n'
        'Implemented additive finite_temperature_boundary_v53 and adapt_finite_stateflow_v53 with refrigerant/water endpoints, finite approaches, variable-flow capacity rates, cooling-to-heating factor conversion, cutoff, external auxiliary energy and strict unsupported-hot-credit rejection. '
        f'Executed216 synthetic vectors,11 saved-v52 scenarios/34 intervals/{q["positive_segments"]} positive segments/all six modes/{q["latch_changes"]} latch changes. '
        f'MATLAB{report["summary"]["passed"]}PASS/0FAIL; six verified v30 physical comparisons6/0;12 domain rejections; '
        f'independent70-digit/original-MAT/padding/port/dwell/evidence QA{q["actual_passed"]}/0 plus five separate mutation checks.\n\n'
        'First new harness506/24 and independent6219/78 failed on multi-timestep reshape/auxiliary-column defects, not a saved controller defect. '
        'Original report/MAT/simulations/logs/source snapshots and one reviewer output-name shadow invocation retained. '
        'Corrected fresh harness includes original-MAT reopen/binding; sequence starts near capacity to exercise latch memory. '
        'Initial sandbox startup failure retained; authorized local batches execute. No prior source/model/data overwritten. '
        'No Jarvice/unrelated files, settings, schedules, agent runner, secrets or publication touched.\n\n'
        'Files created: matlab/+dchr/+components/finite_temperature_boundary_v53.m, matlab/+dchr/adapt_finite_stateflow_v53.m, '
        'matlab/run_finite_interface_v53.m, matlab/compare_finite_reference_v53.m, audit/prepare_finite_interface_v53.py, '
        'audit/run_finite_interface_v53.ps1, audit/verify_finite_interface_v53.py, audit/snapshot_finite_interface_v53.py, '
        'audit/finalize_finite_interface_v53.py, audit/Finite_temperature_interface_derivation_v53.md and results report; '
        'STATUS_v53/MASTER_STAGEBOARD_v53 and immutable fresh/failed evidence. Shared ledgers append only.\n\n'
        'Limitations: '+ ' '.join(limitations)+'\n\nNext actionable task: '+next_task+
        f'\n\nEvidence: {rel}; {qpath.relative_to(ROOT).as_posix()}. Stop coherent run after sealed packaging.\n',
        ROOT/'automation/STATEFLOW_ACCEPTANCE.md':
        f'\n\n## Finite-temperature interface checkpoint — {stamp} / v53\n\n'
        'No new SLX; accepted saved0.52 executes11 new-boundary cases/34 intervals/all six modes. '
        f'MATLAB{report["summary"]["passed"]}/0, reference6/0,12 component/adapter rejections, independent{q["actual_passed"]}/0 '
        'and reviewer5/0. Primary saturation definitions verified; fixed saturation/variable-flow assumptions, external rejected auxiliary heat '
        'and equipment-calibration/physical-validation limits explicit. STATUS_v53 and finite-interface derivation/results authoritative. '
        'No annual finite-interface or calibrated physical acceptance claimed.\n'}
    for p,text in append.items():
        original=p.read_bytes();prefixes.append(dict(path=p.relative_to(ROOT).as_posix(),size=len(original),sha256=hashlib.sha256(original).hexdigest()))
        with p.open('ab') as f:f.write(text.encode('utf-8'))
    write(folder/'ledger_prefixes.json',prefixes)
    stampfile=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    seal=[]
    files=[p for p in folder.rglob('*') if p.is_file() and 'local_build' not in p.parts]
    failed=ROOT/'results/finite_interface_v53_20261011T062518_022505Z'
    files += [p for p in failed.rglob('*') if p.is_file() and 'local_build' not in p.parts]
    files += [ROOT/'STATUS_v53.json',ROOT/'MASTER_STAGEBOARD_v53.md',ROOT/'audit/Finite_temperature_interface_results_v53.md']
    files += [ROOT/v['path'] for v in json.loads((folder/'source_hashes.json').read_text())]
    for p in files:seal.append(dict(path=p.relative_to(ROOT).as_posix(),size=p.stat().st_size,sha256=sha(p)))
    manifest=ROOT/'audit'/f'Finite_interface_manifest_v53_{stampfile}.json';write(manifest,seal)
    ok=all(sha(ROOT/v['path'])==v['sha256'] and (ROOT/v['path']).stat().st_size==v['size'] for v in seal)
    for v in prefixes:
        ok &= hashlib.sha256((ROOT/v['path']).read_bytes()[:v['size']]).hexdigest()==v['sha256']
    ok &= sha(model)==status['model_sha256']
    post=ROOT/'audit'/f'Finite_interface_postclose_v53_{stampfile}.json'
    write(post,dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),sealed_files=len(seal),
        ledger_prefixes_preserved=len(prefixes),model_preserved=True,passed=bool(ok),manifest=manifest.relative_to(ROOT).as_posix()))
    assert ok;print(f'CLOSED_V53 sealed={len(seal)} PASS model0.52 preserved; {post.relative_to(ROOT).as_posix()}')
if __name__=='__main__':main()
