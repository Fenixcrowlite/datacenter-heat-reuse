% A43 standalone executable Simulink MATLAB Function (Stateflow.EMChart).
% Synthetic only: not a physical safety controller, no equipment connections.
here=fileparts(mfilename('fullpath'));
a41=fullfile(fileparts(here),'AUTONOMOUS_RUN_20261026_1751_A41_CLOSED_LOOP_SIM');
assert(license('test','Simulink') && license('test','Stateflow'),'A43:License');
mdl='DCHR_A43_Finite_Trip_Closed_Loop';
if bdIsLoaded(mdl),close_system(mdl,0);end
new_system(mdl);
add_block('simulink/User-Defined Functions/MATLAB Function',[mdl '/CoupledController'], ...
    'Position',[500 180 790 440]);
rt=sfroot;
chart=rt.find('-isa','Stateflow.EMChart','Path',[mdl '/CoupledController']);
assert(isscalar(chart),'A43:EMChartNotFound');
code=[
"function [Tnext,Enext,mode,active,residual,unhandled,served,required,capout,itres,tesres] = step(qdc,hxIn,leakIn,qcharge,qdis,qpool,qdh,nominalCap)"
"%#codegen"
"persistent E T state prevActive prevShed pending good res lastTrip effCap"
"if isempty(E)"
" E=450*3.6e6;T=30;state=0;prevActive=0;prevShed=0;pending=0;good=0;res=0;lastTrip=false;effCap=330000;"
"end"
"dt=900;Emax=900*3.6e6;"
"effCap=min(nominalCap,effCap+60000);"
"fault=nominalCap<=0 || T>=42;"
"if (state==0 || state==3) && fault"
" state=1;pending=0;"
"end"
"if state==1 && ~fault && T<36"
" state=0;pending=0;"
"end"
"if state==1"
" if pending<2"
"  active=qdc;pending=pending+1;"
" else"
"  state=2;active=0;good=0;"
" end"
"elseif state==2"
" active=0;"
" if nominalCap>0 && T<36"
"  good=good+1;"
" else"
"  good=0;"
" end"
" if good>=2"
"  state=3;active=min(qdc,15000);"
" end"
"elseif state==3"
" active=min(qdc,prevActive+15000);"
" if active>=qdc-1e-8"
"  state=0;"
" end"
"else"
" h0=min(hxIn,qdc);l0=min(leakIn,max(0,qdc-h0));"
" av0=max(0,qdc-h0-l0);"
" demand=qpool+qdh;loss0=.002*E/86400;"
" dcap0=max(0,(E-dt*loss0)*.91/dt);"
" dis0=min([qdis,demand,dcap0]);"
" room0=max(0,(Emax-E+dt*(dis0/.91+loss0))/(dt*.93));"
" charge0=min(qcharge,room0);"
" need0=max(0,demand-dis0);desired0=need0+charge0;"
" cop0=max(2,min(5,3.5+.04*(T-30)));"
" source0=min(av0,desired0*(cop0-1)/cop0);"
" required0=max(0,qdc-h0-l0-source0);"
" target=min(.4*qdc,max(0,required0-effCap));"
" shed=min(target,prevShed+15000);"
" active=qdc-shed;"
"end"
"if state==2 && ~lastTrip"
" res=.12*prevActive;"
"elseif res>0"
" res=res*exp(-dt/3600);"
"end"
"active=min(active,max(0,qdc-res));"
"qit=active+res;"
"hx=min(hxIn,qit);leak=min(leakIn,max(0,qit-hx));"
"available=max(0,qit-hx-leak);"
"demand=qpool+qdh;loss=.002*E/86400;"
"discap=max(0,(E-dt*loss)*.91/dt);"
"dis=min([qdis,demand,discap]);"
"room=max(0,(Emax-E+dt*(dis/.91+loss))/(dt*.93));"
"creq=min(qcharge,room);need=max(0,demand-dis);"
"desired=need+creq;cop=max(2,min(5,3.5+.04*(T-30)));"
"source=min(available,desired*(cop-1)/cop);"
"power=source/(cop-1);cond=source+power;"
"servedhp=min(need,cond);charge=min(creq,max(0,cond-servedhp));"
"served=dis+servedhp;"
"Enext=max(0,min(Emax,E+dt*(.93*charge-dis/.91-loss)));"
"required=max(0,qit-hx-leak-source);"
"rejected=min(required,effCap);"
"unhandled=max(0,required-rejected);"
"passive=2000*max(0,T-30);"
"Tnext=max(30,T+dt*(unhandled-passive)/8e6);"
"itres=qit-hx-leak-source-rejected-unhandled;"
"tesres=Enext-E-dt*(.93*charge-dis/.91-loss);"
"mode=state;residual=res;capout=effCap;"
"E=Enext;T=Tnext;prevActive=active;prevShed=qdc-active;lastTrip=(state==2);"
"end"
];
chart.Script=strjoin(code,newline);
tb=readtable(fullfile(a41,'INPUTS_A41.csv'));
assert(height(tb)==672,'A43:InputCount');
fields={'qdc','hx','leak','qcharge','qdis','qpool','qdh'};
tgrid=(0:671)'*900;
for k=1:8
    name=sprintf('%s/Signal_%d',mdl,k);
    add_block('simulink/Sources/From Workspace',name, ...
        'VariableName',sprintf('a43_sig_%d',k), ...
        'Interpolate','on','Position',[40 60+75*k 220 90+75*k]);
    add_line(mdl,sprintf('Signal_%d/1',k),sprintf('CoupledController/%d',k),'autorouting','on');
