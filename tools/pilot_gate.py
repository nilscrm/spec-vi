#!/usr/bin/env python3
"""Independent pilot gate: C++ fixtures, numerical comparison, work/depth experiments."""
import argparse
import json
import math
from pathlib import Path
import struct
import sys
from evaluate import ROOT, run, write_json, compare, parse_stats, sha, tree_hash
from toolchain import verify

POLICY = ROOT/'evaluations/sph-exa/pilot-policy.json'
LIB = ROOT/'benchmarks/sph-exa/vine'
BIN = ROOT/'work/bin/vine'


def balanced(items, leaf=lambda x:x):
    if not items: return 'Tree::Empty()'
    if len(items)==1: return 'Tree::Leaf('+leaf(items[0])+')'
    mid=len(items)//2
    return 'Tree::Branch('+balanced(items[:mid],leaf)+','+balanced(items[mid:],leaf)+')'


def add_tree(items):
    if len(items)==1: return items[0]
    mid=len(items)//2
    return '('+add_tree(items[:mid])+' + '+add_tree(items[mid:])+')'


def lit(x):
    return format(float(x), '.17e')+'[F64]'


def indices(n, count):
    return sorted(set([round(i*(n-1)/(count-1)) for i in range(count)])) if count>1 else [n//2]


def density_input(row):
    i,x,y,z,h,m,expected,nn,period_z,*rest=row
    center='{ x:'+lit(x)+', y:'+lit(y)+', z:'+lit(z)+', h:'+lit(h)+', m:'+lit(m)+', period_z:'+lit(period_z)+' }'
    neighbors=[]
    for j in range(int(nn)):
        _,nx,ny,nz,nm=rest[j*5:(j+1)*5]
        neighbors.append('{ x:'+lit(nx)+', y:'+lit(ny)+', z:'+lit(nz)+', m:'+lit(nm)+' }')
    return '('+center+','+balanced(neighbors)+')'


def make_driver(kind, side, data, path, reduction=True, depth=False):
    mode='true' if reduction else 'false'
    source='use #sph::{pilot, tree};\nuse tree::Tree;\n'
    if kind=='init':
        input_tree=balanced(data,lambda i:str(i))
        call=f'tree::map(input, fn* (i: N32) {{ pilot::initialize(black_box({side}), i, {mode}) }})'
        ty='pilot::Particle'
        checksum=add_tree([f'p.{j}' for j in range(30)])
        line=' '.join('{p.'+str(j)+'}' for j in range(30))
    else:
        input_tree=balanced(data,density_input)
        call=f'tree::map(input, fn* ((center, neighbors)) {{ pilot::density(center, neighbors, {mode}) }})'
        ty='F64';checksum='p';line='{p}'
    if depth:
        source+=f'fn consume(p: {ty}) -> F64 {{ {checksum} }}\n'
        emit='let value = tree::sum(tree::map(output, consume));\nlet N64(lo, hi) = value.to_bits();\nio.println("{lo} {hi}");'
    else:
        source+=f'''fn dump(tree: Tree[{ty}], &io: &IO) {{
  match tree {{
    Tree::Empty() {{}}
    Tree::Leaf(p) {{ io.println("{line}"); }}
    Tree::Branch(l,r) {{ dump(l, &io); dump(r, &io); }}
  }}
}}
'''
        emit='dump(output, &io);'
    source+=f'pub fn main(&io: &IO) {{\nlet input = black_box({input_tree});\nlet output = {call};\n{emit}\n}}\n'
    path.write_text(source)


def run_vine(driver, output, depth, policy):
    argv=[sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib',f'sph={LIB}','--heap','2G']
    argv+=['--depth'] if depth else []
    argv+=[str(driver)]
    return run(argv,ROOT,output,timeout=policy['command_timeout_seconds'])


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args()
    output=Path(args.output).resolve();output.mkdir(parents=True,exist_ok=True)
    p=json.loads(POLICY.read_text())
    report={'milestone':'pilot','passed':False,'port_complete':False,'scope':p['scope'],'correctness':[], 'experiments':[]}
    try:
        verify()
        pinned=json.loads((ROOT/'evaluations/upstream-files.json').read_text())
        if tree_hash(ROOT/'upstream/sph-exa')!=pinned: raise RuntimeError('Upstream source changed')
        reference=ROOT/'work/build/pilot_reference'
        run(['c++','-std=c++14','-O2','-ffp-contract=off','-DNDEBUG','-Wno-unknown-pragmas',
             '-I'+str(ROOT/'upstream/sph-exa/src'),'-I'+str(ROOT/'upstream/sph-exa/src/include'),
             str(ROOT/'benchmarks/sph-exa/reference/pilot.cpp'),'-o',str(reference)],ROOT,output/'build-reference')
        provenance={'policy_sha256':sha(POLICY),'candidate':tree_hash(LIB), 'vine_binary_sha256':sha(BIN),
                    'vine_pin':json.loads((ROOT/'evaluations/vine-pin.json').read_text())}
        write_json(output/'provenance.json',provenance)
        saved={}
        for side in p['sides']:
            for kind in ('init','density'):
                name=f'{kind}_{side}'
                r=run([str(reference),str(side),kind],ROOT,output/(name+'_reference'))
                rows=[[float(v) for v in line.split()] for line in Path(r['stdout']).read_text().splitlines()]
                count=p['initialization_samples_per_side' if kind=='init' else 'density_samples_per_side']
                selected=indices(side**3,count)
                data=selected if kind=='init' else [rows[i] for i in selected]
                expected=[rows[i] if kind=='init' else [rows[i][6]] for i in selected]
                exp=output/(name+'_expected.txt');exp.write_text('\n'.join(' '.join(format(x,'.17e') for x in row) for row in expected)+'\n')
                driver=output/(name+'.vi');make_driver(kind,side,data,driver)
                result=run_vine(driver,output/(name+'_vine'),False,p)
                check=compare(exp,result['stdout'],p['atol'],p['rtol'],count,30 if kind=='init' else 1)
                report['correctness'].append(dict(case=name,**check))
                write_json(output/'progress.json',report)
                if not check['passed']: raise RuntimeError(f'Numerical comparison failed: {name}: {check}')
                saved[(side,kind)]=(data,expected)
        # Both formulations use exactly the same generated inputs and forcing consumer.
        for kind in ('init','density'):
            data,expected=saved[(p['sides'][0],kind)]
            values=[]
            for count in p['depth_counts'][kind]:
                by_mode={}
                for mode in (True,False):
                    name=f'{kind}_n{count}_{"balanced" if mode else "serial"}'
                    driver=output/(name+'.vi');make_driver(kind,p['sides'][0],data[:count],driver,mode,True)
                    r=run_vine(driver,output/name,True,p)
                    stats=parse_stats(Path(r['stderr']).read_text())
                    lo,hi=map(int,Path(r['stdout']).read_text().split())
                    scalar=struct.unpack('<d',struct.pack('<II',lo,hi))[0]
                    oracle=math.fsum(x for row in expected[:count] for x in row)
                    if not math.isfinite(scalar) or abs(scalar-oracle)>p['atol']*count*30+p['rtol']*abs(oracle):
                        raise RuntimeError(f'Depth consumer mismatch: {name}: {scalar} vs {oracle}')
                    if stats['heap_bytes']>p['heap_limit_bytes']: raise RuntimeError('Heap budget exceeded')
                    by_mode['balanced' if mode else 'serial']=stats
                entry={'kind':kind,'count':count,**by_mode}
                report['experiments'].append(entry);values.append(entry)
                write_json(output/'progress.json',report)
            # Parallel runtime is a distinct run: --depth does not execute workers.
            driver=output/(f'{kind}_n{count}_balanced.vi')
            parallel=run([sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib',f'sph={LIB}','--heap','2G','--workers','2',str(driver)],ROOT,output/(kind+'_workers2'),timeout=p['command_timeout_seconds'])
            lo,hi=map(int,Path(parallel['stdout']).read_text().split())
            scalar=struct.unpack('<d',struct.pack('<II',lo,hi))[0]
            oracle=math.fsum(x for row in expected[:count] for x in row)
            if not math.isfinite(scalar) or abs(scalar-oracle)>p['atol']*count*30+p['rtol']*abs(oracle):
                raise RuntimeError('Parallel consumer mismatch')
            report.setdefault('parallel_runs',[]).append({'kind':kind,'workers':2,'process_wall_seconds':parallel['wall_seconds'],'peak_rss_bytes':parallel['peak_rss_bytes'],'runtime_stats':parallel['stderr']})
            last=values[-1]
            if last['balanced']['depth']>p['max_balanced_to_serial_depth']*last['serial']['depth']:
                raise RuntimeError(f'{kind}: insufficient depth improvement')
            if last['balanced']['interactions']>p['max_balanced_to_serial_work']*last['serial']['interactions']:
                raise RuntimeError(f'{kind}: work amplification exceeds budget')
            if last['balanced']['depth']>p['max_depth_growth']*values[0]['balanced']['depth']:
                raise RuntimeError(f'{kind}: depth scaling exceeds budget')
        report['passed']=True
    except Exception as exc:
        report['error']=str(exc)
    write_json(output/'result.json',report)
    print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__':sys.exit(main())
