"""Preserve v73 and add a correlated symbolic passive-root repair."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def write(name,text):
    p=ROOT/name;assert not p.exists(),name;p.write_text(text)

def main():
    k=(ROOT/'matlab/simulink/earliest_dispatch_kernel_v73.m').read_text()
    k=k.replace('function y=earliest_dispatch_kernel_v73(', 'function y=earliest_dispatch_kernel_v73r2(')
    k=k.replace("if deriv(2)<0,candidates(3,:)=certify_event_root_v73(E,B,p(6),restart,-1,u(5),p(23),age)';",
        "if tag==1&&all(B==0)&&p(6)>0&&p(25)-p(5)<=.5*(p(5)-p(2))\n                candidates(3,:)=passive_contact_root_v73r2(p,u(5),p(23),age)';y(72)=1;\n            elseif deriv(2)<0,candidates(3,:)=certify_event_root_v73(E,B,p(6),restart,-1,u(5),p(23),age)';")
    k=k.replace("if all(x==0),z=y;elseif all(y==0),z=x;else,z=out([x(1)+y(1) x(2)+y(2)]);end",
        "if all(x==0),z=y;elseif all(y==0),z=x;\nelseif x(1)==x(2)&&y(1)==y(2)&&x(1)==-y(1),z=[0 0];\nelse,z=out([x(1)+y(1) x(2)+y(2)]);end")
    write('matlab/simulink/earliest_dispatch_kernel_v73r2.m',k)
    b=(ROOT/'matlab/simulink/build_earliest_dispatch_v73.m').read_text()
    b=b.replace('build_earliest_dispatch_v73','build_earliest_dispatch_v73r2').replace("mdl='DCHR_Earliest_Dispatch_Stateflow_v73'","mdl='DCHR_Earliest_Dispatch_Stateflow_v73r2'")
    b=b.replace('earliest_dispatch_kernel_v73','earliest_dispatch_kernel_v73r2')
    b=b.replace("f=Stateflow.EMFunction(ch);f.Name='earliest_mode_v73';", "f=Stateflow.EMFunction(ch);f.Name='passive_contact_root_v73r2';f.Position=[1250 680 380 90];f.Script=fileread(fullfile(here,'passive_contact_root_v73r2.m'));\nf=Stateflow.EMFunction(ch);f.Name='earliest_mode_v73';")
    write('matlab/simulink/build_earliest_dispatch_v73r2.m',b)
    h=(ROOT/'matlab/run_earliest_admissibility_v73.m').read_text().replace('run_earliest_admissibility_v73','run_earliest_admissibility_v73r2').replace('earliest_dispatch_kernel_v73','earliest_dispatch_kernel_v73r2').replace('build_earliest_dispatch_v73','build_earliest_dispatch_v73r2').replace("mdl='DCHR_Earliest_Dispatch_Stateflow_v73'","mdl='DCHR_Earliest_Dispatch_Stateflow_v73r2'")
    write('matlab/run_earliest_admissibility_v73r2.m',h)
    write('audit/run_earliest_admissibility_v73r2.ps1',(ROOT/'audit/run_earliest_admissibility_v73.ps1').read_text().replace('run_earliest_admissibility_v73(', 'run_earliest_admissibility_v73r2('))
    prep=(ROOT/'audit/prepare_earliest_repair_v73.py').read_text()
    prep=prep.replace("cases=[{k:c[k]", """# Cancellation equality and exact-binary near-early disable controls.
    base=next(c for c in cases if c['id']=='HP_only')
    for id,dts,minon,accepted in [('disable_compensated_equality',[.1,.2,.19999999999999998],.5,True),('disable_compensated_safe',[.1,.1,.05],.25,True),('disable_binary_rounded_early',[.1,.2,.7],1,False)]:
        p=list(base['p']);p[5]=0;p[21]=minon;ii=[];clock=0.
        for dt in dts+[.1]:
            clock+=dt;ii.append([1,0,clock,0,dt,.5,20,int(len(ii)<len(dts)),0,3,1,0])
        cases.append(dict(id=id,p=p,input=ii,family='compensated_age',expected_accept=accepted,expected_guard='' if accepted else 'v73 ON dwell not certified'))
    cases=[{k:c[k]""")
    prep=prep.replace("'earliest_repair_v73_'","'earliest_repair_v73r2_'")
    # Prior v73 drafts, generated model and harness are now sealed as well.
    prep=prep.replace("if 'v73' not in p.name","if 'v73r2' not in p.name")
    write('audit/prepare_earliest_repair_v73r2.py',prep)

if __name__=='__main__':main()
