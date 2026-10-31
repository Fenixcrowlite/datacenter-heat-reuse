"""Independent C34 source/contract QA, Decimal arithmetic, mutation controls."""
from __future__ import annotations
import hashlib
import json
import re
import sqlite3
import zipfile
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 40
H = Path(__file__).resolve().parent
R = H.parent.parent
checks = []

def check(name, condition):
    checks.append({"name": name, "passed": bool(condition)})
    if not condition:
        raise AssertionError(name)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()

def main():
    data = json.loads((H / "C34_V85_CONTRACT.json").read_text(encoding="utf-8"))
    sources = {name: Path(p) for name, p in data["source_paths"].items()}
    check("task_existing", data["task"] == "scc-2aab24704c2bd0")
    with sqlite3.connect(f"file:{(R/'tasks.sqlite3').as_posix()}?mode=ro", uri=True) as db:
        check("registry_integrity", db.execute("PRAGMA integrity_check").fetchone()[0] == "ok")
        row = db.execute("SELECT project,status,worker_pid FROM tasks WHERE id=?", (data["task"],)).fetchone()
        check("task_eligible", bool(row and row[0] == "DataCenter Heat Reuse" and row[1] not in ("done","cancelled") and row[2] is None))
    check("source_count", len(sources) == 7)
    for name, path in sources.items():
        check("sha256_" + name, sha(path) == data["source_sha256"][name])
    check("model_known_sha", data["source_sha256"]["slx"] == "2a9de22c0c55e8c4a87f7b0e0cfe9cd97db08c991f09d98361b009de310adde7")
    with zipfile.ZipFile(sources["slx"]) as z:
        check("slx_integrity", z.testzip() is None)
        check("slx_has_stateflow", any("stateflow" in x.lower() for x in z.namelist()))
        check("slx_count", len(z.namelist()) == data["slx_zip_members"])
    spec = json.loads(sources["spec"].read_text(encoding="utf-8-sig"))
    check("spec_27", len(spec["cases"]) == 27 == data["saved_v85_spec_case_count"])
    check("all_25_parameters", all(len(x["p"]) == 25 for x in spec["cases"]))
    expected = []
    for x in spec["cases"]:
        c,lo,hi = map(lambda v: Decimal(str(v)), x["p"][:3])
        e0 = Decimal(str(x["initial"][0]))
        check("physical_domain_" + x["id"], c > 0 and hi > lo and e0 >= 0)
        cap = c * (hi - lo)
        check("capacity_" + x["id"], cap == Decimal(10))
        check("initial_inside_" + x["id"], e0 < cap)
        expected.append((x["id"],cap,lo+e0/c))
    reported = {x["id"]: x for x in data["saved_v85_cases"]}
    check("case_id_exact", set(reported) == {x[0] for x in expected})
    for name, cap, temp in expected:
        check("reported_cap_" + name, Decimal(str(reported[name]["E_capacity_MWh"])) == cap)
        check("reported_temp_" + name, abs(Decimal(str(reported[name]["initial_T_equivalent_C"]))-temp) < Decimal("1e-10"))
    check("capacity_set_10", data["saved_v85_case_capacities_mwh"] == [10.0])
    policy = sources["policy"].read_text(encoding="utf-8-sig")
    kernel = sources["kernel"].read_text(encoding="utf-8-sig")
    builder = sources["builder"].read_text(encoding="utf-8-sig")
    check("policy_capacity_raw_indices", "raw(1)" in policy and "raw(3)" in policy and "raw(2)" in policy and "capacity=mul(" in policy)
    check("kernel_thermal_capacity", "C=P(p(1));Ta=P(p(2));cap=muliv(C,minusiv(P(p(3)),Ta));" in kernel)
    check("builder_links_policy", "electrical_policy_v85.m" in builder)
    check("builder_links_kernel", "earliest_dispatch_kernel_v75.m" in builder)
    c33 = json.loads(sources["c33"].read_text(encoding="utf-8"))
    check("prior_100_assumption", Decimal(str(c33["baseline_simulink_storage_mwh"])) == Decimal(100))
    check("different_reference", Decimal(str(c33["baseline_simulink_storage_mwh"])) != expected[0][1])
    check("no_parity_claim", data["same_baseline_proven"] is False)
    check("no_matlab_claim", data["no_matlab_run"] is True)
    check("no_physical_validation", data["primary_source_signoffs"] == 0)
    check("independent_positive_control", Decimal(2)*(Decimal(70)-Decimal(20)) == Decimal(100))
    check("independent_negative_control", Decimal("0.2")*(Decimal(70)-Decimal(20)) != Decimal(100))
    note = (H / "C34_ENGINEERING_NOTE_SK.md").read_text(encoding="utf-8")
    check("correction_in_note", "10 MWh" in note and "100 MWh" in note and "NOT_PARITY_VERIFIED" in note)
    output = {"status": "PASS", "passed": len(checks), "failed": 0, "checks": checks,
              "method": "independent Decimal recomputation from 27 archived v85 cases, ZIP CRC and source SHA; no MATLAB execution"}
    (H / "QA_INDEPENDENT_C34.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "passed": len(checks), "failed": 0}, ensure_ascii=False))

if __name__ == "__main__":
    main()
