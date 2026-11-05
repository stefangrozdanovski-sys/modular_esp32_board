# Changelog

## v2.0 (unreleased, untested)

- First public release of the ESP32 Modular Base v2.0 hardware: KiCad 7 project, generator scripts, Gerbers, schematic PDF, assembly guide, iBOM, BOM workbook and BOM app.
- 5 PCBs ordered from Seeed Fusion on 2026-10-14. Not yet assembled or tested.
- ESPHome firmware (`firmware/`): `base.yaml` (board setup and port pins as substitutions), 12 port-job packages (relay, dry_contact, ds18b20, ntc, analog, pulse_flow, pzem, rs485_modbus, i2c, i2c_bme280, out_pwm, out_switch) and 3 examples (test-board, energy-relay, greenhouse). Checked with `esphome config` on ESPHome 2026.10.2, not yet run on hardware. The `pulse_flow` factor (pulses per litre) is a placeholder until the flow sensor is chosen.
- Planned next: JLCPCB/PCBWay assembly files (`production/pcba/`), real photos and a test report.
