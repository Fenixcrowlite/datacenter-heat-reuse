"""Close only executed passing v75 evidence, preserve ledger prefixes and seal artifacts."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil, sys
from reporting_provenance_v75 import FILES, REVIEWERS, MODEL
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2);f.write('\n')
def append(rel,text):
    with (ROOT/rel).open('ab') as f:f.write(('\n\n'+text.rstrip()+'\n').encode('utf-8'))
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    r=json.loads((folder/'report.json').read_text());qpath=sorted(folder.glob('independent_QA_v75_*.json'))[-1];q=json.loads(qpath.read_text())
    assert r['summary']['failed']==q['summary']['failed']==0 and all(c['passed'] for c in q['reviewer_selfchecks'])
    assert len(r['mutations'])==17 and all(m['legacy_accepted'] and m['new_error']==m['expected_error'] for m in r['mutations'])
    for p in ['STATUS_v75.json','STATUS_stateflow_v75.json','MASTER_STAGEBOARD_v75.md','MASTER_STAGEBOARD_stateflow_v75.md','audit/Reporting_provenance_results_v75.md']:assert not (ROOT/p).exists()
    utc=datetime.now(timezone.utc).isoformat();relative=folder.relative_to(ROOT).as_posix()
    def rows(x):return [x] if isinstance(x[0],(float,int)) else x
    intervals=sum(len(rows(run['trace'])) for run in r['runs'])
    segments=sum(int(row[12]) for run in r['runs'] for row in rows(run['trace']))
    events=sum(int(row[13]) for run in r['runs'] for row in rows(run['trace']))
    limitations=[
        'Synthetic bounded schedules; no annual representation, calibration, article replication or measured physical validation. Full primary signoffs remain 0/31.',
        'Same-agent algorithmic independence at 120/160 digits; MATLAB MAT reopening and binary export, not an independent HDF5 reader or independent personnel.',
        'v75 adds input provenance and reporting consistency only. Thermal policy is unchanged and bitwise compared with saved v73r2 outside schema/provenance fields. Macro analytic segments, no solver-clock event firing or generated-code claim.',
        'Consistency checks reject demonstrated single faults. Coordinated replacement of provenance, segments, headers and inputs is not authenticated. Independent physical-equation QA remains required.',
        'Inherited finite engineering arithmetic, span, event-order, dwell, clock and segment-budget restrictions remain. Production reporter does not independently recompute all nonlinear thermal trajectories.',
    ]
    next_task='Resume primary equipment-map evidence and boundary audit using audit/HP_upstream_boundary_results_v44.md. Seek a new accessible route to source20 upstream [62] primary text and performance-correlation supplement, DOI 10.1016/j.tsep.2025.103513; distinguish verified text/coefficients/domains from metadata and document any access blocker. Trace refrigerant versus water axes and compressor/auxiliary power before a separate calibrated backend. Preserve accepted v57/v66/v73r2/v75 and all v74/v75 evidence; no annual or calibrated performance inference.'
    status=dict(version='0.75',timestamp_utc=utc,inherits='STATUS_v74.json',result='SAVED_STATEFLOW_REPORTING_PROVENANCE_REPAIR_ACCEPTED_QA_PASS',
                new_model=True,saved_model=MODEL,saved_model_version='0.75',model_executed_this_run=True,corrected_model_accepted=True,
                correction_scope='Input provenance and production reporting consistency; thermal dispatch unchanged',model_sha256=sha(ROOT/MODEL),
                inherited_model_acceptance_preserved=True,matlab_passed=r['summary']['passed'],matlab_failed=0,independent_passed=q['summary']['passed'],independent_failed=0,
                reviewer_selfchecks=len(q['reviewer_selfchecks']),actual_corruption_rejections=len(r['mutations']),legacy_report_acceptance_counterexamples=len(r['mutations']),
                complete_saved_model_runs=len(r['runs']),actual_saved_v73r2_comparisons=len(r['runs'])-1,completed_held_intervals=intervals,positive_event_segments=segments,interior_events=events,
                required_actual_final_mode_coverage=r['mode_coverage'],matlab_metadata=r['metadata'],result_directory=relative,independent_qa=qpath.relative_to(ROOT).as_posix(),
                derivation='audit/Reporting_provenance_derivation_v75.md',results='audit/Reporting_provenance_results_v75.md',source_code=FILES,
                primary_article_replication=False,independent_physical_validation='NOT_TESTED',full_primary_signoffs=0,total_sources=31,
                development_failures_preserved=['results/reporting_provenance_v75_20261012T081216_110192Z'],limitations=limitations,next_actionable_task=next_task)
    for rel in ['STATUS_v75.json','STATUS_stateflow_v75.json']:dump(ROOT/rel,status)
    summary=f'''UTC {utc}. New saved v75 Stateflow model executes all six modes.
MATLAB {r['summary']['passed']} PASS / 0 FAIL; independent closed-form/binary/artifact
QA {q['summary']['passed']} PASS / 0 FAIL; {len(q['reviewer_selfchecks'])} separate reviewer self-checks.
{len(r['runs'])} complete saved-v75 runs / {intervals} held intervals / {segments} positive
segments / {events} interior events. Nine fresh saved-v73r2 comparisons preserve
every thermal output bitwise outside schema/provenance columns.
Seventeen actual reporting corruptions/misassociated-input controls reproduce
legacy reporter acceptance and are rejected by v75. No corrupted record is a
physical plant simulation. The changed-source control executes separately.
Evidence `{relative}`; actual model `{MODEL}`.
Primary/calibration/annual/measured validation remain OPEN; signoffs 0/31.'''
    handoff=f'Next actionable task: {next_task}\nStop after this coherent executed deliverable and clear handoff.'
    for rel in ['MASTER_STAGEBOARD_v75.md','MASTER_STAGEBOARD_stateflow_v75.md']:
        (ROOT/rel).write_text('# Executed Stateflow reporting provenance repair v75\n\n'+summary+'\n\n'+handoff+'\n',encoding='utf-8')
    hp=q['aggregates']['HP_only'];changed=q['aggregates']['changed_source_actual']
    result='''# Executed saved-Stateflow reporting provenance repair v75

'''+summary+f'''

The saved chart now retains the held duration, source heat-capacity rate and
enable commands in columns 73:75. Its schema marker is 75. The additive reporter
binds canonical schedule operands to those fields and reconstructs segment,
interval and cumulative energy records and the first-law residual. Previous
models, reporting APIs, acceptance evidence and data remain unchanged.

Executed synthetic HP-only control: original source input produces HP heat
{hp['hp_heat']} MWh and compressor work {hp['compressor_work']} MWh.
Actually re-executing source capacity zero produces HP heat
{changed['hp_heat']} MWh and compressor work {changed['compressor_work']} MWh.
Legacy reporting nevertheless accepts the original trace labelled with the
zero-source schedule; v75 rejects that mismatch. This is a reporting defect,
not a newly discovered physical-controller energy violation.

The seventeen single-fault controls cover service/source/work/auxiliary/unmet/
backup cumulative energies, reversed hull, zero/fractional segment counts,
mode/event/origin/residual headers, source/HP-enable/charge-enable misassociation,
and a noncanonical adapter input. Actual MATLAB rejection identifiers and the
legacy summaries remain in original/reopened MAT, JSON and binary records.
Independent closed equations check actual accepted trajectories at 120/160
digits, independently detect each introduced inconsistency, and verify all
reported energies. Separate synthetic reviewer self-checks are not execution
counts. Saved archive QA binds the embedded kernel to its source.

Retained development failures: the restricted MATLAB startup failed before
execution; the first build succeeded but the harness failed because the new
package validator call lacked `dchr.`. The reporter was corrected and a fresh
result directory used. No thermal kernel or saved model was changed to repair
that call. Initial logs and source snapshots remain. Stateflow license test and
sfroot chart observation are recorded; an empty `ver('stateflow')` result is not
turned into an installed-version claim.

Limits:

'''+''.join('- '+s+'\n' for s in limitations)+'\n'+handoff+'\n'
    (ROOT/'audit/Reporting_provenance_results_v75.md').write_text(result,encoding='utf-8')
    progress=f'''## {utc} — v75 actual Stateflow/reporting provenance repair

Read latest STATUS/MASTER_STAGEBOARD, Stateflow acceptance, frontier, progress,
v73r2 builder/kernel and v74 adapter/reporter/harness before changes. Immediate
Stateflow work took priority over the next research handoff because code review
identified unbound reporting inputs and unverified cumulative header copying.
All work stayed in this project; no Jarvice, unrelated files, settings, tasks,
runner, secrets or external publication touched.

{summary}

Files added: versioned v75 kernel and builder; actual saved v75 SLX; strict v75
reporter and validator; actual saved-model/parity/corruption harness; prepare,
batch, independent reviewer and closure tools; derivation/results and STATUS/
stageboard twins. Prior models/code/data are hash-preserved. Shared ledgers are
appended byte-preservingly. Timestamped MATLAB logs, original/reopened MAT and
binary exports, precision QA traces and artifact/source seals are retained.
Restricted startup and initial package-call failure logs are preserved.

Limitations: synthetic macro analytic implementation and consistency gates,
same-agent algorithmic QA; no annual/calibration/physical validation, primary
replication, independent personnel or generated-code acceptance. Coordinated
record forgery is outside the reporting gate; independent trajectory QA remains
required. Primary signoffs 0/31.

{handoff}'''
    append('automation/engineering_progress.md',progress)
    append('automation/STATEFLOW_ACCEPTANCE.md','## Reporting provenance repair acceptance — '+utc+' / v75\n\n'+summary+'\n\n'+handoff)
    append('audit/research_frontier_2026_10_08.md','## Saved-Stateflow reporting provenance repair — '+utc+' / v75\n\n'+summary+'\n\n'+handoff)
    records=[]
    for rel in FILES+REVIEWERS+[MODEL,'audit/close_reporting_provenance_v75.py','audit/Reporting_provenance_derivation_v75.md','audit/Reporting_provenance_results_v75.md']:
        p=ROOT/rel;dst=folder/'final_snapshot'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst);records.append(dict(path=rel,sha256=sha(p)))
    dump(folder/'final_source_hashes.json',records)
    # Immutable evidence seal excludes generated cache/codegen implementation
    # details but includes every numeric result, receipt, source and checkpoint.
    evidence=[p for p in folder.rglob('*') if p.is_file() and 'cache' not in p.relative_to(folder).parts and 'codegen' not in p.relative_to(folder).parts]
    release=dict(version='0.75',timestamp_utc=utc,records=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in evidence],
                 checkpoints=[dict(path=rel,sha256=sha(ROOT/rel)) for rel in ['STATUS_v75.json','STATUS_stateflow_v75.json','MASTER_STAGEBOARD_v75.md','MASTER_STAGEBOARD_stateflow_v75.md']],
                 ledgers=[dict(path=rel,sha256=sha(ROOT/rel)) for rel in ['automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md','audit/research_frontier_2026_10_08.md']])
    dump(folder/'release_manifest_v75.json',release)
    checks=[]
    for entry in release['records']+release['checkpoints']+release['ledgers']:checks.append(dict(path=entry['path'],passed=sha(ROOT/entry['path'])==entry['sha256']))
    for entry in json.loads((folder/'preservation.json').read_text()):checks.append(dict(path=entry['path'],passed=sha(ROOT/entry['path'])==entry['sha256']))
    for entry in json.loads((folder/'ledger_prefixes.json').read_text()):checks.append(dict(path=entry['path']+'_prior_prefix',passed=hashlib.sha256((ROOT/entry['path']).read_bytes()[:entry['size']]).hexdigest()==entry['sha256']))
    checks.append(dict(path='STATUS_twins',passed=(ROOT/'STATUS_v75.json').read_bytes()==(ROOT/'STATUS_stateflow_v75.json').read_bytes()))
    checks.append(dict(path='stageboard_twins',passed=(ROOT/'MASTER_STAGEBOARD_v75.md').read_bytes()==(ROOT/'MASTER_STAGEBOARD_stateflow_v75.md').read_bytes()))
    summary=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks))
    dump(folder/'release_verification_v75.json',dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),checks=checks,summary=summary))
    dump(folder/'release_verification_v75.log',summary)
    assert summary['failed']==0
    print(json.dumps(dict(status='STATUS_v75.json',matlab=r['summary'],independent=q['summary'],release=summary,intervals=intervals,segments=segments,events=events)))
if __name__=='__main__':main()
