# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
# Part list for the modular ESP32 base board (v2.0).
# Source of truth for the BOM now; design.py (nets + schematic positions) will be built on it.
#
# Every ref belongs to a BOM line (LINES key). fit: 'Fit' | 'DNP' | 'Trace' (solder jumper,
# bridged by copper) | 'Open' (solder jumper, open) | 'Hole'.

FP = {
    'R':      'Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder',
    'C':      'Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder',
    'CP':     'Capacitor_THT:CP_Radial_D6.3mm_P2.50mm',
    'LED':    'LED_SMD:LED_0805_2012Metric_Pad1.15x1.40mm_HandSolder',
    'SOT23':  'Package_TO_SOT_SMD:SOT-23',
    'SOT236': 'Package_TO_SOT_SMD:SOT-23-6',
    'SOT223': 'Package_TO_SOT_SMD:SOT-223-3_TabPin2',
    'SOIC16': 'Package_SO:SOIC-16_3.9x9.9mm_P1.27mm',
    'SMA':    'Diode_SMD:D_SMA_Handsoldering',
    'F1812':  'Fuse:Fuse_1812_4532Metric_Pad1.30x3.40mm_HandSolder',
    'F1206':  'Fuse:Fuse_1206_3216Metric_Pad1.42x1.75mm_HandSolder',
    'SW':     'Button_Switch_THT:SW_PUSH_6mm',
    'XH4':    'Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical',
    'XH3':    'Connector_JST:JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical',
    'H5':     'Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical',
    'JP3':    'Jumper:SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm',
    'JP2':    'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm',
    'MH':     'MountingHole:MountingHole_3.2mm_M3',
    'ESP':    'esp32-modular:ESP32-WROOM-32_HandSolder',
}

# Ports: number -> (label, GPIO A, GPIO B, VP default, overrides {position: (value, fit)})
PORTS = {
    1: ('P1',   'IO25', 'IO36', '3V3', {}),
    2: ('P2',   'IO26', 'IO39', '3V3', {}),
    3: ('P3',   'IO27', 'IO34', '3V3', {}),
    4: ('P4',   'IO13', 'IO35', '3V3', {}),
    5: ('P5',   'IO4',  'IO32', '3V3', {}),
    6: ('P6',   'IO18', 'IO33', '3V3', {}),
    7: ('UART', 'IO17', 'IO16', '5V',  {'RA': ('330R', 'Fit'), 'RB': ('10k', 'Fit'), 'RBD': ('22k', 'Fit')}),
    8: ('I2C',  'IO21', 'IO22', '3V3', {'RA': ('100R', 'Fit'), 'RAU': ('4k7', 'Fit'),
                                        'RB': ('100R', 'Fit'), 'RBU': ('4k7', 'Fit')}),
}

# Port template: position -> (ref suffix, default value, default fit, role)
TEMPLATE = [
    ('J',   'J{n}01',  'XH 4P',     'Fit',   'Port connector: 1 GND, 2 VP, 3 A, 4 B'),
    ('JP',  'JP{n}01', 'VP select', 'Trace', 'VP source: 1-2 = 3V3, 2-3 = 5V'),
    ('F',   'F{n}01',  'PTC 0.5A',  'Fit',   'Per-port PTC on VP'),
    ('RA',  'R{n}01',  '330R',      'Fit',   'Series resistor, A <-> GPIO'),
    ('RAU', 'R{n}02',  '-',         'DNP',   'Pull-up, A (connector side) -> 3V3'),
    ('RAD', 'R{n}03',  '-',         'DNP',   'Pull-down, A (connector side) -> GND'),
    ('RB',  'R{n}04',  '1k',        'Fit',   'Series resistor, B <-> GPIO'),
    ('RBU', 'R{n}05',  '-',         'DNP',   'Pull-up, B (connector side) -> 3V3'),
    ('RBD', 'R{n}06',  '-',         'DNP',   'Pull-down, B (GPIO side) -> GND (divider bottom)'),
    ('CB',  'C{n}01',  '-',         'DNP',   'Filter cap, B (GPIO side) -> GND'),
]

# value -> BOM line key for port parts
VALUE_LINE = {'330R': 'R330', '1k': 'R1k', '10k': 'R10k', '22k': 'R22k', '100R': 'R100',
              '4k7': 'R4k7', 'XH 4P': 'XH4', 'PTC 0.5A': 'PTC050', 'VP select': 'JP3', '-': None}


