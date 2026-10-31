function results = run_heat_pump_contract_v14(referenceFile, outputDir)
%RUN_HEAT_PUMP_CONTRACT_V14 Python analytical reference vs MATLAB bisection.
% Paths must designate a new evidence directory. No baseline output is touched.
assert(isfile(referenceFile),'DCHR:v14:MissingReference','Reference CSV does not exist.');
if ~isfolder(outputDir), mkdir(outputDir); end
artifacts={'matlab_heat_pump_vectors_v14.csv','matlab_heat_pump_contract_v14.csv', ...
    'matlab_heat_pump_contract_v14.json'};
for k=1:numel(artifacts)
    assert(~isfile(fullfile(outputDir,artifacts{k})),'DCHR:v14:EvidenceExists', ...
        'Refusing to replace evidence: %s',artifacts{k});
end
v=readtable(referenceFile,'TextType','string');
assert(height(v)>0,'Reference vectors must not be empty.');
cfg=default_config_v2();
actual=cell(height(v),1);
for k=1:height(v)
    c=cfg; c.model.hp_backend="carnot";
    c.hp.max_heat_output_MW=v.capacity_MW(k);
    c.hp.carnot_efficiency=v.carnot_efficiency(k);
    c.hp.cop_min=v.cop_min(k); c.hp.cop_max=v.cop_max(k);
    c.hp.part_load_penalty=v.part_load_penalty(k);
    h=dchr.components.heat_pump_step_v14(v.q_source_MW(k),v.source_C(k), ...
        v.sink_C(k),v.request_MW(k),c);
    actual{k}=h;
end
a=struct2table(vertcat(actual{:}));
writetable(a,fullfile(outputDir,artifacts{1}));
names=strings(0,1); passed=false(0,1); notes=strings(0,1);
fields={'cop_carnot','cop_raw','cop_nominal','cop_operating', ...
    'heat_output_MW','electric_MW','source_used_MW'};
maxResidual=0;
for k=1:numel(fields)
    field=fields{k}; expected=v.(['expected_' field]); observed=a.(field);
    matchingNaN=isnan(expected) & isnan(observed);
    finite=isfinite(expected) & isfinite(observed);
    residual=abs(observed(finite)-expected(finite));
    limit=1e-9+1e-11*abs(expected(finite));
    if ~isempty(residual), maxResidual=max(maxResidual,max(residual)); end
    record("python_analytic_match_"+string(field), ...
        all(matchingNaN | finite) && all(residual<=limit), ...
        sprintf('%d vectors; max absolute residual %.12g',height(v),max([0;residual])));
end
expectedOn=ismember(lower(string(v.expected_available)),["true","1"]);
record('python_availability_match',all(a.available==expectedOn), ...
    'Includes declared off and unavailable operating points.');
on=a.available; off=~on;
record('first_law',all(abs(a.heat_output_MW-a.electric_MW-a.source_used_MW)<1e-9), ...
    'Qhot = Qevap + compressor work.');
record('source_and_output_limits',all(a.source_used_MW<=v.q_source_MW+1e-9) && ...
    all(a.heat_output_MW<=min(v.request_MW,v.capacity_MW)+1e-9) && ...
    all(a.source_used_MW>=0) && all(a.electric_MW>=0), ...
    'Nonnegative powers; available source, request and rated capacity respected.');
record('carnot_and_cop_cutoff',all(a.cop_operating(on)<=a.cop_carnot(on)+1e-10) && ...
    all(a.cop_operating(on)>=v.cop_min(on)-1e-10), ...
    'Operating COP never raised to meet a floor.');
record('off_flows_and_undefined_cop',all(a.heat_output_MW(off)==0) && ...
    all(a.electric_MW(off)==0) && all(a.source_used_MW(off)==0) && ...
    all(isnan(a.cop_operating(off))), 'COP is undefined when compressor work is zero.');

legacy=dchr.components.heat_pump(5,-100,80,cfg);
new=dchr.components.heat_pump_step_v14(5,-100,80,12,cfg);
record('legacy_second_law_counterexample_confirmed', ...
    legacy.cop_nominal>(80+273.15)/180 && ~new.available && new.heat_output_MW==0, ...
    sprintf('Legacy COP %.6f; reservoir Carnot %.6f; new status %s', ...
    legacy.cop_nominal,new.cop_carnot,new.status));
c=cfg; c.hp.part_load_penalty=0;
h=dchr.components.heat_pump_step_v14(5,35,70,12,c);
expectedCop=0.45*343.15/35;
record('hand_derived_constant_cop_source_limit',abs(h.cop_operating-expectedCop)<1e-12 && ...
    abs(h.heat_output_MW-5*expectedCop/(expectedCop-1))<1e-9, ...
    'Independent first-law rearrangement with penalty zero.');
