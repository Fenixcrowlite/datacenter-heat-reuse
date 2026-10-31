"""Close the coherent v44 boundary/access audit; additive outputs only."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import csv, hashlib, json

ROOT=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v): p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def main():
    assert not (ROOT/'STATUS_v44.json').exists(), 'Preserve completed checkpoint'
    folder=ROOT/(ROOT/'audit/hp_upstream_current_v44.txt').read_text().strip()
    qa_path=sorted(folder.glob('independent_QA_v44_*.json'))[-1]
    qa=json.loads(qa_path.read_text()); assert qa['actual_failed']==qa['reviewer_selfchecks_failed']==0
    report=json.loads((folder/'boundary_v44.json').read_text()); assert report['failed']==0
    now=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    next_task=("Audit annual reporting boundaries in matlab/+dchr/compute_metrics_v2.m and compute_metrics.m, "
               "using fresh two-interval MATLAB fixtures and independent integrated energy arithmetic. "
               "Check whether mean_cop is a heat-weighted diagnostic or an annual heat/electricity ratio, "
               "and whether finite-backup Unmet_Heat_MW is excluded from delivered reuse. "
               "Map pump/fan electricity and thermal destinations explicitly before an additive reporting repair; "
               "do not invent auxiliary loads or change v42 dispatch. Keep upstream62 calibration blocked until "
               "its primary supplement and equipment-specific coefficient/domain evidence are acquired. "
               "Do not repeat identical failed acquisition attempts without a new accessible route.")
    counts=Counter(x['kind'] for x in qa['checks'])
    status=dict(version='0.44',timestamp_utc=now,inherits='STATUS_v43.json',stateflow_inherits='STATUS_stateflow_v42.json',
        checkpoint='Upstream equipment access and auxiliary thermal-boundary audit',
        result='PASS_SCOPED_BOUNDARY_AUDIT_UPSTREAM_CALIBRATION_BLOCK_OPEN',
        model_version='0.42',new_model=False,model_executed_this_run=False,
        saved_model='matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx',
        model_sha256=sha(ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx'),
        result_directory=folder.relative_to(ROOT).as_posix(),independent_qa=qa_path.relative_to(ROOT).as_posix(),
        synthetic_vectors=report['vector_count'],matlab_version=report['matlab_version'],
        harness_passed=report['passed'],harness_failed=0,matlab_batch_exit_code=0,
        successful_receipts=qa['successful_receipts'],independent_actual_passed=qa['actual_passed'],independent_actual_failed=0,
        independent_breakdown=dict(counts),reviewer_selfchecks_passed=qa['reviewer_selfchecks_passed'],reviewer_selfchecks_failed=0,
        upstream_primary_text_verified=False,upstream_supplement_acquired=False,equipment_coefficients_acquired=False,
        local_primary_verified_locators='source20 p8 Eqs4-7 and upstream supplement citation; p27 references61/62',
        reporting_correction='Same enlarged electrical denominator alone does not imply COPHsystem=EERsystem+1; included auxiliary heat must reach counted hot output.',
        code_defect_repaired=False,full_primary_signoffs=0,total_sources=31,primary_article_replication=False,
        independent_physical_validation='NOT_TESTED',
        limitations=['486 fixtures are synthetic engineering boundary calculations, not manufacturer or measured data.',
          'No new SLX or fresh Stateflow execution this run; six-mode acceptance and runtime QA inherited from v42.',
          'Independent exact Fraction algorithms are executed by same agent, not independent personnel.',
          'Publisher direct web access failed; university record has no attached files; local network attempts WinError10013. Global unavailability is not proved.',
          'Online manufacturer entry led to agreement page; no agreement accepted, application installed or equipment map exported.',
          'Auxiliary heat fraction is a boundary fixture; source20 does not calibrate it. Additional hydraulic/thermal losses are not modeled by this identity.',
          'Initial sandbox MATLAB startup failure retained; authorized local retry and saved-MAT reopen succeeded.'],next=next_task)
    dump(ROOT/'STATUS_v44.json',status)
    evidence=f"{status['result_directory']}; {status['independent_qa']}"
    result=f'''# v44 upstream equipment and auxiliary-boundary results

UTC {now}. PASS scoped boundary audit; upstream calibration blocker OPEN.
Production model remains0.42, SHA256 `{status['model_sha256']}`.
No new SLX, plant/helper change or Stateflow execution is claimed this run.
Existing v42 actual six-mode acceptance and independent QA remain preserved.

MATLAB {report['matlab_version']}: {report['vector_count']} synthetic vectors,
{report['passed']} PASS / 0 FAIL. Saved MAT was reopened and every numeric matrix,
specification and report matched the JSON export. Independent exact Fraction
port/ratio, two-axis, receipt, source-locator, artifact and preservation QA:
{qa['actual_passed']} PASS / 0 FAIL. Reviewer mutation checks4 PASS / 0 FAIL,
counted separately. Check breakdown: {json.dumps(dict(counts),sort_keys=True)}.
The successful batch exit0 log contains no Warning or Error text; initial
sandbox startup failure is retained with exit1 in its own log/receipt.

New derived finding: COPHsystem-EERsystem equals
1-(1-alpha)*Wa/(Wc+Wa), for the stated expanded boundary and no other loss.
Using the same electrical denominator is insufficient to assert a difference1
unless Wa=0 or all auxiliary power becomes counted hot output.
This corrects the v43 report's auxiliary sentence; its compressor-only equations
and executed results are preserved and unchanged. No v42 code defect is claimed.
Same-lift MATLAB groups also show different EER at different absolute temperatures.
This rejects an unsupported information reduction; no reference62 polynomial
equation/order/coefficient is claimed.

Local source20 p8 and p27 were visually inspected again. Its explicit upstream
supplement citation is verified; upstream primary content is not. Retrieved
[university repository record](https://flore.unifi.it/handle/2158/1432822)
has no attached file. Publisher indexed metadata/abstract identify the citation;
direct publisher/DOI opens failed. Exact DOI/title/PII and supplement-oriented
searches found no verified supplementary download link. Manufacturer public
pages identify selector availability and coefficient access routes, but no
equipment-specific map was acquired. Local urllib attempts all failed with
WinError10013; those are local access failures, not observed publisher HTTP
responses. These observations do not prove global/public unavailability.

Required calibration evidence remains: primary supplement identity/version,
both refrigerant-temperature axes, fit equations/coefficients and units, product/
refrigerant, superheat/subcooling, speed/rating convention, admissible envelope,
fit errors and validation data, plus auxiliary electrical/thermal destinations.
Full signoffs0/31; no physical validation or article replication.
Derivation and boundary contract: audit/HP_upstream_boundary_derivation_v44.md.
Access records: result-directory acquisition.json and source_observations_v44.json.
Evidence: {evidence}.

Next actionable task: {next_task}
Stop after this coherent task and handoff.
'''
    (ROOT/'audit/HP_upstream_boundary_results_v44.md').write_text(result,encoding='utf-8')
    (ROOT/'MASTER_STAGEBOARD_v44.md').write_text(f'''# v44 equipment/boundary checkpoint

{now}. PASS_SCOPED_BOUNDARY_AUDIT; upstream calibration blocker OPEN.
Saved model0.42 preserved; no new Stateflow execution or production change.
486 synthetic MATLAB vectors:2648/0. Independent evidence:7228/0;
separate reviewer mutations:4/0. Two-temperature information and auxiliary
thermal destination requirements derived and tested. Reference62 primary
paper/supplement and source20 equipment coefficients/domain remain unverified.
Full source signoffs0/31; physical validation/article replication untested.

Evidence: STATUS_v44.json; audit/HP_upstream_boundary_derivation_v44.md;
audit/HP_upstream_boundary_results_v44.md; {evidence}.

Next actionable task: {next_task}
Run complete; stop with this handoff.
''',encoding='utf-8')
    with (ROOT/'audit/literature_traceability_v43.csv').open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
    for row in rows:
        if row['id']=='20':
            row['blockers']+=' | v44: reference62 identity/citation verified; university record no file; full text/supplement/coefficients/domain NOT VERIFIED; local WinError10013 separate from web failure. Auxiliary boundary correction derived, not equipment calibration.'
    with (ROOT/'audit/literature_traceability_v44.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    progress=f'''\n\n## {now} — v44 upstream equipment and auxiliary-boundary audit

Read acceptance, latest STATUS/stageboards, research frontier, progress and
production HP/Stateflow code before changes. Actual versioned Stateflow v42
already meets scoped execution/QA acceptance. Followed primary-equipment handoff.
Visually rechecked local source20 p8/p27; searched upstream62 DOI/title/PII and
supplement, inspected university and manufacturer public pages, retained local
network access receipts. Upstream primary/supplement calibration remains blocked.

Meaningful deliverable: independently derived and tested the auxiliary thermal
destination correction and two-axis information requirement. Same electrical
denominator alone does not imply COPHsystem=EERsystem+1. No plant/model correction
or newly accepted calibration is claimed; v43 historical evidence preserved.

Pass/fail: MATLAB R2026a Update5 {report['passed']} PASS / 0 FAIL on486 synthetic
vectors; batch plus saved-MAT reopen exit0. Independent exact Fraction/port,
two-axis/MAT/receipt/artifact/preservation evidence {qa['actual_passed']} PASS / 0 FAIL;
separate reviewer mutation checks4/0. {counts['preservation']} prior artifacts retain
bytes/hashes. Initial sandbox MATLAB startup exit1 and five local network
WinError10013 attempts retained in timestamped logs/receipts. Web route supplied
scoped repository/manufacturer text; no upstream equation or coefficient invented.

Files created: audit/prepare_hp_upstream_v44.py, verify_hp_boundary_v44.py,
finalize_hp_upstream_v44.py, run_hp_boundary_v44.ps1, derivation/results,
literature_traceability_v44.csv, STATUS_v44.json and MASTER_STAGEBOARD_v44.md;
matlab/simulink/run_hp_boundary_v44.m and export_hp_boundary_v44.m; timestamped
results/spec/acquisition/source observations/snapshots/MAT/JSON/QA and logs/receipts.
Only progress and acceptance ledgers appended. Production SLX/helpers untouched.

Limitations: synthetic boundaries, unknown auxiliary heat fractions/losses,
same-agent independent algorithms, no new Stateflow execution, no measured
validation/article replication or upstream-specific calibration; full signoffs0/31.
No Jarvice/unrelated files, settings, scheduled tasks, runner, secrets or external
publication touched.

Next actionable task: {next_task}
Evidence: {evidence}. Stop after this coherent task and clear handoff.
'''
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:f.write(progress)
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
        f.write(f'''\n\n## Equipment/boundary research handoff — {now} / checkpoint v44

Accepted actual model remains0.42; no new SLX or Stateflow execution this run.
486 synthetic boundary vectors, MATLAB2648/0, independent evidence7228/0 and
reviewer mutations4/0. Auxiliary thermal-boundary correction documented;
upstream62 primary/supplement/equipment map calibration OPEN, full signoffs0/31.
STATUS_v44.json and audit/HP_upstream_boundary_results_v44.md are authoritative.
Next: annual COP/delivered-reuse/auxiliary reporting audit; preserve v42 dispatch.
''')
    files=set()
    for pattern in ['audit/*v44*','matlab/simulink/*v44.m','automation/logs/*v44*','STATUS_v44.json','MASTER_STAGEBOARD_v44.md']:
        files.update(p for p in ROOT.glob(pattern) if p.is_file())
    files.update(p for p in folder.rglob('*') if p.is_file())
    # Finalizer log is still open; seal independently after this process exits.
    files={p for p in files if not p.name.startswith('hp_finalize_v44_')}
    entries=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)]
    manifest=ROOT/'audit'/f'HP_upstream_manifest_v44_{stamp}.json'
    dump(manifest,dict(version='0.44',timestamp_utc=now,excludes='Mutable ledgers, this manifest and still-writing finalizer log',files=entries))
    print(f'FINALIZED=STATUS_v44.json; MANIFEST={manifest.relative_to(ROOT)}; FILES={len(entries)}')
if __name__=='__main__': main()
