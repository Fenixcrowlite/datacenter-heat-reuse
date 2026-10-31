from pathlib import Path
import hashlib,json
root=Path(r"C:\Users\Lysda\Desktop\SynapseControlCenter\recovery")
dst=root/"AUTONOMOUS_RUN_20261026_2255_A46_INTEGRATION"
src=root/"AUTONOMOUS_RUN_20261026_1945_A43_FINITE_TRIP_RESIDUAL"/"build_a43.m"
original=src.read_text(encoding="utf-8")
assert original.count('"persistent E T state prevActive prevShed pending good res lastTrip effCap"')==1
assert original.count('" E=450*3.6e6;T=30;state=0;prevActive=0;prevShed=0;pending=0;good=0;res=0;lastTrip=false;effCap=330000;"')==1
assert original.count('"source=min(available,desired*(cop-1)/cop);"')==1
new=original.replace("DCHR_A43_Finite_Trip_Closed_Loop","DCHR_A46_Compressor_Closed_Loop")
new=new.replace("A43:","A46:").replace("A43_", "A46_").replace("a43_", "a46_")
new=new.replace("TRACE_A46_", "TRACE_A45_")
new=new.replace('"persistent E T state prevActive prevShed pending good res lastTrip effCap"','"persistent E T state prevActive prevShed pending good res lastTrip effCap hpAvailable"')
new=new.replace('" E=450*3.6e6;T=30;state=0;prevActive=0;prevShed=0;pending=0;good=0;res=0;lastTrip=false;effCap=330000;"','" E=450*3.6e6;T=30;state=0;prevActive=0;prevShed=0;pending=0;good=0;res=0;lastTrip=false;effCap=330000;hpAvailable=0;"')
new=new.replace('"source=min(available,desired*(cop-1)/cop);"','"sourceTarget=min(available,desired*(cop-1)/cop);"\n"hpAvailable=hpAvailable+(1-exp(-dt/1800))*(sourceTarget-hpAvailable);"\n"source=min(sourceTarget,hpAvailable);"')
new=new.replace("graphical_stateflow_chart_built',false", "graphical_stateflow_chart_built',false")
new=new.replace("A46_SIMULINK_EMCHART_CLOSED_LOOP_PARITY_PASS", "A46_SIMULINK_EMCHART_COMPRESSOR_PARITY_PASS")
new=new.replace("A46:License", "A46:License")
out=dst/"build_a46.m"
out.write_text(new,encoding="utf-8")
assert 'TRACE_A45_' in new and 'TRACE_A43_' not in new
assert 'hpAvailable' in new and new.count('hpAvailable')==6
assert "DCHR_A46_Compressor_Closed_Loop" in new
print(json.dumps({"script":str(out),"sha256":hashlib.sha256(out.read_bytes()).hexdigest(),"lines":len(new.splitlines())}))

