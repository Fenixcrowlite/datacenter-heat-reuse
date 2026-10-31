% Isolated v02: actual Simulink/Stateflow v04 copy + coupled DH states and delayed demand feedback.
% Source v04, CSV v08 and Stateflow v85 remain untouched. Synthetic/un-calibrated.
clearvars;
home=fileparts(mfilename('fullpath'));
live=fileparts(home); scada=fileparts(live); project=fileparts(scada);
stop1=fullfile(scada,'STOP');stop2=fullfile(live,'STOP');
assert(~isfile(stop1)&&~isfile(stop2),'DCHR:STOP','STOP flag detected');
srcDir=fullfile(project,'matlab','pool_feedback_v04');
src=fullfile(srcDir,'DC_Bazen_Uzavreta_Regulacia_v04_SK.slx');
expected='0D9A59466A0284CA6BB61D6756222DCCAFC2AC7AA683AE41DE35CE6D72F94EE0';
hashBefore=sha256_file(src);assert(strcmpi(hashBefore,expected),'DCHR:HASH','v04 source changed');
job='ca74c32211a44b6d9e83cd61d96cf59f';
cfgpath=fullfile(live,'runtime','jobs',job,'config.json');
cfg=jsondecode(fileread(cfgpath));
runroot=fullfile(home,'runtime','run_20261025');
if ~isfolder(runroot),mkdir(runroot);end
matlabDir=fullfile(matlabroot,'toolbox');
assert(isfolder(matlabDir));
addpath(srcDir,'-end');
data=[];
for ii=1:2
  assert(~isfile(stop1)&&~isfile(stop2),'DCHR:STOP','STOP before scenario');
  isOff=(ii==2);
  label='DH_ON';if isOff,label='DH_OFF_96h';end
  outdir=fullfile(runroot,label);
  assert(~isfolder(outdir),'DCHR:OVERWRITE','Refuse overwrite of prior run');
  mkdir(outdir);
  srcmodel='DCHR_DH_Dynamic_v02';
  clone=fullfile(outdir,[srcmodel '.slx']);
  [ok,msg]=copyfile(src,clone);assert(ok,msg);
  addpath(outdir,'-begin');
  cleanup=onCleanup(@() safe_close(srcmodel,outdir));
  load_system(clone);
  set_param(srcmodel,'Solver','FixedStepDiscrete','SolverType','Fixed-step','FixedStep','900',...
       'StopTime','603900','SimulationMode','normal','ReturnWorkspaceOutputs','on');
  dt=900;N=672;t=(0:N-1)'*dt;h=t/3600;day=h/24;
  active=double(mod(h,24)>=8 & mod(h,24)<20);
  qdc=max(0,170000+30000*cos(2*pi*day/7)+20000*sin(2*pi*h/24));
  qdc=min(qdc,1000*cfg.dc_available_limit_kw);
  Tdc=30+7*cos(2*pi*(day-2)/7)+cfg.source_temperature_offset_C;
  dh=75000+35000*active+25000*(0.5+0.5*cos(2*pi*day/7));
  dh=min(dh,1000*cfg.dh_request_limit_kw);
  if ~cfg.dh_enabled,dh(:)=0;end
  if isOff,dh(h>=96)=0;end
  air=29+0.6*sin(2*pi*day/7);rh=0.60+0.07*sin(2*pi*day/7);
  pool=ones(N,1)*double(cfg.pool_enabled);
  pool(h>=cfg.pool_off_from_h)=0;
  inputs=[qdc,Tdc,dh,air,rh,0.5+0.5*active,1-active,...
    ones(N,1)*double(cfg.it_enabled),pool,ones(N,1)*double(cfg.tes_enabled),...
    ones(N,1)*double(cfg.hx_enabled)];
  profil_v04=setinterpmethod(timeseries(inputs,t),'zoh');assignin('base','profil_v04',profil_v04);
  % Input profile is modified only inside this clone.
  rt=sfroot;
  d=rt.find('-isa','Stateflow.EMChart','Path',[srcmodel '/Dopyt_bazena_a_straty']);
  a=rt.find('-isa','Stateflow.EMChart','Path',[srcmodel '/Rozdelovac_energie_DC_TES_Bazen']);
  assert(numel(d)==1 && numel(a)==1,'Missing original v04 charts');
  dp=d.Script;ap=a.Script;
  poolW=1000*cfg.pool_limit_kw;hpW=1000*cfg.hp_thermal_limit_kw;
  d0='ziad=min([150000,Qsafe,Qset]);';
  a0='Qdirect=min([ziad,Qdc,150000,Qhxmax]);';
  hp0='QhpCap=min([200000,55000*cop,Qleft/max(1e-9,1-1/cop)]);';
  assert(contains(dp,d0)&&contains(ap,a0)&&contains(ap,hp0),'Original chart signature mismatch');
  dp=strrep(dp,d0,sprintf('ziad=min([%.17g,Qsafe,Qset]);',poolW));
  ap=strrep(ap,a0,sprintf('Qdirect=min([ziad,Qdc,%.17g,Qhxmax]);',poolW));
  ap=strrep(ap,hp0,sprintf('QhpCap=min([%.17g,55000*cop,Qleft/max(1e-9,1-1/cop)]);',hpW));
  if ~cfg.hp_pool_enabled
    p0='QhpPool=min(max(0,ziad-Qdirect),max(0,QhpCap-minDH));';
    p1='extraPool=min(max(0,ziad-Qdirect-QhpPool),spare);';
    assert(contains(ap,p0)&&contains(ap,p1));
    ap=strrep(ap,p0,'QhpPool=0;');
    ap=strrep(ap,p1,'extraPool=0;');
  end
  d.Script=dp;a.Script=ap;
  build_dh_blocks(srcmodel,cfg);
  set_param(srcmodel,'SimulationCommand','update');
  save_system(srcmodel,clone);
  assert(~isfile(stop1)&&~isfile(stop2),'DCHR:STOP','STOP pre-simulation');
  simout=sim(srcmodel,'StopTime',num2str(t(end)),'ReturnWorkspaceOutputs','on');
  Y=squeeze(simout.get('sim_energeticka_bilancia_v04').Data);
  D=squeeze(simout.get('sim_dynamika_CZT_v02').Data);
  U=squeeze(simout.get('sim_dopyt_feedback_CZT_v02').Data);
  if size(Y,1)~=N,Y=Y';end
  if size(D,1)~=N,D=D';end
  if size(U,1)~=N,U=U';end
  assert(isequal(size(Y),[N,25])&&isequal(size(D),[N,9])&&size(U,1)==N,...
      'DCHR:DATA','Dimension mismatch');
  assert(all(isfinite([Y,D,U]),'all'),'Nonfinite model output');
  assert(max(abs(D(:,5)))<1e-5,'DCHR:ENERGY','DH balance failed');
  assert(all(D(:,3)>=-1e-5) && all(D(:,3)<=U(:,3)+1e-5),'Demand violation');
  assert(all(D(:,4)>=0)&&all(D(:,6)>=0),'Pump negative');
  assert(all(abs(Y(:,22:25))<1e-5,'all'),'v04 balance issue');
  assert(all(Y(:,4)<=poolW+1e-5),'Pool power limit');
  if isOff
    mask=h>=96;
    assert(all(abs(Y(mask,11))<1e-5)&&all(abs(D(mask,3))<1e-5),...
      'DCHR:DH_OFF','DH heat after shutdown');
    assert(all(abs(D(mask,4))<1e-5)&&all(abs(D(mask,6))<1e-5),...
      'DCHR:FLOW_OFF','Pump after shutdown');
  end
  if ~cfg.hp_pool_enabled,assert(all(abs(Y(:,7))<1e-5));end
  tab=array2table([h,Y,D,U(:,3)],'VariableNames',[...
    {'cas_h'},arrayfun(@(k) sprintf('v04_y_%02d',k),1:25,'UniformOutput',false),...
    {'T_DH_supply_C','T_DH_return_C','Q_DH_load_W','P_DH_pump_W',...
     'DH_residual_W','DH_massflow_kg_s','Q_DH_source_W',...
     'Q_DH_loss_supply_W','Q_DH_loss_return_W','Q_DH_request_feedback_W'}]);
  writetable(tab,fullfile(outdir,'trajectory.csv'));
  metrics=struct('status','PASS','model','DCHR_DH_Dynamic_v02',...
     'scenario',label,'source_class','D_SYNTHETIC','quality','D_ASSUMED',...
     'rows',N,'dt_s',dt,'hardware_enabled',false,...
     'base_model_sha256',hashBefore,'dh_feedback_on',true,...
     'max_dh_residual_W',max(abs(D(:,5))),...
     'DH_source_MWh',sum(Y(:,11))*dt/3.6e9,...
     'DH_delivered_MWh',sum(D(:,3))*dt/3.6e9,...
     'DH_pump_electric_MWh',sum(D(:,4))*dt/3.6e9,...
     'pool_heat_MWh',sum(Y(:,4))*dt/3.6e9,...
     'DH_request_changed_rows',sum(abs(U(:,3)-inputs(:,3))>1e-3),...
     'is_multiphyiscal_calibrated',false,...
     'model_not_v85',true);
  fid=fopen(fullfile(outdir,'summary.json'),'w','n','UTF-8');assert(fid>0);
  fprintf(fid,'%s',jsonencode(metrics,PrettyPrint=true));fclose(fid);
  disp(jsonencode(metrics));
  data=[data;metrics]; %#ok<AGROW>
  close_system(srcmodel,0);clear cleanup;
  rmpath(outdir);
