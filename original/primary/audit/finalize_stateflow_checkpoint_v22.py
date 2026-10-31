"""Package a passed actual Stateflow gate and independent QA; no numerical fabrication."""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def write(path, data):
    with path.open("x", encoding="utf-8") as f:
        json.dump(data, f, indent=2, allow_nan=False)
        f.write("\n")

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_dir",type=Path)
    args=parser.parse_args()
    result=args.result_dir.resolve()
    if not result.is_relative_to(ROOT / "results"):
        raise ValueError("Result directory must be inside project results")
    summary=read(result/"acceptance_summary_v22.json")
    qa=read(result/"stateflow_independent_qa_v22.json")
    gate=qa["trace_qa"]
    assert summary["failed"] == 0 and summary["checks"] == summary["passed"]
    assert summary["simulink_executed"] and summary["stateflow_executed"]
    assert summary["modes_observed"] == list(range(6))
    assert gate["failed"] == 0
    assert qa["trace_sha256"] == digest(result/"stateflow_trace_v22.csv")
    assert qa["verifier_sha256"] == digest(ROOT/"audit/verify_stateflow_trace_v22.py")
    assert qa["vectors_sha256"] == digest(ROOT/"audit/stateflow_qa_vectors_v22.csv")
    archive_path=sorted((ROOT/"audit").glob("stateflow_archive_review_v22_*.json"))[-1]
    archive=read(archive_path)
    assert archive["failed"] == 0 and archive["passed"] == archive["total"]
    assert archive["model_sha256"] == digest(ROOT/"matlab/simulink/DCHR_Dispatch_Stateflow_v22.slx")
    structure_paths=sorted((ROOT/"results").glob("stateflow_v22_*/stateflow_independent_structure_v22_*.json"))
    structure=read(structure_paths[-1])
    assert structure["failed"] == 0 and structure["checks"] == structure["passed"]
    assert structure["model_sha256"] == archive["model_sha256"]
    assert structure["verifier_sha256"] == digest(ROOT/"audit/verify_stateflow_structure_v22.py")
    with (result/"stateflow_assertions_v22.csv").open(newline="",encoding="utf-8-sig") as f:
        checks=list(csv.DictReader(f))
    assert len(checks) == summary["checks"] and all(r["passed"] in ("1","true") for r in checks)
    now=datetime.now(timezone.utc)
    stamp=now.strftime("%Y%m%dT%H%M%S_%fZ")
    rel=str(result.relative_to(ROOT)).replace("\\","/")
    next_task=("Audit a primary-text TES standing-loss model and derive an exact/exponential "
               "reference with timestep convergence before extending Stateflow; preserve v22's "
               "declared loss-first linear-retention baseline. Faults/hysteresis remain later control work.")
    limitations=["Normal-mode MATLAB HP adapter; standalone generated-code deployment not tested.",
        "Loss-first one-node TES with linear standing retention; time-partition dependence remains.",
        "No hysteresis, minimum dwell, equipment faults, compressor cycling/ramping or sensor model.",
        "Reservoir temperature proxies; no calibrated equipment, hydraulic/network/auxiliary or fuel model.",
        "Stateflow emits nonfatal formal-parameter shadow warnings; local function scopes are intentional.",
        "No new primary-source equation verification, paper replication, annual model or measured-system validation."]
    status=dict(version="0.22",inherits="STATUS_v21.json",checkpoint="Executable six-mode Stateflow dispatch acceptance",
        timestamp_utc=now.isoformat(),stateflow_acceptance="PASS",matlab_batch_exit_code=0,
        matlab_version=summary["matlab_version"],scenarios=summary["scenarios"],intervals=summary["intervals"],
        matlab_checks_passed=summary["passed"],matlab_checks_failed=summary["failed"],
        independent_qa_checks=gate["checks"],independent_qa_failures=gate["failed"],
        independent_archive_checks_passed=archive["passed"],
        independent_structure_checks_passed=structure["passed"],
        modes_observed=summary["modes_observed"],max_abs_balance_residual_MWh=summary["max_abs_balance_residual_MWh"],
        generated_model="matlab/simulink/DCHR_Dispatch_Stateflow_v22.slx",result_directory=rel,
        primary_source_signoffs=0,total_sources=31,primary_paper_replication=False,
        independent_physical_validation="NOT_TESTED",standalone_codegen=False,
        limitations=limitations,next=next_task)
    write(ROOT/"STATUS_stateflow_v22.json",status)
    stage=(f"# v22: executable Stateflow dispatch acceptance\n\n"
        f"PASS: actual MATLAB/Simulink/Stateflow execution across {summary['scenarios']} scenarios, "
        f"{summary['intervals']} intervals, all six modes. MATLAB {summary['passed']}/{summary['checks']} checks; "
        f"independent actual-trace QA {gate['checks']} checks, {gate['failed']} failures. "
        f"Maximum interval first-law residual {summary['max_abs_balance_residual_MWh']:.12g} MWh.\n\n"
        "The chart's entry/during actions allocate actual TES, backup and unmet flows. Guarded initial routing "
        "and state transitions operate on current demand/HP/TES capacity; Unit Delay retains interval TES energy. "
        "Compared all 19 v16 output fields and loss residual with verified MATLAB dispatch; "
        "independent fixed-COP oracle covers 27 additional intervals.\n\n"
        f"Evidence: `{rel}`, `audit/Stateflow_independent_QA_v22.md`, "
        "`audit/Stateflow_equations_review_v22.md`, timestamped logs, and generated versioned `.slx`. "
        "Existing v14 baseline and v21 evidence preserved.\n\n"
        "Engineering-assumption implementation QA only. No paper replication/equipment validation; "
        "0/31 primary signoffs. Host MATLAB HP calls limit this delivery to normal-mode simulation. "
        "Linear TES loss, absent hysteresis/fault/cycling/network physics, and nonfatal Stateflow "
        "local-parameter shadow warnings remain documented.\n\nNext: "+next_task+"\n")
    stage += ("\nReproduce actual simulation from the project root: "
        "`matlab -batch \"addpath('matlab','matlab/simulink'); run_stateflow_acceptance_v22\"`. "
        "The runner requires the existing versioned `.slx` and writes a new timestamped directory. "
        "Run `python audit/verify_stateflow_trace_v22.py --trace <new_directory>/stateflow_trace_v22.csv "
        "--report <new_directory>/stateflow_independent_qa_v22.json` afterward. "
        "The builder refuses to replace an existing versioned model.\n")
    stage += ("\nThis task uses distinct Stateflow checkpoint filenames because a concurrent run "
        "replaced the generic MASTER_STAGEBOARD_v22.md with a Stenberg research checkpoint. "
        "Both deliverables are preserved; the Stateflow result is recorded here.\n")
    with (ROOT/"MASTER_STAGEBOARD_stateflow_v22.md").open("x",encoding="utf-8") as stage_file:
        stage_file.write(stage)
    progress=(f"\n\n## {now.isoformat()} — v22 executable Stateflow acceptance\n\n"
        "Read latest STATUS/stageboard, research frontier, acceptance contract and v14/v16-v19 code before edits. "
        "Created a new versioned six-state model, guarded startup/transitions, state-driven flow allocation, "
        "TES feedback and verified-v14 HP adapter. Independent reviewer derived first laws and identified "
        "adapter demand/boiler/backend domain defects; corrected and added runtime rejection checks. "
        "Independent QA created a closed-form COP oracle without importing production dispatch.\n\n"
        f"Pass/fail: MATLAB {summary['passed']}/{summary['checks']} PASS over {summary['intervals']} intervals/"
        f"{summary['scenarios']} scenarios; independent actual trace {gate['checks']} checks PASS,0 failures; "
        f"all six modes; max balance residual {summary['max_abs_balance_residual_MWh']:.12g} MWh. "
        "Python oracle self-test also checked 500 seeded randomized cases and rejected four corruption classes. "
        "Initial sandbox MATLAB startup FAIL (filesystem inconsistency), authorized local API retry PASS; "
        "initial builder FAIL (ZOH input default extrapolation), fixed with holding-final-value policy; "
        "QA mutation initially found fractional mode truncation, corrected. All failure evidence retained. "
        "MATLAB reports nonfatal local formal-argument shadow warnings.\n\n"
        "Files created: matlab/simulink/{build_dispatch_stateflow_v22.m,DCHR_Dispatch_Stateflow_v22.slx,"
        "dchr_stateflow_hp_v22.m,stateflow_choose_mode_v22.m,stateflow_allocate_v22.m,run_stateflow_acceptance_v22.m}; "
        "audit independent oracle/vectors/reports, archive-inspection evidence and finalizer; STATUS_stateflow_v22.json; "
        f"MASTER_STAGEBOARD_stateflow_v22.md; timestamped logs and `{rel}` traces, assertions, structure, SimulationOutput MATs "
        "and summaries. This ledger appended. Exact file paths/hashes are in the v22 evidence manifest.\n\n"
        "Remaining limits: "+" ".join(limitations)+"\n\n"
        "Next actionable task: "+next_task+"\n\n"
        "Packaging correction: initial manifest integrity failed for the still-open finalizer receipt log "
        "and the generic v22 stageboard overwritten by a concurrent Stenberg audit. Initial evidence and "
        "failure report retained. Distinct Stateflow checkpoint filenames avoid that collision; active "
        "finalization receipt logs and the intentionally mutable progress ledger are excluded from immutable "
        "file-hash checks. Numerical/model/QA artifacts were unchanged.\n\n"
        "Run stops at this coherent acceptance and handoff. No scheduler, runner, settings, Jarvice, "
        "unrelated projects or external publication were touched.\n")
    with (ROOT/"automation/engineering_progress.md").open("a",encoding="utf-8") as f:
        f.write(progress)
    paths=[ROOT/"STATUS_stateflow_v22.json",ROOT/"MASTER_STAGEBOARD_stateflow_v22.md",
        ROOT/"audit/finalize_stateflow_checkpoint_v22.py"]
    paths += sorted((ROOT/"matlab/simulink").glob("*v22.*"))
    paths += sorted(p for p in (ROOT/"audit").glob("*v22*") if 'stateflow' in p.name.lower())
    paths += sorted(p for p in (ROOT/"automation/logs").glob("*v22*")
                    if 'stateflow' in p.name.lower() and not p.name.startswith('stateflow_finalize_v22'))
    paths += sorted(p for directory in (ROOT/"results").glob("stateflow_v22_*")
                    for p in directory.iterdir() if p.is_file())
    manifest=dict(version="0.22",timestamp_utc=now.isoformat(),stateflow_acceptance="PASS",
        scope="Actual executable-model implementation verification, not independent physical validation",
        mutable_ledger="automation/engineering_progress.md",
        mutable_ledger_sha256_at_packaging=digest(ROOT/"automation/engineering_progress.md"),
        excluded_active_receipts="automation/logs/stateflow_finalize_v22*.log",
        supersedes="audit/Stateflow_evidence_manifest_v22_20261009T030008_883989Z.json",
        preserved_baseline_sha256=digest(ROOT/"matlab/simulink/DCHR_Dispatch_Stateflow_v14.slx"),
        files=[dict(path=str(p.relative_to(ROOT)).replace("\\","/"),sha256=digest(p),bytes=p.stat().st_size)
               for p in sorted(set(paths)) if p.is_file()])
    manifest_path=ROOT/"audit"/f"Stateflow_evidence_manifest_v22_{stamp}.json"
    write(manifest_path,manifest)
    print(json.dumps(dict(status="PASS",manifest=str(manifest_path.relative_to(ROOT)),
                         matlab_checks=summary["passed"],independent_qa_checks=gate["checks"]),indent=2))

if __name__ == "__main__":
    main()
