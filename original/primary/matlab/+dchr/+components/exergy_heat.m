function ex_MW = exergy_heat(q_MW, delivery_temp_C, reference_temp_C)
%EXERGY_HEAT Physical exergy of a heat flow relative to environment.
T = delivery_temp_C + 273.15;
T0 = reference_temp_C + 273.15;
ex_MW = q_MW .* max(0,1-T0./T);
end
