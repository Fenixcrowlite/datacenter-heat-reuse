"""Independent seeded Gaussian Monte Carlo, cross-checks analytic product uncertainty."""
import json
import math
import random
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
d = json.loads((HERE / "CORRELATED_METROLOGY_EVIDENCE.json").read_text(encoding="utf-8"))
rng = random.Random(20261025)
k = 997*4182/3600
results = {}
for name, case in d["heat_cases"].items():
    r = case["temperature_correlation"]
    vals = []
    for _ in range(80000):
        zf = rng.gauss(0, 1)
        zh = rng.gauss(0, 1)
        zc = rng.gauss(0, 1)
        flow = 30 + 1.5*zf
        hot = 30 + .2*zh
        cold = 27 + .2*(r*zh+math.sqrt(1-r*r)*zc)
        vals.append(k*flow*(hot-cold))
    empirical_mean = statistics.fmean(vals)
    empirical_std = statistics.stdev(vals)
    analytic_mean = case["gaussian_exact_mean_W"]
    analytic_std = case["gaussian_exact_standard_uncertainty_W"]
    mean_rel = abs(empirical_mean-analytic_mean)/analytic_std
    std_rel = abs(empirical_std-analytic_std)/analytic_std
    results[name] = {"n":len(vals), "empirical_mean_W":empirical_mean,
                     "empirical_std_W":empirical_std,
                     "analytic_mean_W":analytic_mean,
                     "analytic_std_W":analytic_std,
                     "mean_error_in_sigma":mean_rel,
                     "relative_std_error":std_rel}
    if mean_rel > .025 or std_rel > .025:
        raise AssertionError((name, mean_rel, std_rel))
out=HERE/"MONTE_CARLO_QA.json"
if out.exists():
    raise FileExistsError(out)
out.write_text(json.dumps({"status":"PASS","seed":20261025,"cases":results},indent=2)+"\n",encoding="utf-8")
print("MONTE_CARLO_PASS 3 cases x 80000 samples")