end
hashAfter=sha256_file(src);assert(strcmp(hashBefore,hashAfter),'DCHR:HASH','Base modified');
fid=fopen(fullfile(runroot,'release.json'),'w','n','UTF-8');assert(fid>0);
fprintf(fid,'%s',jsonencode(struct('status','PASS','runs',data,'source_hash_unchanged',true),PrettyPrint=true));fclose(fid);
fprintf('DCHR_DH_SIMULINK_V02_PASS runs=2 source_unchanged=1\n');

function build_dh_blocks(m,cfg)
  add_block('simulink/Discrete/Unit Delay',[m '/Ts_prev_CZT'],'SampleTime','900',...
    'InitialCondition',sprintf('%.15g',cfg.dh_return_C+4),'Position',[280 330 335 360]);
  add_block('simulink/Discrete/Unit Delay',[m '/Tr_prev_CZT'],'SampleTime','900',...
    'InitialCondition',sprintf('%.15g',cfg.dh_return_C),'Position',[290 505 345 535]);
  add_block('simulink/User-Defined Functions/MATLAB Function',[m '/Feedback_dopyt_CZT'],...
    'Position',[405 330 610 420]);
  add_block('simulink/User-Defined Functions/MATLAB Function',[m '/Dynamika_CZT_v02'],...
    'Position',[825 335 1050 535]);
  add_block('simulink/Signal Routing/Selector',[m '/Ts_from_DH'],...
    'NumberOfDimensions','1','IndexOptionArray',{'Index vector (dialog)'},...
    'Indices','1','InputPortWidth','9','Position',[1110 340 1160 367]);
  add_block('simulink/Signal Routing/Selector',[m '/Tr_from_DH'],...
    'NumberOfDimensions','1','IndexOptionArray',{'Index vector (dialog)'},...
    'Indices','2','InputPortWidth','9','Position',[1110 390 1160 420]);
  add_block('simulink/Sinks/To Workspace',[m '/DH_trace_v02'],...
    'Position',[1150 470 1310 505],'VariableName','sim_dynamika_CZT_v02','SaveFormat','Timeseries');
  add_block('simulink/Sinks/To Workspace',[m '/DH_feedback_v02'],...
    'Position',[650 320 810 355],'VariableName','sim_dopyt_feedback_CZT_v02','SaveFormat','Timeseries');
  rt=sfroot;
  fb=rt.find('-isa','Stateflow.EMChart','Path',[m '/Feedback_dopyt_CZT']);
  dh=rt.find('-isa','Stateflow.EMChart','Path',[m '/Dynamika_CZT_v02']);
  assert(numel(fb)==1&&numel(dh)==1);
  fb.Script=strjoin({
    'function v=feedback_czt(u,T_supply_prev)'
    '%#codegen'
    'v=u;'
    'if u(3)>0'
    '  multiplier=max(0.45,min(1.25,1+0.025*(52-T_supply_prev)));'
    '  v(3)=min(500000,u(3)*multiplier);'
    'else'
    '  v(3)=0;'
    'end'
    'end'},newline);
  dh.Script=make_dh_chart(cfg);
  fbu=fb.find('-isa','Stateflow.Data','Name','u');
  fbv=fb.find('-isa','Stateflow.Data','Name','v');
  dhu=dh.find('-isa','Stateflow.Data','Name','u');
  dhy=dh.find('-isa','Stateflow.Data','Name','y');
  dhz=dh.find('-isa','Stateflow.Data','Name','z');
  fbu.Props.Array.Size='[1 11]'; fbv.Props.Array.Size='[1 11]';
  dhu.Props.Array.Size='[1 11]'; dhy.Props.Array.Size='[1 25]';
  dhz.Props.Array.Size='[1 9]';
  for dest={'Dopyt_bazena_a_straty/3','Dispecer_Stateflow/2',...
             'Rozdelovac_energie_DC_TES_Bazen/6'}
    delete_line(m,'Prevadzkove_vstupy_DC/1',dest{1});
  end
  add_line(m,'Prevadzkove_vstupy_DC/1','Feedback_dopyt_CZT/1','autorouting','on');
  add_line(m,'Ts_prev_CZT/1','Feedback_dopyt_CZT/2','autorouting','on');
  for dest={'Dopyt_bazena_a_straty/3','Dispecer_Stateflow/2',...
             'Rozdelovac_energie_DC_TES_Bazen/6'}
    add_line(m,'Feedback_dopyt_CZT/1',dest{1},'autorouting','on');
  end
  add_line(m,'Feedback_dopyt_CZT/1','DH_feedback_v02/1','autorouting','on');
  add_line(m,'Rozdelovac_energie_DC_TES_Bazen/1','Dynamika_CZT_v02/1','autorouting','on');
  add_line(m,'Feedback_dopyt_CZT/1','Dynamika_CZT_v02/2','autorouting','on');
  add_line(m,'Ts_prev_CZT/1','Dynamika_CZT_v02/3','autorouting','on');
  add_line(m,'Tr_prev_CZT/1','Dynamika_CZT_v02/4','autorouting','on');
  add_line(m,'Dynamika_CZT_v02/1','Ts_from_DH/1','autorouting','on');
  add_line(m,'Dynamika_CZT_v02/1','Tr_from_DH/1','autorouting','on');
  add_line(m,'Dynamika_CZT_v02/1','DH_trace_v02/1','autorouting','on');
  add_line(m,'Ts_from_DH/1','Ts_prev_CZT/1','autorouting','on');
  add_line(m,'Tr_from_DH/1','Tr_prev_CZT/1','autorouting','on');
