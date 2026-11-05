<!-- SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys -->
<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->
# PCBA files (JLCPCB / PCBWay)

> **Not ready to order yet.** Only CH340C (C84681) was checked live. Every other LCSC number below is an unverified candidate. The rotation corrections have not been checked in JLCPCB's placement preview. Do both before you pay.

| File | Use |
|---|---|
| `esp32-modular-v2.0-BOM-JLCPCB.csv` | JLCPCB BOM: Comment, Designator, Footprint, LCSC Part # |
| `esp32-modular-v2.0-CPL-JLCPCB.csv` | JLCPCB placement: Designator, Mid X, Mid Y, Layer, Rotation (JLCPCB corrections applied) |
| `esp32-modular-v2.0-BOM-PCBWay.csv` | PCBWay BOM: Qty, Designator, Manufacturer Part Number, Description, Package, Type |
| `esp32-modular-v2.0-CPL-PCBWay.csv` | PCBWay placement, KiCad rotations unchanged (PCBWay checks orientation themselves) |
| `esp32-modular-v2.0-THT-hand-solder.csv` | Through-hole parts left for you to solder |

The CPL lists the 54 fitted SMD parts, all on the top side. The files leave out the 38 empty option footprints, 9 solder jumpers (JP*), 4 mounting holes (H*), J902 (not fitted) and the 14 THT parts.

## Ordering at JLCPCB

1. Upload `hardware/fabrication/esp32-modular_gerbers.zip`: 2 layers, 1.6 mm, HASL lead-free or ENIG.
2. Turn on PCB Assembly, top side. Choose Standard PCBA if you want JLCPCB to do the THT parts too (see below). Otherwise Economic is fine.
3. Upload the JLCPCB BOM and CPL. Check that every line matches its LCSC part and is in stock.
4. **In the placement preview, check every part's rotation and pin 1** (see the list below). If one is wrong, fix it in `ROTATION` in `hardware/tools/pcba.py` and regenerate. Don't edit the CSV.
5. Solder the THT parts yourself (assembly guide step 5), or add them to the order.

PCBWay: upload the Gerbers and the PCBWay BOM and CPL. PCBWay sources the parts and confirms orientation by email before production.

## Module choice: ESP32-WROOM-32E-N4 (C701341)

The hand-build BOM uses the Ai-Thinker ESP-32S. A web search found no LCSC/JLCPCB listing for it. The ESP32-WROOM-32E-N4 is Espressif's current module and has the same 18 × 25.5 mm, 38-pad layout. Its flash pins (pads 17–22) are not connected on this board, so it is a drop-in. It also has 4 MB flash, and `board: esp32dev` works. Its JLCPCB class is reported as Extended, which adds the extended-part fee.

## LCSC verification

Checked = looked up live on jlcpcb.com / lcsc.com. Everything else is a **candidate**: the number came from my memory or a web search snippet, and package, value, stock and Basic/Extended status have not been confirmed.

| Line | Refs | LCSC | MPN | Package / value | Stock | Basic/Ext | Status |
|---|---|---|---|---|---|---|---|
| CH340C | U3 | C84681 | WCH CH340C | SOP-16 | 101,694 (JLCPCB), 100,341 (LCSC) | Extended | **Checked 2026-11-05**, JLCPCB part API + lcsc.com page |
| Module | U1 | C701341 | ESP32-WROOM-32E-N4 | module, 4 MB | ? | Extended (search snippet) | candidate |
| LDO | U2 | C6186 | AMS1117-3.3 | SOT-223 | ? | ? | candidate |
| USB ESD | U4 | C7519 | ST USBLC6-2SC6 | SOT-23-6 | ? | Extended (search snippet) | candidate |
| NPN | Q1 Q2 | C20526 | MMBT3904 | SOT-23 | ? | ? | candidate |
| MOSFET | Q901 | C20917 | AO3400A | SOT-23 | ? | ? | candidate |
| TVS | D1 | C113952 | SMAJ5.0A (MDD) | SMA, unidirectional | ? | ? | candidate: check it is not the CA (bidirectional) part |
| Schottky | D901 | C8678 | SS34 | SMA | ? | ? | candidate |
| PTC 1.1 A | F1 | C163516 | Littelfuse 1812L110PR | 1812, 1.1 A hold, 8 V | ? | ? | candidate: no 6 V 1.1 A 1812 part found, 8 V is fine |
| PTC 0.5 A | F101–F801 | C883122 | BHFUSE BSMD1206-050-6V | 1206, 0.5 A hold, 6 V | ? | ? | candidate: LCSC listing, JLCPCB stock unknown |
| 22 µF | C3 | C45783 | CL21A226MQQNNNE | 0805 | ? | ? | candidate |
| 10 µF | C2 C6 | C15850 | CL21A106KAYNNNE | 0805 | ? | ? | candidate |
| 1 µF | C7 | C28323 | CL21B105KBFNNNE | 0805 | ? | ? | candidate |
| 100 nF | C5 C8 | C49678 | CC0805KRX7R9BB104 | 0805 | ? | ? | candidate |
| 330 R | Rn01 (n=1–7) | C17630 | 0805W8F3300T5E | 0805 | ? | ? | candidate |
| 1 k | R10 R11 Rn04 (n=1–6) | C17513 | 0805W8F1001T5E | 0805 | ? | ? | candidate |
| 10 k | R1–R4 R704 | C17414 | 0805W8F1002T5E | 0805 | ? | ? | candidate |
| 100 R | R801 R804 R901 | C17408 | 0805W8F1000T5E | 0805 | ? | ? | candidate |
| 470 R | R5 | C17710 | 0805W8F4700T5E | 0805 | ? | ? | candidate |
| 4.7 k | R802 R805 | C17673 | 0805W8F4701T5E | 0805 | ? | ? | candidate |
| 22 k | R706 | C17560 | 0805W8F2202T5E | 0805 | ? | ? | candidate |
| 100 k | R902 | C149504 | 0805W8F1003T5E | 0805 | ? | ? | candidate |
| LED red | LED1 | C84256 | NationStar NCD0805R1 | 0805 | ? | Basic (search snippet) | candidate |
| LED yellow | LED2 | C2296 | KENTO KT-0805Y | 0805 | ? | ? | candidate |

