
# SmartSplit Thermostat (HACS)

**One thermostat per room, one card to rule them all** — HEAT / COOL / DRY / OFF on a single UI, with adaptive baseline, configurable thresholds and boosts, optional autotune, window handling, humidity-driven DRY, and a watchdog for stubborn ACs (Tuya, GREE, etc.).

Repo: https://github.com/LaloX888/HA_Adaptive_Thermostat

## Features
- Single **proxy climate** entity per room (UI thermostat): modes **heat/cool/dry/off**, target °C.
- Controls any existing **`climate.*`** device (Tuya, GREE...). Uses `set_hvac_mode` + `set_temperature`.
- **Configurable thresholds**:
  - HEAT on/off delta (e.g. on at `target - 0.2`, release at `target - 0.0`)
  - COOL on/off delta (e.g. on at `target + 0.2`, release at `target + 0.0`)
  - **Up/Down boost** (±°C from baseline)
- **Baselines**: separate for HEAT and COOL, editable in Options.
- **Autotune** (optional): nudges baseline by ±0.5 °C if 2h trend shows bias beyond deadband.
- **DRY**: humidity target with ± band; turns DRY on/off (no setpoint fiddling).
- **Window-open** (optional): stores previous mode → OFF while open → auto-restore after 5 min closed.
- **Watchdog** (optional): retries if AC ignores a setpoint (off→on→set).
- **Rate limit** can be disabled (default 0/0 min).

## Installation (HACS)
1. HACS → **Custom repositories** → Add:
   - URL: `https://github.com/LaloX888/HA_Adaptive_Thermostat`
   - Category: **Integration**
2. Install **SmartSplit Thermostat**.
3. Restart Home Assistant.

## Setup
- Settings → Devices & Services → **Add Integration** → **SmartSplit Thermostat**
- Fill per room:
  - **AC entity**: the actual device to control (`climate.*`)
  - **Temperature sensor** (`sensor.*`)
  - *(Optional)* **Humidity sensor** (`sensor.*`) for DRY
  - *(Optional)* **Window sensor** (`binary_sensor.*`)
  - **Initial target** (°C)

Use the created **climate** entity in a Thermostat card. Switch modes (heat/cool/dry/off) and set a target temperature.

## Options (per room)
- **HEAT**: on/off delta
- **COOL**: on/off delta
- **Up / Down boost** (°C)
- **Baseline (heat/cool)**
- **Autotune**: enabled, deadband, step, 2h window (approx), min gap hours
- **DRY**: enabled, RH target, ±band
- **Watchdog**: enabled
- **Rate limit**: day/night minutes (0 = disabled)

## Notes
- DRY mode: many ACs ignore setpoint in DRY; we only toggle DRY/Off based on RH.
- Window handling: keeps things sane when venting.
- Works with Tuya, GREE and most other climate integrations exposing `set_hvac_mode`/`set_temperature`.

## Roadmap
- Recorder-based moving average for true 2h trend
- Multi-room grouping / scheduler
- Export/import presets
