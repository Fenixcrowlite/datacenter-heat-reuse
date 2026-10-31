"""Independent Decimal reconstruction of every water volume and loss result."""
import json
import math
from decimal import Decimal, getcontext
from pathlib import Path
getcontext().prec=45
H=Path(__file__).resolve().parent
r=json.loads((H/"STORAGE_VOLUME_FEASIBILITY.json").read_text(encoding="utf-8"))
n=0
infeasible=0
for x in r["cases"]:
    hot=Decimal(str(x["hot_c"]))
    minimum=Decimal(str(x["supply_c"]))+Decimal(str(r["hx_approach_k"]))
    cap=Decimal(str(x["capacity_mwh"]))
    if hot<=minimum:
        assert not x["temperature_feasible"]
        assert x["ideal_water_volume_m3"] is None
        infeasible+=1
    else:
        volume=(cap*Decimal("3600000000")/
                (Decimal("4180")*Decimal("1000")*(hot-minimum)))
        actual=Decimal(str(x["ideal_water_volume_m3"]))
        assert abs(volume-actual)<max(Decimal("0.000001"),abs(volume)*Decimal("1e-12"))
        geo=x["ideal_geometry_10m"]
        assert math.isclose(geo["footprint_m2"]*geo["height_m"],
                            float(actual),rel_tol=1e-12)
    n+=1
assert n==64
assert r["source"]["rows"]==8760
assert r["source"]["source_sha256"]=="8125719923bae97901f37cf0f5354df77b46544df0477f863172255748873f25"
p=Decimal("1")-Decimal("0.00025")
for days in (30,90,180):
    v=p**(24*days)
    assert abs(v-Decimal(str(r["retention"][f"{days}d"])))<Decimal("1e-13")
ref=next(x for x in r["cases"] if x["capacity_mwh"]==2500 and
         x["hot_c"]==72 and x["supply_statistic"]=="max")
assert 300000<ref["ideal_water_volume_m3"]<320000
out={"status":"PASS","cases_checked":n,"temperature_infeasible_cases":infeasible,
     "decimal_retention_checks":3,"geometry_reconstructions":n-infeasible,
     "reference_volume_m3":ref["ideal_water_volume_m3"],
     "classification":"independent numerical QA, not physical validation"}
(H/"QA_INDEPENDENT.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out))
