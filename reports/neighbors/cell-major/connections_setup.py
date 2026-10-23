from pathlib import Path
import shutil
out=Path('reports/neighbors/cell-major')
extra='''
type Request=(Query,Ranges,~Tree[N32]);
fn wire(qs:Tree[Prepared])->(Tree[Request],Tree[(N32,Tree[N32])]){match qs{
 Tree::Empty(){(Tree::Empty(),Tree::Empty())}
 Tree::Leaf((i,q,r)){let result;(Tree::Leaf((q,r,~result)),Tree::Leaf((i,result)))}
 Tree::Branch(l,r){let(a,b)=wire(l);let(c,d)=wire(r);(Tree::Branch(a,c),Tree::Branch(b,d))}
}}
fn split(qs:Tree[Request])->(Tree[Request],Tree[Request]){match qs{
 Tree::Empty(){(Tree::Empty(),Tree::Empty())}
 Tree::Leaf((q,r,o)){let a;let b;let next=(Tree::Leaf((q,r,~a)),Tree::Leaf((q,r,~b)));~o=Tree::Branch(a,b);next}
 Tree::Branch(l,r){let(a,b)=split(l);let(c,d)=split(r);(Tree::Branch(a,c),Tree::Branch(b,d))}
}}
fn finish(points:Tree[Point],qs:Tree[Request],k:N32){match qs{
 Tree::Empty(){}
 Tree::Leaf((q,r,o)){~o=if in_cell(q,r,k){scan(points,q)}else{Tree::Empty()};}
 Tree::Branch(l,r){finish(points,l,k);finish(points,r,k);}
}}
fn send(t:Tree[Tree[Point]],qs:Tree[Request],first:N32,n:N32){match t{
 Tree::Empty(){finish(Tree::Empty(),qs,first);}
 Tree::Leaf(points){finish(points,qs,first);}
 Tree::Branch(l,r){let(a,b)=split(qs);let half=n/2;send(l,a,first,half);send(r,b,first+half,n-half);}
}}
pub fn find_batch(Grid(b,t):Grid,qs:Tree[(N32,Query)])->Tree[(N32,Tree[N32])]{
 if b.n==0 {#sph::tree::map(qs,fn*((i,_)){(i,Tree::Empty())})}else{let(qs,out)=wire(prepare(qs,b));send(t,qs,0,SIDE*SIDE*SIDE);out}
}
'''
for side in [2,4]:
 lib=out/f'wires{side}'/'sph';shutil.copytree(out/f'grid{side}'/'sph',lib,dirs_exist_ok=True)
 p=lib/'neighbors.vi';s=p.read_text();s=s[:s.index('pub fn find_batch(')];p.write_text(s+extra.replace('SIDE',str(side)))
s=(out/'full.py').read_text().replace("['compact','grid2','grid4']","['wires2','wires4']").replace("out/'full.json'","out/'connections.json'")
(out/'connections.py').write_text(s)
