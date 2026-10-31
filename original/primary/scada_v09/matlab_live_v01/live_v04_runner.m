% SCADA <-> genuine 7-day Simulink/Stateflow v04 run. Originals never saved.
cfgFile=getenv('DCHR_JOB_JSON');
assert(~isempty(cfgFile)&&isfile(cfgFile),'Missing private config');
cfg=jsondecode(fileread(cfgFile)); jobdir=fileparts(cfgFile);
project=cfg.project_root; srcDir=fullfile(project,'matlab','pool_feedback_v04');
model='DC_Bazen_Uzavreta_Regulacia_v04_SK'; src=fullfile(srcDir,[model '.slx']);
assert(isfile(src) && ~isfile(fullfile(project,'scada_v09','STOP')),'Source missing or STOP');
dest=fullfile(jobdir,[model '.slx']);assert(~isfile(dest),'Job must be new');
[ok,msg]=copyfile(src,dest);assert(ok,msg); addpath(srcDir,'-end');addpath(jobdir,'-begin');
clean=onCleanup(@() safeclose(model));load_system(dest);rt=sfroot;
d=rt.find('-isa','Stateflow.EMChart','Path',[model '/Dopyt_bazena_a_straty']);
a=rt.find('-isa','Stateflow.EMChart','Path',[model '/Rozdelovac_energie_DC_TES_Bazen']);
assert(numel(d)==1 && numel(a)==1,'Missing MATLAB Function charts');
dp=d.Script;ap=a.Script; poolW=1000*cfg.pool_limit_kw;hpW=1000*cfg.hp_thermal_limit_kw;
d0='ziad=min([150000,Qsafe,Qset]);';
a0='Qdirect=min([ziad,Qdc,150000,Qhxmax]);';
h0='QhpCap=min([200000,55000*cop,Qleft/max(1e-9,1-1/cop)]);';
assert(contains(dp,d0)&&contains(ap,a0)&&contains(ap,h0),'Chart revision mismatch');
dp=strrep(dp,d0,sprintf('ziad=min([%.17g,Qsafe,Qset]);',poolW));
ap=strrep(ap,a0,sprintf('Qdirect=min([ziad,Qdc,%.17g,Qhxmax]);',poolW));
ap=strrep(ap,h0,sprintf('QhpCap=min([%.17g,55000*cop,Qleft/max(1e-9,1-1/cop)]);',hpW));
if ~cfg.hp_pool_enabled
 p0='QhpPool=min(max(0,ziad-Qdirect),max(0,QhpCap-minDH));';
 p1='extraPool=min(max(0,ziad-Qdirect-QhpPool),spare);';
 assert(contains(ap,p0)&&contains(ap,p1),'HP disable change invalid');
 ap=strrep(ap,p0,'QhpPool=0;');ap=strrep(ap,p1,'extraPool=0;');
end
d.Script=dp;a.Script=ap;
dt=900;N=672;k=(0:N-1)';sec=k*dt;h=sec/3600;day=h/24;
active=double(mod(h,24)>=8&mod(h,24)<20);
qdc=max(0,170000+30000*cos(2*pi*day/7)+20000*sin(2*pi*h/24));
qdc=min(qdc,1000*cfg.dc_available_limit_kw);
Tdc=30+7*cos(2*pi*(day-2)/7)+cfg.source_temperature_offset_C;
dh=75000+35000*active+25000*(0.5+0.5*cos(2*pi*day/7));
dh=min(dh,1000*cfg.dh_request_limit_kw);
if ~cfg.dh_enabled,dh(:)=0;end
dh(h>=cfg.dh_off_from_h)=0;
air=29+0.6*sin(2*pi*day/7);rh=0.60+0.07*sin(2*pi*day/7);
activity=0.5+0.5*active;cover=1-active;
pool=ones(N,1)*double(cfg.pool_enabled);pool(h>=cfg.pool_off_from_h)=0;
inputs=[qdc,Tdc,dh,air,rh,activity,cover,...
  ones(N,1)*double(cfg.it_enabled),pool,ones(N,1)*double(cfg.tes_enabled),...
  ones(N,1)*double(cfg.hx_enabled)];
