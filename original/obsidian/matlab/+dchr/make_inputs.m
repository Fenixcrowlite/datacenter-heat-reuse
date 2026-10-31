function input = make_inputs(cfg)
%MAKE_INPUTS Generate deterministic hourly weather and IT-load profiles.
% This is a replaceable input module. Real Meteostat/ENTSO-E/DC telemetry can
% later be dropped in without changing the thermal core.

rng(cfg.sim.random_seed);
N = cfg.sim.hours;
dt = hours(cfg.sim.dt_h);
input.time = cfg.sim.start + (0:N-1)' .* dt;

hourOfDay = hour(input.time);
dayOfYear = day(input.time,'dayofyear');
weekPhase = (0:N-1)'/(24*7);

season = cfg.weather.seasonal_amplitude_C .* ...
    cos(2*pi*(dayOfYear - cfg.weather.warmest_day)/365);
daily = cfg.weather.daily_amplitude_C .* cos(2*pi*(hourOfDay - 15)/24);
noise = cfg.weather.noise_sigma_C .* randn(N,1);
input.outdoor_temp_C = cfg.weather.annual_mean_C + season + daily + noise;

util = cfg.dc.util_mean ...
    + cfg.dc.util_daily_amp .* sin(2*pi*(hourOfDay - 9)/24) ...
    + cfg.dc.util_weekly_amp .* sin(2*pi*weekPhase) ...
    + cfg.dc.util_noise_sigma .* randn(N,1);
util = min(cfg.dc.util_max, max(cfg.dc.util_min, util));

input.it_utilization = util;
input.it_power_MW = cfg.dc.it_capacity_MW .* util;
input.dc_total_power_MW = cfg.dc.pue .* input.it_power_MW;
end
