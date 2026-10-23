"""Validate every bound bit separately, rather than only the depth checksum."""
exec(open('reports/neighbors/bounds-layout/routing.py').read().split('\nresults=[]')[0])
checks=[]
for name,pts,qs in synthetic():
 if name not in ['scaling_64','scaling_256']:continue
 vals=[v for k in (1,2,3) for v in (min(p[k] for p in pts),max(p[k] for p in pts))]
 expected=['b %s %s'%struct.unpack('<II',struct.pack('<d',v)) for v in vals]+['n '+str(len(pts))]+['p '+str(p[0]) for p in pts]
 for mode in ['bounds','soa','pairs']:
  p=out/f'{name}_{mode}_exact.vi';p.write_text(header+'pub fn main(&io:&IO){let t=black_box('+balanced(pts,point)+');show(neighbors::'+mode+'(t),&io);dump(t,&io);}\n')
  r=run([sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(lib),str(p)],ROOT,p.with_suffix(''),180)
  assert Path(r['stdout']).read_text().splitlines()==expected
  checks.append(dict(case=name,mode=mode,passed=True))
write_json(out/'exact.json',checks);print('All six exact bounds/identity comparisons pass')
