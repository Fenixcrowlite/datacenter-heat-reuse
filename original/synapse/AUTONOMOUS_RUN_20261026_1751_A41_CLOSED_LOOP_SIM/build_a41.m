% A41: isolated synthetic Stateflow + TES + IT thermal feedback model.
% NO hardware interfaces, production model changes, or physical certification.
here=fileparts(mfilename('fullpath'));
srcdir=fullfile(fileparts(here),'AUTONOMOUS_RUN_20261026_1650_A40_STATEFLOW_SUPERVISOR');
srcfile=fullfile(srcdir,'DCHR_A40_Safety_Controller.slx');
assert(exist(srcfile,'file')==2,'A41:MissingA40');
assert(license('test','Stateflow') && license('test','Simulink'),'A41:License');
srcmdl='DCHR_A40_Safety_Controller';
mdl='DCHR_A41_Closed_Loop';
if bdIsLoaded(mdl),close_system(mdl,0);end
load_system(srcfile);
new_system(mdl);
add_block([srcmdl '/Supervisor'],[mdl '/Supervisor'],'Position',[750 140 950 330]);
add_block('simulink/User-Defined Functions/MATLAB Function',[mdl '/TESDispatch'], ...
    'Position',[420 90 620 290]);
add_block('simulink/User-Defined Functions/MATLAB Function',[mdl '/ThermalPlant'], ...
    'Position',[1100 110 1300 320]);
rt=sfroot;
tes=rt.find('-isa','Stateflow.EMChart','Path',[mdl '/TESDispatch']);
plant=rt.find('-isa','Stateflow.EMChart','Path',[mdl '/ThermalPlant']);
assert(isscalar(tes) && isscalar(plant),'A41:EMChart');
tes.Script=strjoin({
'function [required,Enew,sourceNew,tesResidual] = f_tes(qcharge,qdis,qpool,qdh,pold,qsourceold,qrejectbase,E)'
'%#codegen'
'dt=900; Emax=900*3.6e6;'
'loss=.002*E/86400;'
'room=max(0,(Emax-E+dt*(qdis/.91+loss))/(dt*.93));'
'charge=min(qcharge,room);'
'Enew=max(0,min(Emax,E+dt*(.93*charge-qdis/.91-loss)));'
'oldCond=qpool+qdh+qcharge;'
'newCond=oldCond-(qcharge-charge);'
'if oldCond>1e-8'
'    newPower=pold*newCond/oldCond;'
'else'
'    newPower=0;'
'end'
'sourceNew=newCond-newPower;'
'required=max(0,qrejectbase+qsourceold-sourceNew);'
'tesResidual=Enew-E-dt*(.93*charge-qdis/.91-loss);'
},newline);
plant.Script=strjoin({
'function [Tnew,shed,rejected,unhandled,dcResidual,passive] = f_plant(qdc,hx,leak,sourceNew,required,cap,mode,Tprev,prevShed)'
'%#codegen'
'dt=900;'
'if mode==1 || mode==2'
'    ceiling=.4;'
'else'
'    ceiling=0;'
'end'
'target=min([max(0,required-cap),ceiling*qdc,required]);'
'if ceiling>0'
'    shed=min(target,min(prevShed,qdc)+15000);'
'else'
'    shed=0;'
'end'
'rejected=min(required-shed,cap);'
'unhandled=max(0,required-shed-rejected);'
'passive=2000*max(0,Tprev-30);'
'Tnew=max(30,Tprev+dt*(unhandled-passive)/8e6);'
'dcResidual=qdc-shed-hx-sourceNew-leak-rejected-unhandled;'
},newline);
% Delays break feedback loops: current Stateflow sees last completed step.
add_block('simulink/Discrete/Unit Delay',[mdl '/TemperatureMemory'], ...
    'InitialCondition','30','Position',[1470 350 1510 390]);
add_block('simulink/Discrete/Unit Delay',[mdl '/TESMemory'], ...
    'InitialCondition',num2str(450*3.6e6,17),'Position',[690 420 730 460]);
add_block('simulink/Discrete/Unit Delay',[mdl '/ShedMemory'], ...
    'InitialCondition','0','Position',[1470 440 1510 480]);
add_block('simulink/Math Operations/Gain',[mdl '/SOC'], ...
    'Gain',num2str(1/(900*3.6e6),17),'Position',[760 420 830 460]);
add_line(mdl,'TESMemory/1','SOC/1','autorouting','on');
add_line(mdl,'SOC/1','Supervisor/4','autorouting','on');
add_line(mdl,'TemperatureMemory/1','Supervisor/3','autorouting','on');
add_line(mdl,'TESDispatch/1','Supervisor/1','autorouting','on');
add_line(mdl,'TESDispatch/2','TESMemory/1','autorouting','on');
add_line(mdl,'ThermalPlant/1','TemperatureMemory/1','autorouting','on');
add_line(mdl,'ThermalPlant/2','ShedMemory/1','autorouting','on');
% External synthetic inputs, all from A36/A38, never from equipment.
tb=readtable(fullfile(here,'INPUTS_A41.csv'));
assert(height(tb)==672,'A41:InputCount');
tgrid=(0:671)'*900;
fields={'qdc','hx','leak','qcharge','qdis','qpool','qdh','pold','qsourceold','qrejectbase','capacity'};
for k=1:numel(fields)
    sig=sprintf('a41_sig_%d',k);
    if k<=10
        vals=double(tb.(fields{k}));
    else
        vals=330000*ones(672,1);
    end
    assignin('base',sig,[[tgrid;tgrid(end)+900],[vals;vals(end)]]);
    bn=sprintf('%s/Signal_%d',mdl,k);
    add_block('simulink/Sources/From Workspace',bn,'VariableName',sig, ...
        'Interpolate','on','Position',[20 40+65*k 180 65+65*k]);
