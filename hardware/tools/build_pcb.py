#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
"""Build the v2.0 PCB (placement, outline, silkscreen, keepout) from the schematic netlist.
usage: build_pcb.py <netlist> <out.kicad_pcb>   -> also prints courtyard overlaps."""
import math
import os
import re
import sys
import pcbnew
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
from design import PARTS
from parts import PORTS
import layout as LY

PROJ = os.environ.get('PROJ', os.path.abspath(os.path.join(SP, '..')))
NETFILE, OUT = sys.argv[1], sys.argv[2]
OX, OY, W, H, CR = LY.OX, LY.OY, LY.W, LY.H, LY.CR


def mm(u, v):
    return pcbnew.VECTOR2I(pcbnew.FromMM(OX + u), pcbnew.FromMM(OY + v))


PLACE = LY.all_place()

# ---------------------------------------------------------------- netlist
s = open(NETFILE).read()
comps = {}
for m in re.finditer(r'\(comp \(ref "([^"]+)"\)\s*\(value "([^"]*)"\)\s*\(footprint "([^"]*)"\)(.*?)\(tstamps "([0-9a-f-]{36})"\)\)', s, re.S):
    comps[m.group(1)] = dict(value=m.group(2), fp=m.group(3), uuid=m.group(5))
padnet, netnames = {}, []
for m in re.finditer(r'\(net \(code "?\d+"?\) \(name "([^"]*)"\)(.*?)\)\s*(?=\(net \(code|\)\s*\)\s*$)', s, re.S):
    name = m.group(1).lstrip('/')
    if name.startswith('unconnected-'):
        continue
    netnames.append(name)
    for ref, pin in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', m.group(2)):
        padnet[(ref, pin)] = name
assert set(comps) == set(PLACE), set(comps) ^ set(PLACE)

board = pcbnew.BOARD()
board.SetCopperLayerCount(2)
ds = board.GetDesignSettings()
ds.m_MinClearance = pcbnew.FromMM(0.2)
ds.m_TrackMinWidth = pcbnew.FromMM(0.2)
ds.m_ViasMinSize = pcbnew.FromMM(0.6)
ds.m_ViasMinAnnularWidth = pcbnew.FromMM(0.15)
ds.m_MinThroughDrill = pcbnew.FromMM(0.3)
ds.m_CopperEdgeClearance = pcbnew.FromMM(0.5)
ds.m_HoleClearance = pcbnew.FromMM(0.25)
ds.m_HoleToHoleMin = pcbnew.FromMM(0.5)
ds.m_SilkClearance = pcbnew.FromMM(0.0)
nc = ds.m_NetSettings.m_DefaultNetClass
nc.SetClearance(pcbnew.FromMM(0.2)); nc.SetTrackWidth(pcbnew.FromMM(0.3))
nc.SetViaDiameter(pcbnew.FromMM(0.7)); nc.SetViaDrill(pcbnew.FromMM(0.35))

nets = {}
for n in netnames:
    ni = pcbnew.NETINFO_ITEM(board, n)
    board.Add(ni)
    nets[n] = ni


def fp_lib_path(lib):
    return f'{PROJ}/{lib}.pretty' if lib == 'esp32-modular' else f'/usr/share/kicad/footprints/{lib}.pretty'


PORT_REF = re.compile(r'^(R|C|F|JP)[1-8]0[1-6]$')
for ref, c in comps.items():
    lib, name = c['fp'].split(':', 1)
    f = pcbnew.FootprintLoad(fp_lib_path(lib), name)
    if f is None:
        raise SystemExit(f'footprint {c["fp"]} not found')
    f.SetFPID(pcbnew.LIB_ID(lib, name))
    f.SetReference(ref)
    f.SetValue(c['value'])
    f.SetPath(pcbnew.KIID_PATH('/' + c['uuid']))
    u, v, rot = PLACE[ref]
    board.Add(f)
    f.SetPosition(mm(u, v))
    f.SetOrientationDegrees(rot)
    for pad in f.Pads():
        net = padnet.get((ref, pad.GetNumber()))
        if net:
            pad.SetNet(nets[net])
    f.Value().SetLayer(pcbnew.F_Fab); f.Value().SetVisible(True)
    t = f.Reference()
    t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.8), pcbnew.FromMM(0.8)))
    t.SetTextThickness(pcbnew.FromMM(0.12))
    t.SetTextAngleDegrees(0)
    # silk refdes: off inside the dense port groups, on connectors and holes (labels do that job)
    if PORT_REF.match(ref) or ref[0] in 'HJ' or ref in ('SW1', 'SW2', 'U1', 'U4'):
        t.SetVisible(False)
    if PARTS[ref][5].get('DNP'):
        f.SetAttributes(f.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_EXCLUDE_FROM_BOM)
        if hasattr(pcbnew, 'FP_DNP'):
            f.SetAttributes(f.GetAttributes() | pcbnew.FP_DNP)

