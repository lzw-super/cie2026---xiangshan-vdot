#!/usr/bin/env python3
"""Assembly helpers derived from stage2; immutable full-128-bit golden checks."""
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


