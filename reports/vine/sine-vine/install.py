from pathlib import Path
import shutil,json,struct
out=Path('reports/vine/sine-vine');root=Path('work/vine-lookup')
shutil.copy2('evaluations/vine-pin.json',out/'pin-before.json')
shutil.copy2('work/bin/vine',out/'vine-host-sine-before')
for src,name in [('root/numeric/F64/F64.vi','F64-before.vi'),('util/src/arithmetic.rs','arithmetic-before.rs')]:shutil.copy2(root/src,out/name)
s=(out/'sph/sine.vi').read_text();s=s[s.index('/// Bounded software sine:',s.index('pub fn sin_balanced')+1):].replace('pub fn sin_horner(x:F64)','pub fn .sin_bounded(x:F64)')
s='''// Bounded sine implemented entirely with visible Vine arithmetic.
// Range reduction uses three nonoverlapping parts of pi/2; kernels use
// degree17 sine and degree18 cosine Taylor polynomials on [-pi/4,pi/4].
// Domain: finite |x|<=128 radians. This is NOT a general F64 sine API.
// Empirically <=1 ULP on2420 independent high-precision vectors; not a
// proof of correct rounding. Tests enforce a4-ULP regression envelope.
// Horner was selected over balanced evaluation by matched depth measurements.
\n'''+s
(root/'root/numeric/F64/sin_bounded.vi').write_text(s)
p=root/'root/numeric/F64/F64.vi';s=p.read_text();a=s.index('  /// Sine of an angle');b=s.index('  pub impl pos:',a);s=s[:a]+s[b:];s=s.replace('  pub mod ln;','  pub mod ln;\n  pub mod sin_bounded;');p.write_text(s)
p=root/'util/src/arithmetic.rs';s=p.read_text().replace('      Fn("vi:f64:sin", |a: f64| a.sin()),\n','');p.write_text(s)
p=Path('benchmarks/sph-exa/vine/pilot.vi');s=p.read_text().replace('.sin()', '.sin_bounded()');s=s.replace('// Terms are split','// Initialization has x+0.5,y+0.5 in [0,1] and odd modes <=39:\n// sine arguments are bounded by39*pi<128, the explicit software API domain.\n// Terms are split');p.write_text(s)
vectors=json.loads((out/'vectors.json').read_text())['vectors']
def u(x):return struct.unpack('<Q',struct.pack('<d',x))[0]
lines=['pub fn main(&io:&IO){','let pairs=black_box([' ]
lines += [f'({u(x)}[N64],{u(y)}[N64]),' for x,y in vectors]
lines += [']);for (x,w) in pairs {let a=F64::from_bits(x).sin_bounded().to_bits();let d=if a>=w {a-w}else{w-a};assert d<=4[N64] else {debug::error("sine ULP regression")}}',
'assert F64::from_bits(0x8000000000000000[N64]).sin_bounded().to_bits()==0x8000000000000000[N64] else {debug::error("negative zero")}',
'assert 0.0[F64].sin_bounded().to_bits()==0[N64] else {debug::error("positive zero")}',
'let p=F64::inf.sin_bounded();let n=F64::neg_inf.sin_bounded();let a=F64::nan.sin_bounded();assert (p!=p)&(n!=n)&(a!=a) else {debug::error("nonfinite")}', 'io.println("passed");}']
(root/'tests/programs/f64_sin.vi').write_text('\n'.join(lines)+'\n')
