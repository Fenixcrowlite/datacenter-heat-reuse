"""Independent synthetic event sequences for an isolated graphical Stateflow chart.
No hardware interfaces. Timing semantics: evaluate guards, then during actions.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATES = {"ACTIVE": 0, "TRIP_PENDING": 1, "TRIPPED": 2, "RAMPING": 3}
N = 672

def stimuli(case: str):
    rows = []
    for k in range(N):
        fault = False
        if case == "short_fault":
            fault = 96 <= k < 97
        elif case == "sustained_fault":
            fault = 96 <= k < 145
        elif case == "interrupted_recovery":
            fault = (96 <= k < 106) or (111 <= k < 115) or (210 <= k < 230)
        elif case != "nominal":
            raise ValueError(case)
        recover = not fault
        ramp_done = recover and (k >= 160 if case == "sustained_fault" else
                                  k >= 126 if case == "interrupted_recovery" else True)
        rows.append(dict(k=k, fault=int(fault), recover=int(recover),
                         ramp_done=int(ramp_done)))
    return rows

def reference(rows):
    state = "ACTIVE"
    pending = 0
    good = 0
    trace = []
    for r in rows:
        fault, recover, ramp = bool(r["fault"]), bool(r["recover"]), bool(r["ramp_done"])
        # Stateflow outer transitions evaluate before the during action.
        if state == "ACTIVE":
            if fault:
                state, pending = "TRIP_PENDING", 1
        elif state == "TRIP_PENDING":
            if not fault and recover:
                state = "ACTIVE"
            elif pending >= 2:
                state, good = "TRIPPED", 0
            else:
                pending += 1
        elif state == "TRIPPED":
            if good >= 1 and recover and not fault:
                state = "RAMPING"
            else:
                good = good + 1 if recover and not fault else 0
        elif state == "RAMPING":
            if fault:
                state, pending = "TRIP_PENDING", 1
            elif ramp:
                state = "ACTIVE"
        trace.append(dict(**r, mode=STATES[state],
                          alarm=0 if state == "ACTIVE" else (2 if state == "TRIPPED" else 1)))
    return trace

def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

def main():
    summary = {}
    for case in ("nominal", "short_fault", "sustained_fault", "interrupted_recovery"):
        trace = reference(stimuli(case))
        write_csv(HERE / ("STIM_A44_" + case + ".csv"), trace)
        counts = [sum(x["mode"] == mode for x in trace) for mode in range(4)]
        summary[case] = dict(samples=len(trace), counts=counts,
                             transitions=sum(a["mode"] != b["mode"] for a,b in zip(trace, trace[1:])))
    (HERE / "REFERENCE_A44.json").write_text(
        json.dumps({"status": "SYNTHETIC_GRAPHICAL_STATEFLOW_REFERENCE",
                    "physical_release": False, "cases": summary}, indent=2)+"\n",
        encoding="utf-8")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
