# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
# Board geometry and placement for ESP32 Modular Base v2.0 (shared by build_pcb / finish).
# u, v = mm from the board's top-left corner (v down). Board origin on the KiCad canvas = (OX, OY).
import math

OX, OY = 100.0, 100.0
W, H = 75.0, 65.0
CR = 2.0                                  # corner radius
HOLES = {'H1': (3.2, 3.2), 'H2': (W - 3.2, 3.2), 'H3': (3.2, H - 3.2), 'H4': (W - 3.2, H - 3.2)}

# ESP32 module: antenna overhangs the top edge (same offset as v1.0)
MX, MY = 37.5, 9.8
MODULE_KEEPOUT = (MX - 7.6, 0.0, MX + 7.6, 18.2)       # F.Cu: no tracks/vias under the module body

# connector pin-line distance from the edge: courtyard edge-side extent 3.92 + 0.5
EDGE_PIN = 0.5 + 3.92

# Port groups, built in a local "bottom edge" frame: x along the pins from pin 1, y into the board.
# (dx, dy, rot) per template position.  JP vertical left of F, F feeds pin 2, 0805 row behind.
TEMPLATE_POS = {
    'J':   (0.0, 0.0, 0),
    'JP':  (-3.0, 5.6, 90),
    'F':   (1.0, 5.4, 0),
    'CB':  (6.1, 5.4, 0),
    'RAU': (-2.6, 9.9, 90), 'RAD': (-0.2, 9.9, 90), 'RA': (2.2, 9.9, 90),
    'RB':  (4.6, 9.9, 90), 'RBU': (7.0, 9.9, 90), 'RBD': (9.4, 9.9, 90),
}
REFPAT = {'J': 'J{n}01', 'JP': 'JP{n}01', 'F': 'F{n}01', 'CB': 'C{n}01', 'RA': 'R{n}01', 'RAU': 'R{n}02',
          'RAD': 'R{n}03', 'RB': 'R{n}04', 'RBU': 'R{n}05', 'RBD': 'R{n}06'}

# Port anchors: n -> (edge, pin1 position along that edge)
#   bottom: pins left->right, pin1 u;  left: pins top->bottom, pin1 v;  right: pins bottom->top, pin1 v
PORT_ANCHOR = {
    1: ('bottom', 10.0), 2: ('bottom', 25.4), 3: ('bottom', 40.8), 4: ('bottom', 56.2),
    5: ('left', 21.0), 6: ('left', 36.6),
    7: ('right', 19.4), 8: ('right', 34.6),
}
EDGE_ROT = {'bottom': 0, 'left': -90, 'right': 90, 'top': 180}   # KiCad degrees (CCW positive)


def edge_frame(edge, along):
    """Return (u0, v0, ex, ey) : pin-1 position and unit vectors of local x (along pins) and y (into board)."""
    if edge == 'bottom':
        return (along, H - EDGE_PIN, (1, 0), (0, -1))
    if edge == 'top':
        return (along, EDGE_PIN, (-1, 0), (0, 1))
    if edge == 'left':
        return (EDGE_PIN, along, (0, 1), (1, 0))
    if edge == 'right':
        return (W - EDGE_PIN, along, (0, -1), (-1, 0))
    raise ValueError(edge)


def local_to_board(edge, along, dx, dy, rot):
    u0, v0, ex, ey = edge_frame(edge, along)
    u = u0 + dx * ex[0] + dy * ey[0]
    v = v0 + dx * ex[1] + dy * ey[1]
    return (round(u, 3), round(v, 3), (rot + EDGE_ROT[edge]) % 360)


def port_place(n, jp_flip=False):
    edge, along = PORT_ANCHOR[n]
    out = {}
    for pos, (dx, dy, rot) in TEMPLATE_POS.items():
        r = rot + (180 if (pos == 'JP' and jp_flip) else 0)
        out[REFPAT[pos].format(n=n)] = local_to_board(edge, along, dx, dy, r)
    return out


# Everything else: ref -> (u, v, rot)
CORE_PLACE = {
    'U1': (MX, MY, 0),
    # buttons, top-left (SW1 = RESET next to EN, SW2 = BOOT)
    'SW1': (8.8, 1.9, 0), 'SW2': (8.8, 9.8, 0),
    # module support, top-left next to VDD (pin 2) and EN (pin 3)
    'C5': (24.2, 2.6, 0), 'C6': (24.2, 5.0, 0), 'R1': (20.0, 2.6, 0), 'C7': (20.0, 5.0, 0),
    # USB input + CH340C cluster, top-right
    'J1': (59.45, EDGE_PIN, 180),
    'U4': (55.4, 10.6, 0), 'C8': (51.0, 10.9, 0),
    'U3': (54.0, 17.9, 0),
    'R5': (52.0, 24.6, 0), 'R2': (48.0, 24.6, 90),
    'Q1': (51.5, 27.4, 0), 'Q2': (56.5, 27.4, 0), 'R3': (51.5, 31.2, 90), 'R4': (56.5, 31.2, 90),
    # status LED near IO2 (module bottom row)
    'R11': (44.6, 23.6, 0), 'LED2': (44.6, 26.0, 0),
    # 5 V input chain
    'F1': (44.4, 31.6, 0), 'D1': (44.4, 36.0, 0), 'C1': (51.4, 36.6, 0), 'C2': (37.0, 35.8, 0),
    # 3V3 regulator, centre-bottom, with copper spreader on both layers
    'U2': (34.5, 42.0, 0), 'C3': (41.0, 43.0, 90), 'C4': (44.4, 43.0, 0),
    'R10': (31.0, 35.8, 0), 'LED1': (31.0, 33.4, 0),
    # switched output, right-bottom
    'J901': (W - EDGE_PIN, 47.6, 90),
    'D901': (61.0, 40.8, 0), 'Q901': (62.0, 45.4, 90), 'R901': (56.6, 45.6, 90), 'R902': (58.9, 45.6, 90),
    'JP901': (65.0, 45.9, 90),
    # expansion pads, horizontal under the module
    'J902': (29.0, 23.4, 90),
}
CORE_PLACE.update({k: (u, v, 0) for k, (u, v) in HOLES.items()})

AMS_SPREADER = (36.0, 38.6, 40.0, 45.4)       # +3V3 pour under the AMS1117 tab, both layers


def all_place():
    pl = dict(CORE_PLACE)
    for n in PORT_ANCHOR:
        pl.update(port_place(n, jp_flip=(n == 7)))   # UART: pin 1 is +5V, flip so 3V3/5V sides match
    return pl
