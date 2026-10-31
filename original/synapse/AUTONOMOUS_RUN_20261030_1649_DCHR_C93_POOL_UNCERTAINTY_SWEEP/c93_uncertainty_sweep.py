"""C93: independent task-local uncertainty sweep of the synthetic 500 m3 pool.
This is NOT a field-calibrated plant model or an ASHRAE design certification.
Read-only pinned C90/C91/C92; outputs only in this task directory.
"""
from __future__ import annotations
import csv
import datetime as dt
import hashlib
import importlib.util
import json
import math
from pathlib import Path

D = Path(__file__).resolve().parent
RECOVERY = D.parent
SCC = RECOVERY.parent
C91_DIR = RECOVERY / "AUTONOMOUS_RUN_20261030_1553_DCHR_C91_POOL_DYNAMIC_THERMOSTAT"
C92_DIR = RECOVERY / "AUTONOMOUS_RUN_20261030_1603_DCHR_C92_ASHRAE_EVAP_REFERENCE"
C91_FILE = C91_DIR / "c91_pool_dynamic.py"
C92_FILE = C92_DIR / "c92_ashrae_evap_compare.py"
C91_SHA = "964cb181227db7c5af93e8632e352919ab28b030de69c934412dc798bb7264b4"
C92_SHA = "242554e2f5f4cd3c08d31d340630a0cad20d505420b29662c21bea7464dd5990"
FLAGS = ("STOP", "STOP.txt", "STOP.flag", "PAUSE", "PAUSE.txt", "PAUSE.flag", ".STOP", ".PAUSE")
RH = (0.45, 0.55, 0.65)
COVER = (0.05, 0.15, 0.35)
RECOVERY_FRACTION = (0.0, 0.10, 0.25)
BACKUP_CAP = (0.0, 0.05)

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1048576), b""):
            h.update(b)
    return h.hexdigest()

def guard():
    roots = (D, RECOVERY, SCC, Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse"))
    for root in roots:
        for flag in FLAGS:
            if (root / flag).exists():
                raise RuntimeError("STOP_ACTIVE " + str(root / flag))

def load():
    if sha(C91_FILE) != C91_SHA or sha(C92_FILE) != C92_SHA:
        raise RuntimeError("UPSTREAM_SCRIPT_DRIFT")
    spec = importlib.util.spec_from_file_location("c92_c93_reference", C92_FILE)
    c92 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c92)
    c91 = c92.m
    if sha(c91.C90) != c91.C90_SHA:
        raise RuntimeError("UPSTREAM_DATA_DRIFT")
    with c91.C90.open(encoding="utf-8", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["scenario"] == "covered_no_extra"]
    if len(rows) != 8760:
        raise RuntimeError("EXPECTED_8760_HOURS")
    times = [dt.datetime.fromisoformat(r["time"]) for r in rows]
    if times[0] != dt.datetime(2026, 1, 1) or times[-1] != dt.datetime(2026, 12, 31, 23):
        raise RuntimeError("WRONG_TIME_RANGE")
    if any(b - a != dt.timedelta(hours=1) for a, b in zip(times, times[1:])):
        raise RuntimeError("NON_CONTIGUOUS_HOURS")
    return c91, c92, rows, times

def loss_components(c91, c92, temp, hour, rh, cover):
    if not (0 < rh < 1 and 0 <= cover <= 1 and math.isfinite(temp) and 0 < temp < 45):
        raise ValueError("BAD_PHYSICAL_PARAMETER")
    covered = hour >= 20 or hour < 7
    occupied = 9 <= hour < 20
    activity = 1.0 if occupied else 0.5
    delta_p = max(0.0, c91.saturation(temp) - rh * c91.saturation(29.0))
    evap_kg_h = 250.0 * c92.k_ashrae(temp) * delta_p * activity * (cover if covered else 1.0)
    latent = evap_kg_h * (2501.0 - 2.361 * temp) / 3600000.0
    makeup = evap_kg_h * 4.186 * (temp - 12.0) / 3600000.0
    conv = max(0.0, 3.0 * 250.0 * (temp - 29.0) / 1e6) * (0.25 if covered else 1.0)
    rad = max(0.0, 0.96 * 5.670374419e-8 * 250.0 *
              ((temp + 273.15)**4 - (27.0 + 273.15)**4) / 1e6) * (0.30 if covered else 1.0)
    ground = 0.35 * (250.0 + 140.0) * (temp - 18.0) / 1e6
    return latent + makeup + conv + rad + ground, evap_kg_h

