"""C40 MATLAB harness static contract and live resource admission, no MATLAB launch."""
from __future__ import annotations
import ctypes,datetime as dt,hashlib,json,re
from pathlib import Path
H=Path(__file__).resolve().parent
ROOT=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\matlab")
SCC=H.parent.parent
MATLAB=Path(r"C:\Program Files\MATLAB\R2026a\bin\matlab.exe")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for x in iter(lambda:f.read(1048576),b""):h.update(x)
 return h.hexdigest()
def free_ram_gib():
 class MEMORYSTATUSEX(ctypes.Structure):
  _fields_=[("dwLength",ctypes.c_ulong),("dwMemoryLoad",ctypes.c_ulong),
   ("ullTotalPhys",ctypes.c_ulonglong),("ullAvailPhys",ctypes.c_ulonglong),
   ("ullTotalPageFile",ctypes.c_ulonglong),("ullAvailPageFile",ctypes.c_ulonglong),
   ("ullTotalVirtual",ctypes.c_ulonglong),("ullAvailVirtual",ctypes.c_ulonglong),
   ("ullAvailExtendedVirtual",ctypes.c_ulonglong)]
 m=MEMORYSTATUSEX();m.dwLength=ctypes.sizeof(m)
 if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
  raise OSError("GlobalMemoryStatusEx failed")
 return m.ullAvailPhys/(1024**3)
def main():
 script=(H/"c40_export_warm45_v2.m").read_text(encoding="utf-8")
 driver=(ROOT/"run_experiment_v2.m").read_text(encoding="utf-8")
 source=(ROOT/"+dchr"/"simulate_system_v2.m").read_text(encoding="utf-8")
 inputs=(ROOT/"+dchr"/"make_inputs.m").read_text(encoding="utf-8")
 cfg=(ROOT/"default_config.m").read_text(encoding="utf-8")
 active="\n".join(x.split("%",1)[0] for x in script.splitlines())
 checks={
  "matlab_installed":MATLAB.is_file(),
  "source_files_present":all((ROOT/p).is_file() for p in ["default_config_v2.m","default_config.m","+dchr/make_inputs.m","+dchr/simulate_system_v2.m"]),
  "seed42_source":bool(re.search(r"random_seed\s*=\s*42",cfg)) and "rng(cfg.sim.random_seed)" in inputs,
  "warm_scenario_driver":bool(re.search(r"'Warm45_Storage100'",driver)),
  "scenario45":bool(re.search(r"cfg\.dc\.source_temp_C\s*=\s*45\s*;",active)),
  "recovery90":bool(re.search(r"cfg\.dc\.recovery_fraction\s*=\s*0\.90\s*;",active)),
  "storage100":bool(re.search(r"cfg\.storage\.capacity_MWh\s*=\s*100\s*;",active)),
  "weather_mode":'cfg.model.dh_temperature = "weather";' in active,
  "calls_core":'dchr.simulate_system_v2(cfg, input)' in active and 'dchr.compute_metrics_v2(cfg, out)' in active,
  "no_shared_driver":not bool(re.search(r"(?<![\w.])run_experiment_v2\s*\(",active)),
  "isolated_export":'outDir = fileparts(mfilename(' in active and "outputCsv = fullfile(outDir," in active,
  "no_shared_results_path":not bool(re.search(r"writetable\s*\([^;]*resultsDir",active)),
  "no_source_mutation":'save(' not in active and 'delete(' not in active and 'movefile(' not in active,
  "source_contract":'E(1:end-1)' in source and "Storage_E_MWh" in source,
  "output_collision_guard":'~isfile(outputCsv) && ~isfile(outputJson)' in active,
  "no_native_output_yet":not (H/"Warm45_Storage100_v2_MATLAB_NATIVE.csv").exists()
 }
 if not all(checks.values()):raise AssertionError(checks)
 ram=free_ram_gib()
 result={"scope":"DCHR_C40_NATIVE_EXPORT_STATIC_QA",
  "observed_local":dt.datetime.now().astimezone().isoformat(timespec="seconds"),
  "checks":checks,"passed":len(checks),"status":"PASS",
  "free_ram_gib":round(ram,3),"min_ram_for_native_gib":5.0,
  "native_execution_admitted":ram>=5.0,
  "native_executed":False,"matlab_source_sha256":sha(ROOT/"+dchr"/"simulate_system_v2.m"),
  "export_script_sha256":sha(H/"c40_export_warm45_v2.m"),
  "primary_source_signoffs":0}
 with (H/"C40_STATIC_QA.json").open("xb") as f:
  f.write((json.dumps(result,sort_keys=True,indent=2)+"\n").encode("utf-8"))
 print(json.dumps({"status":"PASS","checks":len(checks),"free_ram_gib":round(ram,3),
  "native_admitted":ram>=5.0,"native_executed":False}))
if __name__=="__main__":main()