end
% TES inputs qcharge,qdis,qpool,qdh,pold,qsourceold,qrejectbase,Eprev
for k=1:7
    add_line(mdl,sprintf('Signal_%d/1',k+3),sprintf('TESDispatch/%d',k),'autorouting','on');
end
add_line(mdl,'TESMemory/1','TESDispatch/8','autorouting','on');
% ThermalPlant qdc,hx,leak,sourceNew,required,cap,mode,Tprev,prevShed
for k=1:3
    add_line(mdl,sprintf('Signal_%d/1',k),sprintf('ThermalPlant/%d',k),'autorouting','on');
end
add_line(mdl,'TESDispatch/3','ThermalPlant/4','autorouting','on');
add_line(mdl,'TESDispatch/1','ThermalPlant/5','autorouting','on');
add_line(mdl,'Signal_11/1','Supervisor/2','autorouting','on');
add_line(mdl,'Signal_11/1','ThermalPlant/6','autorouting','on');
add_line(mdl,'Supervisor/1','ThermalPlant/7','autorouting','on');
add_line(mdl,'TemperatureMemory/1','ThermalPlant/8','autorouting','on');
add_line(mdl,'ShedMemory/1','ThermalPlant/9','autorouting','on');
% Export numerical trajectories for independent Python and MATLAB comparison.
outNames={'mode','temp','energy','shed','required','reject','unhandled','dcres','tesres','alarm'};
outSources={'Supervisor/1','ThermalPlant/1','TESDispatch/2','ThermalPlant/2', ...
            'TESDispatch/1','ThermalPlant/3','ThermalPlant/4','ThermalPlant/5', ...
            'TESDispatch/4','Supervisor/3'};
for k=1:numel(outNames)
    bn=sprintf('%s/Out_%s',mdl,outNames{k});
    add_block('simulink/Sinks/To Workspace',bn,'VariableName',['a41_out_' outNames{k}], ...
        'SaveFormat','Array','Position',[1600 50+65*k 1730 75+65*k]);
    add_line(mdl,outSources{k},['Out_' outNames{k} '/1'],'autorouting','on');
end
set_param(mdl,'Solver','FixedStepDiscrete','FixedStep','900', ...
    'StopTime',num2str(671*900),'SaveTime','off');
save_system(mdl,fullfile(here,[mdl '.slx']));
results=struct();
cases={'both','main_only','backup_only','neither'};
for j=1:numel(cases)
    label=cases{j};
    reference=readtable(fullfile(here,['TRACE_A41_' label '.csv']));
    assert(height(reference)==672,'A41:ReferenceRows');
    cap=double(reference.capacity_W);
    assignin('base','a41_sig_11',[[tgrid;tgrid(end)+900],[cap;cap(end)]]);
    simout=sim(mdl,'ReturnWorkspaceOutputs','on');
    actual=struct();
    for k=1:numel(outNames)
        v=simout.get(['a41_out_' outNames{k}]);
        assert(size(v,1)==672,'A41:SimRows');
        actual.(outNames{k})=double(v(:,end));
    end
    check={
      'mode','mode',0;
      'temp','T_next_C',1e-8;
      'energy','E_next_J',2e-3;
      'shed','shed_W',1e-6;
      'required','required_W',1e-6;
      'reject','reject_W',1e-6;
      'unhandled','unhandled_W',1e-6;
      'dcres','dc_residual_W',1e-5;
      'tesres','tes_residual_J',2e-3;
      'alarm','alarm',0};
    diffs=zeros(size(check,1),1);
    for k=1:size(check,1)
        expected=double(reference.(check{k,2}));
        diffs(k)=max(abs(actual.(check{k,1})-expected));
        assert(diffs(k)<=check{k,3},'A41:Parity');
    end
    assert(all(actual.energy>=-1e-3 & actual.energy<=900*3.6e6+1e-3),'A41:TESBound');
    assert(max(abs(actual.dcres))<1e-5,'A41:EnergyBalance');
    assert(all(ismember(actual.mode,[0,1,2,3])),'A41:StateflowMode');
    result=struct('samples',672,'max_abs_diff',diffs', ...
       'max_temperature_C',max(actual.temp), ...
       'critical_steps',sum(actual.mode==2),'parity','PASS');
    results.(label)=result;
    writetable(table(tgrid,actual.mode,actual.temp,actual.energy,actual.shed, ...
        actual.required,actual.reject,actual.unhandled,actual.dcres,actual.tesres, ...
        'VariableNames',{'t_s','mode','T_next_C','E_next_J','shed_W','required_W', ...
        'reject_W','unhandled_W','dc_residual_W','tes_residual_J'}), ...
        fullfile(here,['MATLAB_TRACE_' label '.csv']));
    fprintf('A41_CLOSED_LOOP_PASS %s samples=672 maxT=%g critical=%d\n', ...
        label,result.max_temperature_C,result.critical_steps);
end
result=struct('status','STATEFLOW_CLOSED_LOOP_SIM_PASS','physical_release',false, ...
    'samples_per_scenario',672,'scenarios',results,'model',fullfile(here,[mdl '.slx']));
fid=fopen(fullfile(here,'MATLAB_RESULT.json'),'w');assert(fid>0);
fprintf(fid,'%s\n',jsonencode(result,PrettyPrint=true));fclose(fid);
fprintf('A41_ALL_SCENARIOS_PASS\n');
close_system(mdl,0);
close_system(srcmdl,0);
