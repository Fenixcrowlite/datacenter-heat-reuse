function ok=stateflow_supervisor_guard_v34(target,s,p,c,age)
%#codegen
% Independent Stateflow transition permission. Safety overrides ON dwell.
ok=false;tol=1e-10*max(1,p(2));
if target==1
    ok=s(17)==3 && s(2)<=c(1)+tol && age>=c(3)-tol && s(4)>0 && s(16)==0;
else
    ok=s(16)==0 && ((s(17)==2 && s(2)>=p(2)-tol && age>=c(2)-tol) || ...
        (s(17)==1 && s(4)==0));
end
end
