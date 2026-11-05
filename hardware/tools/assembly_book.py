#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
"""Printable A4 assembly guide for ESP32 Modular Base v2.0.
usage: assembly_book.py <geom.json> <out.html>      (then print with tools/print_pdf.py)
Geometry comes from board_geom.py (the finished PCB); values / fit / notes from parts.py."""
import base64
import html
import json
import math
import os
import sys
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
from parts import CORE, LINES, PORTS, port_refs
from bom_extra import RECIPES

GEOM, OUT = sys.argv[1:3]
ROOT = os.path.abspath(os.path.join(SP, '..'))
G = json.load(open(GEOM))
FP = {f['ref']: f for f in G['fps']}
_mx, _my = G['module']
FP['U1']['crt'] = [_mx - 9.05, _my - 15.79, _mx + 9.05, _my + 9.81 + 1.3]
META = {r[0]: r for r in CORE + port_refs()}          # ref -> (ref, block, value, fp, fit, function, line)
W, H = G['W'], G['H']
E = html.escape
BOARDS = 5

PALETTE = ['#d9480f', '#1971c2', '#2b8a3e', '#9c36b5', '#e67700', '#0b7285', '#c2255c', '#5c940d', '#495057', '#862e9c']

# ------------------------------------------------------------------ assembly steps
def refs_of(pred):
    return sorted([r for r in META if pred(r)], key=lambda r: (META[r][6], natkey(r)))


def natkey(r):
    import re
    m = re.match(r'([A-Z]+)(\d+)', r)
    return (m.group(1), int(m.group(2))) if m else (r, 0)


FITTED = {r for r, m in META.items() if m[4] == 'Fit'}
PORT_PASSIVE = {r for r in FITTED if META[r][1].startswith('Port') and r[0] in 'RF'}
STEPS = [
    dict(n=1, title='Fine-pitch ICs', refs=['U3', 'U4'], per_ref=True,
         why='Solder these first, while the board is flat and nothing is in the way of the iron.',
         tips=['Flux the pads. Tin <b>one corner pad</b> only.',
               'Place the IC with tweezers, pin 1 on the <b>&#9679;1</b> marker. Reheat the tinned pad so the pin sinks in.',
               'Check alignment on all sides with a loupe. If it is off, reheat and nudge; then tack the opposite corner.',
               'Drag-solder each row: plenty of flux, a little solder on a chisel or hoof tip, pull slowly along the pins.',
               'Bridges: add flux and drag again, or lift with wick. Check every gap against light.'],
         temp='330&ndash;350 &deg;C leaded, 360&ndash;380 &deg;C lead-free'),
    dict(n=2, title='Transistors and 3.3 V regulator', refs=['Q1', 'Q2', 'Q901', 'U2'], per_ref=True,
         why='SOT-23 and SOT-223 only fit one way round, but they are small and easy to lose: do them before the 0805 parts crowd the area.',
         tips=['Tin one pad, place the part, reheat to fix it, then solder the other pads.',
               'AMS1117 (U2): the big tab sits on a copper heat spreader. Use a larger tip and more heat, hold 3&ndash;5 s until the solder flows over the whole tab.',
               'Q1/Q2 are MMBT3904 (marking 1AM). Q901 is AO3400A (marking A09T). Do not mix them up.'],
         temp='SOT-23: 330&ndash;350 &deg;C. U2 tab: 360&ndash;390 &deg;C, larger tip'),
    dict(n=3, title='Core 0805 resistors and capacitors', refs=[r for r in FITTED if META[r][3].endswith(('HandSolder',)) and
                                                                r[0] in 'RC' and not META[r][1].startswith('Port') and r not in ('C1', 'C4')],
         why='Decoupling, reset, auto-reset and LED resistors around the ESP32, CH340C and regulator.',
         tips=['Work one value at a time: open one bag, fit every position of that value on all boards, close the bag.',
               'Tin one pad, slide the part in with tweezers, reheat; then solder the second pad.',
               'Ceramic capacitors have no marking: keep them in their bags until placed.',
               'Look for tombstoning (part standing up) and a clean fillet on both ends.'],
         temp='320&ndash;340 &deg;C leaded, 350&ndash;370 &deg;C lead-free'),
    dict(n=4, title='Port parts fitted by default', refs=sorted(PORT_PASSIVE, key=natkey),
         why='Every port gets its 330 R (A series), 1 k (B series) and 0.5 A PTC. UART and I2C have their own default values. '
             'All other port footprints stay empty (dashed on the diagram) until you configure the port.',
         tips=['Colour = value. Do one colour at a time across all boards.',
               'UART: R704 is 10 k (not 1 k) and R706 is 22 k: together they divide 5 V down for RX.',
               'I2C: R801 and R804 are 100 R, R802 and R805 are 4.7 k pull-ups.',
               'PTCs (1206) have no polarity. They need a little more heat than 0805.',
               'Do <b>not</b> fill the dashed footprints now.'],
         temp='320&ndash;340 &deg;C leaded'),
    dict(n=5, title='Diodes, LEDs and input PTC', refs=['D1', 'D901', 'LED1', 'LED2', 'F1'], per_ref=True,
         why='Polarised parts: check every one against the K marker before soldering the second pad.',
         tips=['D1 SMAJ5.0A and D901 SS34: the <b>band</b> on the body is the cathode and goes on the <b>K</b> marker.',
               'LEDs: the cathode is marked by a green dot/line on top or the bar of the T on the underside. '
               'Not sure? Multimeter in diode mode, red probe on the anode: the LED glows.',
               'LED1 is red (power), LED2 is yellow (status). Do not use blue, green or white here.',
               'F1 (1812) has a lot of copper: use the bigger tip and give it time.'],
         temp='340&ndash;360 &deg;C, larger tip for F1, D1, D901'),
    dict(n=6, title='ESP-32S module', refs=['U1'], per_ref=True,
         why='The module covers nothing else, but once it is on, the area under it is closed. All SMD parts around it are done by now.',
         tips=['Antenna end <b>overhangs the top edge</b> of the board. Pin 1 is top-left (&#9679;1).',
               'Tin pad 1 only. Place the module, align all 38 castellations with the pads, reheat pad 1.',
               'Check alignment on the left, right and bottom rows. Tack pad 38 (top-right), check again.',
               'Drag-solder each side with flux. The pads are extended 1 mm so the iron reaches them.',
               'Optional: feed solder into the 1 mm hole in the centre GND pad from the back.'],
         temp='340&ndash;360 &deg;C, chisel tip'),
    dict(n=7, title='Through-hole parts', refs=['SW1', 'SW2', 'C1', 'C4', 'J1', 'J101', 'J201', 'J301', 'J401', 'J501',
                                                'J601', 'J701', 'J801', 'J901'],
         why='Tallest parts last, so the board lies flat for all the SMD work.',
         tips=['Insert from the top, solder from the bottom. Hold the part flat with a finger or kapton tape.',
               'Solder <b>one pin</b>, check the part sits flat and square, reheat that pin to correct it, then solder the rest.',
               'C1 and C4: the long leg is +, the stripe on the can is &minus;. + goes in the square pad (+ marker).',
               'XH sockets: match the plastic outline to the silkscreen; pin 1 is the square pad.',
               'Trim leads to about 1 mm after soldering (switch and connector pins are already short).'],
         temp='340&ndash;360 &deg;C, larger tip for the ground pins'),
]
STEP_COLORS = ['#c92a2a', '#e67700', '#2b8a3e', '#1971c2', '#9c36b5', '#0b7285', '#5f3dc4']
for s in STEPS:
    s['refs'] = sorted(set(s['refs']), key=natkey)

