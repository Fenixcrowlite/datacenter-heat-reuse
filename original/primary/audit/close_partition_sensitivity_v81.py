"""Publish workspace-only checkpoint after observed MATLAB and independent QA."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal as D
import csv, hashlib, json, shutil, sys

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_new(p,text):
    with p.open('x',encoding='utf-8') as f:f.write(text)
def json_new(p,value):write_new(p,json.dumps(value,indent=2)+'\n')

def main(folder):
    report=json.loads((folder/'report.json').read_text())
    qa_path=sorted(folder.glob('independent_QA_v81_*.json'))[-1]
    qa=json.loads(qa_path.read_text())
    assert report['summary']['failed']==qa['summary']['failed']==qa['sensitivity_summary']['failed']==0
    assert len(report['runs'])==len(report['attempts'])==26 and all(a['accepted'] for a in report['attempts'])
    assert all(c['passed'] for c in qa['reviewer_selfchecks'])
    runs=report['runs'];intervals=sum(r['summary']['held_intervals'] for r in runs)
    segments=sum(r['summary']['positive_segments'] for r in runs)
    events=sum(r['summary']['interior_events'] for r in runs)
    mode=report['mode_coverage'];assert mode==list(range(6))
    # Human-readable actual interval records from the verified reopened export.
    with (folder/'actual_interval_traces_v81.csv').open('x',newline='') as f:
        writer=csv.writer(f)
        writer.writerow(['id','tick','duration_h','physical_end_h','final_mode',
                         'initial_TES_lower_MWh','initial_TES_upper_MWh',
                         'final_TES_lower_MWh','final_TES_upper_MWh','HP_latch',
                         'age_lower_h','age_upper_h','segments','events',
                         'first_law_lower_MWh','first_law_upper_MWh'])
        for r in runs:
            trace=r['trace'];trace=[trace] if isinstance(trace[0],(float,int)) else trace
            inp=r['input'];inp=[inp] if isinstance(inp[0],(float,int)) else inp
            for k,(row,u) in enumerate(zip(trace,inp)):
                writer.writerow([r['id'],k,u[4],u[2],row[0],*row[2:9],*row[12:14],*row[52:54]])
    ts=datetime.now(timezone.utc).isoformat();rel=folder.relative_to(ROOT).as_posix()
    rows=[]
    for c in qa['sensitivity']:
        if c['factor']!=8:continue
        agg=qa['aggregates'][c['id']]
        maxdiff=max(abs(D(v)) for v in c['differences'].values())
        src=c['hulls']['recovered_source_MWh_hull'];work=c['hulls']['compressor_work_MWh_hull']
        rows.append(f"| {c['family']} | {float(D(agg['delivered_service'])):.9g} | {float(D(agg['final_inventory'])):.9g} | {float(maxdiff):.3g} | {src['base_width']:.6g} → {src['split_width']:.6g} | {work['base_width']:.6g} → {work['split_width']:.6g} |")
    maxdiff=max(abs(D(v)) for c in qa['sensitivity'] for v in c['differences'].values())
    limitations=[
        'Synthetic bounded normal-mode schedules for the reduced engineering HP/TES equations only; no annual, calibrated equipment, article replication, measured physical validation or generated-code acceptance. Primary signoffs remain 0/31.',
        'No new SLX or thermal/controller/reporting change: actual saved model 0.80, embedded thermal kernel/trace schema 75 and reporting API 0.76 remain preserved. Checkpoint and model versions differ.',
        'Same-agent algorithmic independence: Fraction operand histories and 120/160-digit closed exp/log trajectories call no production MATLAB solver. MATLAB reopens original MAT and exports binary; no independent personnel or independent MAT parser claim.',
        'Sensitivity budget 1e-10 relative to max(1,absolute quantity) is an experiment acceptance threshold, never a relaxed production guard. Hull overlap and widths are also recorded; no midpoint is used as physical truth.',
        'Five physical schedules and dyadic partitions do not prove arbitrary partition invariance. Existing clock/span/event collision/segment-budget domains and necessary-only runtime monitors remain.',
    ]
    next_task='Resume primary equipment-map evidence and boundary audit from audit/HP_upstream_boundary_results_v44.md. Seek a new accessible route to primary text and the performance-correlation supplement for DOI 10.1016/j.tsep.2025.103513; distinguish verified coefficients/domains from metadata and access blockers. Preserve saved v80 and v81 actual partition evidence; do not repeat the same monitor or sensitivity fixtures without new evidence.'
    narrative=f'''UTC {ts}. Preserved saved Stateflow v80 actually executes 26 complete schedules,
{intervals} held intervals, {segments} positive segments and {events} interior events;
all six required final modes observed. MATLAB {report['summary']['passed']} PASS / 0 FAIL;
independent equation/artifact QA {qa['summary']['passed']} PASS / 0 FAIL;
15 matched partition comparisons PASS / 0 FAIL and four separate reviewer
self-checks PASS. Saved model reopened clean and first fixture replayed bitwise.

Five identical physical input histories were split into 1, 2, 4 and 8 pieces
per original hold. Exact Fraction histories verify operand sums and held inputs.
Closed exp/log trajectories at 120/160 digits independently verify original-MAT
inventory, event ordering/dwell, source/work/loss/service/backup/unmet and reports.
Every compared reporting hull overlaps and every event sequence/time meets the
predeclared budget. Maximum absolute aggregate difference across all 15
comparisons is {maxdiff} MWh. This is a reconstruction difference, not a
midpoint estimate of a simulated hull. Differences at roughly 160-digit
reviewer precision indicate reconstruction roundoff, not measured plant accuracy.

The practical tradeoff is in the enclosures. For the 48-hour schedule,
splitting 0.5-hour holds into eight 0.0625-hour holds reduces the recovered-source
hull width from about 0.00220020 to 0.000277281 MWh (about 7.94 times narrower),
while the final-inventory hull widens from about 3.36e-12 to 2.59e-11 MWh.
Additional protocol calls tighten the source quadrature rectangles but accumulate
more outward binary roundoff. Smaller steps do not uniformly tighten every hull.

| Physical schedule, split8 | Delivered service (MWh) | Final TES (MWh) | Max aggregate delta (MWh) | Source hull width, split1 → split8 (MWh) | Work hull width, split1 → split8 (MWh) |
|---|---:|---:|---:|---:|---:|
'''+ '\n'.join(rows)+f'''

No new SLX: actual model remains `matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v80.slx`,
SHA256 `{qa['model_sha256']}`. Its six-mode Stateflow builder and all prior models,
MATLAB code and status/stageboards are hash-preserved. Checkpoint version is 0.81.
This delivers a fresh executable MATLAB sensitivity harness and independent
physical-schedule comparison, not another runtime monitor.

Evidence `{rel}` includes timestamped MATLAB/Simulink logs, execution receipts,
26 original MAT files and reopened combined MAT, binary exports, numeric CSV,
specification, source snapshots and preservation hashes. Initial restricted
MATLAB startup failure is retained separately; only the successful completed
batch counts. No runtime schedule refusals occurred.

Limits:
'''+ '\n'.join('- '+x for x in limitations)+f'\n\nNext actionable task: {next_task}\n'
    source=['matlab/run_partition_sensitivity_v81.m','audit/run_partition_sensitivity_v81.ps1',
            'audit/partition_sensitivity_v81.py','audit/close_partition_sensitivity_v81.py',
            'audit/Partition_sensitivity_derivation_v81.md']
    status=dict(version='0.81',timestamp_utc=ts,inherits='STATUS_v80.json',
        result='SAVED_V80_PARTITION_SENSITIVITY_ACCEPTED_INDEPENDENT_QA_PASS',new_model=False,
        saved_model='matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v80.slx',saved_model_version='0.80',
        model_sha256=qa['model_sha256'],model_executed_this_run=True,trace_schema=75,reporting_api_version='0.76',
        matlab_passed=report['summary']['passed'],matlab_failed=0,
        independent_passed=qa['summary']['passed'],independent_failed=0,
        complete_saved_model_runs=26,held_intervals=intervals,positive_segments=segments,interior_events=events,
        required_actual_final_mode_coverage=mode,partition_comparisons_passed=15,partition_comparisons_failed=0,
        maximum_absolute_aggregate_difference_MWh=str(maxdiff),reviewer_selfchecks=4,
        matlab_metadata=report['metadata'],result_directory=rel,independent_qa=qa_path.relative_to(ROOT).as_posix(),
        derivation='audit/Partition_sensitivity_derivation_v81.md',results='audit/Partition_sensitivity_results_v81.md',
        source_code=source,primary_article_replication=False,independent_physical_validation='NOT_TESTED',
        full_primary_signoffs=0,total_sources=31,limitations=limitations,next_actionable_task=next_task)
    json_new(ROOT/'STATUS_v81.json',status);json_new(ROOT/'STATUS_stateflow_v81.json',status)
    for path in ['MASTER_STAGEBOARD_v81.md','MASTER_STAGEBOARD_stateflow_v81.md','audit/Partition_sensitivity_results_v81.md']:
        write_new(ROOT/path,'# Saved-Stateflow physical partition sensitivity v81\n\n'+narrative)
    progress=f'''\n\n## {ts} — v81 actual saved-Stateflow partition experiment

Read STATUS/stageboards v80, STATEFLOW_ACCEPTANCE, research frontier/progress,
thermal kernel, v80 builder/monitor/harness, held adapter/reporters and independent
reviewers before edits. Work stayed in this project; Jarvice, unrelated files,
settings, scheduled tasks and runner untouched. No external publication.

Files added: {', '.join(source)}, results report and STATUS/stageboard twins.
Shared ledgers appended only. No production code or model changed.

{narrative}
Stop after this coherent executed deliverable and clear handoff.
'''
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:f.write(progress)
    for path in ['automation/STATEFLOW_ACCEPTANCE.md','audit/research_frontier_2026_10_08.md']:
        with (ROOT/path).open('a',encoding='utf-8') as f:
            f.write(f'\n\n## Saved-v80 partition acceptance — {ts} / checkpoint v81\n\n'+narrative)
    files=source+['STATUS_v81.json','STATUS_stateflow_v81.json','MASTER_STAGEBOARD_v81.md',
                  'MASTER_STAGEBOARD_stateflow_v81.md','audit/Partition_sensitivity_results_v81.md']
    sealed=[]
    for name in files:
        p=ROOT/name;dst=folder/'closure_snapshot'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
        sealed.append(dict(path=name,sha256=sha(p)))
    json_new(folder/'closure_manifest.json',sealed)
    print(json.dumps({k:status[k] for k in ['result','matlab_passed','independent_passed','held_intervals','positive_segments','interior_events','maximum_absolute_aggregate_difference_MWh']}))

if __name__=='__main__':
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results');main(folder)
