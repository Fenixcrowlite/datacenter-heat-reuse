"""Publish workspace-only v43 evidence/handoff; never overwrite prior versions."""
from pathlib import Path
from datetime import datetime, timezone
import csv, hashlib, json, sys

ROOT=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fresh(path,text):
    assert not path.exists(),f'Preserve existing artifact: {path}'
    path.write_text(text,encoding='utf-8')
def dump(path,data):fresh(path,json.dumps(data,indent=2)+'\n')

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    folder=ROOT/sys.argv[1];qa_path=sorted(folder.glob('independent_QA_v43_*.json'))[-1]
    qa=json.loads(qa_path.read_text());summary=json.loads((folder/'summary_v43.json').read_text())
    assert qa['actual_failed']==qa['synthetic_failed']==summary['harness_failed']==0
    assert qa['counts']['preservation']['failed']==0
    cases=json.loads((folder/'stateflow_cases_v43.json').read_text());source=json.loads((folder/'source_evidence.json').read_text())
    now=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    next_task=('Acquire and audit source20 upstream reference [62] (Rocchetti and Socci, TSEP 2025, 61, 103513; DOI 10.1016/j.tsep.2025.103513) and its performance-correlation supplement, then public CoolSelector [61] equipment data when accessible. Verify exact coefficients, both refrigerant-temperature axes, compressor versus auxiliary power, units and admissible operating range. If no complete map is public, record the specific access/data blocker. Do not calibrate heating h(2) from the article cooling EERII, adopt a lift-only polynomial, or replace the accepted v42 assumptions without new evidence. Design a separate refrigerant-temperature/cooling-efficiency backend only after evidence supports it; preserve v42 and all v43 diagnostics.')
    rows=list(csv.DictReader((ROOT/'audit/literature_traceability_v25.csv').open(encoding='utf-8-sig',newline='')))
    fields=list(rows[0]);newrows=[dict(r) for r in rows]
    target=next(r for r in newrows if r['id']=='20')
    target['review_level']='PARTIAL_PRIMARY_PDF_HP_BOUNDARY_VERIFIED_NOT_SIGNED_OFF'
    target['blockers']+=' | v43: local PDF p8 Eqs4-7 and p10 visually verified; cooling EERII differs from heating Carnot factor, refrigerant vs reservoir boundary mismatch; 324 synthetic vectors and four saved-v42 cases independently checked; upstream61/62/64 and measured maps unverified; full signoff remains NO'
    assert all(a==b for a,b in zip(rows,newrows) if a['id']!='20')
    csvpath=ROOT/'audit/literature_traceability_v43.csv';assert not csvpath.exists()
    with csvpath.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(newrows)
    status=dict(version='0.43',timestamp_utc=now,research_inherits='STATUS_v25.json',stateflow_inherits='STATUS_stateflow_v42.json',
        checkpoint='Primary-text heat-pump efficiency and temperature-boundary audit',
        result='PASS_SCOPED_EQUATION_TRACEABILITY_AUDIT_CALIBRATION_BLOCK_OPEN',model_version='0.42',new_model=False,
        saved_model='matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx',model_sha256=digest(ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx'),
        result_directory=str(folder.relative_to(ROOT)).replace('\\','/'),independent_qa=str(qa_path.relative_to(ROOT)).replace('\\','/'),
        source_id=20,verified_primary_pdf_sha256=source['sha256'],verified_locators='PDF/printed p8 Eqs4-7; p10 VCC2/3 assumption; p23 units; p27 upstream references',
        component_vectors=summary['component_vectors'],component_calls=summary['component_calls'],fresh_saved_model_scenarios=4,
        harness_passed=summary['harness_passed'],harness_failed=0,independent_actual_passed=qa['actual_passed'],independent_actual_failed=0,
        reviewer_selfchecks_passed=qa['synthetic_passed'],reviewer_selfchecks_failed=0,
        preservation_checks_passed=qa['counts']['preservation']['passed'],six_mode_acceptance='Inherited v42; this run focuses on HEAT_RECOVERY and UNMET_DEMAND with new primary-boundary fixtures',
        scientific_block='Article cooling efficiency and refrigerant temperatures do not calibrate accepted heating-factor/reservoir-proxy/part-load assumptions',
        full_primary_signoffs=0,total_sources=31,primary_article_replication=False,independent_physical_validation='NOT_TESTED',
        limitations=['All 324 sweep points and four Stateflow cases are engineering synthetic fixtures, not measured equipment results.',
                    'Relevant local primary PDF text visually verified; newest publisher PDF identity unverified; direct HTML returned429.',
                    'Upstream61/62/64, performance coefficients/maps and hourly datasets remain unverified.',
                    'Independent algorithms in same agent, not independent personnel; normal-mode host analytic segments remain inherited.',
                    'Initial sandbox startup failure and failed harness with eight wrong-column assertions retained; corrected fresh run and separate MAT export both exit0.',
                    'Inherited Stateflow data-shadow warnings remain in logs; no production model/helper code altered.'],next=next_task)
    dump(ROOT/'STATUS_v43.json',status)
    table='| Synthetic saved-v42 case | COP | Heat MW | Compressor MW | Source MW | Unmet MW | Mode |\n|---|---:|---:|---:|---:|---:|---|\n'
    for item in cases:
        tr=item['dispatch'];mode='HEAT_RECOVERY' if tr[0]==1 else 'UNMET_DEMAND'
        table+=f"| {item['id']} | {tr[22]:.9g} | {tr[18]:.12g} | {tr[19]:.12g} | {tr[20]:.12g} | {tr[5]:.12g} | {mode} |\n"
    maxbalance=max(abs(c['dispatch'][12]) for c in cases)
    report=f'''# v43 primary heat-pump boundary results

UTC {now}. PASS scoped equation/traceability audit; scientific calibration blocker OPEN.
Production remains saved Stateflow 0.42. No new SLX or corrected plant acceptance.

Verified existing local primary PDF: source20, DOI10.3390/en19030800,
SHA256 `{source['sha256']}`. Exact locators, definitions, dimensions,
independent conversion and code mapping: `audit/HP_primary_boundary_derivation_v43.md`.
Rendered p8/10/23/27 were visually checked; extracted p1/6/8/9/10/23/27 retained.
Newest publisher PDF identity remains unverified; direct HTML returned429.
Indexed publisher text is corroboration, not the primary verification basis.

MATLAB R2026a Update5 executed 324 synthetic vectors / 972 component calls,
then four new focused scenarios in the actual saved v42 model. Harness:
{summary['harness_passed']} PASS / 0 FAIL. Separate MATLAB batch reopened saved
MAT files and exported every compared numeric matrix/trace. Independent
80-digit Decimal quadratic roots, exact Fraction identities, dimensional checks,
MAT equivalence, receipts, source snapshots and prior-evidence hashes:
{qa['actual_passed']} PASS / 0 FAIL. Separate reviewer self-checks:
{qa['synthetic_passed']} PASS / 0 FAIL.
{qa['counts']['preservation']['passed']} prior sealed/source entries retain their hashes/sizes.
Evidence: `{status['result_directory']}`; QA: `{status['independent_qa']}`.

Direct factor substitution misses heating COP by 1-etaC: observed gaps
{min(qa['same_factor_COP_gap_range']):.6g} to {max(qa['same_factor_COP_gap_range']):.6g}.
Holding converted etaH fixed but substituting external reservoir proxies with
nonzero symmetric pinch increases COP by {min(qa['proxy_COP_increase_range']):.9g}
to {max(qa['proxy_COP_increase_range']):.9g} in these engineering sweep fixtures.
This is a conditional boundary comparison, not a universal equipment error estimate.

Focused fixture: external source35C / sink75C, assumed symmetric pinch5K
giving refrigerant30C / 80C, etaC0.5, source0.5MW, demand0.68MW,
TES at cutoff5MWh, no TES port transfer or boiler, one 1h macro interval.

{table}

The factor conversion alone changes demand-met to about15.065kW unmet.
A lower COP admits more condenser heat for a fixed source budget by drawing
more electricity. The assumed part-load penalty reverses the service result
in this fixture, further demonstrating why energy balance alone cannot calibrate
performance. All four TES endpoints remain5MWh; maximum saved model integrated
first-law residual {maxbalance:.16g}MWh. These are executed synthetic comparisons,
not Varna performance predictions, paper replication or measured validation.

The initial sandbox startup failure and first harness run are retained in
timestamped logs/receipts and the earlier v43 result folder. All four initial
simulations ran, but eight harness checks addressed wrong trace columns; corrected
assertions use first-law column13, HP columns19-21 and COP column23. A new result
directory was used for the successful run. Inherited data-shadow warnings retained.
No production code/model/data was overwritten; no settings/scheduler/agent runner,
Jarvice/unrelated files, secrets or external publication touched.

Independent QA uses distinct algorithms in the same agent, not independent personnel.
Full source signoffs0/31, upstream61/62/64 and actual performance maps remain open.
New additive ledger `audit/literature_traceability_v43.csv` changes only source20's
partial review/blocker text. Read STATUS_v43.json and MASTER_STAGEBOARD_v43.md
alongside inherited STATUS_stateflow_v42.json before the next task.

Next actionable task: {next_task}
'''
    fresh(ROOT/'audit/HP_primary_boundary_results_v43.md',report)
    fresh(ROOT/'MASTER_STAGEBOARD_v43.md',f'''# v43 primary heat-pump traceability checkpoint

{now}. PASS_SCOPED_EQUATION_TRACEABILITY_AUDIT; calibration blocker OPEN.
Actual saved model remains0.42; no new SLX. Four new focused saved-model cases,
324 synthetic vectors/972 HP calls; MATLAB{summary['harness_passed']}/0,
independent actual{qa['actual_passed']}/0, separate reviewer self-checks{qa['synthetic_passed']}/0.
Local source20 p8 Eqs4-7 and p10 verified visually. Cooling EERII cannot be
copied into heating h(2); refrigerant saturation and reservoir-proxy boundaries
differ. Full primary signoffs0/31; physical validation/article replication untested.

Evidence: STATUS_v43.json; audit/HP_primary_boundary_derivation_v43.md;
audit/HP_primary_boundary_results_v43.md; audit/literature_traceability_v43.csv;
{status['independent_qa']}.

Next actionable task: {next_task}
Stop after this coherent task and handoff; do not repeat regression absent a change.
''')
    progress=f'''\n\n## {now} — v43 primary HP efficiency/temperature-boundary audit

Read acceptance, latest research/Stateflow STATUS and MASTER_STAGEBOARD, frontier,
progress and production code first. Accepted v42 delivery already has actual
six-mode execution and independent QA. Resumed its primary-equipment handoff:
verified local source20 p8 Eqs4-7, p10 assumption, p23 units and p27 upstream
locators visually; derived cooling-to-heating efficiency conversion and dimensions.

Deliverable: independent primary/code boundary mapping, 324 engineering vectors,
972 actual MATLAB component calls and four fresh unchanged saved-v42 simulations.
Pass/fail: corrected MATLAB harness{summary['harness_passed']} PASS/0 FAIL; independent
actual equation/trace/MAT/artifact/receipt/preservation QA{qa['actual_passed']} PASS/0 FAIL;
separate reviewer self-checks{qa['synthetic_passed']}/0. Separate simulation and saved-MAT
export batches exit0. Prior {qa['counts']['preservation']['passed']} entries retain hashes/sizes.
Initial sandbox startup error and first wrong-column harness8 FAIL retained; fixed
only additive harness and reran into a fresh folder. Existing Stateflow warnings retained.

Confirmed scientific assumption mismatch: paper EERII is a cooling factor on
refrigerant saturation temperatures; accepted h(2) is a heating factor on reservoir
proxies. Direct factor substitution removes15.065kW unmet in the focused synthetic
fixture; no calibrated performance or corrected-model acceptance is claimed.

Files created: matlab/simulink/run_hp_traceability_v43.m and export_hp_traceability_v43.m;
audit preparation/test launcher/independent verifier/finalizer, primary derivation/results,
new literature_traceability_v43.csv (source20 review only), STATUS_v43.json and
MASTER_STAGEBOARD_v43.md, versioned result directories/source snapshots/MAT/JSON/
page PNGs and timestamped logs/receipts/manifests. Only progress and acceptance
ledgers appended; production model0.42 and HP0.40 preserved.

Limitations: synthetic engineering fixtures; same-agent independent algorithms;
local PDF verified but newest publisher identity unknown and direct HTML429;
upstream61/62/64, measured equipment maps and raw profiles unverified. Full signoffs
remain0/31; no physical validation/article replication. No unrelated/Jarvice files,
settings, tasks, scheduler, agent runner, secrets or external publication touched.

Next actionable task: {next_task}
Evidence: {status['result_directory']}; {status['independent_qa']};
audit/HP_primary_boundary_results_v43.md. Stop after this coherent task and handoff.
'''
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:f.write(progress)
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
        f.write(f'''\n\n## Primary-boundary audit on saved-v42 — {now} / checkpoint v43

No new model. Savedv42 executed four focused primary-assumption comparison cases;
324 vectors/972 HP calls, MATLAB{summary['harness_passed']}/0, independent actual
{qa['actual_passed']}/0 and separate reviewer self-checks{qa['synthetic_passed']}/0.
Local source20 p8Eqs4-7 and p10 verified; cooling/heating-factor and refrigerant/
reservoir-temperature mismatch documented. Scoped equation traceability only;
calibration blocker OPEN, full source signoffs0/31. STATUS_v43.json and
audit/HP_primary_boundary_results_v43.md are authoritative research handoff;
accepted actual model remains0.42. Next: source20 upstream[62]/[61] map/domain audit.
''')
    # Seal all release evidence, including the failed run, excluding local caches.
    paths=set()
    for pattern in ['audit/*v43*','matlab/simulink/*v43.m','automation/logs/*v43*','STATUS_v43.json','MASTER_STAGEBOARD_v43.md']:
        paths.update(p for p in ROOT.glob(pattern) if p.is_file())
    for d in ROOT.glob('results/hp_traceability_v43_*'):
        paths.update(p for p in d.rglob('*') if p.is_file() and 'local_build' not in p.parts)
    entries=[dict(path=str(p.relative_to(ROOT)).replace('\\','/'),bytes=p.stat().st_size,sha256=digest(p)) for p in sorted(paths)]
    manifest=ROOT/'audit'/f'HP_traceability_manifest_v43_{stamp}.json'
    dump(manifest,dict(version='0.43',timestamp_utc=now,excludes='Mutable ledgers, local caches/codegen, this manifest and still-writing finalizer log',files=entries))
    print(f'FINALIZED=STATUS_v43.json; MANIFEST={manifest.relative_to(ROOT)}; FILES={len(entries)}')

if __name__=='__main__': main()