def simulate(c91, c92, rows, times, rh, cover, fraction, backup_cap):
    if not (0 <= fraction <= 1 and 0 <= backup_cap <= 0.3):
        raise ValueError("BAD_DISPATCH_PARAMETER")
    t, active = 28.0, False
    minimum, maximum, low_hours = 99.0, -99.0, 0
    totals = {k: 0.0 for k in ("pool_loss_MWh", "evap_kg", "HP_heat_MWh",
        "HP_electric_MWh", "HX_extracted_MWh", "backup_MWh", "storage_delta_MWh")}
    max_balance = 0.0
    for stamp, row in zip(times, rows):
        q, evap = loss_components(c91, c92, t, stamp.hour, rh, cover)
        if t <= c91.ON_C:
            active = True
        elif t >= c91.OFF_C:
            active = False
        request = max(0.0, q + (c91.OFF_C - t) * c91.CAP) if active else 0.0
        source = float(row["HX_rejected_MW"])
        hp = min(request, c91.potential_hp(source, fraction))
        backup = min(backup_cap, max(0.0, (27.60 - (t + (hp - q) / c91.CAP)) * c91.CAP)) if active else 0.0
        t_next = t + (hp + backup - q) / c91.CAP
        if not (0 <= t_next <= 45 and math.isfinite(t_next)):
            raise RuntimeError("UNPHYSICAL_TEMPERATURE")
        extracted = hp * (c91.COP - 1) / c91.COP
        if extracted > source * fraction + 1e-10 or hp > 0.30 + 1e-10:
            raise RuntimeError("SOURCE_OR_HP_CAP_EXCEEDED")
        if backup > backup_cap + 1e-10:
            raise RuntimeError("BACKUP_CAP_EXCEEDED")
        balance = abs(c91.CAP * (t_next - t) - (hp + backup - q))
        max_balance = max(max_balance, balance)
        if balance > 1e-10:
            raise RuntimeError("ENERGY_BALANCE_FAILED")
        totals["pool_loss_MWh"] += q
        totals["evap_kg"] += evap
        totals["HP_heat_MWh"] += hp
        totals["HP_electric_MWh"] += hp / c91.COP
        totals["HX_extracted_MWh"] += extracted
        totals["backup_MWh"] += backup
        totals["storage_delta_MWh"] += c91.CAP * (t_next - t)
        minimum, maximum = min(minimum, t_next), max(maximum, t_next)
        low_hours += int(t_next < 27.5)
        t = t_next
    if abs(totals["storage_delta_MWh"] - c91.CAP * (t - 28.0)) > 1e-8:
        raise RuntimeError("ANNUAL_STORAGE_BALANCE_FAILED")
    return {"RH": rh, "cover_multiplier": cover, "recoverable_fraction": fraction,
            "backup_cap_MW": backup_cap, "min_temp_C": minimum, "max_temp_C": maximum,
            "final_temp_C": t, "hours_below_27p5": low_hours,
            "max_abs_balance_MWh": max_balance, **totals}

def selftest(c91, c92):
    for h in (2, 12, 22):
        assert loss_components(c91,c92,28,h,0.45,0.15)[0] >= loss_components(c91,c92,28,h,0.65,0.15)[0]
    assert loss_components(c91,c92,28,2,0.55,0.05)[0] < loss_components(c91,c92,28,2,0.55,0.35)[0]
    assert abs(loss_components(c91,c92,28,12,0.55,0.15)[0] - c92.reference_losses(28,12)) < 1e-12
    assert abs(loss_components(c91,c92,28,2,0.55,0.15)[0] - c92.reference_losses(28,2)) < 1e-12
    for args in ((28,12,-0.1,0.15),(28,12,1.1,0.15),(28,12,0.55,-0.1),(28,12,0.55,1.1)):
        try: loss_components(c91,c92,*args)
        except ValueError: pass
        else: raise AssertionError("INVALID_INPUT_ACCEPTED " + repr(args))
    print("C93 SELFTEST 8/8 PASS")

