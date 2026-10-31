"""Repeatable release gate for isolated A36 reference, no production writes."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
FLAGS=("STOP","STOP.flag","STOP.txt",".STOP","PAUSE","PAUSE.flag",".PAUSE","STOP_MANAGED_WORKERS.txt")
for folder in (ROOT,ROOT/"recovery",HERE,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
    for name in FLAGS:
        if (folder/name).exists():
            raise RuntimeError("STOP_ACTIVE "+str(folder/name))
r=subprocess.run([sys.executable,"-m","unittest","test_redispatch","-q"],
                 cwd=HERE,capture_output=True,text=True,timeout=20)
if r.returncode or not re.search(r"Ran 17 tests",r.stderr+r.stdout):
    raise RuntimeError("UNIT_TESTS_FAILED "+r.stderr)
ind=subprocess.run([sys.executable,"independent_check.py"],cwd=HERE,
                   capture_output=True,text=True,timeout=20)
if ind.returncode:
    raise RuntimeError("INDEPENDENT_QA_FAILED "+ind.stderr)
qa=json.loads((HERE/"INDEPENDENT_QA.json").read_text(encoding="utf8"))
summary=json.loads((HERE/"RESULTS.json").read_text(encoding="utf8"))
if qa["independent_checks_passed"]!=20833 or qa["rows_checked"]!=4032:
    raise RuntimeError("INDEPENDENT_QA_COUNT_CHANGED")
if len(summary["scenarios"])!=6 or summary["samples"]!=672 or summary["physical_release_allowed"]:
    raise RuntimeError("SUMMARY_INVALID")
source=Path(summary["source_path"])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if sha(source)!=summary["source_sha256"]:
    raise RuntimeError("BASELINE_SOURCE_CHANGED")
for data in summary["scenarios"].values():
    if sha(HERE/data["output"])!=data["output_sha256"]:
        raise RuntimeError("SCENARIO_SHA_CHANGED")
result={
    "status":"PASS","unit_tests_passed":17,"independent_checks_passed":20833,
    "scenarios":6,"rows_per_scenario":672,
    "source_sha256":sha(source),
    "physical_release_allowed":False,
    "model_class":"D_SYNTHETIC -> D_DERIVED, instantaneous reference only",
}
(HERE/"QA_RESULT.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
print(json.dumps(result,indent=2))
