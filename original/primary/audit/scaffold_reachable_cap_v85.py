"""Additive Stateflow release: reuse accepted thermal kernel, change only cap contract."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def write(path,text):
    with (R/path).open('x',encoding='utf-8',newline='\n') as f:f.write(text)

s=(R/'matlab/simulink/electrical_policy_v83r2.m').read_text()
s=s.replace('electrical_policy_v83r2(raw)','electrical_policy_v85(raw,initialE)')
s=s.replace('% Conservative constant compressor ceiling across the entire TES domain.','% Constant cap over declared horizon, using a loss-independent reachable bound.')
s=s.replace("raw(26)>=0", "raw(26)>=0&&raw(27)>0&&initialE>=0")
s=s.replace("temperature=add([raw(2)","reachable=add([initialE initialE],mul(mul([raw(7) raw(7)], ...\n    [min(raw(9),raw(11)) min(raw(9),raw(11))]),[raw(27) raw(27)]));\nEbound=min(capacity(2),reachable(2));\ntemperature=add([raw(2)")
s=s.replace('[capacity(2) capacity(2)]','[Ebound Ebound]')
s=s.replace('function effective=', 'function [effective,Ebound]=')
s=s.replace('v83 ', 'v85 ')
write('matlab/simulink/electrical_policy_v85.m',s)
s=(R/'matlab/simulink/build_electrical_ceiling_v83r2.m').read_text().replace('v83r2','v85')
s=s.replace('[26 1]','[27 1]').replace("Size='[27 1]'","Size='[29 1]'").replace('zeros(26,1)','zeros(27,1)')
start=s.index("f.Script=sprintf('function [y,certificate]")
end=s.index("f=Stateflow.EMFunction(ch);f.Name='earliest_mode",start)
s=s[:start]+'''f.Script=sprintf('function [y,certificate]=electrical_dispatch_v85(u,raw,memory,rawMemory)\\nif memory(2)~=0,assert(all(raw==rawMemory),''v85 immutable electrical policy'');E0=memory(51);else,E0=u(10);end\\n[p,Ebound]=electrical_policy_v85(raw,E0);\\ny=earliest_dispatch_kernel_v75(u,p,memory);\\nassert(y(61)<=raw(27),''v85 declared horizon exceeded'');\\nfor k=1:y(13),z=y(100+80*(k-1)+(1:80));assert(max(z(12),z(14))<=Ebound,''v85 reachable inventory bound'');end\\nmonitor_standing_loss_v80(u,p,memory,y);\\ncertificate=[raw;p(11);Ebound];\\nend');
''' + s[end:]
s=s.replace('p=electrical_policy_v85(cfg);','if memory(2)==0,E0=u(10);else,E0=memory(51);end;p=electrical_policy_v85(cfg,E0);')
s=s.replace('v83 conservative compressor-ceiling;', 'v85 declared-horizon reachable-inventory compressor ceiling;')
write('matlab/simulink/build_electrical_ceiling_v85.m',s)
s=(R/'matlab/run_electrical_ceiling_v83r2.m').read_text().replace('v83r2','v85')
s=s.replace('[a.p c.ceiling_MW]','[a.p c.ceiling_MW c.horizon_h]')
s=s.replace("effective=electrical_policy_v85(raw');","[effective,Ebound]=electrical_policy_v85(raw',c.initial(1));")
s=s.replace('[raw a.p(11)]','[raw a.p(11) Ebound]')
s=s.replace('reshape(out.electrical_certificate_v83.Data,27,[])','reshape(out.electrical_certificate_v83.Data,29,[])')
s=s.replace("'version','0.83'","'version','0.85'").replace("'saved_model_version','0.85'","'saved_model_version','0.85'")
s=s.replace('v83 ', 'v85 ').replace('for j=1:4','for j=1:5')
s=s.replace("else,bad(2:end,26)=bad(2:end,26)/2;", "elseif j==5,bad(:,27)=base.input(1,5)/2;guard='v85 declared horizon exceeded';name='horizon_exceeded';\n    else,bad(2:end,26)=bad(2:end,26)/2;")
s=s.replace('electrical_ceiling_v83.mat','electrical_ceiling_v85.mat').replace('ELECTRICAL_V83','REACHABLE_V85')
s=s.replace("'DCHR:v83:AcceptanceFailure'","'DCHR:v85:AcceptanceFailure'")
# Fresh saved global-cap comparison for every candidate on identical inputs.
anchor="    runs{end+1}=struct"
s=s.replace(anchor,"""    globalModel='DCHR_Electrical_Dispatch_Stateflow_v83r2';
    load_system(fullfile(root,'matlab','simulink',[globalModel '.slx']));
    [~,globalTrace]=execute(globalModel,a,raw(1:26));close_system(globalModel,0);
"""+anchor)
s=s.replace("'reference_trace',comparison)","'reference_trace',comparison,'global_trace',globalTrace)")
s=s.replace("'certificate','reference_trace'}","'certificate','reference_trace','global_trace'}")
write('matlab/run_electrical_ceiling_v85.m',s)
write('audit/run_electrical_ceiling_v85.ps1',(R/'audit/run_electrical_ceiling_v83r2.ps1').read_text().replace('run_electrical_ceiling_v83r2','run_electrical_ceiling_v85'))
print('Added v85 builder, adapter, execution harness, batch runner.')
