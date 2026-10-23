from pathlib import Path
import shutil
out=Path('reports/pilot/sine-hoist');lib=out/'sph';shutil.copytree('benchmarks/sph-exa/vine',lib,dirs_exist_ok=True)
p=lib/'pilot.vi';s=p.read_text();a=s.index('// Initialization has');b=s.index('pub type Particle',a)
new='''// Compute20 modes on each axis; retain the exact400-term reduction topology.
type Mode=(F64,F64,F64);
fn axis_modes(x:F64,start:N32,count:N32)->Tree[Mode]{
 if count==1 {let m=(2*start+1) as F64;let mp=m*F64::pi;Tree::Leaf((m,mp,(mp*(x+0.5[F64])).sin_bounded()))}
 else{let half=count/2;Tree::Branch(axis_modes(x,start,half),axis_modes(x,start+half,count-half))}
}
fn mode_at(t:Tree[Mode],i:N32,n:N32)->Mode{match t{
 Tree::Empty(){unreachable!()}Tree::Leaf(p){p}Tree::Branch(l,r){let half=n/2;if i<half {mode_at(l,i,half)}else{mode_at(r,i-half,n-half)}}
}}
fn cached_terms(xs:Tree[Mode],ys:Tree[Mode],start:N32,count:N32)->Tree[F64]{
 if count==1 {let(m,mp,sx)=mode_at(xs,start/20,20);let(l,lp,sy)=mode_at(ys,start%20,20);let pi=F64::pi;
 Tree::Leaf(-32.0[F64]*25.0[F64]/(m*l*(pi*pi))/(mp*mp+lp*lp)*sx*sy)
 }else{let half=count/2;Tree::Branch(cached_terms(xs,ys,start,half),cached_terms(xs,ys,start+half,count-half))}
}
fn pressure_terms(x:F64,y:F64,start:N32,count:N32)->Tree[F64]{cached_terms(axis_modes(x,0,20),axis_modes(y,0,20),start,count)}

'''.replace('unreachable!()','debug::error("invalid mode index");(0.0[F64],0.0[F64],0.0[F64])')
p.write_text(s[:a]+new+s[b:])
