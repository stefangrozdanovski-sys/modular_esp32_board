#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
"""Pin-type electrical rules check on a KiCad netlist (KiCad 7's CLI has no ERC).
Usage: erc_lite.py netlist.net   -> lists findings, exit 1 on unexpected errors."""
import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from design import PARTS

# documented, accepted findings: (rule, net)
EXPECTED = {('multiple power outputs', '+3V3'):
            'CH340C V3 tied to VCC = documented 3.3 V mode; AMS1117 VO is the real source (HANDOFF 2.3)'}

s = open(sys.argv[1]).read()
nets = {}
for m in re.finditer(r'\(net \(code "?\d+"?\) \(name "([^"]*)"\)(.*?)(?=\(net \(code|\Z)', s, re.S):
    name = m.group(1).lstrip('/')
    nets[name] = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)(?: \(pinfunction "([^"]*)"\))? \(pintype "([^"]+)"\)', m.group(2))

flagged = {pm['1'] for r, (lib, v, fp, pos, pm, ex) in PARTS.items() if lib == 'power:PWR_FLAG'}
findings = []
for net, nodes in nets.items():
    types = [n[3].replace('+no_connect', '') for n in nodes]
    drivers = [n for n in nodes if n[3] in ('power_out',)]
    outs = [n for n in nodes if n[3] in ('output',)]
    if net.startswith('unconnected-'):
        if not all(t in ('no_connect', 'passive', 'bidirectional', 'input', 'output', 'power_in', 'tri_state') for t in types):
            findings.append(('odd unconnected pin', net, nodes))
        continue
    if any(t == 'power_in' for t in types) and not drivers and net not in flagged:
        findings.append(('power input not driven', net, [n for n in nodes if n[3] == 'power_in']))
    if len(drivers) > 1:
        findings.append(('multiple power outputs', net, drivers))
    if len(outs) > 1 or (outs and drivers):
        findings.append(('output conflict', net, outs + drivers))
    if types and all(t == 'input' for t in types):
        findings.append(('inputs only, nothing drives the net', net, nodes))
    if any(t == 'no_connect' for t in types):
        findings.append(('no-connect pin wired to a net', net, nodes))

bad = 0
for rule, net, nodes in findings:
    why = EXPECTED.get((rule, net))
    tag = 'EXPECTED' if why else 'ERROR'
    bad += 0 if why else 1
    print(f'{tag:8} {rule}: {net} {[(n[0], n[1], n[2]) for n in nodes]}' + (f'  -- {why}' if why else ''))
print(f'{len(nets)} nets checked, {len(findings)} findings, {bad} unexpected')
sys.exit(1 if bad else 0)
