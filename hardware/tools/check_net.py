#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
"""Compare a KiCad netlist (sexpr) against design.py intent."""
import re, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from design import PARTS

def parse_net(path):
    s = open(path).read()
    nets = {}
    for m in re.finditer(r'\(net \(code "?\d+"?\) \(name "([^"]*)"\)(.*?)\)\s*(?=\(net \(code|\)\s*\)\s*$)', s, re.S):
        name = m.group(1).lstrip('/')
        nodes = set(re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', m.group(2)))
        nets[name] = nodes
    comps = dict(re.findall(r'\(comp \(ref "([^"]+)"\)\s*\(value "([^"]*)"\)', s))
    fps = dict(re.findall(r'\(comp \(ref "([^"]+)"\)\s*\(value "[^"]*"\)\s*\(footprint "([^"]*)"\)', s))
    return nets, comps, fps

def intent():
    want = {}
    for ref, (lib, val, fp, pos, pm, ex) in PARTS.items():
        if ref.startswith('#'):
            continue
        for pin, net in pm.items():
            if net is None:
                continue
            want.setdefault(net, set()).add((ref, pin))
    return want

if __name__ == '__main__':
    nets, comps, fps = parse_net(sys.argv[1])
    want = intent()
    bad = 0
    real = {k: v for k, v in nets.items() if not k.startswith('unconnected-')}
    for n, nodes in want.items():
        got = real.get(n)
        if got is None:
            print('MISSING NET', n); bad += 1; continue
        if got != nodes:
            print('MISMATCH', n, 'extra', got - nodes, 'missing', nodes - got); bad += 1
    for n in real:
        if n not in want:
            print('UNEXPECTED NET', n, real[n]); bad += 1
    # single-node nets are suspicious
    for n, nodes in real.items():
        if len(nodes) < 2:
            print('SINGLE-NODE NET', n, nodes); bad += 1
    exp_refs = {r for r in PARTS if not r.startswith('#')}
    if set(comps) != exp_refs:
        print('COMPONENT SET DIFF', set(comps) ^ exp_refs); bad += 1
    nc = [k for k in nets if k.startswith('unconnected-')]
    print(f'{len(real)} named nets, {len(nc)} no-connect pins, {len(comps)} components, problems={bad}')
    sys.exit(1 if bad else 0)
