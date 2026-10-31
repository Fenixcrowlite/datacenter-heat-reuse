"""Seal one coherent v56 prerequisite/blocker checkpoint after actual gates pass."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, sys

ROOT = Path(__file__).resolve().parents[1]
NEXT = ('Implement a bounded-error charge propagator and compressor/source energy integrals for all ten charge regimes. '
        'Resolve the exact branch/limiter equality endpoint with an explicit one-sided protocol; nominal roots and log1p '
        'event times are diagnostics, not controller certificates. Then integrate an additive coupled Stateflow model '
        'with demand/cutoff/restart/dwell, strict padding/handoff, six modes, faults, verified-reference comparison and '
        'independent original-MAT binary/equation QA. Preserve saved v52 and v53-v56 evidence; do not repeat unchanged '
        'annual matrices. Primary equipment calibration remains OPEN.')

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def new_json(path, value):
    with path.open('x', encoding='utf-8') as f: f.write(json.dumps(value, indent=2) + '\n')
def new_text(path, value):
    with path.open('x', encoding='utf-8') as f: f.write(value)

def main():
    folder = (ROOT / sys.argv[1]).resolve(); assert folder.is_relative_to(ROOT / 'results')
    report = json.loads((folder / 'report.json').read_text())
    temporal = json.loads((folder / 'temporal_report.json').read_text())
    qa_path = max(folder.glob('independent_QA_v56_*.json')); qa = json.loads(qa_path.read_text())
    release_path = max(folder.glob('release_QA_v56_*.json')); release = json.loads(release_path.read_text())
    assert qa['summary']['failed'] == release['failed'] == report['summary']['failed'] == temporal['summary']['failed'] == 0
    assert all(x['passed'] for x in qa['reviewer_selfchecks'] + release['reviewer_selfchecks'])
    assert release['equation_QA'] == qa_path.relative_to(ROOT).as_posix()
    assert release['exact_endpoint_gap_fraction'] == '-5/3602879701896397'
    for name in ['STATUS_v56.json', 'MASTER_STAGEBOARD_v56.md', 'audit/Charge_regime_results_v56.md']:
        assert not (ROOT / name).exists(), f'Preserve existing checkpoint: {name}'
    for manifest in ['source_hashes.json', 'preservation.json']:
        for item in json.loads((folder / manifest).read_text()):
            assert sha(ROOT / item['path']) == item['sha256'], item['path']
            if manifest == 'source_hashes.json': assert sha(folder / 'source_snapshot' / item['path']) == item['sha256']
    for item in release['binary_hashes']: assert sha(folder / item['path']) == item['sha256']
    stamp = datetime.now(timezone.utc).isoformat(); short = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    model = ROOT / 'matlab/simulink/DCHR_Dispatch_Stateflow_v52.slx'
    assert sha(model) == '3d12602aeebcb80585ecfd16e13b0e9ea9cffe091348883b620923e468954e12'
    modes = sorted({int(x['dispatch'][0]) for x in report['runs']}); assert modes == list(range(6))
    accepted = sum(x['accepted'] for x in report['cases'])
    positive = sum(z[1] > 0 for x in report['runs'] for z in x['raw_segments']) + qa['temporal_counts']['positive_segments']
    passed = report['summary']['passed'] + temporal['summary']['passed']
    limitations = [
        'No new SLX or continuously coupled Stateflow acceptance. Actual saved v52 freshly executes six held-input fixtures and a seven-interval sequence; previously accepted v52 remains unchanged.',
        'v56 certifies a unique instantaneous minimum, but coefficients, candidate energies and event times are nominal binary64. Branch/limiter equality, propagated endpoint error and variable-power port integrals remain OPEN. Exact equality and unresolved minima reject.',
        'Actual nominal branch-endpoint replay rejects with DCHR:v55:UnresolvedBranch. The rounded kink energy 5 MWh differs from the exact binary-input kink; exact gap is -5/3602879701896397 K. This is a new-interface prerequisite blocker, not a defect in accepted v52 fixed-temperature scope.',
        'Charge-only event landscape has no direct-demand/discharge or HP dwell dynamics. Dwell checks and temporal traces in this checkpoint verify held-input saved v52, not a coupled v56 controller.',
        'Synthetic tank-return variable-flow topology, without calibrated UA, hydraulics, pumps/minimum-flow law or equipment map. No new literature/primary text retrieved; inherited full signoffs remain 0/31. No article replication or measured physical validation.',
        'Independent exact Fraction algebra, 80-digit Decimal equations, min-envelope RK4, original-MAT binary binding and separate reviewer mutations by the same agent; not independent personnel or a universal numerical-domain proof.',
        'Stateflow license, two charts and actual normal-mode execution observed; ver(Stateflow) empty, so no installed version claimed. Inherited host planner/64-slot/standalone deployment limits and shadow warnings remain.',
        'Pre-existing unfinished v56 files and earlier successful/failed evidence preserved. Their incomplete late-harness/reviewer snapshots are superseded by this fresh complete snapshot; prior results were not overwritten.',
    ]
    status = dict(version='0.56', timestamp_utc=stamp, inherits='STATUS_v55.json',
        result='TEN_CHARGE_REGIMES_VERIFIED_EXACT_EVENT_ENDPOINT_BLOCKER_OPEN', model_version='0.52',
        new_model=False, saved_model=model.relative_to(ROOT).as_posix(), model_sha256=sha(model),
        model_executed_this_run=True, coupled_stateflow_acceptance=False,
        matlab_version=report['metadata']['matlab_version'], stateflow_license_observed=bool(report['metadata']['stateflow_license_test']),
        stateflow_version=report['metadata']['stateflow_version'], chart_count=report['metadata']['chart_count'],
        matlab_passed=passed, matlab_failed=0, matlab_main_passed=report['summary']['passed'],
        matlab_temporal_passed=temporal['summary']['passed'], component_cases=len(report['cases']),
        component_accepted=accepted, component_domain_rejections=len(report['cases'])-accepted,
        charge_regime_coverage=qa['regime_coverage'], nominal_event_labels=qa['event_labels'],
        actual_intervals=13, actual_positive_segments=positive, required_mode_coverage=modes,
        actual_runtime_fault_rejections=1, reference_comparisons=6,
        temporal_macro_transitions=qa['temporal_counts']['macro_transitions'], dwell_latch_changes=release['dwell_latch_changes'],
        independent_equation_passed=qa['summary']['passed'], independent_release_passed=release['passed'], independent_failed=0,
        original_binary_records=release['binary_records'], original_binary_values=release['binary_values'], original_mats=release['original_mats'],
        reviewer_selfchecks_passed=len(qa['reviewer_selfchecks'])+len(release['reviewer_selfchecks']),
        exact_endpoint_gap_fraction=release['exact_endpoint_gap_fraction'], defect_status='COUPLED_EVENT_ENDPOINT_PROTOCOL_OPEN',
        full_primary_signoffs=0, total_sources=31, primary_article_replication=False, independent_physical_validation='NOT_TESTED',
        prior_six_mode_acceptance='STATUS_stateflow_v52.json', result_directory=folder.relative_to(ROOT).as_posix(),
        independent_qa=qa_path.relative_to(ROOT).as_posix(), release_qa=release_path.relative_to(ROOT).as_posix(),
        limitations=limitations, next_actionable_task=NEXT)
    new_json(ROOT / 'STATUS_v56.json', status)
    results = f'''# Charge regime and endpoint blocker checkpoint v56

UTC {stamp}. Saved model remains **0.52**; no new SLX or coupled model acceptance.
This run resumed pre-existing unfinished v56 code and executed it in fresh immutable evidence.

The five charge limits (request, nameplate, hot flow, source, TES port) are derived
on both FLOOR and TANK branches: all ten affine regimes pass independent exact-input
coefficient, event-completeness/time, reachability and min-envelope RK4 checks.
{len(report['cases'])} cases: {accepted} accepted interiors and {len(report['cases'])-accepted} expected domain/endpoint rejections.
Candidate event times are explicitly **nominal**, never production certificates.

MATLAB {passed} PASS / 0 FAIL ({report['summary']['passed']} main, {temporal['summary']['passed']} temporal).
Saved v52 actually executes 13 intervals / {positive} positive segments / all six required
modes. Six fixtures compare with verified MATLAB v30; one actual negative-source fault
rejects. The seven-interval sequence has {qa['temporal_counts']['macro_transitions']} macro mode transitions;
{release['dwell_latch_changes']} actual HP latch changes have separately checked reason/dwell authorization.
Flow/SOC/first-law, cutoff, exact state handoff and zero-duration identity pass.
This held-input acceptance does not establish continuously coupled behavior.

Independent equation/trace QA: {qa['summary']['passed']} PASS / 0 FAIL.
Separate provenance/binary/dwell gate: {release['passed']} PASS / 0 FAIL;
{release['binary_values']} original binary64 values in {release['binary_records']} records reopened from seven original
SimulationOutput MATs bind exactly to the reviewed JSON values. {len(qa['reviewer_selfchecks'])+len(release['reviewer_selfchecks'])} separate synthetic
reviewer self-checks pass. Complete source/reviewer/exporter snapshots and observed
MATLAB batch receipts are required by the release gate. Same agent, separate algorithms.

## Concrete blocker

The FLOOR trajectory's nominal branch target is 5 MWh. Original binary inputs
C=0.2 MWh/K, Ta=20 C, charge/direct approaches=2 K and delivery=45 C yield the
exact endpoint branch gap **-5/3602879701896397 K**, not zero. Actual v56 replay at
the nominal endpoint rejects with `DCHR:v55:UnresolvedBranch`. This proves the
nominal event descriptor cannot yet advance through the kink using the strict
instantaneous gate. No production guard was weakened and no invalid coupled
controller was saved. Prior fixed-temperature v52 acceptance remains intact.

Derivation: `audit/Charge_regime_derivation_v56.md`.
Evidence: `{folder.relative_to(ROOT).as_posix()}`.
Equation QA: `{qa_path.relative_to(ROOT).as_posix()}`.
Release QA: `{release_path.relative_to(ROOT).as_posix()}`.
Original model SHA256: `{sha(model)}`.

## Limits and handoff

''' + '\n'.join('- ' + x for x in limitations) + '\n\nNext actionable task: ' + NEXT + '\n'
    new_text(ROOT / 'audit/Charge_regime_results_v56.md', results)
    new_text(ROOT / 'MASTER_STAGEBOARD_v56.md', f'''# Charge event prerequisite checkpoint v56

UTC {stamp}. **Endpoint protocol OPEN; no coupled model acceptance.**
Accepted actual saved model remains 0.52, preserved with its original hash.

MATLAB {passed}/0; 146 charge cases / ten regimes; fresh 13 Stateflow intervals /
{positive} positive segments / six modes; six verified-reference comparisons; one runtime rejection.
Seven-interval temporal sequence: {qa['temporal_counts']['macro_transitions']} macro mode transitions,
{release['dwell_latch_changes']} independently checked latch changes.
Independent equations {qa['summary']['passed']}/0; separate release gate {release['passed']}/0;
{release['binary_values']} original binary64 values / seven MATs; seven separate reviewer self-checks.

Exact nominal-kink replay rejects: gap -5/3602879701896397 K.
Nominal event candidates cannot authorize propagated endpoints. No new SLX was built.
Synthetic engineering, no equipment calibration, article replication or physical validation;
full primary signoffs remain 0/31. Stateflow license/charts/execution observed, version list empty.

Authoritative results: `audit/Charge_regime_results_v56.md` and `STATUS_v56.json`.
Fresh immutable evidence: `{folder.relative_to(ROOT).as_posix()}`.
Prior unfinished v56 artifacts and failures are preserved; complete provenance now required.

Next actionable task: {NEXT}
''')
    progress = f'''\n\n## {stamp} — v56 resumed charge-regime prerequisite with fresh binary/dwell QA

Read STATUS/stageboard v55 and accepted stateflow v52, acceptance ledger, research frontier,
progress, saved builder/planner/allocation and v54/v55 code before changes. Discovered
unfinished v56 implementation/tests and earlier evidence; did not overwrite them.
Completed fresh actual execution and sealed a documented coupled-event blocker.

Work: all ten FLOOR/TANK affine charge limits, nominal reachability/earliest events,
146 cases/137 accepted/9 expected rejects. MATLAB {passed} PASS / 0 FAIL; actual saved v52
13 intervals/{positive} positive segments/all six modes, six v30 references, one runtime fault,
seven-interval sequence with six macro transitions and {release['dwell_latch_changes']} independently checked latch changes.
Independent equation/trace QA {qa['summary']['passed']}/0; added provenance/binary/dwell gate
{release['passed']}/0; {release['binary_values']} binary64 values/{release['binary_records']} records/seven original MATs;
seven separate reviewer self-checks. Model hash unchanged; no new SLX or coupled acceptance.

Files added this run: matlab/export_charge_release_v56.m, audit/run_charge_release_v56.ps1,
audit/verify_charge_release_v56.py, audit/finalize_charge_release_v56.py,
audit/Charge_regime_results_v56.md, STATUS_v56.json, MASTER_STAGEBOARD_v56.md,
fresh immutable evidence {folder.relative_to(ROOT).as_posix()}. Existing v56 component,
derivation and harnesses were resumed unchanged. Progress/acceptance ledgers append only.
Complete snapshots include temporal harness/reviewer/exporter omitted by earlier v56 evidence.

Remaining blocker: actual nominal E=5MWh kink rejects with DCHR:v55:UnresolvedBranch;
exact original-binary gap=-5/3602879701896397K. Event candidates remain nominal;
propagated energy enclosure, one-sided equality and variable-power compressor/source
integrals are unimplemented. Charge-only landscape is not coupled demand/discharge/dwell.
Synthetic topology/UA/hydraulics/equipment calibration and physical validation OPEN;
no new primary literature retrieved, signoffs0/31. Independent algorithms by same agent,
not personnel. Stateflow version list empty; license, two charts, execution directly observed.
Prior failures/data/models preserved; no Jarvice/unrelated files/settings/schedules/runner,
secrets or publication touched. Any fresh failed startup/test/reviewer logs remain in evidence.

Next actionable task: {NEXT}
Stop this coherent blocker checkpoint after packaging.
'''
    with (ROOT / 'automation/engineering_progress.md').open('a', encoding='utf-8') as f: f.write(progress)
    with (ROOT / 'automation/STATEFLOW_ACCEPTANCE.md').open('a', encoding='utf-8') as f:
        f.write(f'''\n\n## Charge-regime endpoint blocker checkpoint — {stamp} / v56

No new SLX or coupled acceptance. Saved v52 freshly executes 13 intervals/all six modes,
six MATLAB v30 comparisons, one runtime fault and a seven-interval sequence with six
mode transitions; original hash preserved. MATLAB {passed}/0; ten charge regimes/146 cases;
independent equation QA {qa['summary']['passed']}/0 and release gate {release['passed']}/0;
{release['binary_values']} original binary64 values/seven MATs and seven separate reviewer self-checks.
Actual nominal branch endpoint rejects with exact gap -5/3602879701896397K:
one-sided equality, bounded propagated endpoints and variable-power integrals remain OPEN.
STATUS_v56 and audit/Charge_regime_results_v56.md authoritative. Scoped implementation
and blocker evidence only; no equipment calibration/article replication/physical validation.
''')
    paths = [ROOT / n for n in ['STATUS_v56.json', 'MASTER_STAGEBOARD_v56.md', 'audit/Charge_regime_results_v56.md',
        'automation/engineering_progress.md', 'automation/STATEFLOW_ACCEPTANCE.md']]
    paths += [p for p in folder.rglob('*') if p.is_file() and not any(x in p.parts for x in ['local_build', 'temporal_build'])]
    packaging = dict(version='0.56', timestamp_utc=stamp, evidence_root=folder.relative_to(ROOT).as_posix(),
        scope='CHECKPOINT_AND_IMMUTABLE_EVIDENCE_HASHES_EXCLUDING_GENERATED_BUILD_CACHE',
        artifacts=[dict(path=p.relative_to(ROOT).as_posix(), size=p.stat().st_size, sha256=sha(p)) for p in paths])
    manifest_path = ROOT / 'audit' / f'Charge_regime_manifest_v56_{short}.json'
    new_json(manifest_path, packaging)
    for item in packaging['artifacts']: assert sha(ROOT / item['path']) == item['sha256']
    print(json.dumps(dict(status='STATUS_v56.json', evidence=status['result_directory'],
        result=status['result'], matlab_passed=passed, independent_passed=qa['summary']['passed']+release['passed'],
        manifest=manifest_path.relative_to(ROOT).as_posix(), artifacts=len(packaging['artifacts']))))

if __name__ == '__main__': main()
