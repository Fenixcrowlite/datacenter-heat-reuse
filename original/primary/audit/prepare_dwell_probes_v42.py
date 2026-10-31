from pathlib import Path
import json, math, random
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
rows=[]
for hi in (0.,1e-12,.5,1.,100.,1e5):
    for lo in (0.,-.125*math.ulp(max(1.,hi)),.125*math.ulp(max(1.,hi))):
        for bound in (0.,math.ldexp(1.,-80),1e-12,1e-9):
            for dwell in (hi,math.nextafter(hi,math.inf),max(0.,math.nextafter(hi,-math.inf))):
                rows.append([hi,lo,bound,dwell])
rng=random.Random(42)
for k in range(800):
    hi=10**rng.uniform(-12,5);lo=rng.uniform(-.5,.5)*math.ulp(max(1.,hi))
    bound=rng.choice((0.,2**-80,1e-12,1e-9))
    dwell=max(0.,hi+rng.uniform(-2,2)*(bound+abs(lo)))
    rows.append([hi,lo,bound,dwell])
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
p=ROOT/'audit'/('dwell_probe_spec_v42_'+stamp+'.json')
p.write_text(json.dumps(dict(evidence_class='synthetic_numeric_function_probes_not_plant_simulations',probes=rows),indent=2)+'\n')
print('PROBE_SPEC='+p.relative_to(ROOT).as_posix())
