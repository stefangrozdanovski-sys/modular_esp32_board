#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
"""Generate a KiCad 7 schematic from design.py (label-based connectivity)."""
import re, sys, uuid
sys.path.insert(0, __import__('os').path.dirname(__file__))
from design import PARTS, POWER_NETS, NOTES, PROJECT, PAPER, TITLE, REV, DATE, COMMENT

OUT = sys.argv[1]
import random
random.seed(20261013)
U = lambda: str(uuid.UUID(int=random.getrandbits(128), version=4))
NS = uuid.UUID('6f1c2d0e-8a4b-4c55-9d3e-2b7a1e0f9c11')
SYMU = lambda ref: str(uuid.uuid5(NS, 'sym-' + ref))
ROOT = str(uuid.uuid5(NS, 'root'))
SYMDIR = '/usr/share/kicad/symbols'
_cache = {}

def lib_text(lib):
    if lib not in _cache:
        _cache[lib] = open(f'{SYMDIR}/{lib}.kicad_sym').read()
    return _cache[lib]

def block(s, name):
    i = s.find(f'(symbol "{name}"')
    if i < 0:
        raise KeyError(name)
    d = 0; j = i
    while True:
        c = s[j]
        if c == '(':
            d += 1
        elif c == ')':
            d -= 1
            if d == 0:
                break
        j += 1
    return s[i:j + 1]

def props_of(b):
    """top-level property blocks of a symbol"""
    out = {}
    for m in re.finditer(r'\(property "([^"]+)" "', b):
        st = m.start(); d = 0; j = st
        while True:
            c = b[j]
            if c == '(':
                d += 1
            elif c == ')':
                d -= 1
                if d == 0:
                    break
            j += 1
        out[m.group(1)] = b[st:j + 1]
    return out

def flat_symbol(lib_id):
    """Return the symbol definition flattened (extends resolved), named lib:name."""
    lib, name = lib_id.split(':')
    s = lib_text(lib)
    b = block(s, name)
    m = re.search(r'\(extends "([^"]+)"\)', b[:400])
    if m:
        parent = m.group(1)
        pb = block(s, parent)
        if re.search(r'\(extends "', pb[:400]):
            raise RuntimeError('nested extends not handled')
        child_props = props_of(b)
        par_props = props_of(pb)
        body = pb
        for k, v in par_props.items():
            if k in child_props:
                body = body.replace(v, child_props[k], 1)
        body = body.replace(f'(symbol "{parent}"', f'(symbol "{name}"', 1)
        body = body.replace(f'(symbol "{parent}_', f'(symbol "{name}_')
        b = body
    b = b.replace(f'(symbol "{name}"', f'(symbol "{lib_id}"', 1)
    return b

def sym_pins(flat):
    pins = []
    for m in re.finditer(r'\(pin (\w+) (\w+) \(at ([-\d.]+) ([-\d.]+) (\d+)\) \(length ([\d.]+)\)(.*?)\(name "([^"]*)".*?\(number "([^"]*)"', flat, re.S):
        etype, style, x, y, ang, ln, mid, nm, num = m.groups()
        pins.append(dict(num=num, name=nm, x=float(x), y=float(y), ang=int(ang), hidden=('hide' in mid)))
    return pins

def r2(v):
    return round(v, 2)

items = []
lib_defs = {}
pwr_idx = [0]

