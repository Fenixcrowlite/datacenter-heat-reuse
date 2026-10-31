function z=exact_rational_v60(op,x,y)
% Exact rational arithmetic for binary64 input provenance. Host/JVM only.
% No Symbolic Toolbox, rounded decimal input, or production scalar endpoint.
switch op
    case 'from'
        assert(isa(x,'double')&&isscalar(x)&&isreal(x)&&isfinite(x),'DCHR:v60:ExactDomain','Finite scalar double required.');
        b=javaObject('java.math.BigDecimal',x);n=b.unscaledValue();scale=double(b.scale());
        ten=javaObject('java.math.BigInteger','10');one=javaObject('java.math.BigInteger','1');
        if scale>=0,d=ten.pow(scale);else,n=n.multiply(ten.pow(-scale));d=one;end
        z=normalize(n,d);
    case 'add',z=normalize(x.n.multiply(y.d).add(y.n.multiply(x.d)),x.d.multiply(y.d));
    case 'sub',z=normalize(x.n.multiply(y.d).subtract(y.n.multiply(x.d)),x.d.multiply(y.d));
    case 'mul',z=normalize(x.n.multiply(y.n),x.d.multiply(y.d));
    case 'div'
        assert(y.n.signum()~=0,'DCHR:v60:ExactDomain','Zero exact denominator.');
        z=normalize(x.n.multiply(y.d),x.d.multiply(y.n));
    case 'cmp',z=double(x.n.multiply(y.d).compareTo(y.n.multiply(x.d)));
    case 'text',z=struct('numerator',char(x.n.toString()),'denominator',char(x.d.toString()));
    case 'interval'
        mc=javaObject('java.math.MathContext',40);
        n=javaObject('java.math.BigDecimal',x.n);d=javaObject('java.math.BigDecimal',x.d);
        b=n.divide(d,mc);v=double(b.doubleValue());assert(isfinite(v),'DCHR:v60:Resolution','Exact value outside finite binary64.');
        q=exact_rational_v60('from',v);c=exact_rational_v60('cmp',q,x);
        if c==0,z=[v v];elseif c<0,z=[v v+eps(v)];else,z=[v-eps(v) v];end
        assert(all(isfinite(z))&&exact_rational_v60('cmp',exact_rational_v60('from',z(1)),x)<=0 && ...
            exact_rational_v60('cmp',exact_rational_v60('from',z(2)),x)>=0, ...
            'DCHR:v60:Resolution','Directed rational enclosure failed.');
    otherwise,error('DCHR:v60:ExactDomain','Unknown rational operation.');
end
end
function z=normalize(n,d)
assert(d.signum()~=0,'DCHR:v60:ExactDomain','Zero denominator.');
if d.signum()<0,n=n.negate();d=d.negate();end
g=n.gcd(d);z=struct('n',n.divide(g),'d',d.divide(g));
end
