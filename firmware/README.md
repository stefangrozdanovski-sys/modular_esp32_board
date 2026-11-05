# ESP32 Modular Base v2.0: ESPHome firmware

ESPHome packages for the ESP32 Modular Base v2.0, one package per port job, plus three example devices.

> **Status:** every example passes `esphome config` on ESPHome 2026.10.2. The hardware has not been built yet, so nothing here has run on a real board.

## Quick start

1. Install ESPHome 2026.10.2 or newer (`pip install esphome`), or use the Home Assistant ESPHome add-on.
2. Copy `secrets.example.yaml` to `secrets.yaml` **in this folder** (next to `base.yaml`) and fill it in. Make the API key with `openssl rand -base64 32`. It encrypts the Home Assistant API and OTA updates, so there is no separate OTA password. `secrets.yaml` is gitignored.
3. Copy an example from `examples/` (or start a new file there), then edit it.
4. Check it: `esphome config examples/my-device.yaml`
5. First flash over USB (CH340C, auto-reset): `esphome run examples/my-device.yaml`. After that, flash over Wi-Fi (OTA).

New board? Flash `examples/test-board.yaml` first and go through page 13 of the [assembly guide](../hardware/docs/assembly_guide.pdf). It needs no secrets.

Home Assistant ESPHome add-on: copy the whole `firmware/` folder into `/config/esphome/` so the `../base.yaml` and `../packages/` paths still work. Put `secrets.yaml` next to `base.yaml`.

## How to use it

**Pick the job → fit the parts from the recipe → include the package with the port pin.**

```yaml
substitutions:
  device_name: boiler-room      # hostname: lowercase, digits, "-"
  friendly_name: Boiler room

packages:
  base: !include ../base.yaml
  pump_p1: !include
    file: ../packages/relay.yaml
    vars: {id: pump_p1, name: Pump, pin: "${p1_a}"}
  flow_temp_p3: !include
    file: ../packages/ntc.yaml
    vars: {id: flow_temp_p3, name: Flow temperature, pin: "${p3_b}"}
```

- `base.yaml` sets up the board: `esp32dev`, 4 MB, Wi-Fi with fallback AP, API, OTA, logger, status LED (GPIO2), BOOT button (GPIO0), restart button, Wi-Fi signal and uptime. It also defines the pin names below as substitutions.
- Every package takes `vars:`. `id`, `name` and `pin` are needed (some packages take fewer, see the table); the rest have defaults, listed at the top of each package file.
- Every ID inside a package comes from your `id` (for example `ntc_p2`, `ntc_p2_v`, `ntc_p2_r`), so the same package can be used on several ports. Give each one a different `id` (lowercase, digits, `_`).
- The pin names (`${p1_a}` …) from `base.yaml` resolve inside `vars:` (checked on ESPHome 2026.10.2). Always quote them: `pin: "${p1_a}"`. A plain GPIO works too: `pin: GPIO25`.
- Framework: ESP-IDF, the ESPHome default. No package needs Arduino.

## Pin names (from `base.yaml`)

Connector: 1 GND, 2 VP, 3 A, 4 B. A has 330 R in series, B has 1 k.

| Port | A | B | B limits |
|---|---|---|---|
| P1 | `${p1_a}` GPIO25 | `${p1_b}` GPIO36 | input-only, no internal pull-up, **no pulse counting** (errata) |
| P2 | `${p2_a}` GPIO26 | `${p2_b}` GPIO39 | input-only, no internal pull-up, **no pulse counting** (errata) |
| P3 | `${p3_a}` GPIO27 | `${p3_b}` GPIO34 | input-only, ADC1 |
| P4 | `${p4_a}` GPIO13 | `${p4_b}` GPIO35 | input-only, ADC1 |
| P5 | `${p5_a}` GPIO4 | `${p5_b}` GPIO32 | bidirectional, ADC1 |
| P6 | `${p6_a}` GPIO18 | `${p6_b}` GPIO33 | bidirectional, ADC1 |
| UART | TX `${uart_tx}` GPIO17 | RX `${uart_rx}` GPIO16 | VP 5 V, RX through 10 k / 22 k divider |
| I2C | SDA `${i2c_sda}` GPIO21 | SCL `${i2c_scl}` GPIO22 | 4.7 k pull-ups fitted |
| OUT | `${out_pin}` GPIO23 | – | AO3400A low-side, off at boot, about 2 A / 24 V, PWM-capable |
| J902 (not fitted) | `${spare_19}` GPIO19, `${spare_14}` GPIO14, `${spare_5}` GPIO5 | | GPIO14 and GPIO5 output PWM at boot: **use them as inputs only** |

Used by the board: GPIO0 BOOT button, GPIO1/GPIO3 USB serial (CH340C), GPIO2 status LED.

## Packages

