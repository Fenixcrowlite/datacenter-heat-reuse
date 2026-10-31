import csv,json,hashlib,pathlib,math
root=pathlib.Path(__file__).resolve().parents[2]
out=root/"results"/"pool_safety_v05"
j=json.loads((out/"resultaty_v05_SK.json").read_text(encoding="utf8"))
checks=0
for s in j["scenarios"]:
 with (out/("scenar_"+s["scenar"]+"_SK.csv")).open(encoding="utf-8-sig") as f:
  data=[{k:float(v) for k,v in row.items()} for row in csv.DictReader(f)]
 assert len(data)==672
 blocked=0
 for r in data:
  assert all(math.isfinite(v) for v in r.values())
  assert abs(r["Q_DC_W"]-r["Q_priamy_HX_W"]-r["Q_DC_TC_W"]-r["Q_reject_W"])<1e-5
  assert abs(r["Q_bazen_W"]-r["Q_priamy_HX_W"]-r["Q_TC_bazen_W"])<1e-5
  assert 10<r["T_bazen_C"]<=27.75001
  if r["blokovanie"]>0.5:
   assert r["Q_bazen_W"]==0
   blocked+=1
  checks+=5
 assert blocked==s["blocked_samples"]
assert len(j["scenarios"])==7
(out/"QA_V05_SK.json").write_text(json.dumps({"status":"PASS","checks":checks},indent=2))
print("QA_V05_PASS",checks)

additional=0
detail=[]
for s in j["scenarios"]:
 with (out/("scenar_"+s["scenar"]+"_SK.csv")).open(encoding="utf-8-sig") as f:
  rows=[{k:float(v) for k,v in r.items()} for r in csv.DictReader(f)]
 prevT=16.0
 prevLatch=False
 goodResets=0
 for k,r in enumerate(rows):
  b1,b2=r["bias1_K"],r["bias2_K"]
  bad=(abs(b1-b2)>0.35 or abs(b1)>0.45 or abs(b2)>0.45 or
       r["prietok_ok"]<0.5 or r["emergency_stop"]>0.5 or
       prevT+b1>=27.7 or prevT+b2>=27.7)
  release=r["manualny_reset"]>0.5 and prevT<=27.65 and not bad
  expected=bad or (prevLatch and not release)
  assert (r["blokovanie"]>0.5)==expected,(s["scenar"],k,"latch")
  if r["reset_uspesny"]>0.5:
   assert release and prevLatch and not expected
   goodResets+=1
  prevLatch=expected
  prevT=r["T_bazen_C"]
  additional+=2
 assert goodResets==s["manual_reset_events"]
 detail.append({"scenario":s["scenar"],"accepted_manual_resets":goodResets})
checks+=additional
(out/"QA_V05_SK.json").write_text(json.dumps({"status":"PASS","checks":checks,"cases":detail},indent=2),encoding="utf8")
print("QA_V05_LATCH_PASS",additional,"additional checks",checks,"total")
