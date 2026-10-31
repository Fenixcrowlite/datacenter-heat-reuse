% SK: V05 havarijne scenare nad klonom fyziky v04, povodny v85 untouched.
folder=fileparts(mfilename('fullpath'));project=fileparts(fileparts(folder));
output=fullfile(project,'results','pool_safety_v05');
name='DC_Bazen_Bezpecnost_v05_SK';
assert(isfile(fullfile(folder,[name '.slx'])),'Model v05 nebol vytvoreny');
load_system(fullfile(folder,[name '.slx']));
N=7*96;time=(0:N-1)'*900;hour=time/3600;day=hour/24;clock=mod(hour,24);
active=double(clock>=8 & clock<20);
Qdc=max(0,170000+30000*cos(2*pi*day/7)+20000*sin(2*pi*hour/24));
Tdc=30+7*cos(2*pi*(day-2)/7);
Qdh=75000+35000*active+25000*(0.5+0.5*cos(2*pi*day/7));
Tair=29+0.6*sin(2*pi*day/7);RH=0.6+0.07*sin(2*pi*day/7);
poolActivity=0.5+0.5*active;cover=1-active;
base=[Qdc,Tdc,Qdh,Tair,RH,poolActivity,cover,ones(N,4)];
cases={'normalny','rozdiel_senzorov','pomaly_drift_senzora','bez_prietoku',...
    'havarijne_tlacidlo','reset_pocas_poruchy','oba_senzory_bias'};
