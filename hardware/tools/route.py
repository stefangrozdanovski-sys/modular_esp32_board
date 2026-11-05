#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
"""DSN export -> Freerouting -> SES import (parsed here) -> zones -> save.
usage: route.py <in.kicad_pcb> <out.kicad_pcb> [passes]"""
import re, sys, os, subprocess
import pcbnew
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
from design import WIDE_NETS

IN, OUT = sys.argv[1], sys.argv[2]
PASSES = sys.argv[3] if len(sys.argv) > 3 else '40'
DSN, SES = f'{SP}/board.dsn', f'{SP}/board.ses'
W_POWER_UM = 400

b = pcbnew.LoadBoard(IN)
# drop existing tracks/vias and zones before routing
for t in list(b.GetTracks()):
    if not t.IsLocked():
        b.Remove(t)
for z in list(b.Zones()):
    if not z.GetIsRuleArea():
        b.Remove(z)
assert pcbnew.ExportSpecctraDSN(b, DSN)

# --- add a wide 'power' class to the DSN
d = open(DSN).read()
m = re.search(r'\(class kicad_default ""(.*?)\(circuit', d, re.S)
names = m.group(1).split()
sig = [n for n in names if n not in WIDE_NETS]
pwr = [n for n in names if n in WIDE_NETS]
newcls = (f'(class kicad_default "" {" ".join(sig)}\n      (circuit')
d = d[:m.start()] + newcls + d[m.end():]
pcls = f'''(class power {" ".join(pwr)}
      (circuit
        (use_via Via[0-1]_700:350_um)
      )
      (rule
        (width {W_POWER_UM})
        (clearance 200.1)
      )
    )
  )
  (wiring'''
d = re.sub(r'\)\s*\(wiring', '\n    ' + pcls, d, count=1)
# shrink the routing boundary 0.55 mm inside the board edge (edge clearance 0.5 mm)
bm = re.search(r'\(boundary\s*\(path pcb 0(.*?)\)\s*\)', d, re.S)
vals = [int(x) for x in bm.group(1).split()]
xs, ys = vals[0::2], vals[1::2]
x0, x1, y0, y1 = min(xs) + 550, max(xs) - 550, min(ys) + 550, max(ys) - 550
newb = f'(boundary\n      (path pcb 0  {x0} {y0}  {x1} {y0}  {x1} {y1}  {x0} {y1}  {x0} {y0})\n    )'
d = d[:bm.start()] + newb + d[bm.end():]
open(DSN, 'w').write(d)

if os.path.exists(SES):
    os.remove(SES)
cmd = ['xvfb-run', '-a', 'java', '-Djava.awt.headless=false', '-jar', os.environ.get('FREEROUTING_JAR', f'{SP}/freerouting.jar'),
       '-de', DSN, '-do', SES, '-mp', PASSES, '-mt', os.environ.get('FR_THREADS', '0')]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=2400); open(SP + '/fr.log', 'w').write(r.stdout + r.stderr)
if not os.path.exists(SES):
    print(r.stdout[-3000:], r.stderr[-3000:])
    raise SystemExit('freerouting produced no SES')

# --- parse SES and add tracks / vias
ses = open(SES).read()
res = float(re.search(r'\(resolution um (\d+)\)', ses).group(1))  # units per um
def to_iu(v):
    return int(round(float(v) / res * 1000))   # um -> nm
netmap = {n.GetNetname(): n for n in b.GetNetsByName().values()} if hasattr(b, 'GetNetsByName') else None
def net_of(name):
    ni = b.FindNet(name)
    if ni is None:
        raise KeyError(name)
    return ni
layers = {'F.Cu': pcbnew.F_Cu, 'B.Cu': pcbnew.B_Cu}
locked_vias = {(t.GetPosition().x // 1000, t.GetPosition().y // 1000) for t in b.GetTracks() if t.IsLocked() and t.Type() == pcbnew.PCB_VIA_T}
locked_segs = set()
for t in b.GetTracks():
    if t.IsLocked() and t.Type() == pcbnew.PCB_TRACE_T:
        a1 = (t.GetStart().x // 1000, t.GetStart().y // 1000); a2 = (t.GetEnd().x // 1000, t.GetEnd().y // 1000)
        locked_segs.add(frozenset((a1, a2)))
nw = nv = 0
for nm in re.finditer(r'\(net ("[^"]*"|\S+)(.*?)\n    \)', ses, re.S):
    name = nm.group(1).strip('"')
    body = nm.group(2)
    ni = net_of(name)
    for wm in re.finditer(r'\(wire\s*\(path (\S+) (\d+)((?:\s+-?\d+)+)\s*\)', body):
        lay, width, pts = wm.group(1), int(wm.group(2)), wm.group(3).split()
        xy = [(to_iu(pts[i]), -to_iu(pts[i + 1])) for i in range(0, len(pts), 2)]
        for (x1, y1), (x2, y2) in zip(xy, xy[1:]):
            if frozenset(((x1 // 1000, y1 // 1000), (x2 // 1000, y2 // 1000))) in locked_segs:
                continue
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(pcbnew.VECTOR2I(x1, y1)); t.SetEnd(pcbnew.VECTOR2I(x2, y2))
            t.SetWidth(int(round(width / res * 1000)))
            t.SetLayer(layers[lay]); t.SetNet(ni)
            b.Add(t); nw += 1
    for vm in re.finditer(r'\(via "?([^"\s]+)"? (-?\d+) (-?\d+)', body):
        px, py = to_iu(vm.group(2)), -to_iu(vm.group(3))
        if (px // 1000, py // 1000) in locked_vias:
            continue
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(px, py))
        dia, drill = re.search(r'_(\d+):(\d+)_um', vm.group(1)).groups()
        v.SetWidth(pcbnew.FromMM(int(dia) / 1000)); v.SetDrill(pcbnew.FromMM(int(drill) / 1000))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(ni)
        b.Add(v); nv += 1
print(f'imported {nw} track segments, {nv} vias')
pcbnew.SaveBoard(OUT, b)
