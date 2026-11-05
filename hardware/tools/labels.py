# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
# Silkscreen labels: (text, u, v, size, layer, rot, just, bold)  just: -1 left, 0 center, 1 right
F, B = pcbnew.F_SilkS, pcbnew.B_SilkS
LABELS = [
    # USB breakout input (J1, right edge)
    ('J1 USB', 62.0, 6.7, 0.9, F, 0, 0, True),
    ('5V', 63.95, 8.8, 0.8, F, 0, -1, False),
    ('D-', 63.95, 11.34, 0.8, F, 0, -1, False),
    ('D+', 63.95, 13.88, 0.8, F, 0, -1, False),
    ('G', 63.95, 16.42, 0.8, F, 0, -1, False),
    # PZEM (J2)
    ('J2 PZEM', 30.3, 52.8, 0.8, F, 90, 0, True),
    ('5V', 32.6, 51.3, 0.8, F, 0, 0, False),
    ('RX', 35.14, 51.3, 0.8, F, 0, 0, False),
    ('TX', 37.68, 51.3, 0.8, F, 0, 0, False),
    ('G', 40.22, 51.3, 0.8, F, 0, 0, False),
    # Relay module (J3) + supply select
    ('J3 RELAY', 19.4, 52.8, 0.8, F, 90, 0, True),
    ('VCC', 21.6, 51.3, 0.8, F, 0, 0, False),
    ('G', 24.14, 51.3, 0.8, F, 0, 0, False),
    ('IN', 26.68, 51.3, 0.8, F, 0, 0, False),
    ('3V3', 21.5, 48.6, 0.8, F, 0, 1, False),
    ('5V', 25.7, 48.6, 0.8, F, 0, -1, False),
    # NTC (J4)
    ('J4 NTC 10k', 12.54, 44.4, 0.9, F, 0, 0, True),
    # Expansion (J5)
    ('J5 EXP', 3.6, 9.7, 0.9, F, 0, 0, True),
    ('3V3', 5.0, 12.0, 0.8, F, 0, -1, False),
    ('IO35', 5.0, 14.54, 0.8, F, 0, -1, False),
    ('IO32', 5.0, 17.08, 0.8, F, 0, -1, False),
    ('IO33', 5.0, 19.62, 0.8, F, 0, -1, False),
    ('IO26', 5.0, 22.16, 0.8, F, 0, -1, False),
    ('GND', 5.0, 24.7, 0.8, F, 0, -1, False),
    # buttons / LEDs
    ('RST', 24.25, 31.5, 0.9, F, 0, 0, True),
    ('BOOT', 36.85, 31.5, 0.9, F, 0, 0, True),
    ('PWR', 57.4, 51.3, 0.8, F, 0, 0, False),
    ('STAT', 44.3, 32.0, 0.8, F, 0, 0, False),
    # title
    ('ESP32-PZEM-RELAY', 10.5, 35.0, 1.2, F, 0, 0, True),
    ('v1.0  2026-10', 10.5, 37.0, 0.9, F, 0, 0, False),
    # back side legend (mirrored when viewed from the top)
    ('LOW VOLTAGE BOARD - NO MAINS', 33.0, 34.0, 1.2, B, 0, 0, True),
    ('mains only on PZEM + relay module terminals', 33.0, 36.2, 0.9, B, 0, 0, False),
    ('J1 USB: 1=5V 2=D- 3=D+ 4=GND', 33.0, 38.2, 0.9, B, 0, 0, False),
    ('J2 PZEM: 5V RX(IO17) TX(IO16) GND', 33.0, 40.0, 0.9, B, 0, 0, False),
    ('J3 RELAY: VCC GND IN(IO27)', 33.0, 41.8, 0.9, B, 0, 0, False),
    ('J4 NTC->IO34  LED->IO2', 33.0, 43.6, 0.9, B, 0, 0, False),
    ('JP1: 1-2=3V3 (default)  2-3=5V', 33.0, 45.4, 0.9, B, 0, 0, False),
    ('R12: fit only for HIGH-trigger relay', 33.0, 47.2, 0.9, B, 0, 0, False),
]
