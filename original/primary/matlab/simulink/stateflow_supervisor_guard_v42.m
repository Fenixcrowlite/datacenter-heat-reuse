function ok=stateflow_supervisor_guard_v42(target,s,p,c,age,low,bound)
%#codegen
% Energy comparisons in MWh; dwell comparisons in physical hours.
etol=64*eps(max(1,p(2)));
ttol=stateflow_time_tolerance_v36([age;c(2);c(3)]);
ok=false;
if target==1
    ok=s(17)==3 && s(2)<=c(1)+etol && stateflow_dwell_ready_v42(age,low,bound,c(3)) && s(4)>0 && s(16)==0;
else
    ok=s(16)==0 && ((s(17)==2 && s(2)>=p(2)-etol && stateflow_dwell_ready_v42(age,low,bound,c(2))) || ...
        (s(17)==1 && s(4)==0));
end
end
