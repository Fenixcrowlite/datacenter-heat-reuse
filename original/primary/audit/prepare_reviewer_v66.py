"""Version the reviewer, extending independently implemented equation checks."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    dst=ROOT/'audit/verify_interval_dispatch_v66.py';assert not dst.exists()
    s=(ROOT/'audit/verify_interval_dispatch_v65.py').read_text()
    s=s.replace('v65','v66').replace("version='0.65'","version='0.66'").replace('row[179]==65','row[179]==66')
    s=s.replace('ROOT=Path(__file__).resolve().parents[1]', 'from earliest_service_reference_v66 import compare\nfrom verify_interval_dispatch_v65 import analyze as baseline_analyze\nROOT=Path(__file__).resolve().parents[1]')
    anchor="checks[f'{i}_cutoff']=not dis or min(E,en)>=dec(cut)"
    s=s.replace(anchor,anchor+"\n        checks[f'{i}_thermal_stop']=not charge or max(E,en)<dec(C*(stopT-Ta))")
    anchor="check('coverage','six_modes',report['mode_coverage']==list(range(6)))"
    extra="""
    bw=json.loads((folder/'baseline_witness.json').read_text());bu=[bw['input']];bt=[bw['trace']] if isinstance(bw['trace'][0],(int,float)) else bw['trace']
    with localcontext() as ctx:
        ctx.prec=160;bc,bn=baseline_analyze(bw['cfg'],bu,bt)
    check('baseline','saved_v65_independent_equations',all(bc.values()))
    stop=F(bw['cfg'][35])*(F(bw['cfg'][59])-F(bw['cfg'][36]))
    check('baseline','v65_actual_stop_overshoot',F(bt[0][36])>stop)
    rr=runs['stop_overshoot_repair'];tr=rr['trace'];tr=[tr] if isinstance(tr[0],(int,float)) else tr
    check('repair','same_binary_equipment_input',rr['cfg']==bw['cfg'] and rr['input']==bw['input'])
    check('repair','v66_stop_withholds_charge',tr[0][121]==0 and F(tr[0][37])<stop and tr[0][54]==0)
    comparisons=[]
    for id,r in runs.items():
        if not id.startswith('repeated_'):continue
        tr=r['trace'];on=[int(x[54]) for x in tr];ons=sum(a==0 and b==1 for a,b in zip(on,on[1:]));offs=sum(a==1 and b==0 for a,b in zip(on,on[1:]))
        check('repeated',id+'_four_restarts',ons>=3 and offs>=4)
        check('repeated',id+'_cutoff_no_credit',sum(x[122]==0 and x[124]>0 for x in tr)>=4)
        check('repeated',id+'_port_handoffs',all(x[159:161]==old[36:38] for old,x in zip(tr,tr[1:])))
        with localcontext() as ctx:
            ctx.prec=120;ev=compare(r['cfg'],r['input'])
            ctx.prec=160;ev2=compare(r['cfg'],r['input'])
            check('earliest',id+'_event_types',[x['kind'] for x in ev['events']]==[x['kind'] for x in ev2['events']])
            for key in ev['ports']:
                check('earliest',id+'_precision_'+key,abs(D(ev['ports'][key])-D(ev2['ports'][key]))<D('1e-95'))
            for a,b in zip(ev['events'],ev2['events']):
                check('earliest',id+'_root_'+str(a['tick'])+'_'+a['kind'],abs(D(a['time'])-D(b['time']))<D('1e-95'))
        check('earliest',id+'_repeated_stop_cutoff',sum(x['kind']=='thermal_stop_OFF' for x in ev['events'])>=4 and sum(x['kind']=='cutoff' for x in ev['events'])>=4)
        sampled={name:[tr[-1][idx-1],tr[-1][idx]] for name,idx in [('heat',41),('delivered',142),('boiler',144),('unmet',150)]}
        comparisons.append(dict(id=id,dt=r['input'][0][4],sampled_enclosures=sampled,earliest=ev2,observed_restarts=ons,observed_shutdowns=offs))
    (folder/'earliest_comparisons_v66.json').write_text(json.dumps(comparisons,indent=2)+'\\n')
"""
    assert anchor in s;s=s.replace(anchor,extra+'\n    '+anchor)
    dst.write_text(s)

if __name__=='__main__':main()
