"""Optimistic water-storage geometry gate for SYNTHETIC DataCenter sensitivity.
No equipment validation, no Simulink integration, no real savings claim.
"""
from __future__ import annotations
import csv
import hashlib
import json
import math
from pathlib import Path

SOURCE = Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\best_scenario_v2_timeseries.csv")
EXPECTED_SHA = "8125719923bae97901f37cf0f5354df77b46544df0477f863172255748873f25"
CP_J_KG_K = 4180.0
RHO_KG_M3 = 1000.0  # optimistic rounded water density, NOT a calibrated hot-water value
HX_APPROACH_K = 3.0
HOURLY_LOSS = 0.00025
CAPACITIES_MWH = (100, 500, 2500, 10000)
HOT_TEMPERATURES_C = (55, 65, 72, 80)

def water_volume_m3(capacity_mwh, hot_c, min_usable_c, *, cp=CP_J_KG_K, rho=RHO_KG_M3):
    """Water volume for an ideal fully usable temperature swing. None if impossible."""
    vals=(capacity_mwh,hot_c,min_usable_c,cp,rho)
    if not all(math.isfinite(x) for x in vals) or capacity_mwh<0 or cp<=0 or rho<=0:
        raise ValueError("invalid volume inputs")
    if hot_c<=min_usable_c:
        return None
    return capacity_mwh*3.6e9/(cp*rho*(hot_c-min_usable_c))

def cylinder_geometry(volume_m3, height_m=10.0):
    if not (math.isfinite(volume_m3) and math.isfinite(height_m)) or volume_m3<0 or height_m<=0:
        raise ValueError("invalid geometry")
    area=volume_m3/height_m
    return {"height_m":height_m,"footprint_m2":area,
            "equivalent_single_cylinder_diameter_m":2*math.sqrt(area/math.pi)}

def loss_retention(loss_fraction, hours):
    if not (math.isfinite(loss_fraction) and math.isfinite(hours)) or not (0<=loss_fraction<1) or hours<0:
        raise ValueError("invalid loss")
    return (1-loss_fraction)**hours

def half_life_hours(loss_fraction):
    if not (math.isfinite(loss_fraction) and 0<loss_fraction<1):
        raise ValueError("invalid loss")
    return math.log(.5)/math.log1p(-loss_fraction)

def source_profile(path=SOURCE, expected_sha=EXPECTED_SHA):
    raw=Path(path).read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    if expected_sha is not None and digest!=expected_sha:
        raise ValueError("source sha mismatch")
    rows=list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    if len(rows)!=8760:
        raise ValueError("expected 8760 hourly source rows")
    values=[float(r["DH_Supply_C"]) for r in rows]
    if not all(math.isfinite(x) and -50<x<150 for x in values):
        raise ValueError("invalid source temperature")
    ordered=sorted(values)
    return {"source_sha256":digest,"rows":len(values),
            "min_c":min(values),"median_c":ordered[(len(values)-1)//2],
            "p95_c":ordered[int((len(values)-1)*.95)],
            "max_c":max(values)}

def evaluate():
    profile=source_profile()
    cases=[]
    for hot in HOT_TEMPERATURES_C:
        for cap in CAPACITIES_MWH:
            for label in ("min","median","p95","max"):
                supply=profile[label+"_c"]
                min_usable=supply+HX_APPROACH_K
                volume=water_volume_m3(cap,hot,min_usable)
                geometry=cylinder_geometry(volume) if volume is not None else None
                cases.append({"capacity_mwh":cap,"hot_c":hot,"supply_statistic":label,
                    "supply_c":supply,"min_usable_c":min_usable,
                    "usable_delta_k":max(0.0,hot-min_usable),
                    "ideal_water_volume_m3":volume,"ideal_geometry_10m":geometry,
                    "temperature_feasible":volume is not None})
    return {"classification":"SYNTHETIC_OPTIMISTIC_WATER_VOLUME_LOWER_BOUND_NOT_A_DESIGN",
        "source":profile,"cp_j_kg_k":CP_J_KG_K,"rho_kg_m3":RHO_KG_M3,
        "hx_approach_k":HX_APPROACH_K,"cases":cases,
        "hourly_soc_loss_fraction":HOURLY_LOSS,
        "half_life_hours":half_life_hours(HOURLY_LOSS),
        "retention":{"30d":loss_retention(HOURLY_LOSS,720),
                     "90d":loss_retention(HOURLY_LOSS,2160),
                     "180d":loss_retention(HOURLY_LOSS,4320)},
        "baseline_storage_mwh":100,"primary_source_signoffs":0,
        "assumptions":[
          "This computes ideal sensible heat stored in water between hot and minimum usable temperatures.",
          "The 2500 MWh in the previous model is a thermal SOC capacity, not a measured tank volume.",
          "1000 kg/m3 density is optimistic for hot water and gives an optimistic minimum volume.",
          "A 10 m single-cylinder equivalent is a scale visualization, not a proposed engineering layout.",
          "Max-supply gate is conservative for year-round temperature usability, not a demand-weighted optimization.",
          "No stratification, mixing, thermocline, pumping, hydraulic losses, groundworks, UA, or real equipment sizing.",
          "Fixed-temperature SOC in previous model can release energy without cooling; physical temperature trajectory is NOT validated.",
          "Loss retention uses only prior model's assumed proportional SOC decay, not a measured tank UA.",
          "Baseline already has 100 MWh storage; this does not establish incremental energy or financial savings.",
          "Synthetic hourly weather, no real metering, and 0/31 primary-source signoffs."
        ]}
if __name__=="__main__":
    p=Path(__file__).resolve().parent/"STORAGE_VOLUME_FEASIBILITY.json"
    result=evaluate()
    p.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    selected=[x for x in result["cases"] if x["capacity_mwh"]==2500 and x["hot_c"]==72 and x["supply_statistic"]=="max"][0]
    print(json.dumps({"source_rows":result["source"]["rows"],"max_supply_c":result["source"]["max_c"],
      "reference_volume_m3":selected["ideal_water_volume_m3"],"cases":len(result["cases"]),
      "loss_half_life_h":result["half_life_hours"]}))
