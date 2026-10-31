function summary = dchr_a38_replay_acceptance(v08csv, a36csv, a38dir)
%DCHR_A38_REPLAY_ACCEPTANCE Isolated MATLAB numerical acceptance, NOT Stateflow.
% Example:
% dchr_a38_replay_acceptance('...\\sim_v08_zdravy_SK.csv', ...
%     '...\\scenario_both_off.csv', '...\\AUTONOMOUS_RUN_20261026_1054_A38_TES_N1_INTEGRATION')
% Run only in an owned MATLAB session with sufficient RAM. No GUI/SCADA changes.
raw=readtable(v08csv,'VariableNamingRule','preserve');
dispRows=readtable(a36csv,'VariableNamingRule','preserve');
if height(raw)~=672 || height(dispRows)~=672
    error('A38:Length','Expected 672 input intervals');
end
labels={'both','main_only','backup_only','neither'};
capacities=[330000,180000,150000,0];
policies={'no_shed','ideal_40pct','ramp15k_40pct'};
cases=0; comparisons=0; maxError=0;
fields={'Q_reject_actual_W','Q_unhandled_W','Q_IT_shed_W', ...
    'T_IT_next_C','E_TES_next_J','TES_SOC_next', ...
    'Q_TES_charge_actual_W','P_HP_proxy_W','Q_HP_source_W','alarm_next'};
for j=1:numel(labels)
    for k=1:numel(policies)
        filename=['trace_' labels{j} '_' policies{k} '.csv'];
        expected=readtable(fullfile(a38dir,filename),'VariableNamingRule','preserve');
        if height(expected)~=672
            error('A38:TraceLength','Expected 672 output intervals');
        end
        state=struct('E_J',450*3.6e6,'T_C',30,'shed_W',0);
        for i=1:672
            h=(i-1)*.25;
            if abs(double(raw.cas_h(i))-h)>1e-8 || ...
               abs(double(dispRows.cas_h(i))-h)>1e-8 || ...
               abs(double(expected.cas_h(i))-h)>1e-8
                error('A38:Time','Nonaligned timestamps');
            end
            [state,obs]=dchr_a38_step(table2struct(raw(i,:)), ...
                table2struct(dispRows(i,:)),state,capacities(j),policies{k},h>=24);
            for n=1:numel(fields)
                field=fields{n};
                value=double(expected.(field)(i));
                difference=abs(obs.(field)-value);
                tolerance=1e-4;
                if strcmp(field,'TES_SOC_next') || strcmp(field,'T_IT_next_C')
                    tolerance=1e-6;
                end
                if difference>tolerance
                    error('A38:Mismatch','%s interval %d field %s delta %.9g',filename,i,field,difference);
                end
                comparisons=comparisons+1;
                maxError=max(maxError,difference);
            end
        end
        cases=cases+1;
    end
end
summary=struct('status','MATLAB_NUMERICAL_ACCEPTANCE_PASS', ...
    'cases',cases,'samples_per_case',672,'comparisons',comparisons, ...
    'max_error',maxError,'stateflow_executed',false, ...
    'physical_release_allowed',false);
disp(summary);
end
