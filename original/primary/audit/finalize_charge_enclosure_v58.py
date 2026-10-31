from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    report=json.loads((folder/'report.json').read_text());sf=json.loads((folder/'stateflow/report.json').read_text())
    qp=sorted(folder.glob('independent_QA_v58_*.json'))[-1];qa=json.loads(qp.read_text())
    sp=sorted((folder/'stateflow').glob('independent_QA_v57_*.json'))[-1];sq=json.loads(sp.read_text())
    assert all(v['summary']['failed']==0 for v in [report,sf,qa,sq])
    assert qa['reviewer_selfchecks']['failed']==0 and all(x['passed'] for x in sq['reviewer_selfchecks'])
    assert qa['regimes']==10 and sq['counts']['mode_coverage']==list(range(6))
    for rec in json.loads((folder/'preservation.json').read_text()):assert sha(ROOT/rec['path'])==rec['sha256']
    for rec in json.loads((folder/'source_hashes.json').read_text()):assert sha(ROOT/rec['path'])==rec['sha256']==sha(folder/'source_snapshot'/rec['path'])
    stamp=datetime.now(timezone.utc).isoformat();relative=folder.relative_to(ROOT).as_posix()
    next_task=('Implement outward isolation of branch/limiter event times and an explicit one-sided equality protocol using the v58 propagated energy enclosure, without silently snapping an unresolved energy or resetting inventory. Specify correlated endpoint/energy/memory handoff and event power integration. Then integrate an additive continuously tank-linked Stateflow model preserving v57 compiled finite-water guards and v52 cutoff/restart/dwell, execute six modes/fault/reference tests and independent original-MAT QA. Preserve v52-v58; do not repeat unchanged annual matrices. Primary calibration remains OPEN.')
    status=dict(version='0.58',timestamp_utc=stamp,inherits='STATUS_v57.json',result='BOUNDED_CHARGE_REGIMES_PASS_CONTINUOUS_EVENT_PROTOCOL_BLOCKED',
        model_version='0.57',new_model=False,saved_model='matlab/simulink/DCHR_Dispatch_Stateflow_v57.slx',model_sha256=sq['model_sha256'],
        model_executed_this_run=True,coupled_stateflow_acceptance=False,finite_water_stateflow_acceptance='INHERITED_V57_AND_FRESHLY_REEXECUTED',
        matlab_version=sf['metadata']['matlab_version'],stateflow_license_observed=sf['metadata']['stateflow_license_test'],
        stateflow_version=sf['metadata']['stateflow_version'],sfroot_class=sf['metadata']['sfroot_class'],chart_count=sf['metadata']['chart_count'],
        charge_matlab_passed=report['summary']['passed'],charge_matlab_failed=report['summary']['failed'],charge_cases=qa['cases'],charge_regimes=qa['regimes'],
        stateflow_matlab_passed=sf['summary']['passed'],stateflow_matlab_failed=sf['summary']['failed'],actual_scenarios=len(sf['cases']),
        actual_runtime_fault_rejections=sum(v['rejected'] for v in sf['faults']),reference_comparisons=len(sf['references']),
        independent_charge_passed=qa['summary']['passed'],independent_charge_failed=qa['summary']['failed'],independent_stateflow_passed=sq['summary']['passed'],
        independent_stateflow_failed=sq['summary']['failed'],charge_reviewer_selfchecks=qa['reviewer_selfchecks'],stateflow_reviewer_selfchecks=len(sq['reviewer_selfchecks']),
        stateflow_counts=sq['counts'],original_charge_binary_values=qa['binary_values'],max_source_enclosure_width_MWh=qa['max_source_enclosure_width_MWh'],
        exact_kink_gap_K=qa['exact_kink_gap_K'],defect_status='ONE_SIDED_BRANCH_LIMITER_EVENT_AND_CORRELATED_ENDPOINT_HANDOFF_OPEN',
        full_primary_signoffs=0,total_sources=31,primary_article_replication=False,independent_physical_validation='NOT_TESTED',
        result_directory=relative,independent_charge_qa=qp.relative_to(ROOT).as_posix(),independent_stateflow_qa=sp.relative_to(ROOT).as_posix(),
        limitations=['v58 is a bounded single charge regime component, not a new SLX or continuously coupled controller. Branch/limiter event equality and demand/discharge/supervisor integration remain OPEN.',
            'Conditional IEEE binary64 round-to-nearest/gradual-underflow enclosure; |k*t|<=1 at every outward node; at most 4096 cells. Rectangles bound variable-power source energy, without a user-specified accuracy guarantee. Strict hull gate may reject valid steps conservatively.',
            'Synthetic finite-water/HP/TES assumptions; no equipment map, finite UA/hydraulics, physical calibration or article replication. No new primary literature retrieved; inherited signoffs 0/31.',
            'Independent Fraction/Decimal analytic equations by same agent, not independent personnel. Original MAT exports retained. Reviewer mutations are synthetic self-checks.',
            'Saved v57 scope remains held-macro boundary with normal-mode host planner/64 slots and inherited shadow warnings. Observed license/charts/execution; empty Stateflow version list.',
            'Initial MATLAB sandbox startup failure preserved. Earlier development evidence is preserved; final evidence comes from the sealed fresh source snapshot.'],next_actionable_task=next_task)
    for name in ['STATUS_v58.json','STATUS_stateflow_v58.json']:
        p=ROOT/name;assert not p.exists();p.write_text(json.dumps(status,indent=2)+'\n')
    text=f'''# Bounded charge prerequisite v58 — event protocol blocked

UTC {stamp}. Accepted saved model remains **0.57**; no new SLX or continuous coupling accepted.

New v58 MATLAB component encloses all ten charge regimes directly from binary inputs,
using finite Taylor tails and outward source/compressor energy integration.
57 fixtures: MATLAB {report['summary']['passed']} PASS / 0 FAIL;
independent analytic QA {qa['summary']['passed']} PASS / 0 FAIL, five reviewer mutations.
Original nominal kink still rejects; exact gap {qa['exact_kink_gap_K']} K.

Actual saved v57 reexecuted 13 scenarios / {sq['counts']['intervals']} intervals /
{sq['counts']['positive_segments']} positive segments / all six modes.
MATLAB {sf['summary']['passed']} PASS / 0 FAIL; twelve actual runtime faults and six v30 comparisons.
Independent Stateflow QA {sq['summary']['passed']} PASS / 0 FAIL, seven reviewer mutations.
All prior source/model/status hashes preserved.

Evidence: `{relative}`. Derivation: `audit/Charge_enclosure_derivation_v58.md`.
No primary calibration, measured physical validation, or article replication accepted.
Next actionable task: {next_task}
'''
    for name in ['MASTER_STAGEBOARD_v58.md','MASTER_STAGEBOARD_stateflow_v58.md','audit/Charge_enclosure_results_v58.md']:
        p=ROOT/name;assert not p.exists();p.write_text(text)
    progress=f'''\n\n## {stamp} — v58 bounded-charge prerequisite and explicit coupled-event blocker

Read STATUS/stageboard/acceptance v57, research frontier, progress and v55–v57
component/builder/harness/reviewer code before changes. Implemented additive
charge_enclosure_v58 with coefficient/energy/integral enclosures for all ten regimes.
No production exp/log assumption; 24-term Taylor plus finite outward tail.
Variable source/compressor energy is enclosed; separate exact Fraction and
80/120-digit analytic reviewer verifies original-MAT binary inputs/outputs.

Charge MATLAB {report['summary']['passed']}/0; 57 cases/all ten regimes;
independent {qa['summary']['passed']}/0 plus five separate mutations.
Saved v57 actually reexecuted 13 scenarios/66 intervals/78 positive segments/all
six modes: MATLAB 328/0, twelve runtime rejections, six v30 comparisons;
independent {sq['summary']['passed']}/0 plus seven separate mutations.
Both numerical traces and timestamped batch/reviewer logs preserved in `{relative}`.
Initial sandbox MATLAB startup failure and earlier development evidence preserved.
Outward-node span validation added before final fresh-source execution.

Changed/added: matlab/+dchr/+components/charge_enclosure_v58.m,
matlab/run_charge_enclosure_v58.m, audit/prepare/run/verify/finalize_charge_enclosure_v58,
derivation/results, versioned STATUS/stageboards, immutable evidence and append-only ledgers.
All prior MATLAB/model/status/stageboard hashes unchanged. No Jarvice/unrelated
files, user settings, schedules, runner, secrets or external publication touched.

Limits/blocker: not a new SLX or coupled-controller acceptance. Actual nominal
event enclosure rejects and original binary kink gap remains {qa['exact_kink_gap_K']} K.
One-sided equality/time isolation/correlated handoff still OPEN. Domain is strict
single-regime |kt|<=1; synthetic physics, primary equipment calibration and
measured physical validation OPEN. Same-agent independent algorithms, not personnel.
Saved v57 held-macro/host-planner/shadow warnings remain; empty Stateflow version list.
No new primary literature; inherited signoffs 0/31.

Next actionable task: {next_task}
Stop after this coherent prerequisite/blocker checkpoint and clear handoff.
'''
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:f.write(progress)
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
        f.write(f'\n\n## Bounded-charge prerequisite / coupled-event blocker — {stamp} / checkpoint v58\n\nNo new SLX. Saved v57 freshly executes all six modes, twelve faults and six v30 references; MATLAB328/0, independent{sq["summary"]["passed"]}/0. New bounded v58 charge component covers ten regimes/57 fixtures; MATLAB294/0, independent{qa["summary"]["passed"]}/0 plus five separate mutations. Single-regime integration accepted only; one-sided event/equality/correlated handoff remains OPEN, original exact kink rejection retained. STATUS_stateflow_v58 and charge derivation/results authoritative. Physical validation/article replication/primary calibration remain OPEN.\n')
    evidence=[p for p in folder.rglob('*') if p.is_file() and 'local_build' not in p.parts]
    release=[ROOT/n for n in ['STATUS_v58.json','STATUS_stateflow_v58.json','MASTER_STAGEBOARD_v58.md','MASTER_STAGEBOARD_stateflow_v58.md','audit/Charge_enclosure_results_v58.md','automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md']]
    manifest=dict(version='0.58',timestamp_utc=stamp,files=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in evidence+release])
    mp=ROOT/'audit'/('Charge_enclosure_manifest_v58_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')+'.json')
    mp.write_text(json.dumps(manifest,indent=2)+'\n')
    assert all(sha(ROOT/x['path'])==x['sha256'] for x in manifest['files'])
    print(json.dumps(dict(status=status['result'],manifest=mp.relative_to(ROOT).as_posix(),files=len(manifest['files']))))
if __name__=='__main__':main()
