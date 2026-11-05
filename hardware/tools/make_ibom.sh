#!/bin/bash
# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
# make_ibom.sh <project dir> <netlist> : interactive assembly guide -> docs/ibom_assembly.html
set -e
P="$1"; NET="$2"; T=$(mktemp -d)
python3 - "$P/esp32-modular.kicad_pcb" "$T/esp32-modular.kicad_pcb" <<'PY'
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
for f in b.GetFootprints():
    f.Value().SetVisible(False)                       # values are in the BOM table; keep the drawing readable
    for g in f.GraphicalItems():
        if g.GetClass() == 'FP_TEXT' and g.GetLayer() == pcbnew.F_Fab and '${REFERENCE}' in g.GetText():
            small = f.GetReference()[0] in 'RCFL' or f.GetReference().startswith('Q')
            s = pcbnew.FromMM(0.5 if small else 0.9)
            g.SetTextSize(pcbnew.VECTOR2I(s, s)); g.SetTextThickness(pcbnew.FromMM(0.08 if small else 0.13))
pcbnew.SaveBoard(sys.argv[2], b)
PY
cp "$NET" "$T/esp32-modular.net"
generate_interactive_bom "$T/esp32-modular.kicad_pcb" --no-browser --dest-dir "$P/docs" --name-format ibom_assembly \
  --extra-data-file "$T/esp32-modular.net" --dnp-field kicad_dnp --no-blacklist-virtual --blacklist "H*,JP*" \
  --show-fields "Value,Footprint" --group-fields "Value,Footprint" --checkboxes "Sourced,Placed" --mark-when-checked Placed \
  --highlight-pin1 selected --bom-view left-right --layer-view F --show-fabrication --show-silkscreen \
  --include-tracks --include-nets --sort-order "U,Q,D,F,C,R,LED,SW,J,~" >/dev/null 2>&1
# DNP footprints drawn with an outline by default
sed -i 's/initBooleanSetting("dnpOutline", false/initBooleanSetting("dnpOutline", true/' "$P/docs/ibom_assembly.html"
rm -rf "$T"; ls -la "$P/docs/ibom_assembly.html"
