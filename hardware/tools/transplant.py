#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
"""Copy tracks+vias from a routed board onto a freshly built (same placement) board.
usage: transplant.py placed.kicad_pcb routed.kicad_pcb out.kicad_pcb"""
import sys, pcbnew
placed, routed, out = sys.argv[1:4]
r = pcbnew.LoadBoard(routed)
items = []
for t in r.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        items.append(('via', t.GetNetname(), t.GetPosition().x, t.GetPosition().y, t.GetWidth(), t.GetDrill(), t.IsLocked()))
    else:
        items.append(('trk', t.GetNetname(), t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y, t.GetWidth(), t.GetLayer(), t.IsLocked()))
pr = {f.GetReference(): (f.GetPosition().x, f.GetPosition().y, f.GetOrientationDegrees()) for f in r.GetFootprints()}
a = pcbnew.LoadBoard(placed)
pa = {f.GetReference(): (f.GetPosition().x, f.GetPosition().y, f.GetOrientationDegrees()) for f in a.GetFootprints()}
assert pa == pr, 'placement differs'
for t in list(a.GetTracks()):
    a.Remove(t)
for it in items:
    if it[0] == 'via':
        _, net, x, y, w, d, lk = it
        v = pcbnew.PCB_VIA(a); v.SetPosition(pcbnew.VECTOR2I(x, y)); v.SetWidth(w); v.SetDrill(d)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(a.FindNet(net)); v.SetLocked(lk); a.Add(v)
    else:
        _, net, x1, y1, x2, y2, w, layer, lk = it
        t = pcbnew.PCB_TRACK(a); t.SetStart(pcbnew.VECTOR2I(x1, y1)); t.SetEnd(pcbnew.VECTOR2I(x2, y2))
        t.SetWidth(w); t.SetLayer(layer); t.SetNet(a.FindNet(net)); t.SetLocked(lk); a.Add(t)
pcbnew.SaveBoard(out, a)
print('transplanted', len(items))
