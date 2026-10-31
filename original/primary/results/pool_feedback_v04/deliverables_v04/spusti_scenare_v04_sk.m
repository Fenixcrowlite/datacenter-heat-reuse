% V04: uzavrety dopyt bazena a TES -> Stateflow -> alokacia -> T,E -> feedback.
% Vsetky vstupy su synteticke, povodny v85 sa neprepisuje.
folder=fileparts(mfilename('fullpath'));project=fileparts(fileparts(folder));
output=fullfile(project,'results','pool_feedback_v04');
if ~isfolder(output),mkdir(output);end
model='DC_Bazen_Uzavreta_Regulacia_v04_SK';
assert(isfile(fullfile(folder,[model '.slx'])),'Najprv vytvorte model pomocou vytvor_model_v04_sk');
load_system(fullfile(folder,[model '.slx']));
dt=900; N=7*96;
k=(0:N-1)'; cas=k*dt;
h=cas/3600;hodina=mod(h,24);den=h/24;
active=double(hodina>=8 & hodina<20);
source=max(0,170000+30000*cos(2*pi*den/7)+20000*sin(2*pi*h/24));
tsource=30+7*cos(2*pi*(den-2)/7);
dhRequest=75000+35000*active+25000*(0.5+0.5*cos(2*pi*den/7));
air=29+0.6*sin(2*pi*den/7);
rh=0.60+0.07*sin(2*pi*den/7);
activity=0.5+0.5*active;
cover=1-active;
itOK=ones(N,1);poolOK=ones(N,1);tesOK=ones(N,1);hxOK=ones(N,1);
cases={'zaklad','vypnuty_bazen','vypadok_IT_24h','nulovy_zdroj_24h', ...
  'teplejsi_zdroj','bez_plachty','TES_vypnute','vysoky_dopyt_DH'};
results=struct([]);
fig=figure('Visible','off','Color','w','Position',[45 40 1200 690]);
hold on;grid on;
modeall=[];
for ic=1:numel(cases)
 caseName=cases{ic};
 qdc=source;ts=tsource;qdh=dhRequest;kryt=cover;
 it=itOK;pool=poolOK;tes=tesOK;hx=hxOK;
 if strcmp(caseName,'vypnuty_bazen')
    pool(h>=60 & h<108)=0;
 elseif strcmp(caseName,'vypadok_IT_24h')
    it(h>=72 & h<96)=0;
 elseif strcmp(caseName,'nulovy_zdroj_24h')
    qdc(h>=72 & h<96)=0;
 elseif strcmp(caseName,'teplejsi_zdroj')
    ts=ts+12;
 elseif strcmp(caseName,'bez_plachty')
    kryt=zeros(N,1);
 elseif strcmp(caseName,'TES_vypnute')
    tes=zeros(N,1);
 elseif strcmp(caseName,'vysoky_dopyt_DH')
    qdh=qdh+95000;
 end
 input=[qdc,ts,qdh,air,rh,activity,kryt,it,pool,tes,hx];
 profil_v04=timeseries(input,cas);
 profil_v04=setinterpmethod(profil_v04,'zoh');
 assignin('base','profil_v04',profil_v04);
 modelRun=sim(model,'StopTime',num2str(cas(end)), ...
    'ReturnWorkspaceOutputs','on');
 sig=modelRun.get('sim_energeticka_bilancia_v04');
 Y=squeeze(sig.Data);
 if size(Y,1)~=N,Y=Y';end
 assert(isequal(size(Y),[N 25]),'Nespravny pocet riadkov / stlpcov');
 T=Y(:,1);Et=Y(:,2);
 prevT=[16;T(1:end-1)];prevE=[0.45*3.6e9;Et(1:end-1)];
 Qpool=Y(:,4);Qloss=Y(:,5);
 closureWater=max(abs(Cpool()*(T-prevT)/dt-(Qpool-Qloss)));
 closureTES=max(abs((Et-prevE)/dt-(0.93*Y(:,9)-Y(:,10)/0.91-Y(:,21))));
 closureHP=max(abs(Y(:,7)+Y(:,8)+Y(:,9)-Y(:,14)-Y(:,15)));
 closureDC=max(abs(Y(:,18)-Y(:,6)-Y(:,14)-Y(:,17)));
 assert(closureWater<1e-6 && closureTES<1e-6,'Porusenie bilancie stavu');
 assert(closureHP<1e-6 && closureDC<1e-6,'Porusenie prveho zakona DC/HP');
 assert(max(abs(Y(:,22:25)),[],'all')<1e-5,'Rezidua tokov');
 assert(all(T<=27.751) && all(T>10),'Teplotna ochrana a stabilita');
 assert(all(Et>=-1e-5 & Et<=900*3.6e6+1e-4),'Limit energie TES');
 assert(all(Y(:,9).*Y(:,10)==0),'Súbežné nabíjanie a vybíjanie TES');
 assert(all(Qpool<=150000+1e-6 & Qpool>=0),'Bazenska kapacita');
 assert(all(Y(:,11)<=qdh+1e-6),'Sieť nemoze prekrocit dopyt');
 if strcmp(caseName,'vypnuty_bazen')
    assert(all(Qpool(pool<0.5)==0),'STOP bazen');
 end
 if strcmp(caseName,'vypadok_IT_24h')
    assert(all(Qpool(it<0.5)==0) && all(Y(it<0.5,15)==0),'Neopravnene vyuzitie DC pri IT STOP');
    assert(all(abs(Y(it<0.5,17)-qdc(it<0.5))<1e-6),'Independent reject IT');
 end
 if strcmp(caseName,'nulovy_zdroj_24h')
    assert(all(Qpool(qdc==0)==0),'Teplo z nicoty');
 end
 outtable=array2table([h,input,Y], ...
 'VariableNames',[{'cas_h'},{'Qdc_available_W','Tdc_C','Qdh_demand_W','Tair_C','RH','aktivita','plachta','IT_ok','BAZEN_ok','TES_ok','HX_ok'},...
 {'T_bazen_C','E_TES_J','Q_pool_req_W','Q_pool_W','Q_pool_loss_W',...
  'Q_direct_W','Q_HP_pool_W','Q_HP_DH_W','Q_HP_TES_charge_W','Q_TES_dis_W',...
  'Q_DH_delivered_W','Q_DH_unmet_W','Q_pool_unmet_W','Q_HP_source_W',...
  'P_HP_comp_W','P_aux_W','Q_reject_W','Qdc_in_W','COP','rezim_Stateflow',...
  'Q_TES_standing_loss_W','rez_DC_W','rez_HP_W','rez_pool_W','rez_DH_W'}]);
 writetable(outtable,fullfile(output,['scenar_' caseName '_SK.csv']));
 r=struct('scenar',caseName,'hodin',N/4,'stav','VERIFIED_SYNTHETIC',...
  'teplota_min_C',min(T),'teplota_max_C',max(T),'teplota_koniec_C',T(end),...
  'energia_TES_koniec_MWh',Et(end)/3.6e9,...
  'DC_available_MWh',sum(Y(:,18))*dt/3.6e9,...
  'DC_to_HP_source_MWh',sum(Y(:,14))*dt/3.6e9,...
  'DC_direct_MWh',sum(Y(:,6))*dt/3.6e9,...
  'DC_reject_MWh',sum(Y(:,17))*dt/3.6e9,...
  'Bazen_delivered_MWh',sum(Qpool)*dt/3.6e9,...
  'DH_delivered_MWh',sum(Y(:,11))*dt/3.6e9,...
  'DH_unmet_MWh',sum(Y(:,12))*dt/3.6e9,...
  'TES_charge_HP_MWh',sum(Y(:,9))*dt/3.6e9,...
  'TES_discharge_MWh',sum(Y(:,10))*dt/3.6e9,...
  'HP_compressor_MWh',sum(Y(:,15))*dt/3.6e9,...
  'HP_aux_MWh',sum(Y(:,16))*dt/3.6e9,...
  'Qpool_loss_MWh',sum(Y(:,5))*dt/3.6e9,...
  'modes',unique(Y(:,20))',...
  'max_DC_W_resid',closureDC,'max_HP_W_resid',closureHP, ...
  'max_water_W_resid',closureWater,'max_TES_W_resid',closureTES);
 if isempty(results),results=r;else,results(end+1)=r;end %#ok<SAGROW>
 modeall=[modeall;Y(:,20)]; %#ok<AGROW>
 plot(h/24,T,'LineWidth',1.3,'DisplayName',strrep(caseName,'_',' '));
 fprintf('V04_PASS %s P=%.4f MWh DH=%.4f MWh HPel=%.4f MWh maxT=%.5f modes=%s\n',...
    caseName,r.Bazen_delivered_MWh,r.DH_delivered_MWh,r.HP_compressor_MWh,...
    r.teplota_max_C,mat2str(r.modes));
