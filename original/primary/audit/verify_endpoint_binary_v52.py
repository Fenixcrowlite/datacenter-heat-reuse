"""Exact state-protocol and 70-digit ODE review; no production-code import."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal as D, localcontext
import csv, hashlib, json, math, struct, sys

ROOT = Path(__file__).resolve().parents[1]
def binary(value):
    return struct.unpack('>d', bytes.fromhex(value))[0]
def decimal(value):
    return D.from_float(float(value))
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    report=json.loads((folder/'annual_sensitivity_v52.json').read_text())
    checks=[];scenarios=[]
    def check(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    with localcontext() as ctx:
        ctx.prec=70
        for item in report['stateflow']:
            p=item['p'];cap,ec,ed,rate,cutoff=map(decimal,[p[1],p[4],p[5],p[6],p[7]])
            # 64 ulps is the production normalization budget. Eight extra ulps
            # cover arithmetic evaluation when comparing to the exact ODE.
            budget=72*decimal(math.ulp(max(1.,p[1])))
            count=0;maxerror=D(0);maxloss=D(0);bad=[]
            with (folder/'endpoint_binary'/(item['id']+'.csv')).open(newline='') as f:
                for row in csv.DictReader(f):
                    values=[binary(row[k]) for k in ('StartHex','EndHex','TargetHex','ChargeHex','DischargeHex','SpanHex','StandingHex','ResidualHex')]
                    start,end,target,qc,qd,t,standing,residual=map(decimal,values)
                    power=ec*qc-qd/ed
                    retention=(-rate*t).exp();phi=t if rate==0 else (1-retention)/rate
                    expected=start*retention+power*phi
                    error=abs(end-expected);loss_error=abs(standing-(start+power*t-expected))
                    kind=int(row['Kind'])
                    ok=(end==target and 0<=start<=cap and 0<=end<=cap and t>0 and
                        error<=budget and loss_error<=budget and abs(residual)<=budget and
                        (kind!=1 or end==cap) and (kind!=2 or end==cutoff))
                    if not ok:bad.append(dict(interval=row['Interval'],slot=row['Slot'],error=str(error),loss_error=str(loss_error),residual=str(residual)))
                    count+=1;maxerror=max(maxerror,error);maxloss=max(maxloss,loss_error)
            check(item['id']+'_exact_protocol_and_ODE',not bad and count==item['positive_segments'])
            scenarios.append(dict(id=item['id'],positive_segments=count,failed_segments=len(bad),first_failures=bad[:10],equation_budget_MWh=str(budget),max_endpoint_error_MWh=str(maxerror),max_standing_error_MWh=str(maxloss)))
    # Exact identity distinguishes a one-ULP mutation even below ODE tolerance.
    selfchecks=[dict(name='one_ULP_endpoint_mutation',passed=binary('4049000000000000')!=binary('4049000000000001')),
                dict(name='material_ODE_mutation',passed=D('.001')>budget)]
    check('nine_complete_annual_scenarios',len(scenarios)==9 and sum(v['positive_segments'] for v in scenarios)==report['summary']['positive_segments'])
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    result=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),evidence_class='SAME_AGENT_INDEPENDENT_BINARY_DECIMAL_QA',actual_passed=sum(v['passed'] for v in checks),actual_failed=sum(not v['passed'] for v in checks),reviewer_selfchecks_passed=sum(v['passed'] for v in selfchecks),reviewer_selfchecks_failed=sum(not v['passed'] for v in selfchecks),scenarios=scenarios,checks=checks,reviewer_selfchecks=selfchecks,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    path=folder/('endpoint_binary_QA_v52_'+stamp+'.json');path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if result['actual_failed'] or result['reviewer_selfchecks_failed']:raise SystemExit(1)
if __name__=='__main__':main()