def port_refs():
    rows = []
    for n, (label, ga, gb, vp, ov) in PORTS.items():
        for pos, refpat, val, fit, role in TEMPLATE:
            ref = refpat.format(n=n)
            if pos in ov:
                val, fit = ov[pos]
            if pos == 'JP':
                val = f'VP = {vp}' + (' (2-3 bridged)' if vp == '5V' else ' (1-2 bridged)')
                line = 'JP3'
            elif fit == 'DNP':
                line = 'OPT_C' if pos == 'CB' else 'OPT_R'
            else:
                line = VALUE_LINE[val]
            fp = {'J': FP['XH4'], 'JP': FP['JP3'], 'F': FP['F1206'], 'CB': FP['C']}.get(pos, FP['R'])
            gpio = ga if pos in ('RA', 'RAU', 'RAD') else gb if pos in ('RB', 'RBU', 'RBD', 'CB') else ''
            func = f'{label} {pos}: {role}' + (f' ({gpio})' if gpio else '')
            rows.append((ref, f'Port {label}', val if fit != 'DNP' else 'empty', fp, fit, func, line))
    return rows


# Fixed (non-port) refs: ref, block, value, footprint, fit, function, line
CORE = [
    ('J1',   'Power in',   'XH 4P',          FP['XH4'],    'Fit',  'USB-C breakout in: 1 VBUS, 2 D-, 3 D+, 4 GND', 'XH4'),
    ('F1',   'Power in',   'PTC 1.1A',       FP['F1812'],  'Fit',  'Input PTC, VBUS_IN -> +5V', 'PTC110'),
    ('D1',   'Power in',   'SMAJ5.0A',       FP['SMA'],    'Fit',  'TVS on +5V, band to +5V', 'SMAJ'),
    ('C1',   'Power in',   '100uF 10V',      FP['CP'],     'Fit',  '+5V bulk', 'CP100'),
    ('C2',   'Power in',   '10uF',           FP['C'],      'Fit',  '+5V ceramic', 'C10u'),
    ('U2',   '3V3 rail',   'AMS1117-3.3',    FP['SOT223'], 'Fit',  '5V -> 3V3 LDO, tab = 3V3', 'AMS'),
    ('C3',   '3V3 rail',   '22uF',           FP['C'],      'Fit',  '3V3 ceramic at LDO output', 'C22u'),
    ('C4',   '3V3 rail',   '100uF 10V',      FP['CP'],     'Fit',  '3V3 bulk (Wi-Fi TX, relay coils)', 'CP100'),
    ('R10',  'Indicators', '1k',             FP['R'],      'Fit',  'Power LED resistor', 'R1k'),
    ('LED1', 'Indicators', 'Red',            FP['LED'],    'Fit',  'Power LED', 'LEDR'),
    ('R11',  'Indicators', '1k',             FP['R'],      'Fit',  'Status LED resistor (IO2)', 'R1k'),
    ('LED2', 'Indicators', 'Yellow',         FP['LED'],    'Fit',  'Status LED (IO2)', 'LEDY'),
    ('U4',   'USB-UART',   'USBLC6-2SC6',    FP['SOT236'], 'Fit',  'ESD on D+/D-', 'USBLC6'),
    ('U3',   'USB-UART',   'CH340C',         FP['SOIC16'], 'Fit',  'USB-UART, 3.3 V mode (VCC = V3 = 3V3)', 'CH340C'),
    ('C8',   'USB-UART',   '100nF',          FP['C'],      'Fit',  'CH340C decoupling', 'C100n'),
    ('R5',   'USB-UART',   '470R',           FP['R'],      'Fit',  'CH340 TXD -> ESP RXD0', 'R470'),
    ('Q1',   'USB-UART',   'MMBT3904',       FP['SOT23'],  'Fit',  'Auto-reset: DTR -> EN', 'NPN'),
    ('Q2',   'USB-UART',   'MMBT3904',       FP['SOT23'],  'Fit',  'Auto-reset: RTS -> IO0', 'NPN'),
    ('R3',   'USB-UART',   '10k',            FP['R'],      'Fit',  'Q1 base resistor', 'R10k'),
    ('R4',   'USB-UART',   '10k',            FP['R'],      'Fit',  'Q2 base resistor', 'R10k'),
    ('U1',   'MCU',        'ESP-32S',        FP['ESP'],    'Fit',  'Ai-Thinker ESP-32S / WROOM-32(E)', 'ESP'),
    ('C5',   'MCU',        '100nF',          FP['C'],      'Fit',  'ESP32 decoupling', 'C100n'),
    ('C6',   'MCU',        '10uF',           FP['C'],      'Fit',  'ESP32 decoupling', 'C10u'),
    ('R1',   'MCU',        '10k',            FP['R'],      'Fit',  'EN pull-up', 'R10k'),
    ('C7',   'MCU',        '1uF',            FP['C'],      'Fit',  'EN delay', 'C1u'),
    ('SW1',  'MCU',        'RESET',          FP['SW'],     'Fit',  'EN to GND', 'SW'),
    ('R2',   'MCU',        '10k',            FP['R'],      'Fit',  'IO0 pull-up', 'R10k'),
    ('SW2',  'MCU',        'BOOT',           FP['SW'],     'Fit',  'IO0 to GND (user button after boot)', 'SW'),
    ('J901', 'OUT',        'XH 3P',          FP['XH3'],    'Fit',  'Switched output: 1 GND, 2 V+, 3 OUT', 'XH3'),
    ('Q901', 'OUT',        'AO3400A',        FP['SOT23'],  'Fit',  'Low-side N-MOSFET, gate from IO23', 'AO3400'),
    ('R901', 'OUT',        '100R',           FP['R'],      'Fit',  'Gate resistor', 'R100'),
    ('R902', 'OUT',        '100k',           FP['R'],      'Fit',  'Gate pull-down (off at boot)', 'R100k'),
    ('D901', 'OUT',        'SS34',           FP['SMA'],    'Fit',  'Flyback, OUT (anode) -> V+ (cathode)', 'SS34'),
    ('JP901','OUT',        'V+ = 5V link',   FP['JP2'],    'Open', 'Bridge only for 5 V loads with no external supply', 'JP2'),
    ('J902', 'Expansion',  '1x5 header',     FP['H5'],     'DNP',  'Spare pins: 3V3, IO19, IO14, IO5, GND', 'H5'),
    ('H1',   'Mechanical', 'M3',             FP['MH'],     'Hole', 'Mounting hole', 'MH'),
    ('H2',   'Mechanical', 'M3',             FP['MH'],     'Hole', 'Mounting hole', 'MH'),
    ('H3',   'Mechanical', 'M3',             FP['MH'],     'Hole', 'Mounting hole', 'MH'),
    ('H4',   'Mechanical', 'M3',             FP['MH'],     'Hole', 'Mounting hole', 'MH'),
]