h=dchr.components.heat_pump_step_v14(5,32,70,12,cfg);
record('hand_derived_part_load_source_limit',abs(h.heat_output_MW-6.712114501705883)<1e-9 && ...
    abs(h.source_used_MW-5)<1e-9,'Independent quadratic-root example.');
h=dchr.components.heat_pump_step_v14(5,69.75,70,12,c);
record('sub_kelvin_lift_not_clamped',h.lift_K==0.25 && ...
    abs(h.cop_raw-0.45*343.15/0.25)<1e-9,'No synthetic 1 K temperature difference.');

reject('reject_zero_lift',@()dchr.components.heat_pump_step_v14(5,70,70,12,cfg),'DCHR:v14:TemperatureLift');
reject('reject_negative_lift',@()dchr.components.heat_pump_step_v14(5,80,70,12,cfg),'DCHR:v14:TemperatureLift');
reject('reject_absolute_zero',@()dchr.components.heat_pump_step_v14(5,-273.15,70,12,cfg),'DCHR:v14:InvalidInput');
reject('reject_negative_source',@()dchr.components.heat_pump_step_v14(-1,35,70,12,cfg),'DCHR:v14:InvalidInput');
reject('reject_negative_request',@()dchr.components.heat_pump_step_v14(5,35,70,-1,cfg),'DCHR:v14:InvalidInput');
reject('reject_nan',@()dchr.components.heat_pump_step_v14(NaN,35,70,12,cfg),'DCHR:v14:InvalidInput');
reject('reject_infinite_temperature',@()dchr.components.heat_pump_step_v14(5,35,Inf,12,cfg),'DCHR:v14:InvalidInput');
reject('reject_complex',@()dchr.components.heat_pump_step_v14(5+1i,35,70,12,cfg),'DCHR:v14:InvalidInput');
reject('reject_vector',@()dchr.components.heat_pump_step_v14([5;6],35,70,12,cfg),'DCHR:v14:InvalidInput');
c=cfg; c.hp.carnot_efficiency=1.1;
reject('reject_efficiency_above_one',@()dchr.components.heat_pump_step_v14(5,35,70,12,c),'DCHR:v14:InvalidInput');
c=cfg; c.hp.part_load_penalty=1;
reject('reject_penalty_one',@()dchr.components.heat_pump_step_v14(5,35,70,12,c),'DCHR:v14:InvalidInput');
c=cfg; c.hp.cop_max=1.5;
reject('reject_reversed_cop_bounds',@()dchr.components.heat_pump_step_v14(5,35,70,12,c),'DCHR:v14:InvalidInput');
c=cfg; c.model.hp_backend="unknown";
reject('reject_unknown_backend',@()dchr.components.heat_pump_step_v14(5,35,70,12,c),'DCHR:v14:Backend');
c=cfg; c.model.hp_backend="lift_polynomial"; c.hp.poly_c0=20; c.hp.poly_c1=0; c.hp.poly_c2=0;
reject('reject_polynomial_above_carnot',@()dchr.components.heat_pump_step_v14(5,35,70,12,c),'DCHR:v14:PolynomialCarnot');
c.hp.poly_c0=4;
h=dchr.components.heat_pump_step_v14(5,35,70,12,c);
record('polynomial_valid_prediction',h.available && h.cop_raw==4 && ...
    h.cop_operating<=4 && h.source_used_MW<=5+1e-9,'Polynomial coefficients remain scenario inputs.');

results=table(names,passed,notes,'VariableNames',{'Test','Passed','Observation'});
writetable(results,fullfile(outputDir,artifacts{2}));
timestamp=datetime('now','TimeZone','UTC','Format',"yyyy-MM-dd'T'HH:mm:ssXXX");
summary=struct('version','0.14','timestamp_utc',char(timestamp), ...
    'category','matlab_runtime_vs_independent_python_analytical_component', ...
    'matlab_version',version,'reference_file',char(referenceFile),'vectors',height(v), ...
    'total',height(results),'passed',sum(passed),'failed',sum(~passed), ...
    'max_absolute_residual',maxResidual,'primary_paper_replication',false, ...
    'annual_dispatch_integrated',false,'simulink_executed',false,'stateflow_executed',false, ...
    'results',table2struct(results));
fid=fopen(fullfile(outputDir,artifacts{3}),'w');
assert(fid>0,'Unable to write evidence.');
fileCleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(summary,PrettyPrint=true));
disp(results);
assert(all(passed),'DCHR:v14:ContractFailure','One or more heat-pump checks failed.');

    function record(name,ok,note)
        names(end+1,1)=string(name); passed(end+1,1)=logical(ok); notes(end+1,1)=string(note);
    end
    function reject(name,callback,identifier)
        got="NO_ERROR";
        try
            callback();
        catch caught
            got=string(caught.identifier);
        end
        record(name,got==string(identifier),"Expected "+string(identifier)+"; got "+got);
    end
end
