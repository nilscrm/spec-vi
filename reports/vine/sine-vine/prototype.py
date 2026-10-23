"""Pure Vine bounded sine; independent 100-digit Decimal Taylor oracle.
No host sin supplies expected values. Inputs include every SPH coordinate/mode
for sides12/16, reduction boundaries, endpoint neighbors and deterministic randoms.
"""
import sys,json,math,random,struct,decimal,shutil
from pathlib import Path
sys.path.insert(0,'tools')
from evaluate import ROOT,run,parse_stats,write_json
from pilot_gate import balanced
out=ROOT/'reports/vine/sine-vine';lib=out/'sph';lib.mkdir(exist_ok=True)
shutil.copy2(ROOT/'benchmarks/sph-exa/vine/tree.vi',lib/'tree.vi');(lib/'sph.vi').write_text('pub mod tree;pub mod sine;\n')
D=decimal.Decimal;decimal.getcontext().prec=110
# Chudnovsky series, independently computes pi to over100 decimal digits.
m=1;l=13591409;x=1;k=6;total=D(l)
for i in range(1,10):
 m=m*(k*k*k-16*k)//(i*i*i);l+=545140134;x*=-262537412640768000;total+=D(m*l)/D(x);k+=12
pi=426880*D(10005).sqrt()/total

def oracle(x):
 a=D.from_float(x);a=a%(2*pi)
 if a>pi:a-=2*pi
 if a<-pi:a+=2*pi
 term=a;s=a
 for k in range(1,160):
  term *= -a*a/D((2*k)*(2*k+1));s+=term
  if abs(term)<D('1e-105'):break
 return float(s)

def poly(cs,mode):
 vals=[format(c,'.17e')+'[F64]' for c in cs]
 if mode=='horner':
  expr=vals[-1]
  for v in vals[-2::-1]:expr=f'({v}+z*{expr})'
  return expr
 pairs=[f'({vals[i]}+z*{vals[i+1]})' for i in range(0,8,2)]
 return f'(({pairs[0]}+z2*{pairs[1]})+z4*({pairs[2]}+z2*{pairs[3]}))'
sin_cs=[(-1)**(k+1)/math.factorial(2*k+3) for k in range(8)]
cos_cs=[(-1)**k/math.factorial(2*k+4) for k in range(8)]
sources=[]
for mode in ['balanced','horner']:
 sources.append('''
/// Bounded software sine: finite |x|<=128; NaN/infinity ->NaN; signed zero preserved.
/// No promise of correct rounding. Out-of-domain finite inputs fail explicitly.
pub fn sin_MODE(x:F64)->F64 {
 if x!=x {return x;}
 let neg=x<0.0[F64];let a=if neg {-x}else{x};
 if a==F64::inf {return F64::nan;}
 assert a<=128.0[F64] else {debug::error("sin_bounded requires |x| <= 128")}
 if a<7.450580596923828125e-9[F64] {return x;}
 let n=(a*0.63661977236758134308[F64]+0.5[F64]) as N32;let nf=n as F64;
 let r=a-nf*1.57079632673412561417[F64];
 let t=nf*6.07710050630396597660e-11[F64];
 let y=r-t;let tail=((r-y)-t)-nf*2.02226624879595063154e-21[F64];
 let z=y*y;let z2=z*z;let z4=z2*z2;
 let sp=SINPOLY;let cp=COSPOLY;
 let s=y+(y*z)*sp;let c=(1.0[F64]-0.5[F64]*z)+(z*z)*cp;
 let v=if (n&1)==0 {s+tail*c}else{c-tail*s};
 let v=if (n&2)==0 {v}else{-v};if neg {-v}else{v}
}
'''.replace('MODE',mode).replace('SINPOLY',poly(sin_cs,mode)).replace('COSPOLY',poly(cos_cs,mode)))
(lib/'sine.vi').write_text(''.join(sources))
values={0.0,128.0,-128.0,2**-1074,-2**-1074,2**-1022,-2**-1022}
for k in range(-81,82):
 v=float(D(k)*pi/2)
 values.update([v,math.nextafter(v,-math.inf),math.nextafter(v,math.inf)])
for k in range(-162,163):
 v=float(D(k)*pi/4)
 if abs(v)<=128:values.update([v,math.nextafter(v,-math.inf),math.nextafter(v,math.inf)])
for side in [12,16]:
 for i in range(side):
  x=-0.5+1.0/(2.0*side)+i*1.0/side
  for m in range(1,40,2):values.add((m*math.pi)*(x+0.5))
rng=random.Random(67021);values.update(rng.uniform(-128,128) for _ in range(1024))
values=sorted(x for x in values if abs(x)<=128);vectors=[(x,oracle(x)) for x in values]
write_json(out/'vectors.json',{'oracle':'Decimal110 Chudnovsky pi and Taylor sine','vectors':vectors})
header='''use #sph::{tree,sine};use tree::Tree;
fn dump(t:Tree[F64],&io:&IO){match t{Tree::Empty(){}Tree::Leaf(x){let N64(lo,hi)=x.to_bits();io.println("{lo} {hi}");}Tree::Branch(l,r){dump(l,&io);dump(r,&io);}}}
fn sum(t:Tree[F64])->N32{match t{Tree::Empty(){0}Tree::Leaf(x){let N64(a,b)=x.to_bits();a+b}Tree::Branch(l,r){sum(l)+sum(r)}}}
'''
results={}
for mode in ['balanced','horner']:
 p=out/f'{mode}_correctness.vi';p.write_text(header+'pub fn main(&io:&IO){let t=black_box('+balanced(values,lambda x:format(x,'.17e')+'[F64]')+');dump(tree::map(t,fn*(x:F64)->F64 {sine::sin_'+mode+'(x)}),&io);}\n')
 r=run([sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(lib),str(p)],ROOT,p.with_suffix(''),180)
 got=[struct.unpack('<d',struct.pack('<II',*map(int,row.split())))[0] for row in Path(r['stdout']).read_text().splitlines()]
 assert len(got)==len(vectors)
 def ordered(x):
  u=struct.unpack('<Q',struct.pack('<d',x))[0];return (~u)&((1<<64)-1) if u>>63 else u|(1<<63)
 errors=[abs(ordered(a)-ordered(e)) if a!=e else 0 for a,(_,e) in zip(got,vectors)]
 assert max(errors)<=4,(mode,max(errors),vectors[errors.index(max(errors))],got[errors.index(max(errors))])
 results[mode]={'cases':len(values),'max_ulp':max(errors),'metrics':[]};print(mode,len(values),'max ULP',max(errors),flush=True)
 for count in [1,32,256]:
  xs=[values[round(i*(len(values)-1)/max(1,count-1))] for i in range(count)]
  p=out/f'{mode}_n{count}.vi';p.write_text(header+'pub fn main(&io:&IO){let t=black_box('+balanced(xs,lambda x:format(x,'.17e')+'[F64]')+');io.println("{sum(tree::map(t,fn*(x:F64)->F64 {sine::sin_'+mode+'(x)}))}");}\n')
  r=run([sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(lib),'--depth',str(p)],ROOT,p.with_suffix(''),180)
  assert int(Path(r['stdout']).read_text())==sum(sum(struct.unpack('<II',struct.pack('<d',got[values.index(v)]))) for v in xs)%2**32
  metric=dict(count=count,**parse_stats(Path(r['stderr']).read_text()));results[mode]['metrics'].append(metric);print(mode,metric,flush=True)
 write_json(out/'prototype.json',results)
