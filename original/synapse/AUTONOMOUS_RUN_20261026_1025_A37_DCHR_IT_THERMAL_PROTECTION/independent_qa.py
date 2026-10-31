"""Independent Decimal replay and provenance check for A37, no import of model."""
import csv,hashlib,json
from decimal import Decimal, getcontext
from pathlib import Path
getcontext().prec=32
HERE=Path(__file__).resolve().parent
A36B=HERE.parent/"AUTONOMOUS_RUN_20261026_0752_A36B_REJECT_N1_ENVELOPE"
V08=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\pool_measurement_v08\sim_v08_zdravy_SK.csv")
def D(x):return Decimal(str(x))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def close(a,b,tol="0.000005"):
    if abs(D(a)-D(b))>D(tol):
        raise AssertionError(f"DECIMAL_MISMATCH {a} vs {b}")
def main():
    meta=json.loads((HERE/"RESULTS_A37.json").read_text(encoding="utf8"))
    assert meta["physical_release_allowed"] is False
    assert sha(V08)==meta["source_v08_sha256"]
    with V08.open(encoding="utf-8-sig",newline="") as f:
        raw=list(csv.DictReader(f))
    assert len(raw)==672
    n=0;checks=0
    for key,info in meta["cases"].items():
        label,policy=key.split("/")
        cap=D(info["reject_capacity_after_fault_kW"])*1000
        path=HERE/info["trace"]
        assert sha(path)==info["trace_sha256"]
        with path.open(encoding="utf8",newline="") as f:
            rows=list(csv.DictReader(f))
        assert len(rows)==len(raw)
        prev_t=D("30");prev_shed=D("0");alarms=0;energy_unhandled=D("0");energy_shed=D("0");max_t=D("30")
        for r,src in zip(rows,raw):
            h=D(r["cas_h"])
            assert h==D(src["cas_h"])
            effective_cap=D("330000") if h<D("24") else cap
            close(r["fault_capacity_W"],effective_cap)
            required=D(r["reject_required_after_shed_W"])+D(r["shed_W"])
            shed=D(r["shed_W"]);reject=D(r["reject_actual_W"]);unhandled=D(r["unhandled_W"])
            dc=D(src["Q_DC_eff_W"])
            assert shed>=0 and shed<=required+D("0.000001") and shed<=dc+D("0.000001")
            close(required,shed+reject+unhandled)
            close(reject,min(required-shed,effective_cap))
            close(unhandled,max(D("0"),required-shed-effective_cap))
            if policy=="no_shed" or h<D("24"):
                close(shed,0)
            else:
                assert shed<=dc*D("0.40")+D("0.000005")
                if policy=="ramp15k_40pct":
                    assert shed-prev_shed<=D("15000.000005")
            passive=max(D("0"),D("2000")*(prev_t-D("30")))
            expected=max(D("30"),prev_t+D("900")*(unhandled-passive)/D("8000000"))
            close(r["passive_W"],passive)
            close(r["T_IT_start_C"],prev_t)
            close(r["T_IT_next_C"],expected,"0.000001")
            alarm=int(expected>=D("42"))
            assert int(r["alarm_next"])==alarm
            alarms+=alarm
            if h>=D("24"):
                energy_unhandled+=unhandled*D("0.25")/1000
                energy_shed+=shed*D("0.25")/1000
            max_t=max(max_t,expected)
            prev_t=expected;prev_shed=shed;n+=1;checks+=13
        assert alarms==info["alarm_intervals"]
        close(info["unhandled_kWh"],energy_unhandled,"0.000001")
        close(info["shed_kWh"],energy_shed,"0.000001")
        close(info["max_T_IT_C"],max_t,"0.000001")
    old=json.loads((A36B/"RESULTS_N1.json").read_text(encoding="utf8"))
    labels={"both":"both_available","main_only":"main_only","backup_only":"backup_only","neither":"neither_available"}
    for label,target in labels.items():
        expected=old["scenarios"]["both_off"][target]["unhandled_kWh"]
        close(meta["cases"][label+"/no_shed"]["unhandled_kWh"],expected,"0.000002")
    evidence={"status":"PASS","traces":len(meta["cases"]),"rows":n,
              "decimal_invariant_checks":checks,"legacy_N1_energy_crosschecks":4,
              "source_sha256":meta["source_v08_sha256"],
              "physical_release_allowed":False}
    (HERE/"INDEPENDENT_QA.json").write_text(json.dumps(evidence,indent=2)+"\n",encoding="utf8")
    print(json.dumps(evidence))
if __name__=="__main__":
    main()
