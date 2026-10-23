"""Run every fixed size/update combination; preserve failures and don't widen limits."""
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
from evaluate import write_json
out=Path(__file__).resolve().parent
cases=[]
for mode in ['workers2','depth']:
    for updates in [1,3]:
        for side in [12,16]:
            name=f'side{side}_updates{updates}_{mode}'
            target=out/name
            argv=[sys.executable,str(ROOT/'tools/physics_measure.py'),'--side',str(side),'--updates',str(updates),'--mode',mode,'--output',str(target)]
            with (out/(name+'.log')).open('w') as log:
                code=subprocess.run(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT).returncode
            result=json.loads((target/'result.json').read_text()) if (target/'result.json').exists() else {'passed':False,'error':'Missing report'}
            cases.append({'name':name,'argv':argv,'exit_code':code,'result':result})
            write_json(out/'progress.json',{'port_complete':False,'cases':cases})
write_json(out/'result.json',{'passed':all(c['exit_code']==0 and c['result']['passed'] for c in cases),'port_complete':False,'cases':cases})
