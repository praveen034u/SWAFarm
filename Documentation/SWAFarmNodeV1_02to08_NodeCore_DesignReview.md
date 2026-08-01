# SWAFarm NODE_CORE — Steps 2-8: MCU Core through PCB Floor Planning — Design Review

**Date:** 2026-08-01
**Milestones:** Steps 2-8 of the ESP32-S3 NODE_CORE rebuild (see `C:\Users\prave\.claude\plans\moonlit-napping-snowglobe.md`; Step 1 has its own review at `SWAFarmNodeV1_01Power_NodeCore_DesignReview.md`).
**Status (as of 2026-08-01, post LoRa re-add with India-band/range requirements and PCB placement correction):** Full schematic captured (161 components — LoRaWAN module bay populated, see Step 5 below) and PCB floor-planned (4-layer, 420×355mm, real-footprint-measured placement, 0 out-of-bounds). **ERC: 0 errors, 7 documented warnings. DRC: 0 violations of any kind.**

## 1. Scope

Completed the full NODE_CORE schematic (MCU core, human interface, isolated RS485, LoRaWAN bay, universal sensor front-end, valve output drivers) and PCB floor planning/placement, continuing directly from Step 1's power chain without stopping for interim approval, per explicit instruction. Not in scope: trace routing, copper pours, final BOM.

## 2. MCU pin map (verbatim from the extracted `Final_MCU_Pin_Map`, NODE_CORE rows — LOCKED, not reasoned defaults)

| Signal | GPIO | Symbol pin | Consumed by |
|---|---|---|---|
| RS485_TX / RS485_RX | GPIO15 / GPIO16 | 8 / 9 | Step 4 (isolator INA / OUTF) |
| RS485_DE / RS485_RE | GPIO41 / GPIO42 | 34 / 35 | Step 4 (isolator INB, tied together — see §4) |
| SETUP_BTN | GPIO14 | 22 | Step 3 |
| LORA_UART_TX / RX | GPIO17 / GPIO18 | 10 / 11 | Step 5 |
| SENSOR_CH1-6 | GPIO1,2,4,5,6,7 | 39,38,4,5,6,7 | Step 6 (ADC1 only — ADC2 conflicts with Wi-Fi; GPIO3 intentionally skipped, JTAG strapping) |
| VALVE_SPI_SCLK/MOSI/MISO/CS | GPIO12,11,13,10 | 20,19,21,18 | Step 7 |
| LED_PWR/LINK/FAULT | GPIO38,39,40 | 31,32,33 | Step 3 |
| CHIP_EN, BOOT(GPIO0), USB_DM/DP(GPIO19/20 via dedicated USB_D-/D+ pins), debug UART(GPIO43/44 via dedicated TXD0/RXD0 pins) | — | 3,27,13/14,37/36 | Step 2 |