end
assert(all(ismember([1 2 3 4],unique(modeall))),'Niektore Stateflow rezimy neboli navstivene');
reference=results(strcmp({results.scenar},'zaklad'));
withoutPool=results(strcmp({results.scenar},'vypnuty_bazen'));
assert(withoutPool.Bazen_delivered_MWh<reference.Bazen_delivered_MWh,'Bazenska spotreba neriadi dispecer');
hot=results(strcmp({results.scenar},'teplejsi_zdroj'));
assert(hot.DC_direct_MWh>reference.DC_direct_MWh,'Teplota zdroja neriadi rezim priameho HX');
high=results(strcmp({results.scenar},'vysoky_dopyt_DH'));
assert(high.DH_unmet_MWh>reference.DH_unmet_MWh,'Dopyt tepelnej siete neriadi nedostatok');
yline(27.75,'--r','Modelovy limit 27.75 C');
xlabel('Den simulacie');ylabel('Teplota vody [C]');
title('Uzavrety dispecing Stateflow - bazen 500 m3, 15 min');
legend('Location','southoutside','NumColumns',3,'Interpreter','none');
exportgraphics(fig,fullfile(output,'priebeh_teploty_v04_SK.png'),'Resolution',175);
close(fig);
full=struct('status','VERIFIED_SIMULINK_SYNTHETIC_CLOSED_LOOP',...
    'model',model,'step_s',dt,'intervals',N,'simulation_scope','7_DAYS_SYNTHETIC',...
    'old_v85_modified',false,'new_controller_not_original_v85',true,...
    'pool_volume_m3',500,'source_baseline','synthetic', ...
    'model_assumptions',struct('TES_max_MWh',0.9,'TES_initial_MWh',0.45,...
        'eta_charge',0.93,'eta_discharge',0.91,'TES_loss_fraction_day',0.002,...
        'T_pool_ceiling_C',27.75,'max_HP_thermal_kW',200, ...
        'max_HP_compressor_kW',55,'pool_max_kW',150), ...
    'scenarios',results);
fid=fopen(fullfile(output,'vysledky_dispecer_v04_SK.json'),'w','n','UTF-8');
assert(fid>0);fprintf(fid,'%s',jsonencode(full,PrettyPrint=true));fclose(fid);
close_system(model,0);
fprintf('V04_ALL_SIMULATIONS_PASSED COUNT=%d\n',numel(results));
function C=Cpool(),C=997*500*4182;end
