% Rocna simulacia 500 m3 bazena s tepelnym odpadom DC.
% Jednotky: W, s, degC. Vsetky profily su SYNTETICKE (nie merania).
folder=fileparts(mfilename('fullpath')); project=fileparts(fileparts(folder));
outdir=fullfile(project,'results','pool_dc_integration_v02');
if ~exist(outdir,'dir'), mkdir(outdir); end
name='DC_Bazen_Alokacia_Rok_v02_SK';
modelPath=fullfile(folder,[name '.slx']);
if ~exist(modelPath,'file'), vytvor_rocny_model_sk(); end
load_system(modelPath);
h=(0:8759)'; t=h*3600; hr=mod(h,24);
zima=0.5+0.5*cos(2*pi*h/8760);
den=double(hr>=8 & hr<20);
Qit=230e3*(0.94+0.06*cos(2*pi*h/168)+0.035*sin(2*pi*hr/24));
Qdc=0.86*Qit; % synteticky podiel dostupneho odpadoveho tepla
Tzdroj=27+8*cos(2*pi*(h-3200)/8760);
aktivita=0.5+0.5*den;
plachta=1-den;
Qdh=35000+65000*zima;
Qtes=27000*double(hr>=12 & hr<19);
vnutro=29+0.45*cos(2*pi*h/8760);
vlhkost=0.60+0.07*sin(2*pi*h/8760);
scenare={'zaklad','teply_zdroj','vypadok_168h','bez_plachty'};
vysledky=struct([]);
fig=figure('Visible','off','Color','w','Position',[40 40 1140 650]);
hold on;grid on;
for k=1:numel(scenare)
  nazov=scenare{k};
  ts=Tzdroj; cover=plachta; stop=zeros(size(h));
  if strcmp(nazov,'teply_zdroj'), ts=ts+12; end
  if strcmp(nazov,'vypadok_168h'),stop(h>=4000 & h<4168)=1;end
  if strcmp(nazov,'bez_plachty'),cover=zeros(size(plachta));end
  data=[Qdc,ts,aktivita,cover,Qdh,Qtes,ones(size(h)),stop,vnutro,vlhkost];
  profil_roka=timeseries(data,t);
  profil_roka=setinterpmethod(profil_roka,'zoh');
  assignin('base','profil_roka',profil_roka);
  simout=sim(name,'StopTime',num2str(t(end)));
  meranie=simout.get('rok_signaly');
  Y=squeeze(meranie.Data);
  if size(Y,1)~=numel(h),Y=Y';end
  assert(size(Y,1)==numel(h) && size(Y,2)==12,'Rozmery vystupu');
  tw=Y(:,1); qp=Y(:,2); ql=Y(:,3); qs=Y(:,4);
  pe=Y(:,5); dh=Y(:,6); tes=Y(:,7); rej=Y(:,8);
  rezim=Y(:,9); cop=Y(:,10); evap=Y(:,11); qd=Y(:,12);
  rDC=max(abs(qd-(qs+dh+tes+rej)));
  rHP=max(abs(qp-(qs+pe)));
  rPool=abs((tw(end)-16)*997*500*4182/3.6e9 - sum(qp-ql)/1e6);
  assert(rDC<1e-4,'CHYBA: bilancia DC');
  assert(rHP<1e-4,'CHYBA: bilancia TC/vymennik');
  assert(rPool<1e-6,'CHYBA: bilancia akumulacie vody');
  assert(max(tw)<27.801,'CHYBA: bezpecnostna hranica vody');
  if strcmp(nazov,'vypadok_168h')
     assert(all(qp(stop>0)==0) && all(dh(stop>0)==0) ...
       && all(tes(stop>0)==0),'CHYBA: interlock STOP');
  end
  tab=table(h,tw,qp,ql,qs,pe,dh,tes,rej,rezim,cop,evap,qd, ...
    'VariableNames',{'hodina','T_bazen_C','Q_bazen_W','Q_straty_W','Q_odobrane_DC_W', ...
    'P_TC_W','Q_siet_W','Q_akumulacia_W','Q_odpad_W','rezim_0_1_2', ...
    'COP','Q_vypar_W','Q_dostupne_DC_W'});
  writetable(tab,fullfile(outdir,['rocny_' nazov '_SK.csv']));
  s=struct(); s.scenar=nazov; s.hodin=numel(h);
  s.Teplota_max_C=max(tw);s.Teplota_koniec_C=tw(end);
  s.Teplota_min_C=min(tw);
  s.Dodane_bazen_MWh=sum(qp)/1e6;
  s.Straty_bazen_MWh=sum(ql)/1e6;
  s.Teplo_z_DC_do_bazena_MWh=sum(qs)/1e6;
  s.Elektrina_TC_MWh=sum(pe)/1e6;
  s.Do_siete_MWh=sum(dh)/1e6;
  s.Do_akumulacie_MWh=sum(tes)/1e6;
  s.Nevyuzite_teplo_MWh=sum(rej)/1e6;
  s.Dostupne_teplo_DC_MWh=sum(qd)/1e6;
  s.E_IT_MWh=sum(Qit)/1e6;
  s.ERF_scenar_PUE120=(sum(qs+dh)/1e6)/(1.20*s.E_IT_MWh);
  s.ERF_scenar_PUE152=(sum(qs+dh)/1e6)/(1.52*s.E_IT_MWh);
  s.Hodiny_priamy_vymennik=sum(rezim==1);
  s.Hodiny_tepelne_cerpadlo=sum(rezim==2);
  s.Hodiny_bez_ohrevu=sum(rezim==0);
  s.Nevyrovnanost_DC_W=rDC;
  s.Nevyrovnanost_HP_W=rHP;
  s.Nevyrovnanost_bazen_MWh=rPool;
  s.Vyhovuje_modelovemu_limitu_28C=all(tw<=28);
  if isempty(vysledky), vysledky=s; else, vysledky(end+1)=s; end
  plot(h/24,tw,'LineWidth',1.25,'DisplayName',strrep(nazov,'_',' '));
  fprintf('SCENAR %s Tmax=%.4f Qpool=%.2f MWh HPel=%.2f MWh rez=%.2g\n', ...
     nazov,s.Teplota_max_C,s.Dodane_bazen_MWh,s.Elektrina_TC_MWh,rPool);
end
yline(28,'--r','Limit 28 C');xlabel('Den simulacie');ylabel('Teplota vody [C]');
title('Data centrum - bazen 500 m3 | synteticke rocne scenare');
legend('Location','southeast');
exportgraphics(fig,fullfile(outdir,'rocna_teplota_SK.png'),'Resolution',160);
close(fig);
info=struct('model',name,'dataset','SYNTHETIC','model_step_s',3600, ...
    'season_year_hours',8760,'pool_m3',500,'pool_area_m2',312.5, ...
    'max_model_temperature_C',27.75,'PUE_scenar',[1.20 1.52], ...
    'sources',{{'https://eur-lex.europa.eu/eli/reg_del/2024/1364/oj', ...
    'https://www.slov-lex.sk/ezbierky/pravne-predpisy/SK/ZZ/2012/308/20121015.html', ...
    'https://handbook.ashrae.org/handbooks/F17/SI/F17_Ch36/f17_ch36_si.aspx'}}, ...
    'scenare',vysledky);
fid=fopen(fullfile(outdir,'rocne_vysledky_SK.json'),'w','n','UTF-8');
assert(fid~=-1,'JSON zapis');fprintf(fid,'%s',jsonencode(info,PrettyPrint=true));fclose(fid);
close_system(name,0);
fprintf('ROCNE_SIMULACIE_UKONCENE\n');
