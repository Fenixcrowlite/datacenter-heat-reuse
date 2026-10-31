"""C34: read-only saved Simulink v85 thermal inventory contract audit.
No MATLAB execution; never edits OneDrive models or shared runtime.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import re
import sqlite3
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCC = HERE.parent.parent
DCHR = Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")
MAT = DCHR / "matlab" / "simulink"
SLX = MAT / "DCHR_Electrical_Dispatch_Stateflow_v85.slx"
POLICY = MAT / "electrical_policy_v85.m"
KERNEL = MAT / "earliest_dispatch_kernel_v75.m"
BUILDER = MAT / "build_electrical_ceiling_v85.m"
SPEC = DCHR / "results" / "reachable_cap_v85_20261013T110959_296758Z" / "spec.json"
STATUS = DCHR / "STATUS_v86.json"
C33 = HERE.parent / "AUTONOMOUS_RUN_20261028_1601_DCHR_100MWH_TEMP_GATE" / "C33_100MWH_GATE_RESULTS.json"
MODEL_SHA = "2a9de22c0c55e8c4a87f7b0e0cfe9cd97db08c991f09d98361b009de310adde7"
TASK = "scc-2aab24704c2bd0"

def sha(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def guard():
    for root in (SCC, SCC / "recovery", SCC / "Continuity", DCHR, HERE):
        for name in ("STOP", "STOP.txt", "STOP.flag", "PAUSE", "PAUSE.flag", ".STOP", ".PAUSE"):
            if (root / name).exists():
                raise RuntimeError("STOP_ACTIVE: " + str(root / name))
    with sqlite3.connect(f"file:{(SCC/'tasks.sqlite3').as_posix()}?mode=ro", uri=True) as db:
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("REGISTRY_INTEGRITY_FAIL")
        row = db.execute("SELECT project,status,worker_pid FROM tasks WHERE id=?", (TASK,)).fetchone()
        if not row or row[0] != "DataCenter Heat Reuse" or row[1] in ("done", "cancelled") or row[2] is not None:
            raise RuntimeError("TASK_NOT_ELIGIBLE " + str(row))
        return {"project": row[0], "status": row[1], "worker_pid": row[2]}

def audit():
    task = guard()
    paths = {"slx": SLX, "policy": POLICY, "kernel": KERNEL, "builder": BUILDER, "spec": SPEC, "status": STATUS, "c33": C33}
    for name, p in paths.items():
        if not p.is_file():
            raise FileNotFoundError(name + ": " + str(p))
    hashes = {name: sha(p) for name, p in paths.items()}
    if hashes["slx"] != MODEL_SHA:
        raise AssertionError("V85_SOURCE_HASH_MISMATCH")
    policy = POLICY.read_text(encoding="utf-8-sig")
    kernel = KERNEL.read_text(encoding="utf-8-sig")
    builder = BUILDER.read_text(encoding="utf-8-sig")
    assert re.search(r"capacity\s*=\s*mul\(\[raw\(1\) raw\(1\)\],\s*sub\(\[raw\(3\) raw\(3\)\],\s*\[raw\(2\) raw\(2\)\]\)\)", policy)
    assert re.search(r"C=P\(p\(1\)\);Ta=P\(p\(2\)\);cap=muliv\(C,minusiv\(P\(p\(3\)\),Ta\)\)", kernel)
    assert "electrical_policy_v85.m" in builder and "earliest_dispatch_kernel_v75.m" in builder
    assert "electrical_dispatch_v85" in builder and "Six_Mode_Interval_Dispatch" in builder
    with zipfile.ZipFile(SLX) as z:
        if z.testzip() is not None:
            raise AssertionError("SLX_ZIP_CORRUPT")
        members = z.namelist()
        chart_files = [x for x in members if "stateflow" in x.lower()]
        if not chart_files or not any(x.endswith(".xml") for x in members):
            raise AssertionError("SLX_MISSING_STATEFLOW_XML")
    spec = json.loads(SPEC.read_text(encoding="utf-8-sig"))
    status = json.loads(STATUS.read_text(encoding="utf-8-sig"))
    c33 = json.loads(C33.read_text(encoding="utf-8-sig"))
    assert status["model_sha256"].lower() == MODEL_SHA
    assert len(spec["cases"]) >= 20
    cases = []
    for case in spec["cases"]:
        p = case["p"]
        assert len(p) == 25 and p[0] > 0 and p[2] > p[1]
        cap = p[0] * (p[2] - p[1])
        e0 = case["initial"][0]
        assert 0 <= e0 < cap
        cases.append({"id": case["id"], "C_MWh_per_K": p[0], "T_min_C": p[1], "T_max_C": p[2],
                      "E_capacity_MWh": cap, "initial_E_MWh": e0, "initial_T_equivalent_C": p[1] + e0 / p[0]})
    capacities = sorted(set(round(x["E_capacity_MWh"], 12) for x in cases))
    assert capacities == [10.0], "UNEXPECTED_CAPACITY_SET"
    assert c33["baseline_simulink_storage_mwh"] == 100.0
    result = {
        "scope": "DCHR_C34_V85_ACTUAL_STORAGE_CONTRACT",
        "generated_local": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "task": TASK, "task_state_observed": task,
        "source_paths": {k: str(v) for k, v in paths.items()},
        "source_sha256": hashes, "source_model_sha256_expected": MODEL_SHA,
        "slx_zip_members": len(members), "slx_stateflow_members": chart_files,
        "capacity_equation": "E_max_MWh = C_MWh_per_K * (T_max_C - T_min_C)",
        "inventory_temperature_equation": "T_equiv_C = T_min_C + E_MWh / C_MWh_per_K",
        "capacity_unit_inference": "MWh, if raw p1 is interpreted as MWh/K and state E is MWh; dimensional inference, not a metered water volume",
        "saved_v85_spec_case_count": len(cases), "saved_v85_case_capacities_mwh": capacities,
        "saved_v85_cases": cases,
        "prior_c33_comparison_reference_mwh": c33["baseline_simulink_storage_mwh"],
        "same_baseline_proven": False,
        "source_specific_conclusion": "The inspected saved v85 test specification has 10 MWh thermal envelope in every case, not 100 MWh. The prior C33 100 MWh synthetic storage is a different model assumption; no dynamic equivalence has been demonstrated.",
        "no_matlab_run": True, "no_model_modifications": True, "primary_source_signoffs": 0,
        "next_step": "Identify the original model or dataset that actually declares 100 MWh; trace its SOC, temperature and charge/discharge law, then construct identical-boundary replay against C31. Do not label v85 10 MWh cases as 100 MWh baseline."
    }
    (HERE / "C34_V85_CONTRACT.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    note = f"""# DCHR C34: kontrola skutočnej kapacity modelu v85

