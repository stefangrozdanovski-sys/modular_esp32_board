#!/bin/bash
# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
# zoom.sh <pcb> <out.png> <u0> <v0> <u1> <v1>  (board coords, origin 100,100)
PCB=$1; OUT=$2
kicad-cli pcb export svg --exclude-drawing-sheet --page-size-mode 2 -l F.Cu,B.Cu,F.SilkS,Edge.Cuts -o /tmp/z.svg $PCB >/dev/null 2>&1
python3 - "$@" <<'PY'
import sys,re
pcb,out,u0,v0,u1,v1=sys.argv[1],sys.argv[2],*map(float,sys.argv[3:7])
s=open('/tmp/z.svg').read()
vb=re.search(r'viewBox="([-\d. ]+)"',s).group(1).split()
x,y,w,h=map(float,vb)
wa=re.search(r'width="([\d.]+)mm"',s); 
# svg units: assume mm with viewBox in mm
s=re.sub(r'viewBox="[^"]+"',f'viewBox="{u0+0.274} {v0+21.09} {u1-u0} {v1-v0}"',s,1)
s=re.sub(r'width="[\d.]+mm"',f'width="{u1-u0}mm"',s,1)
s=re.sub(r'height="[\d.]+mm"',f'height="{v1-v0}mm"',s,1)
open('/tmp/z2.svg','w').write(s)
print(vb)
PY
rsvg-convert -b white -w 1400 /tmp/z2.svg -o $OUT
