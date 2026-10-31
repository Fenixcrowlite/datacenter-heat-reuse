"""Independent deterministic Python reference for MATLAB v16 contract."""
import csv
import dataclasses
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from dispatch_reference_v16 import DispatchParameters, StorageParameters, dispatch_step
from heat_pump_reference_v14 import HeatPumpParameters

SCENARIOS = [
    ("charge_then_shortage", 10, [(10,35,65,2),(0,35,65,12),(0,35,65,25),(10,35,65,0)]),
    ("empty_then_recover", 0, [(0,35,65,30),(10,35,65,0),(5,35,65,7),(0,35,65,4)]),
    ("full_and_cutoff", 20, [(9,5,85,6),(10,35,65,9),(0,35,65,18),(10,35,65,1)]),
]
def generate():
    p = DispatchParameters(
        hp=HeatPumpParameters(),
        storage=StorageParameters(capacity_MWh=20, charge_limit_MW=5,
            discharge_limit_MW=5, eta_charge=.95, eta_discharge=.95,
            loss_fraction_per_h=.001),
        boiler_capacity_MW=2, dt_h=.5)
    rows = []
    for sid, energy, steps in SCENARIOS:
        for step, (source, tc, th, demand) in enumerate(steps, 1):
            r = dispatch_step(source, tc, th, demand, energy, p)
            row = {
                "scenario_id":sid, "step":step, "dt_h":p.dt_h,
                "storage_capacity_MWh":p.storage.capacity_MWh,
                "charge_limit_MW":p.storage.charge_limit_MW,
                "discharge_limit_MW":p.storage.discharge_limit_MW,
                "eta_charge":p.storage.eta_charge,
                "eta_discharge":p.storage.eta_discharge,
                "loss_fraction_per_h":p.storage.loss_fraction_per_h,
                "boiler_capacity_MW":p.boiler_capacity_MW,
                "hp_capacity_MW":p.hp.capacity_MW,
                "carnot_efficiency":p.hp.carnot_efficiency,
                "cop_min":p.hp.cop_min, "cop_max":p.hp.cop_max,
                "part_load_penalty":p.hp.part_load_penalty,
                "backend":p.hp.backend, "poly_c0":p.hp.poly_c0,
                "poly_c1":p.hp.poly_c1, "poly_c2":p.hp.poly_c2,
                "Source_Heat_MW":source, "Source_C":tc,
                "Sink_C":th, "Heat_Demand_MW":demand}
            row.update({"expected_"+k:int(v) if isinstance(v,bool) else v
                        for k,v in dataclasses.asdict(r).items()})
            rows.append(row)
            energy = r.Storage_E_Next_MWh
    return rows
if __name__ == "__main__":
    rows = generate()
    out = HERE / "dispatch_reference_vectors_v18.csv"
    if out.exists():
        raise FileExistsError(out)
    with out.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    coverage = {
        "charge":any(r["expected_Storage_Charge_MW"]>0 for r in rows),
        "discharge":any(r["expected_Storage_Discharge_MW"]>0 for r in rows),
        "unmet":any(r["expected_Unmet_Heat_MW"]>0 for r in rows),
        "off":any(r["expected_HP_Available"]==0 for r in rows),
        "zero_demand_charge":any(r["Heat_Demand_MW"]==0 and r["expected_Storage_Charge_MW"]>0 for r in rows)}
    assert all(coverage.values()), coverage
    print("V18_REFERENCE", len(rows), coverage, out)
