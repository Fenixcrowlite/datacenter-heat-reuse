"""Create additive v36 executed harness from preserved v35 audit harness."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'matlab/simulink'
s=(HERE/'run_stateflow_admissibility_v35.m').read_text().replace('v35','v36').replace('v34','v36').replace('0.35','0.36').replace('0.34','0.36')
s=s.replace('% Targeted execution of immutable saved v36; temporary in-memory fault only.',
            '% Unified dispatch acceptance of new saved v36; temporary in-memory faults only.')
s=s.replace("'stateflow_admissibility_v36.py','stateflow_reference_v36.py'", "'stateflow_specification_v36.py','stateflow_reference_v34.py'")
s=s.replace("'verify_stateflow_admissibility_v36.py','verify_stateflow_v36.py'", "'verify_stateflow_v36.py','verify_stateflow_v34.py'")
s=s.replace("totals=table();segments=table();checks", "totals=table();segments=table();checks")
# Keep verified v32 execution as separate read-only saved model comparison.
s=s.replace("cleanup=onCleanup(@()close_system(mdl,0));", "load_system(fullfile(here,'DCHR_Dispatch_Stateflow_v32.slx'));\ncleanup=onCleanup(@()closeModels());")
point="    fprintf('CLEAN_EXECUTED=%s intervals=%d\\n',c.id,height(a));"
s=s.replace(point,"""    if j<=6
        dt=c.p(1);n=size(c.inputs,1);old='DCHR_Dispatch_Stateflow_v32';
        os=Simulink.SimulationInput(old);
        ns={'dt','stop','input','p','h','E0'};
        vs={dt,(n-1)*dt,[(0:n-1)'*dt c.inputs],reshape(c.p,1,[]),reshape(c.h,1,[]),c.initial_energy_MWh};
        for ii=1:numel(ns),os=os.setVariable(['dchr_' ns{ii} '_v32'],vs{ii},'Workspace',old);end
        oldresult=sim(os);save(fullfile(folder,[c.id '_v32_comparison.mat']),'oldresult');
        oldy=samples(oldresult.dispatch_trace_v32,25);newy=samples(result.dispatch_trace_v36,25);
        record([c.id '_verified_v32'],near(newy(:,[1:21 23:25]),oldy(:,[1:21 23:25])));
        writematrix(oldy,fullfile(folder,[c.id '_v32_comparison.csv']));
    end
"""+point)
# Fault suite before scale injections, independently saved pre/post clean MATs.
point='% A scale-independent 0.01 physical-hour clock error'
s=s.replace(point,"""runtimeFaults=run_stateflow_faults_v36(mdl,folder,cases{1});
writejson(fullfile(folder,'runtime_fault_evidence_v36.json'),runtimeFaults);
record('30_runtime_faults_rejected',numel(runtimeFaults)==30 && all([runtimeFaults.rejected]));
% A scale-independent 0.01 physical-hour clock error""")
start=s.index('% Expected defect reproduction')
end=s.index('writetable(faultSegments',start)
s=s[:start]+"""% Corrected release must reject every actual clock corruption and early guard.
record('all_scale_clock_corruptions_rejected',numel(faults)==4 && all([faults.rejected]));
record('all_early_dwell_guards_rejected',numel(guard)==4 && all(~[guard.permitted]));
extended=run_stateflow_dimensional_faults_v36(mdl,folder,cases);
writejson(fullfile(folder,'dimensional_fault_evidence_v36.json'),extended.faults);
writejson(fullfile(folder,'time_resolution_evidence_v36.json'),extended.time);
record('extended_dimensional_runtime_faults_rejected',all([extended.faults.rejected]));
record('physical_time_boundary_checks',all([extended.time.passed]));
"""+s[end:]
s=s.replace("'model_version','0.36'", "'model_version','0.36'")
s=s.replace("'conclusion','OPEN dimensional clock/guard tolerance defect; no new model acceptance'", """'runtime_fault_trials',numel(runtimeFaults),'runtime_faults_rejected',sum([runtimeFaults.rejected]), ...
    'extended_fault_trials',numel(extended.faults),'extended_faults_rejected',sum([extended.faults.rejected]), ...
    'conclusion','Dimensional tolerance repair executed; implementation acceptance only'""")
s += """
function closeModels()
for m={'DCHR_Dispatch_Stateflow_v36','DCHR_Dispatch_Stateflow_v32'}
    if bdIsLoaded(m{1}),close_system(m{1},0);end
end
end
"""
path=HERE/'run_stateflow_admissibility_v36.m';assert not path.exists();path.write_text(s,encoding='utf-8')
print('Prepared unified v36 harness.')
