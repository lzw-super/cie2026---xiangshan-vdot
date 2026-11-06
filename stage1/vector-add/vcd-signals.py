#!/usr/bin/env python3
"""Read only a VCD header; emit full hierarchical name, identifier, width."""
import sys
scope = []
with open(sys.argv[1], errors='replace') as f:
    for line in f:
        t = line.split()
        if not t:
            continue
        if t[0] == '$scope':
            scope.append(t[2])
        elif t[0] == '$upscope':
            scope.pop()
        elif t[0] == '$var':
            print('.'.join(scope + [t[4]]), t[3], t[2], sep='\t')
        elif t[0] == '$enddefinitions':
            break
