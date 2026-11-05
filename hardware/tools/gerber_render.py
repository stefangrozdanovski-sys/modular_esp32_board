#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
"""Photo-style render composited from the actual Gerber/drill files via gerbv.
usage: gerber_render.py <gerber_dir> <out_top.png> <out_bottom.png>"""
import sys, os, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw

GD, OUT_T, OUT_B = sys.argv[1:4]
DPI = 600
import os as _o, sys as _s
_s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
import layout as _LY
X0, Y0, W, H = _LY.OX, -(_LY.OY + _LY.H), _LY.W, _LY.H     # board in gerber coords (mm, y up)
pre = os.path.join(GD, 'esp32-modular')
tmp = tempfile.mkdtemp(dir=os.path.dirname(os.path.abspath(__file__)))

def layer(fname, name):
    out = os.path.join(tmp, name + '.png')
    subprocess.run(['xvfb-run', '-a', 'gerbv', '-x', 'png', '-D', str(DPI), '-B', '0',
                    f'--origin={X0/25.4:.4f};{Y0/25.4:.4f}', f'--window_inch={W/25.4:.4f}x{H/25.4:.4f}',
                    '-b', '#000000', '-f', '#ffffffff', '-o', out, fname],
                   check=True, capture_output=True)
    a = np.asarray(Image.open(out).convert('L')) > 127
    return a

def board_mask(shape):
    h, w = shape
    im = Image.new('L', (w, h), 0)
    r = 2.0 / 25.4 * DPI
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=255)
    return np.asarray(im) > 127

def compose(cu, mask, silk, holes, flip=False):
    bm = board_mask(cu.shape)
    img = np.zeros(cu.shape + (4,), np.uint8)
    base = np.array([18, 82, 44, 255]); cu_under = np.array([34, 112, 60, 255])
    gold = np.array([214, 178, 92, 255]); white = np.array([240, 240, 235, 255])
    img[bm] = base
    img[bm & cu] = cu_under
    img[bm & mask] = np.array([150, 130, 90, 255])        # bare FR4 in mask openings
    img[bm & mask & cu] = gold
    img[bm & silk & ~mask] = white
    img[holes | ~bm] = np.array([0, 0, 0, 0])
    im = Image.fromarray(img, 'RGBA')
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    return bg.convert('RGB').resize((im.size[0] // 2, im.size[1] // 2), Image.LANCZOS)

holes = layer(pre + '-PTH.drl', 'pth') | layer(pre + '-NPTH.drl', 'npth')
top = compose(layer(pre + '-F_Cu.gtl', 'fcu'), layer(pre + '-F_Mask.gts', 'fmask'),
              layer(pre + '-F_Silkscreen.gto', 'fsilk'), holes)
bot = compose(layer(pre + '-B_Cu.gbl', 'bcu'), layer(pre + '-B_Mask.gbs', 'bmask'),
              layer(pre + '-B_Silkscreen.gbo', 'bsilk'), holes, flip=True)
top.save(OUT_T); bot.save(OUT_B)
print('rendered', top.size)
