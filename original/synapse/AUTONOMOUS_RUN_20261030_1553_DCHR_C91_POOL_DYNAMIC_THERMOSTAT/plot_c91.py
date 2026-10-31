import csv
from collections import defaultdict
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
d=Path(__file__).resolve().parent
series=defaultdict(list)
with (d/"C91_DYNAMIC_HOURLY.csv").open(encoding="utf-8",newline="") as f:
    for r in csv.DictReader(f):
        if r["time"].endswith("T12:00:00"):
            series[r["scenario"]].append(float(r["temp_end_C"]))
assert len(series)==6 and all(len(v)==365 for v in series.values())
fig,ax=plt.subplots(figsize=(13,5.6),dpi=140)
for name,temps in series.items():
    ax.plot(range(365),temps,label=name.replace("_"," "),linewidth=1.5)
ax.axhline(27.5,linestyle="--",label="comfort threshold 27.5 C")
ax.set(xlabel="Day of synthetic year 2026",ylabel="Pool water temperature [C]",
       title="500 m3 pool: dynamic temperature under hypothetical HX recovery")
ax.grid(alpha=0.25)
ax.legend(loc="lower right",fontsize=8,ncol=2)
fig.tight_layout()
fig.savefig(d/"C91_TEMPERATURE_YEAR.png")
plt.close(fig)
print("PLOT 6 scenarios x 365 days PASS")