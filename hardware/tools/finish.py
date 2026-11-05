#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
"""GND pours on both layers, +3V3 spreader under the AMS1117, stitching vias, fill, DRC.
usage: finish.py <in.kicad_pcb> <out.kicad_pcb> <drc_report.txt> [--stitch]"""
import os
import re
import sys
import pcbnew
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import layout as LY

IN, OUT, REP = sys.argv[1:4]
OX, OY, W, H = LY.OX, LY.OY, LY.W, LY.H
b = pcbnew.LoadBoard(IN)
gnd = b.FindNet('GND')
v33 = b.FindNet('+3V3')
P = lambda u, v: pcbnew.VECTOR2I(pcbnew.FromMM(OX + u), pcbnew.FromMM(OY + v))

for z in list(b.Zones()):
    if not z.GetIsRuleArea():
        b.Remove(z)


def zone(layer, net, rect, prio=0, conn=pcbnew.ZONE_CONNECTION_THERMAL):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer); z.SetNetCode(net.GetNetCode()); z.SetAssignedPriority(prio)
    z.SetLocalClearance(pcbnew.FromMM(0.3)); z.SetMinThickness(pcbnew.FromMM(0.25))
    z.SetThermalReliefGap(pcbnew.FromMM(0.3)); z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.5))
    z.SetPadConnection(conn)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    ol = z.Outline(); ol.NewOutline()
    u0, v0, u1, v1 = rect
    for (u, v) in [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]:
        ol.Append(pcbnew.FromMM(OX + u), pcbnew.FromMM(OY + v))
    b.Add(z)
    return z


m = 0.3
zf = zone(pcbnew.F_Cu, gnd, (m, m, W - m, H - m))
zb = zone(pcbnew.B_Cu, gnd, (m, m, W - m, H - m))
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    zone(layer, v33, LY.AMS_SPREADER, prio=1, conn=pcbnew.ZONE_CONNECTION_FULL)

filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())


def clear_of_items(pt, r_mm=0.85):
    r = pcbnew.FromMM(r_mm)
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if (p.GetPosition() - pt).EuclideanNorm() < r + max(p.GetSize().x, p.GetSize().y) / 2:
                return False
    for t in b.GetTracks():
        if t.HitTest(pt, r):
            return False
    return True


def add_via(u, v, net):
    via = pcbnew.PCB_VIA(b); via.SetPosition(P(u, v))
    via.SetWidth(pcbnew.FromMM(0.7)); via.SetDrill(pcbnew.FromMM(0.35))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); via.SetNet(net); b.Add(via)


# tie the two spreader layers together (only where nothing else is)
s0, t0, s1, t1 = LY.AMS_SPREADER
spread = 0
for (u, v) in [(s1 - 0.6, t0 + 0.6), (s1 - 0.6, t1 - 0.6), (s1 - 0.6, (t0 + t1) / 2)]:
    if clear_of_items(P(u, v), 0.6):
        add_via(u, v, v33); spread += 1

def silk_boxes():
    out = []
    for d in b.GetDrawings():
        if d.GetClass() == 'PCB_TEXT':
            bb = d.GetBoundingBox(); out.append((bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()))
    for fp in b.GetFootprints():
        t = fp.Reference()
        if t.IsVisible():
            bb = t.GetBoundingBox(); out.append((bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()))
    return out


SILK = silk_boxes()


def under_silk(pt, m=pcbnew.FromMM(0.6)):
    return any(x0 - m < pt.x < x1 + m and y0 - m < pt.y < y1 + m for (x0, y0, x1, y1) in SILK)


added = 0
if '--stitch' in sys.argv:
    def inside_both(pt):
        return zf.HitTestFilledArea(pcbnew.F_Cu, pt, pcbnew.FromMM(0.5)) and \
               zb.HitTestFilledArea(pcbnew.B_Cu, pt, pcbnew.FromMM(0.5))
    step = 4.0
    u = 2.0
    while u < W - 1.5:
        v = 2.0
        while v < H - 1.5:
            under_module = (LY.MX - 9.5 < u < LY.MX + 9.5) and v < 21.5
            under_legend = (25.0 < u < 50.0) and (26.0 < v < 41.0)          # back-side port map text
            if not under_module and not under_legend:
                pt = P(u, v)
                if inside_both(pt) and clear_of_items(pt) and not under_silk(pt):
                    add_via(u, v, gnd); added += 1
            v += step
        u += step
filler.Fill(b.Zones())
print('spreader vias:', spread, ' stitching vias:', added)

pcbnew.SaveBoard(OUT, b)
b2 = pcbnew.LoadBoard(OUT)
pcbnew.WriteDRCReport(b2, REP, pcbnew.EDA_UNITS_MILLIMETRES, True)
txt = open(REP).read()
print(re.findall(r'\*\* Found \d+ [^*]+\*\*', txt))
