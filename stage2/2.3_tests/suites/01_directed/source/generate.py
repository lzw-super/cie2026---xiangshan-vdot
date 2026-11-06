#!/usr/bin/env python3
"""Deterministic assembly plus independent scalar reference (no RVV dependency)."""
from pathlib import Path
import json
import random

HERE = Path(__file__).resolve().parent
BUILD = HERE / 'build'
SEED = 20261027
MATCH, MASK = 0xfe000057, 0xfe00707f


def signed8(x):
    x &= 255
    return x - 256 if x & 128 else x


def reference(a, b):
    total = sum(signed8(a[i]) * signed8(b[i]) for i in range(8))
    return list((total & 0xffffffff).to_bytes(4, 'little')) + [0] * 12


def encode(vd, vs1, vs2):
    assert all(0 <= r < 32 for r in (vd, vs1, vs2))
    return MATCH | vs2 << 20 | vs1 << 15 | vd << 7


class Program:
    def __init__(self, name):
        self.name = name
        self.code = ['#include "common.S"', '.globl test_body', 'test_body:']
        self.data = ['.section .data', '.balign 16']
        self.records = []

    def emit(self, text):
        self.code += text.strip().splitlines()

    def blob(self, name, values):
        label = f'data_{self.name}_{name}'
        self.data += ['.balign 16', label + ':', ' .byte ' + ','.join(str(x & 255) for x in values)]
        return label

    def setup(self, a, b, ident, ra=1, rb=2, rd=3, policy='tu, mu'):
        la = self.blob(f'a{ident}', a)
        lb = self.blob(f'b{ident}', b)
        lp = self.blob(f'poison{ident}', [0xa5]*16)
        self.emit(f'vsetivli t0, 16, e8, m1, {policy}\nLOAD v{rd}, {lp}\nLOAD v{ra}, {la}')
        if rb != ra:
            self.emit(f'LOAD v{rb}, {lb}')
        else:
            assert a == b
        self.emit(f'vsetivli t0, 8, e8, m1, {policy}')

    def check(self, rd, values, ident):
        exp = self.blob(f'expected{ident}', values)
        self.emit(f'CHECK v{rd}, {exp}, {ident}')

    def case(self, ident, a, b, rd=3, ra=1, rb=2, policy='tu, mu'):
        self.setup(a,b,ident,ra,rb,rd,policy)
        self.emit(f'.globl target_{ident}\ntarget_{ident}:\nVDOT {rd}, {ra}, {rb}')
        result = reference(a,b)
        self.check(rd,result,ident)
        self.records.append(dict(id=ident, a=a, b=b, vd=rd, vs1=ra, vs2=rb,
                                 instruction=f'{encode(rd,ra,rb):08x}', expected=result))

    def save(self):
        (BUILD / f'{self.name}.S').write_text('\n'.join(self.code + ['j pass'] + self.data) + '\n')
        (BUILD / f'{self.name}.json').write_text(json.dumps(self.records, indent=2)+'\n')


