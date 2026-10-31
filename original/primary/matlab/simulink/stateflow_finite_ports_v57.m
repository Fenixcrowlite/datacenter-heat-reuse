function accounting=stateflow_finite_ports_v57(raw,summary,b,v,p,dt)
%#codegen
% Actual executed segments determine electricity and variable water flows.
work=0;aux=0;residual=0;sourceRate=0;hotRate=0;
etol=1e-10+64*eps(max(1,p(2)+(v(13)+p(11))*dt));
ptol=1e-9+64*eps(max(1,max(abs([b(8);b(9);b(10);v(17)]))));
for k=1:64
    z=raw((k-1)*28+(1:28));span=z(2);
    if span>0
        assert(z(11)<=b(10)+ptol && z(13)<=b(8)+ptol && ...
            z(11)<=b(9)+ptol,'Finite source/hot/nameplate port exceeded.');
        if z(11)>0
            assert(abs(z(15)-b(6))<=1e-10+64*eps(max(1,b(6))), ...
                'Actual compressor COP differs from water boundary.');
        end
        sourceRate=max(sourceRate,z(13)/b(12));
        hotRate=max(hotRate,z(11)/b(13));
        w=z(12)*span;a=b(11)*w;
        % Auxiliary electricity is external and completely rejected as heat.
        % Equal entering/leaving auxiliary energy leaves tank/service unchanged.
        r=z(4)+(z(13)+z(9))*span+w+a-z(20)*span-z(5)-sum(z(17:19))-a;
        assert(isfinite(a) && isfinite(r) && abs(r)<=etol, ...
            'Expanded compressor/source/auxiliary first law failed.');
        work=work+w;aux=aux+a;residual=residual+r;
    end
end
assert(isfinite(work) && isfinite(aux) && abs(work-summary(20)*dt)<=etol && ...
    abs(residual-summary(13))<=2*etol, 'Finite macro accounting failed.');
assert(sourceRate<=v(11)+ptol/b(12) && hotRate<=v(12)+ptol/b(13), ...
    'Finite variable water-flow rates exceeded.');
accounting=[work;aux;aux;work+aux;residual;sourceRate;hotRate];
end
