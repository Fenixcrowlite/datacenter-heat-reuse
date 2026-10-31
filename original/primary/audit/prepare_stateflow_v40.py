"""Additive v40 HP repair and saved-model test harness; never edit v38/v39."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'matlab/simulink'

def write(path, text):
    assert not path.exists(), path
    path.write_text(text, encoding='utf-8')

for name in ('build_dispatch_stateflow', 'dchr_segment_plan', 'dchr_stateflow_hp',
             'stateflow_allocate', 'stateflow_choose_mode', 'stateflow_collect',
             'stateflow_contract_gate', 'stateflow_clock_add', 'stateflow_supervisor_guard',
             'run_stateflow_faults', 'export_stateflow_resolution'):
    text = (HERE / (name + '_v38.m')).read_text().replace('v38', 'v40').replace('0.38', '0.40')
    write(HERE / (name + '_v40.m'), text)

component = (ROOT / 'matlab/+dchr/+components/heat_pump_step_v38.m').read_text().replace('v38', 'v40').replace('V38', 'V40')
start = component.index('if evaporator(upper,cap,nominal,penalty) > q_source_MW')
end = component.index('cop=nominal*', start)
component = component[:start] + '''if evaporator(upper,cap,nominal,penalty) > q_source_MW
    % C>=Cmin implies Qev>=Q*(Cmin-1)/Cmin. Scale the bracket by
    % available SOURCE, not by request/capacity. No COP/MW slope is formed.
    sourceFraction=(double(cfg.hp.cop_min)-1)/double(cfg.hp.cop_min);
    bound=q_source_MW/sourceFraction;
    if isfinite(bound)
        % Outward rounding allowance; retain the original request/cap limit.
        expanded=bound+4*eps(bound);
        if isfinite(expanded),upper=min(upper,expanded);end
    end
    % Feasible lower endpoint and floating-point adjacency terminate search.
    % The guard is a rejection safeguard, not an accuracy iteration budget.
    iterations=0;
    while true
        middle=lower+(upper-lower)/2;
        if middle==lower || middle==upper,break;end
        if evaporator(middle,cap,nominal,penalty)<=q_source_MW
            lower=middle;
        else
            upper=middle;
        end
        iterations=iterations+1;
        if iterations>2048
            error('DCHR:v40:HPResolution','Source bracket cannot resolve an adjacent feasible endpoint.');
        end
    end
    q=lower;
else
    q=upper;
end
if q==0
    error('DCHR:v40:HPResolution','Positive feasible HP output cannot be represented.');
end
''' + component[end:]
component = component.replace('% C(Q)=a+b*Q, and Qev(Q)=Q-Q/C(Q).', '% C(Q)=a+b*(Q/cap), and Qev(Q)=Q-Q/C(Q).')
component = component.replace('hp.source_used_MW=q-hp.electric_MW;', """% Avoid subtracting nearly equal Q and W when COP is close to one.
hp.source_used_MW=evaporator(q,cap,nominal,penalty);
if hp.source_used_MW==0
    error('DCHR:v40:HPResolution','Positive evaporator heat cannot be represented.');
end""")
component = component.replace('qev=q-q/(nominal*(1-penalty+penalty*(q/cap)));',
                              'cop=nominal*(1-penalty+penalty*(q/cap));\n    qev=q*((cop-1)/cop);')
write(ROOT / 'matlab/+dchr/+components/heat_pump_step_v40.m', component)

harness = (HERE / 'run_stateflow_hp_domain_v39.m').read_text().replace('v39', 'v40').replace('v38', 'v40').replace('0.39', '0.40').replace('0.38', '0.40')
harness = harness.replace('% Focused defect audit: execute preserved saved release v40, never rebuild it.', '% Execute saved v40 HP repair, all six modes, references and actual faults.')
harness = harness.replace("cfg.model.hp_backend='lift_polynomial';rejected=false;", "if isfield(q,'nominal_cop'),cfg.hp.poly_c0=q.nominal_cop;end\n    cfg.model.hp_backend='lift_polynomial';rejected=false;")
harness = harness.replace("record([q.id '_no_unexpected_domain_rejection'],~rejected);", "expectedReject=false;if isfield(q,'expected_reject'),expectedReject=q.expected_reject;end\n    record([q.id '_expected_domain'],rejected==expectedReject);\n    if expectedReject,record([q.id '_resolution_diagnostic'],strcmp(eid,'DCHR:v40:HPResolution'));end")
harness = harness.replace("writejson(fullfile(folder,'assertions_v40.json'),checks);", "faults=run_stateflow_faults_v40(mdl,folder,cases{1});\nwritejson(fullfile(folder,'runtime_faults_v40.json'),faults);\nrecord('30_actual_runtime_rejections',numel(faults)==30 && all([faults.rejected]));\nwritejson(fullfile(folder,'assertions_v40.json'),checks);")
harness = harness.replace("'new_model',false", "'new_model',true")
harness = harness.replace("'note','Execution/invariant checks only; independent analytic implementation comparisons are separate, may FAIL.'", "'runtime_faults',numel(faults),'note','Independent analytic comparisons must also pass before scoped acceptance.'")
write(HERE / 'run_stateflow_hp_domain_v40.m', harness)
launcher = (ROOT / 'audit/run_stateflow_hp_domain_v39.ps1').read_text().replace('v39', 'v40')
write(ROOT / 'audit/run_stateflow_hp_domain_v40.ps1', launcher)
print('Prepared additive v40 builder, source-relative HP component, harness and MAT export')
