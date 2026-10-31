"""Generate isolated A45 reference from immutable A43 control equations."""
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
UPSTREAM = HERE.parent / "AUTONOMOUS_RUN_20261026_1945_A43_FINITE_TRIP_RESIDUAL" / "finite_trip_a43.py"
OUT = HERE / "finite_trip_a45.py"

def replace_once(s, old, new):
    if s.count(old) != 1:
        raise RuntimeError("UPSTREAM_SHAPE_CHANGED:" + old[:70])
    return s.replace(old, new, 1)

def main():
    src = UPSTREAM.read_text(encoding="utf8")
    sha = hashlib.sha256(UPSTREAM.read_bytes()).hexdigest()
    # Protect source provenance. A45 never writes to A43.
    assert sha == "7e2cf8fe09b11ae923726e088825bf73477583e1c2e8888bb42987b130d73af2", sha
    src = replace_once(src, "import counterfactual_a42 as counter",
                       "import counterfactual_a42 as counter\nfrom compressor_a45 import step_capacity, dispatch_limited")
    src = replace_once(src, "sensor_lag_steps=0,heat_capacity_J_per_C=base.C_BASE):",
                       "sensor_lag_steps=0,heat_capacity_J_per_C=base.C_BASE,\n             compressor_tau_s=1800.0):")
    src = replace_once(src, '    E,T=base.E_INIT,30.0',
                       '    if not math.isfinite(compressor_tau_s) or compressor_tau_s<0:\n        raise ValueError("INVALID_COMPRESSOR_TAU")\n    hp_available_W=0.0\n    E,T=base.E_INIT,30.0')
    src = replace_once(src, "        flow=base.dispatch(row,qheat,E,T,effective_cap)",
                       "        hp_target_W=base.dispatch(row,qheat,E,T,effective_cap)['hp_source_W']\n"
                       "        hp_available_W=step_capacity(hp_available_W,hp_target_W,DT,compressor_tau_s)\n"
                       "        flow=dispatch_limited(row,qheat,E,T,effective_cap,hp_available_W)")
    src = replace_once(src, "            E_start_J=E,passive_W=passive,**flow)",
                       "            E_start_J=E,passive_W=passive,hp_available_W=hp_available_W,**flow)")
    src = src.replace("TRACE_A43_", "TRACE_A45_").replace("RESULTS_A43.json", "RESULTS_A45.json")
    src = src.replace("A43_SYNTHETIC_FINITE_TRIP_REFERENCE", "A45_SYNTHETIC_COMPRESSOR_LAG_REFERENCE")
    src = src.replace('"A42 HP/TES dispatch remains instantaneous; compressor inertia not modeled"',
                      '"A45 HP evaporator source capacity has a synthetic first-order lag; no compressor coastdown storage"')
    OUT.write_text(src, encoding="utf8")
    print("A45_SOURCE_SHA256", hashlib.sha256(OUT.read_bytes()).hexdigest())

if __name__ == "__main__":
    main()
