"""Create additive exponential loss-first Stateflow sources; no baseline writes."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'matlab/simulink'


def put(name, text):
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as out:
        out.write(text)


for name in ['stateflow_choose_mode', 'stateflow_allocate', 'stateflow_contract_gate']:
    s = (HERE / (name + '_v24.m')).read_text(encoding='utf-8').replace('v24', 'v28')
    s = s.replace('energyStart*(1-cfgPorts(7)*cfgPorts(1))',
                  'energyStart*exp(-cfgPorts(7)*cfgPorts(1))')
    s = s.replace('energyStart*(1-cfgPorts(7)*dt)', 'energyStart*exp(-cfgPorts(7)*dt)')
    s = s.replace('loss/h, boiler', 'continuous lambda/h, boiler')
    if name == 'stateflow_allocate':
        s = s.replace('standing=energyStart-after;', 'standing=-energyStart*expm1(-cfgPorts(7)*dt);')
    if name == 'stateflow_contract_gate':
        s = s.replace('% All powers MW; energies MWh; dt h. No new physical-model assumption.',
            '% Powers MW; energies MWh; dt h. Exponential passive retention, LOSS-FIRST split.\n'
            '% Constant ambient/property lumped assumption; active-flow integration is approximate.')
        s = s.replace("assert(all(isfinite(raw)) && all(isfinite(cfgPorts)),", 
            "assert(cfgPorts(7)>=0 && isfinite(cfgPorts(7)*dt), 'Invalid continuous loss-rate product.');\n"
            "assert(all(isfinite(raw)) && all(isfinite(cfgPorts)),")
    put(name + '_v28.m', s)

s = (HERE / 'build_dispatch_stateflow_v24.m').read_text(encoding='utf-8').replace('v24', 'v28')
s = s.replace('% Build additive v28 runtime-contract model; preserve v14 and v22.',
    '% Build additive v28 exponential loss-first model; preserve all previous models.')
s = s.replace("ch.Description='v28 six-state finite TES/HP/boiler dispatch.",
    "ch.Description='v28 exponential passive TES retention; loss-first split. Six-state finite TES/HP/boiler dispatch.")
put('build_dispatch_stateflow_v28.m', s)

s = (HERE / 'run_stateflow_rejections_v24.m').read_text(encoding='utf-8').replace('v24', 'v28')
s = s.replace('for j=1:numel(c.setup), b=mutate(b,c.setup(j)); end',
    'for j=1:numel(c.setup)\n'
    '            if iscell(c.setup), setup=c.setup{j}; else, setup=c.setup(j); end\n'
    '            b=mutate(b,setup);\n'
    '        end')
put('run_stateflow_rejections_v28.m', s)

s = (HERE / 'run_stateflow_acceptance_v24.m').read_text(encoding='utf-8').replace('v24', 'v28')
s = s.replace('% Execute actual model intervals, compare all v16 ports, and inspect topology.',
    '% Execute new exponential-retention model, compare numerical/reference/legacy ports.')
s = s.replace("sources={fullfile(root,'audit','dispatch_reference_vectors_v18.csv'), ...\n"
    "    fullfile(root,'audit','stateflow_qa_vectors_v22.csv')};",
    "sources={fullfile(root,'audit','stateflow_qa_vectors_v28.csv'), ...\n"
    "    fullfile(root,'audit','dispatch_reference_vectors_v18.csv')};")
s = s.replace("assert(isfile(sources{2})", "assert(isfile(sources{1})")
s = s.replace("v=readtable(sources{f},'TextType','string'); ids=unique(v.scenario_id,'stable');",
    "v=readtable(sources{f},'TextType','string');\n"
    "    if f==2\n"
    "        % New explicit continuous rate: old numbers reused only as scenarios.\n"
    "        v.continuous_loss_rate_per_h=v.loss_fraction_per_h;\n"
    "        v.scenario_id=\"legacy_input_\"+v.scenario_id;\n"
    "    end\n"
    "    v.scheme=repmat(\"exponential_loss_first\",height(v),1);\n"
    "    ids=unique(v.scenario_id,'stable');")
s = s.replace('reference=dchr.simulate_dispatch_v16(cfg,input);', 'reference=dchr.simulate_dispatch_v28(cfg,input);')
s = s.replace('cfg.storage.loss_fraction_per_h', 'cfg.storage.continuous_loss_rate_per_h')
s = s.replace("expectedNames=v.Properties.VariableNames(startsWith(v.Properties.VariableNames,'expected_'));",
    "expectedNames=v.Properties.VariableNames(startsWith(v.Properties.VariableNames,'expected_'));\n"
    "        if f==2, expectedNames={}; end % v18 states follow preserved linear physics.")
s = s.replace('"_v16_"', '"_v28_reference_"').replace('verified v16 MATLAB numerical dispatch', 'separate v28 MATLAB numerical dispatch')
marker='        expectedMode=zeros(n,1);'
addition="""        % Same finite-step map as legacy linear model only after explicit conversion.
        legacyCfg=cfg;
        legacyCfg.storage.loss_fraction_per_h=-expm1(-p(7)*dt)/dt;
        oldReference=dchr.simulate_dispatch_v16(legacyCfg,input);
        for k=1:numel(names)
            record(ids(j)+"_v16_equivalent_retention_"+string(names{k}), ...
                near(actual.(names{k}),oldReference.(names{k})), ...
                'Legacy fraction explicitly converted; this is algebraic equivalence, not new physics validation.');
        end
        old=Simulink.SimulationInput('DCHR_Dispatch_Stateflow_v24');
        old=old.setVariable('dchr_dt_v24',dt,'Workspace','DCHR_Dispatch_Stateflow_v24');
        old=old.setVariable('dchr_stop_v24',(n-1)*dt,'Workspace','DCHR_Dispatch_Stateflow_v24');
        old=old.setVariable('dchr_input_v24',[(0:n-1)'*dt table2array(input)],'Workspace','DCHR_Dispatch_Stateflow_v24');
        oldp=p; oldp(7)=legacyCfg.storage.loss_fraction_per_h;
        old=old.setVariable('dchr_p_v24',oldp,'Workspace','DCHR_Dispatch_Stateflow_v24');
        old=old.setVariable('dchr_h_v24',h,'Workspace','DCHR_Dispatch_Stateflow_v24');
        old=old.setVariable('dchr_E0_v24',cfg.storage.initial_soc*p(2),'Workspace','DCHR_Dispatch_Stateflow_v24');
        oldResult=sim(old);
        save(fullfile(outputDir,char(ids(j)+"_legacy_equivalent_simulation.mat")),'oldResult');
        record(ids(j)+"_actual_v24_equivalent_ports", ...
            near(y,samples(oldResult.dispatch_trace_v24,13)) && ...
            near(u,samples(oldResult.hp_trace_v24,8)) && ...
            near(e,reshape(oldResult.energy_start_trace_v24.Data,[],1)), ...
            'Actual preserved v24 model and new v28 match after effective-fraction conversion.');
"""
assert marker in s
s = s.replace(marker, addition + marker)
s = s.replace("load_system(modelPath); cleanup=onCleanup(@()close_system(mdl,0));", 
    "load_system(modelPath); load_system(fullfile(here,'DCHR_Dispatch_Stateflow_v24.slx'));\n"
    "cleanup=onCleanup(@()close_models(mdl));")
s = s.replace("'eta_charge','eta_discharge','loss_fraction_per_h'", "'eta_charge','eta_discharge','continuous_loss_rate_per_h'")
s = s.replace("'poly_c0','poly_c1','poly_c2'};", "'poly_c0','poly_c1','poly_c2','scheme'};")
s = s.replace("r.loss_fraction_per_h", "r.continuous_loss_rate_per_h")
s = s.replace('c.storage.loss_fraction_per_h=r.continuous_loss_rate_per_h;',
              'c.storage.continuous_loss_rate_per_h=r.continuous_loss_rate_per_h;')
s = s.replace("'version','0.24'", "'version','0.28'")
s = s.replace("rejectSummary=run_stateflow_rejections_v28(mdl,outputDir);", 
    "experiments=run_stateflow_loss_experiments_v28(outputDir);\n"
    "record('actual_storage_timestep_experiments',experiments.failed==0, ...\n"
    "    'Actual v24/v28 idle and constant charging convergence against exact continuous lumped ODE.');\n"
    "rejectSummary=run_stateflow_rejections_v28(mdl,outputDir);")
s = s.replace("'runtime_invalid_cases',rejectSummary.cases,", "'loss_experiments',experiments, ...\n    'runtime_invalid_cases',rejectSummary.cases,")
s += "\nfunction close_models(mdl)\nclose_system(mdl,0); close_system('DCHR_Dispatch_Stateflow_v24',0);\nend\n"
put('run_stateflow_acceptance_v28.m', s)
print('Created additive v28 builder, chart helpers, runtime gate, acceptance and rejection harness.')
