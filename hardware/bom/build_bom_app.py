#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
"""Build the local BOM / procurement web app from the same data as the BOM spreadsheet.
usage: python3 build_bom_app.py bom-app.html"""
import json
import os
import sys
from collections import Counter
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools'))
from parts import LINES, LINE_ORDER, all_refs
from bom_extra import OFFBOARD, OPTIONS

OUT = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))

fit = Counter(r[6] for r in all_refs() if r[4] == 'Fit')
refs = {}
for r in sorted(all_refs(), key=lambda r: r[0]):
    if r[4] == 'Fit':
        refs.setdefault(r[6], []).append(r[0])


def shop_of(where, key=''):
    if key == 'PCB':
        return 'PCB maker'
    return {'Local likely': 'Local store', 'Local maybe': 'Local store', 'AliExpress': 'AliExpress',
            'Have': 'AliExpress', 'Ordered': 'PCB maker'}.get(where, 'Local store')


items = []
for key in LINE_ORDER:
    d = LINES[key]
    if fit[key] == 0:
        continue                                # solder jumpers, holes, empty option footprints
    items.append(dict(id=key, section='pcb', name=d['value'], pkg=d['pkg'], spec=d['spec'],
                      refs=' '.join(refs[key]), perBoard=fit[key], basis='board', spares=d['spares'],
                      where=d['where'], shop=shop_of(d['where']), ali=d['ali'], subs=d['subs'], pack=d['pack'],
                      note=d['note'], stock=100 if key == 'XH3' else None))
for i, (v, pkg, use, q, ali) in enumerate(OPTIONS):
    items.append(dict(id=f'opt{i + 1}', section='option', name=v, pkg=pkg, spec=use, refs='', perBoard=q,
                      basis='drawer', spares=0, where='Local likely', shop='Local store', ali=ali, subs='',
                      pack='', note='Drawer stock for configuring ports', stock=None))
for i, (item, spec, q, basis, sp, where, ali, note) in enumerate(OFFBOARD):
    items.append(dict(id=f'off{i + 1}', section='offboard', name=item, pkg='', spec=spec, refs='', perBoard=q,
                      basis='board' if basis == 'per board' else 'oneoff', spares=sp, where=where,
                      shop=shop_of(where, item), ali=ali, subs='', pack='', note=note,
                      stock=5 if item == 'PCB' else None))

data = dict(project='ESP32 Modular Base', rev='2.0', boardsDefault=5, items=items)
html = open(os.path.join(HERE, 'bom_app_template.html')).read()
html = html.replace('/*__DATA__*/null', json.dumps(data, ensure_ascii=False))
open(OUT, 'w').write(html)
print('written', OUT, len(items), 'items')
