function hp = heat_pump_step_v38(q_source_MW, source_C, sink_C, request_MW, cfg)
%HEAT_PUMP_STEP_V38 Scalar, source-constrained heating-mode screening step.
% Additive component: existing annual dispatch and components are unchanged.
% cop_min is an operating cutoff, never an upward efficiency clamp.
% Temperatures are reservoir proxies; this is not a calibrated refrigerant map.
% Off/unavailable states have zero flows and undefined (NaN) operating COP.

checkScalar(q_source_MW,'q_source_MW',0,Inf,false);
checkScalar(request_MW,'request_MW',0,Inf,false);
checkScalar(source_C,'source_C',-273.15,Inf,true);
checkScalar(sink_C,'sink_C',-273.15,Inf,true);
if sink_C <= source_C
    error('DCHR:v38:TemperatureLift','Heating mode requires sink_C > source_C.');
end
checkScalar(cfg.hp.max_heat_output_MW,'max_heat_output_MW',0,Inf,false);
checkScalar(cfg.hp.cop_min,'cop_min',1,Inf,true);
checkScalar(cfg.hp.cop_max,'cop_max',cfg.hp.cop_min,Inf,false);
checkScalar(cfg.hp.carnot_efficiency,'carnot_efficiency',0,1,true);
checkScalar(cfg.hp.part_load_penalty,'part_load_penalty',0,1,false);
if cfg.hp.part_load_penalty >= 1
    error('DCHR:v38:InvalidInput','part_load_penalty must be less than one.');
end
backend = string(cfg.model.hp_backend);
if ~isscalar(backend) || ismissing(backend) || ...
        ~any(backend == ["carnot","lift_polynomial"])
    error('DCHR:v38:Backend','Supported backends: carnot, lift_polynomial.');
end

q_source_MW=double(q_source_MW); request_MW=double(request_MW);
lift=double(sink_C)-double(source_C);
carnot=(double(sink_C)+273.15)/lift;
if backend == "carnot"
    raw=double(cfg.hp.carnot_efficiency)*carnot;
else
    checkScalar(cfg.hp.poly_c0,'poly_c0',-Inf,Inf,false);
    checkScalar(cfg.hp.poly_c1,'poly_c1',-Inf,Inf,false);
    checkScalar(cfg.hp.poly_c2,'poly_c2',-Inf,Inf,false);
    raw=double(cfg.hp.poly_c0)+double(cfg.hp.poly_c1)*lift+double(cfg.hp.poly_c2)*lift^2;
    if raw > carnot*(1+32*eps)
        error('DCHR:v38:PolynomialCarnot','Polynomial COP exceeds the reservoir Carnot bound.');
    end
end
if ~isfinite(carnot) || ~isfinite(raw)
    error('DCHR:v38:NonfinitePrediction','Temperature/COP prediction is nonfinite.');
end
nominal=min(raw,double(cfg.hp.cop_max));
hp=struct('cop_carnot',carnot,'cop_raw',raw,'cop_nominal',nominal, ...
    'cop_operating',NaN,'heat_output_MW',0,'electric_MW',0,'source_used_MW',0, ...
    'available',false,'lift_K',lift,'status',"OFF");
cap=double(cfg.hp.max_heat_output_MW); penalty=double(cfg.hp.part_load_penalty);
if q_source_MW == 0 || request_MW == 0 || cap == 0
    return
end
if nominal < cfg.hp.cop_min
    hp.status="NOMINAL_COP_BELOW_MIN"; return
end

upper=min(request_MW,cap);
% C(Q)=a+b*Q, and Qev(Q)=Q-Q/C(Q). On C>=cop_min>1,
% dQev/dQ=1-a/C(Q)^2>0. Solve only on this admissible interval.
% Normalize only after bounding Q<=capacity; no COP/MW slope is formed.
fraction=0;
if penalty>0,fraction=max(0,(double(cfg.hp.cop_min)/nominal-(1-penalty))/penalty);end
lower=cap*fraction;
if fraction>0 && lower==0
    error('DCHR:v38:HPResolution','Minimum operating output underflows.');
end
% The lower bound defines the cutoff. Re-evaluating C(lower)<cop_min
% can misclassify an exact cutoff by one floating-point rounding unit.
if lower > upper
    hp.status="PART_LOAD_COP_BELOW_MIN"; return
end
if evaporator(lower,cap,nominal,penalty) > q_source_MW
    hp.status="SOURCE_BELOW_MIN_OPERATING_POINT"; return
end
if evaporator(upper,cap,nominal,penalty) > q_source_MW
    % Keep lower feasible; 80 bisections exceed double precision resolution.
    for iteration=1:80
        middle=lower+(upper-lower)/2;
        if middle == lower || middle == upper, break; end
        if evaporator(middle,cap,nominal,penalty) <= q_source_MW
            lower=middle;
        else
            upper=middle;
        end
    end
    q=lower;
else
    q=upper;
end
if q == 0, return; end
cop=nominal*(1-penalty+penalty*(q/cap));
if ~isfinite(cop) || q/cop==0 || cop<cfg.hp.cop_min-32*eps(max(1,cop))
    error('DCHR:v38:HPResolution','Operating COP/electricity cannot be represented.');
end
hp.cop_operating=cop;
hp.heat_output_MW=q;
hp.electric_MW=q/cop;
hp.source_used_MW=q-hp.electric_MW;
hp.available=true;
hp.status="OPERATING";
end

function qev=evaporator(q,cap,nominal,penalty)
if q == 0
    qev=0;
else
    qev=q-q/(nominal*(1-penalty+penalty*(q/cap)));
end
end

function checkScalar(value,name,lower,upper,strictLower)
if ~isnumeric(value) || ~isreal(value) || ~isscalar(value) || ~isfinite(value)
    error('DCHR:v38:InvalidInput','%s must be a finite real numeric scalar.',name);
end
v=double(value);
if v < lower || v > upper || (strictLower && v == lower)
    error('DCHR:v38:InvalidInput','%s is outside its physical domain.',name);
end
end
