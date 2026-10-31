"""A62: immutable simulation export with signed pool loss and discrete energy.

Consumes A60 + original source, validated by A61. Does not modify upstream
files or infer physical measurement. Writes only a new destination directory.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import os
import shutil
import sys
import tempfile
from pathlib import Path

A61_DIR = Path(__file__).resolve().parent.parent / "AUTONOMOUS_RUN_20261027_1400_A61_POOL_DISCRETE_CLOSURE"
sys.path.insert(0, str(A61_DIR))
from a61_pool_discrete_closure import (audit, records, number, sha, SOURCE,
                                        C_POOL_J_PER_K, INITIAL_T_C, STEP_S)

ADDED = ("Q_pool_loss_W", "Q_pool_net_W", "E_pool_input_cum_J",
         "E_pool_signed_loss_cum_J", "E_pool_stored_cum_J", "state_residual_W")


def export(raw: Path, a60_dir: Path, destination: Path) -> dict:
    raw, a60_dir, destination = Path(raw), Path(a60_dir), Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError("DESTINATION_EXISTS")
    if not destination.parent.is_dir():
        raise ValueError("DESTINATION_PARENT_MISSING")
    # A61 audits both raw and A60 hashes, source kind, mapping, timing and balance.
    proof = audit(raw, a60_dir)
    schema = proof["source_schema"]
    qkey, lkey = SOURCE[schema]
    raw_rows = records(raw, ("cas_h", "T_pool_C", qkey, lkey))
    derived_path = a60_dir / "analysis_timeseries.csv"
    with derived_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, strict=True)
        columns = reader.fieldnames or []
        if len(columns) != len(set(columns)) or any(k in columns for k in ADDED):
            raise ValueError("INVALID_A60_COLUMNS")
        derived_rows = list(reader)
    if len(raw_rows) != len(derived_rows):
        raise ValueError("ROW_COUNT_MISMATCH")
    temp = Path(tempfile.mkdtemp(prefix=".a62-staging-", dir=destination.parent))
    try:
        out = temp / "analysis_with_signed_losses.csv"
        input_J = loss_J = 0.0
        prev_T = INITIAL_T_C
        with out.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns + list(ADDED), lineterminator="\n")
            writer.writeheader()
            for original, derived in zip(raw_rows, derived_rows):
                q = number(original, qkey)
                loss = number(original, lkey)
                T = number(original, "T_pool_C")
                net = q - loss
                residual = C_POOL_J_PER_K * (T - prev_T) / STEP_S - net
                input_J += q * STEP_S
                loss_J += loss * STEP_S
                stored_J = C_POOL_J_PER_K * (T - INITIAL_T_C)
                row = dict(derived)
                row.update({k: format(v, ".17g") for k, v in zip(ADDED,
                    (loss, net, input_J, loss_J, stored_J, residual))})
                writer.writerow(row)
                prev_T = T
        meta = {
            "schema_version": "a62.1", "source_kind": "derived_simulation",
            "physical_release": False, "calibration_ready": False,
            "source_schema": schema, "records": len(raw_rows),
            "step_seconds": STEP_S, "initial_T_C": INITIAL_T_C,
            "pool_heat_capacity_J_per_K": C_POOL_J_PER_K,
            "a60_summary_sha256": sha(a60_dir / "summary.json"),
            "a60_analysis_sha256": sha(derived_path),
            "original_csv_sha256": sha(raw),
            "analysis_with_signed_losses_sha256": sha(out),
            "a61_validation": proof,
            "warning": "D_SYNTHETIC: signed loss can be negative; 168h of 672 discrete state updates is distinct from A60 timestamp span 167.75h.",
        }
        (temp / "summary.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                                            encoding="utf-8")
        os.rename(temp, destination)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    return meta


def main():
    p = argparse.ArgumentParser()
    p.add_argument("original_source_csv", type=Path)
    p.add_argument("a60_derived_directory", type=Path)
    p.add_argument("new_destination", type=Path)
    args = p.parse_args()
    m = export(args.original_source_csv, args.a60_derived_directory, args.new_destination)
    print(json.dumps({"schema": m["source_schema"], "rows": m["records"],
                      "negative_loss_rows": m["a61_validation"]["negative_loss_samples"],
                      "source_kind": m["source_kind"], "physical_release": m["physical_release"]}))


if __name__ == "__main__":
    main()
