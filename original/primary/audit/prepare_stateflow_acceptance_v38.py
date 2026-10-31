from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'matlab/simulink'
def write(name,text):
    p=HERE/name;assert not p.exists(),p;p.write_text(text,encoding='utf-8')
f=(HERE/'run_stateflow_faults_v36.m').read_text().replace('v36','v38')
f=f.replace('[1;0]','[1;0;0;0]').replace('[.5;0]','[.5;0;0;0]').replace('[1;-1]','[1;-1;0;0]').replace('reshape(c.initial_clock,2,1)','reshape(c.initial_clock,4,1)')
f=f.replace("'age=age+s(1);','age=age+1;'","'stateflow_clock_add_v38(age,low,bound,s(1))','stateflow_clock_add_v38(age,low,bound,1)'")
write('run_stateflow_faults_v38.m',f)
export=(HERE/'export_stateflow_resolution_v37.m').read_text().replace('v37','v38').replace('v36','v38')
export=export.replace("'sample_time_h',{}","'sample_time_h',{},'segments',{}")
export=export.replace("'sample_time_h',[]","'sample_time_h',[],'segments',[]")
export=export.replace('clock_start_trace_v38,2','clock_start_trace_v38,4').replace('clock_end_trace_v38,2','clock_end_trace_v38,4')
export=export.replace("saved=load(fullfile(folder,paths(k).name),'result');r=saved.result;","saved=load(fullfile(folder,paths(k).name));if isfield(saved,'result'),r=saved.result;else,r=saved.baseline;end")
export=export.replace('item.sample_time_h=r.dispatch_trace_v38.Time;','''item.sample_time_h=r.dispatch_trace_v38.Time;
        raw=samples(r.segment_trace_v38,1792);plan=samples(r.plan_trace_v38,1408);
        for i=1:size(raw,1)
            z=reshape(raw(i,:),28,64)';s=reshape(plan(i,:),22,64)';
            for j=1:64
                if z(j,2)>0,item.segments(end+1,:)=[i-1 j z(j,:) s(j,:)];end %#ok<AGROW>
            end
        end''')
write('export_stateflow_resolution_v38.m',export)
meta=(HERE/'export_stateflow_numeric_metadata_v37.m').read_text().replace('v37','v38').replace('v36','v38')
meta=meta.replace('cap=hp.heat_output_MW;','cap=0; if ~isempty(hp),cap=hp.heat_output_MW;end')
meta=meta.replace("hp=a.output;cap=0; if ~isempty(hp),cap=hp.heat_output_MW;end","hp=a.output;if isempty(hp),hp=struct('cop_operating',NaN,'heat_output_MW',0);end;cap=hp.heat_output_MW;")
write('export_stateflow_numeric_metadata_v38.m',meta)
print('Prepared v38 fault harness and separate MAT export')
