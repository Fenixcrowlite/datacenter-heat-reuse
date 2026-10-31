"""Additive saved-model provenance and reporting repair; never replace baselines."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def write(rel, data):
    path = ROOT / rel
    with path.open('x', encoding='utf-8', newline='\n') as f:
        f.write(data)

def main():
    kernel = (ROOT/'matlab/simulink/earliest_dispatch_kernel_v73r2.m').read_text()
    kernel = kernel.replace('earliest_dispatch_kernel_v73r2', 'earliest_dispatch_kernel_v75')
    kernel = kernel.replace('y(2)=73;', 'y(2)=75;y(73:75)=[u(5);u(7);u(8)+2*u(9)];')
    kernel = kernel.replace('old(2)==73', 'old(2)==75')
    write('matlab/simulink/earliest_dispatch_kernel_v75.m', kernel)
    builder = (ROOT/'matlab/simulink/build_earliest_dispatch_v73r2.m').read_text()
    builder = builder.replace('build_earliest_dispatch_v73r2', 'build_earliest_dispatch_v75')
    builder = builder.replace('DCHR_Earliest_Dispatch_Stateflow_v73r2', 'DCHR_Earliest_Dispatch_Stateflow_v75')
    builder = builder.replace('earliest_dispatch_kernel_v73r2', 'earliest_dispatch_kernel_v75')
    builder = builder.replace('BUILT_INTERVAL_DISPATCH_V66', 'BUILT_REPORTING_STATEFLOW_V75')
    builder = builder.replace('v73 SAME six-mode', 'v75 input-bound SAME six-mode')
    write('matlab/simulink/build_earliest_dispatch_v75.m', builder)
    reporter = (ROOT/'matlab/+dchr/report_held_schedule_v74.m').read_text()
    reporter = reporter.replace('report_held_schedule_v74', 'report_held_schedule_v75')
    reporter = reporter.replace('DCHR:v74:', 'DCHR:v75:')
    reporter = reporter.replace("'version','0.74','saved_model_version','0.73r2'", "'version','0.75','saved_model_version','0.75'")
    reporter = reporter.replace('all(trace(:,2)==73)', 'all(trace(:,2)==75)')
    reporter = reporter.replace("n=size(a.input,1);", "dchr.validate_reporting_trace_v75(a,trace);\nn=size(a.input,1);")
    write('matlab/+dchr/report_held_schedule_v75.m', reporter)

if __name__ == '__main__':
    main()
