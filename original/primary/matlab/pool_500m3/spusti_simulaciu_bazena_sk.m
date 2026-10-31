% SPUSTI_SIMULACIU_BAZENA_SK: reprodukovatelny sedemdnovy experiment.
% Pracovny jazyk je slovencina. Nezapisuje do modelov v85/v86.
priecinok = fileparts(mfilename('fullpath'));
projekt = fileparts(fileparts(priecinok));
vystup = fullfile(projekt,'results','pool_500m3_v01');
if ~exist(vystup,'dir'), mkdir(vystup); end
addpath(priecinok);
% Harmonogram: bazen otvoreny 08:00-20:00; krycia plachta cez noc.
t = (0:3600:7*86400)';
hodina = mod(t/3600,24);
je_otvorene = (hodina>=8 & hodina<20);
aktivita = 0.5+0.5*double(je_otvorene);
plachta = double(~je_otvorene);
% Model TC: tepelná energia do bazena 150 kW; zdroj DC: 112,5 kW;
% prikon kompresora: 37,5 kW pri scenarovom COP 4.
teplo_dostupne = timeseries(150000*ones(size(t)),t);
aktivita_bazena = timeseries(aktivita,t);
krycia_plachta = timeseries(plachta,t);
teplo_dostupne = setinterpmethod(teplo_dostupne,'zoh');
aktivita_bazena = setinterpmethod(aktivita_bazena,'zoh');
krycia_plachta = setinterpmethod(krycia_plachta,'zoh');
assignin('base','teplo_dostupne',teplo_dostupne);
assignin('base','aktivita_bazena',aktivita_bazena);
assignin('base','krycia_plachta',krycia_plachta);
cesta = vytvor_model_bazena_sk();
[~,nazov] = fileparts(cesta);
open_system(nazov);
zaznam = sim(nazov,'StopTime','604800');
T = zaznam.get('sim_teplota_vody');
Q = zaznam.get('sim_tepelny_vykon');
L = zaznam.get('sim_tepelne_straty');
E = zaznam.get('sim_vypar');
P = zaznam.get('sim_podlozie');
cas_h = T.Time/3600;
tabulka = table(cas_h,T.Data(:),Q.Data(:),L.Data(:),E.Data(:),P.Data(:), ...
    'VariableNames',{'cas_h','teplota_vody_C','teplo_do_bazena_W', ...
    'celkove_straty_W','strata_vypar_W','strata_konstrukcia_W'});
writetable(tabulka,fullfile(vystup,'simulink_vystup_TC_150kW_SK.csv'));
C = 997*500*4182;
dodane_J = trapz(Q.Time,Q.Data(:));
stratene_J = trapz(L.Time,L.Data(:));
ulozene_J = C*(T.Data(end)-T.Data(1));
relativna_odchylka = abs((dodane_J-stratene_J)-ulozene_J) / max(1,abs(dodane_J));
id = find(T.Data>=28,1,'first');
if isempty(id), cas_28_h=NaN; else, cas_28_h = T.Time(id)/3600; end
fig = figure('Visible','off','Color','w','Position',[100 100 1050 560]);
plot(cas_h,T.Data,'LineWidth',1.8);
grid on; hold on;
yline(28,'--','Pozadovana teplota 28 C');
xlabel('Cas [hod]');ylabel('Teplota vody [C]');
title('Ohrev bazena 500 m3 odpadovym teplom datoveho centra');
exportgraphics(fig,fullfile(vystup,'priebeh_teploty_simulink_SK.png'), ...
    'Resolution',160);
close(fig);
prehlad = struct('model',cesta,'cas_28_h',cas_28_h, ...
 'konecna_teplota_C',T.Data(end),'dodane_teplo_MWh',dodane_J/3.6e9, ...
 'straty_MWh',stratene_J/3.6e9,'ulozene_teplo_MWh',ulozene_J/3.6e9, ...
 'relativna_bilancna_odchylka',relativna_odchylka, ...
 'casovy_krok_s',60,'koniec_simulacie_s',T.Time(end));
txt=jsonencode(prehlad,PrettyPrint=true);
fid=fopen(fullfile(vystup,'simulink_akceptacia_SK.json'),'w','n','UTF-8');
assert(fid~=-1,'Nie je mozne zapisat JSON');
fprintf(fid,'%s',txt);fclose(fid);
fprintf('SIMULINK_OVERENE: cas28_h=%.3f Tkon=%.4f odchylka=%g\n', ...
    cas_28_h,T.Data(end),relativna_odchylka);
assert(numel(T.Time)>1000,'Malo zaznamov');
assert(abs(T.Data(1)-16)<1e-9,'Nespravna pociatocna teplota');
assert(all(isfinite(T.Data)),'Neplatna teplota');
assert(cas_28_h>0 && cas_28_h<168,'Nebola dosiahnuta cielova teplota');
assert(relativna_odchylka<0.005,'Neplatny energeticky zakon');
save_system(nazov);
close_system(nazov,0);
