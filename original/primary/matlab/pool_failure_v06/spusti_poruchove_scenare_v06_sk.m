% SK: vykonane rizikove scenare 7 dni, 900 s; v85/v04/v05 sa nemenia.
folder=fileparts(mfilename('fullpath')); root=fileparts(fileparts(folder));
outdir=fullfile(root,'results','pool_failure_v06');
model='DC_Bazen_Fyzikalne_Poruchy_v06_SK';
assert(isfile(fullfile(folder,[model '.slx'])),'Najprv treba zostavit model v06');
load_system(fullfile(folder,[model '.slx']));
N=672;dt=900; sec=(0:N-1)'*dt;h=sec/3600;day=h/24;
hour=mod(h,24);active=double(hour>=8 & hour<20);
Qsrc=max(0,170000+30000*cos(2*pi*day/7)+20000*sin(2*pi*h/24));
Tsrc=30+7*cos(2*pi*(day-2)/7);
Qdh=75000+35000*active+25000*(0.5+0.5*cos(2*pi*day/7));
air=29+0.6*sin(2*pi*day/7); rh=.60+.07*sin(2*pi*day/7);
act=.5+.5*active; cover=1-active;
names={'zdravy','oneskorene_snimace_bias','spolocny_bias_nedetekovany',...
'zaseknuty_ventil','vypadok_REJECT','bez_prietoku','kombinovana_porucha'};
summ=struct([]);
for ci=1:numel(names)
 name=names{ci};
 bias1=zeros(N,1);bias2=zeros(N,1);flow=ones(N,1);
 estop=zeros(N,1);reset=zeros(N,1);valve=zeros(N,1);rej=ones(N,1);
 ts=Tsrc;
 if strcmp(name,'oneskorene_snimace_bias')
   bias1(h>=24 & h<28)=.65;reset(h>=36 & h<36.25)=1;
 elseif strcmp(name,'spolocny_bias_nedetekovany')
   bias1(h>=24 & h<28)=-.40;
   bias2(h>=24 & h<28)=-.40;
 elseif strcmp(name,'zaseknuty_ventil')
   ts=ts+12;valve(h>=24 & h<49)=1;
   estop(h>=26 & h<32)=1; reset(h>=53 & h<53.25)=1;
 elseif strcmp(name,'vypadok_REJECT')
   rej(h>=54 & h<61)=0;
 elseif strcmp(name,'bez_prietoku')
   flow(h>=72 & h<78)=0; reset(h>=85 & h<85.25)=1;
 elseif strcmp(name,'kombinovana_porucha')
   ts=ts+12; valve(h>=30 & h<37)=1;
   rej(h>=31 & h<38)=0;
   estop(h>=30 & h<35)=1;reset(h>=46 & h<46.25)=1;
 end
 base=[Qsrc,ts,Qdh,air,rh,act,cover,ones(N,4)];
 in=[base,bias1,bias2,flow,estop,reset,valve,rej];
 profil_poruchy_v06=timeseries(in,sec);
 profil_poruchy_v06=setinterpmethod(profil_poruchy_v06,'zoh');
 assignin('base','profil_poruchy_v06',profil_poruchy_v06);
 simout=sim(model,'StopTime',num2str(sec(end)),'ReturnWorkspaceOutputs','on');
 Y=squeeze(simout.get('tok_v06').Data);
 F=squeeze(simout.get('interlock_v06').Data);
 if size(Y,1)~=N,Y=Y';end
 if size(F,1)~=N,F=F';end
 assert(isequal(size(Y),[N 33]),'Core vector must have 33 values');
 assert(isequal(size(F),[N 10]),'Safety vector must have 10 values');
 assert(max(abs(Y(:,22)))<1e-5,'Source + unhandled balance');
 assert(max(abs(Y(:,23:25)),[],'all')<1e-5,'HP+Pool+DH balance');
 assert(all(Y(:,1)>0 & Y(:,1)<55),'Pool water numerical bound');
 assert(all(Y(:,17)>=0 & Y(:,27)>=0),'No negative rejection');
 assert(all(Y(:,26)>=0 & Y(:,26)<=25000),'Physical leak limit');
 % This test must NOT incorrectly claim safety from a stuck-open valve.
 if strcmp(name,'zdravy')
   assert(all(F(:,1)==0),'Healthy sensors should not trip');
   assert(all(Y(:,26)==0 & Y(:,27)==0),'Healthy case physically isolated');
   reference=readtable(fullfile(root,'results','pool_feedback_v04','scenar_zaklad_SK.csv'));
   assert(max(abs(Y(:,1)-reference.T_bazen_C))<1e-6,'Regression v04 water T');
 end
 if strcmp(name,'spolocny_bias_nedetekovany')
   assert(~any(F(h>=24 & h<28,1)>0.5),'Common-mode bias unexpectedly detected');
 end
 if strcmp(name,'oneskorene_snimace_bias') || strcmp(name,'bez_prietoku')
   assert(any(F(:,1)>0.5),'Sensor / flow fault not detected');
   assert(all(Y(F(:,1)>.5,4)==0),'Software interlock must stop heat when valves healthy');
 end
 if strcmp(name,'zaseknuty_ventil') || strcmp(name,'kombinovana_porucha')
   assert(any(Y(:,26)>0),'Stuck valve did not cause flow');
   assert(any(Y(:,32)>0),'Leakage despite zero heating command was not detected');
 end
 if strcmp(name,'vypadok_REJECT') || strcmp(name,'kombinovana_porucha')
   assert(any(Y(:,27)>0),'Rejection failure had no unmet heat');
   assert(any(Y(:,29)>0),'IT thermal risk indicator must rise');
 end
 fields=[h,in,Y,F];
 headings=[{'cas_h'},...
 {'Q_DC_in_W','T_DC_C','Q_DH_request_W','T_air_C','RH','aktivita','plachta','IT_ok','BAZEN_ok','TES_ok','HX_ok',...
 'bias1_K','bias2_K','flow_ok','E_STOP','manual_reset','valve_stuck','reject_availability'},...
 {'T_pool_C','E_TES_J','Q_pool_request_W','Q_pool_actual_W','Q_pool_loss_W',...
 'Q_HX_physical_W','Q_HP_pool_W','Q_HP_DH_W','Q_HP_TES_W','Q_TES_out_W',...
 'Q_DH_W','Q_DH_unmet_W','Q_pool_unmet_command_W','Q_HP_source_W',...
 'P_HP_W','P_aux_W','Q_reject_actual_W','Q_DC_available_W','COP','stateflow_mode',...
 'Q_TES_loss_W','Q_balance_DC_W','Q_balance_HP_W','Q_balance_pool_W','Q_balance_DH_W',...
 'Q_stuck_leak_W','Q_reject_unhandled_W','T_IT_risk_C','IT_risk_alarm',...
 'Q_reject_command_W','Q_reject_effective_W','leak_without_command','residual_DC_with_unhandled_W'},...
 {'safety_latched','sensor_disagreement','sensor_overtemp','no_flow','emergency','invalid_sensor',...
 'reset_accepted','sensor_1_C','sensor_2_C','pool_enabled'}];
 assert(numel(headings)==size(fields,2),'Column count mismatch');
 tab=array2table(fields,'VariableNames',headings);
 writetable(tab,fullfile(outdir,['scenar_' name '_SK.csv']));
 row=struct('scenar',name,'intervalov',N,'step_s',dt,...
 'T_pool_max_C',max(Y(:,1)),'T_IT_risk_max_C',max(Y(:,28)),...
 'pool_delivered_MWh',sum(Y(:,4))/4e6,...
 'leak_stuck_MWh',sum(Y(:,26))/4e6,...
 'unhandled_cooling_MWh',sum(Y(:,27))/4e6,...
 'actual_rejected_MWh',sum(Y(:,17))/4e6,...
 'HP_electric_MWh',sum(Y(:,15))/4e6,...
 'fault_latched_samples',sum(F(:,1)>.5),...
 'unsafe_leak_samples',sum(Y(:,32)>.5),...
 'IT_risk_alarm_samples',sum(Y(:,29)>.5));
 if isempty(summ),summ=row;else,summ(end+1)=row;end %#ok<SAGROW>
 fprintf('V06_CASE %s leak=%.5f MWh, unrejected=%.5f MWh, riskITmax=%.2f C, latched=%d\n',...
    name,row.leak_stuck_MWh,row.unhandled_cooling_MWh,row.T_IT_risk_max_C,row.fault_latched_samples);
end
report=struct('status','SIMULINK_EXECUTED_SYNTHETIC_PENDING_INDEPENDENT_QA',...
 'model',model,'scenarios',summ,'interval_s',900,...
 'physical_warning','IT buffer risk temperature is model indicator, not actual server temperature',...
 'source_provenance','D assumed / synthetic; 15-minute sensor delays; reject physical capacity 180kW');
f=fopen(fullfile(outdir,'vysledky_v06_SK.json'),'w','n','UTF-8');
assert(f>0);fprintf(f,'%s',jsonencode(report,PrettyPrint=true));fclose(f);
close_system(model,0);
fprintf('V06_DONE %d SCENARIOS\n',numel(summ));
