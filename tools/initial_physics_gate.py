#!/usr/bin/env python3
"""Progress evaluator for runtime initialization -> grid -> density/rest -> EOS.
Does not accept the full physics milestone or waive neighbor performance checks.
"""
import argparse
import json
import math
from pathlib import Path
import struct
import sys
from evaluate import ROOT, run, write_json, sha, tree_hash, compare, parse_stats, add_resource_args, resources
from pilot_gate import add_tree, balanced, lit
from stage_reference import FIELDS, load_fields, verify_reference
from toolchain import verify
LIB=ROOT/'benchmarks/sph-exa/vine'
HEADER='use #sph::{physics,pilot,tree};\nuse tree::Tree;\n'
DUMP='''fn dump(t:Tree[(N32,physics::Particle)],&io:&IO) {
 match t {Tree::Empty(){} Tree::Leaf((i,p)){io.println("{i} '''+' '.join('{p.'+f+'}' for f in FIELDS)+'''");}
 Tree::Branch(l,r){dump(l,&io);dump(r,&io);}}
}
'''
CONSUMER='fn value(p:physics::Particle)->F64 {'+add_tree(['p.'+f for f in FIELDS])+'}\n'


def driver(path, side, stage, count=None, depth=False):
    n=side**3; count=n if count is None else count
    if stage=='init':
        body=f'let data=physics::initialize(side,0,{n});let i=0;let output=tree::map(data,fn*(p:physics::Particle){{let id=i;i+=1;(id,p)}});'
    else:
        body=f'let output=physics::initial_stages(side,0,{count},{dict(density=1,rest=2,eos=3)[stage]});'
    if depth:
        consume='let total=tree::sum(tree::map(output,fn*((_,p)){value(p)}));let N64(lo,hi)=total.to_bits();io.println("{lo} {hi}");'
    else: consume='dump(output,&io);'
    path.write_text(HEADER+DUMP+CONSUMER+f'pub fn main(&io:&IO){{let side=black_box({side});'+body+consume+'}\n')


def eos_driver(path, rows):
    # Original upstream rest-state inputs; an isolated stage check, not evolution.
    source=balanced(rows,lambda p:'('+','.join(lit(x) for x in p)+')')
    body='let data=black_box('+source+');let i=0;let output=tree::map(data,fn*(p:pilot::Particle){let id=i;i+=1;(id,physics::eos(physics::from_pilot(p)))});dump(output,&io);'
    path.write_text(HEADER+DUMP+'pub fn main(&io:&IO){'+body+'}\n')


def check_checksum(path, rows, policy):
    lo,hi=map(int,Path(path).read_text().split())
    got=struct.unpack('<d',struct.pack('<II',lo,hi))[0]
    want=math.fsum(v for row in rows for v in row)
    if not math.isfinite(got) or abs(got-want)>policy['atol']*len(rows)*30+policy['rtol']*abs(want):
        raise ValueError('Full-state checksum mismatch')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--reference',required=True)
    add_resource_args(ap,600);args=ap.parse_args();out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=True)
    ref=Path(args.reference).resolve();policy=json.loads((ROOT/'evaluations/sph-exa/physics-policy.json').read_text())
    report={'milestone':'initial_physics','passed':False,'full_physics_accepted':False,'port_complete':False,'resources':resources(args),
            'correctness':[],'experiments':[],'scope':'All particles initialization through EOS at iteration zero; isolated EOS from three upstream updates; no IAD or full Vine update validation'}
    try:
        pin=verify();verify_reference(ref,policy)
        if tree_hash(ROOT/'upstream/sph-exa')!=json.loads((ROOT/'evaluations/upstream-files.json').read_text()): raise ValueError('Upstream changed')
        write_json(out/'provenance.json',{'pin':pin,'library':tree_hash(LIB),'policy':policy,'gate_sha256':sha(Path(__file__)), 'reference_report_sha256':sha(ref/'result.json')})
        argv=[sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib','sph='+str(LIB),'--heap',f'{args.heap_gib}G']
        for side in policy['sides']:
            case=ref/f'side{side}'
            for stage in ['init','density','rest','eos']:
                name=f'side{side}_{stage}';src=out/(name+'.vi');driver(src,side,stage)
                r=run(argv+[str(src)],ROOT,out/name,args.timeout)
                expected=case/('init.tsv' if stage=='init' else f'i0-{stage}.tsv')
                load_fields(r['stdout'],side**3)
                check=compare(expected,r['stdout'],policy['atol'],policy['rtol'],side**3,31)
                report['correctness'].append(dict(case=name,**check));write_json(out/'progress.json',report)
                if not check['passed']: raise ValueError('Integrated stage differs: '+name)
            for iteration in range(policy['updates']):
                rows=load_fields(case/f'i{iteration}-rest.tsv',side**3)
                name=f'side{side}_eos_snapshot{iteration}';src=out/(name+'.vi');eos_driver(src,rows)
                r=run(argv+[str(src)],ROOT,out/name,args.timeout)
                load_fields(r['stdout'],side**3)
                check=compare(case/f'i{iteration}-eos.tsv',r['stdout'],policy['atol'],policy['rtol'],side**3,31)
                report['correctness'].append(dict(case=name,**check));write_json(out/'progress.json',report)
                if not check['passed']: raise ValueError('Isolated EOS differs: '+name)
            rows=load_fields(case/'i0-eos.tsv',side**3)
            for count in policy['depth_query_counts']:
                name=f'side{side}_q{count}_depth';src=out/(name+'.vi');driver(src,side,'eos',count,True)
                r=run(argv+['--depth',str(src)],ROOT,out/name,args.timeout)
                check_checksum(r['stdout'],rows[:count],policy)
                stats=parse_stats(Path(r['stderr']).read_text())
                report['experiments'].append(dict(side=side,queries=count,all_input_particles=side**3,**stats,peak_rss_bytes=r['peak_rss_bytes']))
                write_json(out/'progress.json',report)
            name=f'side{side}_workers2'
            r=run(argv+['--workers','2',str(src)],ROOT,out/name,args.timeout)
            check_checksum(r['stdout'],rows[:count],policy)
            report.setdefault('parallel_runs',[]).append(dict(side=side,queries=count,process_seconds=r['wall_seconds'],runtime_log=r['stderr']))
        report['passed']=True
    except Exception as exc: report['error']=str(exc)
    write_json(out/'result.json',report);print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__':sys.exit(main())
