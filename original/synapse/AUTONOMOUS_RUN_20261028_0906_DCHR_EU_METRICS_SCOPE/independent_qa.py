"""Independent deterministic identities using rational arithmetic and original source pin."""
import hashlib,json,random,subprocess,sys
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from eu_dc_metrics import metrics,applicability
H=Path(__file__).resolve().parent
M=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\audit\literature_traceability_v44.csv")
STATUS=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\STATUS_v86.json")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=(sha(M),sha(STATUS))
s=json.loads(STATUS.read_text(encoding="utf-8-sig"))
assert s["full_primary_signoffs"]==0 and s["total_sources"]==31
assert s["new_model"] is False
rng=random.Random(20261028)
checks=0
for i in range(1000):
 edc=rng.randint(1,1000000)
 eit=rng.randint(1,edc)
 reuse=rng.randint(0,edc)
 res=rng.randint(0,edc)
 water=rng.randint(0,10000)
 row={"edc_kwh":str(edc),"eit_kwh":str(eit),"ereuse_kwh":str(reuse),
      "eres_total_kwh":str(res),"win_m3":str(water)}
 got=metrics(row)
 expect={"PUE":Fraction(edc,eit),"ERF":Fraction(reuse,edc),
         "REF":Fraction(res,edc),"WUE_m3_per_MWh_IT":Fraction(water*1000,eit)}
 for k,f in expect.items():
  # Compare to 30-digit Decimal calculation against an independent exact rational.
  value=Decimal(got[k])
  err=abs(value*Decimal(f.denominator)-Decimal(f.numerator))
  assert err < Decimal("1e-20"),(i,k,err)
  checks+=1
assert applicability("500","1000")["article12_reporting_500kW_or_more"]
assert not applicability("500","1000")["article26_heat_reuse_over_1MW"]
checks+=2
p=subprocess.run([sys.executable,"-B",str(H/"test_eu_dc_metrics.py")],
                 capture_output=True,text=True,timeout=20)
assert p.returncode==0 and "Ran 25 tests" in p.stderr and "\nOK" in p.stderr,p.stderr
(H/"UNITTEST_DCHR_EU.log").write_text(p.stdout+p.stderr,encoding="utf-8")
assert (sha(M),sha(STATUS))==before
out={"status":"PASS","rational_identity_checks":checks,"unittest_passed":25,
 "source_status_v86_sha256":before[1],"source_literature_v44_sha256":before[0],
 "source_files_unchanged":True,"full_primary_signoff":False,
 "synthetic_fixture_only":True,"production_modified":False}
(H/"QA_INDEPENDENT_DCHR_EU.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(json.dumps(out,ensure_ascii=False))