# ---------------------------------------------------------------- outline
def seg(a, b, layer=pcbnew.Edge_Cuts, w=0.1):
    sh = pcbnew.PCB_SHAPE(board); sh.SetShape(pcbnew.SHAPE_T_SEGMENT)
    sh.SetStart(mm(*a)); sh.SetEnd(mm(*b)); sh.SetLayer(layer); sh.SetWidth(pcbnew.FromMM(w))
    board.Add(sh)


def arc(c, start, end, layer=pcbnew.Edge_Cuts, w=0.1):
    sh = pcbnew.PCB_SHAPE(board); sh.SetShape(pcbnew.SHAPE_T_ARC)
    a0 = math.atan2(start[1] - c[1], start[0] - c[0]); a1 = math.atan2(end[1] - c[1], end[0] - c[0])
    if a1 < a0:
        a1 += 2 * math.pi
    am = (a0 + a1) / 2; r = math.hypot(start[0] - c[0], start[1] - c[1])
    sh.SetArcGeometry(mm(*start), mm(c[0] + r * math.cos(am), c[1] + r * math.sin(am)), mm(*end))
    sh.SetLayer(layer); sh.SetWidth(pcbnew.FromMM(w)); board.Add(sh)


seg((CR, 0), (W - CR, 0)); seg((W, CR), (W, H - CR)); seg((W - CR, H), (CR, H)); seg((0, H - CR), (0, CR))
arc((W - CR, CR), (W - CR, 0), (W, CR)); arc((W - CR, H - CR), (W, H - CR), (W - CR, H))
arc((CR, H - CR), (CR, H), (0, H - CR)); arc((CR, CR), (0, CR), (CR, 0))

# ---------------------------------------------------------------- silkscreen
def text(t, u, v, size=0.8, layer=pcbnew.F_SilkS, rot=0, just=0, bold=False):
    tx = pcbnew.PCB_TEXT(board)
    tx.SetText(t); tx.SetPosition(mm(u, v)); tx.SetLayer(layer)
    tx.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(size), pcbnew.FromMM(size)))
    tx.SetTextThickness(pcbnew.FromMM(size * (0.2 if bold else 0.15)))
    tx.SetTextAngleDegrees(rot)
    if just < 0:
        tx.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    elif just > 0:
        tx.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    if layer == pcbnew.B_SilkS:
        tx.SetMirrored(True)
    board.Add(tx)
    return tx


PINLBL = {'UART': ('G', 'V', 'TX', 'RX'), 'I2C': ('G', 'V', 'DA', 'CL')}
TEXT_ROT = {'bottom': 0, 'left': 90, 'right': 90}          # keep text readable from the bottom / right
for n, (label, ga, gb, vp, ov) in PORTS.items():
    edge, along = LY.PORT_ANCHOR[n]
    for k, pl in enumerate(PINLBL.get(label, ('G', 'V', 'A', 'B'))):
        u, v, _ = LY.local_to_board(edge, along, 2.5 * k, 3.45, 0)
        text(pl, u, v, 0.8, rot=TEXT_ROT[edge])
    u, v, _ = LY.local_to_board(edge, along, -4.25, 2.6 if n == 1 else 1.2, 0)   # P1: clear of the H3 screw head
    text(label, u, v, 0.85, rot=(90 if edge == 'bottom' else 0), bold=True)

# USB input (top edge, pins right->left from pin 1)
for k, pl in enumerate(('5V', 'D-', 'D+', 'G')):
    u, v, _ = LY.local_to_board('top', LY.CORE_PLACE['J1'][0], 2.5 * k, 3.4, 0)
    text(pl, u, v, 0.8)
text('USB', 63.4, 4.4, 0.85, rot=90, bold=True)
# switched output (right edge, pins bottom->top)
for k, pl in enumerate(('G', 'V+', 'OUT')):
    u, v, _ = LY.local_to_board('right', LY.CORE_PLACE['J901'][1], 2.5 * k, 3.45, 0)
    text(pl, u, v, 0.8, rot=90)
u, v, _ = LY.local_to_board('right', LY.CORE_PLACE['J901'][1], -4.25, 1.2, 0)
text('OUT', u, v, 0.85, bold=True)
text('5V', 65.0, 48.25, 0.8)                                            # JP901 label
J9U, J9V, _ = LY.CORE_PLACE['J902']
text('EXP IO', J9U - 2.6, J9V, 0.8, bold=True, just=1)
for k, pl in enumerate(('3V3', '19', '14', '5', 'G')):
    text(pl, J9U + 2.54 * k, J9V + 2.6, 0.8)
text('RST', 17.35, 4.15, 0.8, rot=90); text('BOOT', 17.35, 12.05, 0.8, rot=90)

# board name + jumper legend (front), port map (back)
text('ESP32 MODULAR', 23.4, 29.6, 1.0, bold=True)
text('BASE v2.0 2026-10', 23.4, 31.2, 0.8)
text('VP JUMPER', 23.4, 34.4, 0.8, bold=True)
text('near pad 3V3', 23.4, 36.0, 0.8)
text('far pad 5V', 23.4, 37.6, 0.8)
text('UART default 5V', 23.4, 39.2, 0.8)
B = pcbnew.B_SilkS
col1 = ['PORT A    B'] + [f'{p[0]:4} {p[1]:5} {p[2]}' for n, p in PORTS.items() if n <= 6]
col2 = [f'UART TX {PORTS[7][1][2:]} RX {PORTS[7][2][2:]}', f'I2C DA {PORTS[8][1][2:]} CL {PORTS[8][2][2:]}',
        'OUT IO23', 'EXP 19 14 5', 'LED IO2', 'BOOT IO0']
