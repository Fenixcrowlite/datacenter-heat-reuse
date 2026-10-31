"""Replay all 672 synthetic v08 healthy samples through conservative redispatch."""
import csv
import hashlib
import json
from pathlib import Path
from redispatch import Caps, apply_after

HERE = Path(__file__).resolve().parent
SOURCE = Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\pool_measurement_v08\sim_v08_zdravy_SK.csv")
SCENARIOS = {
    "baseline": Caps(),
    "pool_off": Caps(pool_W=0),
    "dh_off": Caps(dh_W=0),
    "both_off": Caps(pool_W=0, dh_W=0),
    "pool40_dh25": Caps(pool_W=40000, dh_W=25000),
    "both_off_assumed_reject150": Caps(pool_W=0, dh_W=0, reject_W=150000),
}
OUTPUT_FIELDS = [
    "cas_h", "Q_pool_W", "Q_DH_W", "Q_HX_W", "Q_HP_pool_W",
    "Q_HP_DH_W", "Q_HP_charge_W", "Q_TES_discharge_W",
    "Q_HP_source_W", "P_HP_proxy_W", "Q_reject_required_W",
    "Q_reject_actual_W", "Q_unhandled_W", "Q_pool_unmet_W",
    "Q_DH_unmet_W", "status",
]
ENERGY_FIELDS = [
    "Q_pool_W", "Q_DH_W", "Q_reject_required_W", "Q_reject_actual_W",
    "Q_unhandled_W", "P_HP_proxy_W", "Q_TES_discharge_W",
    "Q_pool_unmet_W", "Q_DH_unmet_W",
]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    with SOURCE.open(encoding="utf-8-sig", newline="") as f:
        original = list(csv.DictReader(f))
    if len(original) != 672:
        raise RuntimeError("EXPECTED_672_V08_SAMPLES")
    hours = [float(r["cas_h"]) for r in original]
    steps = [b-a for a,b in zip(hours,hours[1:])]
    if max(abs(dt - 0.25) for dt in steps) > 1e-9:
        raise RuntimeError("EXPECTED_15MIN_STEP")
    summary = {
        "provenance": "D_SYNTHETIC original v08 -> D_DERIVED conservative instantaneous reference",
        "source_path": str(SOURCE), "source_sha256": sha(SOURCE),
        "samples": len(original), "interval_hours": 0.25,
        "hours": len(original) * 0.25,
        "start_hour": 24.0,
        "reject_150kW": "ASSUMED SENSITIVITY ONLY; NOT A VERIFIED EQUIPMENT RATING",
        "TES_state": "NOT RECOMPUTED", "pool_temperature": "NOT RECOMPUTED",
        "HP_COP": "fixed per-baseline-interval ratio; NOT a measured part-load curve",
        "net_electric_savings": "NOT VALIDATED; fan/pump effects missing",
        "physical_release_allowed": False,
        "scenarios": {},
    }
    for name, caps in SCENARIOS.items():
        results = [apply_after(r, caps, 24.0) for r in original]
        out_path = HERE / f"scenario_{name}.csv"
        with out_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
            w.writeheader()
            for row, result in zip(original, results):
                w.writerow({k: (row["cas_h"] if k == "cas_h" else result[k])
                            for k in OUTPUT_FIELDS})
        energies = {k.replace("_W", "_kWh"): round(sum(r[k] for r in results)*0.25/1000, 6)
                    for k in ENERGY_FIELDS}
        summary["scenarios"][name] = {
            "energy": energies,
            "max_reject_required_kW": round(max(r["Q_reject_required_W"] for r in results)/1000, 6),
            "max_balance_residual_W": max(abs(v) for r in results for v in r["residuals_W"].values()),
            "unsafe_intervals": sum(r["status"] == "UNSAFE_UNHANDLED_HEAT" for r in results),
            "capacity_unknown_intervals": sum(r["status"] == "REJECT_CAPACITY_UNKNOWN" for r in results),
            "output": out_path.name, "output_sha256": sha(out_path),
        }
    baseline = summary["scenarios"]["baseline"]["energy"]
    for name, v in summary["scenarios"].items():
        v["delta_reject_required_kWh"] = round(
            v["energy"]["Q_reject_required_kWh"]-baseline["Q_reject_required_kWh"], 6)
        v["delta_HP_power_proxy_kWh"] = round(
            v["energy"]["P_HP_proxy_kWh"]-baseline["P_HP_proxy_kWh"], 6)
    (HERE/"RESULTS.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({
        "source_sha256": summary["source_sha256"], "samples": summary["samples"],
        "scenarios": {k: {"max_reject_kW":v["max_reject_required_kW"],
                         "delta_reject_kWh":v["delta_reject_required_kWh"],
                         "delta_HP_proxy_kWh":v["delta_HP_power_proxy_kWh"],
                         "unsafe_intervals":v["unsafe_intervals"]}
                      for k,v in summary["scenarios"].items()}
    },ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
