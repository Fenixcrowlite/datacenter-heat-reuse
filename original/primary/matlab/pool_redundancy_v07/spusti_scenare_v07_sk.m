
% SK: dualny ventil + dve odvodne vetvy + podmienene IT load shedding.
% Vsetko D-syntetika, krok 900 s, horizont 168 h, 8 nezavislych behov.
folder=fileparts(mfilename('fullpath')); root=fileparts(fileparts(folder));
model='DC_Bazen_Dvojita_Ochrana_v07_SK';out=fullfile(root,'results','pool_redundancy_v07');
assert(isfile(fullfile(folder,[model '.slx'])),'Build v07 first');
load_system(fullfile(folder,[model '.slx']));
N=672;dt=900;secs=(0:N-1)'*dt;h=secs/3600;days=h/24;
hour=mod(h,24);active=double(hour>=8 & hour<20);
Qdc=max(0,170000+30000*cos(2*pi*days/7)+20000*sin(2*pi*h/24));
Tdc=30+7*cos(2*pi*(days-2)/7);
Qdh=75000+35000*active+25000*(0.5+0.5*cos(2*pi*days/7));
Tair=29+0.6*sin(2*pi*days/7);RH=.6+.07*sin(2*pi*days/7);
activity=.5+.5*active;cover=1-active;
names={'zdravy','primarny_ventil_zaseknuty','oba_ventily_zaseknute',...
 'hlavny_REJECT_off_zalozny_ok','oba_REJECT_off_bez_shedding',...
 'oba_REJECT_off_so_shedding','spolocny_bias_senzorov',...
 'kombinovana_havaria_so_shedding'};
