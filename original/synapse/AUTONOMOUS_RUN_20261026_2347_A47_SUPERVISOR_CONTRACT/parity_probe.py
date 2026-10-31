"""A47 pre-integration: independent graphical-supervisor/A46 state parity probe.
Read-only upstream; synthetic traces, no physical safety certification.
"""
import csv, json, hashlib
from pathlib import Path

ROOT=Path(r"C:\Users\Lysda\Desktop\SynapseControlCenter\recovery")
HERE=Path(__file__).resolve().parent
A45=ROOT/"AUTONOMOUS_RUN_20261026_2200_A45_COMPRESSOR_LAG_REFERENCE"
A44=ROOT/"AUTONOMOUS_RUN_20261026_2050_A44_GRAPHICAL_STATEFLOW"
A46=ROOT/"AUTONOMOUS_RUN_20261026_2255_A46_INTEGRATION"
A41=ROOT/"AUTONOMOUS_RUN_20261026_1751_A41_CLOSED_LOOP_SIM"
CASES=("both","main_only","backup_only","neither","CF_both","CF_backup_only","CF_neither")
STATES={"ACTIVE":0,"TRIP_PENDING":1,"TRIPPED":2,"RAMPING":3}

def hash_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def graphical_reference(rows, qdc):
    """Exact transition/during order of the A44 Python reference; adapted live inputs."""
    state="ACTIVE";pending=0;good=0;previous_active=0.0;out=[]
    for i,r in enumerate(rows):
        fault=float(r["nominal_cap_W"])<=0 or float(r["T_start_C"])>=42
        recover=float(r["nominal_cap_W"])>0 and float(r["T_start_C"])<36
        ramp_done=previous_active+15000>=qdc[i]-1e-8
        if state=="ACTIVE":
            if fault:state,pending="TRIP_PENDING",1
        elif state=="TRIP_PENDING":
            if not fault and recover:state="ACTIVE"
            elif pending>=2:state,good="TRIPPED",0
            else:pending+=1
        elif state=="TRIPPED":
            if good>=1 and recover and not fault:state="RAMPING"
            else:good=good+1 if recover and not fault else 0
        elif state=="RAMPING":
            if fault:state,pending="TRIP_PENDING",1
            elif ramp_done:state="ACTIVE"
        out.append(state)
        previous_active=float(r["active_it_W"])
    return out

def run():
    expected={"A44":hash_file(A44/"DCHR_A44_Graphical_Supervisor.slx"),
              "A46":hash_file(A46/"DCHR_A46_Compressor_Closed_Loop.slx")}
    report={"kind":"A47_GRAPHICAL_PREINTEGRATION_PARITY",
            "source_sha256":expected,"physical_release":False,
            "cases":{},"total_steps":0,"mismatches":0}
    with (A41/"INPUTS_A41.csv").open(newline="",encoding="utf-8") as f:
        qdc=[float(row["qdc"]) for row in csv.DictReader(f)]
    assert len(qdc)==672
    for name in CASES:
        path=A45/("TRACE_A45_"+name+".csv")
        with path.open(newline="",encoding="utf-8") as f:rows=list(csv.DictReader(f))
        assert len(rows)==672,(name,len(rows))
        chart=graphical_reference(rows,qdc)
        mismatches=[{"step":i,"expected_A46":r["state"],"predicted_A44":s,
                     "temp_start_C":float(r["T_start_C"]),
                     "nominal_cap_W":float(r["nominal_cap_W"])}
                    for i,(r,s) in enumerate(zip(rows,chart)) if r["state"]!=s]
        report["cases"][name]={"steps":len(rows),"mismatches":len(mismatches),
                               "first_three":mismatches[:3]}
        report["total_steps"]+=len(rows);report["mismatches"]+=len(mismatches)
    (HERE/"PARITY_PROBE.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"total_steps":report["total_steps"],"mismatches":report["mismatches"],
                      "by_case":{k:v["mismatches"] for k,v in report["cases"].items()}},ensure_ascii=False))
    return report

if __name__=="__main__":
    run()

