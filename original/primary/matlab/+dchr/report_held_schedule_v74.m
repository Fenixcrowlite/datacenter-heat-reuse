function r=report_held_schedule_v74(a,trace)
% Report accepted complete schedules only. Never infer energy from solver ticks,
% average a COP, credit unmet demand, or collapse uncertainty to a midpoint.
n=size(a.input,1);assert(size(trace,1)==n&&size(trace,2)==1380&&n>0, ...
    'DCHR:v74:IncompleteSchedule','Refused/prefix schedules require explicit separate records');
assert(all(all(isfinite(trace))),'DCHR:v74:FiniteTrace','Finite trace required');
assert(trace(1,3)<=a.initial(1)&&a.initial(1)<=trace(1,4)&& ...
    trace(1,178)==a.initial(2)&&trace(1,179)<=a.initial(3)&&a.initial(3)<=trace(1,180), ...
    'DCHR:v74:InitialTrace','Initial inventory, latch and age must match trace');
assert(all(trace(:,2)==73)&&all(all(trace(:,76:100)==repmat(a.p,n,1))), ...
    'DCHR:v74:TraceSchema','Saved v73 schema and immutable policy required');
assert(all(trace(:,10)<=a.schedule(:,2)&a.schedule(:,2)<=trace(:,11)), ...
    'DCHR:v74:ClockHull','Physical labels must remain in retained clock hulls');
assert(isequal(trace(2:end,3:4),trace(1:end-1,5:6)), ...
    'DCHR:v74:InventoryContinuity','Held input changes cannot reset inventory');
assert(all(trace(:,53)<=0&trace(:,54)>=0)&&all(trace(:,5)>=0&trace(:,5)<=trace(:,6)), ...
    'DCHR:v74:TraceConservation','TES and first-law hulls required');
names={'hp_heat','recovered_source','compressor_work','standing_loss','charge_loss', ...
    'discharge_loss','delivered_service','backup_heat','unmet_demand','auxiliary_work'};
r=struct('version','0.74','saved_model_version','0.73r2','held_intervals',n, ...
    'duration_h_label',a.schedule(end,2),'physical_clock_hull',trace(end,10:11), ...
    'initial_inventory',a.initial(1),'final_inventory_hull',trace(end,5:6), ...
    'first_law_residual_hull',trace(end,53:54),'positive_segments',sum(trace(:,13)), ...
    'interior_events',sum(trace(:,14)),'final_modes',unique(trace(:,1))');
for j=1:10,r.([names{j} '_MWh_hull'])=trace(end,31+2*(j-1):32+2*(j-1));end
direct=[0 0];tes=[0 0];demand=[0 0];
for k=1:n
    demand=add(demand,product(a.schedule(k,3),[a.schedule(k,1) a.schedule(k,1)]));
    for j=1:trace(k,13)
        z=trace(k,100+80*(j-1)+(1:80));
        residual=a.schedule(k,3)-z(25)-z(27)-z(28)-z(29);
        assert(abs(residual)<=32*eps(max(1,a.schedule(k,3))), ...
            'DCHR:v74:DemandTrace','Held demand must match every segment allocation');
        direct=add(direct,product(z(25),z(7:8)));tes=add(tes,product(z(27),z(7:8)));
    end
end
r.demand_MWh_hull=demand;r.direct_HP_service_MWh_hull=direct;r.TES_service_MWh_hull=tes;
r.external_electricity_MWh_hull=add(r.compressor_work_MWh_hull,r.auxiliary_work_MWh_hull);
r.service_plus_unmet_MWh_hull=add(r.delivered_service_MWh_hull,r.unmet_demand_MWh_hull);
r.delivered_HP_heating_COP_hull=ratio(r.hp_heat_MWh_hull,r.compressor_work_MWh_hull);
r.electricity_per_delivered_service_hull=ratio(r.external_electricity_MWh_hull,r.delivered_service_MWh_hull);
r.ratio_semantics='EMPTY_WHEN_DENOMINATOR_NOT_CERTAINLY_POSITIVE; SERVICE_INCLUDES_BACKUP_AND_TES';
r.scope='SYNTHETIC_COMPLETE_SCHEDULE_NORMAL_MODE_MACRO_SEGMENTS_NO_ANNUAL_OR_PHYSICAL_VALIDATION';
end
function z=add(x,y)
z=[x(1)+y(1) x(2)+y(2)];z=[z(1)-2*eps(z(1)) z(2)+2*eps(z(2))];
if all(x==0),z=y;elseif all(y==0),z=x;end
end
function z=product(q,t)
if q==0,z=[0 0];else,z=q*t;z=[max(0,z(1)-2*eps(z(1))) z(2)+2*eps(z(2))];end
end
function z=ratio(x,y)
z=[];if y(1)>0,z=[x(1)/y(2) x(2)/y(1)];z=[max(0,z(1)-2*eps(z(1))) z(2)+2*eps(z(2))];end
end
