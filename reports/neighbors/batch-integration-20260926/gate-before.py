#!/usr/bin/env python3
"""Exact membership oracle independent of the candidate spatial representation."""
import argparse
import json
import math
from pathlib import Path
import random
import sys
from evaluate import ROOT, run, write_json, sha, tree_hash, parse_stats
from pilot_gate import balanced, lit, indices
from toolchain import verify

LIB = ROOT/'benchmarks/sph-exa/vine'
POLICY = ROOT/'evaluations/sph-exa/neighbors-policy.json'


def oracle(points, q):
    identity, x, y, z, radius, period = q
    shifts = (0.0, -period, period) if period else (0.0,)
    result = []
    for i, px, py, pz in points:
        dx = x-px; dy = y-py
        if i != identity and any((dx*dx+dy*dy)+(z+shift-pz)*(z+shift-pz) < radius*radius for shift in shifts):
            result.append(i)
    return sorted(result)


def validate_rows(text, expected):
    rows = text.splitlines()
    if len(rows) != len(expected):
        raise ValueError('Neighbor query row count mismatch')
    for n, (row, want) in enumerate(zip(rows, expected)):
        values = list(map(int, row.split()))
        if not values or values[0] != n:
            raise ValueError('Missing or reordered query identity')
        got = values[1:]
        if len(got) != len(set(got)) or sorted(got) != sorted(want):
            raise ValueError(f'Neighbor membership differs at query {n}: missing={sorted(set(want)-set(got))[:16]}, extra={sorted(set(got)-set(want))[:16]}')


def point(p):
    return '{id:'+str(p[0])+',x:'+lit(p[1])+',y:'+lit(p[2])+',z:'+lit(p[3])+'}'


def query(q):
    return '{id:'+str(q[0])+',x:'+lit(q[1])+',y:'+lit(q[2])+',z:'+lit(q[3])+',radius:'+lit(q[4])+',period_z:'+lit(q[5])+'}'


# Trusted baseline: serial point scan, with the same query batch and consumer.
BASELINE = '''
fn inside(p: neighbors::Point, q: neighbors::Query) -> Bool {
  let dx = q.x-p.x; let dy=q.y-p.y; let dz=q.z-p.z;
  let a=q.z-q.period_z-p.z; let b=q.z+q.period_z-p.z;
  p.id != q.id and ((dx*dx+dy*dy)+dz*dz < q.radius*q.radius or
    (q.period_z > 0.0[F64] and ((dx*dx+dy*dy)+a*a < q.radius*q.radius or (dx*dx+dy*dy)+b*b < q.radius*q.radius)))
}
fn scan(t: Tree[neighbors::Point], q: neighbors::Query, total: N32) -> N32 {
 match t {
  Tree::Empty() { total }
  Tree::Leaf(p) { if inside(p,q) { total+p.id+1 } else { total } }
  Tree::Branch(l,r) { scan(r,q,scan(l,q,total)) }
 }
}
'''


