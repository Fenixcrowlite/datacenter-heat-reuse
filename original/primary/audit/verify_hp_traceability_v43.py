"""Independent Decimal/Fraction and saved-MAT QA; no production HP import."""
from pathlib import Path
from decimal import Decimal, localcontext
from fractions import Fraction
from datetime import datetime, timezone
import hashlib, json, math, sys

ROOT=Path(__file__).resolve().parents[1]
def D(v): return Decimal(str(v))
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def close(a,b):
    return abs(D(a)-D(b)) <= D('3e-12')*max(D(1),abs(D(b)))

def expected(sc,tc,eta,penalty,source,request,cap=100):
    # Independent positive quadratic root, rather than output-space search.
    with localcontext() as ctx:
        ctx.prec=80
        L=D(sc)+D('273.15');H=D(tc)+D('273.15')
        nominal=D(eta)*H/(H-L)
        A=nominal*(1-D(penalty));B=nominal*D(penalty)/D(cap)
        s=D(source);d=A-1-s*B
        if B==0: q=s*A/(A-1)
        else:
            radical=(d*d+4*B*s*A).sqrt()
            q=2*s*A/(d+radical) if d>=0 else (radical-d)/(2*B)
        q=min(q,D(request),D(cap));cop=A+B*q;w=q/cop;qev=q-w
        return [cop,q,w,qev]

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    folder=(ROOT/Path(sys.argv[1])).resolve()
    assert folder.is_relative_to(ROOT/'results')
    spec=json.loads((folder/'spec.json').read_text());source=json.loads((folder/'source_evidence.json').read_text())
    matrix=json.loads((folder/'component_vectors_v43.json').read_text())['matrix']
    cases=json.loads((folder/'stateflow_cases_v43.json').read_text())
    export=json.loads((folder/'mat_reexport_v43.json').read_text())
    checks=[]
    def check(kind,name,ok): checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    for item in json.loads((folder/'preservation.json').read_text()):
        p=ROOT/item['path']
        check('preservation',item['path'],p.is_file() and p.stat().st_size==item['bytes'] and digest(p)==item['sha256'])
    check('source','original_pdf_hash',digest(ROOT/source['pdf_path'])==source['sha256'])
    visual=json.loads((folder/'visual_review_v43.json').read_text())
    check('source','visually_verified_locators',visual['pdf_sha256']==source['sha256'] and visual['visually_inspected_pages']==[8,10,23,27] and source['equation_page']==8 and source['vcc23_assumption_page']==10)
    check('source','no_full_signoff',not source['full_signoff'] and source['upstream_61_62_64']=='NOT_VERIFIED')
    for name in ['run_hp_traceability_v43.m','export_hp_traceability_v43.m','dchr_stateflow_hp_v42.m','DCHR_Dispatch_Stateflow_v42.slx']:
        check('artifact',name,digest(folder/'source_snapshot'/name)==digest(ROOT/'matlab/simulink'/name))
    check('artifact','HP_snapshot',digest(folder/'source_snapshot/heat_pump_step_v40.m')==digest(ROOT/'matlab/+dchr/+components/heat_pump_step_v40.m'))
    check('artifact','spec_snapshot',digest(folder/'source_snapshot/spec.json')==digest(folder/'spec.json'))
    check('MAT','component_export_exact',matrix==export['matrix'])
    check('execution','vector_count',len(matrix)==len(spec['vectors'])==324)
    diagnostic_gaps=[];pinch_gaps=[]
    for v,row in zip(spec['vectors'],matrix):
        sc,tc,eta,pinch,qs,request=v
        # Exact rational algebra with physically imposed Kelvin offsets.
        L=Fraction(str(sc))-Fraction(str(pinch))+Fraction('273.15')
        H=Fraction(str(tc))+Fraction(str(pinch))+Fraction('273.15');e=Fraction(str(eta))
        cop=1+e*L/(H-L);mapped=(H-L+e*L)/H
        check('equation',f'cooling_to_heating_{row[0]}',cop-mapped*H/(H-L)==0 and cop-e*H/(H-L)==1-e)
        check('equation',f'mapped_factor_domain_{row[0]}',0<mapped<=1 and 1<cop<=H/(H-L))
        check('numeric',f'derived_COP_{row[0]}',close(row[3],float(cop)))
        check('numeric',f'factor_{row[0]}',close(row[4],float(mapped)))
        for mode,sc1,tc1,e1,offset in [('same',sc-pinch,tc+pinch,eta,5),('mapped',sc-pinch,tc+pinch,row[4],9),('proxy',sc,tc,row[4],13)]:
            oracle=expected(sc1,tc1,e1,0,qs,request)
            for field,a,b in zip(['cop','heat','electric','source'],row[offset:offset+4],oracle):
                check('numeric',f'{mode}_{field}_{row[0]}',close(a,b))
            check('balance',f'{mode}_{row[0]}',close(row[offset+1],D(row[offset+2])+D(row[offset+3])) and row[offset+3]<=qs+1e-11)
        diagnostic_gaps.append(float(cop)-row[5])
        if pinch: pinch_gaps.append(row[13]-float(cop))
    # Units: power/power -> dimensionless; absolute K / K -> dimensionless.
    power=(1,2,-3,0);temperature=(0,0,0,1)
    divide=lambda a,b: tuple(x-y for x,y in zip(a,b))
    check('dimension','EER_and_COP',divide(power,power)==(0,0,0,0))
    check('dimension','Carnot',divide(temperature,temperature)==(0,0,0,0))
    check('dimension','EER_times_compressor_power',tuple(a+b for a,b in zip(divide(power,power),power))==power)
    check('diagnostic','same_factor_mismatch_detected_all',all(abs(g)>0.4 for g in diagnostic_gaps))
    check('diagnostic','nonzero_pinch_inflates_proxy_COP',all(g>0 for g in pinch_gaps))
    for item,mat in zip(cases,export['cases']):
        id=item['id'];tr=item['dispatch'];x=item['input'];h=item['h'];p=item['p']
        # MATLAB encodes a single row as vector; use flat representation.
        if isinstance(tr[0],list): tr=tr[0]
        check('MAT',id+'_saved_simulation',item['dispatch']==mat['dispatch'] and item['segments']==mat['segments'] and mat['error_message']=='')
        oracle=expected(x[1],x[2],h[1],h[4],x[0],x[3],h[0]);cop,q,w,qev=oracle
        for label,got,want in [('heat',tr[18],q),('electric',tr[19],w),('source',tr[20],qev),('cop',tr[22],cop),('unmet',tr[5],max(D(0),D(x[3])-q))]:
            check('Stateflow',id+'_'+label,close(got,want))
        mode=5 if D(x[3])-q>D('1e-10') else 1
        check('Stateflow',id+'_mode',tr[0]==mode)
        check('Stateflow',id+'_bounds_and_energy',close(tr[7],5) and close(tr[12],0) and tr[19]>=0 and tr[20]<=x[0]+1e-12)
        ss=[r for r in item['segments'] if r[1]>0]
        check('Stateflow',id+'_executed_segments',len(ss)==1 and close(ss[0][1],1))
    # Synthetic reviewer checks are separated from executed numeric evidence.
    check('synthetic','detect_changed_heat',not close(matrix[0][10]*1.1,expected(spec['vectors'][0][0],spec['vectors'][0][1],matrix[0][4],0,spec['vectors'][0][4],spec['vectors'][0][5])[1]))
    check('synthetic','detect_wrong_factor',not close(matrix[0][5],matrix[0][3]))
    check('synthetic','detect_Celsius_Carnot',not close(eta*tc/(tc-sc),float(cop)))
    summary=json.loads((folder/'summary_v43.json').read_text());assertions=json.loads((folder/'assertions_v43.json').read_text())
    check('execution','harness',summary['harness_failed']==0 and summary['harness_passed']==len(assertions) and all(c['passed'] for c in assertions))
    check('execution','version_scope',summary['new_model'] is False and summary['model_version']=='0.42')
    receipts=[]
    for pth in ROOT.glob('audit/HP_traceability_execution_v43_*.json'):
        r=json.loads(pth.read_text(encoding='utf-8-sig'))
        if folder.name in r['command']:
            receipts.append(dict(path=str(pth.relative_to(ROOT)),**r))
    for fn,marker in [('run_hp_traceability_v43','FOCUSED_STATEFLOW=converted_refrigerant'),('export_hp_traceability_v43','SAVED_MAT_EXPORT_CASES=4')]:
        valid=[r for r in receipts if fn in r['command'] and r['exit_code']==0 and marker in (ROOT/r['log_path']).read_text(encoding='utf-8-sig')]
        check('execution',fn+'_receipt',len(valid)>=1)
    failures=[x for x in checks if not x['passed']]
    counts={kind:dict(passed=sum(x['passed'] for x in checks if x['kind']==kind),failed=sum(not x['passed'] for x in checks if x['kind']==kind)) for kind in sorted({x['kind'] for x in checks})}
    report=dict(version='0.43',timestamp_utc=datetime.now(timezone.utc).isoformat(),algorithm='80-digit Decimal positive quadratic root, exact Fraction factor algebra, saved MAT re-export',
        qa_independence='Independent algorithms in the same agent, not independent personnel',counts=counts,
        actual_passed=sum(x['passed'] for x in checks if x['kind']!='synthetic'),actual_failed=sum(not x['passed'] for x in checks if x['kind']!='synthetic'),
        synthetic_passed=counts['synthetic']['passed'],synthetic_failed=counts['synthetic']['failed'],
        same_factor_COP_gap_range=[min(diagnostic_gaps),max(diagnostic_gaps)],
        proxy_COP_increase_range=[min(pinch_gaps),max(pinch_gaps)],receipts=receipts,failures=failures,checks=checks)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');path=folder/f'independent_QA_v43_{stamp}.json'
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('QA_REPORT='+str(path.relative_to(ROOT)))
    print(json.dumps({k:report[k] for k in ['actual_passed','actual_failed','synthetic_passed','synthetic_failed','same_factor_COP_gap_range','proxy_COP_increase_range']},indent=2))
    if failures: print(json.dumps(failures[:20],indent=2));sys.exit(1)

if __name__=='__main__':main()
