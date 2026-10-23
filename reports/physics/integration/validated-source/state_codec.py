"""Lossless full-state transport: binary64 bits, never a substitute checksum."""
import math
import struct
from stage_reference import FIELDS


def decode_values(words, count):
    if len(words)!=2*count: raise ValueError('Wrong binary64 field count')
    halves=[int(x) for x in words]
    if any(x<0 or x>0xffffffff for x in halves): raise ValueError('Invalid binary64 half')
    values=[struct.unpack('<d',struct.pack('<II',*halves[i:i+2]))[0] for i in range(0,len(halves),2)]
    if not all(map(math.isfinite,values)): raise ValueError('Nonfinite state')
    return values


def emit_values(expressions):
    return ''.join('let N64(lo,hi)=('+e+').to_bits();io.print(" {lo} {hi}");' for e in expressions)


def vine_state_dump():
    return '''fn dump_particles(t:Tree[physics::Particle],start:N32,count:N32,&io:&IO){
 match t{Tree::Empty(){}Tree::Leaf(p){io.print("P {start}");'''+emit_values(['p.'+f for f in FIELDS])+'''io.println("");}
 Tree::Branch(l,r){let half=count/2;dump_particles(l,start,half,&io);dump_particles(r,start+half,count-half,&io);}}
}
fn snapshot(name:String,s:evolution::State,&io:&IO){io.println("STAGE {name}");dump_particles(s.data,0,s.n,&io);io.print("META");'''+emit_values(['s.'+f for f in ['ttot','etot','ecin','eint','bounds.xmin','bounds.xmax','bounds.ymin','bounds.ymax','bounds.zmin','bounds.zmax']])+'''io.println("");}
fn dump_ids(t:Tree[N32],&io:&IO){match t{Tree::Empty(){}Tree::Leaf(i){io.print(" {i}");}Tree::Branch(l,r){dump_ids(l,&io);dump_ids(r,&io);}}}
fn dump_neighbors(rows:evolution::Rows,&io:&IO){match rows{Tree::Empty(){}Tree::Leaf((i,ns)){io.print("N {i}");dump_ids(ns,&io);io.println("");}Tree::Branch(l,r){dump_neighbors(l,&io);dump_neighbors(r,&io);}}}
'''
