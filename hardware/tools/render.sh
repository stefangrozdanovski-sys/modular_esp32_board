#!/bin/bash
# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
# render.sh <pcb> <outprefix>  -> <outprefix>_top.png, <outprefix>_bot.png
PCB="$1"; OUT="$2"
kicad-cli pcb export svg --exclude-drawing-sheet --page-size-mode 2 \
  -l F.Cu,F.SilkS,F.Mask,Edge.Cuts,F.CrtYd -o "${OUT}_top.svg" "$PCB" >/dev/null 2>&1
kicad-cli pcb export svg --exclude-drawing-sheet --page-size-mode 2 \
  -l B.Cu,B.SilkS,Edge.Cuts --mirror -o "${OUT}_bot.svg" "$PCB" >/dev/null 2>&1
for s in top bot; do
  # white background
  sed -i 's/<svg /<svg style="background:white" /' "${OUT}_${s}.svg"
  rsvg-convert -b white -w 1600 "${OUT}_${s}.svg" -o "${OUT}_${s}.png"
done
ls -la "${OUT}"_*.png
