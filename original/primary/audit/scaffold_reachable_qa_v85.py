from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=(R/'audit/electrical_ceiling_v83r2.py').read_text().replace('v83r2','v85').replace("version='0.83'","version='0.85'")
start=s.index('def prepare():');end=s.index('def electrical_checks',start)
s=s[:start]+'''def prepare():
    old=json.loads((ROOT/'results/electrical_conservatism_v84_20261013T105537_783028Z/spec.json').read_text())
    cases=copy.deepcopy(old['cases'])
    for c in cases:c['compare80']=c['family']=='six_mode' or c['family']=='event_control'
    for c in copy.deepcopy(cases):
        if c['family']=='charge':
            c['id']='loss_'+c['id'];c['p'][5]=.01;c['family']='positive_loss_charge';cases.append(c)
    c=copy.deepcopy(cases[1]);c.update(id='binding_stop',family='binding_stop',compare80=False,ceiling_MW=.2,initial=[9.5,1,1])
    c['p'][9]=c['p'][23]=0.;c['schedule']=[[.25,(j+1)*.25,0.,20.,1.,1.] for j in range(4)];cases.append(c)
    c=copy.deepcopy(cases[1]);c.update(id='zero_ceiling',family='zero',compare80=False,ceiling_MW=0.);cases.append(c)
    for c in cases:c['horizon_h']=sum(s[0] for s in c['schedule'])*1.01
    folder=ROOT/'results'/('reachable_cap_v85_'+stamp());folder.mkdir()
    dump(folder/'spec.json',dict(version='0.85',cases=cases,evidence_class='SYNTHETIC_CERTIFIED_WHOLE_SCHEDULE_CAP_NOT_DYNAMIC_MAXIMUM',
        required_modes=list(range(6)),required_events=[1,2,3],required_floor_crossing=True))
    preserved=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    dump(folder/'preservation.json',[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in preserved])
    dump(folder/'ledger_prefixes.json',[dict(path=p,size=(ROOT/p).stat().st_size,sha256=sha(ROOT/p)) for p in LEDGERS])
    sources=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'audit').glob('*.py'))+[ROOT/'audit/run_electrical_ceiling_v85.ps1',ROOT/'audit/Reachable_cap_derivation_v85.md']
    records=[]
    for p in sources:
        rel=p.relative_to(ROOT);dst=folder/'source_snapshot'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
        records.append(dict(path=rel.as_posix(),sha256=sha(p)))
    dump(folder/'source_hashes.json',records);print(folder.relative_to(ROOT).as_posix())

''' + s[end:]
start=s.index('def electrical_checks');end=s.index('def verify(',start)
s=s[:start]+'''def electrical_checks(r):
    p=list(map(F,r['raw_policy']));pe=list(map(F,r['p']));checks=[]
    def check(name,ok):checks.append(dict(name=r['id']+'_'+name,passed=bool(ok)))
    certs=rows(r['certificate']);Eb=F(certs[0][28]);E0=F(r['adapter']['initial'][0])
    Te=p[11]-p[12]-p[13];A=p[14]*(Te+F(273.15));Lf=p[18]+p[19]+p[17]-Te
    universal=p[25]*(1+A/Lf);charge=min(p[8],p[10],universal)
    reach=min(p[0]*(p[2]-p[1]),E0+p[6]*charge*p[26])
    Lmax=max(p[18]+p[19],p[1]+Eb/p[0]+p[16])+p[17]-Te
    exact_cap=min(p[10],p[25]*(1+A/Lmax))
    check('reachable_upper_enclosure',Eb>=reach)
    check('cap_safe',0<=pe[10]<=exact_cap)
    check('cap_tight',exact_cap-pe[10]<=max(F(1),abs(exact_cap))*F(1,10**12))
    check('only_thermal_cap_changed',pe[:10]+pe[11:]==p[:10]+p[11:25])
    check('declared_horizon_covers_exact_holds',sum((F(v[4]) for v in rows(r['input'])),F(0))<=p[26])
    for k,(row,cert) in enumerate(zip(rows(r['trace']),certs)):
        check(f'{k}_raw_certificate',list(map(F,cert))==p+[pe[10],Eb])
        check(f'{k}_committed_clock_within_horizon',F(row[60])<=p[26])
        for j in range(int(row[12])):
            z=list(map(F,row[100+80*j:180+80*j]));q=z[23];ehi=max(z[11],z[13])
            Lhi=max(p[18]+p[19],p[1]+ehi/p[0]+p[16])+p[17]-Te
            check(f'{k}_{j}_selected_cap',q<=pe[10])
            check(f'{k}_{j}_reachable_segment',ehi<=Eb)
            check(f'{k}_{j}_pointwise_electricity',q*Lhi/(A+Lhi)<=p[25])
            if p[25]==0:check(f'{k}_{j}_zero_exact',q==0 and z[35]==z[36]==0)
    return checks

''' + s[end:]
s=s.replace('electrical_ceiling_v83.mat','electrical_ceiling_v85.mat').replace('independent_QA_v83_','independent_QA_v85_').replace('closed_numeric_v83_','closed_numeric_v85_')
s=s.replace("==c['p']+[c['ceiling_MW']]","==c['p']+[c['ceiling_MW'],c['horizon_h']]")
s=s.replace("if r['raw_policy'][25]==.01","if r['raw_policy'][25]==.05")
s=s.replace("check('scope','25_schedules',len(report['runs'])==25)","check('scope','all_predeclared_schedules',len(report['runs'])==len(spec['cases']))")
s=s.replace("'four_actual_refusals',len(report['faults'])==4","'five_actual_refusals',len(report['faults'])==5")
anchor='    selfchecks=[]'
s=s.replace(anchor,'''    comparisons=[];observed_events=set();floor_crossings=0
    with localcontext() as ctx:
        ctx.prec=160
        for r in report['runs']:
            g=copy.deepcopy(r);g['trace']=rows(r['global_trace']);g['p']=g['trace'][0][75:100]
            for row in g['trace']:row[1]=73;row[72:75]=[0,0,0]
            gc,gn=analyze(g)
            for c in gc:check('global_closed_equations',c['name'],c['passed'])
            gt=total_earliest(g,gn);nt=totals[r['id']]
            comparisons.append(dict(id=r['id'],new_cap=r['p'][10],global_cap=g['p'][10],
                new_totals={k:str(v) for k,v in nt.items()},global_totals={k:str(v) for k,v in gt.items()}))
            check('comparison',r['id']+'_cap_ge_global',r['p'][10]>=g['p'][10])
            p=list(map(F,r['p']));floorE=p[0]*(p[18]+p[19]-p[1]-p[16])
            for row in rows(r['trace']):
                for j in range(int(row[12])):
                    z=row[100+80*j:180+80*j];observed_events.add(z[2])
                    if r['family']=='positive_loss_charge' and F(z[11])<floorE<F(z[12]):floor_crossings+=1
    check('scope','stop_cutoff_restart_events',set([1,2,3])<=observed_events)
    check('scope','positive_loss_floor_crossing',floor_crossings>0)
    check('scope','binding_stop_event',any(row[102]==1 for r in report['runs'] if r['family']=='binding_stop' for row in rows(r['trace'])))
    dump(folder/'comparisons_v85.json',comparisons)
''' + anchor)
with (R/'audit/reachable_cap_v85.py').open('x',encoding='utf-8',newline='\n') as f:f.write(s)
print('Added independent rational/closed-equation QA and predeclared cases.')
