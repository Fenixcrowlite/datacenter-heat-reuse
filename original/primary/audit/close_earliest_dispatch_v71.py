"""Validate and seal scoped v71 acceptance, comparisons and project handoff."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
import csv, hashlib, json, shutil, struct, sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(v):return [v] if isinstance(v[0],(int,float)) else v
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results');rel=folder.relative_to(ROOT).as_posix()
    report=json.loads((folder/'report.json').read_text());qas=sorted(folder.glob('independent_QA_v71_*.json'));assert qas
    qa=json.loads(qas[-1].read_text());assert report['summary']['failed']==qa['summary']['failed']==0 and all(v['passed'] for v in qa['reviewer_selfchecks'])
    assert not (ROOT/'STATUS_v71.json').exists() and not (folder/'closure.json').exists()
    checks=[]
    def check(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    for file in ['source_hashes.json','preservation.json']:
        for r in json.loads((folder/file).read_text()):
            check(file+'_'+r['path'],sha(ROOT/r['path'])==r['sha256'])
            if file=='source_hashes.json':check('snapshot_'+r['path'],sha(folder/'source_snapshot'/r['path'])==r['sha256'])
    runs={r['id']:r for r in report['runs']};ticks=segments=events=references=0;physical_modes=set();segment_modes=set()
    for id,r in runs.items():
        tr=rows(r['trace']);ticks+=len(tr);references+=len(r['reference_v30'])
        for tick,t in enumerate(tr):
            count=int(t[12]);segments+=count;events+=int(t[13]);last=t[100+80*(count-1):180+80*(count-1)]
            check(f'{id}_{tick}_final_chart_mode',t[0]==last[1]);check(f'{id}_{tick}_final_symbolic_tag',t[11]==last[21]);physical_modes.add(int(t[0]))
            segment_modes.update(int(t[101+80*j]) for j in range(count))
    check('actual_chart_state_modes',physical_modes==set(range(6)));check('segment_modes',segment_modes==set(range(6)))
    numeric=list(csv.DictReader((folder/qa['numeric_csv']).open()));aggregates={};comparison=[]
    with localcontext() as ctx:
        ctx.prec=180
        for id in runs:
            ns=[v for v in numeric if v['id']==id]
            totals={key:sum((D(v[key]) for v in ns),D(0)) for key in ['heat','source','work','standing','service','unmet']}
            totals['inventory']=D(ns[-1]['inventory']);totals['events']=int(sum(v['event']!='0' for v in ns));aggregates[id]=totals
        reference=aggregates['repeated_0p25']
        for id in ['repeated_0p5','repeated_1p0']:
            for key in ['heat','source','work','standing','service','unmet','inventory']:
                check(id+'_timestep_'+key,abs(aggregates[id][key]-reference[key])<D('1e-90')*max(D(1),abs(reference[key])))
            check(id+'_event_count',aggregates[id]['events']==reference['events'])
        oldfolder=ROOT/'results/event_candidates_v70_20261012T024414_059326Z';old=json.loads((oldfolder/'report.json').read_text());oldruns={r['id']:r for r in old['runs']}
        # Compare the preserved original-MAT binary trace, not rounded table data.
        oldbinary={}
        for rec in json.loads((oldfolder/'binary_manifest.json').read_text()):
            if rec['id'] not in ['stop_overshoot_repair','repeated_0p25','repeated_0p5','repeated_1p0']:continue
            flat=[v[0] for v in struct.iter_unpack('<d',(oldfolder/rec['file']).read_bytes())];n=rec['columns'];v=[flat[k:k+n] for k in range(0,len(flat),n)]
            if rec['rows']==1:v=v[0]
            check('prior_binary_'+rec['id']+'_'+rec['field'],v==oldruns[rec['id']][rec['field']]);oldbinary[rec['id'],rec['field']]=v
        for id in ['stop_overshoot_repair','repeated_0p25','repeated_0p5','repeated_1p0']:
            check('matched_'+id,oldbinary[id,'cfg'][35:]==runs[id]['p'] and oldbinary[id,'input']==runs[id]['input'])
            ot=rows(oldbinary[id,'trace'])[-1];nt=rows(runs[id]['trace'])[-1];ex=aggregates[id]
            item=dict(id=id,event_count=ex['events'],earliest_heat=str(ex['heat']),earliest_source=str(ex['source']),earliest_work=str(ex['work']),earliest_service=str(ex['service']),earliest_unmet=str(ex['unmet']),
                sampled_heat=ot[40:42],sampled_source=ot[42:44],sampled_work=ot[44:46],sampled_service=ot[141:143],sampled_unmet=ot[149:151],
                earliest_model_service=nt[42:44],earliest_model_unmet=nt[46:48])
            comparison.append(item)
        # The controlled held schedules have the same demand/source boundaries;
        # only numerical partition changes. This is a synthetic invariance test.
        for id in ['repeated_0p25','repeated_0p5','repeated_1p0']:
            u=rows(runs[id]['input']);check(id+'_52h',sum(D(F(x[4]).numerator)/D(F(x[4]).denominator) for x in u)==52)
        check('multiple_cycles_one_call',sum(t[13] for t in rows(runs['multiple_cycles_one_call']['trace']))==11)
    failed=[v for v in checks if not v['passed']]
    now=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    supplemental=dict(version='0.71',timestamp_utc=now,checks=checks,comparisons=comparison,partition_comparison_budget='1e-90 relative/absolute on independently computed 160-digit trajectories; original-model enclosure checks have no tolerance',
        summary=dict(passed=sum(v['passed'] for v in checks),failed=len(failed)))
    path=folder/f'handoff_QA_v71_{stamp}.json';path.write_text(json.dumps(supplemental,indent=2)+'\n');assert not failed,failed
    closure_sources=[]
    for src in [Path(__file__),ROOT/'audit/Earliest_dispatch_derivation_v71.md']:
        relative=src.relative_to(ROOT).as_posix();dst=folder/'closure_source_snapshot'/relative;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);closure_sources.append(dict(path=relative,sha256=sha(src)))
    (folder/'closure_source_hashes.json').write_text(json.dumps(closure_sources,indent=2)+'\n')
    model=ROOT/'matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v71.slx'
    limitations=[
        'Analytic earliest physical segments execute within macro Stateflow protocol calls. Chart state is final positive segment mode; solver-clock thermal event firing is not claimed.',
        'Conditional normal-mode interval arithmetic, conservative lower-bound HP limiter and hull eligibility; lambda*heldDt<=1, sixteen segments per call, kind=1 only. Unresolved boundary/root/dwell/pair order rejects. No generated-code or arbitrary-domain acceptance.',
        'Root-time and symbolic threshold/manifold provenance plus port/clock/age offsets are retained; Cartesian evaluation conservatively widens correlations. No root midpoint consumed. Broad long-horizon numerical-resolution audit remains open.',
        'Same-agent algorithmic independence using exact-binary Fraction and 120/160-digit closed exp/log/source integrals, not independent personnel. Original MAT reopened/exported by MATLAB, not an independent HDF5 parser.',
        'Synthetic engineering fixtures and reduced fixed-approach equipment model. Primary calibration, article replication, measured validation and full primary signoffs remain OPEN (0/31).',
        'No annual v71 simulation or migration of annual adapters/report consumers is accepted. Legacy accepted v57/v66/v70 and earlier evidence are preserved.'
    ]
    nexttask='Audit saved-v71 earliest-segment numerical admissibility and conservation under long repeated service, small restart bands, finite source/water limiter ties, external-disable ON dwell and segment-budget exhaustion. Execute original-MAT counterexamples or scoped acceptance with closed-form QA; preserve v57-v71. Then adapt a held-boundary annual input/reporting interface for v71 before any annual earliest-event claim. Primary calibration and measured validation remain OPEN.'
    status=dict(version='0.71',timestamp_utc=now,inherits='STATUS_v70.json',result='SCOPED_REPEATED_EARLIEST_EVENT_SEGMENTS_ACCEPTED_QA_PASS',new_model=True,saved_model=model.relative_to(ROOT).as_posix(),model_sha256=sha(model),model_executed_this_run=True,
        accepted_dispatch_model='matlab/simulink/DCHR_Dispatch_Stateflow_v57.slx',accepted_sampled_interval_model='matlab/simulink/DCHR_Interval_Dispatch_Stateflow_v66.slx',accepted_event_candidate_model='matlab/simulink/DCHR_Event_Candidates_Stateflow_v70r2.slx',
        accepted_scoped_earliest_event_model=model.relative_to(ROOT).as_posix(),coupled_stateflow_acceptance='SCOPED_MACRO_ANALYTIC_EARLIEST_SEGMENTS',general_repeated_earliest_event_stateflow='SCOPED_TESTED_IMPLEMENTATION_ONLY',
        matlab_passed=report['summary']['passed'],matlab_failed=0,independent_passed=qa['summary']['passed'],independent_failed=0,handoff_passed=supplemental['summary']['passed'],handoff_failed=0,
        actual_runs=len(runs),held_intervals=ticks,positive_event_segments=segments,interior_events=events,required_mode_coverage=sorted(physical_modes),actual_runtime_rejections=len(report['faults']),v30_reference_comparisons=references,
        reviewer_selfchecks=len(qa['reviewer_selfchecks']),matlab_metadata=report['metadata'],result_directory=rel,independent_qa=qas[-1].relative_to(ROOT).as_posix(),handoff_qa=path.relative_to(ROOT).as_posix(),
        derivation='audit/Earliest_dispatch_derivation_v71.md',results='audit/Earliest_dispatch_results_v71.md',primary_article_replication=False,independent_physical_validation='NOT_TESTED',full_primary_signoffs=0,total_sources=31,limitations=limitations,next_actionable_task=nexttask)
    table=['| Synthetic schedule | Earliest events | Earliest served | Sampled served hull | Earliest unmet | Sampled unmet hull |','|---|---:|---:|---|---:|---|']
    for c in comparison:
        table.append(f"| {c['id']} | {c['event_count']} | {D(c['earliest_service']):.9f} | [{c['sampled_service'][0]:.9f}, {c['sampled_service'][1]:.9f}] | {D(c['earliest_unmet']):.9f} | [{c['sampled_unmet'][0]:.9f}, {c['sampled_unmet'][1]:.9f}] |")
    resulttext=f'''# Executed earliest-event Stateflow segments v71

UTC {now}. New saved model: `{status['saved_model']}`.
Actual normal-mode MATLAB simulation executes repeated analytic stop/cutoff/
restart segments in the same six-mode chart. This is scoped executable
implementation acceptance, with the limitations below.

MATLAB **{status['matlab_passed']} PASS / 0 FAIL**; independent exact-binary
closed-form QA **{status['independent_passed']} PASS / 0 FAIL**; separate
closure/preservation QA **{status['handoff_passed']} PASS / 0 FAIL**.
{len(runs)} runs / {ticks} held intervals / {segments} positive segments /
{events} interior events / all six actual final chart modes;
{len(report['faults'])} actual runtime rejections, {references} singleton v30
comparisons, eight detected reviewer corruptions.

One macro interval executes eleven stop/restart events. The dt=0.25/0.5/1
52-hour schedules each execute eight interior events. Independent physical
service, source/work, standing losses and final inventory agree between those
partitions within the labelled 1e-90 high-precision comparison budget. Actual
trace enclosure checks use no tolerance. Cutoff-before-restart recomputes
passive forcing and elapsed OFF age; forced-discharge restart, inactive
contacts/delayed controls, future charge sink, zero/positive loss and exact
lambda*duration=1 witnesses execute. Genuine enabled event collisions,
held-boundary contacts and unresolved derivative signs reject.

Comparison uses exact matched inputs/equipment and preserved v70 original-MAT
binary exports. Numeric values are synthetic project fixture energy units,
not paper data or measured performance. The stop witness has no heat demand;
its meaningful difference is positive charging before its actual stop rather
than sampled whole-interval withholding. Earlier sampled controller outcomes
remain valid under their own policy.

{chr(10).join(table)}

Detailed heat/source/work and service enclosures are in
`{path.name}` and `{qa['numeric_csv']}`. All original/reopened MAT,
little-endian binary/JSON traces, timestamped MATLAB/Python logs, exit receipts,
model/source/reviewer seals and prior-model/checkpoint hashes are retained in
`{rel}`. The accepted model was built once at 02:57:47 execution and then loaded
unchanged for the successful run; subsequent edits corrected test expectations
and increased the explicit synthetic multi-cycle fixture's finite water limit.

Development failures preserved: workspace-restricted MATLAB startup at
02:56:09; non-scalar increment-array compile diagnostic in 02:56:09/02:57:13
folders; 02:57:47 full simulation with 2338 PASS / 4 FAIL (three old sampled-mode
expectations and one unreachable multi-cycle fixture); first independent QA
with no trajectory failures but failed acceptance/exit checks and two inactive
mutation controls. Preparation initially used a stale fault fixture identifier;
it failed before creating an evidence folder and was corrected. No failed
development run is counted as acceptance; none was deleted or overwritten.

Limitations:

{chr(10).join('- '+x for x in limitations)}

Next actionable task: {nexttask}
Stop after this coherent executable deliverable and handoff.
'''
    for name in ['STATUS_v71.json','STATUS_stateflow_v71.json']:(ROOT/name).write_text(json.dumps(status,indent=2)+'\n')
    (ROOT/status['results']).write_text(resulttext)
    stage=f'''# Scoped executed earliest-event segment acceptance v71

UTC {now}. Saved `{status['saved_model']}` actually executes all six modes,
{events} earliest events and eleven stop/restarts in one physical held interval.
MATLAB {status['matlab_passed']}/0; independent {status['independent_passed']}/0;
closure {status['handoff_passed']}/0; eight runtime rejections and eight reviewer
mutations detected. {ticks} held intervals, {segments} positive segments,
{references} v30 comparisons; matched dt=0.25/0.5/1 invariance passes.

Evidence `{rel}` and audit/Earliest_dispatch_results_v71.md are authoritative.
Root hulls, symbolic threshold contacts, forcing/port offsets and OFF age
survive each event. Candidate forcing is recomputed after cutoff/stop/restart.
No root midpoint is consumed; unresolved event and boundary order rejects.
Legacy models and evidence preserved. Scope is macro analytic event segments
inside Stateflow, not solver-clock event firing, annual v71 or calibrated
physical validation. Same-agent closed-form QA; full primary signoffs 0/31.

Next actionable task: {nexttask}
'''
    for name in ['MASTER_STAGEBOARD_v71.md','MASTER_STAGEBOARD_stateflow_v71.md']:(ROOT/name).write_text(stage)
    progress=f'''\n\n## {now} — v71 executed correlated earliest-event segments

Read latest STATUS/stageboards, Stateflow acceptance, frontier, progress and
v70/v69/v66 code before changes. Work stayed in this project; no Jarvice,
unrelated files, settings, tasks, runner, secrets or publication touched.

Added versioned builder, unchanged inherited strict root certifier, correlated
segment kernel, harness and actual saved six-mode model. Executed stop/cutoff/
restart consumption with symbolic contacts, root/clock/age/energy offset
provenance and forcing recomputation. Eleven events execute within one held
interval; repeated dt=0.25/0.5/1 physical trajectories match independently.

PASS/FAIL: MATLAB {status['matlab_passed']}/0; independent
{status['independent_passed']}/0; closure {status['handoff_passed']}/0;
{len(runs)} runs/{ticks} held intervals/{segments} positive segments/{events}
interior events/all six actual final chart modes; eight runtime rejections,
{references} exact-singleton v30 comparisons, eight reviewer mutations detected.
Evidence `{rel}` has timestamped logs/receipts, original/reopened MAT,
little-endian binary/CSV, source/model seals and unchanged preservation hashes.
Earlier development failures and their logs remain preserved and are described
in audit/Earliest_dispatch_results_v71.md.

Files: matlab/simulink/earliest_dispatch_kernel_v71.m,
certify_event_root_v71.m, build_earliest_dispatch_v71.m,
DCHR_Earliest_Dispatch_Stateflow_v71.slx; matlab/run_earliest_dispatch_v71.m;
audit/scaffold/prepare/run/verify/close earliest dispatch v71,
Earliest_dispatch_derivation/results_v71.md; STATUS/stageboards v71.
Shared ledgers appended byte-preservingly only.

Limitations: macro analytic event segments inside Stateflow, no solver-clock
thermal firing; finite segment/span/kind domain and conservative hulls;
same-agent algorithmic QA, MATLAB MAT reopening; annual v71, primary calibration,
article replication, measured validation and full signoffs (0/31) OPEN.

Next actionable task: {nexttask}
Stop after this coherent executed deliverable and clear handoff.
'''
    acceptance=f'''\n\n## Scoped earliest-event segment acceptance — {now} / v71

New saved v71 executes repeated root consumption in the SAME six-mode chart:
MATLAB {status['matlab_passed']}/0, independent {status['independent_passed']}/0,
closure {status['handoff_passed']}/0; {ticks} held intervals/{segments} positive
segments/{events} interior events, eleven stop/restarts in one macro interval;
eight runtime rejections and eight reviewer corruptions detected. Symbolic
threshold/root/port/clock/age provenance retained; forcing recomputed after
every event; matched repeated dt partitions pass. Scoped analytic macro
segments only, not solver-clock firing/annual v71/calibrated validation.
STATUS/stageboards v71 and Earliest_dispatch_results_v71.md authoritative;
legacy models preserved. Primary calibration/replication/measured QA OPEN.
'''
    frontier=f'''\n\n## {now} — v71 repeated earliest-event implementation handoff

Actual saved model now consumes repeated roots with correlated symbolic
threshold/port/clock/OFF-age records; independent closed-form trajectory QA
passes. No new primary text, source signoff or physical calibration.

Next actionable task: {nexttask}
'''
    for path,text in [('automation/engineering_progress.md',progress),('automation/STATEFLOW_ACCEPTANCE.md',acceptance),('audit/research_frontier_2026_10_08.md',frontier)]:
        with (ROOT/path).open('ab') as f:f.write(text.encode('utf-8'))
    artifacts=[]
    for p in folder.rglob('*'):
        if p.is_file() and not any(part in ['cache','codegen'] for part in p.relative_to(folder).parts):artifacts.append(dict(path=p.relative_to(folder).as_posix(),sha256=sha(p)))
    checkpoint=[]
    for p in [ROOT/'STATUS_v71.json',ROOT/'STATUS_stateflow_v71.json',ROOT/'MASTER_STAGEBOARD_v71.md',ROOT/'MASTER_STAGEBOARD_stateflow_v71.md',ROOT/status['results'],model]:checkpoint.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
    closure=dict(timestamp_utc=now,result=status['result'],model_sha256=sha(model),checkpoint_hashes=checkpoint,evidence_hashes=artifacts)
    (folder/'closure.json').write_text(json.dumps(closure,indent=2)+'\n')
    print(json.dumps(dict(result=status['result'],evidence=rel,MATLAB=report['summary'],independent=qa['summary'],handoff=supplemental['summary'],ticks=ticks,segments=segments,events=events,comparisons=comparison)))
if __name__=='__main__':main()
