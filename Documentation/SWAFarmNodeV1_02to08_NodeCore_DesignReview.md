# SWAFarm NODE_CORE — Steps 2-8: MCU Core through PCB Floor Planning — Design Review

**Date:** 2026-08-01
**Milestones:** Steps 2-8 of the ESP32-S3 NODE_CORE rebuild (see `C:\Users\prave\.claude\plans\moonlit-napping-snowglobe.md`; Step 1 has its own review at `SWAFarmNodeV1_01Power_NodeCore_DesignReview.md`).
**Status (as of 2026-08-01, post 11-category design audit and 2 critical-finding fixes — see §6):** Full schematic captured (181 components — LoRaWAN module bay populated per Step 5; valve rail and sensor front-end corrected per §6) and PCB floor-planned (4-layer, 420×361.6mm, real-footprint-measured placement, 0 out-of-bounds). **ERC: 0 errors, 7 documented warnings (unchanged by the audit fixes). DRC: 0 violations of any kind.**

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

**Step 6 — Universal Sensor Front-End.** 6 channels, each: series + burden resistor front end into ADC1, bipolar clamp (2 discrete diodes standing in for a `BAV99` dual-diode package — same protection function, disclosed schematic-level simplification), 100nF RC filter. Each channel's return tied to system GND (no isolation stage ahead of this frontend — disclosed). 2×6-pole terminal blocks (SIG block + RET block), matching the locked `Netlist_Seed` rows (`NODE_SENSOR_001..012`, each channel has its own SIG+RET pair) over the connector description's more ambiguous "shared +12V loop" wording. **The original single-resistor divider/burden network here had a real math defect, found and fixed during the 2026-08-01 audit — see §6.2.**

**Step 7 — Valve Output Drivers.** 6× `DRV8871DDA` (real stock symbol) full H-bridge channels, driven by one `MCP23S17` SPI I/O expander (`GPA0-7` = channels 1-4, `GPB0-3` = channels 5-6, `GPB4-7` spare). Per the resolved DNP contradiction from the plan: `CMP_VALVE_FLYBACK_DIODE_CH`/`CMP_VALVE_GATE_NETWORK_CH`/`CMP_VALVE_CURRENT_SENSE_CH` are **omitted** (not silently forgotten — `DRV8871`'s integrated freewheeling diodes, current limit, and thermal shutdown make them unnecessary, per `DNP_Optional_Parts`' own dated rationale). Each channel gets only a `VM` decoupling cap + `ILIM` resistor. 1000µF/25V bulk cap for latching-solenoid pulse current. 2×6-pole terminal blocks (OUT1 block + OUT2 block — full H-bridge needs both dedicated leads per channel, no shared return, unlike the sensor SIG/RET pattern). **`VM` originally shared the eFuse's 2A-rated `V12_SW` rail with buck1 — a real overcurrent risk, found and fixed during the 2026-08-01 audit; now on its own `V12_VALVE` branch — see §6.1.**

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

## 6. 2026-08-01 design audit — 2 critical findings, both fixed

User-requested 11-category audit (datasheet verification, power rail audit, connectivity/net review, connector verification, pull-up/down check, protection audit, RF verification, test point review, BOM validation, peer design review, simulation) run against the schematic above, verified via real `kicad-cli` ERC/netlist-trace tooling rather than assertions. 2 real defects found; both fixed and re-verified (0 ERC errors/7 pre-existing documented warnings unchanged, 0 DRC violations, 0 out-of-bounds footprints).

### 6.1 Power rail audit — valve rail overcurrent risk (CRITICAL, fixed)

**Finding:** `V12_SW`, the `TPS26600PWP` eFuse's (`U1`) output — rated 2A by the silicon itself, not just an adjustable `ILIM` setting — fed both buck1 (`U2`, the 5V regulator) AND all 6 `DRV8871` valve drivers (`U_DRV1-6`), each individually rated up to 3.6A continuous / capable of ~2.5A+ pulses when driving latching solenoid valves. A single valve channel pulsing already exceeds the eFuse's 2A rating; this was a genuine architecture defect, not a resistor-value tuning issue (no `ILIM` resistor value can raise a 2A-silicon-limited part past its own rating).

