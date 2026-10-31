function u = dchr_stateflow_hp_v24(x,E,p,h,model_dt)
% Runtime physical-domain and clock contract for the saved v24 model.
% The verified v14 HP and v16 loss-first TES policy are unchanged.
try
    validateattributes(model_dt,{'double'},{'real','finite','scalar','positive'});
    validateattributes(p,{'double'},{'real','finite','vector','numel',8});
    validateattributes(p(1),{'double'},{'real','finite','scalar','positive'});
    if p(1)~=model_dt
        error('DCHR:v24:IntegrationStep', ...
            'Physical interval p(1)=%.17g h differs from model sample time %.17g h.',p(1),model_dt);
    end
    u=dchr_stateflow_hp_v22(x,E,p,h);
catch original
    if strcmp(original.identifier,'DCHR:v24:IntegrationStep'), rethrow(original); end
    failure=MException('DCHR:v24:PhysicalDomain','Runtime physical-domain rejection: %s',original.message);
    failure=addCause(failure,original); throw(failure);
end
end
