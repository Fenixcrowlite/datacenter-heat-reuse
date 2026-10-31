"""A60 independent numeric QA against source CSV and across v08/v09 outputs.

Uses Decimal arithmetic and an independent field mapping, not A60 exporter code.
The tolerances certify software agreement ONLY, not physical accuracy.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 42

FIELDS = ("time_s", "T_pool_C", "Q_DC_W", "Q_reject_W",
          "Q_pool_W", "Q_DH_W", "P_HP_W", "E_TES_J")
RAW_MAP = {
    "scada_v08": ("cas_h", "T_pool_C", "Q_DC_eff_W", "Q_reject_physical_W",
                  "Q_pool_phys_W", "Q_DH_W", "P_HP_W", "E_TES_J"),
    "scada_v09_matlab": ("cas_h", "T_pool_C", "Q_DC_W", "Q_reject_W",
                        "Q_pool_W", "Q_DH_W", "P_HP_W", "E_TES_J"),
}
LIMITS = {"time_s": 0, "T_pool_C": 1e-6, "Q_DC_W": .05,
          "Q_reject_W": .05, "Q_pool_W": .05, "Q_DH_W": .05,
          "P_HP_W": .05, "E_TES_J": 50.0}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream, strict=True))


def verify_one(folder: Path) -> tuple[dict, list[dict]]:
    summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    source = Path(summary["source_path"])
    output = folder / "analysis_timeseries.csv"
    if sha(source) != summary["source_csv_sha256"]:
        raise ValueError("SOURCE_HASH_MISMATCH")
    if sha(output) != summary["analysis_csv_sha256"]:
        raise ValueError("OUTPUT_HASH_MISMATCH")
    if (summary["source_kind"] != "derived_simulation" or summary["physical_release"] is not False
            or summary["measurement_calibration_ready"] is not False
            or len(summary["missing_for_A55"]) != 10):
        raise ValueError("PROVENANCE_GATE_FAILED")
    mapping = RAW_MAP[summary["source_schema"]]
    original, normalized = read_csv(source), read_csv(output)
    if len(original) != len(normalized) or len(original) < 3:
        raise ValueError("ROW_COUNT_MISMATCH")
    if list(normalized[0]) != list(FIELDS):
        raise ValueError("NORMALIZED_COLUMNS_CHANGED")
    for orig, norm in zip(original, normalized):
        for field, src in zip(FIELDS, mapping):
            expected = Decimal(orig[src])
            if field == "time_s":
                expected *= 3600
            actual = Decimal(norm[field])
            if abs(actual - expected) > max(Decimal("0.000001"), abs(expected) * Decimal("0.00000000001")):
                raise ValueError("ROW_VALUE_MISMATCH_" + field)
    for field, src in zip(FIELDS[2:7], mapping[2:7]):
        total = Decimal(0)
        for prev, curr in zip(original, original[1:]):
            delta_h = Decimal(curr[mapping[0]]) - Decimal(prev[mapping[0]])
            total += (Decimal(prev[src]) + Decimal(curr[src])) / 2 * delta_h / Decimal(1000000)
        reported = Decimal(str(summary["metrics"]["integrated_MWh"][field]))
        if abs(total - reported) > Decimal("0.0000001"):
            raise ValueError("INTEGRAL_MISMATCH_" + field)
    return summary, normalized


def compare(first: Path, second: Path) -> dict:
    a_meta, a = verify_one(first)
    b_meta, b = verify_one(second)
    if a_meta["source_schema"] != "scada_v08" or b_meta["source_schema"] != "scada_v09_matlab":
        raise ValueError("WRONG_SCHEMA_PAIR")
    if len(a) != len(b):
        raise ValueError("DIFFERENT_SAMPLE_COUNT")
    maxima = {}
    for field in FIELDS:
        maximum = max(abs(float(x[field]) - float(y[field])) for x, y in zip(a, b))
        if maximum > LIMITS[field]:
            raise ValueError("CROSS_VERSION_MISMATCH_" + field)
        maxima[field] = maximum
    return {
        "status": "PASS_SIMULATION_AGREEMENT_NOT_PHYSICAL_VALIDATION",
        "rows_each": len(a),
        "comparisons": len(a) * len(FIELDS),
        "max_abs_differences": maxima,
        "thresholds": LIMITS,
        "independent_integral_checks": 10,
        "physical_release": False,
        "calibration_ready": False,
        "source_sha256": [a_meta["source_csv_sha256"], b_meta["source_csv_sha256"]],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("v08", type=Path)
    parser.add_argument("v09", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError("REPORT_EXISTS")
    result = compare(args.v08, args.v09)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
