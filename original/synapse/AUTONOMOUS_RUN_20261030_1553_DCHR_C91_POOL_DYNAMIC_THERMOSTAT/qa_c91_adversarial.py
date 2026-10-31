"""C91 negative tests: synthetic STOP, pinned input drift, invalid state and source.
Never creates a STOP flag outside its own temporary directory.
"""
import importlib.util, json, tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("c91_model",HERE/"c91_pool_dynamic.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=[]
def expect_error(label,fn,kind,fragment):
    try:fn()
    except kind as e:
        assert fragment in str(e),str(e)
        checks.append(label)
    else:raise AssertionError("MISSING_REJECTION "+label)
with tempfile.TemporaryDirectory(prefix="c91-guard-") as tmp:
    old=m.ROOT
    m.ROOT=Path(tmp)
    (m.ROOT/"STOP").write_text("test only",encoding="utf-8")
    expect_error("stop_flag_rejected",m.guard,RuntimeError,"STOP_ACTIVE")
    m.ROOT=old
expect_error("negative_source",lambda:m.potential_hp(-0.1,0.2),ValueError,"INVALID_HX_SOURCE")
expect_error("fraction_above_one",lambda:m.potential_hp(0.2,1.1),ValueError,"INVALID_FRACTION")
expect_error("fraction_below_zero",lambda:m.potential_hp(0.2,-0.1),ValueError,"INVALID_FRACTION")
expect_error("nan_source",lambda:m.potential_hp(float("nan"),0.2),ValueError,"INVALID_HX_SOURCE")
expect_error("bad_pool_temperature",lambda:m.simulate_hour(-1,False,0.2,0.25,0.0,12),ValueError,"INVALID_POOL_TEMPERATURE")
old_hash=m.C90_SHA
m.C90_SHA="0"*64
expect_error("pinned_source_drift",m.run,RuntimeError,"C90_PIN_MISMATCH")
m.C90_SHA=old_hash
assert m.C90_SHA==m.sha(m.C90);checks.append("restored_source_pin")
out={"schema":"C91_ADVERSARIAL_QA_V1","passed":len(checks),"checks":checks}
with (HERE/"C91_ADVERSARIAL_QA.json").open("x",encoding="utf-8") as f:
    json.dump(out,f,indent=2);f.write("\n")
print("C91 ADVERSARIAL QA",len(checks),"/",len(checks),"PASS")
