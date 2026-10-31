% Porovnanie mesacnych profilov teploty a odberu tepla.
here=fileparts(mfilename('fullpath'));
proj=fileparts(fileparts(here));addpath(fullfile(proj,'matlab'));
w=readtable(fullfile(here,'official_datasets','weather_2025_BRATISLAVA_NASA_POWER_hourly_UTC.csv'));
cfg=default_config();cfg.sim.start=datetime(2025,1,1);cfg.sim.hours=8760;
x=dchr.make_inputs(cfg); months=month(x.time);
monthNo=(1:12)';
sTemp=zeros(12,1);rTemp=sTemp;sHeat=sTemp;rHeat=sTemp;
for k=1:12
 idx=(months==k);
 sTemp(k)=mean(x.outdoor_temp_C(idx));
 rTemp(k)=mean(w.T2M_C(idx));
 sHeat(k)=sum(dchr.heat_demand(x.outdoor_temp_C(idx),cfg));
 rHeat(k)=sum(dchr.heat_demand(w.T2M_C(idx),cfg));
end
summary=table(monthNo,sTemp,rTemp,sHeat,rHeat,'VariableNames',{'Month','T_synthetic_C','T_NASA_2025_C','Heat_synthetic_MWh','Heat_NASA_2025_MWh'});
out=fullfile(here,'experiments','real_vs_synthetic_v01');
writetable(summary,fullfile(out,'monthly_temperature_heat_load_SK.csv'));
figure('Visible','off','Color','w','Position',[80 80 1100 700]);
tiledlayout(2,1);
nexttile;plot(monthNo,sTemp,'o-',monthNo,rTemp,'s-','LineWidth',1.5);grid on;ylabel('Teplota [°C]');legend('Syntetika','NASA POWER 2025','Location','best');
title('Kalibracia vonkajsej teploty');
nexttile;plot(monthNo,sHeat,'o-',monthNo,rHeat,'s-','LineWidth',1.5);grid on;xlabel('Mesiac');ylabel('Teplo [MWh]');legend('Syntetika','NASA POWER 2025','Location','best');
title('Vplyv pocasia na rocny odber tepla');
exportgraphics(gcf,fullfile(out,'monthly_weather_vs_synthetic_SK.png'),'Resolution',180);close(gcf);
assert(abs(sum(rHeat)-56793.6952887537)<0.001);
disp('MONTHLY_REAL_DATA_CHART_VERIFIED');
