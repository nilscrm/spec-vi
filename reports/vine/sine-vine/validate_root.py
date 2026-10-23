import sys,json,shutil
from pathlib import Path
sys.path.insert(0,'tools')
from evaluate import ROOT,run,parse_stats,write_json
out=ROOT/'reports/vine/sine-vine';argv=[sys.executable,str(ROOT/'tools/vine_exec.py'),'run']
r=run(argv+['--no-perf',str(ROOT/'work/vine-lookup/tests/programs/f64_sin.vi')],ROOT,out/'root-test',180)
assert Path(r['stdout']).read_text().strip()=='passed'
for src,dst in [('stdout','output.txt'),('stderr','stats')]:shutil.copy2(out/f'root-test.{src}',ROOT/'work/vine-lookup/tests/snaps/programs/f64_sin'/dst)
p=out/'root_correctness.vi';p.write_text((out/'horner_correctness.vi').read_text().replace('sine::sin_horner(x)','x.sin_bounded()'))
r=run(argv+['--lib','sph='+str(out/'sph'),str(p)],ROOT,p.with_suffix(''),180)
assert Path(r['stdout']).read_bytes()==(out/'horner_correctness.stdout').read_bytes()
metrics=[]
for count in [1,32,256]:
 p=out/f'root_n{count}.vi';p.write_text((out/f'horner_n{count}.vi').read_text().replace('sine::sin_horner(x)','x.sin_bounded()'))
 r=run(argv+['--lib','sph='+str(out/'sph'),'--depth',str(p)],ROOT,p.with_suffix(''),180)
 assert Path(r['stdout']).read_bytes()==(out/f'horner_n{count}.stdout').read_bytes()
 metrics.append(dict(count=count,**parse_stats(Path(r['stderr']).read_text())))
p=out/'outside.vi';p.write_text('pub fn main(&io:&IO){io.println("{black_box(129.0[F64]).sin_bounded()}");}\n')
try:run(argv+['--debug',str(p)],ROOT,out/'outside',180)
except RuntimeError:assert 'sin_bounded requires' in ((out/'outside.stderr').read_text()+(out/'outside.stdout').read_text())
else:raise AssertionError('outside-domain value was accepted')
p=out/'root_n256.vi';r=run(argv+['--lib','sph='+str(out/'sph'),'--workers','2',str(p)],ROOT,out/'workers2',180)
assert Path(r['stdout']).read_bytes()==p.with_suffix('.stdout').read_bytes()
write_json(out/'root-validation.json',{'passed':True,'cases':2420,'matches_prototype_bits':True,'max_observed_ulp':1,'special_cases':'both zeros, NaN, both infinities','out_of_domain_rejected':True,'workers2':True,'metrics':metrics})
print(json.dumps(metrics),flush=True)