S=struct([]);
for ci=1:numel(names)
 name=names{ci};
 b1=zeros(N,1);b2=zeros(N,1);flow=ones(N,1);
 estop=zeros(N,1);reset=zeros(N,1);
 v1=zeros(N,1);v2=zeros(N,1);a=ones(N,1);b=ones(N,1);
 shed=zeros(N,1);temp=Tdc;
 if strcmp(name,'primarny_ventil_zaseknuty')
   temp=temp+12;v1(h>=24 & h<49)=1;
   estop(h>=26 & h<32)=1;reset(h>=53 & h<53.25)=1;
 elseif strcmp(name,'oba_ventily_zaseknute')
   temp=temp+12;v1(h>=24 & h<49)=1;v2(h>=24 & h<49)=1;
   estop(h>=26 & h<32)=1;reset(h>=53 & h<53.25)=1;
 elseif strcmp(name,'hlavny_REJECT_off_zalozny_ok')
   a(h>=54 & h<61)=0;
 elseif strcmp(name,'oba_REJECT_off_bez_shedding')
   a(h>=54 & h<61)=0;b(h>=54 & h<61)=0;
 elseif strcmp(name,'oba_REJECT_off_so_shedding')
   a(h>=54 & h<61)=0;b(h>=54 & h<61)=0;
   shed(:)=1;
 elseif strcmp(name,'spolocny_bias_senzorov')
   b1(h>=30 & h<38)=-.4;b2(h>=30 & h<38)=-.4;
 elseif strcmp(name,'kombinovana_havaria_so_shedding')
   temp=temp+12;
   v1(h>=30 & h<38)=1;v2(h>=30 & h<38)=1;
   a(h>=31 & h<38)=0;b(h>=31 & h<38)=0;
   estop(h>=30 & h<35)=1;reset(h>=46 & h<46.25)=1;
   shed(:)=1;
 end
 basic=[Qdc,temp,Qdh,Tair,RH,activity,cover,ones(N,4)];
 raw=[basic,b1,b2,flow,estop,reset,v1,a,v2,b,shed];
 assert(size(raw,2)==21,'Expected 21 inputs');
 profil_merani_v07=timeseries(raw,secs);
 profil_merani_v07=setinterpmethod(profil_merani_v07,'zoh');
 assignin('base','profil_merani_v07',profil_merani_v07);
 simout=sim(model,'StopTime',num2str(secs(end)),'ReturnWorkspaceOutputs','on');
 Y=squeeze(simout.get('tok_v07').Data);
 F=squeeze(simout.get('interlock_v07').Data);
 if size(Y,1)~=N,Y=Y';end
 if size(F,1)~=N,F=F';end
 assert(isequal(size(Y),[N 39]) && isequal(size(F),[N 10]));
 assert(max(abs(Y(:,22:25)),[],'all')<1e-5,'Thermal conservation failed');
 assert(max(abs(Y(:,39)))<1e-5,'Dual rejection equation failed');
 assert(all(Y(:,26)>=0 & Y(:,27)>=0 & Y(:,34)>=0 & Y(:,35)>=0));
 assert(all(Y(:,34)<=180000.01 & Y(:,35)<=150000.01),'Reject capacities');
 assert(all(Y(:,36)>=0),'No negative shed');
 if strcmp(name,'zdravy')
   assert(all(Y(:,26)==0 & Y(:,27)==0 & Y(:,36)==0),'Healthy unexpected flow');
   ref=readtable(fullfile(root,'results','pool_feedback_v04','scenar_zaklad_SK.csv'));
   assert(max(abs(Y(:,1)-ref.T_bazen_C))<1e-6,'Base physical regression');
 end
 if strcmp(name,'primarny_ventil_zaseknuty')
   assert(all(Y(:,26)==0),'Second valve must isolate primary stuck');
 end
 if strcmp(name,'oba_ventily_zaseknute')
   assert(any(Y(:,26)>0 & Y(:,32)>0),'Dual stuck valve must produce leak despite STOP');
 end
 if strcmp(name,'hlavny_REJECT_off_zalozny_ok')
   assert(all(Y(:,27)<1e-9),'Backup must cover main outage in this profile');
   assert(any(Y(:,35)>0),'Backup cooler did not pick up load');
 end
 if strcmp(name,'oba_REJECT_off_bez_shedding')
   assert(any(Y(:,27)>0 & Y(:,29)>0),'Dual cooling failure hazard not shown');
   assert(all(Y(:,36)==0),'Shedding disabled');
 end
 if strcmp(name,'oba_REJECT_off_so_shedding')
   assert(any(Y(:,36)>0),'Automatic derating never engaged');
 end
 if strcmp(name,'spolocny_bias_senzorov')
   assert(all(F(h>=30 & h<38,1)==0),'Common-mode error falsely classified');
 end
 if strcmp(name,'kombinovana_havaria_so_shedding')
   assert(any(Y(:,26)>0),'Dual valve fault not revealed');
   assert(any(Y(:,36)>0),'IT mitigation not triggered');
 end
 HEAD=[{'cas_h'},{'Q_DC_source_raw_W','T_DC_C','Q_DH_req_W','T_air_C','RH','activity','cover','IT_ok',...
 'pool_ok','TES_ok','HX_ok','bias1_K','bias2_K','flow_ok','E_STOP','manual_RESET',...
 'primary_valve_stuck','reject_main_availability','secondary_valve_stuck',...
 'reject_backup_availability','IT_shedding_enable'},...
 {'T_pool_C','E_TES_J','Q_pool_req_W','Q_pool_phys_W','Q_pool_loss_W','Q_HX_phys_W',...
 'Q_HP_pool_W','Q_HP_DH_W','Q_HP_charge_W','Q_TES_discharge_W','Q_DH_W','Q_DH_unmet_W',...
 'Q_pool_cmd_unmet_W','Q_HP_source_W','P_HP_W','P_aux_W','Q_reject_physical_W',...
 'Q_DC_eff_W','COP','stateflow_mode','Q_TES_loss_W','residual_DC_W','residual_HP_W',...
 'residual_pool_W','residual_DH_W','Q_leak_W','Q_unhandled_W','T_IT_model_C',...
 'IT_model_alarm','Q_reject_command_W','Q_reject_total_W','leak_at_zero_cmd',...
 'residual_DC2_W','Q_reject_main_W','Q_reject_backup_W','Q_IT_shed_W',...
 'primary_valve_fault','secondary_valve_fault','residual_reject_W'},...
 {'safety_latch','sensor_mismatch','sensor_hot','flow_fault','emergency_flag',...
 'invalid_sensor','reset_success','sensor1_C','sensor2_C','pool_enabled'}];
 assert(numel(HEAD)==1+21+39+10);
 tbl=array2table([h,raw,Y,F],'VariableNames',HEAD);
 writetable(tbl,fullfile(out,['scenar_' name '_SK.csv']));
 ss=struct('scenar',name,'intervalov',N,...
   'heat_pool_MWh',sum(Y(:,4))/4e6,...
   'leak_MWh',sum(Y(:,26))/4e6,...
   'unhandled_MWh',sum(Y(:,27))/4e6,...
   'main_rejected_MWh',sum(Y(:,34))/4e6,...
   'backup_rejected_MWh',sum(Y(:,35))/4e6,...
   'IT_avoided_source_MWh',sum(Y(:,36))/4e6,...
   'T_IT_model_max_C',max(Y(:,28)),...
   'T_pool_max_C',max(Y(:,1)),...
   'latched_samples',sum(F(:,1)>.5),...
   'unsafe_leak_samples',sum(Y(:,32)>.5),...
   'IT_alarm_samples',sum(Y(:,29)>.5));
 if isempty(S),S=ss;else,S(end+1)=ss;end %#ok<SAGROW>
 fprintf('V07_PASS %s: leak=%0.5f rejectBackup=%0.5f unhandled=%0.5f shed=%0.5f ITmax=%0.3f\n',...
 name,ss.leak_MWh,ss.backup_rejected_MWh,ss.unhandled_MWh,...
 ss.IT_avoided_source_MWh,ss.T_IT_model_max_C);
end
ref=S(strcmp({S.scenar},'oba_REJECT_off_bez_shedding'));
mit=S(strcmp({S.scenar},'oba_REJECT_off_so_shedding'));
assert(mit.T_IT_model_max_C<ref.T_IT_model_max_C,...
 'IT load shedding did not improve thermal risk');
assert(mit.unhandled_MWh<ref.unhandled_MWh,...
 'IT load shedding did not reduce unmet heat');
j=struct('status','SIMULINK_EXECUTED_AWAITING_INDEPENDENT_QA',...
 'provenance','D assumed synthetic, no field measurements',...
 'step_seconds',dt,'duration_hours',168,'model',model,...
 'limits','not manufacturer cooling datasheets / not actual server temperature',...
 'cases',S);
fid=fopen(fullfile(out,'vysledky_v07_SK.json'),'w','n','UTF-8');
assert(fid>0);fprintf(fid,'%s',jsonencode(j,PrettyPrint=true));fclose(fid);
close_system(model,0);
fprintf('V07_ALL_EIGHT_SCENARIOS_PASS\n');
