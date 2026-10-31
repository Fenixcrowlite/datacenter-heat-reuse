"""Package the bounded IASE audit; not another physics/author-runtime test."""
from datetime import datetime, timezone
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = "audit/Sintong_IASE_tests_v15_20261008T220043_794544Z.json"
PRIMARY = "audit/Sintong_IASE_primary_evidence_v15_20261008T220047_157053Z.json"
PARK = "audit/Park_IASE_evidence_v15_20261008T220137Z.json"
PARK_CHECKS = "automation/logs/Park_provenance_checks_v15_20261008T220228_867073Z.log"
PREVIOUS_MANIFEST = "audit/heat_pump_evidence_manifest_v14_20261008T215520_147043Z.json"
REPORT = "audit/Sintong_IASE_domain_audit_v15.md"
PROGRESS = "automation/engineering_progress.md"


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def sha(relative):
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def write_new(relative, content):
    with (ROOT / relative).open("x", encoding="utf-8") as stream:
        stream.write(content)


def main():
    now = datetime.now(timezone.utc)
    stamp, iso = now.strftime("%Y%m%dT%H%M%S_%fZ"), now.isoformat()
    py, source, park, park_checks = map(read, (TESTS, PRIMARY, PARK, PARK_CHECKS))
    assert py["passed"] == py["tests_run"] == 15
    assert py["failed"] == py["errors"] == 0
    assert not any(py[k] for k in ("paper_replication", "matlab_executed", "simulink_executed", "stateflow_executed"))
    for path, expected in py["source_sha256"].items():
        assert sha(path) == expected, path
    assert sha(source["source"]) == source["source_sha256"]
    for page in source["pages"]:
        assert sha(page["text"]) == page["text_sha256"]
        assert sha(page["render"]) == page["render_sha256"]
    # Earlier p30/p31 visual reviews inspected byte-identical full-page renders.
    for page in (30,31):
        record = next(p for p in source["pages"] if p["pdf_page_1based"] == page)
        assert sha(f"audit/Sintong_p{page}_IASE_visual_v15.png") == record["render_sha256"]
    assert not park["classification"]["full_source_signoff"]
    assert park["classification"]["ham_full_text"] == "NOT_VERIFIED"
    assert not park["park_publisher"]["local_pdf_acquired"]
    assert park_checks["passed"] == 8 and park_checks["failed"] == 0
    assert sha(PARK) == park_checks["evidence_sha256"]
    assert sha(park["memo"]) == park_checks["memo_sha256"]
    with (ROOT / py["comparison"]).open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == py["comparison_vectors"] == 66
    previous = read(PREVIOUS_MANIFEST)
    checked_previous = []
    for path, record in previous["files"].items():
        if path == PROGRESS:
            continue  # the append-only ledger is intentionally mutable
        assert sha(path) == record["sha256"], f"Prior v14 evidence changed: {path}"
        checked_previous.append(path)
    assert not (ROOT / "STATUS_v15.json").exists()
    assert not (ROOT / "MASTER_STAGEBOARD_v15.md").exists()
    next_task = (
        "Integrate heat_pump_step_v14 into a separate finite-boiler/TES/unmet-demand dispatch; "
        "review TES parameter/time-step validation first, then compare a deterministic multi-step trace "
        "with independent Python before a new Simulink model. Keep unresolved IASE algebra out of annual dispatch."
    )
    next_research = (
        "Visually verify Park p9 and acquire upstream Ham et al. (2015) primary model/author code "
        "to resolve the Park/Sintong coefficient normalization and unequal-flow domain."
    )
    manifest_path = f"audit/IASE_evidence_manifest_v15_{stamp}.json"
    review_path = f"audit/Sintong_IASE_visual_review_v15_{stamp}.json"
    review = {"timestamp_utc":iso, "kind":"primary_thesis_visual_review_record",
              "inspected_pdf_pages":[23,30,31,70], "original_pdf_sha256":source["source_sha256"],
              "page_render_sha256":{str(p["pdf_page_1based"]):p["render_sha256"] for p in source["pages"]},
              "eq15_16_locator":"printed/PDF p30, zero-based index29",
              "eq15_parentheses_interpretation":"UNRESOLVED_AUTHOR_IMPLEMENTATION",
              "park_equation_visual_verified":False,
              "independent_math_and_code_review":"NO_MATERIAL_ISSUE_WITHIN_DECLARED_DOMAIN",
              "review_is_equipment_validation":False}
    write_new(review_path,json.dumps(review,indent=2)+"\n")
    status = {
        "project":"DataCenter_Heat_Reuse", "version":"0.15", "updated_utc":iso,
        "kind":"additive_research_and_mathematical_domain_checkpoint",
        "inherits_status":"STATUS_v14.json", "inherits_stageboard":"MASTER_STAGEBOARD_v14.md",
        "milestone":"M1_PARTIAL_PRIMARY_PROVENANCE_M2_IASE_ENDPOINT_DOMAIN_GATE",
        "delivered":"Sintong Eq15-16 both-stream domain audit, independent diagnostic/reference and partial Park provenance",
        "evidence":[REPORT, "audit/Sintong_IASE_independent_review_v15.md", TESTS, py["comparison"],
                    PRIMARY, review_path, "audit/Park_IASE_provenance_v15.md", PARK, PARK_CHECKS,manifest_path],
        "tests":{"independent_python":{"passed":15,"failed":0,"errors":0,
                                       "exact_flow_function_points":1342,"exact_alternative_points":671,
                                       "random_reference_cases":2000,"random_diagnostic_cases":1000,
                                       "comparison_rows":66,"seed":15026},
                 "provenance_integrity":{"passed":8,"failed":0,"scientific_validation":False},
                 "matlab_v15":"NOT_EXECUTED_RESEARCH_TASK",
                 "simulink_v15":"NOT_BUILT_OR_EXECUTED",
                 "stateflow_v15":"NOT_BUILT_OR_EXECUTED_AVAILABILITY_NOT_CHECKED",
                 "primary_author_simulation_replication":"NOT_PERFORMED"},
        "findings":[
            {"id":"F15-IASE-01","state":"CONDITIONAL_UNRESTRICTED_FLOW_ADOPTION_DEFECT_CONFIRMED",
             "topic":"Return-only supply criterion can hide outdoor-stream capacity violation",
             "interpretation":"alpha=epsilon*(1+r)/2, equal constant cp passive sensible exchange",
             "required_bound":"0<=alpha<=min(1,r)",
             "counterexample":{"r":0.25,"scenario_epsilon":0.8,"return_in_C":35,"outdoor_in_C":5,
                               "return_out_C":20,"derived_outdoor_out_C":65,"Q_W":15075,"Qmax_W":7537.5},
             "author_annual_result_disproved":False},
            {"id":"F15-PROV-01","state":"PRIMARY_BODY_TEXT_PARTIAL_NORMALIZATION_UNRESOLVED",
             "topic":"Park Eq22 coefficient notation differs from Sintong Eq15; upstream Ham unverified"}],
        "research_status":{"full_primary_signoffs":0,"count_source":"inherited v14; no new full signoff",
                           "sintong_eq15_16":"PRIMARY_TEXT_AND_VISUAL_VERIFIED_AUTHOR_IMPLEMENTATION_UNRESOLVED",
                           "park":"PRIMARY_PDF_BODY_PARSED_TEXT_VERIFIED_VISUAL_PENDING",
                           "ham_upstream":"FULL_TEXT_NOT_VERIFIED",
                           "primary_metadata_or_abstract_only":False,
                           "park_local_original":"NOT_ACQUIRED_WINERROR_10013"},
        "limitations":["Both-outlet bound is conditional on sensible passive positive-flow equal-cp source interpretation",
                       "No validated epsilon curve, geometry/UA, fan work, moist-air, frost or leakage model",
                       "No new calibrated annual result, MATLAB integration or Simulink/Stateflow execution",
                       "Legacy mathematical vulnerabilities remain as recorded in v14 until separate integration"],
        "preservation":{"previous_manifest":PREVIOUS_MANIFEST,
                        "previous_artifact_hashes_unchanged":len(checked_previous),
                        "intentional_existing_edit":"Append automation/engineering_progress.md only"},
        "next":[next_task,next_research],
    }
    write_new("STATUS_v15.json",json.dumps(status,indent=2)+"\n")
    write_new("MASTER_STAGEBOARD_v15.md",f"""# DataCenter Heat Reuse - stageboard v0.15

UTC checkpoint: {iso}. Additive to STATUS_v14.json and MASTER_STAGEBOARD_v14.md.

Completed one bounded research/equation task: visually verified Sintong p30 Eq15-16 and p31 Fig14, derived both-stream endpoint/first-law limits, and traced Park [38] to publisher primary body text. No full source signoff or author-result replication.

The flow-function interpretation requires `0<=epsilon*(1+r)/2<=min(1,r)` under positive-flow passive sensible equal-cp assumptions. New hidden-outdoor counterexample: r=.25, scenario epsilon=.8, return35 C/outdoor5 C gives return20 C but derived outdoor65 C; transfer15075 W exceeds maximum7537.5 W. This is a conditional adoption/domain defect, not proof that the authors executed that point.

- Python15/15 PASS;1342 exact main-interpretation points,671 alternative points;2000 reference plus1000 diagnostic random cases;66-row comparison. Evidence: {TESTS}.
- Park provenance integrity8/8 PASS; these are evidence checks, not physical tests. Publisher primary parsed Eq22-23 read, visual checking pending, upstream Ham unverified. Local acquisition WinError10013; web screenshots cache miss. No local Park original is claimed.
- Independent equation/code review found no material issue within the declared model domain. Prior v14 immutable artifact hashes checked unchanged: {len(checked_previous)}; append-only progress ledger excluded from prior hash check.

M1 remains partial with0 full source signoffs. M2 gains an explicit IASE endpoint domain. M3/v14 annual integration and M4/M5 actual Simulink/Stateflow remain open. No new MATLAB runtime result; Stateflow availability not checked. Existing v07 Eq17/24 work was not repeated.

Next engineering task: {next_task}

Next source task: {next_research}

Report: {REPORT}. Ledger: {PROGRESS}. Immutable evidence hashes: {manifest_path}. Stop after this task and handoff; scheduler/runner/settings and unrelated projects were not modified.
""")
    progress = f"""
## {iso} - v15 Sintong IASE two-stream domain / Park provenance

Completed the v14 next research task after reading status, stageboard, frontier, earlier source corrections and relevant code. Visually checked thesis pages23,30,31,70; established exact Eq15-16 locator p30; derived both-outlet first-law/capacity domain. Created an audit-only Python diagnostic with explicit notation alternatives and a separately defined passive sensible-HX reference. Independent reviewer agreed with the equations and code within their stated domain. Found new conditional adoption defect: scenario r=.25/epsilon=.8 reaches return20 C while implying outdoor65 C from35/5 C inlets, requiring15075 W against7537.5 W maximum.

Pass/fail: Python15/15 PASS,0 failures/errors;1342 exact flow-function points +671 alternate points,2000 random reference energy/endpoint/entropy cases +1000 random source diagnostic cases,seed15026;66 comparison rows. Park evidence integrity8/8 PASS (packaging/provenance checks only). Primary local PDF hash/extraction PASS. Exploratory cp1251 console extraction FAIL, corrected with explicit UTF8. Park local PDF acquisition FAIL WinError10013; screenshots FAIL cache miss; browser fallback unavailable/timed out. Publisher primary body parsed text SUCCESS beyond abstract/metadata. Park visual and upstream Ham full text remain unverified. No paper-result replication, MATLAB/Simulink/Stateflow execution or equipment validation; Stateflow availability not checked.

Files created: {REPORT}; audit/Sintong_IASE_independent_review_v15.md; audit/sintong_iase_domain_v15.py; audit/test_sintong_iase_domain_v15.py; audit/extract_sintong_iase_evidence_v15.py; audit/finalize_checkpoint_v15.py; timestamped thesis extraction/text/renders/visual-review JSON, test JSON/CSV/logs; audit/Park_IASE_provenance_v15.md and timestamped evidence/acquisition JSON/check log; STATUS_v15.json; MASTER_STAGEBOARD_v15.md; {manifest_path}. Existing edit: append this ledger. All prior v14 manifest artifacts except this intentionally mutable ledger passed unchanged-hash checks ({len(checked_previous)} files). Original PDFs, datasets, legacy MATLAB and .slx models preserved. Exploratory p24/p56 renders retained without using them as Eq15-16 evidence; no cleanup.

Logs: {py['log']}; automation/logs/Sintong_IASE_extraction_v15_20261008T220047_157053Z.log; {PARK_CHECKS}; Park transport error in audit/Park_acquisition_v15_20261008T215837_580374Z.json. New checkpoint log records packaging counts/hashes only. Primary/assumption classifications and source links are in the two audit reports.

Remaining limitations: coefficient normalization and parenthesis meaning/author implementation unresolved; unequal-flow source correlation not ready for production adoption. Endpoint admissibility is not finite-UA/geometry validation. No latent heat, fans inside thermal boundary, frost/leakage, calibrated controller or annual effect estimate. Full primary-source signoffs remain0.

Next actionable engineering task: {next_task}

Research handoff: {next_research}

Run stops at this coherent research/math checkpoint. Scheduler, runner, user settings, Jarvice and unrelated files were not modified.
"""
    with (ROOT / PROGRESS).open("a",encoding="utf-8") as stream:
        stream.write(progress)
    log_path = f"automation/logs/checkpoint_v15_{stamp}.log"
    write_new(log_path,f"UTC {iso}\nPackaging consistency PASS\nPython15/15;provenance integrity8/8;comparison66 rows\n"
              f"Prior v14 immutable hashes unchanged:{len(checked_previous)}\n"
              "No MATLAB, Simulink, Stateflow, author simulation or full source signoff\n"
              f"Manifest:{manifest_path}\n")
    files = {"STATUS_v15.json","MASTER_STAGEBOARD_v15.md",PROGRESS,source["source"],log_path}
    files.update(p.relative_to(ROOT).as_posix() for p in (ROOT/"audit").glob("*v15*") if p.is_file())
    files.update(p.relative_to(ROOT).as_posix() for p in (ROOT/"automation/logs").glob("*v15*") if p.is_file())
    manifest = {"timestamp_utc":iso,"kind":"post_gate_immutable_evidence_snapshot",
                "packaging_checks":"PASS","scientific_test_rerun":False,
                "mutable_ledger_snapshot_note":"Progress ledger is append-only; later entries intentionally change its hash",
                "prior_immutable_hashes_checked":len(checked_previous),
                "files":{p:{"bytes":(ROOT/p).stat().st_size,"sha256":sha(p)} for p in sorted(files)}}
    write_new(manifest_path,json.dumps(manifest,indent=2)+"\n")
    print(json.dumps({"status":"STATUS_v15.json","manifest":manifest_path,"log":log_path,
                      "python_passed":15,"provenance_integrity_passed":8,
                      "previous_immutable_files_unchanged":len(checked_previous)}))


if __name__=="__main__":
    main()
