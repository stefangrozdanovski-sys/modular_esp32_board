#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
"""Move silkscreen texts off pads, vias, other silk and the board edge.
usage: silk_fix.py <in.kicad_pcb> <out.kicad_pcb>
Refdes: tried above/below/left/right of the part, hidden if no spot is clear.
Board texts: nearest clear spot within 4 mm, else reported."""
import os
import sys
import pcbnew
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import layout as LY

IN, OUT = sys.argv[1:3]
b = pcbnew.LoadBoard(IN)
T, F = pcbnew.ToMM, pcbnew.FromMM
OX, OY, W, H = LY.OX, LY.OY, LY.W, LY.H
GAP = 0.12


def rect(bb, grow=0.0):
    return (T(bb.GetLeft()) - grow, T(bb.GetTop()) - grow, T(bb.GetRight()) + grow, T(bb.GetBottom()) + grow)


def hit(a, c):
    if c[0] == 'hole':                                   # circle (screw head) vs rectangle
        cx, cy, r = c[1], c[2], c[3]
        nx, ny = min(max(cx, a[0]), a[2]), min(max(cy, a[1]), a[3])
        return (nx - cx) ** 2 + (ny - cy) ** 2 < r * r
    return a[0] < c[2] and c[0] < a[2] and a[1] < c[3] and c[1] < a[3]


def uid(x):
    return x.m_Uuid.AsString() if x is not None else None


def obstacles(side, skip=None):
    """copper with mask openings + silk on one side.  skip = the text object being placed."""
    sk = uid(skip)
    silk = pcbnew.F_SilkS if side == 'F' else pcbnew.B_SilkS
    cu = pcbnew.F_Cu if side == 'F' else pcbnew.B_Cu
    obs = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.IsOnLayer(cu):
                obs.append(rect(p.GetBoundingBox(), GAP))
        for g in fp.GraphicalItems():
            if g.GetLayer() == silk and uid(g) != sk:
                if g.GetClass() in ('FP_TEXT', 'PCB_TEXT') and not g.IsVisible():
                    continue
                obs.append(rect(g.GetBoundingBox(), GAP))
        for t in (fp.Reference(),):
            if t.IsVisible() and t.GetLayer() == silk and uid(t) != sk:
                obs.append(rect(t.GetBoundingBox(), GAP))
    # vias are tented (no mask opening in KiCad 7), so silk may cross them
    for d in b.GetDrawings():
        if d.GetLayer() == silk and uid(d) != sk and d.GetClass() == 'PCB_TEXT':
            obs.append(rect(d.GetBoundingBox(), GAP))
    for (hu, hv) in LY.HOLES.values():
        obs.append(('hole', OX + hu, OY + hv, 3.3))
    # module body and antenna: keep silk off the module outline area
    return obs


def inside_board(r, m=0.35):
    return r[0] > OX + m and r[1] > OY + m and r[2] < OX + W - m and r[3] < OY + H - m


def clear(t, side):
    r = rect(t.GetBoundingBox())
    if not inside_board(r):
        return False
    return not any(hit(r, o) for o in obstacles(side, skip=t))


def crt(fp):
    xs, ys = [], []
    for g in fp.GraphicalItems():
        if g.GetLayer() == pcbnew.F_CrtYd:
            bb = g.GetBoundingBox(); xs += [bb.GetLeft(), bb.GetRight()]; ys += [bb.GetTop(), bb.GetBottom()]
    if not xs:
        bb = fp.GetBoundingBox(False, False); xs = [bb.GetLeft(), bb.GetRight()]; ys = [bb.GetTop(), bb.GetBottom()]
    return T(min(xs)), T(min(ys)), T(max(xs)), T(max(ys))


moved = hidden = 0
for fp in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
    t = fp.Reference()
    if not t.IsVisible() or t.GetLayer() != pcbnew.F_SilkS:
        continue
    if clear(t, 'F'):
        continue
    x0, y0, x1, y1 = crt(fp)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    hh = T(t.GetTextHeight()) / 2 + 0.15
    cands = []
    for sh in (0, -1.0, 1.0, -2.0, 2.0):
        cands += [(cx + sh, y0 - hh, 0), (cx + sh, y1 + hh, 0), (x0 - hh, cy + sh, 90), (x1 + hh, cy + sh, 90)]
    ok = False
    for (x, y, a) in cands:
        t.SetTextAngleDegrees(a)
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
        t.SetPosition(pcbnew.VECTOR2I(F(x), F(y)))
        if clear(t, 'F'):
            ok = True
            break
    if ok:
        moved += 1
    else:
        t.SetVisible(False); hidden += 1
        print('  hidden refdes', fp.GetReference())

unresolved = []
for d in list(b.GetDrawings()):
    if d.GetClass() != 'PCB_TEXT':
        continue
    side = 'F' if d.GetLayer() == pcbnew.F_SilkS else 'B'
    if clear(d, side):
        continue
    p0 = d.GetPosition()
    best = None
    nmax = 4 if len(d.GetText()) <= 4 else 16      # labels stay within 1 mm of their pin, notes 4 mm
    for step in range(1, nmax + 1):                # spiral search, 0.25 mm steps
        r = step * 0.25
        for (dx, dy) in [(0, -r), (0, r), (-r, 0), (r, 0), (-r, -r), (r, -r), (-r, r), (r, r)]:
            d.SetPosition(pcbnew.VECTOR2I(p0.x + F(dx), p0.y + F(dy)))
            if clear(d, side):
                best = (dx, dy)
                break
        if best:
            break
    if best is None:
        d.SetPosition(p0); unresolved.append(d.GetText())
    else:
        print(f'  moved "{d.GetText()}" by {best}')
if '--keepout' in sys.argv:
    # no vias under any visible silk text (tracks and pours still allowed), both copper layers
    ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu)
    items = [fp.Reference() for fp in b.GetFootprints() if fp.Reference().IsVisible()
             and fp.Reference().GetLayer() == pcbnew.F_SilkS]
    items += [d for d in b.GetDrawings() if d.GetClass() == 'PCB_TEXT']
    for it in items:
        r = rect(it.GetBoundingBox(), 0.25)
        z = pcbnew.ZONE(b); z.SetIsRuleArea(True); z.SetLayerSet(ls)
        z.SetDoNotAllowVias(True); z.SetDoNotAllowTracks(False); z.SetDoNotAllowCopperPour(False)
        z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False); z.SetZoneName('silk: no vias')
        ol = z.Outline(); ol.NewOutline()
        for (x, y) in [(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])]:
            ol.Append(F(x), F(y))
        b.Add(z)
    print('via keepouts under silk:', len(items))
pcbnew.SaveBoard(OUT, b)
print(f'refdes moved {moved}, hidden {hidden}; texts unresolved: {unresolved if unresolved else "none"}')
