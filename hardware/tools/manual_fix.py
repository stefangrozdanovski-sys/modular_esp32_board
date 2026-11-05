#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
"""Hand-routed completions after autorouting. usage: manual_fix.py in.kicad_pcb out.kicad_pcb"""
import sys, pcbnew
IN, OUT = sys.argv[1:3]
b = pcbnew.LoadBoard(IN)
P = lambda u, v: pcbnew.VECTOR2I(pcbnew.FromMM(100 + u), pcbnew.FromMM(100 + v))
FIXES = [
    # +5V trunk on B.Cu: PZEM 5V (J2.1) along the bottom edge to the LDO input via
    ('+5V', pcbnew.B_Cu, 0.4, [(32.6, 53.4), (32.6, 55.15), (54.836, 55.15), (54.836, 42.28)]),
]
for net, layer, w, pts in FIXES:
    ni = b.FindNet(net)
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(P(*a)); t.SetEnd(P(*c))
        t.SetWidth(pcbnew.FromMM(w)); t.SetLayer(layer); t.SetNet(ni); t.SetLocked(True)
        b.Add(t)
pcbnew.SaveBoard(OUT, b)
print('fixes applied:', len(FIXES))