text('ESP32 MODULAR BASE v2.0', 37.5, 27.0, 0.9, layer=B, bold=True)
for i, ln in enumerate(col1):
    text(ln, 31.0, 29.0 + 1.7 * i, 0.8, layer=B)
for i, ln in enumerate(col2):
    text(ln, 44.0, 29.0 + 1.7 * i, 0.8, layer=B)

# ---------------------------------------------------------------- escape stubs for boxed-in USBLC6 pins
fps = {f.GetReference(): f for f in board.GetFootprints()}
for ref, num, (du, dv), netname in [('U4', '2', (-1.0, 0.0), 'GND'), ('U4', '5', (1.55, 0.0), '+5V')]:
    pad = [p for p in fps[ref].Pads() if p.GetNumber() == num][0]
    p0 = pad.GetPosition(); p1 = pcbnew.VECTOR2I(p0.x + pcbnew.FromMM(du), p0.y + pcbnew.FromMM(dv))
    t = pcbnew.PCB_TRACK(board); t.SetStart(p0); t.SetEnd(p1)
    t.SetWidth(pcbnew.FromMM(0.3)); t.SetLayer(pcbnew.F_Cu); t.SetNet(nets[netname]); t.SetLocked(True)
    board.Add(t)
    v = pcbnew.PCB_VIA(board); v.SetPosition(p1)
    v.SetWidth(pcbnew.FromMM(0.7)); v.SetDrill(pcbnew.FromMM(0.35))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(nets[netname]); v.SetLocked(True)
    board.Add(v)

# ---------------------------------------------------------------- module keepout (F.Cu tracks/vias)
ka = pcbnew.ZONE(board); ka.SetIsRuleArea(True); ka.SetLayer(pcbnew.F_Cu)
ka.SetDoNotAllowTracks(True); ka.SetDoNotAllowVias(True)
ka.SetDoNotAllowCopperPour(False); ka.SetDoNotAllowPads(False); ka.SetDoNotAllowFootprints(False)
ka.SetZoneName('ESP32 module body: no tracks')
kol = ka.Outline(); kol.NewOutline()
u0, v0, u1, v1 = LY.MODULE_KEEPOUT
for (u, v) in [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]:
    kol.Append(pcbnew.FromMM(OX + u), pcbnew.FromMM(OY + v))
board.Add(ka)

pcbnew.SaveBoard(OUT, board)

# ---------------------------------------------------------------- placement checks
def crt(f):
    xs, ys = [], []
    for g in f.GraphicalItems():
        if g.GetLayer() == pcbnew.F_CrtYd:
            bb = g.GetBoundingBox(); xs += [bb.GetLeft(), bb.GetRight()]; ys += [bb.GetTop(), bb.GetBottom()]
    if not xs:
        bb = f.GetBoundingBox(False, False); xs = [bb.GetLeft(), bb.GetRight()]; ys = [bb.GetTop(), bb.GetBottom()]
    return [pcbnew.ToMM(min(xs)) - OX, pcbnew.ToMM(min(ys)) - OY, pcbnew.ToMM(max(xs)) - OX, pcbnew.ToMM(max(ys)) - OY]


boxes = {f.GetReference(): crt(f) for f in board.GetFootprints() if not f.GetReference().startswith('H')}
boxes['U1'][1] = max(boxes['U1'][1], -0.5)          # module courtyard: on-board part only
boxes['U1'] = [LY.MX - 10.93, 0.0, LY.MX + 10.93, LY.MY + 11.62]
over = []
refs = sorted(boxes)
for i, a in enumerate(refs):
    A = boxes[a]
    for b in refs[i + 1:]:
        Bx = boxes[b]
        ox = min(A[2], Bx[2]) - max(A[0], Bx[0]); oy = min(A[3], Bx[3]) - max(A[1], Bx[1])
        if ox > 0.02 and oy > 0.02:
            over.append((a, b, round(ox, 2), round(oy, 2)))
out_of_board = [r for r, bx in boxes.items() if r != 'U1' and (bx[0] < 0 or bx[1] < 0 or bx[2] > W or bx[3] > H)]
for (hu, hv) in LY.HOLES.values():
    for r, bx in boxes.items():
        cu, cv = min(max(hu, bx[0]), bx[2]), min(max(hv, bx[1]), bx[3])
        if math.hypot(cu - hu, cv - hv) < 3.5:
            over.append(('hole', r, round(math.hypot(cu - hu, cv - hv), 2), ''))
print('saved', OUT, len(comps), 'footprints', len(nets), 'nets')
print('courtyard overlaps:', over if over else 'none')
print('outside board:', out_of_board if out_of_board else 'none')
