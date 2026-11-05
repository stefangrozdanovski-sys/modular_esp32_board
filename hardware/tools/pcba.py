#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
"""JLCPCB / PCBWay assembly files from a KiCad 7 position file and parts.py.

  pcba.py <kicad pos.csv> <out dir>    write BOM + CPL (JLCPCB and PCBWay) and hand-solder list
  pcba.py --verify <out dir>           query JLCPCB for every LCSC number (needs network access
                                       to cart.jlcpcb.com) and write lcsc_check.csv

The pos file comes from `kicad-cli pcb export pos --format csv --units mm --smd-only`
(see export.sh). KiCad 7 already drops footprints marked "exclude from position files"
(DNP options, solder jumpers, holes); this script cross-checks the result against parts.py
and stops if a fitted SMD part is missing or a non-fitted part slipped in.
"""
import csv
import datetime
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parts  # noqa: E402

# BOM line -> LCSC part. 'checked' is filled only for numbers looked up live on
# jlcpcb.com / lcsc.com: (date, stock, library type). None = candidate, NOT verified.
# Run `pcba.py --verify` (or check by hand) and update before ordering.
LCSC = {
    'ESP':    dict(lcsc='C701341', mpn='ESP32-WROOM-32E-N4', comment='ESP32-WROOM-32E-N4', checked=None),
    'AMS':    dict(lcsc='C6186',   mpn='AMS1117-3.3',        comment='AMS1117-3.3',        checked=None),
    'CH340C': dict(lcsc='C84681',  mpn='CH340C',             comment='CH340C',
                   checked=('2026-11-05', '101,694 (jlcpcb.com) / 100,341 (lcsc.com)', 'Extended')),
    'USBLC6': dict(lcsc='C7519',   mpn='USBLC6-2SC6',        comment='USBLC6-2SC6',        checked=None),
    'NPN':    dict(lcsc='C20526',  mpn='MMBT3904',           comment='MMBT3904',           checked=None),
    'AO3400': dict(lcsc='C20917',  mpn='AO3400A',            comment='AO3400A',            checked=None),
    'SMAJ':   dict(lcsc='C113952', mpn='SMAJ5.0A',           comment='SMAJ5.0A',           checked=None),
    'SS34':   dict(lcsc='C8678',   mpn='SS34',               comment='SS34',               checked=None),
    'PTC110': dict(lcsc='C163516', mpn='1812L110PR',         comment='PTC 1.1A 1812',      checked=None),
    'PTC050': dict(lcsc='C883122', mpn='BSMD1206-050-6V',    comment='PTC 0.5A 1206',      checked=None),
    'C22u':   dict(lcsc='C45783',  mpn='CL21A226MQQNNNE',    comment='22uF 0805',          checked=None),
    'C10u':   dict(lcsc='C15850',  mpn='CL21A106KAYNNNE',    comment='10uF 0805',          checked=None),
    'C1u':    dict(lcsc='C28323',  mpn='CL21B105KBFNNNE',    comment='1uF 0805',           checked=None),
    'C100n':  dict(lcsc='C49678',  mpn='CC0805KRX7R9BB104',  comment='100nF 0805',         checked=None),
    'R330':   dict(lcsc='C17630',  mpn='0805W8F3300T5E',     comment='330R 0805',          checked=None),
    'R1k':    dict(lcsc='C17513',  mpn='0805W8F1001T5E',     comment='1k 0805',            checked=None),
    'R10k':   dict(lcsc='C17414',  mpn='0805W8F1002T5E',     comment='10k 0805',           checked=None),
    'R100':   dict(lcsc='C17408',  mpn='0805W8F1000T5E',     comment='100R 0805',          checked=None),
    'R470':   dict(lcsc='C17710',  mpn='0805W8F4700T5E',     comment='470R 0805',          checked=None),
    'R4k7':   dict(lcsc='C17673',  mpn='0805W8F4701T5E',     comment='4.7k 0805',          checked=None),
    'R22k':   dict(lcsc='C17560',  mpn='0805W8F2202T5E',     comment='22k 0805',           checked=None),
    'R100k':  dict(lcsc='C149504', mpn='0805W8F1003T5E',     comment='100k 0805',          checked=None),
    'LEDR':   dict(lcsc='C84256',  mpn='NCD0805R1',          comment='LED red 0805',       checked=None),
    'LEDY':   dict(lcsc='C2296',   mpn='KT-0805Y',           comment='LED yellow 0805',    checked=None),
}

# JLCPCB rotation correction (degrees, added to KiCad's rotation) by footprint name prefix.
# Values follow the community JLCPCB tables (JLCKicadTools cpl_rotations_db.csv, KiBot's
# internal JLCPCB list). NOT confirmed for this board: check every part in JLCPCB's
# placement preview before ordering and fix the number here, not in the CSV.
ROTATION = [
    (r'^SOT-223',                 180),  # AMS1117 U2
    (r'^SOT-23-6',                180),  # USBLC6 U4
    (r'^SOT-23',                  180),  # MMBT3904 Q1 Q2, AO3400A Q901
    (r'^SOIC-',                   270),  # CH340C U3
    (r'^D_SMA',                   180),  # SMAJ5.0A D1, SS34 D901 (cathode band)
    (r'^LED_0805',                  0),  # LED1 LED2: polarity, check the cathode mark
    (r'^ESP32-WROOM-32',            0),  # U1: no published value found, check the preview
    (r'^(R|C)_0805|^Fuse_',         0),  # passives, PTCs
]

THT_NOTE = 'Hand-solder after assembly, or order JLCPCB THT assembly (see README).'