end

function s=make_dh_chart(cfg)
  mdot=cfg.dh_mass_flow_kg_s; t0=cfg.dh_return_C;
  s=sprintf([ ...
    'function z=dynamika_czt(y,u,Ts,Tr)\n',...
    '%%#codegen\n',...
    'dt=900;cp=4182;cs=10000*cp;cr=10000*cp;Ta=15;UAs=120;UAr=80;\n',...
    'q=max(0,y(11));demand=max(0,u(3));\n',...
    'target=%.17g;mdot=%.17g;\n',...
    'if demand<=1e-9,mdot=0;end\n',...
    'f=mdot*cp;ss=cs/dt+f+UAs;rr=cr/dt+f+UAr;det=ss*rr-f*f;\n',...
    'rhsS=cs/dt*Ts+q+UAs*Ta;rhsR=cr/dt*Tr+UAr*Ta;\n',...
    'tS0=(rhsS*rr+f*rhsR)/det;\n',...
    'if demand<=0 || f==0 || f*(tS0-target)<=0\n',...
    '  load=0;tS=tS0;tR=(ss*rhsR+f*rhsS)/det;\n',...
    'else\n',...
    '  tSc=(rhsS*rr+f*(rhsR-demand))/det;\n',...
    '  if f*(tSc-target)>=demand\n',...
    '    load=demand;tS=tSc;tR=(ss*(rhsR-demand)+f*rhsS)/det;\n',...
    '  else\n',...
    '    tR=(rhsR+f*target)/rr;tS=(rhsS+f*tR)/ss;\n',...
    '    load=max(0,min(demand,f*(tS-target)));\n',...
    '  end\n',...
    'end\n',...
    'qs=UAs*(tS-Ta);qr=UAr*(tR-Ta);\n',...
    'res=(cs*(tS-Ts)+cr*(tR-Tr))/dt+qs+qr+load-q;\n',...
    'dp=150000*(mdot/5)^2; pump=dp*mdot/(997*0.70);\n',...
    'z=[tS,tR,load,pump,res,mdot,q,qs,qr];\n',...
    'end\n'],t0,mdot);
end

function result=sha256_file(path)
  import java.security.MessageDigest
  md=MessageDigest.getInstance('SHA-256');
  b=fileread_bin(path);
  md.update(b);
  raw=typecast(md.digest(),'uint8');
  result=upper(reshape(dec2hex(raw,2)',1,[]));
end
function b=fileread_bin(path)
  f=fopen(path,'rb');assert(f>0);c=onCleanup(@()fclose(f));b=fread(f,Inf,'uint8=>uint8');
end
function safe_close(m,path)
  if bdIsLoaded(m),close_system(m,0);end
  if contains(path,pathsep),return;end
end
