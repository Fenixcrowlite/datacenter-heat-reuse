"""Additive source preparation; never edit a prior model/source release."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'matlab/simulink'
def write(name,text):
    path=HERE/name
    assert not path.exists(), path
    path.write_text(text,encoding='utf-8')

write('stateflow_choose_mode_v34.m',(HERE/'stateflow_choose_mode_v32.m').read_text().replace('v32','v34'))

s=(HERE/'stateflow_allocate_v32.m').read_text().replace('v32','v34')
s=s.replace('(mode,seg,cfg)','(mode,seg,cfg,clock)').replace('seg(9)];','seg(9);clock(1);seg(16);clock(2)];')
write('stateflow_allocate_v34.m',s)
s=(HERE/'stateflow_collect_v32.m').read_text().replace('v32','v34')
s=s.replace('index==1 || index==2','index>=1 && index<=64').replace('zeros(50,1)','zeros(1792,1)')
s=s.replace('if index==1,packed(1:25)=z;else,packed(26:50)=z;end','packed((double(index)-1)*28+(1:28))=z;')
write('stateflow_collect_v34.m',s)
s=(HERE/'build_dispatch_stateflow_v32.m').read_text().replace('v32','v34')
s=s.replace('plan=make_plan(x,E,p,h,dt)','plan=make_plan(x,E,p,h,dt,m,c)').replace('zeros(14,2)','zeros(18,64)')
s=s.replace('dchr_segment_plan_v34(x,E,p,h,dt)','dchr_segment_plan_v34(x,E,p,h,dt,m,c)')
s=s.replace("'IterationLimit','2'","'IterationLimit','64'")
s=s.replace("'[14 1]'","'[18 1]'").replace("'[50 1]'","'[1792 1]'").replace("'[25 1]'","'[28 1]'")
s=s.replace('Trace=zeros(50,1)','Trace=zeros(1792,1)')
s=s.replace('stateflow_allocate_v34(%d,segmentInput,parameters)','stateflow_allocate_v34(%d,segmentInput,parameters,hpClock)')
s=s.replace("data(ch,'iteration','Input',3,'1');","data(ch,'iteration','Input',3,'1');data(ch,'hpClock','Input',4,'[2 1]');")
s=s.replace("'Release 0.32: two ordered analytic intra-interval segments; actual guarded state execution each iteration. Offsets are physical event times; Simulink clock stays at macro sample start. Normal-mode host HP.'", "'Release 0.34: bounded physical-hour events, actual persistent HP ON/OFF supervisor and six guarded thermal modes. Normal-mode host HP planner.'")
s=s.replace("f.Script=fileread(fullfile(here,'stateflow_contract_gate_v34.m'));", "f.Script=fileread(fullfile(here,'stateflow_contract_gate_v34.m'));")
point="add_block('simulink/Ports & Subsystems/Out1',[sub '/Trace']"
supervisor="""add_block('simulink/Ports & Subsystems/In1',[sub '/Control'],'Port','3','Position',[20 220 50 235]);
add_block('sflib/Chart',[sub '/HP_Supervisor'],'Position',[270 240 490 350]);
hc=rt.find('-isa','Stateflow.Chart','Path',[sub '/HP_Supervisor']);
hc.ActionLanguage='MATLAB';hc.ChartUpdate='INHERITED';hc.ExecuteAtInitialization=false;
hc.Description='Persistent HP latch and explicit physical-hour elapsed timer. Safety capacity/input infeasibility overrides ON dwell; OFF dwell remains binding.';
data(hc,'s','Input',1,'[18 1]');data(hc,'p','Input',2,'[1 11]');data(hc,'c','Input',3,'[1 4]');
data(hc,'clock','Output',1,'[2 1]');
d=Stateflow.Data(hc);d.Name='age';d.Scope='Local';d.DataType='double';d.Props.InitialValue='0';
f=Stateflow.EMFunction(hc);f.Name='stateflow_supervisor_guard_v34';f.Position=[40 400 260 70];
f.Script=fileread(fullfile(here,'stateflow_supervisor_guard_v34.m'));
hs=cell(2,1);
for k=1:2
    a=Stateflow.State(hc);a.Name='HP_OFF';if k==2,a.Name='HP_ON';end
    a.Position=[70+(k-1)*300 70 250 210];
    a.LabelString=sprintf(['%s\\nen:\\nage=s(16);\\n' ...
        'assert(s(15)==%d);\\nage=age+s(1);\\nclock=[%d;age];\\n' ...
        'du:\\nassert(s(15)==%d);\\nassert(abs(age-s(16))<=1e-9);\\n' ...
        'age=age+s(1);\\nclock=[%d;age];'],a.Name,k-1,k-1,k-1,k-1);
    hs{k}=a;
end
jj=Stateflow.Junction(hc);jj.Position.Center=[35 35];jj.Position.Radius=8;
t=Stateflow.Transition(hc);t.Destination=jj;t.DestinationOClock=12;t.SourceEndPoint=[35 5];t.MidPoint=[35 15];
for k=1:2
    t=Stateflow.Transition(hc);t.Source=jj;t.Destination=hs{k};t.SourceOClock=3;t.DestinationOClock=12;
    t.LabelString=sprintf('[s(15)==%d]',k-1);
end
for k=1:2
    n=3-k;t=Stateflow.Transition(hc);t.Source=hs{k};t.Destination=hs{n};t.SourceOClock=3;t.DestinationOClock=9;
    t.LabelString=sprintf('[s(15)==%d && stateflow_supervisor_guard_v34(%d,s,p,c,age)]',n-1,n-1);
