function summary=run_experiment_v2()
%RUN_EXPERIMENT_V2 Architecture comparison with component-oriented model.
rootDir=fileparts(fileparts(mfilename('fullpath'))); resultsDir=fullfile(rootDir,'results');
figDir=fullfile(resultsDir,'figures'); if ~exist(figDir,'dir'),mkdir(figDir);end
base=default_config_v2(); input=dchr.make_inputs(base);
S=struct( ...
'name',{'Air25_Fixed70','Liquid35_Weather','Warm45_Weather','Warm45_Storage100','Liquid35_LowTempDH'}, ...
'source',{25,35,45,45,35},'recovery',{0.70,0.85,0.90,0.90,0.85}, ...
'storage',{0,0,0,100,100},'tempMode',{'fixed','weather','weather','weather','weather'}, ...
'lowTemp',{false,false,false,false,true});
rows=cell(numel(S),1); O=cell(numel(S),1); C=cell(numel(S),1);
for i=1:numel(S)
 cfg=base; cfg.dc.source_temp_C=S(i).source; cfg.dc.recovery_fraction=S(i).recovery;
 cfg.storage.capacity_MWh=S(i).storage; cfg.model.dh_temperature=string(S(i).tempMode);
 if S(i).storage==0, cfg.storage.charge_limit_MW=0; cfg.storage.discharge_limit_MW=0; end
 if S(i).lowTemp
   cfg.dh.supply_min_C=45; cfg.dh.supply_max_C=65; cfg.dh.return_min_C=30; cfg.dh.return_max_C=40;
 end
 o=dchr.simulate_system_v2(cfg,input); m=dchr.compute_metrics_v2(cfg,o); O{i}=o; C{i}=cfg;
 rows{i}=table(string(S(i).name),S(i).source,S(i).recovery,S(i).storage,m.mean_cop,m.mean_lift_K, ...
 m.heat_demand_MWh,m.reused_to_network_MWh,m.coverage_fraction,m.erf,m.ere_system,m.hp_electric_MWh, ...
 m.gas_heat_MWh,m.curtailed_hp_heat_MWh,m.exergy_delivered_MWh,m.opex_saving_EUR,m.CO2_saving_t, ...
 m.screening_LCOH_EUR_per_MWh,m.simple_payback_y, ...
 'VariableNames',{'Scenario','SourceTemp_C','RecoveryFraction','Storage_MWh','MeanCOP','MeanLift_K', ...
 'HeatDemand_MWh','ReusedHeat_MWh','Coverage','ERF','ERE_System','HPElectric_MWh','GasHeat_MWh', ...
 'CurtailedHPHeat_MWh','UsefulExergy_MWh','OpexSaving_EUR','CO2Saving_t','ScreeningLCOH_EUR_MWh','SimplePayback_y'});
end
summary=vertcat(rows{:}); writetable(summary,fullfile(resultsDir,'scenario_summary_v2.csv'));
writetable(O{end},fullfile(resultsDir,'best_scenario_v2_timeseries.csv'));

f=figure('Visible','off','Position',[100 100 1200 720]); tiledlayout(2,2,'Padding','compact');
nexttile; bar(categorical(summary.Scenario),100*summary.Coverage); ylabel('Coverage [%]'); grid on; title('Annual DH coverage');
nexttile; bar(categorical(summary.Scenario),summary.MeanCOP); ylabel('COP [-]'); grid on; title('Heat-pump COP');
nexttile; bar(categorical(summary.Scenario),summary.HPElectric_MWh/1000); ylabel('Electricity [GWh]'); grid on; title('Heat-pump electricity');
nexttile; bar(categorical(summary.Scenario),summary.GasHeat_MWh/1000); ylabel('Gas heat [GWh]'); grid on; title('Residual backup');
exportgraphics(f,fullfile(figDir,'08_scenario_comparison_v2.png'),'Resolution',200); close(f);

f=figure('Visible','off','Position',[100 100 1000 600]);
scatter(summary.MeanLift_K,summary.MeanCOP,100,100*summary.Coverage,'filled'); grid on;
xlabel('Mean temperature lift [K]'); ylabel('Mean COP [-]'); cb=colorbar; cb.Label.String='Coverage [%]';
for i=1:height(summary), text(summary.MeanLift_K(i)+0.5,summary.MeanCOP(i),summary.Scenario(i),'Interpreter','none'); end
title('Temperature lift is the central coupling variable');
exportgraphics(f,fullfile(figDir,'09_lift_cop_coverage_v2.png'),'Resolution',200); close(f);

out=O{end}; idx=1:24*14; f=figure('Visible','off','Position',[100 100 1200 720]); tiledlayout(3,1,'Padding','compact');
nexttile; plot(out.Time(idx),out.Heat_Demand_MW(idx),'LineWidth',1.2); hold on; plot(out.Time(idx),out.HP_Heat_Used_MW(idx),'LineWidth',1.2); plot(out.Time(idx),out.Gas_Heat_MW(idx),'LineWidth',1.2); grid on; ylabel('MW'); legend('Demand','HP used','Gas');
nexttile; plot(out.Time(idx),out.DH_Supply_C(idx),'LineWidth',1.2); hold on; plot(out.Time(idx),out.Tout_C(idx),'LineWidth',1.0); grid on; ylabel('Temperature [C]'); legend('DH supply','Outdoor');
nexttile; plot(out.Time(idx),out.Storage_E_MWh(idx),'LineWidth',1.2); grid on; ylabel('Storage [MWh]'); xlabel('Time');
exportgraphics(f,fullfile(figDir,'10_best_scenario_operation_v2.png'),'Resolution',200); close(f);
save(fullfile(resultsDir,'experiment_workspace_v2.mat'),'summary','S','C'); disp(summary);
end
