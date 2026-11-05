#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
"""Rename nets to KiCad's schematic naming, write project netclasses, save into the project."""
import sys, json, re, pcbnew
IN, PROJ_PCB, SCHNET = sys.argv[1:4]
s = open(SCHNET).read()
names = [m for m in re.findall(r'\(net \(code "?\d+"?\) \(name "([^"]*)"\)', s) if not m.startswith('unconnected-')]
full = {n.lstrip('/'): n for n in names}
b = pcbnew.LoadBoard(IN)
for short, longname in full.items():
    ni = b.FindNet(short)
    if ni is not None and short != longname:
        ni.SetNetname(longname)
pcbnew.SaveBoard(PROJ_PCB, b)
pro = PROJ_PCB.replace('.kicad_pcb', '.kicad_pro')
d = json.load(open(pro))
ns = d['net_settings']
default = [c for c in ns['classes'] if c['name'] == 'Default'][0]
default.update({'track_width': 0.3, 'clearance': 0.2, 'via_diameter': 0.7, 'via_drill': 0.35})
power = dict(default); power.update({'name': 'Power', 'track_width': 0.4})
ns['classes'] = [default, power]
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from design import WIDE_NETS, POWER_NETS
ns['netclass_patterns'] = [{'netclass': 'Power', 'pattern': (n if n in POWER_NETS else '/' + n)} for n in sorted(WIDE_NETS)]
json.dump(d, open(pro, 'w'), indent=2)
print('nets renamed; netclasses written')
