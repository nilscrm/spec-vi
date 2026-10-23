"""Diagnostic ONLY: prebuilt exact tree removes construction from the workload.
Not an acceptance measurement or implementation: production inputs must be built at runtime.
"""
import sys,json
from pathlib import Path
sys.path.insert(0,'tools')
from evaluate import ROOT,run,parse_stats,write_json
from neighbors_gate import synthetic,driver,point,oracle
from pilot_gate import lit
out=ROOT/'reports/neighbors/batch-routing'
def tree(xs):
 if not xs:return None
 if len(xs)==1:return ('leaf',xs[0])
 m=len(xs)//2;return ('branch',tree(xs[:m]),tree(xs[m:]))
def leaves(t):
 if t is None:return []
 if t[0]=='leaf':return [t[1]]
 return leaves(t[1])+leaves(t[2])
def join(a,b):
 return b if a is None else a if b is None else ('branch',a,b)
def partition(t,axis,mid):
 if t is None:return None,None
 if t[0]=='leaf':return (t,None) if t[1][axis+1]<mid else (None,t)
 a,b=partition(t[1],axis,mid);c,d=partition(t[2],axis,mid)
 return join(a,c),join(b,d)
def emit_tree(t):
 if t is None:return 'Tree::Empty()'
 if t[0]=='leaf':return 'Tree::Leaf('+point(t[1])+')'
 return 'Tree::Branch('+emit_tree(t[1])+','+emit_tree(t[2])+')'
def index(t,level=0):
 xs=leaves(t);n=len(xs)
 if not n:return 'neighbors::Index::Empty()'
 if n==1:return 'neighbors::Index::Leaf('+point(xs[0])+')'
 if n<=8 or level>=32:return 'neighbors::Index::Bucket('+emit_tree(t)+')'
 low=[min(x[k] for x in xs) for k in (1,2,3)];high=[max(x[k] for x in xs) for k in (1,2,3)]
 spans=[b-a for a,b in zip(low,high)];axis=max(range(3),key=lambda i:spans[i])
 mid=low[axis]+(high[axis]-low[axis])*.5
 if mid<=low[axis] or mid>=high[axis]:return 'neighbors::Index::Bucket('+emit_tree(t)+')'
 b='{n:'+str(n)+','+','.join(f'{a}min:{lit(lo)},{a}max:{lit(hi)}' for a,lo,hi in zip('xyz',low,high))+'}'
 l,r=partition(t,axis,mid)
 return 'neighbors::Index::Branch('+b+','+index(l,level+1)+','+index(r,level+1)+')'
results=[]
for name,pts,qs in synthetic():
 if not name.startswith('scaling_'):continue
 for mode in ('single','batch'):
  p=out/(name+'_query_only_'+mode+'.vi');driver(pts,qs,p,'candidate')
  s=p.read_text();s='\n'.join(line for line in s.splitlines() if not line.startswith('let points='))+'\n'
  s=s.replace('neighbors::build(points)','black_box('+index(tree(pts))+')')
  if mode=='batch':s=s.replace('tree::map(queries,fn* ((i,q)) {(i,neighbors::find(index,q))})','neighbors::find_batch(index,queries)')
  p.write_text(s)
  r=run([sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(out/'sph'),'--depth',str(p)],ROOT,p.with_suffix(''),180)
  assert int(Path(r['stdout']).read_text())==sum(i+1 for q in qs for i in oracle(pts,q))
  results.append(dict(case=name,mode=mode,**parse_stats(Path(r['stderr']).read_text())))
write_json(out/'query-only.json',{'diagnostic_only':True,'excludes_construction':True,'metrics':results});print(json.dumps(results,indent=2))