# sanity: every fitted part is in exactly one step
assigned = [r for s in STEPS for r in s['refs']]
missing = FITTED - set(assigned) - {r for r in FITTED if r.startswith('H')}
dupes = {r for r in assigned if assigned.count(r) > 1}
assert not missing and not dupes, (missing, dupes)
STEP_OF = {r: s['n'] for s in STEPS for r in s['refs']}

POLARITY = {}       # ref -> marker text at pad 1
for r in FITTED:
    if r.startswith(('U', 'Q', 'J')):
        POLARITY[r] = '1'
    elif r.startswith(('D', 'LED')):
        POLARITY[r] = 'K'
    elif r in ('C1', 'C4'):
        POLARITY[r] = '+'

ORIENT = {
    'U3': 'Pin-1 dot/notch on the &#9679;1 marker (top-left)', 'U4': 'Pin-1 dot on the &#9679;1 marker',
    'Q1': 'Fits one way (3 pads)', 'Q2': 'Fits one way (3 pads)', 'Q901': 'Fits one way (3 pads)',
    'U2': 'Big tab = right side', 'D1': 'Band on K (toward +5V)', 'D901': 'Band on K (toward V+)',
    'LED1': 'Cathode on K', 'LED2': 'Cathode on K', 'F1': 'No polarity', 'U1': 'Antenna over top edge, pin 1 top-left',
    'C1': 'Long leg + in square pad', 'C4': 'Long leg + in square pad',
}