end
outs={'temp','energy','mode','active','residual','unhandled','served','required','cap','itres','tesres'};
for k=1:numel(outs)
    add_block('simulink/Sinks/To Workspace',[mdl '/Out_' outs{k}], ...
        'VariableName',['a43_out_' outs{k}],'SaveFormat','Array', ...
        'Position',[1010 50+65*k 1180 80+65*k]);
    add_line(mdl,sprintf('CoupledController/%d',k), ...
        ['Out_' outs{k} '/1'],'autorouting','on');
end
set_param(mdl,'Solver','FixedStepDiscrete','FixedStep','900', ...
    'StopTime',num2str(671*900),'SaveTime','off');
save_system(mdl,fullfile(here,[mdl '.slx']));
cases={'both','main_only','backup_only','neither','CF_both','CF_backup_only','CF_neither'};
result=struct();totalChecks=0;
for j=1:numel(cases)
    label=cases{j};
    ref=readtable(fullfile(here,['TRACE_A43_' label '.csv']));
    vals=tb;
    if startsWith(label,'CF_')
        idx=97:384;
        vals.qpool(idx)=60000;vals.qdh(idx)=100000;vals.qdis(idx)=20000;
        vals.qcharge(idx)=0;vals.hx(idx)=0;vals.leak(idx)=0;
    end
    for k=1:8
        if k<=7
            y=double(vals.(fields{k}));
        else
            y=double(ref.nominal_cap_W);
        end
        assignin('base',sprintf('a43_sig_%d',k),[[tgrid;tgrid(end)+900],[y;y(end)]]);
    end
    simout=sim(mdl,'ReturnWorkspaceOutputs','on');
    expected={'T_next_C','E_next_J','state','active_it_W','residual_it_W', ...
        'unhandled_W','pool_dh_served_W','required_reject_W','effective_cap_W', ...
        'it_balance_W','tes_balance_J'};
    tolerance=[1e-7,1e-3,0,1e-6,1e-6,1e-6,1e-6,1e-6,1e-6,1e-5,1e-3];
    diff=zeros(1,numel(outs));
    actual=struct();
    for k=1:numel(outs)
        v=simout.get(['a43_out_' outs{k}]);
        assert(size(v,1)==672,'A43:SimRows');
        y=double(v(:,end));
        if k==3
            mapping=containers.Map({'ACTIVE','TRIP_PENDING','TRIPPED','RAMPING'},[0,1,2,3]);
            want=zeros(672,1);
            for ix=1:672
                want(ix)=mapping(char(string(ref.state(ix))));
            end
        else
            want=double(ref.(expected{k}));
        end
        diff(k)=max(abs(y-want));
        assert(diff(k)<=tolerance(k),'A43:Parity');
        actual.(outs{k})=y;
        totalChecks=totalChecks+numel(y);
    end
    result.(label)=struct('samples',672,'max_temperature_C',max(actual.temp), ...
        'max_abs_differences',diff,'parity','PASS');
    fprintf('A43_SIMULINK_PASS %s maxT=%g\n',label,max(actual.temp));
end
audit=struct('status','A43_SIMULINK_EMCHART_CLOSED_LOOP_PARITY_PASS', ...
    'model',fullfile(here,[mdl '.slx']), ...
    'samples',672*numel(cases),'numeric_comparisons',totalChecks, ...
    'physical_release',false,'graphical_stateflow_chart_built',false, ...
    'state_machine_implemented_in_EMChart',true,'scenarios',result);
fid=fopen(fullfile(here,'SIMULINK_A43_RESULT.json'),'w');assert(fid>0);
fprintf(fid,'%s\n',jsonencode(audit,PrettyPrint=true));fclose(fid);
fprintf('A43_SIMULINK_ALL_PASS %d\n',totalChecks);
close_system(mdl,0);
