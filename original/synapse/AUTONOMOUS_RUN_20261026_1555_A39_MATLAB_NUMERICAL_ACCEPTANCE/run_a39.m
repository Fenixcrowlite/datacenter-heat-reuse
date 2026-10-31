% A39 isolated numerical replay; no Simulink, Stateflow, SCADA, or hardware actuation.
a38 = 'C:/Users/Lysda/Desktop/SynapseControlCenter/recovery/AUTONOMOUS_RUN_20261026_1054_A38_TES_N1_INTEGRATION';
v08 = 'C:/Users/Lysda/OneDrive/Projects/DataCenter_Heat_Reuse/results/pool_measurement_v08/sim_v08_zdravy_SK.csv';
a36 = 'C:/Users/Lysda/Desktop/SynapseControlCenter/recovery/AUTONOMOUS_RUN_20261026_0744_A36_DCHR_REDISPATCH_REFERENCE/scenario_both_off.csv';
outdir = 'C:/Users/Lysda/Desktop/SynapseControlCenter/recovery/AUTONOMOUS_RUN_20261026_1555_A39_MATLAB_NUMERICAL_ACCEPTANCE';
addpath(a38);
try
    result = dchr_a38_replay_acceptance(v08,a36,a38);
    result.run_type = 'MATLAB_R2026a_BATCH_NUMERICAL_ONLY';
    result.release_allowed = false;
    result.executed_at = char(datetime('now','Format','yyyy-MM-dd''T''HH:mm:ssXXX'));
    fp = fopen(fullfile(outdir,'MATLAB_RESULT.json'),'w');
    assert(fp > 0,'A39:Output','Cannot open output');
    fwrite(fp,jsonencode(result),'char');
    fclose(fp);
    disp('A39_MATLAB_NUMERICAL_PASS');
catch ME
    fp = fopen(fullfile(outdir,'MATLAB_FAILURE.txt'),'w');
    if fp > 0
        fprintf(fp,'%s\n%s\n',ME.identifier,ME.message);
        fclose(fp);
    end
    rethrow(ME);
end
