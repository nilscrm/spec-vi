"""Read-only diagnosis of saved full runs; never changes the acceptance oracle."""
import sys,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools'))
from state_codec import decode_values
from stage_reference import FIELDS
from evaluate import compare,write_json,sha
out=Path(__file__).resolve().parent
src=out.parent/'three_updates_12/run.stdout';ref=ROOT/'reports/physics/first-stages/reference/side12'
blocks={}
for line in src.read_text().splitlines():
 w=line.split()
 if w[0]=='STAGE':name=w[1];blocks[name]=[]
 elif w[0]=='P':blocks[name].append(decode_values(w[2:],30))
checks=[]
for name,rows in blocks.items():
 path=out/(name+'.tsv');path.write_text(''.join(str(i)+' '+' '.join(format(x,'.17e') for x in row)+'\n' for i,row in enumerate(rows)))
 c=compare(ref/(name+'.tsv'),path,1e-9,5e-12,1728,31);c['stage']=name;checks.append(c)
eos=[]
for it in [1,2]:
 original=[[float(x) for x in l.split()[1:]] for l in (ref/f'i{it}-eos.tsv').read_text().splitlines()]
 for label,rows in [('original_inputs',original),('vine_inputs',blocks[f'i{it}-rest'])]:
  for power in ['pow','multiply']:
   errs=[];fails=0
   for p,q in zip(rows,original):
    r=p[9]/p[10];r2=r*r;r4=r2*r2
    v=math.pow(r,7) if power=='pow' else (r4*r2)*r
    pressure=(1/7)*(3500*3500)*(v-1)+p[13]
    err=abs(pressure-q[12]);errs.append(err);fails+=err>1e-9+5e-12*abs(q[12])
   eos.append({'iteration':it,'inputs':label,'power':power,'failures':fails,'max_absolute_error':max(errs)})
write_json(out/'analysis.json',{'source_sha256':sha(src),'scope':'diagnostic replay, not acceptance','all_stage_fields':checks,'eos_input_isolation':eos})
print(json.dumps(eos,indent=2));print([(c['stage'],c['failures']) for c in checks if not c['passed']])
