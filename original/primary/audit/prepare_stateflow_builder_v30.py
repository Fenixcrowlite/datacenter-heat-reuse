"""Additive v30 Stateflow builder based on preserved six-state topology."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
here = root / 'matlab/simulink'
s = (here / 'build_dispatch_stateflow_v28.m').read_text(encoding='utf-8').replace('v28', 'v30')
s = s.replace('% Build additive v30 exponential loss-first model; preserve all previous models.',
              '% Build new ambient-temperature TES model with exact constant-power integration.')
s = s.replace('[0 6 35 70 5;1 0 35 70 6;2 0 35 70 10]',
              '[0 6 35 75 5 45;1 0 35 75 6 45;2 0 35 75 10 45]')
s = s.replace('[1 10 3 4 .9 .8 .01 2]', '[1 10 3 4 .9 .8 .01 6 .2 20 2]')
s = s.replace("'[1 8]'", "'[1 11]'").replace("'[13 1]'", "'[17 1]'")
s = s.replace("'InputPortWidth','13'", "'InputPortWidth','17'")
s = s.replace("ch.Description='v30 exponential passive TES retention; loss-first split. Six-state finite TES/HP/boiler dispatch. Normal-mode host HP component; state actions drive all delivery ports.';",
              "ch.Description='Release 0.30: constant-ambient mixed TES, exact constant-power integration and uniformly throttled endpoint capacity/cutoff limits. Separate condenser/delivery proxies. Six operating states; normal-mode host HP.';")
marker="names={'IDLE'"
insert="f=Stateflow.EMFunction(ch); f.Name='storage_kernel_v30';\nf.Position=[600 420 220 65]; f.Script=fileread(fullfile(root,'matlab','+dchr','+components','storage_kernel_v30.m'));\n"
assert marker in s
s = s.replace(marker, insert + marker)
with (here / 'build_dispatch_stateflow_v30.m').open('x', encoding='utf-8', newline='\n') as out:
    out.write(s)
print('Created matlab/simulink/build_dispatch_stateflow_v30.m; preserved every prior builder/model.')
