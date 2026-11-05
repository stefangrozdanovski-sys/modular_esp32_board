#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
"""Sync footprint values + schematic paths from a netlist without touching geometry."""
import sys, re, pcbnew
PCB, NET = sys.argv[1:3]
s = open(NET).read()
comps = {}
for m in re.finditer(r'\(comp \(ref "([^"]+)"\)\s*\(value "([^"]*)"\)\s*\(footprint "([^"]*)"\)(.*?)\(tstamps "([0-9a-f-]{36})"\)\)', s, re.S):
    comps[m.group(1)] = (m.group(2), m.group(3), m.group(5))
b = pcbnew.LoadBoard(PCB)
for f in b.GetFootprints():
    v, fp, u = comps[f.GetReference()]
    assert fp.split(':')[1] == str(f.GetFPID().GetLibItemName()), (f.GetReference(), fp)
    f.SetValue(v)
    f.SetPath(pcbnew.KIID_PATH('/' + u))
pcbnew.SaveBoard(PCB, b)
print('synced', len(comps))