def add_power(net, x, y, rot=0):
    pwr_idx[0] += 1
    lid = f'power:{net}'
    if lid not in lib_defs:
        lib_defs[lid] = flat_symbol(lid)
    ref = f'#PWR{pwr_idx[0]:02d}'
    below = (net == 'GND') != (rot == 180)
    vy = y + 3.81 if below else y - 3.81
    items.append(f'''  (symbol (lib_id "{lid}") (at {r2(x)} {r2(y)} {rot}) (unit 1)
    (in_bom yes) (on_board yes) (dnp no)
    (uuid {U()})
    (property "Reference" "{ref}" (at {r2(x)} {r2(y+6.35)} 0)
      (effects (font (size 1.27 1.27)) hide))
    (property "Value" "{net}" (at {r2(x)} {r2(vy)} 0)
      (effects (font (size 1.27 1.27))))
    (property "Footprint" "" (at {r2(x)} {r2(y)} 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "" (at {r2(x)} {r2(y)} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid {U()}))
    (instances (project "{PROJECT}" (path "/{ROOT}" (reference "{ref}") (unit 1))))
  )''')

def add_wire(x1, y1, x2, y2):
    items.append(f'  (wire (pts (xy {r2(x1)} {r2(y1)}) (xy {r2(x2)} {r2(y2)})) (stroke (width 0) (type default)) (uuid {U()}))')

def add_label(net, x, y, d):
    ang, just = {'L': (180, 'right bottom'), 'R': (0, 'left bottom'), 'U': (90, 'left bottom'), 'D': (270, 'right bottom')}[d]
    items.append(f'  (label "{net}" (at {r2(x)} {r2(y)} {ang}) (fields_autoplaced) (effects (font (size 1.27 1.27)) (justify {just})) (uuid {U()}))')

def add_nc(x, y):
    items.append(f'  (no_connect (at {r2(x)} {r2(y)}) (uuid {U()}))')

def add_text(txt, x, y, size):
    items.append(f'  (text "{txt}" (at {r2(x)} {r2(y)} 0) (effects (font (size {size} {size})) (justify left bottom)) (uuid {U()}))')

