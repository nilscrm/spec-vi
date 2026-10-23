"""Isolated preparation and runtime bucket scan diagnostics; not acceptance."""
import sys,json,shutil
from pathlib import Path
sys.path.insert(0,'tools')
from evaluate import ROOT,run,write_json,parse_stats,tree_hash
from neighbors_gate import driver,validate_rows,oracle
from pilot_gate import balanced
from toolchain import verify
out=ROOT/'reports/neighbors/capture-audit/local-copy';verify();lib=out/'sph';shutil.copytree(ROOT/'reports/neighbors/cell-major/grid4/sph',lib,dirs_exist_ok=True)
p=lib/'neighbors.vi';s=p.read_text();a=s.index('fn prepare(');b=s.index('\nfn in_cell',a);part=s[a:b];start=part.index(' let r=');part=part[:start]+' let local=b;'+part[start:].replace('b.', 'local.');s=s[:a]+part+s[b:];fields=[f'r.{i}+{8*i}' for i in range(10)]
s+='''
pub fn diag_ranges(points:Tree[Point],qs:Tree[(N32,Query)])->Tree[(N32,Tree[N32])]{
 let b=bounds(points);#sph::tree::map(prepare(qs,b),fn*((i,_,r):Prepared){(i,RANGES)})
}
pub fn diag_scan(points:Tree[Point],qs:Tree[(N32,Query)])->Tree[(N32,Tree[N32])]{
 let b=bounds(points);let bucket=select(labels(points,b),0);#sph::tree::map(qs,fn*((i,q)){(i,scan(bucket,q))})
}
'''.replace('RANGES',balanced(fields));p.write_text(s)
fixtures=json.loads((ROOT/'reports/neighbors/eager-cached-validation/fixtures.json').read_text());results=[]
for c in fixtures:
 if not c['name'].startswith('scaling_'):continue
 pts=c['points'];los=[min(p[k] for p in pts) for k in (1,2,3)];his=[max(p[k] for p in pts) for k in (1,2,3)]
 def cell(v,k):
  lo=los[k];hi=his[k];d=hi-lo
  return 0 if hi<=lo else (0 if v<lo+d*.25 else 1) if v<lo+d*.5 else (2 if v<lo+d*.75 else 3)
 bucket=[p for p in pts if all(cell(p[k+1],k)==0 for k in range(3))]
 for nq in [1,16,64,256]:
  qs=[c['queries'][i%len(c['queries'])] for i in range(nq)]
  for mode in ['ranges']:
   if mode=='scan':expected=[oracle(bucket,q) for q in qs]
   else:
    expected=[]
    for _,x,y,z,r,period in qs:
     vals=[cell(x-r,0),cell(x+r,0),cell(y-r,1),cell(y+r,1),cell(z-r,2),cell(z+r,2),cell((z-period)-r,2),cell((z-period)+r,2),cell((z+period)-r,2),cell((z+period)+r,2)]
     expected.append([v+8*i for i,v in enumerate(vals)])
   for measure in ['correctness','depth']:
    p=out/f'{c["name"]}_q{nq}_{mode}_{measure}.vi';driver(pts,qs,p,'correctness' if measure=='correctness' else 'candidate')
    s=p.read_text();a=s.index('let index=neighbors::build(points);');b=s.index('\n',s.index('let output=',a));s=s[:a]+f'let output=neighbors::diag_{mode}(points,queries);'+s[b:];p.write_text(s)
    r=run([sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(lib)]+(['--depth'] if measure=='depth' else [])+[str(p)],ROOT,p.with_suffix(''),180)
    value=Path(r['stdout']).read_text()
    if measure=='correctness':validate_rows(value,expected)
    else:
     assert int(value)==sum(v+1 for row in expected for v in row)
     entry=dict(points=len(pts),bucket_points=len(bucket),queries=nq,mode=mode,**parse_stats(Path(r['stderr']).read_text()));results.append(entry);print(entry,flush=True)
    write_json(out/'result.json',{'diagnostic_only':True,'correctness':True,'metrics':results,'library':tree_hash(lib)})
