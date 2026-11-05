# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
# Single source of truth for the ESP32 Modular Base v2.0 schematic.
# Values / footprints / fit status come from parts.py (shared with the BOM generator);
# this file adds the symbol, the schematic position and the {pin: net} map of every part.
# Net None = no-connect.
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parts import FP, PORTS, TEMPLATE, CORE, port_refs

PROJECT = 'esp32-modular'
FPLIB = PROJECT
PAPER = 'A2'
TITLE = 'ESP32 Modular Base'
REV = '2.0'
DATE = '2026-10-13'
COMMENT = '6 generic ports + UART + I2C + switched output. USB-C 5 V, CH340C flashing.'

G = 2.54
def g(n): return round(n * G, 2)

# Module pin numbers (RF_Module:ESP32-WROOM-32 symbol)
ESP_PIN = {'IO36': '4', 'IO39': '5', 'IO34': '6', 'IO35': '7', 'IO32': '8', 'IO33': '9', 'IO25': '10',
           'IO26': '11', 'IO27': '12', 'IO14': '13', 'IO12': '14', 'IO13': '16', 'IO15': '23', 'IO2': '24',
           'IO0': '25', 'IO4': '26', 'IO16': '27', 'IO17': '28', 'IO5': '29', 'IO18': '30', 'IO19': '31',
           'IO21': '33', 'IO22': '36', 'IO23': '37'}

# value / fit / function per ref, from parts.py
META = {r[0]: r for r in CORE + port_refs()}

def val(ref):
    _r, _b, v, _fp, fit, _f, _l = META[ref]
    return 'DNP' if fit == 'DNP' and not ref.startswith('J9') else v

def fp(ref): return META[ref][3]

def extra(ref):
    _r, _b, _v, _fp, fit, func, _l = META[ref]
    e = {'Description': func}
    if fit == 'DNP':
        e['DNP'] = True
    return e

PARTS = {}
FIELDS = {'Transistor_BJT': (5.08, -1.27, 5.08, 1.27), 'Transistor_FET': (5.08, -1.27, 5.08, 1.27),
          'Jumper:SolderJumper_3': (1.27, 6.35, 1.27, 8.89)}
def P(ref, lib, pos, pins, value=None):
    e = extra(ref)
    for k, f in FIELDS.items():
        if lib.startswith(k):
            e['_fields'] = f
    PARTS[ref] = (lib, value or val(ref), fp(ref), (g(pos[0]), g(pos[1])), pins, e)

# ---------------- Power input (v1.0 block 2.1) ----------------
P('J1',  'Connector_Generic:Conn_01x04', (12, 20), {'1': 'VBUS_IN', '2': 'USB_DM', '3': 'USB_DP', '4': 'GND'},
  'USB-C breakout (V D- D+ G)')
P('U4',  'Power_Protection:USBLC6-2SC6', (24, 20), {'1': 'USB_DP', '6': 'USB_DP', '3': 'USB_DM', '4': 'USB_DM', '2': 'GND', '5': '+5V'})
P('F1',  'Device:Polyfuse', (36, 20), {'1': 'VBUS_IN', '2': '+5V'}, '1.1A hold PTC')
P('D1',  'Device:D_Zener', (44, 20), {'1': '+5V', '2': 'GND'})
P('C1',  'Device:C_Polarized', (52, 20), {'1': '+5V', '2': 'GND'})
P('C2',  'Device:C', (60, 20), {'1': '+5V', '2': 'GND'})
# ---------------- 3V3 rail (2.2) ----------------
P('U2',  'Regulator_Linear:AMS1117-3.3', (70, 20), {'3': '+5V', '2': '+3V3', '1': 'GND'})
P('C3',  'Device:C', (80, 20), {'1': '+3V3', '2': 'GND'})
P('C4',  'Device:C_Polarized', (87, 20), {'1': '+3V3', '2': 'GND'})
P('R10', 'Device:R', (94, 18), {'1': '+3V3', '2': 'LED_PWR'})
P('LED1', 'Device:LED', (98, 24), {'2': 'LED_PWR', '1': 'GND'})
PARTS['#FLG01'] = ('power:PWR_FLAG', 'PWR_FLAG', '', (g(100), g(30)), {'1': '+5V'}, {})
PARTS['#FLG02'] = ('power:PWR_FLAG', 'PWR_FLAG', '', (g(106), g(30)), {'1': 'GND'}, {})