Every SMD line has a candidate. None is known to be unavailable.

**To finish the check**, run this from a machine that can reach `cart.jlcpcb.com`:

```bash
python3 hardware/tools/pcba.py --verify production/pcba
```

It writes `lcsc_check.csv` with model, package, stock and Basic/Extended for every number. Compare the model and package with the table above, fix any wrong entry in `LCSC` in `pcba.py`, put the date and stock into `checked`, regenerate, and update this table.

## Rotation corrections (unconfirmed)

KiCad and JLCPCB use different zero orientations for some packages. `pcba.py` adds these corrections to the KiCad rotation for the JLCPCB CPL only:

| Package | Parts | Correction |
|---|---|---|
| SOT-223 | U2 | +180° |
| SOT-23-6 | U4 | +180° |
| SOT-23 | Q1 Q2 Q901 | +180° |
| SOIC-16 | U3 | +270° |
| SMA | D1 D901 | +180° |
| LED 0805 | LED1 LED2 | 0° (check the cathode side) |
| ESP32 module | U1 | 0° (no published value found) |
| 0805 R/C, 1206/1812 PTC | rest | 0° |

The values follow the community JLCPCB rotation tables (JLCKicadTools `cpl_rotations_db.csv` and KiBot's JLCPCB list). I took them from memory and did not re-read those tables. I also can't open JLCPCB's placement preview, so **none of these is confirmed for this board.** Before ordering, check each package in the preview: pin 1 on the IC dot, diode bands toward +5V (D1) and V+ (D901), LED cathodes toward GND, module antenna over the board edge.

## THT parts

| Qty | Refs | Part |
|---|---|---|
| 9 | J1, J101–J801 | JST XH 4P vertical |
| 1 | J901 | JST XH 3P vertical |
| 2 | SW1, SW2 | 6 × 6 mm tactile switch |
| 2 | C1, C4 | 100 µF 10 V radial 6.3 mm |

The default is to hand-solder them after assembly (51 joints, assembly guide step 5).

JLCPCB can also hand-solder THT parts. That needs Standard PCBA rather than Economic and adds a THT setup charge plus a per-joint fee, so expect a noticeably higher quote for a small batch. The parts need LCSC numbers too; they are not in the BOM. Check the current rates in the JLCPCB quote, not here. I did not check them.

## The hand-solder pads

The footprints keep their enlarged hand-solder pads (`*_HandSolder`, the extended module pads). Machine assembly works with them; paste follows the pads. Nothing on the board or footprints was changed for PCBA.

## Regenerating

```bash
bash hardware/tools/export.sh hardware
```

This also rebuilds the Gerbers and schematic PDF. For the PCBA files alone:

```bash
kicad-cli pcb export pos --side both --format csv --units mm --smd-only -o hardware/fabrication/positions.csv hardware/esp32-modular.kicad_pcb
```

```bash
python3 hardware/tools/pcba.py hardware/fabrication/positions.csv production/pcba
```

This needs KiCad 7 (`kicad-cli`; Ubuntu 24.04 `apt install kicad` gives 7.0.11) and Python 3, with no other packages. `pcba.py` stops if the position file and `parts.py` disagree.
