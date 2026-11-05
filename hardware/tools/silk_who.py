#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
"""Diagnose what a silk text collides with.  usage: silk_who.py <pcb> text1 [text2 ...]"""
import sys
pcb, names = sys.argv[1], sys.argv[2:]
sys.argv = ['x', pcb, '/dev/null']
exec(open(__file__.replace('silk_who.py', 'silk_fix.py')).read().split('moved = hidden = 0')[0])
for d in b.GetDrawings():
    if d.GetClass() == 'PCB_TEXT' and d.GetText() in names:
        side = 'F' if d.GetLayer() == pcbnew.F_SilkS else 'B'
        r = rect(d.GetBoundingBox())
        hits = [o for o in obstacles(side, skip=d) if hit(r, o)]
        print(repr(d.GetText()), side, [round(x - 100, 2) for x in r], 'edge-ok' if inside_board(r) else 'EDGE',
              [tuple(round(x - 100, 2) if isinstance(x, float) else x for x in o) for o in hits][:4])