profil_v04=setinterpmethod(timeseries(inputs,sec),'zoh');
assignin('base','profil_v04',profil_v04);
assert(~isfile(fullfile(project,'scada_v09','STOP')),'STOP before sim');
run=sim(model,'StopTime',num2str(sec(end)),'ReturnWorkspaceOutputs','on');
Y=squeeze(run.get('sim_energeticka_bilancia_v04').Data);
if size(Y,1)~=N,Y=Y';end
assert(isequal(size(Y),[N,25])&&all(isfinite(Y),'all'),'Invalid simulation result');
C=997*500*4182;
pT=[16;Y(1:end-1,1)];pE=[0.45*3.6e9;Y(1:end-1,2)];
errT=max(abs(C*(Y(:,1)-pT)/dt-(Y(:,4)-Y(:,5))));
errE=max(abs((Y(:,2)-pE)/dt-(0.93*Y(:,9)-Y(:,10)/0.91-Y(:,21))));
errF=max(abs(Y(:,22:25)),[],'all');
assert(errT<1e-5 && errE<1e-5 && errF<1e-5,'Energy closure failed');
assert(all(Y(:,1)<=27.751 & Y(:,1)>10),'Water temperature bounds');
assert(all(Y(:,2)>=-1e-4 & Y(:,2)<=900*3.6e6+1e-4),'TES bounds');
assert(all(Y(:,9).*Y(:,10)==0),'TES simultaneous charge/discharge');
assert(all(Y(:,4)<=poolW+1e-4) && all(Y(:,11)<=dh+1e-4),'Power limits');
assert(all(Y(pool<.5,4)==0) && all(Y(dh==0,11)==0),'Disabled branch receives heat');
if ~cfg.hp_pool_enabled,assert(all(Y(:,7)==0),'HP pool still active');end
% DH supply is a derived instantaneous estimate; not hydraulic simulation.
Tdh=cfg.dh_return_C+Y(:,11)/(cfg.dh_mass_flow_kg_s*4182);
names={'cas_h','T_pool_C','E_TES_J','Q_pool_request_W','Q_pool_W',...
 'Q_pool_losses_W','Q_HX_direct_W','Q_HP_pool_W','Q_HP_DH_W',...
 'Q_HP_TES_W','Q_TES_discharge_W','Q_DH_W','Q_DH_unmet_W',...
 'Q_pool_unmet_W','Q_HP_source_W','P_HP_W','P_aux_W',...
 'Q_reject_W','Q_DC_W','COP','stateflow_mode',...
 'Q_TES_losses_W','residual_DC_W','residual_HP_W',...
 'residual_pool_W','residual_DH_W','T_DH_supply_derived_C'};
tab=array2table([h,Y,Tdh],'VariableNames',names);
writetable(tab,fullfile(jobdir,'result.csv'));
meta=struct('status','VERIFIED_SIMULINK_NEW_RUN','source_class','D_SYNTHETIC',...
 'derived_quality','D_DERIVED','model',model,...
 'model_scope','v04 closed loop, not v08 or v85','dt_s',dt,'rows',N,...
 'pool_volume_m3',500,'hardware_enabled',false,...
 'closure_pool_W',errT,'closure_TES_W',errE,'closure_flow_W',errF,...
 'max_T_pool_C',max(Y(:,1)),'final_T_pool_C',Y(end,1),...
 'total_pool_MWh',sum(Y(:,4))*dt/3.6e9,...
 'total_DH_MWh',sum(Y(:,11))*dt/3.6e9,...
 'total_reject_MWh',sum(Y(:,17))*dt/3.6e9,...
 'total_HP_electrical_MWh',sum(Y(:,15))*dt/3.6e9,...
 'dh_supply_note','Derived Q/mcp, no pipe inertia');
fid=fopen(fullfile(jobdir,'result.json'),'w','n','UTF-8');assert(fid>0);
fprintf(fid,'%s',jsonencode(meta,PrettyPrint=true));fclose(fid);
fprintf('DCHR_LIVE_SIMULINK_PASS rows=%d pool_MWh=%.6f dh_MWh=%.6f\n',N,meta.total_pool_MWh,meta.total_DH_MWh);
function safeclose(name)
if bdIsLoaded(name),close_system(name,0);end
end