def grid(u, v):
    return 'ABCDEFGH'[min(7, max(0, int(u // 10)))] + str(min(7, max(0, int(v // 10))) + 1)


def pkg_short(ref):
    fp = META[ref][3].split(':')[1]
    for k, v in [('SOIC-16', 'SOIC-16'), ('SOT-23-6', 'SOT-23-6'), ('SOT-223', 'SOT-223'), ('SOT-23', 'SOT-23'),
                 ('R_0805', '0805'), ('C_0805', '0805'), ('LED_0805', '0805 LED'), ('Fuse_1206', '1206'),
                 ('Fuse_1812', '1812'), ('D_SMA', 'SMA'), ('CP_Radial', 'Radial 6.3 mm'), ('SW_PUSH', '6x6 THT'),
                 ('B4B-XH', 'XH 4P'), ('B3B-XH', 'XH 3P'), ('ESP32', 'Module'), ('PinHeader_1x05', '1x5 2.54'),
                 ('SolderJumper', 'Jumper'), ('MountingHole', 'M3')]:
        if k in fp:
            return v
    return fp


def value_of(ref):
    key = META[ref][6]
    v = LINES[key]['value'] if key in LINES else META[ref][2]
    if ref.startswith('J') and ref != 'J1':
        v = 'XH 4P socket' if ref != 'J901' else 'XH 3P socket'
    return v.replace(', vertical', '')


# ------------------------------------------------------------------ SVG board drawing
def svg_pad(p, fill, stroke='none', sw=0):
    cx, cy = p['c']
    w, h = p['s']
    a = -p.get('a', 0)
    if p['k'] in ('circ',):
        el = f'<circle cx="{cx}" cy="{cy}" r="{w / 2}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
    else:
        rx = min(w, h) / 2 if p['k'] == 'oval' else (min(w, h) * p.get('rr', 0) if p['k'] == 'rrect' else 0.05)
        el = (f'<rect x="{cx - w / 2}" y="{cy - h / 2}" width="{w}" height="{h}" rx="{rx:.3f}" fill="{fill}" '
              f'stroke="{stroke}" stroke-width="{sw}" transform="rotate({a} {cx} {cy})"/>')
    if p['th'] and p['drill'] > 0:
        el += f'<circle cx="{cx}" cy="{cy}" r="{p["drill"] / 2}" fill="#fff"/>'
    return el


def svg_shape(s, stroke, sw_scale=1.0, fill='none', min_w=0.08):
    w = max(min_w, s['w'] * sw_scale)
    if s['t'] == 'seg':
        return f'<line x1="{s["a"][0]}" y1="{s["a"][1]}" x2="{s["b"][0]}" y2="{s["b"][1]}" stroke="{stroke}" stroke-width="{w}" stroke-linecap="round"/>'
    if s['t'] == 'rect':
        x0, y0 = min(s['a'][0], s['b'][0]), min(s['a'][1], s['b'][1])
        return f'<rect x="{x0}" y="{y0}" width="{abs(s["b"][0] - s["a"][0])}" height="{abs(s["b"][1] - s["a"][1])}" fill="{fill if s.get("f") else "none"}" stroke="{stroke}" stroke-width="{w}"/>'
    if s['t'] == 'circ':
        return f'<circle cx="{s["c"][0]}" cy="{s["c"][1]}" r="{s["r"]}" fill="{fill if s.get("f") else "none"}" stroke="{stroke}" stroke-width="{w}"/>'
    if s['t'] == 'arc':
        (x1, y1), (xm, ym), (x2, y2) = s['a'], s['m'], s['b']
        d = (x1 * (ym - y2) + xm * (y2 - y1) + x2 * (y1 - ym)) * 2
        if abs(d) < 1e-9:
            return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{w}"/>'
        ux = ((x1 ** 2 + y1 ** 2) * (ym - y2) + (xm ** 2 + ym ** 2) * (y2 - y1) + (x2 ** 2 + y2 ** 2) * (y1 - ym)) / d
        uy = ((x1 ** 2 + y1 ** 2) * (x2 - xm) + (xm ** 2 + ym ** 2) * (x1 - x2) + (x2 ** 2 + y2 ** 2) * (xm - x1)) / d
        r = math.hypot(x1 - ux, y1 - uy)
        cross = (xm - x1) * (y2 - y1) - (ym - y1) * (x2 - x1)
        sweep = 1 if cross < 0 else 0
        a1, a2, am = (math.atan2(y - uy, x - ux) for x, y in ((x1, y1), (x2, y2), (xm, ym)))
        large = 0
        return f'<path d="M{x1} {y1} A{r:.3f} {r:.3f} 0 {large} {sweep} {x2} {y2}" fill="none" stroke="{stroke}" stroke-width="{w}"/>'
    if s['t'] == 'poly':
        pts = ' '.join(f'{x},{y}' for x, y in s['p'])
        return f'<polygon points="{pts}" fill="{stroke if s.get("f") else "none"}" stroke="{stroke}" stroke-width="{w}"/>'
    return ''


def text(x, y, s, size, fill='#111', anchor='middle', weight=400, halo=True, rot=0, cls=''):
    tr = f' transform="rotate({rot} {x} {y})"' if rot else ''
    halo_attr = f' stroke="#fff" stroke-width="{size * 0.28:.3f}" paint-order="stroke" stroke-linejoin="round"' if halo else ''
    return (f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" dominant-baseline="central" '
            f'font-weight="{weight}" fill="{fill}"{halo_attr}{tr}{(" class=" + chr(34) + cls + chr(34)) if cls else ""}>{E(s)}</text>')


def board_svg(hl=None, labels=None, dnp_dashed=True, crop=None, width_mm=176, show_grid=True, label_size=0.95,
              marks=True, dim=True, show_texts=True, extra=''):
    """hl: ref -> colour.  labels: ref -> text (defaults to ref for highlighted parts)."""
    hl = hl or {}
    labels = labels if labels is not None else {r: r for r in hl}
    u0, v0, u1, v1 = crop or (-5.5, -8.0, W + 5.5, H + 5.0)
    vw, vh = u1 - u0, v1 - v0
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{u0} {v0} {vw} {vh}" style="width:{width_mm}mm;height:{width_mm * vh / vw:.1f}mm" '
         f'font-family="DejaVu Sans, Liberation Sans, Arial, sans-serif">']
    cr = G['CR']
    # off-board antenna part of the module (dashed)
    mx, my = G['module']
    o.append(f'<rect x="{mx - 9.0}" y="{my - 15.79}" width="18" height="{15.79 - my + 0.0}" fill="none" stroke="#868e96" '
             f'stroke-width="0.12" stroke-dasharray="0.6 0.4"/>')
    if not crop:
        o.append(text(mx, (my - 15.79) / 2, 'antenna overhangs the edge', 1.0, '#868e96', halo=False))
    # board
    o.append(f'<rect x="0" y="0" width="{W}" height="{H}" rx="{cr}" fill="#eef3ee" stroke="#2f3a33" stroke-width="0.25"/>')
    if show_grid and not crop:
        for i in range(1, 8):
            o.append(f'<line x1="{i * 10}" y1="0" x2="{i * 10}" y2="{H}" stroke="#2f3a33" stroke-opacity=".09" stroke-width="0.12"/>')
        for j in range(1, 7):
            o.append(f'<line x1="0" y1="{j * 10}" x2="{W}" y2="{j * 10}" stroke="#2f3a33" stroke-opacity=".09" stroke-width="0.12"/>')
        for i, L in enumerate('ABCDEFGH'):
            cx = min(i * 10 + 5, (i * 10 + W) / 2 if i == 7 else i * 10 + 5)
            o.append(text(cx, -1.6 if i not in (3, 4) else -1.6, L, 1.5, '#495057', weight=700, halo=False) if False else
                     text(cx, H + 2.4, L, 1.5, '#495057', weight=700, halo=False))
        for j in range(7):
            cy = min(j * 10 + 5, (j * 10 + H) / 2 if j == 6 else j * 10 + 5)
            o.append(text(-2.6, cy, str(j + 1), 1.5, '#495057', weight=700, halo=False))
            o.append(text(W + 2.6, cy, str(j + 1), 1.5, '#495057', weight=700, halo=False))
    # mounting holes
    for (hu, hv) in G['holes'].values():
        o.append(f'<circle cx="{hu}" cy="{hv}" r="2.9" fill="none" stroke="#adb5bd" stroke-width="0.12" stroke-dasharray="0.5 0.4"/>'
                 f'<circle cx="{hu}" cy="{hv}" r="1.6" fill="#fff" stroke="#495057" stroke-width="0.15"/>')
    # silkscreen texts + all parts (dimmed)
    if show_texts:
        for t in G['texts']:
            o.append(text(t['c'][0], t['c'][1], t['s'], t['h'] * 0.95, '#7c8a82', anchor=t['j'], halo=False, rot=-t['a']))
    for f in G['fps']:
        r = f['ref']
        if r.startswith('H'):
            continue
        is_dnp = META.get(r, ('', '', '', '', 'Fit'))[4] == 'DNP'
        if r in hl:
            continue
        for s in f['silk']:
            if len(f['silk']) > 60 and s['t'] == 'seg':      # skip electrolytic hatch fill
                continue
            o.append(svg_shape(s, '#a7b2ab', 0.8))
        for s in f['fab']:
            o.append(svg_shape(s, '#c3cbc5', 0.8))
        for p in f['pads']:
            if is_dnp and dnp_dashed:
                o.append(svg_pad(p, 'none', '#868e96', 0.12).replace('stroke-width="0.12"', 'stroke-width="0.12" stroke-dasharray="0.35 0.25"'))
            else:
                o.append(svg_pad(p, '#cdd4cf' if dim else '#b8c0ba'))
    # highlighted parts
    for r, col in hl.items():
        f = FP[r]
        for s in f['fab']:
            o.append(svg_shape(s, col, 1.6, fill=col, min_w=0.16))
        if f['crt']:
            x0, y0, x1, y1 = f['crt']
            o.append(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="0.3" fill="{col}" fill-opacity=".13" stroke="{col}" stroke-width="0.12"/>')
        for p in f['pads']:
            o.append(svg_pad(p, col, '#000', 0.04))
    # polarity markers
    if marks:
        for r, col in hl.items():
            m = POLARITY.get(r)
            if not m:
                continue
            f = FP[r]
            p1 = [p for p in f['pads'] if p['n'] == '1']
            if not p1:
                continue
            p1 = p1[0]
            cx, cy = f['pos']
            if r.startswith('U1'):
                cx, cy = G['module'][0], G['module'][1]
            dx, dy = p1['c'][0] - cx, p1['c'][1] - cy
            n = math.hypot(dx, dy) or 1
            ext = max(p1['s']) / 2 + 0.9
            if r.startswith('J'):          # connectors: put the marker on the board-interior side of pin 1
                ext = 2.0
            mx_, my_ = p1['c'][0] + dx / n * ext, p1['c'][1] + dy / n * ext
            if r.startswith('J'):
                mx_, my_ = p1['c'][0] - dx / n * 0 , p1['c'][1]
                # interior direction = toward board centre
                bx, by = W / 2 - p1['c'][0], H / 2 - p1['c'][1]
                bn = math.hypot(bx, by)
                mx_, my_ = p1['c'][0] + bx / bn * 2.4, p1['c'][1] + by / bn * 2.4
            o.append(f'<circle cx="{mx_:.3f}" cy="{my_:.3f}" r="0.62" fill="#111"/>')
            o.append(text(mx_, my_ + 0.02, m, 0.85, '#fff', weight=700, halo=False))
    # labels
    for r, lab in labels.items():
        f = FP[r]
        if f['crt']:
            x0, y0, x1, y1 = f['crt']
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        else:
            cx, cy = f['pos']
        small = f['crt'] and (f['crt'][2] - f['crt'][0]) * (f['crt'][3] - f['crt'][1]) < 20
        size = label_size if small else label_size * 1.45
        rot = 0
        if small and f['crt'] and (f['crt'][3] - f['crt'][1]) > 1.3 * (f['crt'][2] - f['crt'][0]):
            rot = -90                       # vertical part: run the label along its long side
        if r == 'U1':
            cy += 2
        o.append(text(cx, cy, lab, size, '#111', weight=700, rot=rot))
    o.append(extra)
    o.append('</svg>')
    return ''.join(o)


# ------------------------------------------------------------------ HTML helpers
def boxes(n=BOARDS):
    return ''.join('<td class="tick"><span class="box"></span></td>' for _ in range(n))


def tick_head(n=BOARDS):
    return ''.join(f'<th class="tick">B{i + 1}</th>' for i in range(n))


def step_groups(step):
    """per_ref steps: one row per ref. Otherwise group by BOM line (value + package)."""
    rows = []
    if step.get('per_ref'):
        for i, r in enumerate(step['refs']):
            rows.append(dict(color=PALETTE[i % len(PALETTE)], refs=[r], value=value_of(r), pkg=pkg_short(r),
                             note=ORIENT.get(r, '')))
    else:
        by = {}
        for r in step['refs']:
            by.setdefault(META[r][6], []).append(r)
        for i, (key, rs) in enumerate(sorted(by.items(), key=lambda kv: (-len(kv[1]), kv[0]))):
            note = {'R330': 'A-pin series resistors + UART TX',
                    'R1k': 'B-pin series resistors' if step['n'] == 4 else 'LED resistors (R10 power, R11 status)',
                    'R10k': 'UART RX series (with R706)' if step['n'] == 4 else 'EN pull-up, IO0 pull-up, auto-reset bases', 'R22k': 'UART RX divider bottom', 'R100': 'I2C series' if step['n'] == 4 else 'OUT gate resistor', 'R4k7': 'I2C pull-ups',
                    'PTC050': 'One per port, no polarity', 'C10u': '', 'C100n': 'Decoupling',
                    'C22u': 'Regulator output', 'C1u': 'EN delay', 'R470': 'CH340 TX to ESP RX', 'R100k': 'OUT gate pull-down'}.get(key, '')
            rows.append(dict(color=PALETTE[i % len(PALETTE)], refs=sorted(rs, key=natkey), value=value_of(rs[0]),
                             pkg=pkg_short(rs[0]), note=note))
    return rows


PAGES = []


def page(title, body, kicker=''):
    PAGES.append((title, body, kicker))


def img_uri(path):
    return 'data:image/png;base64,' + base64.b64encode(open(path, 'rb').read()).decode()


# ------------------------------------------------------------------ page 1: cover
n_fit = len([r for r in FITTED if not r.startswith('H')])
n_dnp = len([r for r, m in META.items() if m[4] == 'DNP'])
contents = [('Before you start', 'tools, temperatures, symbols'), ('Board map', 'every part and its step')] + \
           [(f'Step {s["n"]}: {s["title"]}', f'{len(s["refs"])} parts per board') for s in STEPS] + \
           [('Inspection', 'before the first power-up'), ('Tests', 'resistance, voltages, USB, firmware'),
            ('Port options', 'the empty footprints, recipes'), ('VP and OUT jumpers', 'changing 3V3 / 5V'),
            ('Board record', 'one line per board'), ('Parts index', 'every reference with its grid square')]
cover = f'''
<div class="cover-photos"><figure><img src="{img_uri(os.path.join(ROOT, 'docs', 'board_top.png'))}"><figcaption>Top</figcaption></figure>
<figure><img src="{img_uri(os.path.join(ROOT, 'docs', 'board_bottom.png'))}"><figcaption>Bottom</figcaption></figure></div>
<div class="facts">
 <div><b>Board</b>75 &times; 65 mm, 2 layers, 1.6 mm</div>
 <div><b>Parts to solder</b>{n_fit} per board</div>
 <div><b>Left empty</b>{n_dnp} option footprints</div>
 <div><b>Batch</b>{BOARDS} boards (tick columns B1&ndash;B{BOARDS})</div>
</div>
<div class="two">
<div><h3>How to use this guide</h3>
<ol class="tight">
<li>Work through the steps in order. Each step is one page: a board drawing with only that step's parts in colour, and a table.</li>
<li>Do one step on <b>all {BOARDS} boards</b> before moving to the next. Tick the box for each board (B1&ndash;B{BOARDS}) as you finish a line.</li>
<li>Number the boards on the back with a marker so the ticks and test results stay with the right board.</li>
<li>Colours in a step = values. Black dots mark pin 1 (<b>1</b>), cathode (<b>K</b>) or plus (<b>+</b>).</li>
<li>Footprints drawn dashed stay <b>empty</b>. They are options for configuring ports later.</li>
<li>Grid squares (A&ndash;H, 1&ndash;7) help find a part: the parts index on the last page lists every reference.</li>
</ol></div>
<div><h3>Contents</h3><table class="toc">{''.join(f'<tr><td>{E(a)}</td><td class="muted">{E(b)}</td><td class="pg">{{pg:{E(a)}}}</td></tr>' for a, b in contents)}</table></div>
</div>'''
page('ESP32 Modular Base v2.0: assembly guide', cover, 'Hand assembly · rev 2.0 · 2026-10')

# ------------------------------------------------------------------ page 2: before you start
legend_svg = ('<svg viewBox="0 0 60 14" style="width:120mm;height:28mm" font-family="DejaVu Sans, Arial">'
              '<rect x="1" y="2" width="5" height="3" rx=".4" fill="#1971c2"/>' + text(8, 3.5, 'part of this step (colour = value)', 1.6, anchor='start', halo=False) +
              '<rect x="1" y="7" width="5" height="3" rx=".4" fill="#cdd4cf"/>' + text(8, 8.5, 'already fitted or later step', 1.6, anchor='start', halo=False) +
              '<rect x="34" y="2" width="5" height="3" rx=".4" fill="none" stroke="#868e96" stroke-width=".15" stroke-dasharray=".5 .35"/>' + text(41, 3.5, 'leave empty (option)', 1.6, anchor='start', halo=False) +
              '<circle cx="36.5" cy="8.5" r="1.1" fill="#111"/>' + text(36.5, 8.55, '1', 1.4, '#fff', weight=700, halo=False) +
              text(39, 8.5, 'pin 1 · K cathode · + plus', 1.6, anchor='start', halo=False) + '</svg>')
prep = f'''
<div class="two">
<div><h3>Tools</h3>
<table class="list">
<tr><td>Soldering iron</td><td>Temperature controlled. Chisel or hoof tip 1.6&ndash;2.4 mm for drag soldering, a fine conical tip for 0805, a big chisel for the regulator tab and THT ground pins.</td></tr>
<tr><td>Solder</td><td>0.5&ndash;0.8 mm wire with flux core. Leaded 63/37 is easiest; lead-free SAC305 needs about 30 &deg;C more.</td></tr>
<tr><td>Flux</td><td>No-clean flux pen or gel. Use plenty on the CH340C, USBLC6 and the module.</td></tr>
<tr><td>Desoldering wick</td><td>1.5&ndash;2 mm, for bridges.</td></tr>
<tr><td>Tweezers</td><td>Fine straight or curved, non-magnetic if possible.</td></tr>
<tr><td>Magnification</td><td>10&times; loupe or a USB microscope for checking IC pins and the module.</td></tr>
<tr><td>Cleaning</td><td>Isopropyl alcohol (99 %) and an old toothbrush.</td></tr>
<tr><td>Multimeter</td><td>Continuity, diode test, DC volts.</td></tr>
<tr><td>Other</td><td>Kapton tape, side cutters, a USB-A to C cable, a PC with a USB port.</td></tr>
</table>
<h3>Iron temperature (guide)</h3>
<table class="list"><tr><td>0805, SOT-23</td><td>320&ndash;340 &deg;C leaded &middot; 350&ndash;370 &deg;C lead-free</td></tr>
<tr><td>SOIC, module</td><td>330&ndash;360 &deg;C leaded &middot; 360&ndash;380 &deg;C lead-free</td></tr>
<tr><td>U2 tab, F1, THT GND pins</td><td>360&ndash;390 &deg;C with a large tip, hold longer</td></tr></table>
</div>
<div><h3>Prepare the boards</h3>
<ol class="tight">
<li>Check each bare PCB: no scratches across tracks, holes clear, edges clean.</li>
<li>Number the boards 1&ndash;{BOARDS} on the back (marker, near a corner).</li>
<li>Continuity check on one bare board: <b>+5V to GND</b> and <b>+3V3 to GND</b> must be open (no beep).
   Probe +5V on the C1 square pad, +3V3 on the C4 square pad, GND on any port pin <b>G</b>.</li>
<li>Sort the parts by step. Keep each value in its own labelled bag; unmarked 0805 capacitors look identical.</li>
<li>Work on an ESD mat or touch a grounded object before handling the CH340C, USBLC6 and the module.</li>
</ol>
<h3>Symbols on the drawings</h3>{legend_svg}
<h3>Good joint, bad joint</h3>
<ul class="tight"><li><b>Good:</b> shiny (leaded) or satin (lead-free), concave fillet from pad to part, pad fully wetted.</li>
<li><b>Cold:</b> grey, lumpy, ball sitting on the pad. Reheat with flux.</li>
<li><b>Bridge:</b> solder joining two pins. Flux + drag, or wick.</li>
<li><b>Tombstone:</b> 0805 standing on one end. Reheat the high end and press down.</li></ul>
</div></div>'''
page('Before you start', prep, 'Tools · temperatures · symbols')

# ------------------------------------------------------------------ page 3: board map
hl = {r: STEP_COLORS[STEP_OF[r] - 1] for r in STEP_OF}
legend = ''.join(f'<span class="chip"><span class="sw" style="background:{STEP_COLORS[s["n"] - 1]}"></span>Step {s["n"]} {E(s["title"])}</span>' for s in STEPS)
conn = '''<table class="list small"><tr><th>Connector</th><th>Where</th><th>Pins (pin 1 = square pad)</th></tr>
<tr><td>J1 USB in</td><td>top right</td><td>5V, D&minus;, D+, G</td></tr>
<tr><td>J101&ndash;J401 P1&ndash;P4</td><td>bottom</td><td>G, VP, A, B</td></tr>
<tr><td>J501, J601 P5, P6</td><td>left</td><td>G, VP, A, B</td></tr>
<tr><td>J701 UART, J801 I2C</td><td>right</td><td>G, VP, TX, RX / G, VP, SDA, SCL</td></tr>
<tr><td>J901 OUT</td><td>right, low</td><td>G, V+, OUT</td></tr>
<tr><td>SW1 RESET, SW2 BOOT</td><td>top left</td><td>&ndash;</td></tr></table>'''
page('Board map', f'<div class="diagram">{board_svg(hl, labels={r: r for r in hl}, label_size=0.62)}</div>'
     f'<div class="chips">{legend}</div>{conn}', 'All fitted parts, coloured by assembly step')

# ------------------------------------------------------------------ step pages
for s in STEPS:
    groups = step_groups(s)
    hl = {}
    for g in groups:
        for r in g['refs']:
            hl[r] = g['color']
    big = s['n'] in (1, 2, 5, 6, 7)
    diagram = board_svg(hl, label_size=1.0 if big else 1.12, dnp_dashed=True,
                        width_mm=176 if len(groups) <= 5 else 142)
    rows = ''
    for g in groups:
        refs_txt = ' '.join(g['refs'])
        locs = ' '.join(sorted({grid(*FP[r]['pos']) for r in g['refs']}))
        rows += (f'<tr><td><span class="sw" style="background:{g["color"]}"></span></td>'
                 f'<td class="num">{len(g["refs"])}</td><td><b>{E(g["value"])}</b></td><td class="mono">{E(refs_txt)}</td>'
                 f'<td>{E(g["pkg"])}</td><td class="mono small">{locs}</td><td class="small">{g["note"]}</td>{boxes()}</tr>')
    table = (f'<table class="parts"><thead><tr><th></th><th>Qty</th><th>Value</th><th>References</th><th>Package</th>'
             f'<th>Grid</th><th>Orientation / note</th>{tick_head()}</tr></thead><tbody>{rows}</tbody></table>')
    tips = ''.join(f'<li>{t}</li>' for t in s['tips'])
    body = (f'<p class="why">{s["why"]}</p><div class="diagram">{diagram}</div>{table}'
            f'<div class="tipbox"><div class="temp">Iron: {s["temp"]}</div><ul class="tight">{tips}</ul></div>')
    page(f'Step {s["n"]}: {s["title"]}', body, f'{len(s["refs"])} parts per board · {len(s["refs"]) * BOARDS} for {BOARDS} boards')

# ------------------------------------------------------------------ inspection
pol = ['U3', 'U4', 'U2', 'Q1', 'Q2', 'Q901', 'D1', 'D901', 'LED1', 'LED2', 'C1', 'C4', 'U1']
pol_rows = ''.join(f'<tr><td class="mono"><b>{r}</b></td><td>{E(value_of(r))}</td><td>{ORIENT.get(r, "")}</td><td class="mono">{grid(*FP[r]["pos"])}</td>{boxes()}</tr>' for r in pol)
checks = [('U3 CH340C', 'No bridges between the 16 pins; all pins wetted (look from both sides)'),
          ('U4 USBLC6', 'No bridges; pin 2 (GND) and pin 5 (+5V) joined to their vias'),
          ('U1 module', 'All 38 castellations wetted; no bridge on the left, right or bottom row'),
          ('U2 regulator', 'Tab fully soldered to the copper area; three small pins wetted'),
          ('0805 parts', 'No tombstones, no missing parts in the tables, fillets on both ends'),
          ('Empty footprints', 'Dashed option footprints are still empty and free of solder blobs'),
          ('Solder jumpers', 'JP101&ndash;JP801 untouched (copper trace still joins the factory pads); JP901 open'),
          ('Cleaning', 'Flux removed with isopropyl alcohol; board dry'),
          ('Loose solder', 'No solder balls or wire clippings on the board (shake it, look under the module)')]
chk_rows = ''.join(f'<tr><td><b>{a}</b></td><td>{b}</td>{boxes()}</tr>' for a, b in checks)
insp = (f'<p class="why">Do this under magnification before any power is applied. Most first-power failures are a bridge on the CH340C or the module, or a part the wrong way round.</p>'
        f'<h3>Polarity and orientation, part by part</h3><table class="parts"><thead><tr><th>Ref</th><th>Part</th><th>Must be</th><th>Grid</th>{tick_head()}</tr></thead><tbody>{pol_rows}</tbody></table>'
        f'<h3>Solder joints and cleanliness</h3><table class="parts"><thead><tr><th>Area</th><th>Check</th>{tick_head()}</tr></thead><tbody>{chk_rows}</tbody></table>')
page('Inspection', insp, 'Before the first power-up')

# ------------------------------------------------------------------ tests
def meas_rows(items):
    return ''.join(f'<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td>{"".join("<td class=meas></td>" for _ in range(BOARDS))}</tr>' for a, b, c in items)


res = [('+5V to GND', 'C1 square pad (+) &rarr; any port G', 'Starts low, climbs (capacitors charging); must end above ~1 k&Omega;. Under 50 &Omega; = short.'),
       ('+3V3 to GND', 'C4 square pad (+) &rarr; any port G', 'Same: climbs to above ~1 k&Omega;.'),
       ('+5V to +3V3', 'C1 + &rarr; C4 +', 'Not a short (above ~1 k&Omega;).'),
       ('VBUS to +5V', 'J1 pin 5V &rarr; C1 +', 'Under 1 &Omega; (through the PTC F1).')]
volts = [('VBUS (USB in)', 'J1 pin 5V &rarr; G', '4.75&ndash;5.25 V'),
         ('+5V', 'C1 + &rarr; G', '4.7&ndash;5.2 V (a little under VBUS)'),
         ('+3V3', 'C4 + &rarr; G', '3.23&ndash;3.37 V'),
         ('Power LED', 'LED1 (red)', 'On'),
         ('Regulator', 'Touch U2 after 1 minute', 'Warm at most, never too hot to touch'),
         ('EN', 'R1 pad on the EN side &rarr; G', '3.3 V (RESET not pressed)'),
         ('Port VP', 'Pin V of P1&ndash;P6 and I2C &rarr; G', '3.3 V'),
         ('UART VP', 'Pin V of UART &rarr; G', '5 V'),
         ('I2C idle', 'DA and CL pins &rarr; G', '3.3 V (pull-ups)')]
tests = (f'<p class="why">Write the reading for each board in its column. Stop at the first wrong value and look for the cause before going on.</p>'
         f'<h3>1. Resistance, power off</h3><table class="parts meas"><thead><tr><th>Check</th><th>Probe</th><th>Expected</th>{tick_head()}</tr></thead><tbody>{meas_rows(res)}</tbody></table>'
         f'<h3>2. First power-up</h3><p class="small">Power from the USB-C breakout with an A-to-C cable. A USB power meter in line is useful: '
         f'note the current. If anything gets hot or the power LED does not light, unplug at once.</p>'
         f'<table class="parts meas"><thead><tr><th>Check</th><th>Probe</th><th>Expected</th>{tick_head()}</tr></thead><tbody>{meas_rows(volts)}</tbody></table>')
page('Tests (1/2): resistance and voltages', tests, 'Multimeter checks')

test_yaml = '''esphome:
  name: modbase-test
esp32:
  board: esp32dev
logger:
wifi:
  ap:
    ssid: "modbase-test"
captive_portal:
web_server:
  port: 80
status_led:
  pin: GPIO2
binary_sensor:
  - platform: gpio
    name: "BOOT button"
    pin: {number: GPIO0, inverted: true}
switch:
  - {platform: gpio, name: "P1 A", pin: GPIO25}
  - {platform: gpio, name: "P2 A", pin: GPIO26}
  - {platform: gpio, name: "P3 A", pin: GPIO27}
  - {platform: gpio, name: "P4 A", pin: GPIO13}
  - {platform: gpio, name: "P5 A", pin: GPIO4}
  - {platform: gpio, name: "P6 A", pin: GPIO18}
  - {platform: gpio, name: "UART TX", pin: GPIO17}
  - {platform: gpio, name: "OUT", pin: GPIO23}'''
fn = [('USB serial', 'Plug into the PC', 'CH340 appears: COMx (Windows) / ttyUSB0 (Linux)'),
      ('Flash', 'Flash the test config below', 'Auto-reset works; if not, hold BOOT, tap RESET'),
      ('Status LED', 'After boot', 'LED2 (yellow) blinks while Wi-Fi is not connected'),
      ('Wi-Fi', 'Connect to AP "modbase-test", open 192.168.4.1', 'Web page with the switches'),
      ('BOOT button', 'Press SW2, watch the web page', 'BOOT button turns ON'),
      ('RESET', 'Press SW1', 'Board restarts (LED2 blinks again)'),
      ('Port A pins', 'Switch each A on, measure pin A &rarr; G', '3.3 V on, 0 V off (P1&ndash;P6)'),
      ('UART TX', 'Switch UART TX, measure TX &rarr; G', '3.3 V / 0 V'),
      ('OUT', 'LED + 1 k&Omega; from UART pin V (5 V) to OUT pin', 'LED on when OUT switch is on')]
fn_rows = ''.join(f'<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td>{boxes()}</tr>' for a, b, c in fn)
tests2 = (f'<h3>3. USB, firmware and function</h3><table class="parts"><thead><tr><th>Check</th><th>How</th><th>Expected</th>{tick_head()}</tr></thead><tbody>{fn_rows}</tbody></table>'
          f'<div class="two"><div><h3>Test firmware (ESPHome)</h3><pre class="code">{E(test_yaml)}</pre></div>'
          f'<div><h3>Notes</h3><ul class="tight"><li>Flash over USB: <span class="mono">esphome run modbase-test.yaml</span> and pick the CH340 port.</li>'
          f'<li>ESPHome warns that GPIO0 and GPIO2 are strapping pins: expected, they are the BOOT button and status LED.</li>'
          f'<li>The A pins are measured at the connector, through the 330 R: with nothing connected you read the full 3.3 V.</li>'
          f'<li>B pins are inputs; test them when you configure a port (NTC, pulse, divider).</li>'
          f'<li>IO36/IO39 (P1/P2 B) cannot drive anything: they are input-only.</li>'
          f'<li>When the board passes, flash your real configuration over USB or OTA.</li>'
          f'<li>Mains: this board is low voltage only. Keep relay modules and meters behind the divider in the box, and flash with mains disconnected.</li></ul></div></div>')
page('Tests (2/2): USB, firmware and function', tests2, 'With the board on USB')

# ------------------------------------------------------------------ port options
p1 = {f'R10{i}' for i in range(1, 7)} | {'C101', 'F101', 'JP101', 'J101'}
pos_name = {'R101': 'RA', 'R102': 'RAU', 'R103': 'RAD', 'R104': 'RB', 'R105': 'RBU', 'R106': 'RBD', 'C101': 'CB',
            'F101': 'F', 'JP101': 'JP', 'J101': 'J'}
hl = {r: ('#2b8a3e' if META[r][4] == 'Fit' else '#e67700') for r in p1}
labels = {r: f'{pos_name[r]}' for r in p1}
x0 = min(FP[r]['crt'][0] for r in p1) - 1.2
y0 = min(FP[r]['crt'][1] for r in p1) - 1.2
x1 = max(FP[r]['crt'][2] for r in p1) + 1.2
y1 = H + 0.6
zoom = board_svg(hl, labels=labels, crop=(x0, y0, x1, y1), width_mm=92, label_size=0.8, show_texts=True)
posrows = ''.join(f'<tr><td class="mono"><b>{p}</b></td><td class="mono">{pat}</td><td>{d}</td><td>{role}</td></tr>' for p, pat, d, role in [
    ('RA', 'Rn01', '330 R fitted', 'Series resistor, connector A &harr; GPIO'),
    ('RAU', 'Rn02', 'empty', 'Pull-up, A to 3V3 (connector side)'),
    ('RAD', 'Rn03', 'empty', 'Pull-down, A to GND'),
    ('RB', 'Rn04', '1 k fitted', 'Series resistor, connector B &harr; GPIO'),
    ('RBU', 'Rn05', 'empty', 'Pull-up, B to 3V3 (connector side)'),
    ('RBD', 'Rn06', 'empty', 'B to GND on the GPIO side (divider bottom)'),
    ('CB', 'Cn01', 'empty', 'Filter capacitor, B to GND on the GPIO side'),
    ('F', 'Fn01', '0.5 A PTC', 'Protects VP'), ('JP', 'JPn01', 'trace 3V3', 'VP source jumper')])
ports_rows = ''.join(f'<tr><td><b>{lab}</b></td><td class="mono">{n}01&ndash;{n}06</td><td class="mono">{ga}</td><td class="mono">{gb}</td><td>{vp}</td></tr>'
                     for n, (lab, ga, gb, vp, ov) in PORTS.items())
rec_rows = ''.join(f'<tr><td><b>{E(j)}</b></td><td>{E(pin)}</td><td>{E(vp)}</td><td>{E(fitv)}</td><td class="mono small">{E(ex)}</td></tr>'
                   for j, pin, vp, fitv, esp, ex, note in RECIPES)
opts = (f'<p class="why">Every port has the same layout. Port <i>n</i> uses references with that number: P1 = R101&hellip;R106, C101, F101, JP101. '
        f'Green = fitted in step 4, orange = empty until you need it. Drawing: P1 at the bottom-left corner of the board.</p>'
        f'<div class="two"><div class="diagram">{zoom}</div><div><table class="list small"><tr><th>Pos.</th><th>Ref</th><th>Default</th><th>Job</th></tr>{posrows}</table>'
        f'<table class="list small" style="margin-top:3mm"><tr><th>Port</th><th>Refs</th><th>A</th><th>B</th><th>VP</th></tr>{ports_rows}</table></div></div>'
        f'<h3>What to fit for each job</h3><table class="list small"><tr><th>Job</th><th>Pin</th><th>VP</th><th>Fit (on top of defaults)</th><th>Example on P3</th></tr>{rec_rows}</table>')
page('Port options', opts, 'Configuring a port later')

# ------------------------------------------------------------------ jumpers
def jumper_svg(state):
    """state: 'factory33', 'cut', 'set5'"""
    o = ['<svg viewBox="0 0 30 16" style="width:56mm;height:30mm" font-family="DejaVu Sans, Arial">']
    xs = [6, 15, 24]
    o.append('<rect x="1" y="1" width="28" height="14" rx="1" fill="#eef3ee" stroke="#adb5bd" stroke-width=".15"/>')
    if state in ('factory33',):
        o.append('<rect x="7" y="7.1" width="7" height="1.8" fill="#c08a2e"/>')
    if state == 'cut':
        o.append('<rect x="7" y="7.1" width="2.4" height="1.8" fill="#c08a2e"/><rect x="11.6" y="7.1" width="2.4" height="1.8" fill="#c08a2e"/>')
        o.append('<line x1="10.5" y1="4.5" x2="10.5" y2="11.5" stroke="#c92a2a" stroke-width=".5" stroke-dasharray="1 .6"/>')
    if state == 'set5':
        o.append('<rect x="7" y="7.1" width="2.4" height="1.8" fill="#c08a2e"/><rect x="11.6" y="7.1" width="2.4" height="1.8" fill="#c08a2e"/>')
        o.append('<ellipse cx="19.5" cy="8" rx="5.6" ry="2.6" fill="#adb5bd" stroke="#495057" stroke-width=".2"/>')
    for i, x in enumerate(xs):
        o.append(f'<rect x="{x - 2}" y="5" width="4" height="6" rx=".9" fill="#d4a24c" stroke="#7a5b1c" stroke-width=".2"/>')
    o.append(text(6, 13.3, '3V3', 1.6, halo=False, weight=700))
    o.append(text(15, 13.3, 'VP', 1.6, halo=False, weight=700))
    o.append(text(24, 13.3, '5V', 1.6, halo=False, weight=700))
    o.append(text(6, 2.9, 'near connector', 1.2, '#495057', halo=False))
    o.append('</svg>')
    return ''.join(o)


jp_rows = ''.join(f'<tr><td><b>{lab}</b></td><td class="mono">JP{n}01</td><td>{vp}</td><td class="mono">{grid(*FP[f"JP{n}01"]["pos"])}</td>'
                  f'<td></td><td></td></tr>' for n, (lab, ga, gb, vp, ov) in PORTS.items())
jump = f'''
<p class="why">Each port's supply pin <b>VP</b> comes from a three-pad solder jumper. The pad <b>nearest the connector is 3V3</b>, the far pad is 5V, the middle pad is VP.
The board ships with a thin copper trace joining the default pair: 3V3 on P1&ndash;P6 and I2C, <b>5V on UART</b>.</p>
<div class="jrow"><figure>{jumper_svg('factory33')}<figcaption>1. As made: 3V3 joined by a trace</figcaption></figure>
<figure>{jumper_svg('cut')}<figcaption>2. Cut the trace between the pads</figcaption></figure>
<figure>{jumper_svg('set5')}<figcaption>3. Bridge VP to 5V with solder</figcaption></figure></div>
<h3>Changing a port to 5V</h3>
<ol class="tight"><li>Power off. Find the jumper (table below), between the connector and the PTC.</li>
<li>Cut the trace between the 3V3 pad and the middle pad with a sharp hobby knife: two or three light strokes, across the gap only.</li>
<li>Check with the multimeter: <b>no continuity</b> between the two pads.</li>
<li>Add flux and bridge the middle pad to the 5V pad with a blob of solder.</li>
<li>Check: VP pin of the connector reads 5 V after power-up. Write the change in the table.</li>
<li>To go back: remove the blob with wick, bridge the 3V3 side with solder instead (the trace is gone).</li></ol>
<p class="small">Only switch a port to 5V for a device that needs it, and only if the device's signal into the ESP32 stays at 3.3 V
(or the port has the 10 k / 22 k divider on B). The ESP32 pins are not 5 V tolerant.</p>
<table class="list"><tr><th>Port</th><th>Jumper</th><th>Default</th><th>Grid</th><th>Changed to</th><th>Date</th></tr>{jp_rows}</table>
<h3>JP901: OUT supply</h3>
<p>JP901 is a two-pad jumper next to the OUT connector, <b>open</b> as made. Bridge it only to power a 5 V load from the board (pin V+ then carries +5V).
<b>Never bridge it while an external 12/24 V supply is on V+</b>: that would feed 12/24 V into the board's 5 V rail.</p>'''
page('VP and OUT jumpers', jump, 'Changing a port between 3V3 and 5V')

# ------------------------------------------------------------------ board record
rec_cols = ['Board', 'Assembled', 'Inspected', '+5V (V)', '+3V3 (V)', 'Current (mA)', 'USB / flash', 'Ports OK', 'Changes made / notes']
rec_rows = ''.join('<tr>' + f'<td class="mono"><b>B{i + 1}</b></td>' + ''.join('<td></td>' for _ in rec_cols[1:]) + '</tr>' for i in range(BOARDS))
record = (f'<p class="why">One line per board. Keep this page with the boards; it is the record of what was built and how each one tested.</p>'
          f'<table class="record"><tr>{"".join(f"<th>{c}</th>" for c in rec_cols)}</tr>{rec_rows}</table>'
          f'<h3>Port configuration per board</h3><p class="small">Write what is plugged into each port and which option parts you fitted (for example "NTC: R305 10k1%, C301 100n").</p>'
          f'<table class="record"><tr><th>Board</th>{"".join(f"<th>{p[0]}</th>" for p in PORTS.values())}<th>OUT</th></tr>'
          + ''.join(f'<tr class="tall"><td class="mono"><b>B{i + 1}</b></td>' + ''.join('<td></td>' for _ in range(len(PORTS) + 1)) + '</tr>' for i in range(BOARDS))
          + '</table>')
page('Board record', record, 'Assembly and test results')

# ------------------------------------------------------------------ parts index
allrefs = sorted([r for r in META if not r.startswith('H')], key=natkey)
def idx_row(r):
    fit = META[r][4]
    st = STEP_OF.get(r)
    what = f'step {st}' if st else ('empty (option)' if fit == 'DNP' else ('jumper' if r.startswith('JP') else fit.lower()))
    val = value_of(r) if fit == 'Fit' else ('&ndash;' if r.startswith('JP') else 'empty')
    return f'<tr class="{"dnp" if fit != "Fit" else ""}"><td class="mono"><b>{r}</b></td><td>{val if val.startswith("&") else E(val)}</td><td>{E(pkg_short(r))}</td><td class="mono">{grid(*FP[r]["pos"])}</td><td>{what}</td></tr>'
half = (len(allrefs) + 1) // 2
cols = [allrefs[:half], allrefs[half:]]
idx = ''.join(f'<table class="index"><tr><th>Ref</th><th>Value</th><th>Pkg</th><th>Grid</th><th>When</th></tr>{"".join(idx_row(r) for r in c)}</table>' for c in cols)
page('Parts index', f'<div class="idx">{idx}</div>', f'All {len(allrefs)} references · grid squares as on the drawings')

# ------------------------------------------------------------------ assemble HTML
css = '''
@page { size: A4 portrait; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: #fff; }
body { font: 9pt/1.35 "DejaVu Sans", "Liberation Sans", Arial, sans-serif; color: #15191c; }
.page { width: 210mm; height: 297mm; padding: 11mm 12mm 9mm; position: relative; overflow: hidden; page-break-after: always; break-after: page; }
.page:last-child { page-break-after: auto; break-after: auto; }
.hd { display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 2px solid #15191c; padding-bottom: 2mm; margin-bottom: 3mm; }
.hd h1 { font-size: 16pt; margin: 0; letter-spacing: -.01em; }
.hd .k { font-size: 8.5pt; color: #5c666c; text-align: right; }
.ft { position: absolute; left: 12mm; right: 12mm; bottom: 5mm; display: flex; justify-content: space-between; font-size: 7.5pt; color: #6c757d; border-top: .3mm solid #ced4da; padding-top: 1mm; }
h3 { font-size: 10.5pt; margin: 3.5mm 0 1.5mm; }
p { margin: 0 0 2mm; }
.why { font-size: 9.5pt; color: #343a40; }
.small { font-size: 8pt; }
.muted { color: #6c757d; }
.mono { font-family: "DejaVu Sans Mono", "Liberation Mono", monospace; font-size: 8pt; }
.diagram { display: flex; justify-content: center; margin: 1mm 0 2mm; }
table { border-collapse: collapse; width: 100%; }
table.parts th, table.list th, table.index th, table.record th { text-align: left; font-size: 7.5pt; text-transform: uppercase; letter-spacing: .03em; color: #495057; border-bottom: .4mm solid #343a40; padding: 1mm 1.2mm; }
table.parts td, table.list td { border-bottom: .2mm solid #dee2e6; padding: 1.1mm 1.2mm; vertical-align: top; }
table.parts td.num { text-align: right; font-weight: 700; }
th.tick, td.tick { width: 7mm; text-align: center; padding-left: 0; padding-right: 0; }
.box { display: inline-block; width: 4mm; height: 4mm; border: .35mm solid #212529; border-radius: .5mm; }
table.meas td.meas, table.meas th.tick { width: 13mm; border-left: .2mm solid #dee2e6; }
.sw { display: inline-block; width: 4mm; height: 4mm; border-radius: .8mm; vertical-align: middle; }
.tipbox { border: .3mm solid #adb5bd; border-left: 1.4mm solid #1971c2; border-radius: 1mm; padding: 2mm 3mm; margin-top: 3mm; background: #f8f9fa; }
.tipbox .temp { font-weight: 700; margin-bottom: 1mm; }
ul.tight, ol.tight { margin: 0; padding-left: 5mm; }
ul.tight li, ol.tight li { margin: .6mm 0; }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 6mm; }
.chips { display: flex; flex-wrap: wrap; gap: 1.5mm 4mm; margin: 1mm 0 3mm; font-size: 8pt; }
.chip { display: inline-flex; align-items: center; gap: 1.5mm; }
.cover-photos { display: grid; grid-template-columns: 1fr 1fr; gap: 5mm; margin: 2mm 0 4mm; }
.cover-photos figure { margin: 0; text-align: center; }
.cover-photos img { width: 100%; border-radius: 1.5mm; }
.cover-photos figcaption { font-size: 8pt; color: #6c757d; }
.facts { display: grid; grid-template-columns: repeat(4, 1fr); gap: 3mm; margin-bottom: 3mm; }
.facts div { border: .3mm solid #ced4da; border-radius: 1mm; padding: 2mm; font-size: 9pt; }
.facts b { display: block; font-size: 7.5pt; text-transform: uppercase; color: #6c757d; letter-spacing: .03em; }
table.toc td { padding: .9mm 1mm; border-bottom: .2mm dotted #ced4da; }
table.toc td.pg { text-align: right; font-weight: 700; width: 8mm; }
table.list.small td, table.list.small th { font-size: 8pt; padding: .8mm 1mm; }
pre.code { font: 7.4pt/1.32 "DejaVu Sans Mono", monospace; background: #f1f3f5; border-radius: 1mm; padding: 2mm 3mm; margin: 0; white-space: pre; }
.jrow { display: flex; justify-content: space-between; gap: 3mm; margin: 2mm 0; }
.jrow figure { margin: 0; text-align: center; font-size: 8pt; }
table.record th, table.record td { border: .25mm solid #868e96; padding: 1mm; font-size: 8pt; }
table.record td { height: 11mm; }
table.record tr.tall td { height: 16mm; }
.idx { display: grid; grid-template-columns: 1fr 1fr; gap: 5mm; }
table.index td { font-size: 7.3pt; padding: .35mm 1mm; border-bottom: .15mm solid #e9ecef; }
table.index tr.dnp td { color: #868e96; }
'''
total = len(PAGES)
pg_of = {t: i + 1 for i, (t, b, k) in enumerate(PAGES)}
pg_of.update({'Before you start': pg_of['Before you start'], 'Board map': pg_of['Board map'],
              'Inspection': pg_of['Inspection'], 'Tests': pg_of['Tests (1/2): resistance and voltages'],
              'Port options': pg_of['Port options'], 'VP and OUT jumpers': pg_of['VP and OUT jumpers'],
              'Board record': pg_of['Board record'], 'Parts index': pg_of['Parts index']})
out = [f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Modular Base Assembly Guide</title><style>{css}</style></head><body>']
for i, (title, body, kicker) in enumerate(PAGES):
    for t, p in pg_of.items():
        body = body.replace('{pg:' + E(t) + '}', str(p))
    out.append(f'<section class="page"><div class="hd"><h1>{E(title)}</h1><div class="k">{E(kicker)}</div></div>{body}'
               f'<div class="ft"><span>ESP32 Modular Base v2.0 &middot; assembly guide</span><span>page {i + 1} / {total}</span></div></section>')
out.append('</body></html>')
open(OUT, 'w').write(''.join(out))
print('pages', total, '->', OUT)
