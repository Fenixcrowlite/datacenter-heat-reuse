from pathlib import Path
import re,hashlib,json
root=Path(r'C:\Users\Lysda\Desktop\SynapseControlCenter\recovery')
src=root/'AUTONOMOUS_RUN_20261026_2255_A46_INTEGRATION'/'build_a46.m'
out=root/'AUTONOMOUS_RUN_20261027_0048_A48_GRAPHICAL_COUPLING_CANDIDATE'
out.mkdir(exist_ok=True)
s=src.read_text(encoding='utf-8')
s=s.replace('% A43 standalone executable Simulink MATLAB Function (Stateflow.EMChart).','% A48: isolated graphical Stateflow controller with separate EMChart thermal plant.')
s=s.replace("mdl='DCHR_A46_Compressor_Closed_Loop';","mdl='DCHR_A48_Graphical_Closed_Loop';")
s=s.replace('function [Tnext,Enext,mode,active,residual,unhandled,served,required,capout,itres,tesres] = step(qdc,hxIn,leakIn,qcharge,qdis,qpool,qdh,nominalCap)','function [Tnext,Enext,mode,active,residual,unhandled,served,required,capout,itres,tesres] = step(qdc,hxIn,leakIn,qcharge,qdis,qpool,qdh,nominalCap,modeIn)')
s=s.replace('persistent E T state prevActive prevShed pending good res lastTrip effCap hpAvailable','persistent E T prevActive prevShed prevMode res lastTrip effCap hpAvailable')
s=s.replace('E=450*3.6e6;T=30;state=0;prevActive=0;prevShed=0;pending=0;good=0;res=0;lastTrip=false;effCap=330000;hpAvailable=0;','E=450*3.6e6;T=30;prevActive=0;prevShed=0;prevMode=0;res=0;lastTrip=false;effCap=330000;hpAvailable=0;')
start=s.index('"fault=nominalCap<=0 || T>=42;"')
end=s.index('"if state==2 && ~lastTrip"',start)
old=s[start:end]
idx=old.index('" h0=min(hxIn,qdc);')
normal=old[idx:old.rfind('"end"')]
new='''"state=modeIn;"
"if state==1"
" active=qdc;"
"elseif state==2"
" active=0;"
"elseif state==3"
" active=min(qdc,prevActive+15000);"
"elseif prevMode==3"
" active=qdc;"
"else"
'''+normal+'''"end"
'''
s=s[:start]+new+s[end:]
s=s.replace('"E=Enext;T=Tnext;prevActive=active;prevShed=qdc-active;lastTrip=(state==2);"','"E=Enext;T=Tnext;prevActive=active;prevShed=qdc-active;prevMode=state;lastTrip=(state==2);"')
needle="chart.Script=strjoin(code,newline);"
assert s.count(needle)==1
insertion=r"""
% Copy the ACTUAL graphical A44 Stateflow chart, not an EMChart FSM.
a44file=fullfile(fileparts(here),'AUTONOMOUS_RUN_20261026_2050_A44_GRAPHICAL_STATEFLOW','DCHR_A44_Graphical_Supervisor.slx');
load_system(a44file);
add_block('DCHR_A44_Graphical_Supervisor/Supervisor',[mdl '/GraphicalSupervisor'],...
    'Position',[730 790 950 1010]);
% Combinational input adapter; feedback enters through discrete Unit Delay.
add_block('simulink/User-Defined Functions/MATLAB Function',[mdl '/SupervisorSignals'],...
    'Position',[360 800 600 980]);
ad=rt.find('-isa','Stateflow.EMChart','Path',[mdl '/SupervisorSignals']);
assert(isscalar(ad),'A48:SignalAdapter');
ad.Script=sprintf(['function [fault,recover,rampDone] = signals(Tstart,previousActive,qdc,nominalCap)\n' ...
    '%%#codegen\n' ...
    'fault=(nominalCap<=0 || Tstart>=42);\n' ...
    'recover=(nominalCap>0 && Tstart<36);\n' ...
    'rampDone=(previousActive+15000>=qdc-1e-8);\n' ...
    'end\n']);
"""
s=s.replace(needle,needle+'\n'+insertion)
needle2="set_param(mdl,'Solver','FixedStepDiscrete'"
assert s.count(needle2)==1
wiring=r"""
% Stateflow mode is the ONLY state-machine output used by the plant.
add_block('simulink/Discrete/Unit Delay',[mdl '/DelayTemp'],...
    'InitialCondition','30','SampleTime','900','Position',[1200 790 1250 820]);
add_block('simulink/Discrete/Unit Delay',[mdl '/DelayActive'],...
    'InitialCondition','0','SampleTime','900','Position',[1200 850 1250 880]);
add_line(mdl,'CoupledController/1','DelayTemp/1','autorouting','on');
add_line(mdl,'CoupledController/4','DelayActive/1','autorouting','on');
add_line(mdl,'DelayTemp/1','SupervisorSignals/1','autorouting','on');
add_line(mdl,'DelayActive/1','SupervisorSignals/2','autorouting','on');
add_line(mdl,'Signal_1/1','SupervisorSignals/3','autorouting','on');
add_line(mdl,'Signal_8/1','SupervisorSignals/4','autorouting','on');
for k=1:3
    add_line(mdl,sprintf('SupervisorSignals/%d',k),...
        sprintf('GraphicalSupervisor/%d',k),'autorouting','on');
end
add_line(mdl,'GraphicalSupervisor/1','CoupledController/9','autorouting','on');
add_block('simulink/Sinks/Terminator',[mdl '/UnusedAlarm'],...
    'Position',[1020 930 1040 950]);
add_line(mdl,'GraphicalSupervisor/2','UnusedAlarm/1','autorouting','on');
"""
s=s.replace(needle2,wiring+'\n'+needle2)
s=s.replace("A46:","A48:").replace("A46_SIMULINK_","A48_SIMULINK_")
s=s.replace("'graphical_stateflow_chart_built',false,","'graphical_stateflow_chart_built',true,")
s=s.replace("'state_machine_implemented_in_EMChart',true,","'state_machine_implemented_in_EMChart',false,")
s=s.replace("'SIMULINK_A46_RESULT.json'","'SIMULINK_A48_RESULT.json'")
s=s.replace("a46_sig_","a48_sig_").replace("a46_out_","a48_out_")
s=s.replace("A48_SIMULINK_EMCHART_COMPRESSOR_PARITY_PASS","A48_GRAPHICAL_COUPLED_PARITY_PASS")
assert '"state=modeIn;"' in s and '"fault=nominalCap<=0 || T>=42;"' not in s
assert s.count("add_line(mdl,'GraphicalSupervisor/1','CoupledController/9'")==1
p=out/'build_a48.m';p.write_text(s,encoding='utf-8')
manifest={'status':'SOURCE_CANDIDATE_NOT_MATLAB_VALIDATED','source_a46_sha256':hashlib.sha256((src.parent/'DCHR_A46_Compressor_Closed_Loop.slx').read_bytes()).hexdigest(),'build_a48_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'physical_release':False,'model_generated':False}
(out/'SOURCE_CANDIDATE.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps(manifest,indent=2));print('PATH',p)
