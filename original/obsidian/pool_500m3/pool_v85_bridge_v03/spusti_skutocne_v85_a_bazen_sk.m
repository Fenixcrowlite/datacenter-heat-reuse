% Realne znovuspustenie ulozeneho v85 a sucasny beh oddeleneho Simulinku bazena.
% Ziadny vymysleny rocny profil v85, ziadna duplicita tepelných MWh.
folder=fileparts(mfilename('fullpath'));
root=fileparts(fileparts(folder));
output=fullfile(root,'results','pool_v85_bridge_v03');
if ~isfolder(output),mkdir(output);end
ref=fullfile(root,'results','horizon_sensitivity_v86_20261013T112610_976653Z');
addpath(folder,fullfile(root,'matlab'),fullfile(root,'matlab','simulink'));
spec=jsondecode(fileread(fullfile(ref,'spec.json')));
namev85='DCHR_Electrical_Dispatch_Stateflow_v85';
namePool='Bazen_Prepripojenie_Sluzby_v85_v03_SK';
original=fullfile(root,'matlab','simulink',[namev85 '.slx']);
pathPool=fullfile(folder,[namePool '.slx']);
assert(isfile(original),'Chyba ulozeny model v85');
if ~isfile(pathPool),vytvor_most_simulink_v85_sk();end
load_system(original);load_system(pathPool);
% SHA256 posudzuje externy nezavisly QA cez Get-FileHash.
cases={'service_E3.0_a1.0_H2_dt0.25', ...
 'charge_E4.95_a1.0_H2_dt0.25','binding_stop'};
