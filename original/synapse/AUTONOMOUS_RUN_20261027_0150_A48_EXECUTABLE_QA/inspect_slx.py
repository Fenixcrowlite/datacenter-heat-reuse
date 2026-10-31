from pathlib import Path
from zipfile import ZipFile
p=Path(__file__).parent/'DCHR_A48_Graphical_Closed_Loop.slx'
with ZipFile(p) as z:
 print('ZIP_TEST',z.testzip())
 names=z.namelist();print('FILES',names[:20]);
 for key in ['GraphicalSupervisor','CoupledController','SupervisorSignals','TRIP_PENDING','RAMPING','Stateflow']:
  matches=[n for n in names if n.endswith(('.xml','.mxarray')) and key.encode() in z.read(n)]
  print(key,matches[:8])
