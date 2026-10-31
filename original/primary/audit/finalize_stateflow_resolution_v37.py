"""Seal saved-v36 defect evidence and a concrete additive-v38 handoff."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    assert not p.exists(),f'Preserve existing {p}'
    p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def rel(p):return str(p.relative_to(ROOT))
def main():
    folder=ROOT/Path(sys.argv[1]);qa_path=ROOT/Path(sys.argv[2]);qa=read(qa_path)
    assert not sum(v['failed'] for v in qa['counts'].values())
    summary=read(folder/'summary_v37.json');assert summary['harness_failed']==0
    rpaths=[ROOT/Path(x) for x in sys.argv[3:]];receipts=[read(p) for p in rpaths]
    assert len(receipts)==3 and all(r['exit_code']==0 for r in receipts)
    metadata=read(folder/'numeric_metadata_v37.json');assert metadata['stateflow_license_test']==1
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v36.slx'
    assert sha(model)==read(ROOT/'STATUS_stateflow_v36.json')['model_sha256']==qa['model_sha256']
    executions=read(folder/'execution_v37.json')
    intervals=sum(len(x['clock_end']) if x['clock_end'] and isinstance(x['clock_end'][0],list) else int(bool(x['clock_end'])) for x in executions)
    ts=datetime.now(timezone.utc);stamp=ts.strftime('%Y%m%dT%H%M%S_%fZ')
    passed=sum(v['passed'] for v in qa['counts'].values())
    handoff=('Implement additive saved Stateflow v38: reject unresolved capacity/restart/cutoff bands before planning; '
             'replace overflow-prone HP slope arithmetic with a finite normalized-load component; '
             'implement compensated persistent physical-hour clocks with declared cumulative accuracy and reset/guard semantics. '
             'Execute six modes, v36 changing-input references, preserved v37 stress/counterexamples, clock partitions, '
             'cutoff overlap and source/request-limited HP cases; independently export MAT and compare exact-input Decimal '
             'clocks and normalized/analytic HP laws. Preserve every prior model/evidence; do not claim physical calibration.')
    limits=[
        'Defect reproduction only; no new SLX or corrected-controller acceptance. Prior v36 fixture acceptance remains preserved.',
        'Clock bias is a cumulative-accuracy gap; v36 local tolerance checks pass. No observed early clean dwell transition is claimed.',
        'Aged-clock, near-ulp bands and subnormal HP powers are numerical stress fixtures, not plausible equipment specifications.',
        'HP component returns Inf but actual saved-model runtime COP gate rejects it; no invalid successful plant output is claimed.',
        'Stateflow license test is true and saved charts execute; ver(Stateflow) returned empty and the full installed-product list lacks a Stateflow entry. No standalone product version is fabricated.',
        'Independent QA is algorithm/artifact QA in the same agent, not a separate human/agent or physical validation.',
        'Normal-mode host planning and macro-time analytic segments remain; standalone code generation, solver-clock events, calibrated hydraulics/stratification/startup losses and article replication remain untested.'
    ]
    status=dict(version='0.37',inherits='STATUS_stateflow_v36.json',research_inherits='STATUS_v25.json',timestamp_utc=ts.isoformat(),
        checkpoint='Fresh saved-Stateflow numerical-domain defect audit',stateflow_acceptance='PASS_DEFECT_REPRODUCTION_ONLY',model_version='0.36',new_model=False,
        generated_model=rel(model),model_sha256=sha(model),controller_defect='OPEN: cumulative clock accuracy, unresolved bands, HP slope overflow',
        result_directory=rel(folder),independent_qa=rel(qa_path),matlab_batch_receipts=[rel(p) for p in rpaths],
        matlab_batch_exit_code=0,scenarios=summary['scenarios'],completed_scenarios=summary['completed'],completed_intervals=intervals,
        runtime_rejections=summary['rejected'],component_probes=4,harness_checks_passed=summary['harness_passed'],harness_checks_failed=0,
        independent_checks_passed=passed,independent_checks_failed=0,independent_check_breakdown=qa['counts'],
        equation_checks_passed=qa['counts']['equation']['passed'],previous_immutable_entries_preserved=qa['previous_immutable_entries'],
        full_primary_signoffs=0,total_sources=31,primary_article_replication=False,independent_physical_validation='NOT_TESTED',limitations=limits,next=handoff)
    results=f'''# v37 executed saved-v36 numerical-domain defect audit

UTC {ts.isoformat()}. Defect reproduction PASS; controller repair OPEN.

Actual saved v36 executed in {summary['scenarios']} scenarios: {summary['completed']} completed,
{summary['rejected']} rejected at runtime, {intervals} completed intervals. Four host HP component
probes also executed. MATLAB harness 3/3 PASS; separate MAT export and
numeric-metadata batches exit 0. Independent QA {passed}/{passed} PASS,
including {qa['counts']['equation']['passed']} equation checks and
{qa['previous_immutable_entries']} preserved immutable entries. PASS counts describe
the audit and defect reproduction, not a corrected controller.

Six baseline modes/cases still match the independent v34/v30 numerical
reference. Saved SimulationOutput MATs, fresh numeric JSON traces, error
phase/time/messages, matched sources, exact inputs and timestamped logs
are in `{rel(folder)}`. No production model/source is changed.

| Initial OFF age (h) | Partitions of 1.024e-7 h | Final clock bias (h) |
|---:|---:|---:|
| 1e6 | 1 | 4.548320770263299e-11 |
| 1e6 | 16 | 4.548320770263299e-11 |
| 1e6 | 128 | 1.908128356933590e-9 |
| 1e6 | 1024 | 1.6809289550781246e-8 |

The last value is about 60.51 microseconds, exceeding the 36 microsecond
comparison budget while local clock assertions pass. Changing demand halfway
through 1024 intervals gives the same bias. Initial-age-zero controls remain
within the comparison budget. A nonadvancing 1e-12 h interval at age 1e6 h
rejects with the existing resolution diagnostic. No early dwell transition
is observed in these OFF/source-unavailable stress fixtures.

At capacity 10 MWh, OFF age .25 h, zero demand/loss and available HP,
restart gaps 1/32/64 energy ulps pass strict configuration ordering but fail
with Nonpositive event progress during execution. Gaps 65/128/256 ulps keep
the HP OFF and energy constant. The exact policy has no capacity crossing
in any of these cases. A supported-band domain is missing.

At HP capacity/output 1e-309 MW, the preserved host component reports
available=true and COP=Inf with electricity zero. Separate saved-MAT flags
distinguish Inf from NaN; its intermediate slope is also Inf. The normalized
full-load reference gives COP=4. The actual saved Stateflow COP gate rejects
this response. 8, 1e-300 and 1e-308 MW component controls have finite COP=4;
the 1e-300 MW saved-model control completes.

Evidence: `{rel(qa_path)}`; `audit/TES_resolution_derivation_v37.md`;
`STATUS_stateflow_v37.json`; `MASTER_STAGEBOARD_stateflow_v37.md`.
The derivation identifies verified primary MathWorks software text separately
from engineering equations/assumed fixture values. No new primary article
equation, calibrated value or paper signoff was adopted; full signoffs stay 0/31.

Local MATLAB is R2026a Update 5. The Stateflow license test returns true;
the saved six thermal states and two HP supervisor states are inspected and
executed. The `ver('Stateflow')` lookup/full-product inventory did not expose
a standalone Stateflow version entry, so none is claimed.

Sandbox startup failed before simulation; its receipt/log is retained. The
local execution, MAT export, numeric metadata and both independent QA
revisions pass. Original reviewer snapshot/first QA remain; the final reviewer
revision has its own timestamped source snapshot. Known Stateflow argument
shadow warnings remain visible. No settings/runner/scheduler changes.

Limitations: {' '.join(limits)}

Next actionable task: {handoff}
'''
    result_path=ROOT/'audit/TES_resolution_results_v37.md';assert not result_path.exists();result_path.write_text(results,encoding='utf-8')
    write(ROOT/'STATUS_stateflow_v37.json',status)
    stage=ROOT/'MASTER_STAGEBOARD_stateflow_v37.md';assert not stage.exists()
    stage.write_text(f'# v37 saved-Stateflow numerical-domain defect checkpoint\n\nUTC {ts.isoformat()}. Defect reproduction PASS; repair OPEN.\n\nSaved v36: 24 scenarios, 19 complete, 5 runtime rejections, {intervals} completed intervals; four HP component probes. Six baseline modes pass. MATLAB harness 3/3; independent QA {passed}/{passed}; {qa["counts"]["equation"]["passed"]} equation checks; prior immutable entries {qa["previous_immutable_entries"]} preserved. No new SLX.\n\nClock cumulative bias 1.6809289550781246e-8 h; bands <=64 energy ulps fail progress; subnormal host HP slope yields Inf COP, rejected by runtime gate. These are numerical stress defects; no early clean dwell or physical validation claim.\n\nEvidence: STATUS_stateflow_v37.json; audit/TES_resolution_results_v37.md; audit/TES_resolution_derivation_v37.md.\n\nNext: {handoff}\n',encoding='utf-8')
    progress=f'''\n\n## {ts.isoformat()} — v37 fresh saved-v36 numerical-domain defect audit

Read current Stateflow/research STATUS/stageboards, acceptance/frontier/progress and production/independent code before changes. Implemented versioned targeted harness and exact-input Decimal/normalized-HP reviewer, executed the preserved actual v36 model, separately re-exported MATs and observed Inf/NaN/product/chart metadata. Derived cumulative roundoff, band separation and normalized-load repair handoff. Verified full primary MathWorks software documentation; no primary article equation/value/signoff adopted.

Pass/fail: sandbox MATLAB startup FAIL before simulation (receipt retained); local simulation/MAT/numeric-metadata exits 0; harness 3/3 PASS; 24 scenarios, 19 completed/5 runtime rejections, {intervals} completed intervals, four component probes; independent QA {passed}/{passed} PASS including {qa['counts']['equation']['passed']} equation checks and {qa['previous_immutable_entries']} preservation checks. Six baseline modes agree with independent reference. Both reviewer revisions pass; original sources/first QA retained and final source snapshot separately bound.

Finding: OPEN cumulative clock-accuracy gap (bias 1.6809289550781246e-8 h after1024 updates of1e-10 h at initial age1e6 h, held/changing demand); strict-order-valid restart bands <=64 ulps fail zero-event progress; tiny positive HP cap1e-309 MW produces host Inf COP/zero electricity. Actual saved-model COP gate rejects the latter. No early clean dwell transition is claimed. No production controller/model changes, corrected acceptance or physical claims.

Files created: audit/stateflow_resolution_v37.py, verify_stateflow_resolution_v37.py, finalize_stateflow_resolution_v37.py, run_stateflow_v37.ps1, TES_resolution_derivation/results_v37.md; matlab/simulink/run_stateflow_resolution_v37.m, export_stateflow_resolution_v37.m, export_stateflow_numeric_metadata_v37.m; new spec, results/MAT/JSON/source/QA snapshots, status/stageboard, manifest and timestamped logs/receipts. Existing mutable progress and acceptance append only. Result: `{rel(folder)}`; QA: `{rel(qa_path)}`.

Remaining limitations: {' '.join(limits)}

Next actionable task: {handoff}

Run stops at coherent documented defects and additive-v38 handoff. No Jarvice/unrelated files, user settings, scheduler, agent runner, secrets or external publication touched.
'''
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:f.write(progress)
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
        f.write(f'\n\n## Saved-v36 numerical-domain defect checkpoint — {ts.isoformat()} / v37\n\nSaved v36 freshly executed:24 scenarios/3382 completed intervals; six baseline modes and {passed} independent QA checks pass. Cumulative clock accuracy, unresolved restart bands and host HP coefficient overflow remain OPEN; five actual runtime rejections and four component probes are retained. No corrected SLX or physical validation is accepted. Prior v36 acceptance is preserved within its tested scope. STATUS/stageboard v37 and audit/TES_resolution_results_v37.md provide the additive-v38 handoff.\n')
    completion=ROOT/'audit'/f'Stateflow_completion_QA_v37_{stamp}.json'
    bindings=[model,qa_path,*rpaths,ROOT/'STATUS_stateflow_v37.json',stage,result_path,ROOT/'audit/TES_resolution_derivation_v37.md']
    write(completion,dict(timestamp_utc=ts.isoformat(),checkpoint='defect reproduction only',failed=0,bindings=[dict(path=rel(p),sha256=sha(p),bytes=p.stat().st_size) for p in bindings]))
    files=[p for p in folder.rglob('*') if p.is_file()]
    files += list((ROOT/'audit').glob('*v37*'))
    files += list((ROOT/'matlab/simulink').glob('*v37.m'))
    files += list((ROOT/'automation/logs').glob('*v37*'))
    # Original timestamped spec directory is located by bound cases SHA.
    for p in (ROOT/'audit').glob('stateflow_spec_v37_*'):
        if p.is_dir():files += [x for x in p.rglob('*') if x.is_file()]
    files += [ROOT/'STATUS_stateflow_v37.json',stage]
    # An actively written finalizer console log is excluded; it is post-close evidence.
    unique={rel(p):p for p in files if p.is_file() and 'finalize_console' not in p.name}
    manifest=ROOT/'audit'/f'Stateflow_manifest_v37_{stamp}.json'
    write(manifest,dict(timestamp_utc=ts.isoformat(),files=[dict(path=name,sha256=sha(p),bytes=p.stat().st_size) for name,p in sorted(unique.items())],
                        mutable_ledgers_excluded=['automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md']))
    print('STATUS=STATUS_stateflow_v37.json');print('MANIFEST='+rel(manifest));print('QA_PASSED='+str(passed));print('NEXT='+handoff)

if __name__=='__main__':main()