# BOM lines: key -> dict. 'where' is an estimate of where to look first, not a stock check.
L = lambda **k: k
LINES = {
    'ESP':    L(block='MCU', value='ESP-32S (Ai-Thinker)', pkg='WROOM-32 footprint, 38 castellated pads',
                spec='4 MB flash. WROOM-32 / WROOM-32E fit the same pads', spares=0, where='Have',
                ali='Ai-Thinker ESP-32S module', subs='ESP32-WROOM-32E (N4), ESP32-WROOM-32D', pack='1',
                note='You already have these: enter the count in "In stock".'),
    'AMS':    L(block='3V3 rail', value='AMS1117-3.3', pkg='SOT-223', spec='3.3 V fixed LDO, 1 A, tab = output',
                spares=1, where='Local likely', ali='AMS1117-3.3 SOT-223', subs='LD1117S33 (same pinout)', pack='10-50',
                note='Not the ADJ version.'),
    'CH340C': L(block='USB-UART', value='CH340C', pkg='SOIC-16', spec='Must be the C variant: internal oscillator, no crystal',
                spares=1, where='AliExpress', ali='CH340C SOP-16', subs='None on this footprint (CH340G needs a crystal)',
                pack='10', note='Marking "CH340C".'),
    'USBLC6': L(block='USB-UART', value='USBLC6-2SC6', pkg='SOT-23-6', spec='USB ESD protection, 2 lines',
                spares=1, where='AliExpress', ali='USBLC6-2SC6 SOT-23-6', subs='USBLC6-2SC6Y',
                pack='10-20', note='If you cannot get it, leave U4 empty: the board works, just without USB ESD protection.'),
    'NPN':    L(block='USB-UART', value='MMBT3904', pkg='SOT-23', spec='NPN, pin 1 B, 2 E, 3 C (marking 1AM)',
                spares=1, where='Local maybe', ali='MMBT3904 SOT-23', subs='MMBT2222A (1P), S8050 SOT-23 (J3Y): same pinout',
                pack='50-100', note='Auto-reset pair.'),
    'AO3400': L(block='OUT', value='AO3400A', pkg='SOT-23', spec='N-MOSFET 30 V 5.7 A, logic level (works from 3.3 V gate)',
                spares=1, where='AliExpress', ali='AO3400A SOT-23', subs='SI2302 (A2SHB): 20 V max, so 12 V loads only',
                pack='50-100', note='Marking "A09T".'),
    'SMAJ':   L(block='Power in', value='SMAJ5.0A', pkg='SMA (DO-214AC)', spec='Unidirectional TVS, 5.0 V standoff',
                spares=1, where='Local maybe', ali='SMAJ5.0A SMA', subs='SMAJ5.0A from any maker. Not the "CA" (bidirectional)',
                pack='20-100', note='Band (cathode) toward +5V.'),
    'SS34':   L(block='OUT', value='SS34', pkg='SMA (DO-214AC)', spec='Schottky 40 V 3 A',
                spares=1, where='Local maybe', ali='SS34 SMA DO-214AC', subs='SS24, SS36, SS14 (1 A, fine for small loads)',
                pack='50-100', note='Check the package is SMA, not SMB. Band toward V+.'),
    'PTC110': L(block='Power in', value='PTC 1.1 A hold', pkg='1812', spec='Resettable fuse, 1.1 A hold, >= 6 V',
                spares=1, where='Local maybe', ali='1812 PTC 1.1A SMD resettable fuse', subs='Bourns MF-MSMF110-2, Littelfuse 1812L110',
                pack='10-50', note='Marking often "110".'),
    'PTC050': L(block='Ports', value='PTC 0.5 A hold', pkg='1206', spec='Resettable fuse, 0.5 A hold, >= 6 V',
                spares=2, where='AliExpress', ali='1206 PTC 0.5A SMD resettable fuse', subs='Bourns MF-NSMF050-2, Littelfuse 1206L050',
                pack='50-100', note='One per port. Fallback: 0R 1206 or a wire bridge (port loses its own protection).'),
    'CP100':  L(block='Power', value='100 uF 10 V', pkg='Radial 6.3 mm, 2.5 mm pitch', spec='Electrolytic, 10 V or higher, height <= 12 mm',
                spares=1, where='Local likely', ali='100uF 16V 6.3x7mm electrolytic', subs='100 uF 16 V or 25 V in 6.3 mm',
                pack='50-100', note='Mind polarity.'),
    'C10u':   L(block='Power', value='10 uF', pkg='0805', spec='X5R or X7R, 10 V or higher', spares=5,
                where='Local maybe', ali='0805 10uF 10V X5R', subs='16 V or 25 V rating', pack='100', note=''),
    'C22u':   L(block='3V3 rail', value='22 uF', pkg='0805', spec='X5R, 6.3 V or higher', spares=3,
                where='Local maybe', ali='0805 22uF 10V X5R', subs='10 V rating', pack='100', note=''),
    'C1u':    L(block='MCU', value='1 uF', pkg='0805', spec='X7R, 10 V or higher', spares=3,
                where='Local likely', ali='0805 1uF 25V X7R', subs='', pack='100', note=''),
    'C100n':  L(block='Decoupling', value='100 nF', pkg='0805', spec='X7R, 16 V or higher', spares=5,
                where='Local likely', ali='0805 100nF 50V X7R', subs='', pack='100',
                note='Same value is used as the NTC/analog filter option (Port options sheet).'),
    'R10k':   L(block='Resistors', value='10 k', pkg='0805', spec='1 % or 5 %', spares=5,
                where='Local likely', ali='0805 resistor kit 1%', subs='', pack='100 / kit', note=''),
    'R1k':    L(block='Resistors', value='1 k', pkg='0805', spec='1 % or 5 %', spares=5,
                where='Local likely', ali='0805 resistor kit 1%', subs='', pack='100 / kit', note=''),
    'R330':   L(block='Resistors', value='330 R', pkg='0805', spec='1 % or 5 %', spares=5,
                where='Local likely', ali='0805 resistor kit 1%', subs='220 R to 470 R', pack='100 / kit',
                note='Series protection on each port A pin and UART TX.'),
    'R470':   L(block='Resistors', value='470 R', pkg='0805', spec='1 % or 5 %', spares=3,
                where='Local likely', ali='0805 resistor kit 1%', subs='330 R to 1 k', pack='100 / kit', note=''),
    'R22k':   L(block='Resistors', value='22 k', pkg='0805', spec='1 % or 5 %', spares=3,
                where='Local likely', ali='0805 resistor kit 1%', subs='20 k', pack='100 / kit',
                note='UART RX 5 V divider bottom.'),
    'R100':   L(block='Resistors', value='100 R', pkg='0805', spec='1 % or 5 %', spares=3,
                where='Local likely', ali='0805 resistor kit 1%', subs='47 R to 220 R', pack='100 / kit', note=''),
    'R4k7':   L(block='Resistors', value='4.7 k', pkg='0805', spec='1 % or 5 %', spares=3,
                where='Local likely', ali='0805 resistor kit 1%', subs='', pack='100 / kit', note='I2C pull-ups.'),
    'R100k':  L(block='Resistors', value='100 k', pkg='0805', spec='1 % or 5 %', spares=3,
                where='Local likely', ali='0805 resistor kit 1%', subs='47 k', pack='100 / kit', note=''),
    'LEDR':   L(block='Indicators', value='LED red', pkg='0805', spec='Vf about 2 V', spares=2,
                where='Local likely', ali='0805 LED red', subs='Orange', pack='100',
                note='Do not use blue, green or white: Vf too high for 3.3 V with 1 k.'),
    'LEDY':   L(block='Indicators', value='LED yellow', pkg='0805', spec='Vf about 2 V', spares=2,
                where='Local likely', ali='0805 LED yellow', subs='Orange, red', pack='100', note='Cathode mark toward GND.'),
    'SW':     L(block='MCU', value='Tactile switch', pkg='6 x 6 mm THT, 4 pins', spec='Any height (5 mm typical)',
                spares=1, where='Local likely', ali='6x6x5 tactile switch DIP 4 pin', subs='', pack='50-100', note='RESET and BOOT.'),
    'XH4':    L(block='Connectors', value='XH 4P socket, vertical', pkg='JST XH B4B-XH-A, 2.50 mm',
                spec='Top entry, through-hole. "XH2.54" AliExpress parts fit', spares=1, where='AliExpress',
                ali='XH2.54 4P straight pin header socket', subs='Plain 1x4 2.54 mm pin header (no lock)', pack='50-100',
                note='8 ports + USB input. Housings and crimps are on the Off-board sheet.'),
    'XH3':    L(block='Connectors', value='XH 3P socket, vertical', pkg='JST XH B3B-XH-A, 2.50 mm',
                spec='Top entry, through-hole', spares=1, where='Have', ali='XH2.54 3P straight pin header socket',
                subs='Plain 1x3 2.54 mm pin header', pack='100', note='Switched output connector.'),
    'H5':     L(block='Expansion', value='1x5 pin header', pkg='2.54 mm', spec='Optional, only if you use the spare pins',
                spares=0, where='Local likely', ali='2.54mm single row male header', subs='', pack='strip of 40',
                note='Footprint only. Fit when needed.'),
    'JP3':    L(block='Ports', value='3-way solder jumper', pkg='PCB copper', spec='No part to buy',
                spares=0, where='-', ali='', subs='', pack='',
                note='Set at the factory by a thin trace (1-2 = 3V3; UART port 2-3 = 5V). To change: cut the trace, bridge the other side with solder.'),
    'JP2':    L(block='OUT', value='2-pad solder jumper', pkg='PCB copper', spec='No part to buy', spares=0, where='-',
                ali='', subs='', pack='', note='Open by default. Never bridge it while an external supply is on V+.'),
    'OPT_R':  L(block='Ports', value='Option resistors (empty)', pkg='0805', spec='See Port options sheet',
                spares=0, where='-', ali='', subs='', pack='', note='Empty by default. Values depend on what you plug in.'),
    'OPT_C':  L(block='Ports', value='Option capacitors (empty)', pkg='0805', spec='See Port options sheet',
                spares=0, where='-', ali='', subs='', pack='', note='Empty by default. 100 nF for analog, 1 nF for pulses.'),
    'MH':     L(block='Mechanical', value='M3 mounting hole', pkg='3.2 mm', spec='Standoffs on Off-board sheet',
                spares=0, where='-', ali='', subs='', pack='', note='No part on the PCB.'),
}

LINE_ORDER = ['ESP', 'AMS', 'CH340C', 'USBLC6', 'NPN', 'AO3400', 'SMAJ', 'SS34', 'PTC110', 'PTC050',
              'CP100', 'C22u', 'C10u', 'C1u', 'C100n',
              'R330', 'R1k', 'R10k', 'R100', 'R470', 'R4k7', 'R22k', 'R100k',
              'LEDR', 'LEDY', 'SW', 'XH4', 'XH3', 'H5', 'JP3', 'JP2', 'OPT_R', 'OPT_C', 'MH']


def all_refs():
    return CORE + port_refs()
