% SK: V08 kompletna vazba medzi validovanym meracim CSV a Simulink.
% Vstupny subor A/B/C nie je dostupny. Ciel su 8 nezavisle skontrolovanych
% D-syntetickych replay priebehov v07 pre regresny test signalnej architektury.
folder=fileparts(mfilename('fullpath'));root=fileparts(fileparts(folder));
out=fullfile(root,'results','pool_measurement_v08');
model='DC_Bazen_Externe_Merania_v08_SK';
assert(isfile(fullfile(folder,[model '.slx'])),'Najprv vytvorit model v08');
load_system(fullfile(folder,[model '.slx']));
man=jsondecode(fileread(fullfile(out,'D_REPLAY_INPUT_MANIFEST.json')));
assert(numel(man.cases)==8);
outcases=struct([]);
for ci=1:numel(man.cases)
 name=man.cases(ci).case;
 folderCase=fullfile(out,'source_D',name);
 staged=fullfile(out,'staged_D',name);
 op=readtable(fullfile(folderCase,'source_operational_inputs_D_21.csv'));
 m=readtable(fullfile(staged,'normalized_measurements_v07.csv'));
 provenance=jsondecode(fileread(fullfile(staged,'validated_dataset_metadata.json')));
 assert(strcmp(provenance.provenance,'D'),'False real-data claim');
 assert(height(op)==672 && height(m)==672);
 assert(width(op)==22,'Operational raw vector exactly 21 columns + time');
 % Original 21-channel vector is known to be synthetic. Mandatory telemetry is
 % the VALIDATED external sensor channels T1/T2; no true-T shortcut.
 raw=op{:,2:22};
 raw(:,1)=m.Q_DC_available_W;
 raw(:,2)=m.T_DC_C;raw(:,3)=m.Q_DH_request_W;
 raw(:,4)=m.T_air_C;raw(:,5)=m.RH;
 raw(:,14)=double(m.pool_flow_m3h>0);
 raw(:,18)=m.main_reject_ok;raw(:,20)=m.backup_reject_ok;
 inputs=[raw,m.T_pool_sensor1_C,m.T_pool_sensor2_C];
 assert(isequal(size(inputs),[672 23]));
 sec=(0:671)'*900;
 profil_merani_v08=timeseries(inputs,sec);
 profil_merani_v08=setinterpmethod(profil_merani_v08,'zoh');
 assignin('base','profil_merani_v08',profil_merani_v08);
 result=sim(model,'StopTime',num2str(sec(end)), ...
   'ReturnWorkspaceOutputs','on');
 Y=squeeze(result.get('tok_v08').Data);
 F=squeeze(result.get('interlock_v08').Data);
 if size(Y,1)~=672,Y=Y';end
 if size(F,1)~=672,F=F';end
 assert(isequal(size(Y),[672 39]) && isequal(size(F),[672 10]));
 gold=readtable(fullfile(root,'results','pool_redundancy_v07',...
   ['scenar_' name '_SK.csv']));
 assert(height(gold)==672);
 DT=max(abs(Y(:,1)-gold.T_pool_C));
 DG=max(abs(Y(:,4)-gold.Q_pool_phys_W));
 DR=max(abs(Y(:,27)-gold.Q_unhandled_W));
 DL=max(abs(F(:,1)-gold.safety_latch));
 assert(DT<0.005,['Temperature mismatch ' name ' ' num2str(DT)]);
 assert(DG<200,['Heating mismatch ' name ' ' num2str(DG)]);
 assert(DR<200,['Reject mismatch ' name ' ' num2str(DR)]);
 assert(DL==0,['Latch replay differs ' name]);
 assert(max(abs(Y(:,22:25)),[],'all')<1e-5,'Thermodynamic residual');
 assert(max(abs(Y(:,39)))<1e-5,'Dual rejection residual');
 assert(all(Y(:,1)>10 & Y(:,1)<55),'Pool temperature physically implausible');
 assert(all(Y(:,26)>=0 & Y(:,27)>=0),'Invalid sign of heat');
 % Full audit output with 23 external input columns and 49 core/flag columns.
 headers=[{'cas_h'},op.Properties.VariableNames(2:end),...
   {'external_T1_C','external_T2_C'},...
   gold.Properties.VariableNames(23:61),gold.Properties.VariableNames(62:71)];
 assert(numel(headers)==1+23+39+10);
 tbl=array2table([sec/3600,inputs,Y,F],'VariableNames',headers);
 writetable(tbl,fullfile(out,['sim_v08_' name '_SK.csv']));
 r=struct('scenario',name,'source_class','D_SYNTHETIC_REPLAY',...
  'records',672,'maximum_temperature_error_vs_v07_C',DT,...
  'maximum_heat_error_vs_v07_W',DG,...
  'maximum_unhandled_heat_error_vs_v07_W',DR,...
  'maximum_latch_error',DL,'pool_MWh',sum(Y(:,4))/4e6,...
  'IT_model_max_C',max(Y(:,28)),...
  'unhandled_heat_MWh',sum(Y(:,27))/4e6,...
  'rejected_backup_MWh',sum(Y(:,35))/4e6);
 if isempty(outcases),outcases=r;else,outcases(end+1)=r;end %#ok<SAGROW>
 fprintf('V08_REPLAY_PASS %s T_delta=%.9f C Q_delta=%.6f W latch_delta=%g\n',...
     name,DT,DG,DL);
end
s=struct('status','VERIFIED_SIMULINK_D_REPLAY_PENDING_INDEPENDENT_QA',...
 'classification','D_SYNTHETIC_NO_REAL_SENSOR_MEASUREMENT',...
 'model',model,'step_seconds',900,'period_days',7,...
 'sensors','FROM validated CSV (23 inputs: 21 control + external T1/T2)',...
 'cases',outcases);
fid=fopen(fullfile(out,'vysledky_v08_SK.json'),'w','n','UTF-8');
assert(fid>0);fprintf(fid,'%s',jsonencode(s,PrettyPrint=true));fclose(fid);
close_system(model,0);
fprintf('V08_ALL_REPLAY_CASES_PASS %d\n',numel(outcases));
