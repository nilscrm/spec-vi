#!/usr/bin/env python3
"""Validate the native driver, inclusive steps and original output column semantics.
The separate physics gate retains complete all-field, per-stage validation.
"""
import argparse,json,math,sys
from pathlib import Path
from evaluate import ROOT,run,write_json,tree_hash,sha,compare,parse_stats
from stage_reference import load_fields,FIELDS
from toolchain import verify
LIB=ROOT/'benchmarks/sph-exa/vine'
SOURCE=ROOT/'benchmarks/sph-exa/app/square_patch.vi'

def expected_dump(fields):
    indices=[FIELDS.index(f) for f in 'x y z vx vy vz h ro u p c grad_P_x grad_P_y grad_P_z'.split()]
    result=[]
    for p in fields:
        x,y,z=p[:3];vx,vy,vz=p[6:9]
        radius=math.sqrt(x*x+y*y+z*z)
        result.append([p[i] for i in indices]+[radius,(vx*x+vy*y+vz*z)/radius])
    return result

def table(path,rows):
    path.write_text(''.join(' '.join(format(x,'.17e') for x in row)+'\n' for row in rows))

def validate_case(case,ref,side,last,frequency,policy):
    expected=case/'expected';expected.mkdir()
    constants=[];checks=[]
    names={'constants.txt'}
    for step in range(last+1):
        fields=load_fields(ref/f'side{side}'/f'i{step}-energy.tsv',side**3)
        meta=list(map(float,(ref/f'side{side}'/f'i{step}-energy.meta').read_text().split()))
        nn=sum(len(l.split())-1 for l in (ref/f'side{side}'/f'i{step}-neighbors.tsv').read_text().splitlines())
        constants.append([step,meta[0],fields[0][FIELDS.index('dt')],*meta[1:4],nn])
        if frequency>0 and step%frequency==0:
            name=f'dump{step}.txt';names.add(name);table(expected/name,expected_dump(fields))
            checks.append({'file':name,**compare(expected/name,case/name,policy['atol'],policy['rtol'],side**3,16)})
    table(expected/'constants.txt',constants)
    checks.append({'file':'constants.txt',**compare(expected/'constants.txt',case/'constants.txt',policy['atol'],policy['rtol'],last+1,7)})
    actual={p.name for p in case.glob('*.txt')}
    if actual!=names:raise ValueError(f'Wrong driver output files: {actual} != {names}')
    rows=[[float(x) for x in l.split()] for l in (case/'constants.txt').read_text().splitlines()]
    if any(r[0]!=i or r[6]!=constants[i][6] for i,r in enumerate(rows)):raise ValueError('Iteration or neighbor count differs')
    if not all(c['passed'] for c in checks):raise ValueError('Driver numerical mismatch')
    return checks

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--reference',required=True);args=ap.parse_args()
    out=Path(args.output).resolve();out.mkdir(parents=True);ref=Path(args.reference).resolve()
    policy=json.loads((ROOT/'evaluations/sph-exa/physics-policy.json').read_text())
    report={'passed':False,'port_complete':False,'scope':'Upstream serial CLI and output semantics; native decimal precision, no SPEC equivalence claim','policy':policy,'pin':verify(),'library':tree_hash(LIB),'driver_sha256':sha(SOURCE),'cases':[]}
    try:
        original=json.loads((ref/'result.json').read_text())
        if not original['reference_verified'] or original['policy']!=policy or original['source_sha256']!=sha(ROOT/'benchmarks/sph-exa/reference/stages.cpp'):raise ValueError('Reference provenance mismatch')
        for name,digest in original['snapshots'].items():
            if sha(ref/name)!=digest:raise ValueError('Oracle changed')
        for side,last,freq in [(12,0,1),(16,2,2),(12,0,-1)]:
            case=out/f'side{side}_s{last}_w{freq}';case.mkdir()
            command=[sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(LIB),'--heap','2G',str(SOURCE),'--','-n',str(side),'-s',str(last),'-w',str(freq)]
            r=run(command,case,case/'run',policy['command_timeout_seconds'])
            checks=validate_case(case,ref,side,last,freq,policy)
            stats=parse_stats(Path(r['stderr']).read_text(),require_depth=False)
            if stats['heap_bytes']>policy['heap_limit_bytes']:raise ValueError('Heap limit exceeded')
            report['cases'].append({'side':side,'last_step':last,'frequency':freq,'checks':checks,'stats':stats,'process':r});write_json(out/'progress.json',report)
        if sha(SOURCE)!=report['driver_sha256'] or tree_hash(LIB)!=report['library']:raise ValueError('Sources changed during validation')
        report['passed']=True
    except Exception as exc:report['error']=str(exc)
    write_json(out/'result.json',report);print(json.dumps({k:v for k,v in report.items() if k not in ('pin','library','cases')},indent=2));return 0 if report['passed'] else 1
if __name__=='__main__':sys.exit(main())