def run():
    guard()
    c91, c92, rows, times = load()
    selftest(c91,c92)
    results = []
    for rh in RH:
        for cover in COVER:
            for fraction in RECOVERY_FRACTION:
                for backup in BACKUP_CAP:
                    results.append(simulate(c91,c92,rows,times,rh,cover,fraction,backup))
    if len(results) != 54:
        raise RuntimeError("BAD_SCENARIO_COUNT")
    reference = json.loads((C92_DIR/"C92_REFERENCE_COMPARISON.json").read_text(encoding="utf-8"))
    for fraction in (0.10,0.25):
        ours = next(r for r in results if r["RH"]==0.55 and r["cover_multiplier"]==0.15
                    and r["recoverable_fraction"]==fraction and r["backup_cap_MW"]==0.0)
        theirs = reference["simulations"][f"ASHRAE2023_reference_{int(fraction*100)}pct"]
        for ours_key, their_key in (("HP_heat_MWh","HP_heat_MWh"),("min_temp_C","min_temp_C"),
                                   ("final_temp_C","final_temp_C")):
            if abs(ours[ours_key]-theirs[their_key])>1e-8:
                raise RuntimeError("C92_REGRESSION_MISMATCH " + ours_key)
        if ours["hours_below_27p5"] != theirs["hours_below_27p5"]:
            raise RuntimeError("C92_HOURS_MISMATCH")
    guard()
    outcsv = D/"C93_SCENARIO_MATRIX.csv"
    with outcsv.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(results[0]))
        w.writeheader()
        w.writerows(results)
    metadata = {
        "schema":"C93_POOL_UNCERTAINTY_MATRIX_V1",
        "task_id":"scc-2aab24704c2bd0",
        "synthetic":True,"validated_real_facility":False,"source_signoffs_added":0,
        "hourly_steps_per_scenario":8760,"scenarios":len(results),
        "parameter_grid":{"relative_humidity":RH,"night_cover_multiplier":COVER,
                          "hypothetical_HX_recovery_fraction":RECOVERY_FRACTION,
                          "backup_capacity_MW":BACKUP_CAP},
        "pins":{"C90_input_sha256":c91.C90_SHA,"C91_script_sha256":C91_SHA,"C92_script_sha256":C92_SHA,
                "C92_reference_json_sha256":sha(C92_DIR/"C92_REFERENCE_COMPARISON.json")},
        "reference":"ASHRAE Handbook 2023, HVAC Applications, Chapter 6, Eq. 2 (see C92)",
        "crosscheck":"C92 RH=.55, cover=.15, no backup, recovery=.10/.25 agrees within 1e-8",
        "limitations":["RH, cover effectiveness and recovery fractions are hypothetical, not measurements.",
                       "COP fixed at 4; no source/sink temperature feasibility, pinch, or heat pump map.",
                       "Ventilation/dehumidification and air-side heating not coupled to this water-only model.",
                       "1h explicit Euler, single fully mixed pool, assumed occupancy and 29C air temperature.",
                       "No real pool classification, energy meter data, tariffs or source signoffs."],
        "matrix_sha256":sha(outcsv)}
    (D/"C93_MATRIX_METADATA.json").write_text(json.dumps(metadata,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"scenarios":len(results),"matrix_sha256":sha(outcsv),
                      "anchor_10pct":next(r for r in results if (r["RH"],r["cover_multiplier"],
                           r["recoverable_fraction"],r["backup_cap_MW"])==(0.55,0.15,0.1,0.0)),
                      "anchor_25pct":next(r for r in results if (r["RH"],r["cover_multiplier"],
                           r["recoverable_fraction"],r["backup_cap_MW"])==(0.55,0.15,0.25,0.0))},indent=2))
if __name__ == "__main__":
    run()
