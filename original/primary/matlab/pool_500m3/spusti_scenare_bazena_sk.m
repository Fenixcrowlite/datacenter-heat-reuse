% Viacnasobne sedemdnové scenare Simulink: 75/150/300 kW, kryt versus bez krytu.
% Zachovava a opätovne pouziva existujuci samostatny model bazena.
priecinok=fileparts(mfilename('fullpath'));
projekt=fileparts(fileparts(priecinok));
vystup=fullfile(projekt,'results','pool_500m3_v01');
nazov='Bazen_DC_Ohrev_500m3_SK';
load_system(fullfile(priecinok,[nazov '.slx']));
t=(0:3600:7*86400)';
hodina=mod(t/3600,24);
aktivita=0.5+0.5*double(hodina>=8 & hodina<20);
kryt=double(hodina<8 | hodina>=20);
scenare=struct('nazov',{'TC_75kW','TC_150kW','TC_300kW','TC_150kW_bez_plachty'}, ...
 'vykon_W',{75000,150000,300000,150000},'s_plachtou',{true,true,true,false});
vysledky=struct([]);
fig=figure('Visible','off','Color','w','Position',[30 30 1000 540]);
hold on;grid on;
for k=1:numel(scenare)
 s=scenare(k);
 teplo_dostupne=timeseries(s.vykon_W*ones(size(t)),t);
 aktivita_bazena=timeseries(aktivita,t);
 krycia_plachta=timeseries(double(s.s_plachtou)*kryt,t);
 teplo_dostupne=setinterpmethod(teplo_dostupne,'zoh');
 aktivita_bazena=setinterpmethod(aktivita_bazena,'zoh');
 krycia_plachta=setinterpmethod(krycia_plachta,'zoh');
 assignin('base','teplo_dostupne',teplo_dostupne);
 assignin('base','aktivita_bazena',aktivita_bazena);
 assignin('base','krycia_plachta',krycia_plachta);
 out=sim(nazov,'StopTime','604800');
 T=out.get('sim_teplota_vody');H=out.get('sim_tepelny_vykon');
 S=out.get('sim_tepelne_straty');
 miesto=find(T.Data(:)>=28,1,'first');
 if isempty(miesto),first28=NaN;else,first28=T.Time(miesto)/3600;end
 Eteplo=trapz(H.Time,H.Data(:))/3.6e9;
 Estraty=trapz(S.Time,S.Data(:))/3.6e9;
 Eulozene=997*500*4182*(T.Data(end)-T.Data(1))/3.6e9;
 odchylka=abs(Eulozene-(Eteplo-Estraty))/max(1,Eteplo);
 vystupna=table(T.Time(:)/3600,T.Data(:),H.Data(:),S.Data(:),...
    'VariableNames',{'cas_h','teplota_C','ohrev_W','straty_W'});
 writetable(vystupna,fullfile(vystup,['simulink_' s.nazov '.csv']));
 plot(T.Time(:)/3600,T.Data(:),'LineWidth',1.55);
 vysledky(k).scenar=s.nazov;
 vysledky(k).vykon_kW=s.vykon_W/1000;
 vysledky(k).plachta=s.s_plachtou;
 vysledky(k).prvy_dosiahnuty_28C_h=first28;
 vysledky(k).teplota_na_konci_C=T.Data(end);
 vysledky(k).dodane_teplo_MWh=Eteplo;
 vysledky(k).straty_MWh=Estraty;
 vysledky(k).reziduum_rel=odchylka;
 fprintf('SCENAR_OK: %s 28C=%0.3fh reziduum=%g\n',s.nazov,first28,odchylka);
 assert(isfinite(first28)&&first28<168,'Cielova teplota nedosiahnuta');
 assert(odchylka<0.005,'Nesedi prvy zakon termodynamiky');
end
yline(28,'--k','Pozadovana teplota');
xlabel('Cas [h]');ylabel('Teplota vody [C]');
title('Porovnanie scenarov ohrevu bazena 500 m3');
legend({scenare.nazov},'Interpreter','none','Location','southeast');
exportgraphics(fig,fullfile(vystup,'simulink_porovnanie_scenarov_SK.png'),'Resolution',165);
close(fig);
fid=fopen(fullfile(vystup,'simulink_scenare_SK.json'),'w','n','UTF-8');
assert(fid~=-1);
fprintf(fid,'%s',jsonencode(vysledky,PrettyPrint=true));
fclose(fid);
close_system(nazov,0);
fprintf('SIMULINK_4_SCENARE_UKONCENE\n');
