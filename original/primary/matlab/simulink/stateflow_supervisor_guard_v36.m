function ok=stateflow_supervisor_guard_v36(target,s,p,c,age)
%#codegen
% Energy comparisons in MWh; dwell comparisons in physical hours.
etol=64*eps(max(1,p(2)));
ttol=stateflow_time_tolerance_v36([age;c(2);c(3)]);
ok=false;
if target==1
    ok=s(17)==3 && s(2)<=c(1)+etol && age>=c(3)-ttol && s(4)>0 && s(16)==0;
else
    ok=s(16)==0 && ((s(17)==2 && s(2)>=p(2)-etol && age>=c(2)-ttol) || ...
        (s(17)==1 && s(4)==0));
end
end
