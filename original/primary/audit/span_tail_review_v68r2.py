"""Independent Taylor remainder proof and exact-binary domain-defect QA.

Production uses recurrence and interval arithmetic. This reviewer uses rational
polynomial coefficients and Decimal exp/log, without production imports.
"""
from fractions import Fraction as F
from decimal import Decimal as D, localcontext
from math import factorial, nextafter, inf
from pathlib import Path
import hashlib, json

def dec(v):
    v=F(v)
    return D(v.numerator)/D(v.denominator)

def rows(v):
    return [v] if v and isinstance(v[0],(int,float)) else v

def additional_review(folder, report, check):
    for rec in json.loads((folder/'reviewer_hashes_v68r2.json').read_text()):
        path=folder.parents[1]/rec['path']
        sealed=folder/'reviewer_snapshot_v68r2'/rec['path']
        check('reviewer_seal',rec['path'],hashlib.sha256(path.read_bytes()).hexdigest()==rec['sha256'] and hashlib.sha256(sealed.read_bytes()).hexdigest()==rec['sha256'])
    # Integral forms: phi1=int_0^1 exp(sx)ds;
    # phi2=int_0^1 (1-s)exp(sx)ds. The degree-24 Taylor
    # remainders are <= e^2*2^25/26! and e^2*2^25/27!.
    # e <= sum_0^4 1/n! + (1/5!)/(1-1/5) = 87/32.
    e_bound=sum((F(1,factorial(n)) for n in range(5)),F(0))+F(1,factorial(5))/(1-F(1,5))
    check('tail_proof','e2_less_than_8',e_bound==F(87,32) and e_bound**2<8)
    bound=F(8*2**25,factorial(26))
    check('tail_proof','exact_numerator',8*2**25==268435456)
    check('tail_proof','phi2_conservative_bound',F(8*2**25,factorial(27))<bound)
    with localcontext() as ctx:
        ctx.prec=160
        for i in range(-40,41):
            x=F(i,20)
            p1=sum((x**n/factorial(n+1) for n in range(25)),F(0))
            p2=sum((x**n/factorial(n+2) for n in range(25)),F(0))
            if x:
                expx=dec(x).exp()
                true1=(expx-1)/dec(x)
                true2=(expx-1-dec(x))/dec(x)**2
            else:
                true1=D(1);true2=D('.5')
            check('tail_numeric',f'phi1_{i}',abs(true1-dec(p1))<dec(bound))
            check('tail_numeric',f'phi2_{i}',abs(true2-dec(p2))<dec(bound))
    legacy=report['legacy_defects']
    actual=[v for v in legacy if v['model']!='host_v67']
    check('defect','two_actual_failures_one_control',len(actual)==3)
    for v in actual:
        inputs=rows(v['input']);cfg=v['cfg'];lam=F(cfg[40]);H=F(inputs[-1][4])
        check('defect',v['id']+'_valid_exact_binary_span',0<lam*H<=1)
        if v['id']=='span_near_one':
            check('defect',v['id']+'_legacy_near_control',not v['message'])
        else:
            check('defect',v['id']+'_specific_guard',bool(v['identifier']) and 'v63 outward span exceeds one' in v['message'])
            check('defect',v['id']+'_stateflow_stack','DCHR_Event_Brackets_Stateflow_v67r2/Six_Mode_Interval_Dispatch' in v['message'])
        if v['id']=='span_delayed':
            prefix=rows(v['valid_prefix'])
            check('defect','two_retained_prefix_ticks',len(prefix)==2 and all(len(r)==256 and r[179]==66 for r in prefix))
            # Original physical passive trajectory independently contained.
            with localcontext() as ctx:
                ctx.prec=160
                for k,row in enumerate(prefix):
                    exact=dec(F(inputs[0][9]))*(-dec(lam*F(inputs[k][2]))).exp()
                    check('defect',f'legacy_prefix_inventory_{k}',dec(F(row[36]))<=exact<=dec(F(row[37])))
    host=[v for v in legacy if v['model']=='host_v67']
    check('defect','three_host_controls',len(host)==3)
    for v in host:
        H=v['horizon'];exact=F(.125)*F(H)
        # At exact H=8 the expansion exceeds 1; neighboring values
        # below it complete. At the adjacent value, ties-to-even rounds
        # the expanded endpoint back to exactly 1.
        expect_failure=H==8.
        check('defect',v['id']+'_exact_admissibility',0<exact<=1)
        check('defect',v['id']+'_expected_rejection',bool(v['message'])==expect_failure)
        if expect_failure:
            check('defect',v['id']+'_specific_root_guard','v67 outward root span' in v['message'])
        else:
            check('defect',v['id']+'_legacy_interior_control',v['output'][0]==1)
    runs={v['id']:v for v in report['runs']}
    for id in ['span_equal_one','span_near_one','span_inside_one','span_delayed']:
        r=runs[id];trace=rows(r['trace'])
        check('repair',id+'_actual_completed',len(trace)==len(rows(r['input'])))
        check('repair',id+'_passive_restart_certificate',trace[-1][235] in [1,3] and trace[-1][246]==1)
    root=folder.parents[1]
    cert=(root/'matlab/simulink/certify_event_root_v68.m').read_text()
    obs=(root/'matlab/simulink/event_observer_v68.m').read_text()
    kernel=(root/'matlab/simulink/interval_dispatch_kernel_v68.m').read_text()
    prior=(root/'matlab/simulink/interval_dispatch_kernel_v66.m').read_text()
    expected=prior.replace('function y=interval_dispatch_kernel_v66(', 'function y=interval_dispatch_kernel_v68(')
    expected=expected.replace("assert(max(abs(x))<=1,'v63 outward span exceeds one')", "assert(max(abs(x))<=2,'v68 outward span exceeds two')")
    expected=expected.replace('tail=diviv([3 3],fac);','% On the outward evaluation interval |x|<=2, e^2<8.\n% Tail for both phi1 and phi2 is <=8*2^25/26!.\ntail=diviv([268435456 268435456],fac);')
    check('scope','only_kernel_padding_and_tail_changed',kernel==expected)
    check('scope','embedded_host_certifier_identical',obs.endswith(cert))
    check('scope','public_root_domain_remains_one','lambda*horizon<=1' in cert)
