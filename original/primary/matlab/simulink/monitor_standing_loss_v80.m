function monitor_standing_loss_v80(u,p,old,y)
%#codegen
% Necessary constitutive loss bound, independent of the TES flow/root solver.
monitor_hp_partition_v79(u,p,old,y);
assert(p(6)>=0,'v80 nonnegative loss coefficient');
for j=1:y(13)
    z=y(100+80*(j-1)+(1:80));loss=z(38:39)';
    if p(6)==0
        assert(all(loss==0),'v80 zero coefficient standing loss');
    else
        % E'=B-lambda*E with held B has a derivative of constant sign.
        % Thus lambda*duration*[min(endpoint E),max(endpoint E)] encloses
        % the standing-loss integral. All quantities here are nonnegative.
        E=[min(z(11),z(13)) max(z(12),z(14))];
        bound=mulpositive(mulpositive([p(6) p(6)],z(7:8)'),E);
        assert(loss(1)<=bound(2)&&bound(1)<=loss(2),'v80 standing loss rate');
    end
end
end
function z=mulpositive(x,y)
assert(all(x>=0)&&all(y>=0),'v80 positive multiplication domain');
if all(x==0)||all(y==0),z=[0 0];return;end
v=[x(1)*y(1) x(2)*y(2)];
z=[max(0,v(1)-2*eps(v(1))) v(2)+2*eps(v(2))];
assert(all(isfinite(z)),'v80 loss arithmetic');
end