**Fix:** gave the valve rail its own branch, independent of the eFuse:
- New net `V12_VALVE`, tapped from `V12_PROT` (the fused, TVS-protected, reverse-polarity-protected input rail) **upstream** of the eFuse — through a new dedicated fuse `F2` (Littelfuse 1812L-class PTC, ~4A hold current).
- `U_DRV1-6` pin 5 (`VM`), `C_VMDEC1-6` pin 1, and `C_VALVEBULK1` pin 1 moved from `V12_SW` to `V12_VALVE`.
- `F1` (input fuse) resized 1.5A → 5A — it was undersized even for a single valve pulse alone, before this fix existed.
- New `TP_VALVE_PWR1` test point on `V12_VALVE`, matching the existing `TP_12V_SW1` pattern; new `#FLG06` `PWR_FLAG` (required — `V12_VALVE` has no power-output-type pin driving it in ERC's strict sense, same requirement class as `#FLG01-05` on the other rails).

**Real defect caught by the user, not by this session's own checks:** the new flag was initially placed with a literal reference `FLAG6` rather than the `#FLG0n` convention the other 5 flags use — KiCad recognizes a `#`-prefixed reference as a power-flag symbol exempt from needing a board footprint; without it, the user's own "Update PCB from Schematic" run in the KiCad GUI correctly errored ("Cannot add FLAG6 (no footprint assigned)"). This is the same class of lesson as the GND-symbol `#PWR0n` convention already relied on elsewhere in this schematic — fixed by renaming to `#FLG06`, re-verified 0 ERC errors/7 warnings unchanged.

**Disclosed caveat, not yet enforced in hardware:** `F2`'s sizing assumes sequential (one-channel-at-a-time) valve actuation — standard practice for solenoid valve banks, and consistent with a single shared `MCP23S17` SPI expander driving all 6 channels. Simultaneous multi-valve firing is a firmware policy this hardware doesn't prevent by itself; if simultaneous operation is required, `F2` and its downstream wiring/connector gauge need resizing for the full multi-channel worst case.

Verified via netlist trace (`kicad-cli sch export netlist`): `V12_SW` now contains only `C_IN2`, `C_OUT1`, `R_EN1A1`, `TP_12V_SW1`, `U1`.15/16, `U2`.2 (the logic/buck chain). `V12_VALVE` contains `F2`.2, `TP_VALVE_PWR1`, `#FLG06`, `C_VALVEBULK1`.1, `U_DRV1-6`.5, `C_VMDEC1-6`.1 (the valve chain) — cleanly separated.

### 6.2 Datasheet + connectivity review — sensor front-end 0-10V divider math (CRITICAL, fixed)

**Finding:** the Step 6 front-end's `R_SER`(100kΩ)+`R_BURDEN`(150Ω) network was a single shared resistor pair serving both the 0-10V divider and the 4-20mA burden. By calculation: for 0-10V mode, `Vadc = Vin × 150/(100000+150) ≈ Vin × 0.0015` — a 10V input produced only **~15mV** at the ADC, far too small for usable resolution. Separately, for 4-20mA mode, having `R_SER` permanently in series with the current loop meant the loop's compliance voltage requirement became `I × (100150Ω)` — at 20mA, over **2000V**, physically impossible for any real 4-20mA transmitter. A single fixed passive network cannot serve both modes correctly (verified by circuit analysis, not assumption): 0-10V sensing needs a high-impedance divider (~100kΩ+ class) while 4-20mA sensing needs a low-impedance burden (~150Ω class) with no series resistance blocking the loop — the two requirements are mutually exclusive for one fixed network.

**Fix:** jumper-selectable dual network per channel, matching standard industrial universal-analog-input practice (verified correct in both modes by circuit analysis before implementing, using KiCad-stock, production-appropriate parts — 2.54mm pin headers + shorting jumpers, not a novel/hobby component):
- `R_SER` revalued 100k → 232k (now the divider's top leg), paired with new `R_VBOT` (100k, bottom leg): `10V × 100k/(232k+100k) ≈ 3.01V` at the ADC — within the ESP32-S3 ADC's safe input range with headroom.
- New `JP_VBYP` (2-pin jumper, in parallel with `R_SER`/232k): populate **only** for 4-20mA mode, shorting out the 232k resistor so loop current isn't blocked. Leave open for 0-10V mode.
- New `JP_IGND` (2-pin jumper, gates `R_BURDEN`'s GND return): populate **only** for 4-20mA mode, together with `JP_VBYP` — completes the 150Ω burden's circuit (0.6-3.0V for 4-20mA, unchanged/correct). Leave open for 0-10V mode, so the 150Ω burden doesn't sit permanently across a voltage-mode transmitter's output (would otherwise pull ~67mA at 10V, likely exceeding many transmitters' rated output current).
- **`JP_VBYP`/`JP_IGND` must be populated as a matched pair** — populating one without the other reintroduces one of the two original defects. A single mechanically-ganged DPDT switch or dual-row shorting shunt is a valid, more foolproof alternative at the layout/production engineer's discretion; not implemented here to avoid guessing a non-stock multi-pole part.
- `D_CLHI`/`D_CLLO` clamp diodes, `C_FILT`, and the MCU ADC connection are unchanged — still correctly protect/filter the shared ADC sensing node in both modes.

Verified via netlist trace, channel 1 shown (channels 2-6 identical topology): `SENSOR_CH1` = `{C_FILT1.1, D_CLHI1.2, D_CLLO1.1, JP_VBYP1.2, R_BURDEN1.1, R_SER1.2, R_VBOT1.1, U_MCU1.39}`; `net_CH1_SIG` = `{JP_VBYP1.1, J_SENSOR_SIG1.1, R_SER1.1}`; `net_CH1_IGND` = `{JP_IGND1.1, R_BURDEN1.2}` — exactly the designed topology.

### 6.3 Other audit categories

Connector verification, pull-up/pull-down survey, protection audit, RF verification (LoRa link budget — already covered in §3 Step 5), test point review, and BOM validation did not surface additional defects beyond items already tracked in §7's open-items list (M12 connector placeholders, `--schematic-parity` gap, `_TBD` resistor values). Full SPICE-level simulation is not available in this environment; the two findings above were instead verified by hand-calculation (link budget, divider ratio, current-loop compliance voltage) cross-checked against real netlist topology — the same discipline used throughout this project.

Component count: 161 → **181** BOM/PCB-placed components (3 new for §6.1's fix: `F2`, `TP_VALVE_PWR1`, plus a schematic-only `#FLG06` `PWR_FLAG` that carries no footprint, same as `#FLG01-05`; 18 new for §6.2's fix: 6× `R_VBOT`, 6× `JP_VBYP`, 6× `JP_IGND` — the revalued/rewired existing `R_SER`/`R_BURDEN` per channel don't add count). Schematic symbol count (including `#FLG06`): 182. PCB rebuilt with the same measured-footprint placement technique as §5 (0 out-of-bounds); board grew from 420×355mm to 420×361.6mm to fit the 20 new footprints. BOM regenerated: 84 grouped lines covering 181 components (`BOM/SWAFarmNodeV1_NodeCore_BOM.csv`), full disclosure notes in `BOM/SWAFarmNodeV1_NodeCore_BOM_Notes.md`.

### 6.4 Independent re-verification pass — 2026-08-01 (no critical defects; 3 new items logged)

User requested the same 11-category audit be re-run as an independent check on the design as it stands after §6.1/§6.2. Re-executed live against the current files rather than trusting the §6 writeup or the on-disk `_erc.json`/`_netlist.xml`/`_drc.json` exports (which predate the final schematic/PCB save by several hours): fresh `run_erc`/`run_drc`, a freshly regenerated netlist (`generate_netlist`), and pin-level `trace_netlist_connection` spot-checks. **Result: 0 new critical defects.** Both §6.1/§6.2 fixes reconfirmed intact — `V12_VALVE` still cleanly separated from `V12_SW` (verified by fresh netlist trace on `F1`/`F2`/`U1`), sensor-channel divider/jumper topology unchanged.

**MCU/STM32 contamination check (user-prompted).** Full pin-by-pin re-verification of `U_MCU1`'s real embedded `RF_Module:ESP32-S3-WROOM-1` symbol (all 41 pins, read directly from the schematic's `lib_symbols` block) against every GPIO assignment in §2's pin map table — all match exactly (e.g. pin 39/38 = `IO1`/`IO2` for `SENSOR_CH1`/`CH2`, pin 34/35 = `IO41`/`IO42` for `RS485_DE`/`RE`, pin 36/37 = `RXD0`/`TXD0` for the debug UART). Zero STM32 contamination in the design. The only literal "STM32" string anywhere in the file is inside `U_LORA1`'s own `Description` property ("LoRa Module, **STM32WLE5**, RU864/IN865/EU868") — RAKwireless's own factual description of the radio SoC built into their off-the-shelf RAK3172 module, unrelated to this project's own MCU choice and not something to change.

**Tooling caveat found and logged, not a design defect.** The MCP server's `detect_pin_conflicts` tool reported three components — `J_SWD1`, `U_CHG1`, `U_PROT1` — with STM32 port-style pin names (`PA4`, `PC0`, `PH0`, etc.) that do not exist anywhere in this project. Confirmed absent via `list_schematic_components` (181 real components, no such refs) and a full grep of the `lib_symbols` block (92 symbol defs, zero STM32-family symbols). Root cause not confirmed (plausibly a stale cache from some other project's data inside the MCP server process), but the tool's output does not reflect this file's real contents — future sessions should not trust `detect_pin_conflicts`' component list at face value for this project; cross-check against `list_schematic_components`/`get_symbol_details` first.

**Independent hand-verification (no SPICE available).** Re-derived the RF link budget from the free-space path loss formula (`FSPL(dB) = 20log₁₀(d_km) + 20log₁₀(f_MHz) + 32.44`) independently of §3 Step 5's numbers: 105.17dB at 5km/866MHz, 91.19dB at 1km — both match §3's table to within rounding. Re-derived the sensor divider (`10V × 100k/(232k+100k) = 3.01V`) — matches §6.2 exactly. This sandbox has no SPICE tooling and no PDF-rendering tool (`pdftoppm`/poppler not installed), so the TPS26600 `ILIM`/`UVLO`/`OVP`/`dVdT` exact datasheet formulas could not be extracted to close out the `_TBD` values in §4/§7 — that still needs a pull of the real datasheet on a machine with normal PDF tooling (or TI's WEBENCH/design-calculator).

**3 new items found, none blocking, added to §8:**
1. **`F1` sizing vs. combined downstream branch capacity (power rail audit).** `F1` (5A hold) feeds `V12_PROT`, which branches to both the eFuse (`U1`, 2A silicon-limited) and `F2` (4A hold) — combined downstream demand (~6A) exceeds `F1`'s own hold rating on paper. Likely fine in practice: the valves are *latching* solenoids (brief pulse to change state, not held energized) and `C_VALVEBULK1` (1000µF) supplies the pulse transient locally rather than pulling it all through `F1`, and PTC fuses trip on a thermal time constant, not instantaneously — but that reasoning is not written down anywhere or checked against the real solenoid's actual pulse duration/energy. Given `F1` was already found undersized once this same audit cycle (§6.1) for a related reason (not accounting for downstream valve demand), this deserves an explicit check rather than a repeat assumption.
2. **No production debug-lockdown / secure-boot plan (peer design review).** `hardware_requirements.md`'s Security Considerations mandate that "debug ports must be gated or disabled for production" and that "hardware support for secure boot and signed firmware verification is mandatory." `J_PROG1` (debug UART) and `J_USB1` (native USB programming) are both currently exposed with no documented plan for production lockdown. ESP32-S3 supports secure boot and flash encryption natively in silicon; nothing in this design or its BOM/docs tracks provisioning it yet. Not a schematic-capture blocker, but a real gap against the project's own mandatory requirement, worth a decision before mass production.
3. **No test point on `V12_PROT` itself (test point review).** `V12_PROT` is the single rail feeding both the eFuse branch (`V12_SW`) and the valve branch (`V12_VALVE`) — a dedicated test point here (matching the existing `TP_12V_SW1`/`TP_VALVE_PWR1` pattern) would let production test distinguish "input fuse (`F1`) blown," "eFuse (`U1`) fault," and "valve fuse (`F2`) fault" without probing component leads directly. Minor; add if convenient during routing.

## 7. Files changed

- `Hardware/SWAFarmNodeV1/SWAFarmNodeV1.kicad_sch` — extended through Steps 2-7 (incremental splices onto Step 1's file), then further edited 2026-08-01 for the §6 audit fixes (coordinate-anchored splices + targeted net/value edits, not a full rebuild).
- `Hardware/SWAFarmNodeV1/SWAFarmNodeV1.kicad_pcb` — rebuilt from scratch for Step 8 (Arduino_Mega template placeholder replaced), then re-placed 2026-08-01 to include the §6 fix's 20 new footprints.
- `Hardware/SWAFarmNodeV1/fp-lib-table` — extended to reference the full KiCad standard footprint library table (was previously only the Arduino template's single mounting-hole library).
- `Hardware/SWAFarmNodeV1/SWAFarmNodeV1_erc.json`, `_netlist.xml`, `_drc.json` — fresh exports.
- `Documentation/images/SWAFarmNodeV1_NodeCore_08PCB_TopView.png` — rendered top-down placement view.
- `BOM/SWAFarmNodeV1_NodeCore_BOM.csv`, `BOM/SWAFarmNodeV1_NodeCore_BOM_Notes.md` — regenerated/updated for the §6 fixes.

## 8. Open items for pre-fabrication review

- M12 connector footprints are placeholder THT headers, not real circular-connector footprints (same disclosed gap as Step 1's design review flagged) — must be resolved before Gerber export.
- `kicad-cli --schematic-parity` cross-reference gap (§5) — run "Update PCB from Schematic" in the KiCad GUI once, before routing, to fully link footprint UUIDs to schematic symbols.
- eFuse `ILIM`/`dVdT`, buck compensation, and now valve-driver `ILIM` resistor values remain reasoned placeholders (`_TBD` suffix in their Value fields) pending real datasheet-formula/loop-stability confirmation.
- Second-source qualification for all newly-introduced parts (`ESP32-S3-WROOM-1`, `ISO7761DW`, `MEE1S0505SC`, `THVD1450DR`, `DRV8871DDA`, `MCP23S17`, `RAK3172`) — same open item class as every prior milestone's Risk R-2/SWA-CST-004.
- Isolation-barrier creepage/clearance is not yet enforced by an actual copper-exclusion keepout zone on the PCB (floor-plan only) — needs a real keepout region around the RS485 isolated zone before routing, sized to the isolator/DC-DC's rated working voltage.
- `F1`/`F2` cited by real PTC family/class (Bourns MF-RG1812 / Littelfuse 1812L) rather than an exact single MPN — pin down exact hold-current part once the M12 connector's real current rating is resolved (previous item).
- `JP_VBYP`/`JP_IGND` (§6.2) are 2 separate jumpers populated as a matched pair by convention, not physically interlocked — consider a single mechanically-ganged DPDT switch or dual-row shorting shunt at the production-engineering stage to remove the possibility of populating them inconsistently.
- `F1` (5A hold) sizing doesn't have a written justification against the combined worst-case draw of its two downstream branches (eFuse's 2A silicon limit + `F2`'s 4A hold ≈ 6A) — likely fine given the valves are latching-solenoid (pulse, not held) loads buffered by `C_VALVEBULK1`, but confirm explicitly against the real solenoid pulse profile before BOM lock (§6.4).
- No production debug-lockdown / secure-boot provisioning plan yet for `J_PROG1`/`J_USB1`, against `hardware_requirements.md`'s mandatory Security Considerations (gated debug ports, secure boot/signed firmware) — needs a decision before mass production (§6.4).
- No test point on `V12_PROT` itself — would improve production fault isolation between input-fuse, eFuse, and valve-fuse failures; add if convenient during routing (§6.4).