# ---------------- MCU ----------------
used = {'IO0': 'IO0', 'IO2': 'IO2', 'IO23': 'IO23', 'IO19': 'IO19', 'IO14': 'IO14', 'IO5': 'IO5'}
for n, (label, ga, gb, vp, ov) in PORTS.items():
    used[ga] = ga
    used[gb] = gb
esp = {'1': 'GND', '15': 'GND', '38': 'GND', '39': 'GND', '2': '+3V3', '3': 'EN',
       '35': 'ESP_TXD', '34': 'ESP_RXD', '32': None,
       '14': None, '23': None,                                   # IO12, IO15: strapping, unused
       '17': None, '18': None, '19': None, '20': None, '21': None, '22': None}  # flash
for name, pin in ESP_PIN.items():
    if pin not in esp:
        esp[pin] = used.get(name)
assert all(v is not None for k, v in esp.items() if k in [ESP_PIN[x] for x in used]), 'unmapped GPIO'
P('U1',  'RF_Module:ESP32-WROOM-32', (32, 62), esp, 'ESP-32S (Ai-Thinker)')
P('C5',  'Device:C', (8, 48), {'1': '+3V3', '2': 'GND'})
P('C6',  'Device:C', (12, 48), {'1': '+3V3', '2': 'GND'})
P('R1',  'Device:R', (8, 62), {'1': '+3V3', '2': 'EN'})
P('C7',  'Device:C', (12, 62), {'1': 'EN', '2': 'GND'})
P('SW1', 'Switch:SW_Push', (10, 74), {'1': 'EN', '2': 'GND'})
P('R2',  'Device:R', (52, 50), {'1': '+3V3', '2': 'IO0'})
P('SW2', 'Switch:SW_Push', (54, 60), {'1': 'IO0', '2': 'GND'})
P('R11', 'Device:R', (52, 72), {'1': 'IO2', '2': 'LED_STAT_A'})
P('LED2', 'Device:LED', (56, 78), {'2': 'LED_STAT_A', '1': 'GND'})

# ---------------- USB-UART + auto-reset (2.3, 2.4) ----------------
P('U3',  'Interface_USB:CH340C', (76, 58),
  {'1': 'GND', '16': '+3V3', '4': '+3V3', '5': 'USB_DP', '6': 'USB_DM',
   '2': 'CH_TXD', '3': 'ESP_TXD', '13': 'DTR', '14': 'RTS', '15': 'GND',
   '7': None, '8': None, '9': None, '10': None, '11': None, '12': None})
P('C8',  'Device:C', (90, 50), {'1': '+3V3', '2': 'GND'})
P('R5',  'Device:R', (90, 62), {'1': 'CH_TXD', '2': 'ESP_RXD'})
P('R3',  'Device:R', (68, 80), {'1': 'DTR', '2': 'Q1_B'})
P('Q1',  'Transistor_BJT:MMBT3904', (76, 80), {'1': 'Q1_B', '2': 'RTS', '3': 'EN'})
P('R4',  'Device:R', (86, 80), {'1': 'RTS', '2': 'Q2_B'})
P('Q2',  'Transistor_BJT:MMBT3904', (94, 80), {'1': 'Q2_B', '2': 'DTR', '3': 'IO0'})