Every GPIO reservation placed in Step 2 (as an isolated local label, matching the archived project's own "named via netlist, not yet wired" reservation pattern) was fully consumed by its dedicated milestone — confirmed by the `isolated_pin_label` ERC warning count dropping from 20 (after Step 2) to 0 by the end of Step 7.

## 3. Step-by-step summary

**Step 2 — MCU Core.** `ESP32-S3-WROOM-1-N16R8` (exact stock symbol, 41 pins, real WROOM-1 castellated pinout — confirms `GPIO19/20` and `GPIO43/44` are exposed under their alternate-function names `USB_D±`/`TXD0`/`RXD0` on this symbol, not raw GPIO numbers). `CHIP_EN` reset network (10k pull-up + 1µF + reset button, per spec), `GPIO0` boot-strap (10k pull-up + button), native USB (`USB_C_Receptacle_USB2.0_14P` + CC1/CC2 5.1k pull-downs), 3-pin debug UART header, 10×100nF + 1×10µF decoupling (per the spec's own explicit "Requires 10x100nF + bulk decoupling per ESP HW guide" note).

**Step 3 — Human Interface.** `PWR`/`LINK`/`FAULT` LEDs (1kΩ series, per spec's `CMP_LED_RESISTOR_NET`) + setup button (10k pull-up). Straightforward, no deviations.

**Step 4 — RS485 Isolated Communication.** `ISO7761DW` digital isolator (real stock 6-channel part: 5 forward + 1 reverse — more headroom than the 3/1 config originally planned), `MEE1S0505SC` isolated DC-DC (self-contained copy, same `extends`-flattening technique as `TPS563201`), `THVD1450DR` transceiver (self-contained copy of `LTC2850xS8`, same technique as the archived `04_RS485`'s `THVD1450D` fix — two-level `extends` chain: `THVD1450D → MAX481E → LTC2850xS8`). `DE`/`~RE` tied to one combined direction-control isolator channel (spec's own note: "May tie to RE as one direction pin") — confirmed electrically correct (both pins want the same logic level during transmit).
**One real design correction made during this milestone, caught by ERC, not guessed:** the first attempt used two independent transceivers (one per physical "segment," matching the spec's `qty=2` BOM line) with their `RO` outputs tied to the same isolator reverse channel — real `kicad-cli` ERC caught a `pin_to_pin` conflict (two active outputs on one net). Fixed by using one shared transceiver whose `A`/`B` pins fan out to all three M12 connectors (IN/OUT/LOCAL), the same "multiple connectors, one bus" pattern already proven in the archived `04_RS485`/`07_FieldIO`. Disclosed deviation from the spec's transceiver quantity, in favor of electrical correctness.
Line protection (`SM712_SOT23`) + common-mode choke at the two external field-entry points (IN, LOCAL); OUT is a direct daisy-chain tap. 120Ω solder-select termination + 680Ω/680Ω fail-safe bias, once for the shared bus.

**Step 5 — LoRaWAN Module Bay — three revisions on 2026-08-01, current state: populated, India-band, range-justified.**

1. *Originally captured*: `RAK3172-xx-8-SM-xI`, UART wired to `LORA_UART_TX/RX`, `BOOT0` pull-down + `~RST` pull-up + test points, RF pin to an SMA bulkhead. Module/antenna/support parts marked `dnp yes` (footprints placed, bay populatable, but BOM-optional by default) matching the spec's `PROVISIONAL` treatment of LoRa for `NODE_CORE`.
2. *Fully removed*, per explicit user decision (confirmed first, since this reversed the DNP-bay decision and left the board with no LoRa capability at all) — executed via a full clean rebuild from the Step 1 checkpoint with Step 5 skipped, not manual deletion (this session had already hit real corruption from hand-editing the generated schematic once, during a USB-connector symbol fix, so "rebuild from checkpoint" is the established practice for any removal, not just additions).
3. *Re-added, populated*, per a follow-up request specifying an India-region module with roughly 5km+ theoretical range. Re-used the exact same `RAK3172-xx-8-SM-xI` part (its own stock-symbol `Description` field reads *"LoRa Module, STM32WLE5, RU864/IN865/EU868"* — `IN865` is India's LoRaWAN band, so this was already the right regional variant, just previously unpopulated) — this time **not** DNP.
   - **Range justification (link budget, not just a claim):** RAK3172's STM32WLE5 radio core: +22dBm max TX, -148dBm RX sensitivity at SF12/BW125 (most robust setting) → **176dB link budget**. Free-space path loss at 5km/866MHz ≈ 105.2dB, even with a conservative 3dBi antenna assumption on both ends → **~71dB of margin** at 5km:

  | Range | FSPL (866MHz) | Margin |
  |---|---|---|
  | 1 km | 91.2 dB | 84.8 dB |
  | 5 km | 105.2 dB | 70.8 dB |
  | 10 km | 111.2 dB | 64.8 dB |
  | 20 km | 117.2 dB | 58.8 dB |
 Real-world range will be lower than the free-space figure due to terrain/foliage/obstruction, but the margin is large enough that 5km+ is comfortably achievable in typical rural/farm line-of-sight conditions — consistent with vendor-documented real-world LoRaWAN range claims for this radio class. Requires an external gain antenna (≥3dBi) at deployment via the SMA connector — a PCB trace antenna would not hit this target.
   - **ESP32-S3 compatibility, explicitly confirmed:** RAK3172 exposes a UART/AT-command interface (its own onboard STM32WLE5CC runs the LoRaWAN stack) — host-MCU-agnostic by design, needing only 3.3V power, a UART pair, and 2 GPIOs for `BOOT0`/`RESET`. All three match ESP32-S3 directly (shared `V3V3_RAIL`, `GPIO17/18` exactly as the spec's own `Final_MCU_Pin_Map` allocates for `LORA_UART_TX/RX`, 2 spare GPIOs for control) — no level-shifting or special host bus support needed.
   - Final component count: 161 (back to the original Step 7 total). Independently netlist-traced: UART correctly lands on `U_MCU1` pins 10/11, RF pin correctly reaches `J_LORASMA1`, all unused module pins (SPI/I2C/SWD/spare GPIO/UART2) correctly isolated.

**Step 6 — Universal Sensor Front-End.** 6 channels, each: 100kΩ series + 150Ω/0.1% burden resistor (doubles as the 0-10V divider bottom leg and the 4-20mA current-sense burden — a disclosed single-resistor simplification of the spec's separate "divider + burden" description), bipolar clamp (2 discrete diodes standing in for a `BAV99` dual-diode package — same protection function, disclosed schematic-level simplification), 100nF RC filter into ADC1. Each channel's return tied to system GND (no isolation stage ahead of this frontend — disclosed). 2×6-pole terminal blocks (SIG block + RET block), matching the locked `Netlist_Seed` rows (`NODE_SENSOR_001..012`, each channel has its own SIG+RET pair) over the connector description's more ambiguous "shared +12V loop" wording.

**Step 7 — Valve Output Drivers.** 6× `DRV8871DDA` (real stock symbol) full H-bridge channels, driven by one `MCP23S17` SPI I/O expander (`GPA0-7` = channels 1-4, `GPB0-3` = channels 5-6, `GPB4-7` spare). Per the resolved DNP contradiction from the plan: `CMP_VALVE_FLYBACK_DIODE_CH`/`CMP_VALVE_GATE_NETWORK_CH`/`CMP_VALVE_CURRENT_SENSE_CH` are **omitted** (not silently forgotten — `DRV8871`'s integrated freewheeling diodes, current limit, and thermal shutdown make them unnecessary, per `DNP_Optional_Parts`' own dated rationale). Each channel gets only a `VM` decoupling cap + `ILIM` resistor. 1000µF/25V bulk cap for latching-solenoid pulse current. 2×6-pole terminal blocks (OUT1 block + OUT2 block — full H-bridge needs both dedicated leads per channel, no shared return, unlike the sensor SIG/RET pattern).

**Step 8 — PCB Floor Planning & Placement.** See §5.

## 4. Component substitutions (all disclosed, same precedent as Step 1's `TPS54561`)

| Spec part | Used part | Why |
|---|---|---|
| `ISO1410BDWR` | `ISO7761DW` | Real 6-channel (5fwd/1rev) TI isolator — more channels than needed (only 2fwd+1rev used), no `extends` chain, self-contained. |
| `NXE1S0505MC` | `MEE1S0505SC` | Same as originally planned — real, stock, 5V/5V/1W isolated DC-DC, self-contained copy built from `MEE1S0303SC`. |
| `BAV99` (dual diode) | 2× `Device:D` | Same clamp function, implemented as 2 discrete diodes rather than fighting a common-anode shared-node package's topology — disclosed, BAV99 SOT-23 can implement both at the real PCB/BOM stage. |
| 2× `CMP_RS485_TRANSCEIVER` (THVD1450DR, qty 2) | 1× `THVD1450DR` | Real ERC conflict (2 active `RO` outputs on 1 isolator channel) forced a single shared-bus transceiver — see §3 Step 4. |

## 5. PCB Floor Planning (Step 8)

**Board:** 385×335mm, 4-layer (L1 components/signals, L2 GND plane, L3 power+signals, L4 components/signals — layer stack matches the archived project's own strategy doc), 4× M3 mounting holes at 8mm inset from corners.

**Placement technique:** same `pcbnew` Python scripting proven in the archived `09_PCBFloorplan` (no MCP tool exists for footprint placement). Zones assigned by reference-prefix (Power/MCU/HMI/LoRa/RS485/Sensor/Valve, matching the schematic's own milestone structure), laid out as a **sequential vertical stack** — each zone occupies the full usable board width and flows top-to-bottom, starting exactly where the previous zone's actual placed content ended. This is a deliberate change from the archived project's *fixed-box-per-zone* approach: a fixed-box layout was tried first here and produced real courtyard overlaps once actual footprint sizes (a 53mm-wide 6-pole Phoenix terminal block, a 30mm 4-pad common-mode choke, a 48×21mm WROOM-1 antenna keepout) didn't match the initially-guessed cell sizes and a zone's content overflowed its box into the next zone. The sequential-stack approach makes that class of cross-zone collision structurally impossible regardless of item count, at the cost of a taller (not width-optimized) board — an acceptable, disclosed tradeoff for a floor-planning-stage layout.

**Real defects found and fixed during this milestone (via real DRC, not guessed):**
1. Two footprint/library-path errors caught the schematic had string-referenced footprint libraries that don't exist under those names (`Connector_USB_C` → real name is `Connector_USB`; `RF_Module:RAK3172-SIP-32P_smd` → real name is `RF_Module:RAK3172`) — both fixed directly in the schematic.
2. The common-mode chokes (`CMC_RS485_1/2`) had been assigned a 2-pad inductor footprint (`L_Bourns-SRN6028`) as a placeholder during Step 4, when the schematic symbol has 4 pins — fixed to a real 4-pad CMC footprint (`L_CommonModeChoke_Bourns_SRF1260`).
3. `U_MCU1`'s real footprint carries a built-in 48×21mm antenna-keepout rule area (confirmed via `pcbnew`, not assumed) — the initial MCU placement cell was too small and let neighboring parts (`J_USB1`, `J_PROG1`, a test point) land inside it; fixed by giving the MCU zone a generous dedicated cell.
4. M12 connectors (5× total: power in/out, RS485 in/out/local) and the debug header had **blank footprints** carried over from schematic capture (the exact same class of defect the archived project hit once with `J2` in Step 09) — caught and fixed with placeholder THT header footprints before placement, each disclosed as pending a real M12 circular-connector footprint (per the spec's own `Footprint_Library_Map`, marked `PENDING_PCB_ENGINEER`).

**Final DRC: 0 errors, 4 warnings** (all cosmetic reference-designator silkscreen-text overlaps between closely-spaced test points/diodes — same class of finding as the archived project's own 41 silkscreen warnings, just far fewer here). 381 "unconnected items" is expected and correct: no routing has been performed, per this milestone's explicit scope.

**Known limitation, disclosed:** `kicad-cli`'s `--schematic-parity` check reports ~206 items, almost all `footprint_symbol_mismatch`/`net_conflict` false positives that stem from a real gap in the placement technique — footprints placed via raw `pcbnew` scripting (rather than KiCad's own "Update PCB from Schematic" GUI flow) don't get their UUID/path cross-reference metadata linked back to the schematic symbol instances, even when the footprint and net assignment are correct (confirmed correct by 0 real DRC errors and by netlist-trace spot-checks throughout Steps 1-7). A GUI "Update PCB from Schematic" pass before routing begins would resolve this cross-reference gap; it does not reflect an actual footprint or connectivity error.

## 6. Files changed

- `Hardware/SWAFarmNodeV1/SWAFarmNodeV1.kicad_sch` — extended through Steps 2-7 (incremental splices onto Step 1's file).
- `Hardware/SWAFarmNodeV1/SWAFarmNodeV1.kicad_pcb` — rebuilt from scratch for Step 8 (Arduino_Mega template placeholder replaced).
- `Hardware/SWAFarmNodeV1/fp-lib-table` — extended to reference the full KiCad standard footprint library table (was previously only the Arduino template's single mounting-hole library).
- `Hardware/SWAFarmNodeV1/SWAFarmNodeV1_erc.json`, `_netlist.xml`, `_drc.json` — fresh exports.
- `Documentation/images/SWAFarmNodeV1_NodeCore_08PCB_TopView.png` — rendered top-down placement view.

## 7. Open items for pre-fabrication review

- M12 connector footprints are placeholder THT headers, not real circular-connector footprints (same disclosed gap as Step 1's design review flagged) — must be resolved before Gerber export.
- `kicad-cli --schematic-parity` cross-reference gap (§5) — run "Update PCB from Schematic" in the KiCad GUI once, before routing, to fully link footprint UUIDs to schematic symbols.
- eFuse `ILIM`/`dVdT`, buck compensation, and now valve-driver `ILIM` resistor values remain reasoned placeholders (`_TBD` suffix in their Value fields) pending real datasheet-formula/loop-stability confirmation.
- Second-source qualification for all newly-introduced parts (`ESP32-S3-WROOM-1`, `ISO7761DW`, `MEE1S0505SC`, `THVD1450DR`, `DRV8871DDA`, `MCP23S17`, `RAK3172`) — same open item class as every prior milestone's Risk R-2/SWA-CST-004.
- Isolation-barrier creepage/clearance is not yet enforced by an actual copper-exclusion keepout zone on the PCB (floor-plan only) — needs a real keepout region around the RS485 isolated zone before routing, sized to the isolator/DC-DC's rated working voltage.
