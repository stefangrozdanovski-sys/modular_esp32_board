# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
"""Build the BOM workbook from parts.py.  Usage: python build_bom.py out.xlsx"""
import re
import sys
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import FormulaRule
from openpyxl.comments import Comment

import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
from parts import LINES, LINE_ORDER, PORTS, TEMPLATE, all_refs
from bom_extra import OFFBOARD, OPTIONS, RECIPES

OUT = sys.argv[1]
FONT = 'Arial'
F = lambda **k: Font(name=FONT, size=k.pop('size', 10), **k)
HDR_FILL = PatternFill('solid', fgColor='1F3A4D')
SEC_FILL = PatternFill('solid', fgColor='DCE6EC')
INPUT_FILL = PatternFill('solid', fgColor='FFF2A8')
GREY_FILL = PatternFill('solid', fgColor='F2F2F2')
BUY_FILL = PatternFill('solid', fgColor='FBD5C9')
THIN = Side(style='thin', color='BFBFBF')
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical='top')
CENTER = Alignment(horizontal='center', vertical='top', wrap_text=True)
BLUE = '0000FF'
EUR = '€#,##0.00;-€#,##0.00;"-"'
QTY = '0;-0;"-"'

wb = Workbook()


def header(ws, row, cols, widths=None):
    for i, h in enumerate(cols, 1):
        c = ws.cell(row=row, column=i, value=h)
        c.font = F(bold=True, color='FFFFFF')
        c.fill = HDR_FILL
        c.alignment = Alignment(wrap_text=True, vertical='center', horizontal='center')
        c.border = BOX
    ws.row_dimensions[row].height = 30
    if widths:
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w


def cell(ws, r, c, v, *, fmt=None, inp=False, bold=False, align=WRAP, fill=None, color=None):
    x = ws.cell(row=r, column=c, value=v)
    x.font = F(bold=bold, color=(BLUE if inp else color))
    x.alignment = align
    x.border = BOX
    if inp:
        x.fill = INPUT_FILL
    elif fill:
        x.fill = fill
    if fmt:
        x.number_format = fmt
    return x


def title(ws, text, sub):
    ws['A1'] = text
    ws['A1'].font = F(bold=True, size=14, color='1F3A4D')
    ws['A2'] = sub
    ws['A2'].font = F(italic=True, color='595959')


