"""Independent Decimal audit of original simulation CSVs and A61 JSON.

No imports from the A61 implementation; arithmetic and boundary correction
are recomputed from original source data.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from decimal import Decimal, localcontext
from pathlib import Path

M = Decimal("3600000000")
KWH = Decimal("3600000")
DT = Decimal("900")
C = Decimal("997") * Decimal("500") * Decimal("4182")
SPEC = {"v08": ("Q_pool_phys_W", "Q_pool_loss_W", "scada_v08"),
        "v09": ("Q_pool_W", "Q_pool_losses_W", "scada_v09_matlab")}


def inspect(raw: Path, record: dict, qkey: str, lkey: str) -> dict:
    with raw.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == record["samples"]
    with localcontext() as ctx:
        ctx.prec = 45
        qvals = [Decimal(row[qkey]) for row in rows]
        losses = [Decimal(row[lkey]) for row in rows]
        temps = [Decimal(row["T_pool_C"]) for row in rows]
        times = [Decimal(row["cas_h"]) * Decimal(3600) for row in rows]
        assert all(t == i * DT for i, t in enumerate(times))
        prev = Decimal(16)
        residuals = []
        for t, q, loss in zip(temps, qvals, losses):
            residuals.append(C * (t - prev) / DT - (q - loss))
            prev = t
        Ein = sum(qvals) * DT
        Eloss = sum(losses) * DT
        U = C * (temps[-1] - Decimal(16))
        closure = Ein - Eloss - U
        negative = sum(x < 0 for x in losses)
        boundary = (qvals[0] + qvals[-1]) * DT / (Decimal(2) * KWH)
        # The trapezoid covers N-1 intervals. Discrete forward-Euler updates cover N.
        assert abs(closure) < Decimal("1")
        assert max(abs(x) for x in residuals) < Decimal("0.001")
        assert negative == record["negative_loss_samples"]
        assert abs(Ein / M - Decimal(str(record["E_pool_input_discrete_MWh"]))) < Decimal("1e-8")
        assert abs(Eloss / M - Decimal(str(record["E_pool_signed_losses_MWh"]))) < Decimal("1e-8")
        assert abs(U / M - Decimal(str(record["E_pool_stored_MWh"]))) < Decimal("1e-8")
        assert abs(boundary + Decimal(str(record["A60_trapezoid_minus_discrete_kWh"]))) < Decimal("1e-6")
        return {"rows": len(rows), "decimal_max_abs_residual_W": str(max(abs(x) for x in residuals)),
                "decimal_closure_J": str(closure), "negative_loss_rows": negative,
                "discrete_input_MWh": str(Ein / M), "signed_loss_MWh": str(Eloss / M),
                "stored_MWh": str(U / M), "a60_missing_boundary_kWh": str(boundary),
                "original_source_sha256": hashlib.sha256(raw.read_bytes()).hexdigest()}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("raw_v08", type=Path)
    p.add_argument("raw_v09", type=Path)
    p.add_argument("a61_report", type=Path)
    p.add_argument("qa_output", type=Path)
    args = p.parse_args()
    if args.qa_output.exists():
        raise ValueError("QA_OUTPUT_EXISTS")
    report = json.loads(args.a61_report.read_text(encoding="utf-8"))
    assert report["physical_release"] is False
    assert report["status"] == "VERIFIED_SYNTHETIC_DISCRETE_CLOSURE"
    qa = {"qa_kind": "independent_decimal_source_recalculation",
          "physical_release": False, "source_kind": "derived_simulation"}
    for key, path in (("v08", args.raw_v08), ("v09", args.raw_v09)):
        q, loss, schema = SPEC[key]
        assert report[key]["source_schema"] == schema
        qa[key] = inspect(path, report[key], q, loss)
        assert qa[key]["original_source_sha256"] == report[key]["source_sha256"]
    assert qa["v08"]["rows"] == qa["v09"]["rows"] == 672
    assert qa["v08"]["negative_loss_rows"] == qa["v09"]["negative_loss_rows"] == 91
    args.qa_output.write_text(json.dumps(qa, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "decimal_rows_checked": 1344,
                      "v08_closure_J": qa["v08"]["decimal_closure_J"],
                      "v09_closure_J": qa["v09"]["decimal_closure_J"],
                      "negative_loss_rows": [91, 91]}))


if __name__ == "__main__":
    main()