scenarios={'studena_voda','tepla_voda','stop_bazen'};
result=struct([]);
for ic=1:numel(cases)
   if iscell(spec.cases)
       ids=cellfun(@(v)v.id,spec.cases,'UniformOutput',false);
   else
       ids={spec.cases.id};
   end
   found=find(strcmp(ids,cases{ic}),1);
   assert(~isempty(found),'Ziadany v85 scenar nie je v spec');
   if iscell(spec.cases),c=spec.cases{found};else,c=spec.cases(found);end
   a=dchr.adapt_held_schedule_v74(c.schedule,c.p,c.initial);
   assert(all(abs(a.schedule(:,1)-0.25)<1e-14),'Len 15 minutove intervaly');
   raw=[a.p,c.ceiling_MW,c.horizon_h];
   [effective,~]=electrical_policy_v85(raw',c.initial(1));
   a.p=effective(:)';
   mw=get_param(namev85,'ModelWorkspace');
   assignin(mw,'dispatch_input_v66',[a.protocol_ticks,a.input]);
   assignin(mw,'dispatch_cfg_v66',[a.protocol_ticks,repmat(raw,size(a.input,1),1)]);
   out85=sim(namev85,'StopTime',num2str(size(a.input,1)-1),'ReturnWorkspaceOutputs','on');
   trace=reshape(out85.interval_trace_v66.Data,1380,[])';
   r=dchr.report_held_schedule_v76(a,trace); % certifikovane pravidla v85
   old=load(fullfile(ref,[c.id '.mat']),'trace');
   assert(isequal(trace,old.trace),'V85 trace sa po opatovnom spusteni nezhoduje s ulozenym MAT');
   n=size(trace,1);qW=zeros(n,1);Eraw=0;
   for k=1:n
      energy=0;
      segments=round(trace(k,13));
      for seg=1:segments
          z=trace(k,100+80*(seg-1)+(1:80));
          assert(z(7)>=0 && z(8)>=z(7));
          % Energeticka alokacia uz dodanej priamej sluzby v85 [MW].
          % Pri intervalovej neistote kontrolujeme hornu a dolnu hranicu.
          energy=energy+z(25)*(z(7)+z(8))/2;
      end
      qW(k)=energy/a.schedule(k,1)*1e6;
      Eraw=Eraw+energy;
   end
   assert(Eraw>=r.direct_HP_service_MWh_hull(1)-1e-8 && ...
      Eraw<=r.direct_HP_service_MWh_hull(2)+1e-8,...
      'Nepovolena interpretacia sluzby v85');
   for js=1:numel(scenarios)
       cas=scenarios{js};
       firstT=16;stop=zeros(n,1);
       if strcmp(cas,'tepla_voda'),firstT=27.70;end
       if strcmp(cas,'stop_bazen'),stop(:)=1;end
       profile=[qW,stop,ones(n,1),zeros(n,1),29*ones(n,1),0.6*ones(n,1)];
       profil_v85=timeseries(profile,(0:n-1)'*900);
       profil_v85=setinterpmethod(profil_v85,'zoh');
       assignin('base','profil_v85',profil_v85);
       set_param([namePool '/Teplota_vody'],'InitialCondition',num2str(firstT,'%.17g'));
       resultPool=sim(namePool,'StopTime',num2str((n-1)*900));
       ts=resultPool.get('spolu_v85_bazen');
       Y=squeeze(ts.Data);
       if size(Y,1)~=n,Y=Y';end
       assert(isequal(size(Y),[n 9]),'Rozmery casoveho vystupu');
       assert(max(abs(Y(:,5)-qW))<1e-6,'V85 signal nebol dodany do bazena');
       assert(max(abs(Y(:,2)+Y(:,3)-Y(:,5)))<1e-6,'Dvojite zapocitanie tepla');
       assert(all(Y(:,2)>=0 & Y(:,3)>=0) && max(Y(:,2))<=150000+1e-8);
       assert(all(Y(:,1)<=27.750000001),'Limit modelovej teploty');
       if all(stop>0), assert(all(Y(:,2)==0),'STOP neodpojil bazen');end
       dt=900;C=997*500*4182;
       Qp=sum(Y(:,2))*dt/3.6e9;
       Qdh=sum(Y(:,3))*dt/3.6e9;
       Qbefore=sum(Y(:,5))*dt/3.6e9;
       Qloss=sum(Y(:,4))*dt/3.6e9;
       residual=abs(C*(Y(end,1)-firstT)/3.6e9-(Qp-Qloss));
       assert(residual<1e-10,'Prvy zakon nezodpoveda meraniu');
       assert(abs((Qp+Qdh)-Qbefore)<1e-10,'Dvojite zapocitanie');
       file=[c.id '__' cas];
       tab=table((0:n-1)',Y(:,1),Y(:,2),Y(:,3),Y(:,4),Y(:,5),Y(:,6), ...
           'VariableNames',{'interval','T_bazen_C','Q_bazen_W','Q_DH_povodne_W', ...
           'Q_straty_W','Q_v85_povodna_sluzba_W','STOP_bazen'});
       writetable(tab,fullfile(output,['sim_' file '.csv']));
       s=struct('id',file,'pramen_v85',c.id,'scenar_bazen',cas, ...
           'simulink_v85_spusteny_teraz',true,'zhoda_retained_trace_bitwise',true,...
           'pocet_intervalov',n,'cas_h',sum(a.schedule(:,1)),...
           'v85_hp_direct_service_MWh',Qbefore,...
           'bazen_presmerovane_MWh',Qp,'dh_zostava_MWh',Qdh,...
           'v85_hull_direct_HP_MWh',r.direct_HP_service_MWh_hull,...
           'v85_hp_teplo_hull_MWh',r.hp_heat_MWh_hull,...
           'v85_kompresor_hull_MWh',r.compressor_work_MWh_hull,...
           'v85_zdroj_hull_MWh',r.recovered_source_MWh_hull,...
           'bazenska_energia_strat_MWh',Qloss,...
           'max_T_bazen_C',max(Y(:,1)), ...
           'energeticke_reziduum_bazen_MWh',residual,...
           'duplicita_MWh',abs(Qp+Qdh-Qbefore));
       if isempty(result),result=s;else,result(end+1)=s;end %#ok<SAGROW>
       fprintf('PASS_V85_POOL %s pool_MWh=%.9f remaining_DH_MWh=%.9f maxT=%.5f\n',...
           file,Qp,Qdh,s.max_T_bazen_C);
   end
end
close_system(namev85,0);close_system(namePool,0);
info=struct('status','VERIFIED_ON_REAL_EXECUTED_V85_TRACE',...
   'model_v85',namev85,'model_pool',namePool,'scope', ...
   'CERTIFIED_SHORT_HORIZON_HEAT_SERVICE_REALLOCATION_NO_ADDITIONAL_RECOVERY',...
   'warning','No year 8760 v85 input is available; no feedback to Stateflow v85; no vendor COP map',...
   'cases',result);
fid=fopen(fullfile(output,'most_v85_bazen_v03_SK.json'),'w','n','UTF-8');
assert(fid>0);fprintf(fid,'%s',jsonencode(info,PrettyPrint=true));fclose(fid);
fprintf('DONE_V85_BRIDGE %d scenare\n',numel(result));
