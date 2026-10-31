"""Independent Decimal check of A62 materialized CSVs against ORIGINAL raw sources."""
import argparse
import csv
import hashlib
import json
from decimal import Decimal, localcontext
from pathlib import Path

C = Decimal("997") * Decimal("500") * Decimal("4182")
DT = Decimal("900")
FIELDS = ("Q_pool_loss_W", "Q_pool_net_W", "E_pool_input_cum_J",
          "E_pool_signed_loss_cum_J", "E_pool_stored_cum_J", "state_residual_W")
SOURCE = {"v08": ("Q_pool_phys_W", "Q_pool_loss_W", "scada_v08"),
          "v09": ("Q_pool_W", "Q_pool_losses_W", "scada_v09_matlab")}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(raw, output, label):
    qkey, losskey, schema = SOURCE[label]
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert summary["schema_version"] == "a62.1"
    assert summary["source_schema"] == schema
    assert summary["source_kind"] == "derived_simulation"
    assert summary["physical_release"] is False
    assert summary["calibration_ready"] is False
    assert sha(raw) == summary["original_csv_sha256"]
    out = output / "analysis_with_signed_losses.csv"
    assert sha(out) == summary["analysis_with_signed_losses_sha256"]
    with raw.open(encoding="utf-8-sig", newline="") as f:
        source_rows = list(csv.DictReader(f))
    with out.open(encoding="utf-8", newline="") as f:
        exported_rows = list(csv.DictReader(f))
    assert len(source_rows) == len(exported_rows) == 672
    checks = 0
    with localcontext() as ctx:
        ctx.prec = 45
        input_J = loss_J = Decimal(0)
        prev_T = Decimal(16)
        max_res = Decimal(0)
        for i, (a, b) in enumerate(zip(source_rows, exported_rows)):
            q, loss = Decimal(a[qkey]), Decimal(a[losskey])
            T = Decimal(a["T_pool_C"])
            input_J += q * DT
            loss_J += loss * DT
            expected = (loss, q-loss, input_J, loss_J, C*(T-Decimal(16)),
                        C*(T-prev_T)/DT - (q-loss))
            for key, value in zip(FIELDS, expected):
                observed = Decimal(b[key])
                tolerance = Decimal("0.1") if key.endswith("_cum_J") else Decimal("0.001")
                assert abs(observed - value) < tolerance, (label, i, key, observed, value)
                checks += 1
            assert Decimal(b["time_s"]) == i*DT
            assert abs(Decimal(b["T_pool_C"])-T) < Decimal("0.000001")
            checks += 2
            max_res = max(max_res, abs(expected[-1]))
            prev_T = T
        closure = input_J - loss_J - C*(prev_T-Decimal(16))
        assert abs(closure) < Decimal("1")
        return {"rows": 672, "decimal_checks": checks, "max_state_residual_W": str(max_res),
                "integrated_closure_J": str(closure), "source_sha256": sha(raw),
                "output_sha256": sha(out)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("raw_v08", type=Path)
    p.add_argument("out_v08", type=Path)
    p.add_argument("raw_v09", type=Path)
    p.add_argument("out_v09", type=Path)
    p.add_argument("report_json", type=Path)
    a = p.parse_args()
    if a.report_json.exists():
        raise ValueError("REPORT_EXISTS")
    result = {"source_kind": "derived_simulation", "physical_release": False,
              "v08": verify(a.raw_v08, a.out_v08, "v08"),
              "v09": verify(a.raw_v09, a.out_v09, "v09")}
    result["decimal_checks"] = result["v08"]["decimal_checks"] + result["v09"]["decimal_checks"]
    a.report_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "rows": 1344, "decimal_checks": result["decimal_checks"]}))


if __name__ == "__main__":
    main()
