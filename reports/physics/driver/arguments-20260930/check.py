import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools'))
from evaluate import run,write_json,sha
out=Path(__file__).resolve().parent;source=ROOT/'benchmarks/sph-exa/app/square_patch.vi';cases=[]
for name,args in [('unknown',['--bogus']),('missing',['-n']),('invalid_side',['-n','9','-s','0'])]:
 case=out/name;case.mkdir();argv=[sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--heap','2G','--lib','sph='+str(ROOT/'benchmarks/sph-exa/vine'),str(source),'--',*args]
 try:run(argv,case,case/'run',60)
 except RuntimeError:pass
 r=json.loads((case/'run.json').read_text());passed=r['exit_code']!=0 and not r['timed_out'] and not list(case.glob('*.txt'))
 cases.append({'name':name,'passed':passed,'process':r});write_json(out/'progress.json',{'cases':cases})
write_json(out/'result.json',{'passed':all(c['passed'] for c in cases),'driver_sha256':sha(source),'cases':cases})
