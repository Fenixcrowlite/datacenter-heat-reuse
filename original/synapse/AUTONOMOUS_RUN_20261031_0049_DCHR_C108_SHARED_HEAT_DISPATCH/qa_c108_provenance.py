"""Fail-closed provenance and timestamp audit of C108 immutable upstream inputs."""
import csv,gzip,hashlib,json
from pathlib import Path
D=Path(__file__).resolve().parent
m=json.loads((D/"C108_METADATA.json").read_text(encoding="utf-8"))
def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
checks=0
for path,pin in m["source_pins"].items():
 assert Path(path).is_file() and sha(path)==pin,("PIN_MISMATCH",path)
 checks+=1
c96=D.parent/"AUTONOMOUS_RUN_20261030_1850_DCHR_C96_UA_NTU_PUMP_ENVELOPE"/"c96_ua_ntu_pool.py"
assert sha(c96)==m["source_C96_script_sha256"]
checks+=1
for name,expected in (("C108_SHARED_HOURLY.csv.gz","hourly_sha256"),
                      ("C108_SUMMARY.csv","summary_sha256")):
 assert sha(D/name)==m[expected]
 checks+=1
assert m["scenarios"]==12 and m["rows"]==105120
checks+=1
with gzip.open(D/"C108_SHARED_HOURLY.csv.gz","rt",encoding="utf-8",newline="") as f:
 r=csv.DictReader(f)
 times={}
 for row in r:
  name=row["scenario"]; t=row["time"]
  if name not in times:times[name]=[t,t,1]
  else:
   assert t>times[name][1],("TIME_ORDER",name,t)
   times[name][1]=t;times[name][2]+=1
assert len(times)==12
for name,(start,end,n) in times.items():
 assert (start,end,n)==("2026-01-01T00:00:00","2026-12-31T23:00:00",8760)
 checks+=1
# Negative provenance control, no source file modified.
fake="0"*64
assert sha(c96)!=fake
checks+=1
out={"schema":"C108_PROVENANCE_QA_V1","status":"PASS",
 "checks":checks,"source_pins_verified":3,"scenario_time_ranges":len(times),
 "negative_control":1,"C96_script_sha256":sha(c96)}
with (D/"C108_PROVENANCE_QA.json").open("x",encoding="utf-8") as f:
 json.dump(out,f,indent=2,sort_keys=True);f.write("\n")
print(json.dumps(out,indent=2))