def natkey(ref):
    m = re.match(r'([A-Z]+)(\d+)', ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


# ------------------------------------------------------------------ Read me
rm = wb.active
rm.title = 'Read me'
rm.column_dimensions['A'].width = 3
rm.column_dimensions['B'].width = 34
rm.column_dimensions['C'].width = 16
rm.column_dimensions['D'].width = 70
title(rm, 'ESP32 Modular Base v2.0: bill of materials',
      'Schematic and PCB done 2026-10-13 (75 x 65 mm, 2 layers). Generated from the same parts list as the schematic.')

rm['B4'] = 'Build settings'
rm['B4'].font = F(bold=True, size=11)
cell(rm, 5, 2, 'Boards to build', bold=True)
cell(rm, 5, 3, 5, inp=True, fmt='0', align=CENTER)
rm['C5'].comment = Comment('PCB makers ship 5 boards minimum. Change this and every "Need" column updates.', 'BOM')
cell(rm, 5, 4, 'All "Need" quantities scale with this number.')
wb.defined_names['Boards'] = DefinedName('Boards', attr_text="'Read me'!$C$5")

rm['B7'] = 'How to use this file'
rm['B7'].font = F(bold=True, size=11)
howto = [
    ('Yellow cell, blue text', 'You fill this in: In stock, Unit price, Boards to build, option quantities, Fit status.'),
    ('White cell, black text', 'Calculated. Do not type over it.'),
    ('Red-tinted row', 'Something still has to be bought (To buy > 0).'),
    ('Need', 'Qty per board x Boards to build + Spares. Spares cover 0805 parts that fly off the tweezers.'),
    ('To buy', 'Need minus In stock, never below zero.'),
    ('Where to look first', 'My estimate of which parts a local electronics store usually carries. Not a stock check.'),
    ('Qty per board', 'Counted from the Per reference sheet. Change a Fit status there (e.g. DNP to Fit) and the BOM follows.'),
    ('Example row', 'BOM line "XH 3P socket" shows the format: In stock = 100 (the 3P stock you mentioned).'),
]
for i, (a, b) in enumerate(howto):
    cell(rm, 8 + i, 2, a, bold=True)
    cell(rm, 8 + i, 4, b)
    rm.merge_cells(start_row=8 + i, start_column=2, end_row=8 + i, end_column=3)
rm['B8'].fill = INPUT_FILL
rm['B8'].font = F(bold=True, color=BLUE)
rm['B10'].fill = BUY_FILL

r0 = 8 + len(howto) + 1
rm.cell(row=r0, column=2, value='Totals').font = F(bold=True, size=11)

rm.cell(row=r0 + 5, column=2, value='Sheets').font = F(bold=True, size=11)
sheets = [('BOM', 'Every part on the PCB, grouped by value. Stock, to-buy and cost columns.'),
          ('Port options', 'Port map, what each option footprint is for, setup recipes, and option parts to keep in the drawer.'),
          ('Off-board', 'Mating connectors, cables, standoffs, PCB order, crimp tool.'),
          ('Per reference', 'One row per reference designator: value, fitted or empty, footprint. Use it while soldering.')]
for i, (a, b) in enumerate(sheets):
    cell(rm, r0 + 6 + i, 2, a, bold=True)
    cell(rm, r0 + 6 + i, 4, b)
    rm.merge_cells(start_row=r0 + 6 + i, start_column=2, end_row=r0 + 6 + i, end_column=3)

# ------------------------------------------------------------------ Per reference
pr = wb.create_sheet('Per reference')
title(pr, 'Per reference', 'One row per reference designator. Fit: Fit = solder it, DNP = leave empty, Trace/Open = solder jumper, Hole = no part.')
PR_COLS = ['Ref', 'Block', 'Value', 'Fit', 'Function / connection', 'KiCad footprint', 'BOM line #', 'BOM line']
header(pr, 4, PR_COLS, [9, 13, 16, 8, 52, 50, 9, 26])
line_no = {k: i + 1 for i, k in enumerate(LINE_ORDER)}
block_order = ['Power in', '3V3 rail', 'USB-UART', 'MCU', 'Indicators'] + \
              [f'Port {p[0]}' for p in PORTS.values()] + ['OUT', 'Expansion', 'Mechanical']
refs = sorted(all_refs(), key=lambda r: (block_order.index(r[1]), natkey(r[0])))
dv = DataValidation(type='list', formula1='"Fit,DNP,Trace,Open,Hole"', allow_blank=False)
pr.add_data_validation(dv)
r = 5
for ref, block, val, fp, fit, func, line in refs:
    n = line_no[line]
    cell(pr, r, 1, ref, bold=True)
    cell(pr, r, 2, block)
    cell(pr, r, 3, val)
    cell(pr, r, 4, fit, inp=True, align=CENTER)
    dv.add(pr.cell(row=r, column=4))
    cell(pr, r, 5, func)
    cell(pr, r, 6, fp.split(':')[1], color='595959')
    cell(pr, r, 7, n, align=CENTER)
    cell(pr, r, 8, f"=INDEX(BOM!$D$5:$D${4 + len(LINE_ORDER)},G{r})")
    if fit == 'DNP':
        for c in range(1, 9):
            if c != 4:
                pr.cell(row=r, column=c).fill = GREY_FILL
    r += 1
PR_LAST = r - 1
pr.freeze_panes = 'B5'
pr.auto_filter.ref = f'A4:H{PR_LAST}'

# ------------------------------------------------------------------ BOM
bom = wb.create_sheet('BOM', 1)
title(bom, 'BOM: parts on the PCB',
      'Qty per board and empty footprints are counted from the Per reference sheet. Fill the yellow cells.')
COLS = ['#', 'Block', 'References', 'Value', 'Package', 'What to look for', 'Qty / board',
        'Empty footprints', 'Spares', 'Need', 'In stock', 'To buy', 'Where to look first',
        'AliExpress search', 'Substitutes', 'Typical pack', 'Unit price (€)', 'Line cost (€)', 'Notes']
header(bom, 4, COLS, [5, 12, 30, 22, 20, 34, 9, 10, 8, 8, 9, 8, 13, 28, 30, 10, 10, 10, 44])
refs_by_line = {}
for ref, *_rest in refs:
    pass
for row in all_refs():
    refs_by_line.setdefault(row[6], []).append(row)


def compress(rlist):
    """Fitted refs as a compact list; R101 R201 ... stays explicit (short enough)."""
    return ' '.join(sorted((x[0] for x in rlist), key=natkey))


first = 5
for i, key in enumerate(LINE_ORDER):
    r = first + i
    d = LINES[key]
    rl = refs_by_line.get(key, [])
    cell(bom, r, 1, i + 1, align=CENTER)
    cell(bom, r, 2, d['block'])
    cell(bom, r, 3, compress(rl))
    cell(bom, r, 4, d['value'], bold=True)
    cell(bom, r, 5, d['pkg'])
    cell(bom, r, 6, d['spec'])
    rng = f"'Per reference'!$G$5:$G${PR_LAST}"
    fit = f"'Per reference'!$D$5:$D${PR_LAST}"
    cell(bom, r, 7, f'=COUNTIFS({rng},A{r},{fit},"Fit")', fmt=QTY, align=CENTER)
    cell(bom, r, 8, f'=COUNTIFS({rng},A{r},{fit},"DNP")', fmt=QTY, align=CENTER)
    cell(bom, r, 9, d['spares'], fmt=QTY, align=CENTER, color=BLUE)
    cell(bom, r, 10, f'=IF(G{r}=0,0,G{r}*Boards+I{r})', fmt=QTY, align=CENTER, bold=True)
    stock = 100 if key == 'XH3' else None
    x = cell(bom, r, 11, stock, inp=True, fmt=QTY, align=CENTER)
    if key == 'XH3':
        x.comment = Comment('From you, 2026-10-13: 100 pcs XH 3P already stocked.', 'BOM')
    cell(bom, r, 12, f'=MAX(0,J{r}-N(K{r}))', fmt=QTY, align=CENTER, bold=True)
    cell(bom, r, 13, d['where'], align=CENTER)
    cell(bom, r, 14, d['ali'])
    cell(bom, r, 15, d['subs'])
    cell(bom, r, 16, d['pack'], align=CENTER)
    cell(bom, r, 17, None, inp=True, fmt=EUR)
    cell(bom, r, 18, f'=IF(ISNUMBER(Q{r}),L{r}*Q{r},0)', fmt=EUR)
    cell(bom, r, 19, d['note'])
    if key in ('JP3', 'JP2', 'OPT_R', 'OPT_C', 'MH'):
        for c in range(1, 20):
            if bom.cell(row=r, column=c).fill != INPUT_FILL:
                bom.cell(row=r, column=c).fill = GREY_FILL
BOM_LAST = first + len(LINE_ORDER) - 1
tr = BOM_LAST + 2
cell(bom, tr, 6, 'Totals', bold=True, fill=SEC_FILL)
cell(bom, tr, 7, f'=SUM(G{first}:G{BOM_LAST})', fmt=QTY, bold=True, align=CENTER, fill=SEC_FILL)
cell(bom, tr, 8, f'=SUM(H{first}:H{BOM_LAST})', fmt=QTY, bold=True, align=CENTER, fill=SEC_FILL)
cell(bom, tr, 11, 'Lines to buy', bold=True, fill=SEC_FILL)
cell(bom, tr, 12, f'=COUNTIF(L{first}:L{BOM_LAST},">0")', fmt=QTY, bold=True, align=CENTER, fill=SEC_FILL)
cell(bom, tr, 17, 'Total', bold=True, fill=SEC_FILL)
cell(bom, tr, 18, f'=SUM(R{first}:R{BOM_LAST})', fmt=EUR, bold=True, fill=SEC_FILL)
cell(bom, tr + 1, 6, 'Qty / board counts placed parts per board (solder jumpers and holes are not parts).', color='595959')
bom.merge_cells(start_row=tr + 1, start_column=6, end_row=tr + 1, end_column=12)
bom.conditional_formatting.add(f'A{first}:J{BOM_LAST}', FormulaRule(formula=[f'$L{first}>0'], fill=BUY_FILL))
bom.conditional_formatting.add(f'L{first}:P{BOM_LAST}', FormulaRule(formula=[f'$L{first}>0'], fill=BUY_FILL))
bom.freeze_panes = 'E5'
bom.auto_filter.ref = f'A4:S{BOM_LAST}'

# ------------------------------------------------------------------ Port options
po = wb.create_sheet('Port options', 2)
title(po, 'Port options', 'How each port is wired, what the empty footprints are for, and which parts to fit for each job.')
for col, w in zip('ABCDEFG', [14, 13, 30, 30, 34, 28, 40]):
    po.column_dimensions[col].width = w

r = 4
po.cell(row=r, column=1, value='1. Port map').font = F(bold=True, size=11)
r += 1
header_row = ['Port', 'Connector', 'Pin 3: A (GPIO)', 'Pin 4: B (GPIO)', 'VP default', 'Ref numbers', 'Notes']
for i, h in enumerate(header_row, 1):
    c = po.cell(row=r, column=i, value=h)
    c.font = F(bold=True, color='FFFFFF'); c.fill = HDR_FILL; c.border = BOX; c.alignment = CENTER
notes = {
    1: 'B is input-only, no internal pull-up. Avoid pulse counting on IO36 (false edges with Wi-Fi on).',
    2: 'B is input-only, no internal pull-up. Avoid pulse counting on IO39 (false edges with Wi-Fi on).',
    3: 'B is input-only, no internal pull-up. Good for 5 V pulse inputs.',
    4: 'B is input-only, no internal pull-up. Good for 5 V pulse inputs.',
    5: 'B is a full GPIO with ADC1: second UART, second I2C, RS485 direction pin.',
    6: 'B is a full GPIO with ADC1: second UART, second I2C, RS485 direction pin.',
    7: 'A = TX out, B = RX in through a 10k/22k divider (5 V devices). For a 3.3 V device remove R706.',
    8: 'A = SDA, B = SCL, 4.7 k pull-ups to 3V3 fitted. Remove pull-ups on 5 V modules (e.g. LCD backpack).',
}
for n, (label, ga, gb, vp, ov) in PORTS.items():
    r += 1
    vals = [label, f'J{n}01', ga + (' (ADC1)' if ga in ('IO32', 'IO33') else ''),
            gb + (' (ADC1)' if gb in ('IO32', 'IO33', 'IO34', 'IO35', 'IO36', 'IO39') else ''),
            vp, f'R{n}01-R{n}06, C{n}01, F{n}01, JP{n}01', notes[n]]
    for i, v in enumerate(vals, 1):
        cell(po, r, i, v, bold=(i == 1))
r += 1
cell(po, r, 1, 'OUT', bold=True)
cell(po, r, 2, 'J901')
cell(po, r, 3, 'IO23 -> AO3400A gate')
cell(po, r, 4, '-')
cell(po, r, 5, 'V+ external')
cell(po, r, 6, 'Q901, R901, R902, D901, JP901')
cell(po, r, 7, 'Pins: 1 GND, 2 V+, 3 OUT. Load between V+ and OUT. Up to about 2 A, 24 V. JP901 ties V+ to 5V (open by default).')
r += 1
cell(po, r, 1, 'Fixed', bold=True)
cell(po, r, 2, '-')
cell(po, r, 3, 'IO0 BOOT, IO1/IO3 CH340, IO2 status LED')
cell(po, r, 4, '-')
cell(po, r, 5, '-')
cell(po, r, 6, 'J902 (empty): 3V3, IO19, IO14, IO5, GND')
cell(po, r, 7, 'IO5 and IO14 pulse at boot: inputs only. IO12 and IO15 unused (boot strapping).')

r += 2
po.cell(row=r, column=1, value='2. Positions in every port (n = port number: 1-6 = P1-P6, 7 = UART, 8 = I2C)').font = F(bold=True, size=11)
r += 1
for i, h in enumerate(['Position', 'Ref', 'Default', 'Role'], 1):
    c = po.cell(row=r, column=i, value=h)
    c.font = F(bold=True, color='FFFFFF'); c.fill = HDR_FILL; c.border = BOX; c.alignment = CENTER
for pos, refpat, val, fit, role in TEMPLATE:
    r += 1
    cell(po, r, 1, pos, bold=True)
    cell(po, r, 2, refpat.replace('{n}', 'n'))
    cell(po, r, 3, val if fit != 'DNP' else 'empty')
    cell(po, r, 4, role)
    po.merge_cells(start_row=r, start_column=4, end_row=r, end_column=6)

r += 2
po.cell(row=r, column=1, value='3. Recipes: what to fit for each job').font = F(bold=True, size=11)
r += 1
for i, h in enumerate(['Job', 'Port pin', 'VP jumper', 'Fit (on top of defaults)', 'ESPHome', 'Example (port P3)', 'Notes'], 1):
    c = po.cell(row=r, column=i, value=h)
    c.font = F(bold=True, color='FFFFFF'); c.fill = HDR_FILL; c.border = BOX; c.alignment = CENTER
recipes = RECIPES
for rec in recipes:
    r += 1
    for i, v in enumerate(rec, 1):
        cell(po, r, i, v, bold=(i == 1))

r += 2
po.cell(row=r, column=1, value='4. Option parts to keep in the drawer (on top of the BOM quantities)').font = F(bold=True, size=11)
r += 1
for i, h in enumerate(['Value', 'Package', 'Used for', 'Suggested qty', 'In stock', 'To buy', 'AliExpress search'], 1):
    c = po.cell(row=r, column=i, value=h)
    c.font = F(bold=True, color='FFFFFF'); c.fill = HDR_FILL; c.border = BOX; c.alignment = CENTER
opts = OPTIONS
opt_first = r + 1
for v, pkg, use, q, ali in opts:
    r += 1
    cell(po, r, 1, v, bold=True)
    cell(po, r, 2, pkg)
    cell(po, r, 3, use)
    cell(po, r, 4, q, inp=True, fmt=QTY, align=CENTER)
    cell(po, r, 5, None, inp=True, fmt=QTY, align=CENTER)
    cell(po, r, 6, f'=MAX(0,D{r}-N(E{r}))', fmt=QTY, align=CENTER, bold=True)
    cell(po, r, 7, ali)
opt_last = r
po.conditional_formatting.add(f'A{opt_first}:G{opt_last}', FormulaRule(formula=[f'$F{opt_first}>0'], fill=BUY_FILL))
cell(po, r + 1, 3, 'Quantities are a drawer stock, not per board; they do not scale with Boards to build.', color='595959')
po.merge_cells(start_row=r + 1, start_column=3, end_row=r + 1, end_column=7)

# ------------------------------------------------------------------ Off-board
ob = wb.create_sheet('Off-board', 3)
title(ob, 'Off-board parts', 'Everything you need that is not soldered to the PCB.')
OCOLS = ['Item', 'Spec', 'Qty', 'Basis', 'Spares', 'Need', 'In stock', 'To buy', 'Where to look first',
         'AliExpress search', 'Unit price (€)', 'Line cost (€)', 'Notes']
header(ob, 4, OCOLS, [30, 34, 7, 11, 8, 8, 9, 8, 13, 30, 10, 10, 44])
items = OFFBOARD
for i, (item, spec, q, basis, sp, where, ali, note) in enumerate(items):
    r = 5 + i
    cell(ob, r, 1, item, bold=True)
    cell(ob, r, 2, spec)
    cell(ob, r, 3, q, fmt=QTY, align=CENTER, color=BLUE)
    cell(ob, r, 4, basis, align=CENTER)
    cell(ob, r, 5, sp, fmt=QTY, align=CENTER, color=BLUE)
    cell(ob, r, 6, f'=IF(C{r}=0,0,IF(D{r}="per board",C{r}*Boards,C{r})+E{r})', fmt=QTY, align=CENTER, bold=True)
    cell(ob, r, 7, None, inp=True, fmt=QTY, align=CENTER)
    cell(ob, r, 8, f'=MAX(0,F{r}-N(G{r}))', fmt=QTY, align=CENTER, bold=True)
    cell(ob, r, 9, where, align=CENTER)
    cell(ob, r, 10, ali)
    cell(ob, r, 11, None, inp=True, fmt=EUR)
    cell(ob, r, 12, f'=IF(ISNUMBER(K{r}),H{r}*K{r},0)', fmt=EUR)
    cell(ob, r, 13, note)
OB_LAST = 5 + len(items) - 1
basis_dv = DataValidation(type='list', formula1='"per board,one-off"')
ob.add_data_validation(basis_dv)
basis_dv.add(f'D5:D{OB_LAST}')
tr2 = OB_LAST + 2
cell(ob, tr2, 7, 'Lines to buy', bold=True, fill=SEC_FILL)
cell(ob, tr2, 8, f'=COUNTIF(H5:H{OB_LAST},">0")', fmt=QTY, bold=True, align=CENTER, fill=SEC_FILL)
cell(ob, tr2, 11, 'Total', bold=True, fill=SEC_FILL)
cell(ob, tr2, 12, f'=SUM(L5:L{OB_LAST})', fmt=EUR, bold=True, fill=SEC_FILL)
ob.conditional_formatting.add(f'A5:F{OB_LAST}', FormulaRule(formula=['$H5>0'], fill=BUY_FILL))
ob.conditional_formatting.add(f'H5:J{OB_LAST}', FormulaRule(formula=['$H5>0'], fill=BUY_FILL))
ob.freeze_panes = 'B5'

# ------------------------------------------------------------------ Read me totals
tot = [
    ('Parts per board (placed)', f'=BOM!G{tr}'),
    ('BOM lines still to buy', f'=BOM!L{tr}+\'Off-board\'!H{tr2}+COUNTIF(\'Port options\'!F{opt_first}:F{opt_last},">0")'),
    ('Cost of parts to buy (€)', f'=BOM!R{tr}+\'Off-board\'!L{tr2}'),
    ('Note', 'Cost counts only lines where you entered a unit price.'),
]
for i, (a, f) in enumerate(tot):
    cell(rm, r0 + 1 + i, 2, a, bold=True)
    fmt = EUR if '€' in a else (QTY if i < 2 else None)
    cell(rm, r0 + 1 + i, 3, f, fmt=fmt, align=CENTER if i < 3 else WRAP, bold=i < 3)

for ws in wb.worksheets:
    ws.sheet_view.zoomScale = 100
    ws.page_setup.orientation = 'landscape'
    ws.page_setup.fitToWidth = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.fitToHeight = 0

wb.save(OUT)
print('saved', OUT, 'refs', len(refs), 'lines', len(LINE_ORDER))