def driver(points, queries, path, mode='correctness', candidate='tree', api=None):
    if candidate not in ('tree','grid'): raise ValueError('Unknown neighbor candidate')
    api = api or ('batch' if candidate=='grid' else 'single')
    if api not in ('single','batch') or (candidate=='tree' and api=='batch'): raise ValueError('Unsupported neighbor API')
    module = 'grid' if candidate=='grid' else 'neighbors'
    s='use #sph::{neighbors,tree};\nuse tree::Tree;\n'
    s+='''fn sum(t: Tree[N32]) -> N32 {
 match t { Tree::Empty() { 0 } Tree::Leaf(v) { v+1 } Tree::Branch(l,r) { sum(l)+sum(r) } }
}
fn dump(t: Tree[N32], &io: &IO) {
 match t { Tree::Empty() {} Tree::Leaf(v) { io.print(" {v}"); } Tree::Branch(l,r) { dump(l,&io); dump(r,&io); } }
}
fn emit(t: Tree[(N32,Tree[N32])], &io: &IO) {
 match t { Tree::Empty() {} Tree::Leaf((i,v)) { io.print("{i}"); dump(v,&io); io.println(""); } Tree::Branch(l,r) { emit(l,&io);emit(r,&io); } }
}
fn totals(t: Tree[N32]) -> N32 {
 match t { Tree::Empty() {0} Tree::Leaf(v) {v} Tree::Branch(l,r) {totals(l)+totals(r)} }
}
'''
    if candidate=='grid' and mode!='serial': s+='use #sph::grid;\n'
    if mode=='serial': s+=BASELINE
    s+='pub fn main(&io: &IO) {\nlet points=black_box('+balanced(points,point)+');\n'
    s+='let queries=black_box('+balanced(list(enumerate(queries)),lambda iq:'('+str(iq[0])+','+query(iq[1])+')')+');\n'
    if mode=='serial':
        s+='let output=tree::map(queries,fn* ((_,q)) {scan(points,q,0)});\nio.println("{totals(output)}");\n'
    else:
        s+=f'let index={module}::build(points);\n'
        if api=='batch': s+=f'let output={module}::find_batch(index,queries);\n'
        else: s+='let output=tree::map(queries,fn* ((i,q)) {(i,'+module+'::find(index,q))});\n'
        s+= 'emit(output,&io);\n' if mode=='correctness' else 'let sums=tree::map(output,fn* ((_,v)) {sum(v)});io.println("{totals(sums)}");\n'
    path.write_text(s+'}\n')


