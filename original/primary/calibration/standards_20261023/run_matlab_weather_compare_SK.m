% Porovnanie: modelova syntetika vs NASA POWER Bratislava 2025.
here=fileparts(mfilename('fullpath'));
proj=fileparts(fileparts(here));
addpath(fullfile(proj,'matlab'));
weather=readtable(fullfile(here,'official_datasets','weather_2025_BRATISLAVA_NASA_POWER_hourly_UTC.csv'));
assert(height(weather)==8760 && all(isfinite(weather.T2M_C)));
cfg=default_config();
cfg.sim.start=datetime(2025,1,1);
cfg.sim.hours=8760;
x=dchr.make_inputs(cfg);
xr=x;
xr.outdoor_temp_C=weather.T2M_C;
inputs={x,xr};
names={'SYNTHETIC','NASA_POWER_2025'};
outDir=fullfile(here,'experiments','real_vs_synthetic_v01');
rows=cell(2,1);
for j=1:2
  u=inputs{j};c=cfg;c.dc.pue=1.36;
  u.dc_total_power_MW=u.it_power_MW*c.dc.pue;
  out=dchr.simulate_system(c,u);
  m=dchr.compute_metrics(c,out);
  reusedSource=sum(max(0,out.HP_Heat_Used_MW-out.HP_Electric_MW));
  erfs=reusedSource/m.dc_total_energy_MWh;
  rows{j}=table(string(names{j}),mean(u.outdoor_temp_C),m.heat_demand_MWh,m.hp_electric_MWh,m.gas_heat_MWh,m.dc_total_energy_MWh,erfs,m.erf,'VariableNames',{'Weather','MeanOutdoor_C','HeatDemand_MWh','HPElectric_MWh','GasHeat_MWh','DCEnergy_MWh','ERF_source_proxy','ERF_original_energy_included'});
  fprintf('SAVED_CHECK %s HEAT=%.2f ERFproxy=%.5f\n',names{j},m.heat_demand_MWh,erfs);
end
summary=vertcat(rows{:});
writetable(summary,fullfile(outDir,'matlab_weather_compare.csv'));
assert(height(summary)==2);