# ---------------- Generic ports (loop) ----------------
SIGNAMES = {'UART': ('TX', 'RX'), 'I2C': ('SDA', 'SCL')}
PORT_ORIGIN = {}
for i, (n, (label, ga, gb, vp, ov)) in enumerate(PORTS.items()):
    bx = 120 + 56 * (i // 4)
    by = 8 + 27 * (i % 4)
    PORT_ORIGIN[n] = (bx, by)
    sa, sb = SIGNAMES.get(label, ('A', 'B'))
    A, B, VP, SEL = f'{label}_{sa}', f'{label}_{sb}', f'{label}_VP', f'{label}_VPSEL'
    lo, hi = ('+5V', '+3V3') if vp == '5V' else ('+3V3', '+5V')   # JP pin1 side is the default
    P(f'J{n}01', 'Connector_Generic:Conn_01x04', (bx + 8, by + 8), {'1': 'GND', '2': VP, '3': A, '4': B},
      f'{label} (G VP {sa} {sb})')
    P(f'JP{n}01', 'Jumper:SolderJumper_3_Bridged12', (bx + 18, by + 7), {'1': lo, '2': SEL, '3': hi},
      f'VP {vp} (1-2)')
    P(f'F{n}01', 'Device:Polyfuse', (bx + 26, by + 7), {'1': SEL, '2': VP}, '0.5A PTC')
    P(f'R{n}01', 'Device:R', (bx + 32, by + 6), {'1': A, '2': ga})
    P(f'R{n}02', 'Device:R', (bx + 38, by + 6), {'1': '+3V3', '2': A})
    P(f'R{n}03', 'Device:R', (bx + 44, by + 6), {'1': A, '2': 'GND'})
    P(f'R{n}04', 'Device:R', (bx + 32, by + 17), {'1': B, '2': gb})
    P(f'R{n}05', 'Device:R', (bx + 38, by + 17), {'1': '+3V3', '2': B})
    P(f'R{n}06', 'Device:R', (bx + 44, by + 17), {'1': gb, '2': 'GND'})
    P(f'C{n}01', 'Device:C', (bx + 50, by + 17), {'1': gb, '2': 'GND'})

# ---------------- Switched output ----------------
ox, oy = 120, 122
P('J901', 'Connector_Generic:Conn_01x03', (ox + 8, oy + 8), {'1': 'GND', '2': 'OUT_VPLUS', '3': 'OUT_SW'}, 'OUT (G V+ OUT)')
P('R901', 'Device:R', (ox + 18, oy + 8), {'1': 'IO23', '2': 'OUT_G'})
P('R902', 'Device:R', (ox + 24, oy + 13), {'1': 'OUT_G', '2': 'GND'})
P('Q901', 'Transistor_FET:AO3400A', (ox + 32, oy + 8), {'1': 'OUT_G', '2': 'GND', '3': 'OUT_SW'})
P('D901', 'Device:D_Schottky', (ox + 40, oy + 4), {'1': 'OUT_VPLUS', '2': 'OUT_SW'})
P('JP901', 'Jumper:SolderJumper_2_Open', (ox + 48, oy + 4), {'1': '+5V', '2': 'OUT_VPLUS'}, 'V+ = 5V (open)')
P('J902', 'Connector_Generic:Conn_01x05', (ox + 64, oy + 8),
  {'1': '+3V3', '2': 'IO19', '3': 'IO14', '4': 'IO5', '5': 'GND'}, 'EXP (DNP)')

for k, x in enumerate((100, 104, 108, 112)):
    PARTS[f'H{k + 1}'] = ('Mechanical:MountingHole', 'M3', FP['MH'], (g(x), g(108)), {}, {})

POWER_NETS = {'GND', '+3V3', '+5V'}
WIDE_NETS = {'VBUS_IN', '+5V', '+3V3', 'GND', 'OUT_VPLUS', 'OUT_SW'} | \
            {f'{p[0]}_VP' for p in PORTS.values()} | {f'{p[0]}_VPSEL' for p in PORTS.values()}

NOTES = [
    ((g(4), g(8)), 'POWER: USB-C breakout -> F1 1.1 A PTC -> D1 TVS -> +5V -> AMS1117-3.3. USB data via USBLC6 ESD to CH340C.', 2.0),
    ((g(4), g(36)), 'MCU + USB-UART: CH340C in 3.3 V mode (V3 tied to VCC). DTR/RTS auto-reset. IO0 = BOOT, IO2 = status LED.', 2.0),
    ((g(4), g(100)), 'Strapping: IO0 pulled up, IO2 LED to GND (safe). IO12 and IO15 unused. IO5/IO14 only on J902 (inputs).', 1.6),
    ((g(120), g(4)), 'PORTS: XH 4P = 1 GND, 2 VP, 3 A, 4 B. VP = 3V3 or 5V by solder jumper (pin 1 side bridged), 0.5 A PTC per port.', 2.0),
    ((g(120), g(116)), 'Rn01 series A (330R) | Rn02 A pull-up | Rn03 A pull-down | Rn04 series B (1k) | Rn05 B pull-up | Rn06 / Cn01 B to GND (GPIO side). DNP = option footprint.', 1.6),
    ((g(120), g(120)), 'OUT: AO3400A low-side switch on IO23, SS34 flyback to V+. JP901 ties V+ to +5V (open by default).', 1.6),
]
