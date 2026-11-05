#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
"""Dump drawing geometry of the finished board to JSON (mm, board-relative, y down).
usage: board_geom.py <board.kicad_pcb> <out.json>"""
import json
import math
import os
import sys
import pcbnew
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import layout as LY

PCB, OUT = sys.argv[1:3]
b = pcbnew.LoadBoard(PCB)
T = pcbnew.ToMM


def P(v):
    return [round(T(v.x) - LY.OX, 3), round(T(v.y) - LY.OY, 3)]


def shapes(items, layer):
    out = []
    for g in items:
        if g.GetLayer() != layer or g.GetClass() not in ('FP_SHAPE', 'PCB_SHAPE', 'MGRAPHIC'):
            continue
        w = round(T(g.GetWidth()), 3)
        st = g.GetShape()
        if st == pcbnew.SHAPE_T_SEGMENT:
            out.append({'t': 'seg', 'a': P(g.GetStart()), 'b': P(g.GetEnd()), 'w': w})
        elif st == pcbnew.SHAPE_T_RECT:
            out.append({'t': 'rect', 'a': P(g.GetStart()), 'b': P(g.GetEnd()), 'w': w, 'f': bool(g.IsFilled())})
        elif st == pcbnew.SHAPE_T_CIRCLE:
            c = P(g.GetCenter())
            out.append({'t': 'circ', 'c': c, 'r': round(T(g.GetRadius()), 3), 'w': w, 'f': bool(g.IsFilled())})
        elif st == pcbnew.SHAPE_T_ARC:
            out.append({'t': 'arc', 'a': P(g.GetStart()), 'm': P(g.GetArcMid()), 'b': P(g.GetEnd()), 'w': w})
        elif st == pcbnew.SHAPE_T_POLY:
            ol = g.GetPolyShape().Outline(0)
            pts = [P(ol.CPoint(i)) for i in range(ol.PointCount())]
            out.append({'t': 'poly', 'p': pts, 'w': w, 'f': bool(g.IsFilled())})
    return out


fps = []
for f in b.GetFootprints():
    pads = []
    for p in f.Pads():
        sh = p.GetShape()
        kind = {pcbnew.PAD_SHAPE_RECT: 'rect', pcbnew.PAD_SHAPE_ROUNDRECT: 'rrect', pcbnew.PAD_SHAPE_CIRCLE: 'circ',
                pcbnew.PAD_SHAPE_OVAL: 'oval'}.get(sh, 'box')
        d = {'n': p.GetNumber(), 'c': P(p.GetPosition()), 'k': kind, 'net': p.GetNetname().lstrip('/'),
             'th': p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH or p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH,
             'drill': round(T(p.GetDrillSize().x), 3)}
        if kind == 'box':          # custom / chamfered: use the bounding box
            bb = p.GetBoundingBox()
            d['c'] = [round(T(bb.GetCenter().x) - LY.OX, 3), round(T(bb.GetCenter().y) - LY.OY, 3)]
            d['s'] = [round(T(bb.GetWidth()), 3), round(T(bb.GetHeight()), 3)]; d['a'] = 0
        else:
            d['s'] = [round(T(p.GetSize().x), 3), round(T(p.GetSize().y), 3)]
            d['a'] = round(p.GetOrientationDegrees(), 2)
            if kind == 'rrect':
                d['rr'] = round(p.GetRoundRectRadiusRatio(), 3)
        pads.append(d)
    xs, ys = [], []
    for g in f.GraphicalItems():
        if g.GetLayer() == pcbnew.F_CrtYd:
            bb = g.GetBoundingBox(); xs += [bb.GetLeft(), bb.GetRight()]; ys += [bb.GetTop(), bb.GetBottom()]
    crt = [round(T(min(xs)) - LY.OX, 3), round(T(min(ys)) - LY.OY, 3), round(T(max(xs)) - LY.OX, 3),
           round(T(max(ys)) - LY.OY, 3)] if xs else None
    fps.append({'ref': f.GetReference(), 'value': f.GetValue(), 'pos': P(f.GetPosition()),
                'rot': round(f.GetOrientationDegrees(), 2), 'fpname': str(f.GetFPID().GetLibItemName()),
                'pads': pads, 'fab': shapes(f.GraphicalItems(), pcbnew.F_Fab),
                'silk': shapes(f.GraphicalItems(), pcbnew.F_SilkS), 'crt': crt})

texts = []
for d in b.GetDrawings():
    if d.GetClass() == 'PCB_TEXT' and d.GetLayer() == pcbnew.F_SilkS:
        texts.append({'s': d.GetText(), 'c': P(d.GetPosition()), 'h': round(T(d.GetTextHeight()), 3),
                      'a': round(d.GetTextAngleDegrees(), 1),
                      'j': {pcbnew.GR_TEXT_H_ALIGN_LEFT: 'start', pcbnew.GR_TEXT_H_ALIGN_RIGHT: 'end'}.get(d.GetHorizJustify(), 'middle'),
                      'bold': bool(d.IsBold()) if hasattr(d, 'IsBold') else False})
json.dump({'W': LY.W, 'H': LY.H, 'CR': LY.CR, 'holes': LY.HOLES, 'module': [LY.MX, LY.MY],
           'fps': fps, 'texts': texts}, open(OUT, 'w'))
print('footprints', len(fps), 'texts', len(texts))
