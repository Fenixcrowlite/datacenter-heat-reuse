from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil, sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    r=json.loads((folder/'report.json').read_text());qp=sorted(folder.glob('independent_QA_v55_*.json'))[-1];q=json.loads(qp.read_text())
    assert r['summary']['failed']==q['failed']==q['reviewer_selfchecks_failed']==0
    for rec in json.loads((folder/'preservation.json').read_text()):assert sha(ROOT/rec['path'])==rec['sha256']
    stamp=datetime.now(timezone.utc).isoformat();rel=folder.relative_to(ROOT).as_posix();qa=qp.relative_to(ROOT).as_posix()
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v52.slx'
    nexttask=('Derive all charge-side request/nameplate/hot-flow/source limiter regimes and their earliest branch, limiter and capacity events. '
              'Use the v55 conservative instantaneous gate, explicitly resolve equality/event endpoints, and bound propagated endpoint energy error. '
              'Only then build an additive energy-linked condenser/COP/variable-port Stateflow release with demand, cutoff/restart/dwell memory, '
              'strict padding/handoff, six required modes, fault tests and independent equations/original-MAT QA. Preserve saved v52 and v53/v54/v55 controls; '
              'avoid unchanged annual matrices. Primary calibration remains OPEN.')
    limitations=[
        'No new SLX or accepted coupled Stateflow controller. Accepted saved v52 unchanged; two fresh held-boundary charge controls execute only mode 2. Prior six-mode acceptance remains STATUS_stateflow_v52.json.',
        'The v55 wrapper conservatively rejects intervals including zero, including exact equality and some resolvable near-kink signs. It certifies exact binary instantaneous inputs under IEEE binary64 round-to-nearest/gradual-underflow assumptions; it is not a certified event endpoint or general active-limiter selector.',
        'Instantaneous source uniqueness is diagnostic only. General charge-side limiter regimes, direct/discharge coupled service, earliest events, propagated exponential endpoint-error enclosure and variable-power integrals remain unimplemented; new coupled model acceptance stays blocked by these prerequisites.',
        'Synthetic tank-return variable-flow engineering topology; no UA, hydraulics, minimum/standby-flow/pump law, calibrated equipment map, article replication or independent measured physical validation. No new literature or primary text was retrieved in this focused implementation run; inherited source signoffs remain 0/31.',
        'Independent QA means exact Fraction equations plus separately implemented 80-digit Decimal saved-trace checks by the same agent; not independent personnel, universal floating-point proof or continuous-coupling validation.',
        'Stateflow license, two actual charts and normal-mode execution observed. ver(Stateflow) is empty; no installed Stateflow version fabricated. Inherited shadow warnings and 64-slot host-planner/standalone deployment limits persist.',
        'Sandbox MATLAB startup failed with filesystem inconsistency; failure log retained. Authorized local batch passes. No production/model tolerance, saved controller or prior evidence was modified.'
    ]
    status=dict(version='0.55',timestamp_utc=stamp,inherits='STATUS_v54.json',
                result='CONSERVATIVE_INSTANTANEOUS_BRANCH_GATE_PASS_COUPLED_STATEFLOW_PREREQUISITES_OPEN',
                model_version='0.52',new_model=False,saved_model=model.relative_to(ROOT).as_posix(),model_sha256=sha(model),
                model_executed_this_run=True,matlab_version=r['metadata']['matlab_version'],
                stateflow_license_observed=r['metadata']['stateflow_license_test']==1,stateflow_version=r['metadata']['stateflow_version'],chart_count=r['metadata']['chart_count'],
                matlab_passed=r['summary']['passed'],matlab_failed=0,component_vectors=q['vectors'],
                resolved_accepted=q['resolved_accepted'],unresolved_rejected=q['unresolved_rejected'],component_domain_rejections=len(r['faults']),
                exact_witness_gap_fraction=q['exact_witness_gap_fraction'],legacy_v54_branch_disagreements_reproduced_and_rejected=len(q['legacy_branch_defects']),
                independent_passed=q['passed'],independent_failed=0,reviewer_selfchecks_passed=q['reviewer_selfchecks_passed'],reviewer_selfchecks_failed=0,
                actual_intervals=q['actual_intervals'],actual_positive_segments=q['actual_positive_segments'],actual_modes_this_run=q['actual_modes'],
                prior_six_mode_acceptance='STATUS_stateflow_v52.json',coupled_stateflow_acceptance=False,
                full_primary_signoffs=0,total_sources=31,primary_article_replication=False,independent_physical_validation='NOT_TESTED',
                result_directory=rel,independent_qa=qa,limitations=limitations,next_actionable_task=nexttask)
    paths=[ROOT/'STATUS_v55.json',ROOT/'MASTER_STAGEBOARD_v55.md',ROOT/'audit/Branch_guard_results_v55.md']
    assert all(not p.exists() for p in paths)
    paths[0].write_text(json.dumps(status,indent=2)+'\n')
    text=f'''# Conservative coupled branch checkpoint v55

UTC {stamp}. Instantaneous gate implementation and independent QA PASS.
Accepted model stays 0.52; no new SLX or coupled Stateflow acceptance.

MATLAB {r['summary']['passed']} PASS / 0 FAIL. {q['vectors']} vectors:
{q['resolved_accepted']} resolved accepted, {q['unresolved_rejected']} unresolved
rejected, six invalid-domain rejections. All twelve retained v54 exact-branch
misclassifications are reproduced and safely rejected. The original witness has
exact gap {q['exact_witness_gap_fraction']} K ({q['exact_witness_gap_K']:.17g} K).
No guard/tolerance was weakened. Exact equality deliberately rejects.

Independent exact rational interval/sign/limiter algebra, original-MAT binding,
80-digit held-input ODE/first-law/port/clock checks and preservation evidence:
{q['passed']} PASS / 0 FAIL. Five separately counted reviewer mutations detected.
Two actual normal-mode saved-v52 simulations execute two positive charging
segments (mode 2): source-limited and hot-flow-limited sampled controls. Exact
energy handoff and zero-span padding remain preserved. This is not continuous
coupling or fresh six-mode coupled acceptance.

Evidence: `{rel}`. Independent QA: `{qa}`.
Derivation: `audit/Branch_guard_derivation_v55.md`.
Source/model snapshots, original SimulationOutputs/MAT reopens, binary inputs,
timestamped MATLAB/reviewer logs and startup-failure receipt retained.

Limitations:

'''+''.join('- '+x+'\n' for x in limitations)+f'\nNext actionable task: {nexttask}\n'
    paths[1].write_text(text);paths[2].write_text(text.replace('# Conservative coupled branch checkpoint v55','# Coupled branch guard results v55',1))
    note=f'''

## {stamp} — v55 conservative branch-domain repair and actual saved-v52 controls

Read STATUS/stageboard v54, Stateflow acceptance, frontier, engineering progress,
v54 component/harness and saved v52 builder/controller context before editing.
Completed the concrete v54 branch-gate handoff. Added outward binary-input
temperature/limit certificates and a rejecting v55 boundary wrapper; preserved
v54/v53/v52 and all prior evidence. No new SLX acceptance is claimed.

MATLAB {r['summary']['passed']} PASS / 0 FAIL; {q['vectors']} vectors,
{q['resolved_accepted']} resolved accepted and {q['unresolved_rejected']} unresolved
rejected; six domain rejections. All twelve v54 exact-branch defects reproduced
and rejected, including gap {q['exact_witness_gap_fraction']} K. Two actual saved-v52
source/hot-limited charge controls execute 2 intervals/2 positive segments/mode 2.
Independent exact rational/80-digit ODE/original-MAT/handoff/padding/preservation
QA {q['passed']} PASS / 0 FAIL; five separate reviewer mutations detected.
Initial sandbox MATLAB startup failure retained; authorized local batch succeeds.

Files created: matlab/+dchr/+components/coupled_branch_certificate_v55.m,
matlab/+dchr/+components/coupled_temperature_boundary_v55.m,
matlab/run_branch_guard_v55.m, audit/prepare_branch_guard_v55.py,
audit/run_branch_guard_v55.ps1, audit/verify_branch_guard_v55.py,
audit/finalize_branch_guard_v55.py, audit/Branch_guard_derivation_v55.md,
audit/Branch_guard_results_v55.md, STATUS_v55.json, MASTER_STAGEBOARD_v55.md and
fresh immutable evidence {rel}. Shared ledgers appended only. No Jarvice/unrelated
files, settings, scheduled tasks, runner, secrets or publication touched.

Remaining limitations: conservative exact-equality/near-kink rejection; no
general event selector, exponential trajectory-error bound, complete charge-side
limiter dynamics or new coupled Stateflow. Synthetic variable-flow topology,
no calibrated UA/hydraulics/pumps/equipment, full primary signoffs 0/31 and no
physical validation. Same-agent independent algorithms, not independent personnel.
Inherited Stateflow shadow warnings/host planner remain; version list empty,
license/charts/actual execution observed. Saved v52 hash remains {sha(model)}.

Next actionable task: {nexttask}

Evidence: {qa}. Stop after this coherent gate checkpoint and sealed handoff.
'''
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as out:out.write(note)
    acceptance=f'''

## Conservative coupled-interface prerequisite — {stamp} / checkpoint v55

No new SLX. Additive instantaneous v55 branch gate rejects all twelve v54
exact-input branch disagreements, with {q['vectors']} vectors,
MATLAB {r['summary']['passed']}/0, independent {q['passed']}/0 and five reviewer
mutations. Saved v52 executes two held-boundary charge controls; its accepted
six-mode scope remains STATUS_stateflow_v52.json. Coupled Stateflow acceptance
remains OPEN pending limiter/event/endpoint-error/variable-port derivation and
actual six-mode execution. STATUS_v55 and audit/Branch_guard_results_v55.md
are authoritative. No physical calibration or article replication claimed.
'''
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as out:out.write(acceptance)
    # Bind the reviewer/finalizer added after pre-execution snapshots separately.
    supplemental=[]
    for p in [ROOT/'audit/verify_branch_guard_v55.py',ROOT/'audit/finalize_branch_guard_v55.py']+paths:
        dest=folder/'source_snapshot'/p.relative_to(ROOT);assert not dest.exists()
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        supplemental.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
    (folder/'supplemental_source_hashes.json').write_text(json.dumps(supplemental,indent=2)+'\n')
    manifest=[]
    for p in sorted(folder.rglob('*')):
        if p.is_file() and 'local_build' not in p.parts:
            manifest.append(dict(path=p.relative_to(folder).as_posix(),sha256=sha(p),size=p.stat().st_size))
    mp=folder/'artifact_manifest_v55.json';assert not mp.exists();mp.write_text(json.dumps(manifest,indent=2)+'\n')
    assert all(sha(folder/x['path'])==x['sha256'] and (folder/x['path']).stat().st_size==x['size'] for x in manifest)
    # Seal the status and handoff bindings without changing any earlier result.
    seal=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),passed=True,manifest_sha256=sha(mp),artifact_count=len(manifest),
              handoff_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in paths},
              ledgers_sha256={name:sha(ROOT/name) for name in ['automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md']})
    (folder/'packaging_QA_v55.json').write_text(json.dumps(seal,indent=2)+'\n')
    print(json.dumps(dict(status='STATUS_v55.json',matlab=r['summary'],independent=q['passed'],manifest_artifacts=len(manifest),result_directory=rel)))
if __name__=='__main__':main()
