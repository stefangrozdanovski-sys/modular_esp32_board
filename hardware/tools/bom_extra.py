# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
# Off-board items and option-drawer parts (shared by build_bom.py and build_bom_app.py)
# OFFBOARD: (item, spec, qty, basis, spares, where, aliexpress search, note)
# OPTIONS:  (value, package, used for, suggested drawer qty, aliexpress search)
OFFBOARD = [
    ('PCB', '2 layers, 75 x 65 mm, 1.6 mm, 1 oz, HASL lead-free', 1, 'per board', 0,
     'Ordered', '', 'Ordered 2026-10-14 from Seeed Fusion: 5 boards $9.90 + $16.48 shipping.'),
    ('XH 4P housing (female plug)', 'JST XH 2.50 mm, 4 positions', 9, 'per board', 2, 'AliExpress',
     'XH2.54 4P housing', 'One per port in use (8 ports + USB input). Buy fewer if you won\'t use every port.'),
    ('XH crimp terminals', 'For XH housings, AWG 22-28', 39, 'per board', 20, 'AliExpress',
     'XH2.54 crimp terminal', '9 x 4P + 1 x 3P = 39 per fully wired board. Spares for bad crimps.'),
    ('XH 3P housing (female plug)', 'JST XH 2.50 mm, 3 positions', 1, 'per board', 0, 'Have',
     'XH2.54 3P housing', 'For the OUT connector. Your 3P kit likely covers it.'),
    ('XH 4P pre-crimped lead (alternative)', '20 cm, one end with housing', 0, 'per board', 0, 'AliExpress',
     'XH2.54 4P cable single head 20cm', 'Instead of crimping yourself. Set Qty if you go this way.'),
    ('USB-C breakout (bare)', 'Pads V, D-, D+, G; no CC resistors', 1, 'per board', 0, 'Have',
     'USB type C breakout board', 'Needs a USB-A to C cable (no CC resistors).'),
    ('USB-A to USB-C cable', 'Data-capable, short', 1, 'per board', 0, 'Local likely',
     'USB A to type C cable 30cm', 'Data lines are needed for flashing and logs.'),
    ('USB charger 5 V', '2 A or more, CE marked', 1, 'per board', 0, 'Local likely', '', 'Mains side of the box, behind the divider.'),
    ('Lead wire, J1 to breakout', '4 cores, AWG 24-26, under 10 cm', 1, 'per board', 0, 'Local likely', '',
     'Twist D+ and D-.'),
    ('M3 nylon standoff', 'Male-female, 10 mm', 4, 'per board', 0, 'Local maybe', 'M3 nylon standoff 10mm', ''),
    ('M3 nylon screw', '6 mm', 4, 'per board', 0, 'Local maybe', 'M3 nylon screw 6mm', 'Board side.'),
    ('M3 nylon nut', 'M3', 4, 'per board', 0, 'Local maybe', 'M3 nylon nut', 'Base-plate side, if the box needs it.'),
    ('Crimp tool for XH', 'For 2.5 mm JST-style terminals (e.g. IWISS SN-28B / SN-01BM)', 1, 'one-off', 0,
     'AliExpress', 'SN-28B crimping tool', 'Skip if you already have one.'),
]

OPTIONS = [
    ('10 k 1 %', '0805', 'NTC reference (RBU)', 10, '0805 resistor 10k 1%'),
    ('10 k', '0805', 'Pull-ups, pull-downs, divider series (RAU, RAD, RB)', 20, '0805 resistor kit 1%'),
    ('4.7 k', '0805', 'DS18B20 pull-up (RAU)', 10, '0805 resistor kit 1%'),
    ('22 k', '0805', '5 V divider bottom (RBD)', 10, '0805 resistor kit 1%'),
    ('100 nF', '0805', 'Analog / NTC filter (CB)', 10, '0805 100nF 50V X7R'),
    ('1 nF', '0805', 'Pulse input filter (CB)', 10, '0805 1nF 50V C0G'),
    ('0 R', '0805', 'Bypass a series resistor', 10, '0805 0 ohm resistor'),
    ('0 R', '1206', 'Bypass a port PTC if you have none', 5, '1206 0 ohm resistor'),
]

# RECIPES: (job, port pin, VP jumper, fit on top of defaults, ESPHome, example on P3, notes)
RECIPES = [
    ('Relay module, low-level trigger', 'A', '3V3', 'Nothing', 'switch: gpio, inverted: true', 'Defaults only',
     'Most 3.3 V relay modules. 5V module: VP to 5V only if its IN switches from a 3.3 V high.'),
    ('Relay module, high-level trigger', 'A', '3V3', 'RAD 10 k', 'switch: gpio', 'R303 = 10k', 'Keeps the relay off during boot.'),
    ('DS18B20 (1-Wire)', 'A', '3V3', 'RAU 4.7 k', 'one_wire + dallas_temp', 'R302 = 4k7', 'Several sensors can share one port.'),
    ('Button or dry contact', 'A', '-', 'Nothing (internal pull-up); RAU 10 k for long cables', 'binary_sensor: gpio',
     'R302 = 10k (long cable)', 'Contact between A and GND.'),
    ('NTC 10 k (B3950)', 'B', '-', 'RBU 10 k 1 %, CB 100 nF', 'adc + resistance + ntc', 'R305 = 10k 1%, C301 = 100nF',
     'RB 1 k stays fitted. Same circuit as v1.0.'),
    ('0-3.3 V analog sensor', 'B', 'as sensor needs', 'CB 100 nF', 'adc (attenuation: 12db)', 'C301 = 100nF', 'Signal above 3.3 V: use the 5 V divider row.'),
    ('5 V logic or pulse (flow sensor with 5 V output)', 'B (P3-P6)', '5V', 'RB 10 k (replace 1 k), RBD 22 k, CB 1 nF',
     'pulse_counter', 'R304 = 10k, R306 = 22k, C301 = 1nF',
     'Check first: sensor powered, output idles at 5 V = this row. Floating = next row.'),
    ('Open-collector pulse (flow sensor)', 'A', '5V', 'RAU 10 k', 'pulse_counter', 'R302 = 10k', 'Pull-up goes to 3V3, so the ESP32 never sees 5 V.'),
    ('PZEM-004T energy meter', 'UART port', '5V (default)', 'Nothing', 'uart + modbus + pzemac', 'J701',
     'Cable: GND-GND, 5V-5V, board TX -> PZEM RX, board RX <- PZEM TX.'),
    ('RS485 module (Modbus)', 'UART port + P5 or P6 B', '5V', 'Remove R706 if the module is 3.3 V', 'uart + modbus (flow_control_pin)',
     'Direction pin on IO32 (P5 B)', 'Auto-direction modules need no extra pin.'),
    ('I2C sensors (BME280, SHT3x, ADS1115, OLED)', 'I2C port', '3V3 (default)', 'Nothing', 'i2c + sensor', 'J801',
     'Several modules can share the port with a splitter.'),
    ('Solid-state relay (DC input), buzzer, 12/24 V LED, fan', 'OUT', 'V+ from load supply', 'Nothing', 'output: gpio or ledc', 'J901',
     'Supply negative to GND pin 1. Load between V+ and OUT.'),
]