for ref, (lib_id, value, fp, (X, Y), pinmap, extra) in PARTS.items():
    flat = flat_symbol(lib_id)
    lib_defs.setdefault(lib_id, flat)
    pins = sym_pins(flat)
    is_flag = ref.startswith('#FLG')
    # property placement
    if pins:
        ys = [Y - p['y'] for p in pins]
        top, bot = min(ys), max(ys)
    else:
        top, bot = Y - 2, Y + 2
    horiz2 = len(pins) == 2 and all(p['ang'] in (0, 180) for p in pins)
    if horiz2:
        rpos, vpos, just = (X - 3.81, Y - 6.35), (X - 3.81, Y - 3.81), 'left'
    elif len(pins) <= 3 and not is_flag:
        rpos, vpos, just = (X + 3.81, Y - 1.27), (X + 3.81, Y + 1.27), 'left'
    else:
        rpos, vpos, just = (X + 3.81, top - 3.0), (X + 3.81, bot + 3.0), 'left'
    if '_fields' in extra:
        a, b, c, d_ = extra['_fields']
        rpos, vpos, just = (X + a, Y + b), (X + c, Y + d_), 'left'
    dnp = 'yes' if extra.get('DNP') else 'no'
    flds = ''
    for k, v in extra.items():
        if k == 'DNP' or k.startswith('_'):
            continue
        flds += f'''
    (property "{k}" "{v}" (at {r2(X)} {r2(Y)} 0) (effects (font (size 1.27 1.27)) hide))'''
    pin_uuids = ''.join(f'\n    (pin "{p["num"]}" (uuid {U()}))' for p in pins)
    hide_ref = ' hide' if is_flag else ''
    items.append(f'''  (symbol (lib_id "{lib_id}") (at {r2(X)} {r2(Y)} 0) (unit 1)
    (in_bom {'no' if is_flag else 'yes'}) (on_board {'no' if is_flag else 'yes'}) (dnp {dnp})
    (uuid {SYMU(ref)})
    (property "Reference" "{ref}" (at {r2(rpos[0])} {r2(rpos[1])} 0)
      (effects (font (size 1.27 1.27)) (justify {just}){hide_ref}))
    (property "Value" "{value}" (at {r2(vpos[0])} {r2(vpos[1])} 0)
      (effects (font (size 1.27 1.27)) (justify {just})))
    (property "Footprint" "{fp}" (at {r2(X)} {r2(Y)} 0)
      (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "~" (at {r2(X)} {r2(Y)} 0)
      (effects (font (size 1.27 1.27)) hide)){flds}{pin_uuids}
    (instances (project "{PROJECT}" (path "/{ROOT}" (reference "{ref}") (unit 1))))
  )''')
    done = set()
    pwr_ends = {}
    def neighbour(px, py, below):
        for q in pins:
            qx, qy = X + q['x'], Y - q['y']
            if abs(qx - px) < 0.1 and ((0 < qy - py <= 5.1) if below else (0 < py - qy <= 5.1)):
                return True
        return False
    for p in pins:
        if p['num'] not in pinmap:
            if p['hidden']:
                continue
            raise SystemExit(f'{ref} pin {p["num"]} ({p["name"]}) not mapped')
        net = pinmap[p['num']]
        px, py = X + p['x'], Y - p['y']
        key = (r2(px), r2(py))
        if key in done:
            continue
        done.add(key)
        if net is None:
            add_nc(px, py)
            continue
        # stub goes away from body (opposite of pin direction)
        d = {0: 'L', 180: 'R', 90: 'D', 270: 'U'}[p['ang']]
        dx, dy = {'L': (-2.54, 0), 'R': (2.54, 0), 'U': (0, -2.54), 'D': (0, 2.54)}[d]
        if is_flag:
            # PWR_FLAG pin points up into body -> attach directly
            if net == 'GND':
                add_power(net, px, py)
            else:
                add_wire(px, py, px, py + 5.08)
                add_wire(px, py + 5.08, px + 5.08, py + 5.08)
                add_power(net, px + 5.08, py + 5.08)
            continue
        ex, ey = px + dx, py + dy
        add_wire(px, py, ex, ey)
        if net in POWER_NETS:
            prev = pwr_ends.get((net, r2(ey)))
            if prev is not None and abs(prev - ex) <= 2.6:
                add_wire(prev, ey, ex, ey)             # share the neighbour's power symbol
                continue
            pwr_ends[(net, r2(ey))] = ex
            if d in ('L', 'R') and neighbour(px, py, below=(net == 'GND')) and not neighbour(px, py, below=(net != 'GND')):
                sgn = -1 if net == 'GND' else 1        # go the free way, symbol flipped
                add_wire(ex, ey, ex, ey + sgn * 1.27)
                add_power(net, ex, ey + sgn * 1.27, 180)
            elif (net == 'GND' and d == 'D') or (net != 'GND' and d == 'U'):
                add_power(net, ex, ey)                 # natural direction
            elif d in ('U', 'D'):
                add_power(net, ex, ey, 180)            # flipped, points away from the body
            elif net == 'GND':
                add_wire(ex, ey, ex, ey + 1.27)
                add_power(net, ex, ey + 1.27)
            else:
                add_wire(ex, ey, ex, ey - 1.27)
                add_power(net, ex, ey - 1.27)
        else:
            add_label(net, ex, ey, d)
    for k in pinmap:
        if k not in {p['num'] for p in pins}:
            raise SystemExit(f'{ref}: pin {k} not in symbol {lib_id}')

for (x, y), txt, size in NOTES:
    add_text(txt, x, y, size)

libs = '\n'.join('    ' + v.replace('\n', '\n    ') for v in lib_defs.values())
doc = f'''(kicad_sch (version 20230121) (generator eeschema)
  (uuid {ROOT})
  (paper "{PAPER}")
  (title_block
    (title "{TITLE}")
    (date "{DATE}")
    (rev "{REV}")
    (comment 1 "{COMMENT}")
  )
  (lib_symbols
{libs}
  )
{chr(10).join(items)}
  (sheet_instances (path "/" (page "1")))
)
'''
open(OUT, 'w').write(doc)
print('written', OUT, len(items), 'items')
