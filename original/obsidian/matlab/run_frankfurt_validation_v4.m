clear; clc;
root = fileparts(mfilename('fullpath'));
addpath(root);
outdir = fullfile(fileparts(root),'results');
figdir = fullfile(outdir,'figures');
if ~exist(figdir,'dir'), mkdir(figdir); end

% Frankfurt literature-validation branch.
cfg = default_config_v2();
cfg.meta.name = "Frankfurt literature validation";
cfg.meta.version = "0.4.0-validation";
cfg.model.hp_backend = "carnot";
cfg.model.dh_temperature = "fixed";
cfg.hp.supply_temp_C = 70.0;          % scenario assumption
cfg.hp.carnot_efficiency = 0.50;      % scenario assumption
cfg.hp.max_heat_output_MW = 37.0;     % literature anchor
cfg.hx.max_heat_MW = 40.0;
cfg.hx.effectiveness = 0.99;
cfg.hx.approach_K = 0.0;
cfg.dc.it_capacity_MW = 30.0;
cfg.dc.source_temp_C = 30.0;          % scenario assumption
cfg.storage.capacity_MWh = 300.0;     % scenario assumption
cfg.storage.charge_limit_MW = 37.0;
cfg.storage.discharge_limit_MW = 37.0;
cfg.storage.eta_charge = 0.98;
cfg.storage.eta_discharge = 0.98;
cfg.storage.loss_fraction_per_h = 0.005/24;

% Deterministic synthetic inputs; normalize DH demand to 144 GWh/a.
input = dchr.make_inputs(cfg);
q0 = dchr.heat_demand(input.outdoor_temp_C,cfg);
scale = 144000 / (sum(q0)*cfg.sim.dt_h);
cfg.dh.space_heat_design_MW = cfg.dh.space_heat_design_MW * scale;
cfg.dh.base_hot_water_MW = cfg.dh.base_hot_water_MW * scale;

% Calibrate recovery fraction only to the published 97.5% heat-coverage target.
target = 0.975;
lo = 0.20; hi = 1.00;
for it = 1:40
    mid = 0.5*(lo+hi);
    cfg.dc.recovery_fraction = mid;
    out = dchr.simulate_system_v2(cfg,input);
    m = dchr.compute_metrics_v2(cfg,out);
    if m.coverage_fraction < target, lo = mid; else, hi = mid; end
end
cfg.dc.recovery_fraction = 0.5*(lo+hi);
out = dchr.simulate_system_v2(cfg,input);
m = dchr.compute_metrics_v2(cfg,out);

summary = table(m.heat_demand_MWh,m.coverage_fraction,m.mean_cop,m.hp_heat_MWh, ...
    m.hp_electric_MWh,m.gas_heat_MWh,m.scenario_gas_fuel_MWh,m.scenario_opex_EUR, ...
    m.scenario_CO2_t,cfg.dc.recovery_fraction,cfg.hp.max_heat_output_MW,cfg.storage.capacity_MWh, ...
    'VariableNames',{'Demand_MWh','Coverage','Mean_COP','HP_Heat_MWh','HP_Electric_MWh', ...
    'Gas_Heat_MWh','Gas_Fuel_MWh','Scenario_OPEX_EUR','Scenario_CO2_t','Calibrated_RecoveryFraction', ...
    'HP_Rated_MWth','Storage_MWh'});
writetable(summary,fullfile(outdir,'frankfurt_validation_v4.csv'));
writetable(out,fullfile(outdir,'frankfurt_validation_v4_timeseries.csv'));
save(fullfile(outdir,'frankfurt_validation_v4.mat'),'cfg','input','out','m','summary');

% Sensitivity: source temperature x storage capacity.
Ts = [20 30 40 50]; Es = [0 100 300 600];
nr = numel(Ts)*numel(Es);
Tsource_C=zeros(nr,1); Storage_MWh=zeros(nr,1); Coverage=zeros(nr,1); Mean_COP=zeros(nr,1);
HP_Electric_MWh=zeros(nr,1); Gas_Heat_MWh=zeros(nr,1); CO2_t=zeros(nr,1); OPEX_EUR=zeros(nr,1);
row=0;
for i=1:numel(Ts)
    for j=1:numel(Es)
        row=row+1;
        c=cfg; c.dc.source_temp_C=Ts(i); c.storage.capacity_MWh=Es(j);
        c.storage.charge_limit_MW=max(37,Es(j)); c.storage.discharge_limit_MW=max(37,Es(j));
        o=dchr.simulate_system_v2(c,input); mm=dchr.compute_metrics_v2(c,o);
        Tsource_C(row)=Ts(i); Storage_MWh(row)=Es(j); Coverage(row)=mm.coverage_fraction;
        Mean_COP(row)=mm.mean_cop; HP_Electric_MWh(row)=mm.hp_electric_MWh;
        Gas_Heat_MWh(row)=mm.gas_heat_MWh; CO2_t(row)=mm.scenario_CO2_t; OPEX_EUR(row)=mm.scenario_opex_EUR;
    end
end
R=table(Tsource_C,Storage_MWh,Coverage,Mean_COP,HP_Electric_MWh,Gas_Heat_MWh,CO2_t,OPEX_EUR);
writetable(R,fullfile(outdir,'frankfurt_sensitivity_v4.csv'));

f=figure('Visible','off','Color','w','Position',[100 100 1000 520]); hold on;
for j=1:numel(Es)
    rr=R(R.Storage_MWh==Es(j),:);
    plot(rr.Tsource_C,100*rr.Coverage,'-o','LineWidth',1.8,'DisplayName',sprintf('%g MWh',Es(j)));
end
grid on; xlabel('Source temperature [degC]'); ylabel('DC heat coverage [%]');
title('Frankfurt validation: source temperature x storage'); legend('Location','best');
exportgraphics(f,fullfile(figdir,'15_frankfurt_validation_sensitivity_v4.png'),'Resolution',180); close(f);

fprintf('FRANKFURT VALIDATION v0.4\n');
fprintf('Demand: %.3f GWh/a\n',m.heat_demand_MWh/1000);
fprintf('Coverage: %.4f %% (target 97.5%%)\n',100*m.coverage_fraction);
fprintf('Mean COP: %.3f\n',m.mean_cop);
fprintf('HP electricity: %.3f GWh/a\n',m.hp_electric_MWh/1000);
fprintf('Gas heat: %.3f GWh/a\n',m.gas_heat_MWh/1000);
fprintf('Calibrated recovery fraction: %.5f\n',cfg.dc.recovery_fraction);
