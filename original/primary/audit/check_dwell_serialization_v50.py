"""Resolve each initial CSV-only dwell flag with exact original-MAT binary spans."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal as D,localcontext
import csv,json,struct,sys

ROOT=Path(__file__).resolve().parents[1]

def exact(h):return struct.unpack('>d',bytes.fromhex(h))[0]

def main():
    folder=(ROOT/Path(sys.argv[1])).resolve();assert folder.is_relative_to(ROOT/'results')
    first=sorted(folder.glob('independent_QA_v50_*.json'))[0];q=json.loads(first.read_text())
    names={v['name'] for v in q['checks'] if not v['passed']}
    assert len(names)==152 and all(v['kind']=='certified_dwell' for v in q['checks'] if not v['passed'])
    with (folder/'off_05_segments.csv').open(newline='') as f:segments=list(csv.reader(f))
    with (folder/'binary_reopen/off_05_spans_hex.csv').open(newline='') as f:
        spans={(int(r[0]),int(r[1])):exact(r[2]) for r in csv.reader(f)}
    with (folder/'binary_reopen/off_05_clocks_hex.csv').open(newline='') as f:
        clocks={int(r[0]):[exact(v) for v in r[1:]] for r in csv.reader(f)}
    resolutions=[];ageCSV=D(0);ageExact=D(0);latch=1;lastinterval=0;j=0
    with localcontext() as ctx:
        ctx.prec=60
        for row in segments:
            interval,slot=int(float(row[0])),int(float(row[1]));z=[float(v) for v in row[2:]]
            if interval!=lastinterval:j=0;lastinterval=interval
            name=f'off_05_{interval-1}_{j}';new=int(z[25])
            if name in names:
                assert new!=latch
                bound=max(D.from_float(clocks[interval][3]),D.from_float(clocks[interval][7]))
                dwell=D('.5') if new else D('.25')
                a=ageCSV-bound-dwell;b=ageExact-bound-dwell
                resolutions.append(dict(name=name,latch_target=new,csv_lower_margin_h=str(a),
                    exact_binary_lower_margin_h=str(b),serialization_age_difference_h=str(ageExact-ageCSV),
                    resolved=a<0 and b>=0))
            if new!=latch:ageCSV=D(0);ageExact=D(0)
            ageCSV+=D(str(z[1]));ageExact+=D.from_float(spans[(interval,slot)])
            latch=new;j+=1
    assert {v['name'] for v in resolutions}==names
    out=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),initial_qa=first.relative_to(ROOT).as_posix(),
        evidence_class='EXACT_BINARY_SERIALIZATION_AUDIT_NOT_GUARD_RELAXATION',
        passed=sum(v['resolved'] for v in resolutions),failed=sum(not v['resolved'] for v in resolutions),
        min_exact_lower_margin_h=str(min(D(v['exact_binary_lower_margin_h']) for v in resolutions)),
        max_abs_serialization_age_difference_h=str(max(abs(D(v['serialization_age_difference_h'])) for v in resolutions)),
        decisions=resolutions)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    path=folder/('dwell_serialization_resolution_v50_'+stamp+'.json');assert not path.exists()
    path.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='decisions'},indent=2))
    if out['failed']:raise SystemExit(1)

if __name__=='__main__':main()
