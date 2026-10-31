function run_sensitivity()
%RUN_SENSITIVITY Factor-isolated sweeps for temperature lift and storage sizing.
rootDir = fileparts(fileparts(mfilename('fullpath')));
resultsDir = fullfile(rootDir,'results'); figDir = fullfile(resultsDir,'figures');
base = default_config(); input = dchr.make_inputs(base);

sourceT = (20:5:50)'; supplyT = (50:10:90)';
COP = zeros(numel(sourceT),numel(supplyT)); HPE = COP; Cov = COP; Save = COP;
for i=1:numel(sourceT)
    for j=1:numel(supplyT)
        cfg=base; cfg.dc.source_temp_C=sourceT(i); cfg.dc.recovery_fraction=0.85;
        cfg.hp.supply_temp_C=supplyT(j); cfg.storage.capacity_MWh=0;
        cfg.storage.charge_limit_MW=0; cfg.storage.discharge_limit_MW=0;
        o=dchr.simulate_system(cfg,input); m=dchr.compute_metrics(cfg,o);
        COP(i,j)=m.mean_cop; HPE(i,j)=m.hp_electric_MWh; Cov(i,j)=m.coverage_fraction; Save(i,j)=m.opex_saving_EUR;
    end
end

rows=[];
for i=1:numel(sourceT)
 for j=1:numel(supplyT)
  rows=[rows; table(sourceT(i),supplyT(j),COP(i,j),HPE(i,j),Cov(i,j),Save(i,j), ...
   'VariableNames',{'SourceTemp_C','SupplyTemp_C','MeanCOP','HPElectric_MWh','Coverage','OpexSaving_EUR'})]; %#ok<AGROW>
 end
end
writetable(rows,fullfile(resultsDir,'temperature_lift_sensitivity.csv'));

f=figure('Visible','off','Position',[100 100 1000 650]); imagesc(supplyT,sourceT,COP); axis xy; colorbar; xlabel('DH supply temperature [C]'); ylabel('DC source temperature [C]'); title('Mean COP: source temperature x DH supply temperature');
for i=1:numel(sourceT), for j=1:numel(supplyT), text(supplyT(j),sourceT(i),sprintf('%.2f',COP(i,j)),'HorizontalAlignment','center'); end, end
exportgraphics(f,fullfile(figDir,'06_cop_temperature_lift_map.png'),'Resolution',180); close(f);

storageSizes=[0 25 50 100 250 500 1000]';
Sm=zeros(numel(storageSizes),4);
for i=1:numel(storageSizes)
 cfg=base; cfg.dc.source_temp_C=45; cfg.dc.recovery_fraction=0.90; cfg.storage.capacity_MWh=storageSizes(i);
 if storageSizes(i)==0, cfg.storage.charge_limit_MW=0; cfg.storage.discharge_limit_MW=0; end
 o=dchr.simulate_system(cfg,input); m=dchr.compute_metrics(cfg,o);
 Sm(i,:)=[m.coverage_fraction,m.gas_heat_MWh,m.curtailed_hp_heat_MWh,m.opex_saving_EUR];
end
st=table(storageSizes,Sm(:,1),Sm(:,2),Sm(:,3),Sm(:,4),'VariableNames',{'Storage_MWh','Coverage','GasHeat_MWh','CurtailedHPHeat_MWh','OpexSaving_EUR'});
writetable(st,fullfile(resultsDir,'storage_sensitivity.csv'));

f=figure('Visible','off','Position',[100 100 1000 600]); yyaxis left; plot(storageSizes,100*st.Coverage,'o-','LineWidth',1.4); ylabel('Coverage [%]'); yyaxis right; plot(storageSizes,st.CurtailedHPHeat_MWh/1000,'s-','LineWidth',1.4); ylabel('Curtailed potential [GWh]'); xlabel('Storage capacity [MWh]'); grid on; title('Storage capacity: diminishing returns');
exportgraphics(f,fullfile(figDir,'07_storage_sensitivity.png'),'Resolution',180); close(f);
end
