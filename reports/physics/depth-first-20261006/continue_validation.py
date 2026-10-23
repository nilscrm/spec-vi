"""Run fixed coverage after the in-flight depth measurement, without overlapping runs."""
import json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
while not (HERE/'depth12-16g/result.json').exists():time.sleep(2)
cmd=[sys.executable,str(ROOT/'tools/physics_gate.py'),'--output',str(HERE/'full-stages-16g'),'--reference',str(ROOT/'reports/physics/first-stages/reference'),'--library',str(HERE/'candidate/sph'),'--heap-gib','16']
with (HERE/'full-stages-16g.log').open('w') as log:
 code=subprocess.call(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
print(json.dumps({'command':cmd,'exit_code':code}),flush=True)
