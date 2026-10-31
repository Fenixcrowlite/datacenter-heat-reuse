import json
import random
from datetime import datetime, timezone
from pathlib import Path
from dispatch_reference_v16 import StorageParameters, DispatchParameters, dispatch_step
rng = random.Random(17009)
errors = []
max_residual = 0.0
for i in range(1000):
    capacity = rng.uniform(1, 100)
    storage = StorageParameters(capacity_MWh=capacity)
    cfg = DispatchParameters(storage=storage, boiler_capacity_MW=10, dt_h=1)
    initial = rng.uniform(0, capacity)
    source = rng.uniform(0, 30)
    demand = rng.uniform(0, 50)
    source_temp = rng.uniform(5, 35)
    x = dispatch_step(source, source_temp, source_temp+30, demand, initial, cfg)
    residual = (x.HP_Source_Used_MW + x.HP_Electric_MW + x.Gas_Heat_MW
                + initial - x.Supplied_Heat_MW - x.Storage_E_Next_MWh
                - x.Storage_Standing_Loss_MWh - x.Storage_Charge_Loss_MWh
                - x.Storage_Discharge_Loss_MWh)
    max_residual = max(max_residual, abs(residual))
    if abs(residual)>1e-8 or abs(demand-x.Supplied_Heat_MW-x.Unmet_Heat_MW)>1e-8:
        errors.append(i)
report = {"utc": datetime.now(timezone.utc).isoformat(),
          "scope": "Python algebraic stress, not physical or MATLAB validation",
          "cases": 1000, "errors": errors, "max_abs_balance_MWh": max_residual}
Path(__file__).with_name("dispatch_properties_v17.json").write_text(json.dumps(report,indent=2))
print(report)
raise SystemExit(bool(errors))
