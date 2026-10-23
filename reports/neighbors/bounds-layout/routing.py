"""Compare cached partition summaries with deferred bounds; same routed outputs."""
exec(open('reports/neighbors/bounds-layout/run.py').read().split('results=[]')[0])
s=(lib/'neighbors.vi').read_text().replace('fn partition(', 'pub fn partition(')
s+='''
fn route(t:Tree[Point],mid:F64)->(Tree[Point],Tree[Point]) {match t {
Tree::Empty(){(Tree::Empty(),Tree::Empty())}
Tree::Leaf(p){if p.x<mid {(Tree::Leaf(p),Tree::Empty())}else{(Tree::Empty(),Tree::Leaf(p))}}
Tree::Branch(l,r){let(a,b)=route(l,mid);let(c,d)=route(r,mid);(join(a,c),join(b,d))}
}}
pub fn deferred(t:Tree[Point],mid:F64)->((Bounds,Tree[Point]),(Bounds,Tree[Point])) {
let(l,r)=route(t,mid);((bounds(l),l),(bounds(r),r))
}
'''
(lib/'neighbors.vi').write_text(s)
header+='''
fn checksum(b:neighbors::Bounds)->N32 {((bits(b.xmin)+bits(b.xmax))+(bits(b.ymin)+bits(b.ymax)))+((bits(b.zmin)+bits(b.zmax))+b.n)}
fn dump(t:Tree[neighbors::Point],&io:&IO){match t{Tree::Empty(){}Tree::Leaf(p){io.println("p {p.id}");}Tree::Branch(l,r){dump(l,&io);dump(r,&io);}}}
fn show(b:neighbors::Bounds,&io:&IO){
'''+''.join('let N64(lo,hi)=b.'+f+'.to_bits();io.println("b {lo} {hi}");' for f in ['xmin','xmax','ymin','ymax','zmin','zmax'])+'io.println("n {b.n}");}\n'
results=[]
for name,pts,qs in synthetic():
 if name not in ['scaling_64','scaling_256']:continue
 mid=(min(p[1] for p in pts)+max(p[1] for p in pts))/2
 groups=[[p for p in pts if p[1]<mid],[p for p in pts if p[1]>=mid]]
 expected=[];sums=[]
 for group in groups:
  vals=[v for k in (1,2,3) for v in (min(p[k] for p in group),max(p[k] for p in group))]
  words=[struct.unpack('<II',struct.pack('<d',v)) for v in vals]
  expected+=['b %s %s'%w for w in words]+['n '+str(len(group))]+['p '+str(p[0]) for p in group]
  sums.append(sum(sum(w) for w in words)+len(group)+sum(p[0]+1 for p in group))
 for mode in ['cached','deferred']:
  for measure in ['correctness','depth']:
   expr=f'neighbors::partition(t,0,{mid}[F64])' if mode=='cached' else f'neighbors::deferred(t,{mid}[F64])'
   consume='show(a,&io);dump(l,&io);show(b,&io);dump(r,&io);' if measure=='correctness' else 'let value=(checksum(a)+ids(l))+(checksum(b)+ids(r));io.println("{value}");'
   p=out/f'{name}_routing_{mode}_{measure}.vi'
   p.write_text(header+'pub fn main(&io:&IO){let t=black_box('+balanced(pts,point)+');let((a,l),(b,r))='+expr+';'+consume+'}\n')
   r=run([sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(lib)]+(['--depth'] if measure=='depth' else [])+[str(p)],ROOT,p.with_suffix(''),180)
   actual=Path(r['stdout']).read_text().splitlines()
   assert actual==(expected if measure=='correctness' else [str(sum(sums)%2**32)]),(actual,expected)
   if measure=='depth':
    entry=dict(case=name,mode=mode,**parse_stats(Path(r['stderr']).read_text()));results.append(entry);print(entry,flush=True)
write_json(out/'routing.json',{'correctness':True,'measurements':results,'library':tree_hash(lib)})
