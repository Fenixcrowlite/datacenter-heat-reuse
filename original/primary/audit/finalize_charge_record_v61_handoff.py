from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    report=json.loads((folder/'report.json').read_text());sf=json.loads((folder/'stateflow/report.json').read_text())
    qp=sorted(folder.glob('independent_QA_v61_*.json'))[-1];qa=json.loads(qp.read_text())
    sp=sorted((folder/'stateflow').glob('independent_QA_v57_*.json'))[-1];sq=json.loads(sp.read_text())
    assert all(v['summary']['failed']==0 for v in [report,sf,qa,sq])
    assert len(qa['reviewer_selfchecks'])==6 and all(v['passed'] for v in qa['reviewer_selfchecks'])
    assert all(v['passed'] for v in sq['reviewer_selfchecks']) and sq['counts']['mode_coverage']==list(range(6))
    assert len(report['runs'])==48 and len(report['faults'])==8 and len(sf['faults'])==12 and all(v['rejected'] for v in sf['faults'])
    assert all(v['record']['bounded_branch_continuation'] and not v['record']['compiled_stateflow_handoff_authorized'] and not v['record']['scalar_memory_handoff_authorized'] for v in report['runs'])
    for rec in json.loads((folder/'preservation.json').read_text()):assert sha(ROOT/rec['path'])==rec['sha256']
    for rec in json.loads((folder/'source_hashes.json').read_text()):assert sha(ROOT/rec['path'])==rec['sha256']==sha(folder/'source_snapshot'/rec['path'])
    stamp=datetime.now(timezone.utc).isoformat();rel=folder.relative_to(ROOT).as_posix()
    next_task='Implement fixed-size compiled correlated event/inventory/port/HP-clock memory retaining exact manifold provenance and enclosures, then build an additive continuously tank-linked Stateflow model that executes the v61 branch fixture without scalar snap/reset. Extend general limiters/event chains and uncertainty-aware dwell before six-mode/fault/reference acceptance. Preserve v52-v61; no unchanged annual-matrix reruns. Primary calibration and measured physical validation remain OPEN.'
    status=dict(version='0.61',timestamp_utc=stamp,inherits='STATUS_v59.json',result='HOST_CORRELATED_BRANCH_CONTINUATION_PASS_COMPILED_STATEFLOW_HANDOFF_BLOCKED',
        new_model=False,model_version='0.57',saved_model='matlab/simulink/DCHR_Dispatch_Stateflow_v57.slx',model_sha256=sq['model_sha256'],
        model_executed_this_run=True,coupled_stateflow_acceptance=False,finite_water_stateflow_acceptance='INHERITED_V57_AND_FRESHLY_REEXECUTED',
        matlab_version=sf['metadata']['matlab_version'],stateflow_license_observed=sf['metadata']['stateflow_license_test'],
        stateflow_version=sf['metadata']['stateflow_version'],chart_count=sf['metadata']['chart_count'],
        host_matlab_passed=report['summary']['passed'],host_matlab_failed=report['summary']['failed'],host_runs=len(report['runs']),host_runtime_rejections=len(report['faults']),
        independent_host_passed=qa['summary']['passed'],independent_host_failed=qa['summary']['failed'],host_reviewer_selfchecks=len(qa['reviewer_selfchecks']),
        stateflow_matlab_passed=sf['summary']['passed'],stateflow_matlab_failed=sf['summary']['failed'],stateflow_counts=sq['counts'],
        actual_runtime_fault_rejections=len(sf['faults']),reference_comparisons=len(sf['references']),independent_stateflow_passed=sq['summary']['passed'],independent_stateflow_failed=sq['summary']['failed'],
        defect_status='HOST_NONREPRESENTABLE_BRANCH_AND_EQUIVALENT_TIE_RESOLVED_IN_SCOPED_FIXTURES_COMPILED_CORRELATED_MEMORY_OPEN',
        full_primary_signoffs=0,total_sources=31,primary_article_replication=False,independent_physical_validation='NOT_TESTED',
        result_directory=rel,independent_host_qa=qp.relative_to(ROOT).as_posix(),independent_stateflow_qa=sp.relative_to(ROOT).as_posix(),
        derivation='audit/Charge_record_derivation_v61.md',next_actionable_task=next_task,
        limitations=['Host-only Java BigInteger exact manifold; no new SLX or compiled correlated memory/handoff accepted.',
            'Increasing FLOOR/REQUEST to TANK/REQUEST only, constant heat on both sides. Unique/equivalent constant right limiter set supported; other contacts/events, general interval initial inventory and event chains unsupported.',
            'Conditional outward binary64 arithmetic, |lambda*t|<=1, finite partition bounds. Correlated quantities reported as enclosures, never scalar service credit.',
            'Saved v57 held-macro boundary/normal-mode host planner/64 slots and inherited shadow warnings remain; Stateflow version listing is empty despite observed license, two charts and actual simulations.',
            'Same-agent independent Fraction/120-/160-digit algorithms and original-MAT binding; synthetic reviewer mutations separate. No equipment calibration, measured validation or new primary text.',
            'Development startup, JSON age orientation and package qualification failures retained. Final acceptance uses fresh sealed source execution.'])
    for name in ['STATUS_v61.json','STATUS_stateflow_v61.json']:
        path=ROOT/name;assert not path.exists();path.write_text(json.dumps(status,indent=2)+'\n')
    text=f'''# Correlated branch checkpoint v61 — compiled Stateflow handoff blocked

UTC {stamp}. Accepted saved plant remains **0.57**. No new SLX or continuously coupled Stateflow accepted.

Host continuation across exact nonrepresentable branch threshold: 48 runs,
MATLAB {report['summary']['passed']} PASS / 0 FAIL; eight domain/contact rejections;
independent Fraction/120-/160-digit/original-MAT QA {qa['summary']['passed']} PASS / 0 FAIL;
six separate reviewer mutations detected. Unique and exactly equivalent right
limiter sets, uncertain time/inventory/ports and HP-age continuity verified.
No scalar midpoint, inventory snap, age reset or scalar service credit authorized.

Actual saved v57: {len(sf['cases'])} scenarios / {sq['counts']['intervals']} intervals /
{sq['counts']['positive_segments']} positive segments / all six required modes;
MATLAB {sf['summary']['passed']} PASS / 0 FAIL; twelve actual runtime fault rejections;
six v30 reference comparisons; independent {sq['summary']['passed']} PASS / 0 FAIL;
seven separate reviewer mutations. Prior model/source/status hashes preserved.

Blocker: the exact manifold and correlated time/port constraints are host records;
saved v57 scalar TES/HP memory and held condenser inputs cannot preserve them.
Increasing constant-request branch crossing is supported. General events, arbitrary
interval inventory, compiled correlated memory and dwell/finite-water integration
remain OPEN. Synthetic engineering only; calibration/physical validation/primary
article replication remain OPEN, inherited full primary signoffs 0/31.

Evidence: `{rel}`. Derivation: `audit/Charge_record_derivation_v61.md`.
Failed development evidence remains in the earlier charge_record_v60 folders. The unfinished pre-existing v60 candidate has no accepted checkpoint; all 268 original candidate source hashes are restored/preserved. This new work uses v61.

Next actionable task: {next_task}
'''
    for name in ['MASTER_STAGEBOARD_v61.md','MASTER_STAGEBOARD_stateflow_v61.md','audit/Charge_record_results_v61.md']:
        path=ROOT/name;assert not path.exists();path.write_text(text)
    progress=f'''\n\n## {stamp} — v61 exact correlated branch continuation and compiled-memory blocker

Read latest STATUS/stageboard, acceptance, research frontier, progress, v55-v59
component/harness/QA and saved v57 builder/runtime code before changes. Stayed
within this project. No Jarvice access, settings/schedule/runner edits or publication.

Implemented versioned exact binary rational host arithmetic and correlated
constant-request FLOOR-to-TANK continuation. Exact equivalent limiter set,
symbolic event inventory, time/port/HP-age enclosures retained. Derived and
independently verified root/global ODE and analytic variable-source integrals.

MATLAB host {report['summary']['passed']} PASS/0 FAIL, 48 runs/eight rejections;
independent {qa['summary']['passed']}/0 plus six separately labelled reviewer mutations.
Saved v57 MATLAB {sf['summary']['passed']}/0, all six modes, twelve actual runtime
faults, six v30 references; independent {sq['summary']['passed']}/0 plus seven mutations.
Timestamped batch/reviewer logs, reopened original MATs, binary exports, numeric
traces and sealed sources in `{rel}`. Prior hashes unchanged. Development startup,
fixture orientation and package qualification failures preserved and repaired. A prematurely launched reviewer lacked the still-running batch receipt; final review waits for batch completion.

Files added: matlab/+dchr/+components/exact_rational_v61.m,
charge_branch_record_v61.m, matlab/run_charge_record_v61.m;
audit/prepare/run/verify/finalize_charge_record_v61, derivation/results/manifest,
STATUS_v61/stateflow_v61, MASTER_STAGEBOARD_v61/stateflow_v61 and immutable evidence.
Shared progress/acceptance appended only. No destructive cleanup.

A pre-existing unaccepted v60 scaffold was initially missed and its rational helper
filename collided with this work. Restored that original helper byte-for-byte from
the 120113 snapshot (SHA256 9390fb2163fa9cada672ba55c48b09d3a53c7bf3f82d1d270c96f003cda57f46);
all 268 original candidate source hashes match. Moved new work to v61, retaining
all v60 development evidence and new draft files inside results. A fresh v61
execution under sealed sources supplies final acceptance evidence.

Scope/blocker: host branch/tie representation solved in tested fixtures; no new
SLX or continuously coupled acceptance. Compiled scalar inventory/clock memory
cannot retain the manifold/port correlation. Other regimes/event chains/arbitrary
interval inventories remain unsupported. IEEE/span limits, same-agent independent
algorithms, synthetic physics and open calibration/physical validation explicit.
No new primary article evidence; inherited full signoffs 0/31.

Next actionable task: {next_task}
Stop after this coherent engineering prerequisite/blocker checkpoint and handoff.
'''
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:f.write(progress)
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
        f.write(f'\n\n## Correlated host branch record / compiled-memory blocker — {stamp} / checkpoint v61\n\nNo new SLX. Host 48 runs, MATLAB {report["summary"]["passed"]}/0, independent {qa["summary"]["passed"]}/0, eight rejections and six separate reviewer mutations. Exact nonrepresentable branch and equivalent persistent tie continue as correlated enclosures; compiled Stateflow memory/handoff remains OPEN. Actual saved v57 all six modes, twelve runtime faults/six references, MATLAB {sf["summary"]["passed"]}/0 and independent {sq["summary"]["passed"]}/0. STATUS_stateflow_v61 and derivation/results authoritative. Prior hashes preserved; physical validation/calibration/article replication OPEN.\n')
    paths=[p for p in folder.rglob('*') if p.is_file() and 'local_build' not in p.parts]
    paths += list((ROOT/'audit').glob('*v61.*')) + [ROOT/'matlab/run_charge_record_v61.m',ROOT/'matlab/+dchr/+components/exact_rational_v61.m',ROOT/'matlab/+dchr/+components/charge_branch_record_v61.m']
    paths += [ROOT/n for n in ['STATUS_v61.json','STATUS_stateflow_v61.json','MASTER_STAGEBOARD_v61.md','MASTER_STAGEBOARD_stateflow_v61.md','audit/Charge_record_results_v61.md','automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md']]
    manifest=dict(version='0.61',timestamp_utc=stamp,files=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in paths])
    mp=ROOT/'audit'/('Charge_record_manifest_v61_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')+'.json');mp.write_text(json.dumps(manifest,indent=2)+'\n')
    assert all(sha(ROOT/x['path'])==x['sha256'] for x in manifest['files']);print(json.dumps(dict(result=status['result'],manifest=mp.relative_to(ROOT).as_posix(),files=len(paths))))
if __name__=='__main__':main()

