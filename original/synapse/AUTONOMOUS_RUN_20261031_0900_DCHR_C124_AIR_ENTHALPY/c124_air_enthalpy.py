"""C124 synthetic 15-minute room moist-air energy/mass state, no shared runtime edits."""
import csv,gzip,hashlib,json,math,os
from pathlib import Path
from collections import defaultdict
D=Path(__file__).resolve().parent; R=D.parent; S=R.parent
SOURCE=R/"AUTONOMOUS_RUN_20261031_0446_DCHR_C116_RH_EVAP_COUPLED"/"C116_TWO_WAY_HOURLY.csv.gz"
PIN="6f8fa6a7c8d6927811e02b3c8d3a970a3f6216022a7d03ed012e26da3b14e6bf"
TASK="scc-2aab24704c2bd0"
M=3540.; P=101.325; EPS=.62198; CP_DA=1.006; CP_V=1.86; HFG=2501.; CP_L=4.186
DT_S=900.; VENT_KG_DRY=885.; TARGET_T=29.; SUPPLY_T=26.; SUPPLY_RH=.55
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
FIELDS=("scenario","time","quarter","pool_T_C","T0_C","T1_C","w0","w1","RH0","RH1",
        "evap_kg","vent_vapor_kg","dehum_kg","humid_kg","condensate_kg","storage_kg",
        "mass_residual_kg","H0_kJ","H1_kJ","evap_kJ","vent_kJ","HVAC_kJ",
        "dehum_out_kJ","humid_in_kJ","condensate_out_kJ","energy_residual_kJ")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def guard():
    for root in (D,R,S,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
        for f in FLAGS:
            if (root/f).exists():raise RuntimeError("STOP_ACTIVE "+str(root/f))
def sat(t):
    if not math.isfinite(t) or not -50<t<80:raise ValueError("INVALID_T")
    return .61094*math.exp(17.625*t/(t+243.04))
def w_from(t,rh):
    if not math.isfinite(rh) or not 0<=rh<=1:raise ValueError("INVALID_RH")
    pv=rh*sat(t)
    return EPS*pv/(P-pv)
def rh_from(t,w):
    if not math.isfinite(w) or w<0:raise ValueError("INVALID_W")
    return (P*w/(EPS+w))/sat(t)
def h(t,w):
    return CP_DA*t+w*(HFG+CP_V*t)
def H(t,mv):
    return M*h(t,mv/M)
def temperature(energy,mv):
    return (energy-mv*HFG)/(M*CP_DA+mv*CP_V)
def condensation(energy,mv):
    t=temperature(energy,mv)
    if rh_from(t,mv/M)<=1+1e-12:return (0.,t,energy)
    lo,hi=0.,mv
    for _ in range(65):
        mid=(lo+hi)/2
        tm=(energy-(mv-mid)*HFG)/(M*CP_DA+(mv-mid)*CP_V+mid*CP_L)
        if rh_from(tm,(mv-mid)/M)>1:lo=mid
        else:hi=mid
    c=hi
    t=(energy-(mv-c)*HFG)/(M*CP_DA+(mv-c)*CP_V+c*CP_L)
    return (c,t,energy-c*CP_L*t)
def step(t,w,tw,evap,cap_kg_h,heat_cap_kw):
    if not all(map(math.isfinite,(t,w,tw,evap,cap_kg_h,heat_cap_kw))):raise ValueError("NONFINITE")
    if evap<0 or cap_kg_h<0 or heat_cap_kw<0:raise ValueError("NEGATIVE_INPUT")
    h0=H(t,M*w); supply_w=w_from(SUPPLY_T,SUPPLY_RH)
    vent=VENT_KG_DRY*(supply_w-w)
    target=M*w_from(TARGET_T,.55)
    projected=M*w+evap+vent
    dehum=min(cap_kg_h*.25,max(0.,projected-target))
    humid=min(cap_kg_h*.25,max(0.,target-projected))
    mv=projected-dehum+humid
    q_evap=evap*(2501.-2.361*tw)
    q_vent=VENT_KG_DRY*(h(SUPPLY_T,supply_w)-h(t,w))
    q_hvac=max(-heat_cap_kw,min(heat_cap_kw,5.*(TARGET_T-t)))*DT_S
    hv=HFG+CP_V*t
    q_dehum=dehum*hv; q_humid=humid*hv
    provisional=h0+q_evap+q_vent+q_hvac-q_dehum+q_humid
    cond,t1,h1=condensation(provisional,mv)
    mv1=mv-cond; w1=mv1/M
    storage=mv1-M*w
    mass_res=storage-(evap+vent-dehum+humid-cond)
    q_cond=cond*CP_L*t1
    energy_res=h1-(h0+q_evap+q_vent+q_hvac-q_dehum+q_humid-q_cond)
    if abs(mass_res)>1e-7 or abs(energy_res)>1e-6:raise AssertionError("BALANCE")
    if not -20<t1<70 or not 0<=rh_from(t1,w1)<=1+1e-8:raise AssertionError("STATE_BOUND")
    return (t1,w1,evap,vent,dehum,humid,cond,storage,mass_res,h0,h1,
            q_evap,q_vent,q_hvac,q_dehum,q_humid,q_cond,energy_res)
def selftest():
    assert abs(rh_from(29,w_from(29,.55))-.55)<1e-12
    assert abs(temperature(H(29,M*.01),M*.01)-29)<1e-12
    assert condensation(H(29,M*.01),M*.01)[0]==0
    e=H(29,M*w_from(29,1.0))+1000
    c,t,he=condensation(e,M*w_from(29,1.0)+5)
    assert c>0 and abs(he-(e-c*CP_L*t))<1e-7
    assert abs(step(29,w_from(29,.55),28,1,5,5)[8])<1e-7
    for invalid in (-1,float("nan")):
        try:step(29,w_from(29,.55),28,invalid,5,5)
        except ValueError:pass
        else:raise AssertionError("INVALID_ACCEPTED")
    return 7
def main():
    guard()
    if sha(SOURCE)!=PIN:raise RuntimeError("SOURCE_SHA_DRIFT")
    tests=selftest()
    scenarios={(cap,heat):{"t":TARGET_T,"w":w_from(TARGET_T,.55),"n":0,"s":defaultdict(float),
                             "min_t":1e9,"max_t":-1e9,"min_rh":1e9,"max_rh":-1e9}
               for cap in (5.,45.66) for heat in (5.,15.)}
    out=D/"C124_QUARTER_AIR.csv.gz";tmp=D/"C124_QUARTER_AIR.partial.csv.gz"
    summary=D/"C124_SUMMARY.json";meta=D/"C124_METADATA.json"
    if any(x.exists() for x in (out,tmp,summary,meta)):raise RuntimeError("OUTPUT_EXISTS")
    hours=rows=0
    with gzip.open(SOURCE,"rt",encoding="utf-8",newline="") as f, gzip.open(tmp,"xt",encoding="utf-8",newline="",compresslevel=4) as g:
        writer=csv.writer(g);writer.writerow(FIELDS)
        for r in csv.DictReader(f):
            if r["policy"]!="water_first" or r["control"]!="ideal":continue
            if hours%720==0:guard()
            stamp=r["time"];evap=float(r["evap_kg"]);tw=float(r["pool_start_C"])
            for (cap,heat),st in scenarios.items():
                name=f"dehum{cap:g}_hvac{heat:g}"
                for quarter,weight in enumerate((1.,0.,0.,0.)):
                    t0,w0=st["t"],st["w"]
                    x=step(t0,w0,tw,evap*weight,cap,heat)
                    t1,w1=x[:2]
                    vals=(name,stamp,quarter,tw,t0,t1,w0,w1,rh_from(t0,w0),rh_from(t1,w1),*x[2:])
                    writer.writerow([z if isinstance(z,str) else str(z) if isinstance(z,int) else f"{z:.12f}" for z in vals])
                    st["t"],st["w"]=t1,w1
                    st["n"]+=1;rows+=1
                    st["min_t"]=min(st["min_t"],t1);st["max_t"]=max(st["max_t"],t1)
                    rh=rh_from(t1,w1)
                    st["min_rh"]=min(st["min_rh"],rh);st["max_rh"]=max(st["max_rh"],rh)
                    st["s"]["high65_quarters"]+=int(rh>.65)
                    st["s"]["low45_quarters"]+=int(rh<.45)
                    st["s"]["condensate_kg"]+=x[6]
                    st["s"]["hvac_abs_kWh"]+=abs(x[13])/3600
                    st["s"]["mass_abs_residual"]+=abs(x[8])
                    st["s"]["energy_abs_residual_kJ"]+=abs(x[-1])
            hours+=1
    assert hours==8760 and rows==140160
    guard();os.replace(tmp,out)
    summary_data={f"dehum{cap:g}_hvac{heat:g}":{"quarters":st["n"],"min_T_C":st["min_t"],
      "max_T_C":st["max_t"],"min_RH":st["min_rh"],"max_RH":st["max_rh"],
      **dict(st["s"])} for (cap,heat),st in scenarios.items()}
    summary.write_text(json.dumps(summary_data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    m={"schema":"C124_SYNTHETIC_15MIN_AIR_ENTHALPY_V1","task_id":TASK,"hours":hours,
       "quarters":rows,"scenarios":len(scenarios),"selftests":tests,
       "source_sha256":PIN,"data_sha256":sha(out),"summary_sha256":sha(summary),
       "room_dry_air_kg":M,"supply_T_C":SUPPLY_T,"supply_RH":SUPPLY_RH,
       "vent_dry_air_kg_per_quarter":VENT_KG_DRY,
       "synthetic":True,"field_validated":False,"source_signoffs_added":0,
       "limitations":["C116 pool temperature and evaporation are prescribed; no return coupling.",
       "Preconditioned supply at 26 C and 55% RH is synthetic, not real weather/coil output.",
       "Dehumidifier removes vapor enthalpy; no vendor COP, heat recovery or compressor model.",
       "HVAC thermostat is ideal proportional with capped heat/cooling, no hardware dynamics.",
       "Instant saturation condensation; no wall thermal mass or sensor lag.",
       "Mass and moist-air enthalpy conservation are accounting identities, not field validation."]}
    meta.write_text(json.dumps(m,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS","hours":hours,"quarters":rows,"selftests":tests,
       "sha256":m["data_sha256"],"summary":summary_data},indent=2))
if __name__=="__main__":main()