def main():
    BUILD.mkdir(exist_ok=True)
    assert encode(3,1,2) == 0xfe2081d7
    assert reference([-128]*16,[-128]*16)[:4] == [0,0,2,0]
    assert reference([-1]*16,[1]*16) == [248,255,255,255]+[0]*12
    rng = random.Random(SEED)
    def full(low):
        return low + [rng.randrange(256) for _ in range(8)]
    p = Program('00_smoke')
    p.case(1,full(list(range(1,9))),full([1]*8))
    p.save()
    p = Program('01_directed')
    pairs = [([0]*8,[127]*8),([1]*8,[-1]*8),([127]*8,[127]*8),
             ([-128]*8,[-128]*8),([-128]*8,[127]*8),
             ([1,-2,3,-4,5,-6,7,-8],[1]*8),
             ([-128,127,0,1,-1,64,-64,2],[127,-128,1,-1,1,-64,64,3])]
    for i,(a,b) in enumerate(pairs,1):
        p.case(i,full(a),full(b),policy='ta, ma' if i%2 else 'tu, mu')
    # Same low 64 bits, changed high half; output must be identical.
    for i,hi in enumerate((0,255,128),20):
        p.case(i,list(range(8))+[hi]*8,[2]*8+[hi]*8)
    p.save()
    p = Program('02_random')
    for i in range(128):
        p.case(i+1,[rng.randrange(256) for _ in range(16)],
               [rng.randrange(256) for _ in range(16)])
    p.save()
    p = Program('03_alias_v0')
    for i,(rd,ra,rb) in enumerate([(1,1,2),(2,1,2),(1,1,1),(3,1,1),
                                  (0,1,2),(3,0,2),(3,1,0),(0,0,2),(0,0,0)],1):
        a,b=full([-1,2,-3,4,-5,6,-7,8]),full([8,-7,6,-5,4,-3,2,-1])
        p.case(i,a,a if ra==rb else b,rd,ra,rb)
    p.save()
    p = Program('04_pipeline')
    a,b=full(list(range(1,9))),full([1]*8)
    p.setup(a,b,0)
    # Distinct destinations: no artificial dependency between dot instructions.
    p.emit('.globl independent_begin\nindependent_begin:')
    for rd in range(3,19):
        p.emit(f'VDOT {rd}, 1, 2')
    p.emit('.globl independent_end\nindependent_end:')
    for rd in range(3,19):
        p.check(rd,reference(a,b),rd)
    p.emit('vsetivli t0, 8, e8, m1, tu, mu')
    p.emit('.globl dependency_begin\ndependency_begin:\nVDOT 3, 1, 2')
    result=reference(a,b)
    for _ in range(32):
        p.emit('VDOT 3, 3, 2')
        result=reference(result,b)
    p.check(3,result,30)
    p.emit('vsetivli t0, 8, e8, m1, tu, mu\nVDOT 3, 1, 2\nVDOT 3, 2, 2\nVDOT 3, 1, 1')
    p.check(3,reference(a,a),31)
    # Normal vector producer -> vdot; then vdot -> normal vadd consumer.
    p.emit('vsetivli t0, 16, e8, m1, tu, mu\nvadd.vv v4, v1, v2')
    c=[(x+y)&255 for x,y in zip(a,b)]
    p.emit('vsetivli t0, 8, e8, m1, tu, mu\nVDOT 5, 4, 2')
    p.check(5,reference(c,b),32)
    p.emit('vsetivli t0, 8, e8, m1, tu, mu\nVDOT 5, 1, 2\nvadd.vv v4, v5, v2')
    result=reference(a,b)
    p.check(4,[(result[i]+b[i])&255 for i in range(8)]+c[8:],33)
    p.save()
    p=Program('05_redirect')
    a,b=full(list(range(1,9))),full([1]*8)
    p.setup(a,b,0)
    poison=p.blob('branch_poison',[0xa5]*16)
    good=p.blob('branch_good',reference(a,b))
    p.emit('li s2, 0\nli s3, 32\nbranch_loop:')
    p.emit(f'vsetivli t0, 16, e8, m1, tu, mu\nLOAD v3, {poison}')
    p.emit('vsetivli t0, 8, e8, m1, tu, mu\nli t1, 31\nsub t1, s2, t1\nseqz t1, t1\nli t2, 1\ndiv t1, t1, t2')
    p.emit('.globl branch_under_test\nbranch_under_test:\nbnez t1, branch_taken')
    p.emit('.globl wrong_path_candidate\nwrong_path_candidate:\nVDOT 3, 1, 2')
    p.emit(f'CHECK v3, {good}, 1\nj branch_next\nbranch_taken:\nCHECK v3, {poison}, 2')
    p.emit('branch_next:\naddi s2, s2, 1\nbltu s2, s3, branch_loop')
    p.case(3,a,b)
    p.save()
    p=Program('06_illegal')
    p.emit('li s10, 0')
    settings = ['vsetivli t0, 7, e8, m1, tu, mu',
                'vsetivli t0, 8, e16, m1, tu, mu',
                'vsetivli t0, 8, e8, m2, tu, mu',
                'vsetivli t0, 8, e8, m1, tu, mu\nli t0, 1\ncsrw vstart, t0',
                'vsetivli t0, 8, e8, m1, tu, mu']
    for i,setting in enumerate(settings):
        p.emit(setting)
        p.emit(f'la s11, illegal_{i}\nillegal_{i}:')
        p.emit('.word 0xfc2081d7' if i==4 else 'VDOT 3, 1, 2')
        p.emit(f'li t0, {i+1}\nbne s10, t0, mismatch')
    p.save()
    p=Program('07_vadd')
    a,b=full(list(range(8))),full(list(range(8,16)))
    p.setup(a,b,0)
    p.emit('vsetivli t0, 16, e8, m1, tu, mu\nvadd.vv v3, v1, v2')
    p.check(3,[(x+y)&255 for x,y in zip(a,b)],1)
    p.save()
    print(f'Generated 8 suites, seed={SEED}; golden model sanity checks passed')

if __name__ == '__main__':
    main()
