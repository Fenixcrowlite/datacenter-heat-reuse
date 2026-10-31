from pathlib import Path
p=Path(__file__).with_name("run_a40.m")
s=p.read_text(encoding="utf-8-sig")
def replace_once(a,b):
    global s
    if s.count(a)!=1:
        raise SystemExit(f"Expected once ({s.count(a)}): {a[:70]}")
    s=s.replace(a,b)
replace_once("c.Position=[260 210 150 80];","""c.Position=[260 210 150 80];
z=Stateflow.State(ch);
z.LabelString=sprintf('TES_FULL\\nentry: mode=3; shedFraction=0; alarm=1;');
z.Position=[45 210 130 80];""")
replace_once("t.LabelString='[requiredW > capacityW + 1e-6]';","t.LabelString='[requiredW > capacityW + 1e-6 && tempC < 42 && capacityW > 0]';")
replace_once("t.LabelString='[requiredW + 5000 <= capacityW && tempC < 39]';","t.LabelString='[requiredW + 5000 <= capacityW && tempC < 39 && soc < 0.999]';")
replace_once("""t.LabelString='[tempC >= 42 || capacityW <= 0]';
% Precedence for NORMAL -> CRITICAL before NORMAL -> DEGRADED.""","""t.LabelString='[tempC >= 42 || capacityW <= 0]';
t=Stateflow.Transition(ch);t.Source=n;t.Destination=z;
t.LabelString='[soc >= 0.999 && requiredW <= capacityW && tempC < 42 && capacityW > 0]';
t=Stateflow.Transition(ch);t.Source=z;t.Destination=n;
t.LabelString='[soc <= 0.98 && requiredW + 5000 <= capacityW && tempC < 39]';
t=Stateflow.Transition(ch);t.Source=z;t.Destination=d;
t.LabelString='[requiredW > capacityW + 1e-6 && tempC < 42 && capacityW > 0]';
t=Stateflow.Transition(ch);t.Source=z;t.Destination=c;
t.LabelString='[tempC >= 42 || capacityW <= 0]';
t=Stateflow.Transition(ch);t.Source=d;t.Destination=z;
t.LabelString='[soc >= 0.999 && requiredW + 5000 <= capacityW && tempC < 39]';
% All critical transitions are disjoint from capacity-only guards.""")
replace_once("assert(numel(trs)==6,'A40:Transitions');","assert(numel(trs)==11,'A40:Transitions');")
replace_once("""assert(all(ismember(m(:,end),[0,1,2])),'A40:Modes');
assert(all(abs(f(:,end)-0.4*(m(:,end)>0))<1e-12),'A40:Shed');
assert(all(a(:,end)==m(:,end)),'A40:Alarm');""","""assert(all(ismember(m(:,end),[0,1,2,3])),'A40:Modes');
assert(all(abs(f(:,end)-0.4*ismember(m(:,end),[1,2]))<1e-12),'A40:Shed');
assert(all(a(:,end)==min(m(:,end),2)-(m(:,end)==3)),'A40:Alarm');
trace=table(tgrid,double(vals{1}),double(vals{2}),double(vals{3}),double(vals{4}), ...
 m(:,end),f(:,end),a(:,end),'VariableNames', ...
 {'t_s','required_W','capacity_W','temperature_C','tes_soc','mode','shed_fraction','alarm'});
writetable(trace,fullfile(here,'STATEFLOW_TRACE.csv'));""")
replace_once("""'mode_counts',[sum(m(:,end)==0),sum(m(:,end)==1),sum(m(:,end)==2)], ...""","""'mode_counts',[sum(m(:,end)==0),sum(m(:,end)==1),sum(m(:,end)==2),sum(m(:,end)==3)], ...""")
p.write_text(s,encoding="utf-8")
print("PATCHED_A40_4MODES")
