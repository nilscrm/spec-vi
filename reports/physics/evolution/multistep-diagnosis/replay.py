"""Separate original-order density replay on saved candidate states."""
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'tools'))
from evaluate import write_json,sha
out=Path(__file__).resolve().parent;ref=ROOT/'reports/physics/first-stages/reference/side12'
commands=[];values={}
for i in range(3):
 for source in ['original','vine']:
  geometry=(ref if source=='original' else out)/f'i{i}-geometry.tsv'
  target=out/f'replayed_{source}_{i}.tsv'
  cmd=[str(out/'replay'),'12',str(geometry),str(ref/f'i{i}-geometry.meta'),str(ref/f'i{i}-neighbors.tsv'),str(target)]
  subprocess.run(cmd,check=True,capture_output=True);commands.append(cmd)
  values[source,i]=[float(l.split()[1]) for l in target.read_text().splitlines()]
checks=[]
for i in range(3):
 expected=[[float(x) for x in l.split()[1:]] for l in (ref/f'i{i}-density.tsv').read_text().splitlines()]
 for source in ['original','vine']:
  errs=[abs(a-b[9]) for a,b in zip(values[source,i],expected)]
  checks.append({'iteration':i,'source_geometry':source,'max_density_error':max(errs),'different_density_values':sum(e!=0 for e in errs)})
eos=[]
for i in [1,2]:
 expected=[[float(x) for x in l.split()[1:]] for l in (ref/f'i{i}-eos.tsv').read_text().splitlines()]
 candidate=[[float(x) for x in l.split()[1:]] for l in (out/f'i{i}-rest.tsv').read_text().splitlines()]
 errors=[];failures=0
 for ro,ro0,p,q in zip(values['vine',i],values['vine',0],candidate,expected):
  r=ro/ro0;r2=r*r;r4=r2*r2;pressure=(1/7)*(3500*3500)*((r4*r2)*r-1)+p[13]
  e=abs(pressure-q[12]);errors.append(e);failures+=e>1e-9+5e-12*abs(q[12])
 eos.append({'iteration':i,'failures':failures,'max_pressure_error':max(errors)})
report={'scope':'Diagnostic only: original ordered IDs supplied, no runtime Vine ordering acceptance','commands':commands,'source_sha256':sha(out/'replay.cpp'),'density_checks':checks,'eos_with_replayed_densities':eos}
write_json(out/'replay.json',report);print(json.dumps({'density':checks,'eos':eos},indent=2))
