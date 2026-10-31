"""Publish an additive defect checkpoint and byte-preserving local handoff."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal as D
import hashlib, json, shutil, sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(v):return [v] if isinstance(v[0],(int,float)) else v
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    rel=folder.relative_to(ROOT).as_posix();assert not (ROOT/'STATUS_v72.json').exists() and not (folder/'closure.json').exists()
    report=json.loads((folder/'report.json').read_text());qapath=sorted(folder.glob('independent_QA_v72_*.json'))[-1];qa=json.loads(qapath.read_text())
    assert report['summary']['failed']==qa['summary']['failed']==0 and all(v['passed'] for v in qa['reviewer_selfchecks'])
    for manifest in ['source_hashes.json','preservation.json','reviewer_sources.json']:
        for r in json.loads((folder/manifest).read_text()):assert sha(ROOT/r['path'])==r['sha256'],r['path']
    ticks=segments=events=references=0;finalmodes=set()
    for r in report['runs']:
        trace=rows(r['trace']);ticks+=len(trace);segments+=sum(int(t[12]) for t in trace);events+=sum(int(t[13]) for t in trace)
        references+=len(r['reference_v30']);finalmodes.update(int(t[0]) for t in trace)
    assert finalmodes==set(range(6))
    defects=sorted({r['classification'] for r in qa['findings'] if r['classification'].startswith('OPEN_')});assert len(defects)==4
    rejected=[p for p in report['probes'] if not p['accepted']]
    now=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    nexttask='Implement additive saved v73 numerical-admissibility repairs: stable monotone passive/affine inventory images; correlated ON-age equality certificate; source-capacity proof retaining selected limiter/denominator relation; correlated compressor-work/auxiliary nonnegativity proof. Execute all original v72 counterexamples and six modes, long passive/repeated schedules, exact/early/late disable, source/water ties, narrow bands, genuine collision and explicit segment-exhaustion controls. Preserve v57-v72. Accept only after saved-model execution and independent closed-form original-MAT QA; then develop the held-boundary annual adapter. Primary calibration and measured validation remain OPEN.'
    limitations=[
        'Four numerical admissibility defects remain OPEN in saved v71. This checkpoint reproduces defects and accepts no repaired or annual model.',
        'Accepted traces cover synthetic tested fixtures only. Actual rejected calls have runtime diagnostics; separately executed valid prefixes are saved. No complete trajectory is claimed for a rejected call.',
        'Diagnostic return/capture copies run on the MATLAB host only. They supply rejection-branch operands and are separately labelled, not saved-model execution or independent QA.',
        'Same-agent algorithmic QA with exact-binary Fraction and 120/160-digit closed exp/log/source equations; not independent personnel. MAT reopening/export uses MATLAB, not an independent HDF5 parser.',
        'Macro analytic physical segments execute within Stateflow protocol calls; no solver-clock thermal firing, generated-code or arbitrary-domain acceptance. Sixteen-segment resource limit remains explicit.',
        'Primary article replication, equipment calibration, measured validation and annual v71 remain untested. Full primary signoffs remain 0/31.'
    ]
    status=dict(version='0.72',timestamp_utc=now,inherits='STATUS_v71.json',result='SAVED_V71_FOUR_NUMERICAL_ADMISSIBILITY_DEFECTS_CONFIRMED_QA_PASS',new_model=False,
        saved_model='matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v71.slx',saved_model_version='0.71',model_sha256=qa['model_sha256'],model_executed_this_run=True,
        accepted_dispatch_model='matlab/simulink/DCHR_Dispatch_Stateflow_v57.slx',accepted_sampled_interval_model='matlab/simulink/DCHR_Interval_Dispatch_Stateflow_v66.slx',
        accepted_scoped_earliest_event_model='matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v71.slx',corrected_model_accepted=False,
        matlab_passed=report['summary']['passed'],matlab_failed=0,independent_passed=qa['summary']['passed'],independent_failed=0,
        actual_probe_scenarios=len(report['probes']),accepted_probe_scenarios=len(report['probes'])-len(rejected),accepted_runs_including_valid_prefixes=len(report['runs']),
        completed_held_intervals=ticks,positive_event_segments=segments,interior_events=events,required_actual_final_mode_coverage=sorted(finalmodes),
        actual_runtime_rejections=len(rejected),v30_reference_comparisons=references,reviewer_selfchecks=len(qa['reviewer_selfchecks']),
        open_defect_classes=defects,findings=qa['findings'],matlab_metadata=report['metadata'],result_directory=rel,
        independent_qa=qapath.relative_to(ROOT).as_posix(),derivation='audit/Earliest_admissibility_derivation_v72.md',results='audit/Earliest_admissibility_results_v72.md',
        primary_article_replication=False,independent_physical_validation='NOT_TESTED',full_primary_signoffs=0,total_sources=31,limitations=limitations,next_actionable_task=nexttask)
    text=f'''# Saved-v71 numerical admissibility defects v72

UTC {now}. The preserved saved `{status['saved_model']}` was freshly executed.
Four numerical rejection defects are **CONFIRMED OPEN**. No new SLX or repaired
controller acceptance is claimed; v71's prior acceptance stays scoped.

MATLAB execution/monitor checks **{status['matlab_passed']} PASS / 0 FAIL**;
independent original-MAT closed-form QA **{status['independent_passed']} PASS / 0 FAIL**;
eight separate reviewer corruption controls detected.
These counts mean the audit reproduced and verified its evidence; they do not
mean the controller is repaired. {len(report['probes'])} probe scenarios:
{status['accepted_probe_scenarios']} accepted and {len(rejected)} runtime rejections.
{len(report['runs'])} accepted runs including separately executed valid prefixes,
{ticks} completed held intervals, {segments} positive segments, {events} interior
events, all six actual final chart modes and {references} singleton v30 comparisons.

| Witness | Actual saved-model outcome | Independent evidence |
|---|---|---|
| Passive HP service, lambda=0.2/h | TES bounds refusal at hour 91 | E=3.74077583572529e-8 remains positive; 90-hour actual prefix retained |
| Passive HP service, lambda=1/h | TES bounds refusal at hour 23 | E=3.07856388951057e-10 remains positive; 22-hour actual prefix retained |
| External disable at exact ON dwell | Refuses at 0.25h | Two exact 0.125h holds meet 0.25h; retained lower-age endpoint falls below equality |
| Source-limited / rounded water tie / below tie | Three finite-source guard refusals | Exact selected host-replay source rates remain below capacity; widened upper boxes fail comparison |
| Restart band 2^-42 K | Nonnegative-energy guard refusal | Exact work=1.68616713036551e-14 is positive; interval subtraction lower endpoint is negative |
| Segment budget control | Explicit 16-segment refusal | Ideal exact policy needs 23 positive segments / 22 interior events; resource limit remains explicit |

All values are synthetic fixture model units, not measurements or article data.
Refusals are fail-closed. No physical capacity violation, negative exact work
or premature physical dwell transition is demonstrated. The concrete blocker
is loss of admissible operation from interval dependencies and equality proof.

Controls pass: 256-hour passive service at lambda=0.01/h; 208-hour repeated
service (four copies of the prior held demand schedule); early disable refuses
and later disable accepts; water-limited and above-tie controls accept; restart
bands 2^-10, 2^-20 and 2^-32 K accept. Every accepted actual trace and prefix
passes independent energy/source/work/service, event, clock and first-law
enclosure checks at 120/160-digit precision. Numeric closed trajectories are
saved in `{qa['numeric_csv']}`. No broad annual acceptance is inferred.

Evidence: `{rel}`. Original and reopened MAT, binary exports, numeric CSV,
timestamped MATLAB/Python logs, execution receipts, original/diagnostic/reviewer
source seals and prior model/checkpoint preservation hashes are retained.
The four instrumented diagnostic host runs capture operands before the same
source/work guards; they are labelled separately from actual Stateflow and QA.
The production model and source hashes are unchanged.

Development failures retained: initial restricted MATLAB startup with file
system inconsistency; first diagnostic replay incorrectly indexed a singleton
JSON input as a row. The corrected replay reshapes the input, creates a fresh
timestamped diagnostic function and succeeds; failed source/logs are preserved.
No failed run is counted as acceptance and no evidence was deleted.

Limitations:

'''+''.join('- '+v+'\n' for v in limitations)+f'''
Next actionable task: {nexttask}
Stop after this coherent executed defect checkpoint and handoff.
'''
    (ROOT/'audit/Earliest_admissibility_results_v72.md').write_text(text)
    for name in ['STATUS_v72.json','STATUS_stateflow_v72.json']:(ROOT/name).write_text(json.dumps(status,indent=2)+'\n')
    stage=f'''# Saved-v71 numerical admissibility defect checkpoint v72

UTC {now}. Four OPEN numerical false-rejection classes reproduced on actual
saved v71: passive inventory wrapping, exact ON-dwell equality, source-limiter
proof dependency, correlated compressor-work nonnegativity. No repaired SLX.
MATLAB {status['matlab_passed']}/0; independent {status['independent_passed']}/0;
eight reviewer mutations detected. {ticks} completed intervals / {segments}
positive segments / {events} events / all six final modes. Nine actual runtime
refusals include correct early-disable and explicit segment-budget controls.

Authoritative evidence `{rel}` and audit/Earliest_admissibility_results_v72.md.
Prior v57-v71 models/checkpoints preserved. QA is algorithmically independent
same-agent, not independent personnel; host diagnostics are labelled separately.
Annual, physical validation and primary calibration remain OPEN; signoffs 0/31.

Next actionable task: {nexttask}
'''
    for name in ['MASTER_STAGEBOARD_v72.md','MASTER_STAGEBOARD_stateflow_v72.md']:(ROOT/name).write_text(stage)
    progress=f'''

## {now} — v72 saved-v71 numerical admissibility defect audit

Read STATUS/stageboards, acceptance/frontier/progress and production/builder/
harness/reviewer code before changes. Work stayed in this project. No Jarvice,
unrelated files, settings, scheduler, runner, secrets or publication touched.

Fresh actual saved-v71 simulation confirms four OPEN rejection defects:
passive wrapping at 91/23h; exact 0.25h ON-dwell equality; finite source/water
limiter proof; tiny correlated work/auxiliary nonnegativity. Preserved actual
valid prefixes and independently proved admissible exact quantities. Nine
runtime refusals include true early-disable and explicit segment-budget limits.
No new SLX or corrected acceptance. 208h repeated service and 256h lower-loss
passive control pass; six actual final chart modes and v30 comparisons pass.

PASS/FAIL: MATLAB {status['matlab_passed']}/0; independent {status['independent_passed']}/0;
eight reviewer corruptions detected; {len(report['probes'])} probes, {ticks} completed held
intervals, {segments} positive segments, {events} interior events. Evidence `{rel}`
has timestamped logs, execution receipts, original/reopened MAT, binary/CSV,
sealed sources and prior preservation hashes. Algorithmic same-agent QA uses
exact-binary Fraction/120/160-digit closed exp/log/source formulas. Diagnostic
host capture copies are explicitly separate from saved-model execution and QA.

Files added: matlab/run_earliest_admissibility_v72.m, run_earliest_rejection_probes_v72.m;
audit/prepare/run/verify/seal/close earliest admissibility v72 and diagnostic
runner; derivation/results v72; STATUS/stageboard twins. Shared ledgers append
only. Initial MATLAB startup and diagnostic shape failures remain retained.

Limitations: four numerical blockers OPEN; no annual v71, repaired model,
primary replication/calibration, measured validation or independent personnel
QA. Full primary signoffs 0/31; macro analytic segments only, no solver-clock
thermal event firing or generated-code acceptance.

Next actionable task: {nexttask}
Stop after this coherent executed defect checkpoint and clear handoff.
'''
    acceptance=f'''\n\n## Saved-v71 admissibility defects — {now} / checkpoint v72

Actual preserved v71 freshly executed all six final modes. MATLAB
{status['matlab_passed']}/0 and independent {status['independent_passed']}/0 reproduce four OPEN
numerical rejection defects with exact-binary closed-form evidence; no new SLX
or corrected acceptance. {ticks} accepted/prefix held intervals, nine runtime
refusals and eight reviewer mutations retained. STATUS/stageboards v72 and
audit/Earliest_admissibility_results_v72.md are authoritative. Prior v71 scope
is preserved; long passive/source-tie/dwell/tiny-band admissibility blocks broad
annual acceptance. Same-agent algorithmic QA; calibration/physical validation
remain OPEN. Next: additive v73 repairs described in the checkpoint.
'''
    frontier=f'''\n\n## {now} — v72 executed numerical-admissibility blockers

Saved-v71 runtime evidence and independent closed equations confirm four
numerical rejection classes. No new primary text or source signoff.

Next actionable task: {nexttask}
'''
    for name,append in [('automation/engineering_progress.md',progress),('automation/STATEFLOW_ACCEPTANCE.md',acceptance),('audit/research_frontier_2026_10_08.md',frontier)]:
        p=ROOT/name;before=p.read_bytes()
        with p.open('ab') as f:f.write(append.encode('utf-8'))
        assert p.read_bytes().startswith(before)
    paths=[Path(__file__),ROOT/'audit/Earliest_admissibility_derivation_v72.md',ROOT/'audit/Earliest_admissibility_results_v72.md']
    seal=[]
    for src in paths:
        r=src.relative_to(ROOT).as_posix();dst=folder/'closure_source_snapshot'/r;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);seal.append(dict(path=r,sha256=sha(src)))
    (folder/'closure_source_hashes.json').write_text(json.dumps(seal,indent=2)+'\n')
    checkpoints=[ROOT/n for n in ['STATUS_v72.json','STATUS_stateflow_v72.json','MASTER_STAGEBOARD_v72.md','MASTER_STAGEBOARD_stateflow_v72.md','audit/Earliest_admissibility_results_v72.md','audit/Earliest_admissibility_derivation_v72.md']]
    (folder/'closure.json').write_text(json.dumps(dict(timestamp_utc=now,qa=qapath.name,checkpoint_hashes=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in checkpoints]),indent=2)+'\n')
    (folder/f'closure_{stamp}.log').write_text(f'V72 DEFECT CHECKPOINT SEALED; MATLAB {status["matlab_passed"]}/0; QA {status["independent_passed"]}/0; 4 OPEN classes; next v73.\n')
    evidence=[]
    for p in sorted(folder.rglob('*')):
        if p.is_file() and 'cache' not in p.relative_to(folder).parts and 'codegen' not in p.relative_to(folder).parts and p.name!='evidence_manifest.json':
            evidence.append(dict(path=p.relative_to(folder).as_posix(),sha256=sha(p)))
    (folder/'evidence_manifest.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(dict(result=status['result'],summary=report['summary'],independent=qa['summary'],intervals=ticks,segments=segments,events=events,references=references,sealed=len(evidence))))
if __name__=='__main__':main()
