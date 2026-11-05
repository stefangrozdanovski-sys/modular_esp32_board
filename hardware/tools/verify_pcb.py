#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
"""Independent check: every PCB pad's net vs the schematic netlist, plus DRC.  usage: verify_pcb.py <pcb> <netlist> <drc.txt>"""
import re, sys, pcbnew
pcb, netfile, rep = sys.argv[1:4]
s = open(netfile).read()
want = {}
for m in re.finditer(r'\(net \(code "?\d+"?\) \(name "([^"]*)"\)(.*?)\)\s*(?=\(net \(code|\)\s*\)\s*$)', s, re.S):
    name = m.group(1)
    for ref, pin in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', m.group(2)):
        want[(ref, pin)] = '' if name.startswith('unconnected-') else name
b = pcbnew.LoadBoard(pcb)
n = bad = 0
for f in b.GetFootprints():
    for p in f.Pads():
        if not p.GetNumber():
            continue
        n += 1
        if p.GetNetname() != want.get((f.GetReference(), p.GetNumber()), ''):
            bad += 1; print('MISMATCH', f.GetReference(), p.GetNumber(), p.GetNetname())
refs_pcb = {f.GetReference() for f in b.GetFootprints()}
refs_sch = {r for r, _ in want}
print(f'{n} pads checked, {bad} mismatches; footprints {len(refs_pcb)}, set diff {refs_pcb ^ refs_sch or "none"}')
pcbnew.WriteDRCReport(b, rep, pcbnew.EDA_UNITS_MILLIMETRES, True)
print(re.findall(r'\*\* Found \d+ [^*]+\*\*', open(rep).read()))
