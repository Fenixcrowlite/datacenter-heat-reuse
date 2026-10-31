function r=report_held_schedule_v76(a,trace)
% Reporting version 0.76 accepts trace schema / saved model 0.75.
dchr.validate_temporal_trace_v76(a,trace);
r=dchr.report_held_schedule_v75(a,trace);
r.version='0.76';
end