def rot_fix(pkg):
    for pat, deg in ROTATION:
        if re.search(pat, pkg):
            return deg
    sys.exit(f'pcba.py: no rotation rule for footprint {pkg!r}; add one to ROTATION')


def fp_name(fp):
    return fp.split(':', 1)[1]


def is_tht(fp):
    return fp.split(':')[0] in ('Capacitor_THT', 'Button_Switch_THT', 'Connector_JST', 'Connector_PinHeader')


def read_pos(path):
    with open(path, newline='') as f:
        return list(csv.DictReader(f))


def natkey(ref):
    m = re.match(r'([A-Z]+)(\d+)', ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def build(pos_path, out):
    refs = {r[0]: r for r in parts.all_refs()}
    smd_fit = {ref for ref, r in refs.items() if r[4] == 'Fit' and not is_tht(r[3])}
    tht_fit = sorted((ref for ref, r in refs.items() if r[4] == 'Fit' and is_tht(r[3])), key=natkey)
    pos = read_pos(pos_path)
    placed = {p['Ref'] for p in pos}
    extra, missing = placed - smd_fit, smd_fit - placed
    if extra or missing:
        sys.exit(f'pcba.py: pos file does not match parts.py. extra={sorted(extra)} missing={sorted(missing)}')
    for p in pos:
        if fp_name(refs[p['Ref']][3]) != p['Package']:
            sys.exit(f"pcba.py: footprint mismatch for {p['Ref']}: {p['Package']}")
    no_lcsc = sorted({refs[r][6] for r in smd_fit} - LCSC.keys())
    if no_lcsc:
        sys.exit(f'pcba.py: BOM lines without an LCSC entry: {no_lcsc}')

    os.makedirs(out, exist_ok=True)
    pos.sort(key=lambda p: natkey(p['Ref']))

    # CPL
    cpl = []
    for p in pos:
        layer = 'Top' if p['Side'] == 'top' else 'Bottom'
        rot = (float(p['Rot']) + rot_fix(p['Package'])) % 360
        cpl.append((p['Ref'], f"{float(p['PosX']):.4f}mm", f"{float(p['PosY']):.4f}mm", layer, f'{rot:g}'))
    write(out, 'esp32-modular-v2.0-CPL-JLCPCB.csv', ['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'], cpl)
    write(out, 'esp32-modular-v2.0-CPL-PCBWay.csv', ['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'],
          [(r, x, y, l, f"{float(p['Rot']):g}") for (r, x, y, l, _), p in zip(cpl, pos)])

    # BOM, one row per line, in parts.py order
    groups = {}
    for ref in smd_fit:
        groups.setdefault(refs[ref][6], []).append(ref)
    jlc, pcbway = [], []
    for line in parts.LINE_ORDER:
        if line not in groups:
            continue
        rs = sorted(groups[line], key=natkey)
        e, fp = LCSC[line], fp_name(refs[rs[0]][3])
        jlc.append((e['comment'], ','.join(rs), fp, e['lcsc']))
        info = parts.LINES[line]
        pcbway.append((len(rs), ','.join(rs), e['mpn'], f"{e['comment']}; {info['spec']}", info['pkg'],
                       'SMD', e['lcsc']))
    write(out, 'esp32-modular-v2.0-BOM-JLCPCB.csv', ['Comment', 'Designator', 'Footprint', 'LCSC Part #'], jlc)
    write(out, 'esp32-modular-v2.0-BOM-PCBWay.csv',
          ['Qty', 'Designator', 'Manufacturer Part Number', 'Description', 'Package', 'Type', 'LCSC Part #'], pcbway)

    # THT, hand-soldered
    tht = {}
    for ref in tht_fit:
        tht.setdefault(refs[ref][6], []).append(ref)
    write(out, 'esp32-modular-v2.0-THT-hand-solder.csv', ['Qty', 'Designator', 'Part', 'Package', 'Note'],
          [(len(rs), ','.join(rs), parts.LINES[k]['value'], parts.LINES[k]['pkg'], THT_NOTE)
           for k, rs in tht.items()])
    print(f'pcba.py: {len(cpl)} SMD placements, {len(jlc)} BOM lines, {len(tht_fit)} THT parts -> {out}')


def write(out, name, head, rows):
    with open(os.path.join(out, name), 'w', newline='') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(head)
        w.writerows(rows)


def verify(out):
    """Live lookup on JLCPCB's parts API. Writes lcsc_check.csv; copy results into LCSC/README."""
    today = datetime.date.today().isoformat()
    rows = []
    for line, e in LCSC.items():
        url = f"https://cart.jlcpcb.com/shoppingCart/smtGood/getComponentDetail?componentCode={e['lcsc']}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'pcba.py'})
            d = json.load(urllib.request.urlopen(req, timeout=30))['data'] or {}
            lib = {'base': 'Basic', 'expand': 'Extended'}.get(d.get('componentLibraryType'), d.get('componentLibraryType'))
            rows.append((line, e['lcsc'], d.get('componentModelEn'), d.get('componentSpecificationEn'),
                         d.get('stockCount'), lib, d.get('describe'), today))
        except Exception as ex:  # network blocked, part gone, API changed
            rows.append((line, e['lcsc'], 'ERROR', '', '', '', str(ex)[:120], today))
        print(*rows[-1][:6])
    write(out, 'lcsc_check.csv', ['Line', 'LCSC', 'Model', 'Package', 'Stock', 'Library', 'Description', 'Checked'], rows)


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--verify':
        verify(sys.argv[2])
    elif len(sys.argv) == 3:
        build(sys.argv[1], sys.argv[2])
    else:
        sys.exit(__doc__)
