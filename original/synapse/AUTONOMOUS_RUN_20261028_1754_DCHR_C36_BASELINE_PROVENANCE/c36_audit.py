"""C36 read-only provenance and 8760-hour storage contract audit, stdlib only."""
from __future__ import annotations
import csv, datetime as dt, hashlib, json, re, sqlite3
from decimal import Decimal, getcontext
from pathlib import Path
getcontext().prec = 36
H=Path(__file__).resolve().parent
SCC=H.parent.parent
DCHR=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")
MAT=DCHR/"matlab"
RES=DCHR/"results"
TASK="scc-2aab24704c2bd0"
D=lambda s: Decimal(str(s))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def guard():
    for root in (SCC,SCC/"recovery",SCC/"Continuity",DCHR,H):
        for n in ("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.flag",".STOP",".PAUSE"):
            if (root/n).exists(): raise RuntimeError("STOP_ACTIVE "+str(root/n))
    with sqlite3.connect(f"file:{(SCC/'tasks.sqlite3').as_posix()}?mode=ro",uri=True) as db:
        assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
        t=db.execute("SELECT project,status,worker_pid FROM tasks WHERE id=?",(TASK,)).fetchone()
        if t is None or t[0]!="DataCenter Heat Reuse" or t[1] in ("done","cancelled") or t[2] is not None:raise RuntimeError("TASK_NOT_ELIGIBLE "+str(t))
    return t
def close(a,b,tol=D("0.00000005")):
    if abs(a-b)>tol:raise AssertionError(f"balance {a} vs {b} delta {a-b}")
def audit_csv(name, scenario, source_file, source_model):
    p=RES/name
    summary=next(r for r in csv.DictReader((RES/source_file).open(encoding="utf-8-sig",newline="")) if r["Scenario"]==scenario)
    cfg=dict(cap=D("100"),dt=D("1"),loss=D("0.0001"),charge_limit=D("5"),discharge_limit=D("5"),eta_charge=D("0.95"),eta_discharge=D("0.95"))
    prev=D("0"); rows=0; gas=D(0); hp_e=D(0); demand=D(0); charged=D(0); discharged=D(0); loss=D(0)
    max_error=D(0); positive_charge=0; positive_discharge=0; boundary_checks=0
    with p.open(encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f):
            rows+=1
            E=D(row["Storage_E_MWh"]); qch=D(row["Storage_Charge_MW"]); qdis=D(row["Storage_Discharge_MW"])
            qneed=D(row["Heat_Demand_MW"]); qpot=D(row["HP_Heat_MW"]); qused=D(row["HP_Heat_Used_MW"])
            qgas=D(row["Gas_Heat_MW"]); qcurt=D(row["Curtailed_HP_Heat_MW"]); pelec=D(row["HP_Electric_MW"])
            close(E,prev)
            post=max(D(0),E*(1-cfg["loss"]*cfg["dt"]))
            surplus=max(D(0),qpot-qneed); deficit=max(D(0),qneed-qpot)
            expected_charge=min(surplus,cfg["charge_limit"],max(D(0),cfg["cap"]-post)/(cfg["eta_charge"]*cfg["dt"])) if surplus>0 else D(0)
            expected_dis=min(deficit,cfg["discharge_limit"],post*cfg["eta_discharge"]/cfg["dt"]) if deficit>0 else D(0)
            close(qch,expected_charge); close(qdis,expected_dis)
            close(qused,min(qpot,qneed)+qch)
            close(qgas,max(D(0),qneed-min(qpot,qneed)-qdis))
            close(qcurt,max(D(0),qpot-qused))
            close(qneed,qused-qch+qdis+qgas)
            if source_model=="v1": close(pelec,qused/D(row["COP"]))
            if qch>0:positive_charge+=1
            if qdis>0:positive_discharge+=1
            if qch>0 and qdis>0:raise AssertionError("SIMULTANEOUS_CHARGE_DISCHARGE")
            nxt=post+cfg["eta_charge"]*qch*cfg["dt"]-qdis*cfg["dt"]/cfg["eta_discharge"]
            if not -D("0.00000005")<=nxt<=cfg["cap"]+D("0.00000005"):raise AssertionError("CAPACITY")
            max_error=max(max_error,abs(E-prev))
            loss+=E-post
            prev=max(D(0),nxt)
            gas+=qgas; hp_e+=pelec; demand+=qneed; charged+=qch; discharged+=qdis
            boundary_checks+=8
    if rows!=8760:raise AssertionError(f"EXPECTED_8760 {rows}")
    close(gas,D(summary["GasHeat_MWh"]),D("0.000001"))
    close(hp_e,D(summary["HPElectric_MWh"]),D("0.000001"))
    close(demand,D(summary["HeatDemand_MWh"]),D("0.000001"))
    close(demand-gas,D(summary["ReusedHeat_MWh"]),D("0.000001"))
    close(D(0)+cfg["eta_charge"]*charged-discharged/cfg["eta_discharge"]-loss,prev,D("0.000001"))
    return {"file":name,"sha256":sha(p),"summary_file":source_file,"scenario":scenario,"rows":rows,
            "capacity_mwh":100,"initial_energy_mwh":0,"final_energy_mwh":float(prev),
            "gas_heat_mwh":float(gas),"hp_electric_mwh":float(hp_e),"heat_demand_mwh":float(demand),
            "charged_input_mwh":float(charged),"discharged_to_network_mwh":float(discharged),
            "storage_losses_mwh":float(loss),"charge_hours":positive_charge,"discharge_hours":positive_discharge,
            "balance_checks":boundary_checks,"storage_law":"E_next=E*(1-loss)+0.95*Qcharge-Qdischarge/0.95; 1h",
            "max_pre_step_energy_residual_mwh":float(max_error)}
