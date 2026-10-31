function summary = run_uncertainty_v3(N)
%RUN_UNCERTAINTY_V3 Scenario uncertainty around the warm-liquid architecture.
% These ranges are engineering assumptions, not measured distributions.
if nargin < 1, N = 300; end
rootDir = fileparts(fileparts(mfilename('fullpath')));
resultsDir = fullfile(rootDir,'results');
figDir = fullfile(resultsDir,'figures');
if ~exist(figDir,'dir'), mkdir(figDir); end
base = default_config_v2();
base.dc.source_temp_C = 45;
base.dc.recovery_fraction = 0.90;
base.storage.capacity_MWh = 100;
input = dchr.make_inputs(base);
rng(20261004);
A = zeros(N,11);
for i = 1:N
    cfg = base;
    cfg.dc.source_temp_C = min(50,max(38,45 + 3*randn));
    cfg.dc.recovery_fraction = 0.82 + 0.13*rand;
    cfg.hp.carnot_efficiency = 0.40 + 0.10*rand;
    cfg.econ.electricity_EUR_per_MWh = 70 + 70*rand;
    cfg.econ.gas_EUR_per_MWh_fuel = 40 + 40*rand;
    cfg.econ.grid_tCO2_per_MWh = 0.08 + 0.22*rand;
    out = dchr.simulate_system_v2(cfg,input);
    m = dchr.compute_metrics_v2(cfg,out);
    A(i,:) = [cfg.dc.source_temp_C,cfg.dc.recovery_fraction,cfg.hp.carnot_efficiency, ...
        cfg.econ.electricity_EUR_per_MWh,cfg.econ.gas_EUR_per_MWh_fuel, ...
        m.mean_cop,m.coverage_fraction,m.opex_saving_EUR,m.CO2_saving_t, ...
        m.screening_LCOH_EUR_per_MWh,m.simple_payback_y];
end
T = array2table(A,'VariableNames',{'SourceTemp_C','RecoveryFraction','CarnotEfficiency', ...
    'Electricity_EUR_MWh','Gas_EUR_MWhFuel','MeanCOP','Coverage','OpexSaving_EUR', ...
    'CO2Saving_t','ScreeningLCOH_EUR_MWh','SimplePayback_y'});
writetable(T,fullfile(resultsDir,'uncertainty_v3.csv'));
metrics = {'MeanCOP','Coverage','OpexSaving_EUR','CO2Saving_t','ScreeningLCOH_EUR_MWh','SimplePayback_y'};
rows = cell(numel(metrics),1);
for j = 1:numel(metrics)
    x = T.(metrics{j});
    rows{j} = table(string(metrics{j}),qv(x,0.05),qv(x,0.50),qv(x,0.95),mean(x), ...
        'VariableNames',{'Metric','P05','Median','P95','Mean'});
end
summary = vertcat(rows{:});
writetable(summary,fullfile(resultsDir,'uncertainty_summary_v3.csv'));

f = figure('Visible','off','Position',[100 100 1200 760]);
tiledlayout(2,2,'Padding','compact');
nexttile; histogram(T.MeanCOP,24); xlabel('Mean COP'); ylabel('Runs'); grid on; title('COP uncertainty');
nexttile; histogram(100*T.Coverage,24); xlabel('Coverage [%]'); ylabel('Runs'); grid on; title('Heat coverage uncertainty');
nexttile; scatter(T.Electricity_EUR_MWh,T.OpexSaving_EUR/1e6,18,T.SourceTemp_C,'filled'); grid on;
xlabel('Electricity [EUR/MWh]'); ylabel('OPEX saving [MEUR/a]'); cb=colorbar; cb.Label.String='Source temp [C]';
nexttile; scatter(T.RecoveryFraction,T.SimplePayback_y,18,T.CarnotEfficiency,'filled'); grid on;
xlabel('Recovery fraction'); ylabel('Simple payback [y]'); cb=colorbar; cb.Label.String='Carnot efficiency';
exportgraphics(f,fullfile(figDir,'14_uncertainty_v3.png'),'Resolution',220); close(f);
disp(summary);
end

function y = qv(x,p)
x = sort(x(:)); n = numel(x); pos = 1 + (n-1)*p;
lo = floor(pos); hi = ceil(pos);
if lo == hi, y = x(lo); else, y = x(lo) + (pos-lo)*(x(hi)-x(lo)); end
end
