% Konfrontacia predpokladaneho Carnot COP s certifikovanymi Eurovent bodmi.
here=fileparts(mfilename('fullpath'));addpath(here);
P=readtable(fullfile(here,'manufacturer_certified_points_carrier.csv'));
n=height(P);
pred=zeros(n,1);delta=zeros(n,1);stat=strings(n,1);
for k=1:n
 [c,st]=manufacturer_cop_reference_SK(P.source_out_C(k),P.sink_out_C(k),here);
 assert(abs(c-P.COP(k))<1e-12);
 pred(k)=max(2.2,min(7.0,0.50*(273.15+P.sink_out_C(k))/(P.sink_out_C(k)-P.source_out_C(k))));
 delta(k)=100*(pred(k)-c)/c;stat(k)=st;
end
[bad,sta]=manufacturer_cop_reference_SK(25,70,here);
assert(isnan(bad) && sta=="UNSUPPORTED_UNCERTIFIED_CONDITION");
[bad2,sta2]=manufacturer_cop_reference_SK(7,70,here);
assert(isnan(bad2) && sta2=="UNSUPPORTED_UNCERTIFIED_CONDITION");
[c50,st50]=manufacturer_cop_reference_SK(7,50,here);
assert(st50=="INTERPOLATED_NONCERTIFIED_BETWEEN_POINTS" && c50<P.COP(2) && c50>P.COP(3));
S=table(P.source_out_C,P.sink_out_C,P.COP,pred,delta,stat,...
 'VariableNames',{'SourceOutlet_C','SinkOutlet_C','COP_Certified',...
 'COP_ScenarioCarnot','CarnotRelativeError_percent','EvidenceStatus'});
writetable(S,fullfile(here,'carrier_cop_certified_vs_scenario.csv'));
f=figure('Visible','off','Color','w','Position',[50 50 950 590]);
plot(S.SinkOutlet_C,S.COP_Certified,'o-','LineWidth',1.7);hold on;
plot(S.SinkOutlet_C,S.COP_ScenarioCarnot,'s--','LineWidth',1.7);
grid on;xlabel('Teplota vystupu kondenzatora [C]');ylabel('COP');
title('Carrier 61XWH-ZE07: Eurovent W10-7 vs modelovy Carnot 0.50');
legend('Certifikovane Eurovent body','Modelovy Carnot 0.50','Location','best');
exportgraphics(f,fullfile(here,'carrier_cop_certified_comparison_SK.png'),'Resolution',170);close(f);
fprintf('MANUFACTURER_COP_REFERENCE_QA_PASS certified_points=%d error_range_percent=[%.1f, %.1f], OUTSIDE_GRID_BLOCKED\n',...
 n,min(delta),max(delta));