def synthetic():
    yield 'empty', [], [(9,0.,0.,0.,1.,0.)]
    yield 'strict_boundary', [(0,0.,0.,0.),(1,1.,0.,0.),(2,math.nextafter(1.,0.),0.,0.),(3,math.nextafter(1.,2.),0.,0.),(4,0.,0.,0.)], [(0,0.,0.,0.,1.,0.),(0,0.,0.,0.,0.,0.)]
    points=[(0,0.,0.,.1),(1,0.,0.,9.9),(2,0.,0.,5.),(3,9.9,0.,.1)]
    yield 'periodic', points, [(*p,.3,10.) for p in points]
    rng=random.Random(7604)
    points=[(i, rng.gauss(0 if i%2 else 8,.3),rng.gauss(0,.3),rng.gauss(0,.3)) for i in range(128)]
    rng.shuffle(points)
    yield 'clusters_shuffled',points,[(*p,.65,0.) for p in points[::8]]
    for n in (64,256):
        points=[(i,float(i%8),float(i//8%8),float(i//64)) for i in range(n)]
        rng.shuffle(points)
        yield f'scaling_{n}',points,[(*p,1.1,0.) for p in points]


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--candidate',choices=('tree','grid'),default='tree');args=ap.parse_args()
    output=Path(args.output).resolve();output.mkdir(parents=True,exist_ok=True)
    p=json.loads(POLICY.read_text());report={'milestone':'neighbors','passed':False,'port_complete':False,'scope':p['scope'],'candidate':args.candidate,'api':'batch' if args.candidate=='grid' else 'single','correctness':[],'experiments':[]}
    try:
        pin=verify()
        if tree_hash(ROOT/'upstream/sph-exa') != json.loads((ROOT/'evaluations/upstream-files.json').read_text()):
            raise RuntimeError('Upstream source changed')
        write_json(output/'provenance.json',{'policy_sha256':sha(POLICY),'candidate':tree_hash(LIB),'vine_binary':pin['binary_sha256'],'selected_candidate':args.candidate,'extra_fixtures_sha256':sha(ROOT/'evaluations/sph-exa/neighbors-extra.json')})
        cases=list(synthetic())
        reference=ROOT/'work/build/neighbors_reference'
        run(['c++','-std=c++14','-O2','-ffp-contract=off','-DNDEBUG','-Wno-unknown-pragmas','-I'+str(ROOT/'upstream/sph-exa/src'),'-I'+str(ROOT/'upstream/sph-exa/src/include'),str(ROOT/'benchmarks/sph-exa/reference/pilot.cpp'),'-o',str(reference)],ROOT,output/'build-reference')
        for side in p['sides']:
            r=run([str(reference),str(side),'density'],ROOT,output/f'upstream_{side}')
            rows=[[float(v) for v in line.split()] for line in Path(r['stdout']).read_text().splitlines()]
            points=[(int(r[0]),*r[1:4]) for r in rows]
            selected=[rows[i] for i in indices(len(rows),p['queries_per_side'])]
            queries=[(int(r[0]),*r[1:4],2*r[4],r[8]) for r in selected]
            for q,row in zip(queries,selected):
                upstream=[int(row[9+j*5]) for j in range(int(row[7]))]
                if sorted(upstream)!=oracle(points,q):
                    raise RuntimeError(f'Upstream and brute-force oracle disagree: side={side}, id={q[0]}')
            cases.append((f'upstream_{side}',points,queries))
        for case in json.loads((ROOT/'evaluations/sph-exa/neighbors-extra.json').read_text()):
            if case['expected'] != [oracle(case['points'],q) for q in case['queries']]: raise RuntimeError('Extra fixture oracle mismatch')
            cases.append(('extra_'+case['name'],case['points'],case['queries']))
        write_json(output/'fixtures.json',[{'name':name,'points':pts,'queries':qs,'expected':[oracle(pts,q) for q in qs]} for name,pts,qs in cases])
        for name,points,queries in cases:
            expected=[oracle(points,q) for q in queries]
            argv=[sys.executable,str(ROOT/'tools/vine_exec.py'),'run','--lib',f'sph={LIB}','--heap','2G']
            checks=[('tree','single')]+([('grid','single'),('grid','batch')] if args.candidate=='grid' else [])
            for candidate,api in checks:
                label=name+'_'+candidate+'_'+api
                src=output/(label+'.vi');driver(points,queries,src,candidate=candidate,api=api)
                r=run(argv+[str(src)],ROOT,output/(label+'_correctness'),p['command_timeout_seconds'])
                validate_rows(Path(r['stdout']).read_text(),expected)
                report['correctness'].append({'case':name,'candidate':candidate,'api':api,'queries':len(queries),'passed':True})
                write_json(output/'progress.json',report)
            if name.startswith('scaling_'):
                entry={'count':len(points)}
                for mode in ('candidate','serial'):
                    src=output/(name+'_'+mode+'.vi');driver(points,queries,src,mode,candidate=args.candidate)
                    r=run(argv+['--depth',str(src)],ROOT,output/(name+'_'+mode),p['command_timeout_seconds'])
                    if int(Path(r['stdout']).read_text())!=sum(i+1 for row in expected for i in row):
                        raise RuntimeError('Depth consumer checksum mismatch')
                    stats=parse_stats(Path(r['stderr']).read_text())
                    if stats['heap_bytes']>p['heap_limit_bytes']: raise RuntimeError('Heap budget exceeded')
                    entry[mode]=dict(stats,peak_rss_bytes=r['peak_rss_bytes'])
                report['experiments'].append(entry)
                src=output/(name+'_candidate.vi')
                r=run(argv+['--workers','2',str(src)],ROOT,output/(name+'_workers2'),p['command_timeout_seconds'])
                if int(Path(r['stdout']).read_text())!=sum(i+1 for row in expected for i in row): raise RuntimeError('Parallel checksum mismatch')
                entry['parallel_process_seconds']=r['wall_seconds']
                entry['parallel_runtime_log']=r['stderr']
                write_json(output/'progress.json',report)
        first,last=report['experiments']
        if last['candidate']['depth']>p['max_depth_ratio']*last['serial']['depth']: raise RuntimeError('Insufficient depth improvement over serial scan')
        if last['candidate']['interactions']>p['max_work_ratio']*last['serial']['interactions']: raise RuntimeError('Work amplification exceeds budget')
        if last['candidate']['interactions']>p['max_work_growth']*first['candidate']['interactions']: raise RuntimeError('Build/query work scaling exceeds budget')
        if last['candidate']['depth']>p['max_depth_growth']*first['candidate']['depth']: raise RuntimeError('Depth scaling exceeds budget')
        report['passed']=True
    except Exception as exc: report['error']=str(exc)
    write_json(output/'result.json',report);print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__': sys.exit(main())