end
add_block('simulink/Ports & Subsystems/Out1',[sub '/Clock'],'Port','2','Position',[550 260 580 275]);
add_line(sub,'Select_Segment/1','HP_Supervisor/1');add_line(sub,'Parameters/1','HP_Supervisor/2');
add_line(sub,'Control/1','HP_Supervisor/3');add_line(sub,'HP_Supervisor/1','Thermal_Dispatch/4');
add_line(sub,'HP_Supervisor/1','Clock/1');
"""
s=s.replace(point,supervisor+point)
point="add_block('simulink/User-Defined Functions/MATLAB Function',[mdl '/Segment_HP_Plan']"
memory="""assignin(mw,'dchr_c_v34',[8 .25 .25 64]);assignin(mw,'dchr_m0_v34',[1;0]);
add_block('simulink/Sources/Constant',[mdl '/Control_Parameters'],'Value','dchr_c_v34','Position',[20 420 150 450]);
add_block('simulink/Discrete/Unit Delay',[mdl '/HP_Clock_Memory'],'InitialCondition','dchr_m0_v34', ...
    'SampleTime','dchr_dt_v34','Position',[500 470 550 510]);
add_block('simulink/Sinks/To Workspace',[mdl '/Clock_Start_Trace'],'VariableName','clock_start_trace_v34', ...
    'SaveFormat','Timeseries','Position',[1030 450 1190 480]);
add_block('simulink/Sinks/To Workspace',[mdl '/Clock_End_Trace'],'VariableName','clock_end_trace_v34', ...
    'SaveFormat','Timeseries','Position',[1030 520 1190 550]);
"""
s=s.replace(point,memory+point)
s=s.replace("'TES_Energy_Memory/1','Energy_Start_Trace/1'};", """'TES_Energy_Memory/1','Energy_Start_Trace/1'; ...
    'HP_Clock_Memory/1','Segment_HP_Plan/6';'Control_Parameters/1','Segment_HP_Plan/7'; ...
    'Control_Parameters/1','Execute_Segments/3';'Execute_Segments/2','Runtime_Contract_Gate/7'; ...
    'HP_Clock_Memory/1','Runtime_Contract_Gate/8';'Control_Parameters/1','Runtime_Contract_Gate/9'; ...
    'Runtime_Contract_Gate/3','HP_Clock_Memory/1';'HP_Clock_Memory/1','Clock_Start_Trace/1'; ...
    'Runtime_Contract_Gate/3','Clock_End_Trace/1'};""")
write('build_dispatch_stateflow_v34.m',s)

s=(HERE/'stateflow_contract_gate_v32.m').read_text().replace('v32','v34')
s=s.replace('[checked,summary]=stateflow_contract_gate_v34(raw,plan,x,cfg,h,model_dt)',
            '[checked,summary,nextClock]=stateflow_contract_gate_v34(raw,plan,x,cfg,h,model_dt,clock,m,c)')
s=s.replace('for k=1:2','offset=0;previousE=plan(2,1);prevOn=m(1);prevAge=m(2);\nfor k=1:64')
s=s.replace('raw((k-1)*25+(1:25))','raw((k-1)*28+(1:28))')
s=s.replace("z(24)==s(13) && ismember(z(24),[0 1 2])","z(24)==s(13) && ismember(z(24),[0 1 2 3 4])")
start=s.index('first=raw(1:25);last=raw(26:50);')
end=s.index('supplied=(energy(1)+energy(3)+energy(4))/dt;',start)
s=s[:start]+"""first=raw(1:28);last=raw(1765:1792);
tol=1e-9*max(1,cap+(energy(6)+cfg(11)*dt));
assert(abs(offset-dt)<=tol,'Interval partition failure.');
assert(all(abs(clock-[prevOn;prevAge])<=tol),'Final persistent supervisor clock mismatch.');
nextClock=clock;
"""+s[end:]
point='    energy=energy+[z(6:14)]*span;loss=loss+z(17:19);'
checks="""    assert(abs(z(3)-offset)<=tol && abs(z(4)-previousE)<=tol,'Ordered event/energy handoff failure.');
    assert(z(26)==s(15) && ismember(z(26),[0 1]) && abs(z(27)-s(16))<=tol && ...
        abs(z(28)-z(27)-span)<=tol && abs(z(28)-s(18))<=tol,'Physical-hour clock failure.');
    if z(26)~=prevOn
        assert(stateflow_supervisor_guard_v34(z(26),s,cfg,c,prevAge),'Unauthorized HP latch transition.');
    else
        assert(s(17)==0 && abs(z(27)-prevAge)<=tol,'Persistent timer continuity failure.');
    end
    if span>0
        assert((z(26)==0 && z(11)==0) || (z(26)==1 && z(11)>0),'HP latch/allocation mismatch.');
    end
    if z(24)==1,assert(abs(z(5)-cap)<=tol,'Capacity event mismatch.');end
    if z(24)==2,assert(abs(z(5)-cfg(8))<=tol,'Cutoff event mismatch.');end
    prevOn=z(26);prevAge=z(28);previousE=z(5);offset=offset+span;
"""
s=s.replace(point,checks+point)
# A MATLAB Function block cannot resolve an embedded function in another chart.
s+='\n'+(HERE/'stateflow_supervisor_guard_v34.m').read_text()
write('stateflow_contract_gate_v34.m',s)
print('Prepared additive v34 sources.')
