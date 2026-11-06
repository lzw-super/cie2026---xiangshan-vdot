#!/usr/bin/env python3
"""Generate semantically equivalent RVV/vdot tests and paired loop benchmarks."""
from pathlib import Path
import json
import program as m
here=Path(__file__).resolve().parent
m.BUILD=here/'build';m.BUILD.mkdir(exist_ok=True)
# Standard RVV: zero destination full-width, signed widening multiplication,
# widen the reduction again (16 -> 32), then restore exactly e8/m1/VL8/tu/mu.
BASE='''vmv1r.v v3, v6
vwmul.vv v4, v1, v2
vsetivli zero, 8, e16, m2, tu, mu
vwredsum.vs v3, v4, v6
vsetivli zero, 8, e8, m1, tu, mu'''
ZERO='''vsetivli zero, 4, e32, m1, tu, mu
vmv.v.i v6, 0
vsetivli zero, 8, e8, m1, tu, mu'''
# All directed boundaries plus 32 random cases from the unchanged stage2 corpus.
records=json.loads((here/'fixtures.json').read_text())
p=m.Program('rvv_equivalence')
for i,r in enumerate(records,1):
 p.setup(r['a'],r['b'],i)
 p.emit(ZERO)
 p.emit(f'.globl baseline_{i}\nbaseline_{i}:\n'+BASE)
 p.check(3,m.reference(r['a'],r['b']),i)
 p.emit('csrr t0, vtype\nbnez t0, wrong_config\ncsrr t0, vl\nli t1, 16\nbne t0, t1, wrong_config') # CHECK used e8/m1/VL16
p.save()
for n in [1,32,128]:
 for kind in ['vdot','rvv']:
  p=m.Program(f'bench_{kind}_{n}')
  a=[-128,127,0,1,-1,64,-64,2]+[0xa5]*8
  b=[127,-128,1,-1,1,-64,64,3]+[0x5a]*8
  p.setup(a,b,0)
  p.emit(ZERO) # same setup, registers, inputs and final configuration in both variants
  p.emit(f'li s2, {n}\n.globl kernel_begin\nkernel_begin:')
  p.emit('VDOT 3, 1, 2' if kind=='vdot' else BASE)
  p.emit('addi s2, s2, -1\nbnez s2, kernel_begin\n.globl kernel_end\nkernel_end:')
  # Identical final result checking; no timer CSR used as an unproven OoO barrier.
  p.check(3,m.reference(a,b),1)
  p.emit('csrr t0, vtype\nbnez t0, wrong_config')
  p.save()
print('Generated RVV equivalence (42 cases) and 6 paired benchmarks')
