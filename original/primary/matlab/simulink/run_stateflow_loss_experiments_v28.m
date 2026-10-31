function summary = run_stateflow_loss_experiments_v28(outputDir)
% Actual saved v24/v28 simulations: passive semigroup and active split error.
% Synthetic sensitivity rate .04/h, 24 h horizon; no equipment calibration.
% Each tick integrates [t,t+dt); terminal is last Next port, not final timestamp.
dtValues=[4 2 1 .5 .25]; lambda=.04; horizon=24;
schemes={'linear_loss_first','exponential_loss_first'};
rows=table(); checks=struct('name',{},'passed',{});
for experiment=1:2
    if experiment==1, id='passive'; initial=10; q=0;
    else, id='constant_charge'; initial=0; q=1; end
    exact=initial*exp(-lambda*horizon)+q*(-expm1(-lambda*horizon))/lambda;
    for schemeIndex=1:2
        scheme=schemes{schemeIndex};
        if schemeIndex==1, mdl='DCHR_Dispatch_Stateflow_v24'; suffix='v24';
        else, mdl='DCHR_Dispatch_Stateflow_v28'; suffix='v28'; end
        previousError=Inf;
        for dt=dtValues
            n=round(horizon/dt); p=[dt 100 q 0 1 1 lambda 0]; h=[8 .45 1.2 8 0 1 4 0 0];
            inputs=[(0:n-1)'*dt repmat([.75*q 35 70 0],n,1)];
            s=Simulink.SimulationInput(mdl);
            s=s.setVariable(['dchr_dt_' suffix],dt,'Workspace',mdl);
            s=s.setVariable(['dchr_stop_' suffix],(n-1)*dt,'Workspace',mdl);
            s=s.setVariable(['dchr_input_' suffix],inputs,'Workspace',mdl);
            s=s.setVariable(['dchr_p_' suffix],p,'Workspace',mdl);
            s=s.setVariable(['dchr_h_' suffix],h,'Workspace',mdl);
            s=s.setVariable(['dchr_E0_' suffix],initial,'Workspace',mdl);
            result=sim(s);
            name=sprintf('%s_%s_dt_%g',id,suffix,dt); name=strrep(name,'.','p');
            save(fullfile(outputDir,[name '_simulation.mat']),'result');
            ts=result.get(['dispatch_trace_' suffix]); y=samples(ts,13);
            terminal=y(end,8); error=abs(terminal-exact);
            if schemeIndex==1, retention=1-lambda*dt; else, retention=exp(-lambda*dt); end
            expected=initial*retention^n+q*dt*(1-retention^n)/(1-retention);
            record([name '_recurrence'],abs(terminal-expected)<1e-9);
            record([name '_samples'],numel(ts.Time)==n && max(abs(ts.Time-(0:n-1)'*dt))<1e-9);
            record([name '_bounds_closure'],all(y(:,8)>=0 & y(:,8)<=100) && all(abs(y(:,13))<1e-9));
            record([name '_constant_charge'],all(abs(y(:,3)-q)<1e-9));
            if experiment==1 && schemeIndex==2
                record([name '_exact_passive'],error<1e-9);
            else
                record([name '_refinement_decreases_error'],error<previousError);
            end
            if experiment==2 && schemeIndex==2
                record([name '_loss_first_charge_overestimates'],terminal>exact);
            end
            previousError=error;
            trace=table(ts.Time,y(:,1),y(:,3),y(:,4),y(:,7),y(:,8),y(:,9),y(:,13), ...
                'VariableNames',{'Time_h','Mode','Charge_MW','Discharge_MW','After_MWh','Next_MWh','Standing_Loss_MWh','Residual_MWh'});
            traceFile=[name '_trace.csv']; writetable(trace,fullfile(outputDir,traceFile));
            rows=[rows;table(string(id),string(scheme),dt,lambda,horizon,initial,q,terminal,exact,error,n,string(traceFile), ...
                'VariableNames',{'scenario_id','scheme','dt_h','lambda_per_h','horizon_h','initial_MWh', ...
                'charge_internal_MW','terminal_MWh','exact_continuous_MWh','abs_error_MWh','intervals','trace_file'})]; %#ok<AGROW>
        end
    end
end
writetable(rows,fullfile(outputDir,'storage_timestep_experiments_v28.csv'));
writetable(struct2table(checks),fullfile(outputDir,'storage_experiment_assertions_v28.csv'));
summary=struct('cases',height(rows),'checks',numel(checks),'passed',sum([checks.passed]), ...
    'failed',sum(~[checks.passed]),'lambda_per_h',lambda,'horizon_h',horizon,'dt_values_h',dtValues, ...
    'passive_exp_partition_invariant',true,'active_exp_loss_first_exact',false, ...
    'scope','Actual saved-model sensitivity; constant-UA reduced assumption, uncalibrated scenario.', ...
    'max_abs_error_MWh',max(rows.abs_error_MWh));
assert(summary.failed==0,'DCHR:v28:LossExperimentFailed','See saved loss-experiment assertions.');

    function record(name,ok)
        checks(end+1)=struct('name',name,'passed',logical(ok));
        if ~ok, fprintf(2,'FAIL %s\n',name); end
    end
end

function values=samples(ts,width)
raw=ts.Data; n=numel(ts.Time);
if ismatrix(raw) && isequal(size(raw),[n width]), values=raw;
elseif size(raw,1)==width && numel(raw)==n*width, values=reshape(raw,width,n)';
else, error('DCHR:v28:TraceDimensions','Unexpected experiment timeseries dimensions.'); end
end
