#!/usr/bin/env python3
"""Check emitted machine words and data against manifests, independent of assembler mnemonics."""
from pathlib import Path
import json
import struct

build = Path(__file__).resolve().parent / 'build'
count = 0
for manifest in sorted(build.glob('*.json')):
    image = manifest.with_suffix('.bin').read_bytes()
    symbols = {}
    for line in manifest.with_suffix('.symbols').read_text().splitlines():
        fields = line.split()
        if len(fields) == 3:
            symbols[fields[2]] = int(fields[0],16) - 0x80000000
    for case in json.loads(manifest.read_text()):
        def data(label, size):
            pos = symbols[label]
            return image[pos:pos+size]
        word = struct.unpack('<I',data(f'target_{case["id"]}',4))[0]
        assert word == int(case['instruction'],16)
        assert word & 0xfe00707f == 0xfe000057
        assert (word >> 7) & 31 == case['vd']
        assert (word >> 15) & 31 == case['vs1']
        assert (word >> 20) & 31 == case['vs2']
        prefix = f'data_{manifest.stem}_'
        a = struct.unpack('16b',data(prefix+f'a{case["id"]}',16))
        b = struct.unpack('16b',data(prefix+f'b{case["id"]}',16))
        expected = struct.pack('<I',sum(x*y for x,y in zip(a[:8],b[:8])) & 0xffffffff) + bytes(12)
        assert data(prefix+f'expected{case["id"]}',16) == expected == bytes(case['expected'])
        count += 1
assert count >= 140
assert len(list(build.glob('*.bin'))) == 8
print(f'PASS: 8 images, {count} manifest cases: encoding, fields and full 16-byte golden data')
