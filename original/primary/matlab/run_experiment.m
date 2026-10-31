function summary = run_experiment()
%RUN_EXPERIMENT Reproducible scenario experiment for data-centre heat reuse.
rootDir = fileparts(fileparts(mfilename('fullpath')));
resultsDir = fullfile(rootDir,'results');
figDir = fullfile(resultsDir,'figures');
if ~exist(figDir,'dir'), mkdir(figDir); end

base = default_config();
input = dchr.make_inputs(base);

scenarios = struct( ...
 'name', {'Air25_NoStorage','Liquid35_NoStorage','Warm45_NoStorage','Warm45_Storage100'}, ...
 'source_C',{25,35,45,45}, ...
 'recovery',{0.70,0.85,0.90,0.90}, ...
 'storage_MWh',{0,0,0,100});

rows = cell(numel(scenarios),1);
allOut = cell(numel(scenarios),1);
allCfg = cell(numel(scenarios),1);
for i = 1:numel(scenarios)
    cfg = base;
    cfg.dc.source_temp_C = scenarios(i).source_C;
    cfg.dc.recovery_fraction = scenarios(i).recovery;
    cfg.storage.capacity_MWh = scenarios(i).storage_MWh;
    if cfg.storage.capacity_MWh == 0
        cfg.storage.charge_limit_MW = 0;
        cfg.storage.discharge_limit_MW = 0;
    end
    out = dchr.simulate_system(cfg,input);
    m = dchr.compute_metrics(cfg,out);
    allOut{i} = out; allCfg{i} = cfg;
    rows{i} = table(string(scenarios(i).name), scenarios(i).source_C, scenarios(i).recovery, ...
        scenarios(i).storage_MWh, m.mean_cop, m.heat_demand_MWh, m.reused_to_network_MWh, ...
        m.coverage_fraction, m.erf, m.ere, m.hp_electric_MWh, m.gas_heat_MWh, ...
        m.curtailed_hp_heat_MWh, m.opex_saving_EUR, m.CO2_saving_t, m.CO2_saving_fraction, ...
        'VariableNames', {'Scenario','SourceTemp_C','RecoveryFraction','Storage_MWh','MeanCOP', ...
        'HeatDemand_MWh','ReusedHeat_MWh','Coverage','ERF','ERE','HPElectric_MWh','GasHeat_MWh', ...
        'CurtailedHPHeat_MWh','OpexSaving_EUR','CO2Saving_t','CO2SavingFraction'});
end
summary = vertcat(rows{:});
writetable(summary,fullfile(resultsDir,'scenario_summary.csv'));
writetable(allOut{4},fullfile(resultsDir,'warm45_storage100_timeseries.csv'));

% Figure 1: annual KPI comparison
f = figure('Visible','off','Position',[100 100 1100 650]);
tiledlayout(2,2,'Padding','compact');
nexttile; bar(categorical(summary.Scenario),100*summary.Coverage); ylabel('Heat coverage [%]'); grid on; title('District heat covered by DC heat');
nexttile; bar(categorical(summary.Scenario),summary.MeanCOP); ylabel('COP [-]'); grid on; title('Heat-pump COP');
nexttile; bar(categorical(summary.Scenario),summary.GasHeat_MWh/1000); ylabel('Gas backup [GWh]'); grid on; title('Residual gas heat');
nexttile; bar(categorical(summary.Scenario),summary.CurtailedHPHeat_MWh/1000); ylabel('Curtailed heat [GWh]'); grid on; title('Unused heat-pump potential');
exportgraphics(f,fullfile(figDir,'01_scenario_comparison.png'),'Resolution',180); close(f);

% Figure 2: winter two-week operation, storage scenario
out = allOut{4}; n = 24*14; idx = 1:n;
f = figure('Visible','off','Position',[100 100 1200 700]);
tiledlayout(2,1,'Padding','compact');
nexttile; plot(out.Time(idx),out.Heat_Demand_MW(idx),'LineWidth',1.2); hold on; plot(out.Time(idx),out.HP_Heat_Used_MW(idx),'LineWidth',1.2); plot(out.Time(idx),out.Gas_Heat_MW(idx),'LineWidth',1.2); ylabel('Heat [MW]'); legend('Demand','Heat pump','Gas backup','Location','best'); grid on; title('Winter operation: first 14 days');
nexttile; yyaxis left; plot(out.Time(idx),out.Tout_C(idx),'LineWidth',1.0); ylabel('Outdoor T [C]'); yyaxis right; plot(out.Time(idx),out.Storage_E_MWh(idx),'LineWidth',1.2); ylabel('Storage [MWh]'); grid on; xlabel('Time');
exportgraphics(f,fullfile(figDir,'02_winter_operation.png'),'Resolution',180); close(f);

% Figure 3: heat-demand duration curve
f = figure('Visible','off','Position',[100 100 1000 600]);
[dSort,~] = sort(out.Heat_Demand_MW,'descend'); [gSort,~] = sort(out.Gas_Heat_MW,'descend');
plot((1:numel(dSort))/numel(dSort)*100,dSort,'LineWidth',1.4); hold on; plot((1:numel(gSort))/numel(gSort)*100,gSort,'LineWidth',1.4); grid on; xlabel('Hours exceeded [% of year]'); ylabel('Heat [MW]'); legend('Demand','Residual gas','Location','best'); title('Annual load-duration curve');
exportgraphics(f,fullfile(figDir,'03_load_duration.png'),'Resolution',180); close(f);

% Figure 4: sensitivity of COP to source temperature
Ts = (20:1:50)'; qDummy = ones(size(Ts)); cops = zeros(size(Ts));
for k=1:numel(Ts)
    c = base; c.dc.source_temp_C = Ts(k); h = dchr.heat_pump_capability(qDummy(k),Ts(k),c); cops(k)=h.cop;
end
f = figure('Visible','off','Position',[100 100 900 550]);
plot(Ts,cops,'LineWidth',1.6); grid on; xlabel('Waste-heat source temperature [C]'); ylabel('COP [-]'); title(sprintf('COP sensitivity, district supply = %.0f C',base.hp.supply_temp_C));
exportgraphics(f,fullfile(figDir,'04_cop_sensitivity.png'),'Resolution',180); close(f);

% Figure 5: monthly energy balance for best scenario
monthNum = month(out.Time); monthHeat = accumarray(monthNum,out.Heat_Demand_MW*base.sim.dt_h,[12 1]); monthReuse = accumarray(monthNum,(out.Heat_Demand_MW-out.Gas_Heat_MW)*base.sim.dt_h,[12 1]); monthGas = accumarray(monthNum,out.Gas_Heat_MW*base.sim.dt_h,[12 1]);
f = figure('Visible','off','Position',[100 100 1000 580]);
bar(1:12,[monthReuse monthGas],'stacked'); hold on; plot(1:12,monthHeat,'k.-','LineWidth',1.2,'MarkerSize',16); grid on; xlabel('Month'); ylabel('Energy [MWh]'); legend('DC heat incl. storage','Gas backup','Demand','Location','best'); title('Monthly district-heating energy balance');
exportgraphics(f,fullfile(figDir,'05_monthly_energy_balance.png'),'Resolution',180); close(f);

save(fullfile(resultsDir,'experiment_workspace.mat'),'summary','scenarios','allCfg');
disp(summary);
end
