"""Independent A64 QA: direct Decimal recomputation from CSV, no import of A64 module."""
import csv,hashlib,json
from decimal import Decimal as D,getcontext
from pathlib import Path
getcontext().prec=45
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
MWH=D(3600000000)
KEYS=("Q_DC_W","Q_reject_W","Q_pool_W","Q_DH_W","P_HP_W")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    report=json.loads((HERE/"OUTPUT/comparison.json").read_text(encoding="utf-8"))
    assert report["schema"]=="a64.1"
    checks=0
    for v in ("V08","V09"):
        a=ROOT/"AUTONOMOUS_RUN_20261027_1250_A60_SCADA_DERIVED_EXPORT"/f"OUTPUT_{v}_DERIVED"
        b=ROOT/"AUTONOMOUS_RUN_20261027_1405_A62_SIGNED_LOSS_EXPORT"/f"OUTPUT_{v}_SIGNED"
        with (a/"analysis_timeseries.csv").open(newline="",encoding="utf-8") as f: x=list(csv.DictReader(f))
        with (b/"analysis_with_signed_losses.csv").open(newline="",encoding="utf-8") as f: y=list(csv.DictReader(f))
        assert len(x)==len(y)==672
        r=report["scenarios"][v]
        assert r["a60_csv_sha256"]==sha(a/"analysis_timeseries.csv")
        assert r["a62_csv_sha256"]==sha(b/"analysis_with_signed_losses.csv")
        for i,(u,w) in enumerate(zip(x,y)):
            assert D(u["time_s"])==D(w["time_s"])==D(i*900)
            checks+=1
            for k in KEYS:
                assert D(u[k])==D(w[k]);checks+=1
        for k in KEYS:
            values=[D(row[k]) for row in x]
            # Direct endpoint-weight trapezoid, independent from A64 pairwise sum.
            trapez=(values[0]/2+sum(values[1:-1])+values[-1]/2)*900
            discrete=sum(values)*900
            d=discrete-trapez
            got=r["channels"][k]
            assert D(got["trapezoid_MWh"])*MWH==trapez
            assert D(got["discrete_MWh"])*MWH==discrete
            assert D(got["discrete_minus_trapezoid_kWh"])*D(3600000)==d
            assert d==(values[0]+values[-1])*450
            checks+=4
        assert abs(D(y[-1]["E_pool_input_cum_J"])-D(r["channels"]["Q_pool_W"]["discrete_MWh"])*MWH)<D(".01")
        checks+=1
    page=(HERE/"OUTPUT/comparison.html").read_text(encoding="utf-8")
    assert "DERIVED SIMULATION" in page and "physical" not in page.lower()
    checks+=1
    result={"status":"PASS","decimal_checks":checks,"versions":["V08","V09"],"physical_release":False,"source_kind":"derived_simulation","html_sha256":sha(HERE/"OUTPUT/comparison.html")}
    (HERE/"INDEPENDENT_QA_A64.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result))
if __name__=="__main__":main()
