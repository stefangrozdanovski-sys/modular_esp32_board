#!/bin/bash
# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
# export.sh <project dir> : Gerbers + drill (+ zip), schematic PDF, position file
set -e
P="$1"; PCB="$P/esp32-modular.kicad_pcb"; G="$P/fabrication/gerbers"
rm -rf "$G"; mkdir -p "$G"
kicad-cli pcb export gerbers --no-x2 --subtract-soldermask \
  -l F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts -o "$G/" "$PCB" >/dev/null
kicad-cli pcb export drill --format excellon --excellon-units mm --generate-map --map-format gerberx2 \
  --excellon-separate-th -o "$G/" "$PCB" >/dev/null 2>&1 || \
kicad-cli pcb export drill --format excellon --excellon-units mm --generate-map --map-format gerberx2 -o "$G/" "$PCB" >/dev/null
kicad-cli pcb export pos --side both --format csv --units mm --exclude-dnp -o "$P/fabrication/positions.csv" "$PCB" >/dev/null 2>&1 || true
kicad-cli sch export pdf -o "$P/docs/schematic.pdf" "$P/esp32-modular.kicad_sch" >/dev/null
(cd "$G" && rm -f ../esp32-modular_gerbers.zip && zip -q ../esp32-modular_gerbers.zip *)
ls "$G"
