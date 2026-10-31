"""A63 independent QA: do not import production generator."""
import csv
from decimal import Decimal, getcontext
import hashlib
import json
from pathlib import Path
import re
import subprocess

getcontext().prec = 35
ROOT = Path(__file__).resolve().parent
A62 = ROOT.parent / "AUTONOMOUS_RUN_20261027_1405_A62_SIGNED_LOSS_EXPORT"
FIELDS = ("time_s","T_pool_C","Q_pool_W","Q_pool_loss_W","Q_pool_net_W",
          "E_pool_input_cum_J","E_pool_signed_loss_cum_J",
          "E_pool_stored_cum_J","state_residual_W")
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    html = (ROOT / "OUTPUT" / "dashboard.html").read_text(encoding="utf-8")
    assert "https://" not in html and html.count("http://") == 1
    assert "<script src=" not in html and "<link href=" not in html
    match = re.search(r'<script type="application/json" id="payload">(.*?)</script>', html, re.S)
    assert match
    data = json.loads(match.group(1))
    assert data["metrics"] == json.loads((ROOT / "OUTPUT" / "metrics.json").read_text(encoding="utf-8"))
    script = re.search(r"<script>\s*(.*?)\s*</script>", html, re.S)
    assert script
    js = ROOT / "QA_SCRIPT_A63.js"
    js.write_text(script.group(1) + "\n", encoding="utf-8")
    checked = subprocess.run(["node", "--check", str(js)], capture_output=True, text=True)
    assert checked.returncode == 0, checked.stderr
    checks = 0
    results = {}
    for key, dirname in (("v08","OUTPUT_V08_SIGNED"),("v09","OUTPUT_V09_SIGNED")):
        path = A62 / dirname / "analysis_with_signed_losses.csv"
        summary = json.loads((A62 / dirname / "summary.json").read_text(encoding="utf-8"))
        assert digest(path) == summary["analysis_with_signed_losses_sha256"]
        assert data["metrics"][key]["source_csv_sha256"] == digest(path)
        with path.open(encoding="utf-8",newline="") as f:
            rows = list(csv.DictReader(f))
        plot = data["series"][key]["rows"]
        assert len(rows) == len(plot) == 672
        ein = eloss = gain = Decimal(0)
        negative = 0
        for row, shown in zip(rows,plot):
            for k, displayed in zip(FIELDS, shown):
                expected = Decimal(row[k])
                actual = Decimal(str(displayed))
                tol = max(Decimal("0.000001"),abs(expected)*Decimal("0.00000000000001"))
                assert abs(actual-expected) <= tol, (key,k,expected,actual)
                checks += 1
            q,loss = Decimal(row["Q_pool_W"]),Decimal(row["Q_pool_loss_W"])
            ein += q*900
            eloss += loss*900
            if loss < 0:
                gain -= loss*900
                negative += 1
        metrics = data["metrics"][key]
        assert negative == metrics["negative_loss_rows"] == 91
        for label,expected in (("input_MWh",ein/Decimal(3600000000)),
                               ("signed_loss_MWh",eloss/Decimal(3600000000)),
                               ("ambient_gain_MWh",gain/Decimal(3600000000))):
            assert abs(Decimal(str(metrics[label]))-expected) < Decimal("0.000000001")
            checks += 1
        assert abs(ein-eloss-Decimal(str(metrics["stored_MWh"]))*Decimal(3600000000)) < Decimal("0.2")
        assert metrics["physical_release"] is False and metrics["source_kind"] == "derived_simulation"
        results[key] = {"rows":len(rows),"checks":len(rows)*len(FIELDS)+3,
                        "negative_loss_rows":negative,"input_MWh":float(ein/Decimal(3600000000)),
                        "stored_MWh":metrics["stored_MWh"],"source_sha256":digest(path)}
    report = {"qa":"PASS","source_kind":"derived_simulation","physical_release":False,
              "decimal_field_checks":checks,"node_js_syntax":"PASS",
              "scenarios":results,"dashboard_sha256":digest(ROOT/"OUTPUT"/"dashboard.html")}
    (ROOT/"INDEPENDENT_QA_A63.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"qa":report["qa"],"decimal_checks":checks,"node_js_syntax":"PASS"}))


if __name__ == "__main__":
    main()