def run():
    task=guard()
    files={"v1_driver":MAT/"run_experiment.m","v2_driver":MAT/"run_experiment_v2.m",
           "v1_config":MAT/"default_config.m","v2_config":MAT/"default_config_v2.m",
           "v1_sim":MAT/"+dchr"/"simulate_system.m","v2_sim":MAT/"+dchr"/"simulate_system_v2.m",
           "v2_storage":MAT/"+dchr"/"+components"/"storage_step.m",
           "v1_csv":RES/"warm45_storage100_timeseries.csv","v2_csv":RES/"best_scenario_v2_timeseries.csv",
           "v1_summary":RES/"scenario_summary.csv","v2_summary":RES/"scenario_summary_v2.csv"}
    for k,p in files.items():
        if not p.is_file():raise FileNotFoundError(f"{k}: {p}")
    s={k:p.read_text(encoding="utf-8-sig") for k,p in files.items() if p.suffix==".m"}
    assert "'storage_MWh',{0,0,0,100}" in s["v1_driver"]
    assert "writetable(allOut{4}" in s["v1_driver"]
    assert "'storage',{0,0,0,100,100}" in s["v2_driver"]
    assert "'Warm45_Storage100','Liquid35_LowTempDH'" in s["v2_driver"]
    assert "writetable(O{end}" in s["v2_driver"]
    assert "cfg.storage.capacity_MWh = 50.0" in s["v1_config"]
    assert "cfg.storage.initial_soc = 0.00" in s["v1_config"]
    assert "cfg.storage.loss_fraction_per_h = 1.0e-4" in s["v1_config"]
    assert "cfg.storage.eta_charge = 0.95" in s["v1_config"]
    assert "cfg.storage.eta_discharge = 0.95" in s["v1_config"]
    assert "st=dchr.components.storage_step(E(k),surplus,deficit,cfg)" in s["v2_sim"]
    v1=audit_csv("warm45_storage100_timeseries.csv","Warm45_Storage100","scenario_summary.csv","v1")
    v2=audit_csv("best_scenario_v2_timeseries.csv","Liquid35_LowTempDH","scenario_summary_v2.csv","v2")
    summary=list(csv.DictReader((RES/"scenario_summary_v2.csv").open(encoding="utf-8-sig",newline="")))
    best_coverage=max(summary,key=lambda x:D(x["Coverage"]))
    last=summary[-1]
    assert best_coverage["Scenario"]=="Warm45_Storage100" and last["Scenario"]=="Liquid35_LowTempDH"
    assert D(last["GasHeat_MWh"])>D(best_coverage["GasHeat_MWh"])
    result={"scope":"DCHR_C36_100MWH_PROVENANCE_AND_MISLABEL",
      "observed_local":dt.datetime.now().astimezone().isoformat(timespec="seconds"),
      "task_id":TASK,"task_status":task[1],"source_hashes":{k:sha(p) for k,p in files.items()},
      "v1_100mwh":{"scenario":"Warm45_Storage100","driver":"run_experiment.m","model":"simulate_system","storage":"energy-only 1-node, no tank temperature, no stratification","trace":v1},
      "v2_100mwh":{"scenario":"Liquid35_LowTempDH","driver":"run_experiment_v2.m","model":"simulate_system_v2","storage":"energy-only 1-node, no tank temperature, no stratification","trace":v2},
      "v2_timeseries_filename":"best_scenario_v2_timeseries.csv",
      "v2_timeseries_actual_scenario":last["Scenario"],
      "v2_best_coverage_scenario":best_coverage["Scenario"],
      "v2_last_coverage":float(D(last["Coverage"])),
      "v2_best_coverage":float(D(best_coverage["Coverage"])),
      "v2_last_gas_mwh":float(D(last["GasHeat_MWh"])),
      "v2_best_gas_mwh":float(D(best_coverage["GasHeat_MWh"])),
      "v2_gas_difference_mwh":float(D(last["GasHeat_MWh"])-D(best_coverage["GasHeat_MWh"])),
      "finding":"The file called best_scenario_v2_timeseries.csv is the LAST scenario Liquid35_LowTempDH (100 MWh), not the max-coverage scenario Warm45_Storage100. Previous C29-C35 annual interpretations using this CSV must retain Liquid35_LowTempDH provenance; v85 10 MWh tests are a separate contract.",
      "model_limit":"100 MWh is an assumed energy-only capacity in early MATLAB scenario code, not validated physical volume or temperature; cannot claim v85 parity.",
      "matlab_executed":False,"source_modified":False,"primary_source_signoffs":0,
      "next_step":"Produce an explicitly named Warm45_Storage100 v2 time series via an isolated MATLAB run, then compare both 100 MWh scenarios and v85 10 MWh at matching inputs. Do not rename/rewrite the shared existing CSV."}
    (H/"C36_PROVENANCE_RESULTS.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    note=f"""# DCHR C36: pôvod 100 MWh a nesprávne označený časový rad

## Preukázané zo zdrojov
Staršie skripty `run_experiment.m` a `run_experiment_v2.m` explicitne nastavujú `capacity_MWh = 100` pre scenáre. Zásobník je **jednou energetickou veličinou E [MWh]** so stratami, limitmi nabíjania/vybíjania a účinnosťou 0,95; bez dynamickej teploty vody a bez stratifikácie. Toto je pôvod hypotézy 100 MWh, nie overená fyzická nádrž.

## Kritická chyba označenia
`run_experiment_v2.m` zapisuje `O{{end}}` ako `best_scenario_v2_timeseries.csv`. Posledný scenár je **Liquid35_LowTempDH**, nie Warm45_Storage100. Má pokrytie **{100*result['v2_last_coverage']:.3f} %** a potrebuje **{result['v2_last_gas_mwh']:.3f} MWh** plynového tepla. Najvyššie pokrytie v uloženej tabuľke má **Warm45_Storage100**: **{100*result['v2_best_coverage']:.3f} %**, plyn **{result['v2_best_gas_mwh']:.3f} MWh**. Rozdiel v plynovom teple je **{result['v2_gas_difference_mwh']:.3f} MWh**.

## Nezávislé overenie
Oba uložené hodinové CSV majú po **8760** riadkov. Počas každého kroku sme z CSV zrekonštruovali zákon energie zásobníka, nabíjacie/vybíjacie limity, bilanciu tepla, obmedzenie 100 MWh a súlad ročných súčtov s tabuľkami scenárov. Originálne zdrojové súbory boli iba čítané; MATLAB sa nespúšťal.

## Hranica interpretácie
Uložené testy Stateflow v85 s kapacitou **10 MWh** sú iný kontrakt. Výpočty C29–C35 nad `best_scenario_v2_timeseries.csv` treba označovať ako **Liquid35_LowTempDH**, nie ako automaticky najlepší scenár a nie ako v85. Vzniká požiadavka na reprodukovateľný export **Warm45_Storage100** pre korektné porovnanie.
"""
    (H/"C36_ENGINEERING_NOTE_SK.md").write_text(note,encoding="utf-8")
    guard()
    print(json.dumps({"status":"PASS","v1_rows":v1["rows"],"v2_rows":v2["rows"],"balance_checks":v1["balance_checks"]+v2["balance_checks"],"v2_actual":last["Scenario"],"v2_best_coverage":best_coverage["Scenario"],"gas_difference_mwh":result["v2_gas_difference_mwh"]},ensure_ascii=False))
if __name__=="__main__":run()
