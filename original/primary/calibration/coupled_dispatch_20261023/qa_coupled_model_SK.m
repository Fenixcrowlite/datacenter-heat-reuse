% Oddelene regresne testy spojeneho modelu, ziadne modifikacie povodnych SLX.
here=fileparts(mfilename('fullpath'));root=fileparts(fileparts(here));addpath(fullfile(root,'matlab'));addpath(here);
cfg=dchr_config_real_2025_SK();cfg.sim.hours=168;
x=dchr.make_inputs(cfg);
[o1,m1]=simulate_coupled_pool_SK(cfg,x,'poolEnabled',true,'poolMode',"DIRECT",'source_C',35,'thermalStep_s',300);
[o2,m2]=simulate_coupled_pool_SK(cfg,x,'poolEnabled',true,'poolMode',"DIRECT",'source_C',35,'thermalStep_s',60);
assert(abs(m1.pool_energy_residual_MWh)<1e-6);
assert(abs(m2.pool_energy_residual_MWh)<1e-6);
assert(abs(m1.pool_heat_MWh-m2.pool_heat_MWh)<0.15);
assert(abs(m1.pool_max_C-m2.pool_max_C)<0.15);
assert(m1.pool_max_C<=27.8 && m2.pool_max_C<=27.8);
assert(all(o1.Pool_Source_Reserved_MW+1e-10>=o1.Pool_Source_MW));
assert(all(o1.Pool_Source_Reserved_MW+o1.DH_Source_MW<=o1.DC_Source_Available_MW+1e-7));
% Pri nulovom odpade DC bazen nesmie cerpat "vymyslene" teplo.
zero=x;zero.it_power_MW=zeros(size(zero.it_power_MW));zero.dc_total_power_MW=zero.it_power_MW;
[o3,m3]=simulate_coupled_pool_SK(cfg,zero,'poolEnabled',true,'source_C',35);
assert(m3.pool_heat_MWh<1e-10 && m3.total_source_used_MWh<1e-8);
assert(all(o3.Gas_Q_MW>=0));
% Ochranna blokacia teploty nie je volitelna nad publikovane maximum.
blocked=false;
try
 simulate_coupled_pool_SK(cfg,x,'poolMax_C',28.1);
catch
 blocked=true;
end
assert(blocked,'Overtemperature config must be rejected');
fprintf('COUPLED_GATES_PASS n=168h dt300=%0.4fMWh dt60=%0.4fMWh maxT=%0.4fC\n',...
 m1.pool_heat_MWh,m2.pool_heat_MWh,m1.pool_max_C);
