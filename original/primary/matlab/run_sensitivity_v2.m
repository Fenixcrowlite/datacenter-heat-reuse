function run_sensitivity_v2()
%RUN_SENSITIVITY_V2 Isolated parameter maps for the component model.
rootDir=fileparts(fileparts(mfilename('fullpath'))); R=fullfile(rootDir,'results'); F=fullfile(R,'figures');
base=default_config_v2(); input=dchr.make_inputs(base);
sourceT=(20:5:50)'; supplyT=(50:10:90)'; nr=numel(sourceT)*numel(supplyT);
A=zeros(nr,6); n=0;
for i=1:numel(sourceT)
 for j=1:numel(supplyT)
  cfg=base; cfg.model.dh_temperature="fixed"; cfg.hp.supply_temp_C=supplyT(j);
  cfg.dc.source_temp_C=sourceT(i); cfg.dc.recovery_fraction=.85; cfg.storage.capacity_MWh=0;
  cfg.storage.charge_limit_MW=0; cfg.storage.discharge_limit_MW=0;
  o=dchr.simulate_system_v2(cfg,input); m=dchr.compute_metrics_v2(cfg,o); n=n+1;
  A(n,:)=[sourceT(i),supplyT(j),m.mean_cop,m.coverage_fraction,m.hp_electric_MWh,m.screening_LCOH_EUR_per_MWh];
 end
end
T=array2table(A,'VariableNames',{'SourceTemp_C','SupplyTemp_C','MeanCOP','Coverage','HPElectric_MWh','ScreeningLCOH_EUR_MWh'});
writetable(T,fullfile(R,'temperature_lift_sensitivity_v2.csv'));
COP=reshape(A(:,3),numel(supplyT),numel(sourceT))'; COV=reshape(A(:,4),numel(supplyT),numel(sourceT))';
f=figure('Visible','off','Position',[100 100 1000 650]); imagesc(supplyT,sourceT,COP); axis xy; colorbar; xlabel('DH supply [C]'); ylabel('DC source [C]'); title('v0.2 Mean COP map');
exportgraphics(f,fullfile(F,'11_cop_map_v2.png'),'Resolution',200); close(f);
f=figure('Visible','off','Position',[100 100 1000 650]); imagesc(supplyT,sourceT,100*COV); axis xy; colorbar; xlabel('DH supply [C]'); ylabel('DC source [C]'); title('v0.2 Heat coverage [%]');
exportgraphics(f,fullfile(F,'12_coverage_map_v2.png'),'Resolution',200); close(f);

sizes=[0 25 50 100 250 500 1000]'; B=zeros(numel(sizes),6);
for i=1:numel(sizes)
 cfg=base; cfg.dc.source_temp_C=45; cfg.dc.recovery_fraction=.90; cfg.storage.capacity_MWh=sizes(i);
 if sizes(i)==0, cfg.storage.charge_limit_MW=0; cfg.storage.discharge_limit_MW=0; end
 o=dchr.simulate_system_v2(cfg,input); m=dchr.compute_metrics_v2(cfg,o);
 B(i,:)=[sizes(i),m.coverage_fraction,m.gas_heat_MWh,m.curtailed_hp_heat_MWh,m.opex_saving_EUR,m.screening_LCOH_EUR_per_MWh];
end
S=array2table(B,'VariableNames',{'Storage_MWh','Coverage','GasHeat_MWh','CurtailedHPHeat_MWh','OpexSaving_EUR','ScreeningLCOH_EUR_MWh'});
writetable(S,fullfile(R,'storage_sensitivity_v2.csv'));
f=figure('Visible','off','Position',[100 100 1000 600]); yyaxis left; plot(S.Storage_MWh,100*S.Coverage,'o-','LineWidth',1.4); ylabel('Coverage [%]'); yyaxis right; plot(S.Storage_MWh,S.ScreeningLCOH_EUR_MWh,'s-','LineWidth',1.4); ylabel('Screening LCOH [EUR/MWh]'); xlabel('Storage [MWh]'); grid on; title('Storage benefit versus cost proxy');
exportgraphics(f,fullfile(F,'13_storage_tradeoff_v2.png'),'Resolution',200); close(f);
end