outputRows=struct([]);
for ic=1:numel(cases)
  scenario=cases{ic};
  b1=zeros(N,1);b2=zeros(N,1);flow=ones(N,1);estop=zeros(N,1);reset=zeros(N,1);
  if strcmp(scenario,'rozdiel_senzorov')
    b1(hour>=30&hour<32)=0.85;
    reset(hour>=38&hour<38.25)=1;
  elseif strcmp(scenario,'pomaly_drift_senzora')
    mask=hour>=52&hour<60;
    b1(mask)=(hour(mask)-52)*0.11;
    reset(hour>=67&hour<67.25)=1;
  elseif strcmp(scenario,'bez_prietoku')
    flow(hour>=72&hour<80)=0;
    reset(hour>=86&hour<86.25)=1;
  elseif strcmp(scenario,'havarijne_tlacidlo')
    estop(hour>=96&hour<101)=1;
    reset(hour>=114&hour<114.25)=1;
  elseif strcmp(scenario,'reset_pocas_poruchy')
    flow(hour>=40&hour<52)=0;
    reset(hour>=45&hour<45.25)=1; % nesmie uvolnit
    reset(hour>=58&hour<58.25)=1; % po poruche moze uvolnit
  elseif strcmp(scenario,'oba_senzory_bias')
    b1(hour>=70&hour<75)=0.70;
    b2(hour>=70&hour<75)=0.70;
    reset(hour>=85&hour<85.25)=1;
  end
  raw=[base,b1,b2,flow,estop,reset];
  profil_bezpecnost_v05=timeseries(raw,time);
  profil_bezpecnost_v05=setinterpmethod(profil_bezpecnost_v05,'zoh');
  assignin('base','profil_bezpecnost_v05',profil_bezpecnost_v05);
  simout=sim(name,'StopTime',num2str(time(end)),'ReturnWorkspaceOutputs','on');
  P=squeeze(simout.get('sim_energeticka_bilancia_v04').Data);
  F=squeeze(simout.get('zaznam_interlock_v05').Data);
  if size(P,1)~=N,P=P';end
  if size(F,1)~=N,F=F';end
  assert(isequal(size(P),[N 25])&&isequal(size(F),[N 10]));
  bad=(abs(b1-b2)>0.35 | abs(b1)>0.45 | abs(b2)>0.45 | flow<0.5 | estop>0.5);
  if strcmp(scenario,'normalny')
    assert(all(F(:,1)==0),'Healthy environment unexpectedly latched');
    reference=readtable(fullfile(project,'results','pool_feedback_v04','scenar_zaklad_SK.csv'));
    % Compares safely cloned v04 physics with previously tested v04 golden CSV.
    assert(max(abs(P(:,1)-reference.T_bazen_C))<1e-7,'Baseline water v04 mismatch');
    assert(max(abs(P(:,4)-reference.Q_pool_W))<1e-7,'Baseline pool power v04 mismatch');
    assert(max(abs(P(:,17)-reference.Q_reject_W))<1e-7,'Baseline reject v04 mismatch');
  else
    assert(any(F(:,1)>0.5),['Safety not tripped ' scenario]);
    assert(all(F(bad,1)>0.5),['Trip should occur within same sample ' scenario]);
    assert(all(P(F(:,1)>.5,4)==0),['Heating while latched ' scenario]);
    if strcmp(scenario,'reset_pocas_poruchy')
       idx=find(hour>=45 & hour<45.25);
       assert(all(F(idx,1)>0.5),'Unsafe reset while fault active');
    end
    assert(any(F(:,7)>0.5),['No explicit successful manual reset ' scenario]);
  end
  assert(all(F(:,1)==0 | F(:,1)==1));
  assert(all(P(:,1)<=27.751),'Temperature ceiling');
  assert(max(abs(P(:,18)-(P(:,6)+P(:,14)+P(:,17))))<1e-5,'Source balance');
  assert(max(abs((P(:,7)+P(:,8)+P(:,9))-(P(:,14)+P(:,15))))<1e-5,'HP balance');
  assert(max(abs(P(:,4)-(P(:,6)+P(:,7))))<1e-5,'Pool balance');
  % DC cooling continues to have independent rejection even if pool latched.
  assert(all(P(F(:,1)>.5,18)>=P(F(:,1)>.5,17)-1e-5));
  z=table(hour,P(:,1),P(:,2),P(:,4),P(:,5),P(:,6),P(:,7),P(:,8),P(:,9),...
      P(:,10),P(:,11),P(:,14),P(:,15),P(:,16),P(:,17),P(:,18),P(:,20),...
      F(:,1),F(:,2),F(:,3),F(:,4),F(:,5),F(:,6),F(:,7),F(:,8),F(:,9),F(:,10),...
      b1,b2,flow,estop,reset,...
      'VariableNames',{'cas_h','T_bazen_C','E_TES_J','Q_bazen_W','Q_straty_W',...
      'Q_priamy_HX_W','Q_TC_bazen_W','Q_TC_DH_W','Q_TC_TES_W','Q_TES_dis_W',...
      'Q_DH_W','Q_DC_TC_W','P_kompresor_W','P_pomocne_W','Q_reject_W','Q_DC_W','rezim',...
      'blokovanie','rozdiel_senzorov','teplota_vysoka','prietok_chyba','havaria',...
      'neplatne_senzory','reset_uspesny','T_senzor1_C','T_senzor2_C','bazen_ok_po_gating',...
      'bias1_K','bias2_K','prietok_ok','emergency_stop','manualny_reset'});
  writetable(z,fullfile(output,['scenar_' scenario '_SK.csv']));
  summary=struct('scenar',scenario,'vzorky',N,'interval_s',900,...
      'Tmax_C',max(P(:,1)),'blocked_samples',sum(F(:,1)>0.5),...
      'pool_MWh',sum(P(:,4))/4e6,'DC_rejected_MWh',sum(P(:,17))/4e6,...
      'HP_electric_MWh',sum(P(:,15))/4e6,...
      'sensor_fault_samples',sum(F(:,2)>0.5),...
      'flow_fault_samples',sum(F(:,4)>0.5),...
      'manual_reset_events',sum(F(:,7)>0.5),...
      'max_source_balance_W',max(abs(P(:,18)-(P(:,6)+P(:,14)+P(:,17)))));
  if isempty(outputRows),outputRows=summary;else,outputRows(end+1)=summary;end %#ok<SAGROW>
  fprintf('V05_PASS %s blocked=%d poolMWh=%.5f maxT=%.3f\n',...
    scenario,summary.blocked_samples,summary.pool_MWh,summary.Tmax_C);
end
saveinfo=struct('status','VERIFIED_SIMULINK_FAULT_INJECTION_SYNTHETIC',...
 'date','2026-10-23','model',name,'notes',...
 'sensor1=simplified true temperature plus injected bias; do not interpret as physical dual-sensor validation',...
 'original_v85_modified',false,'base_v04_modified',false,'scenarios',outputRows);
fid=fopen(fullfile(output,'resultaty_v05_SK.json'),'w','n','UTF-8');
assert(fid>0);fprintf(fid,'%s',jsonencode(saveinfo,PrettyPrint=true));fclose(fid);
close_system(name,0);
fprintf('V05_ALL_PASS %d\n',numel(outputRows));