## Overený kontrakt
Uložený súbor `DCHR_Electrical_Dispatch_Stateflow_v85.slx` má SHA256 `{MODEL_SHA}`, zhodný so stavom v86. Jeho priložený testovací predpis obsahuje **{len(cases)} prípadov**. Vo všetkých platí `C = 0,2 MWh/K`, `T_min = 20 °C`, `T_max = 70 °C`, teda `E_max = C (T_max - T_min) = 10 MWh`. Zdrojová funkcia `electrical_policy_v85.m` používa presne tento vzťah a pôvodné jadro v75 ho používa pri kontrole energetických hraníc.

## Kritická hranica porovnania
Predchádzajúci izolovaný výpočet C33 predpokladal **100 MWh**. To však nie je hodnota preukázaná v 27 uložených testoch v85. Preto **nesmieme tvrdiť**, že C33 reprodukuje dynamiku uloženého modelu v85 alebo že 100 MWh je kapacita týchto testov. Ani údaj 10 MWh nie je automaticky objem reálnej nádrže: parameter C je agregovaná tepelná kapacita, chýba potvrdenie fyzikálneho objemu, stratifikácie a hydrauliky.

## Dôkaz a hranice
Kontrolovaný SHA modelu, zdrojové funkcie, generátor Stateflow, uložený testovací predpis a pôvodné C33 JSON sú v `C34_V85_CONTRACT.json`. Archív SLX bol skontrolovaný na integritu a prítomnosť Stateflow XML. **Bez spustenia MATLAB/Simulink**, bez úpravy pôvodných súborov, bez overenia primárnych zdrojov. Údaje sú modelové, nie merané.

## Ďalší krok
Nájsť skutočný pôvod predpokladu 100 MWh v dátach alebo inom modeli, overiť definíciu SOC a teploty, následne vykonať porovnanie oboch modelov pri rovnakých vstupoch a počiatočných podmienkach. Dovtedy ponechať porovnanie C33 ako `NOT_PARITY_VERIFIED`.
"""
    (HERE / "C34_ENGINEERING_NOTE_SK.md").write_text(note, encoding="utf-8")
    guard()
    print(json.dumps({"cases": len(cases), "capacity_mwh": capacities, "model_sha256": hashes["slx"], "slx_members": len(members), "stateflow_members": len(chart_files), "task_status": task["status"]}, ensure_ascii=False))

if __name__ == "__main__":
    audit()