| Package | Job | Pins | Fit (on top of defaults) | Needed vars | Optional vars (default) |
|---|---|---|---|---|---|
| `relay.yaml` | Relay module | A | low trigger: nothing. High trigger: RAD 10 k | id, name, pin | `inverted` ("true" = low trigger; "false" for high trigger), `restore_mode` (ALWAYS_OFF) |
| `dry_contact.yaml` | Button / dry contact to GND | A | nothing (internal pull-up); long cable: RAU 10 k | id, name, pin | `device_class` (none), `debounce` (50ms) |
| `ds18b20.yaml` | DS18B20 1-Wire | A, VP 3V3 | RAU 4.7 k | id, name, pin | `update_interval` (60s) |
| `ntc.yaml` | NTC 10 k B3950 to GND | B | RBU 10 k 1 %, CB 100 nF | id, name, pin | `b_constant` (3950), `update_interval` (60s) |
| `analog.yaml` | 0–3.3 V signal | B | CB 100 nF | id, name, pin | `scale` (1.0), `unit` (V), `update_interval` (10s) |
| `pulse_flow.yaml` | Flow sensor → L/min + total L | B on **P3–P6 only** (5 V output) or any A (open collector) | B: RB 10 k (replaces 1 k), RBD 22 k, CB 1 nF, VP 5V. A: RAU 10 k, VP 5V | id, name, pin | `pulses_per_litre` (450, **placeholder**), `update_interval` (60s) |
| `pzem.yaml` | PZEM-004T v3 energy meter | UART port only | nothing, VP 5V | id, name | `address` (1), `update_interval` (10s) |
| `rs485_modbus.yaml` | RS485 Modbus RTU master | UART port + DE/RE on P5 B or P6 B | VP 5V; 3.3 V module: remove R706 | id, de_pin | `address` (1), `baud_rate` (9600), `parity` (NONE), `update_interval` (30s) |
| `i2c.yaml` | I2C bus (include once) | I2C port only | nothing | – | `frequency` (100kHz) |
| `i2c_bme280.yaml` | BME280 (needs `i2c.yaml`) | I2C port | nothing | id, name | `address` (0x76), `update_interval` (60s) |
| `out_pwm.yaml` | PWM fan on OUT | OUT only | nothing | id, name | `frequency` (1000Hz), `min_power` (0.0) |
| `out_switch.yaml` | On/off load on OUT (SSR, LED, buzzer, valve) | OUT only | nothing | id, name | `restore_mode` (ALWAYS_OFF) |

Full parts list per job: "Port recipes" in the [main README](../README.md#port-recipes) and page 13+ of the assembly guide. Port n uses parts Rn01–Rn06 and Cn01 (example: RBU on P3 is R305).

### Limits to know

- **P1 B (GPIO36) and P2 B (GPIO39): never `pulse_counter`.** ESP32 errata: false edges while Wi-Fi is active. ESPHome does not check this, so `pulse_flow` on these pins would pass `esphome config` and count wrong. Use them for NTC or analog.
- **B pins on P1–P4 are input-only:** never relay, DE/RE or anything that drives.
- **Dry contacts go on A.** The B pins of P1–P4 have no internal pull-up.
- **One UART job per board:** `pzem` or `rs485_modbus`, not both.
- **`pulse_flow` placeholder:** `pulses_per_litre` is 450 (F = 7.5 × Q in L/min, a common hall flow sensor). The sensor model is not chosen yet. Set the value from its datasheet, then check with a bucket. The total counts from boot; Home Assistant handles the reset (`total_increasing`).
- **DS18B20:** one sensor per package without an address. For more probes on the same port, add them in your device config with `one_wire_id: <id>_bus` and the address shown in the boot log.
- **RS485 auto-direction modules** (no DE/RE pin) do not fit `rs485_modbus.yaml`: use `uart` + `modbus` without `flow_control_pin` in your device config. Add registers with `platform: modbus_controller` and `modbus_controller_id: <id>` (example at the top of the package).
- **OUT:** low-side switch. Load between V+ and OUT, supply negative to GND. For a dimmable LED strip, use `out_pwm.yaml`'s output (`<id>_pwm`) with `light: monochromatic`, or copy the `output:` block.
- **I2C:** include `i2c.yaml` once, then the sensor packages. Two BME280s need different addresses (0x76 / 0x77).

### Flow sensor factors

Hall flow sensors output F (Hz) = k × Q (L/min), so `pulses_per_litre` = 60 × k. Set it per sensor: each `pulse_flow` instance has its own `pulses_per_litre`, so one board can mix models.

| Sensor | k (typical) | `pulses_per_litre` |
|---|---|---|
| YF-S201 (1/2") | 7.5 | 450 |
| YF-B1 (1/2" brass) | 11 | 660 |
| FS300A (3/4") | 5.5 | 330 |
| FS400A (1") | 4.8 | 288 |
| YF-S401 (small, 1–5 L/min) | 98 | 5880 |

These are typical values from seller datasheets, and units vary between batches. Use your sensor's datasheet, then calibrate: run a known volume (e.g. 10 L into a bucket) and set `pulses_per_litre` = counted pulses ÷ litres.

## Examples

| File | What | Ports used |
|---|---|---|
| `examples/test-board.yaml` | Bring-up test (assembly guide p. 13). AP `modbase-test`, web page at 192.168.4.1. No secrets | all A pins, UART TX, OUT |
| `examples/energy-relay.yaml` | PZEM-004T, relay, tank NTC, water flow | UART, P1 A, P2 B, P3 B |
| `examples/greenhouse.yaml` | BME280 air, DS18B20 soil, PWM vent fan | I2C, P4 A, OUT |

## Licence

MIT, © 2026 stefangrozdanovski-sys. See [LICENSES/MIT.txt](../LICENSES/MIT.txt).
