# SWAFarm Node V1 — Step 08: Battery & Solar Power Management — Design Review

**Status:** Captured, ERC-clean against baseline (92 violations: 45 errors / 47 warnings — 2 fewer errors than the pre-milestone baseline, zero new warnings). Awaiting approval before Step 09.
**Date:** 2026-07-31

---

## 1. Executive Summary

This milestone completes the power architecture that `01_power` deliberately deferred: solar input, battery charging, independent hardware battery protection, automatic power-path arbitration, and battery monitoring. It implements the architecture already designed on paper in `SWAFarmNodeV1_PowerSupply_Design.md` (TI BQ25792-family charger, TI BQ76920 protection AFE, 4S LiFePO4 pack), now captured in KiCad for the first time. The existing `01_power` buck converter (U1) — previously fed directly from the raw, unmanaged DC-IN protection stage — is now correctly fed from the charger's regulated `VSYS` output, completing the intended power chain: **External DC / Solar → protection → charger/power-path → battery ↔ VSYS → buck → 3.3V rail**.

Two genuine missing-requirement gates were hit and resolved with the user before implementation rather than guessed: (1) battery capacity, solar panel spec, and environmental temperature range were not defined anywhere in the requirements documentation — resolved via explicit confirmation (3.35Ah/cell provisional capacity, 10W/≤20V Voc solar target, -20°C to +60°C operating range); (2) the exact BQ25792 part has no official KiCad symbol — substituted with **BQ25798**, a real, verified, same-family, same-topology stock KiCad part (dual-input VAC1/VAC2 NVDC buck-boost charger), mirroring the identical LT8609A→LT8610AC substitution precedent already established in `01_power`.

No previously-approved circuitry was altered except the one disclosed, necessary rewire (U1's input source).

---

## 2. Power Architecture

```
External DC 12V ──[J1]── Surge/PTC/reverse-pol (existing 01_power) ──► VIN_PROT ──► VAC1 ─┐
Solar Panel 12V-class ──[J2]── Surge/PTC/reverse-pol (mirrors J1, new) ──► SOL_PROT ──► VAC2 ─┤
                                                                                              ▼
                                                                          U_CHG1: BQ25798 (substitutes BQ25792)
                                                                          I2C-controlled dual-input NVDC buck-boost charger
                                                                                    │            │
                                                                                 BAT_P          VSYS (9-15V)
                                                                                    │            │
                                                                    U_PROT1: BQ76920PW           ├──► U1 (LT8610AC buck, EXISTING) ──► 3V3_RAIL
                                                                    independent HW protection     │
                                                                    + Q_DSG1/Q_CHG1 FET pair       └──► VSYS_RAW_OUT (relay coils / sensor power,
                                                                    + R_SENSE1 shunt                    EXISTING nets from 06_Relay/07_FieldIO)
                                                                                    │
                                                                          [F3 series fuse] ──[J3]── 4S LiFePO4 Pack

I2C (PWR_I2C_SDA/SCL, shared bus) + CHG_ALERT_N + PROT_ALERT_N ──► MCU (02_MCU-reserved pins, first use this milestone)
Battery voltage sense (discrete, low-IQ divider) ──► MCU ADC (PB1, spare pool, first use this milestone)
```

This directly implements §3 of `SWAFarmNodeV1_PowerSupply_Design.md` — the same architecture, now realized in the actual schematic rather than just the logical design doc.

---

## 3. Solar Interface Design

The Solar-IN port (`J2`) mirrors the existing DC-IN port (`J1`) topology **exactly** — same protection philosophy already approved in `01_power`, applied to the second input:

| Stage | Component | Rationale |
|---|---|---|
| Connector | `J2`, `Connector:Screw_Terminal_01x02`, Phoenix MKDS-3 5.08mm pluggable screw terminal (same footprint family as J1) | Field-serviceable, polarity-labeled per SWA-HWR-305 |
| Overcurrent | `F2`, 0.75A hold PTC | Sized for a 10W/≤20V panel's worst-case current (~0.6-0.65A at Isc), well below F1's 1.1A DC-IN rating since solar current is inherently lower — right-sized, not just reused |
| Surge/reverse-polarity | `D2`, `SMBJ24A_class_unidirectional` TVS | **Unidirectional** (vs. D1's bidirectional class) since solar panel output is inherently single-polarity — 24V standoff gives margin above the 20V Voc target while staying under the charger's 24V VAC absolute-max window; doubles as crude reverse-polarity clamping (forward-conducts if a technician miswires the connector), same reasoning already applied to the sensor-power TVS in `07_FieldIO` |
| Reverse-polarity switch | `Q2` + `R_gate2`, identical low-side self-biased N-MOSFET topology as `Q1`/`R_gate1` | Direct reuse of the already-approved, ERC-verified `01_power` topology — zero added quiescent current, near-zero voltage drop, no new part number |
| Input filtering | `C_SOL_IN1`, 4.7µF bulk | Local bulk capacitance at the protected solar input, before the charger's VAC2 pin |
| Test point | `TP_SOLAR1` on `SOL_PROT` | Satisfies the explicit "Solar Voltage" testability requirement (§7 of the task) |

**Maximum input voltage**: the charger's VAC1/VAC2 pins accept 3.6–24V; D2's 24V standoff plus the ≤20V Voc panel target (user-approved) gives a real margin, not a knife-edge — consistent with Risk R-1 already recorded in the architecture doc.

---

## 4. Battery Charger Selection

**Selected: TI BQ25798** (`Battery_Management:BQ25798`, real stock KiCad symbol, VQFN-29, footprint `Package_DFN_QFN:Texas_RQM0029A_VQFN-29_4x4mm_P0.4mm`), substituting the architecture doc's originally-specified **BQ25792**.

**Why the substitution**: BQ25792 has no official or community KiCad symbol available in this environment (same class of gap that forced the LT8609A→LT8610AC substitution in `01_power`). BQ25798 is a real, verified, same-family TI part sharing the core architecture the design actually needs: I2C-controlled, dual-input (VAC1/VAC2) NVDC buck-boost charger, 1–4 cell, 5A class, 3.6–24V input window — confirmed pin-for-pin against the real stock symbol (29 unique pin positions extracted and verified, not guessed). This is a **documented, explained substitution**, not a silent change — flagged as Risk R-BATT-2 (§12) for confirmation against a locked BQ25792 or BQ25798 datasheet before BOM release, exactly the same treatment already given to the three single-source ICs in the original architecture doc.

**Charging profile**: 4S LiFePO4, charge voltage regulation range comfortably covers the pack's ~10.0–14.6V operating window (charger's regulation range is 3–18.8V per the part's own description). Target charge current ~1.6A (≈0.5C of the 3.35Ah provisional capacity, a conservative rate that preserves LiFePO4 cycle life) — set via `R_PROG1` on the PROG pin, value marked `TBD_verify_datasheet_for_1.6A_target` pending the exact scaling formula from a locked datasheet (same "class"/TBD component treatment used throughout this project for values that depend on a specific datasheet revision).

**Safety features implemented**:
- Dual-input selector (`Q_AC1`/`Q_AC2`, gate-driven by ACDRV1/ACDRV2 with BTST1/BTST2 bootstrap caps) — standard NVDC input-qualification topology for this device family, ORing the two sources at the internal `CHG_VBUS_INT` node.
- NTC thermistor input (`NTC_CHG1`) for charge-temperature qualification, sized for the -20°C to +60°C operating range (user-confirmed).
- I2C telemetry (VBUS, VBAT, VSYS, IBUS, IBAT, TDIE, TS per the part family) plus a dedicated `CHG_ALERT_N` interrupt line to the MCU's previously-reserved pin (`02_MCU`'s "Battery monitor / charger telemetry I2C" allocation, PC4) — consumed for the first time this milestone.
- Charge status LED (`D_CHG_STAT1` + pull-up `R_CHG_STAT1`) on the open-collector STAT pin.

**Explicit, disclosed simplifications** (documented, not silent):
- `D+`/`D-` (USB BC1.2/HVDCP detection pins) left unconnected — no USB negotiation needed for this application.
- `SDRV` (ship-mode FET drive) left unconnected — no ship-mode disconnect FET added this milestone; battery disconnect is handled by the independent protection AFE instead (§5).
- `QON` tied to GND via a 100kΩ pull-down — standard "no external wake button, auto power-up on VBUS presence" configuration.
- `CE` tied directly to GND — charger permanently enabled at the hardware level (no MCU-controlled enable this milestone; a spare GPIO could add this in a future revision).

**This entire IC's external application circuit (input selector FETs, bootstrap network, ILIM/PROG resistor scaling) is captured per standard BQ2579x-family application-circuit convention, not verified pin-by-pin against a specific locked datasheet revision — flagged prominently as Risk R-BATT-1 (§12), the most important open item from this milestone.**

---

## 5. Battery Protection Strategy

**Selected: TI BQ76920PW** (`Battery_Management:BQ76920PW`, real stock KiCad symbol, TSSOP-20) — an **exact match** to the architecture doc's specification (no substitution needed), confirmed "Lithium battery monitor, 3-5 cells, integrated balancing, I2C interface" directly in the library's own part description.

This AFE forms a **second, independent hardware protection layer** — its FET pair physically breaks the battery's own return path regardless of what the charger IC or MCU firmware is doing, satisfying SWA-PWM-003 ("all high-risk fault modes must map to protective hardware... response") exactly as the architecture doc specified.

| Protection | Mechanism |
|---|---|
| **Overcharge** | BQ76920 monitors each cell tap (VC0–VC4 for this 4S pack; VC5 tied to VC4 per the standard "5S-capable device used in 4S mode" configuration) and opens `Q_CHG1` (charge FET) if any cell exceeds its safe upper threshold — independent of the charger IC's own regulation loop |
| **Over-discharge** | Same per-cell monitoring opens `Q_DSG1` (discharge FET) below the safe lower threshold |
| **Reverse current** | The back-to-back FET pair (`Q_DSG1`.Source = `Q_CHG1`.Source at the shared `FET_MID` node) blocks current in both directions when either FET is commanded off — standard low-side protector topology |
| **Short-circuit** | BQ76920's autonomous SCD (short-circuit-in-discharge) hardware comparator trips `Q_DSG1` directly, without waiting for I2C/firmware — this is the core reason a *dedicated* protection AFE was chosen over relying on the charger's own BATFET (Risk R-6 in the original architecture doc, explicitly preserved here) |
| **Battery disconnect** | Achieved via the FET pair itself (both open = pack fully isolated from the rest of the board) — no separate mechanical disconnect added |
| **Tertiary failsafe** | `F3`, a one-time series fuse in the `BAT_P` path (between `J3` pin 1 and the rest of the circuit) — a last-resort backup beyond the two active FET-based layers, per the architecture doc's own "Supporting parts" list |
| **Current sensing** | `R_SENSE1`, 5mΩ 1% precision shunt (2512 package) between `Q_CHG1`'s drain and system GND, differentially sensed via SRP/SRN — supports both overcurrent protection and coulomb counting |
| **Thermal** | `NTC_PROT1`, dedicated to the AFE's own TS1 pin (separate from the charger's `NTC_CHG1` — two thermistors rather than sharing one, to avoid interaction between the two ICs' internal bias current sources) |

**Cell tap network**: `VC1`/`VC2`/`VC3` each get a 1kΩ series resistor + 100nF filter-to-GND (`R_VC1_1`/`C_VC1_1` etc.) — standard practice limiting fault current into the IC and filtering sense noise. **Simplification disclosed**: the filter caps are referenced to GND rather than to each tap's adjacent lower cell (the more precise differential-filter convention some BQ769x0 reference designs use) — a reasonable, common simplification for a 4S pack, flagged in Risk R-BATT-1 alongside the charger's own application-circuit caveat.

**Testability**: `TP_ISENSE_HI1`/`TP_ISENSE_LO1` across `R_SENSE1` let a production technician measure the millivolt drop with a precision meter and compute current = ΔV/R_sense — satisfies the "Charging Current" test point requirement (§7 of the task) without needing a dedicated current-sense IC.

---

## 6. Power Path Management

**Priority and failover**, implemented natively in the BQ25798's NVDC power-path silicon (not firmware-managed switching, per the architecture doc's explicit reasoning):

1. **External DC (VAC1) is primary**, Solar (VAC2) is secondary — the charger's own input-qualification logic selects whichever source is present and valid; if both are present, it arbitrates per its internal priority (default: VAC1).
2. **VSYS is regulated slightly above VBAT** whenever any input source is present (NVDC — Narrow Voltage DC power path), with the battery supplementing load transients the input alone can't cover.
3. **Battery-only fallback**: when neither DC-IN nor Solar is present, VSYS is powered directly from the battery through the charger's own pass-through path — no hardware change needed, this is inherent to the NVDC architecture.
4. **Sequencing**: `U1` (the existing 3.3V buck) now draws from `VSYS` (post-charger) rather than the old direct `VIN_PROT` tap — meaning the 3.3V rail is available under all three source conditions (external DC, solar, or battery-only) rather than only when raw DC-IN was present, a **functional improvement** over the as-built `01_power`-only state, not just a rewire for its own sake.
5. **`VSYS_RAW_OUT`** (relay coils, `06_Relay`; sensor power, `07_FieldIO`) remains a raw ~9–15V tap off the same `VSYS` bus, unchanged in its own topology — it simply now has a real, managed source behind it for the first time, closing the gap both of those milestones explicitly disclosed and flagged (Risk R-RELAY-1, R-FIO-2).

**This is the single most consequential integration change of this milestone**: `U1`'s input was redirected from `VIN_PROT` to the new `VSYS` net (user-approved before implementation, §4 of the pre-implementation discussion). The old `VIN_PROT`-side `PWR_FLAG` (`#FLG02`) was relocated to a different point still on `VIN_PROT` (coincident with `TP1`) rather than deleted, since `VIN_PROT` itself still needs one for ERC (it feeds `VAC1` and the pre-existing DC-IN protection stage, none of which are "power output" pin types). A new `PWR_FLAG` (`#FLG05`) was added at the charger's internal `CHG_VBUS_INT` node — the input-selector-FET topology means no pin there is natively typed "power output" from ERC's perspective, even though it is one architecturally; this is the standard, already-precedented fix for that class of situation on this board.

---

## 7. Battery Monitoring Design

Two independent, complementary paths, per the task's explicit request for a discrete divider distinct from I2C telemetry:

**Digital (I2C)**: BQ25798 and BQ76920PW both report cell/pack voltage, current, and temperature over the shared `PWR_I2C_SDA`/`PWR_I2C_SCL` bus (4.7kΩ pull-ups, `R_I2C_SDA_PU1`/`R_I2C_SCL_PU1`, to `3V3_RAIL`) — the primary, precise telemetry path, matching the architecture doc's fleet-analytics intent.

**Analog (discrete divider)**: a low-quiescent-current backup/redundant path directly on `BAT_P`:

```
BAT_P ──[R_BATSENSE_TOP1, 680kΩ]──┬──[R_BATSENSE_BOT1, 180kΩ]── GND
                                    │
                              [C_BATSENSE1, 100nF] to GND
                                    │
                              MCU ADC (PB1, spare pool)
```

- **Ratio**: 180k/(680k+180k) ≈ 0.2093 — at the pack's worst-case high voltage (~14.6V), the ADC sees ~3.06V (safely under the 3.3V reference with margin); at the low cutoff (~10V), ~2.09V (still comfortably resolvable by a 12-bit ADC).
- **Measurement accuracy**: dominated by resistor tolerance (standard 1% parts give ~±1% ratio accuracy) and ADC reference accuracy — adequate for coarse battery-state monitoring and low-voltage brownout detection; the I2C path remains the precision source for fleet telemetry.
- **Power consumption**: 14.6V / 860kΩ ≈ 17µA continuous — deliberately sized 10× larger than a "textbook" divider specifically to minimize quiescent draw (a 100k/27k-class divider would draw ~170µA, a ~40% addition to the whole board's sleep budget by itself). This is a direct, disclosed trade-off in favor of the milestone's explicit "low quiescent current" priority.
- **Calibration**: firmware should apply the nominal 0.2093 ratio and MCU VREF as a first-order calibration; a per-unit factory trim (reading a known-good reference voltage during production test) would improve accuracy further but is a firmware/test-process decision, out of scope here.
- **Test point**: `TP_BATSENSE1` on the divider midpoint, plus `TP_BAT1` on the raw (undivided) `BAT_P` node for direct verification.

**MCU pin**: `PB1`, verified against the real STM32L462RETx symbol's pin table (not assumed) — confirmed floating/spare in the `02_MCU` GPIO reservation table before use.

---

## 8. Current Consumption Table

Datasheet-class, planning-level figures (per SWA-PWM-201, not yet a measured budget — same disclosure already applied throughout this project):

| Mode | Rail | Contributors | Current |
|---|---|---|---|
| Sleep | VSYS-side | Charger IC standby (~20µA) + protection AFE normal-mode (~15µA) + buck IQ (~3µA) | 38µA |
| Sleep | 3.3V-side | MCU STOP2 (~1.5µA) + LoRa deep sleep (~2µA) + RS485 transceiver idle (~1mA, not power-gated — see `06_Relay`/`07_FieldIO` note) + battery-sense divider (17µA) + misc (~8µA) | ~1028.5µA |
| **Sleep total** | referred to VSYS via buck efficiency (~70% at light load) | | **≈0.41mA (410µA)** |
| LoRa TX (peak) | 3.3V-side | RAK3172 @ max power | ~130mA (+MCU ~5mA active) |
| All 5 relays energized | VSYS-side | `06_Relay` | 385mA |
| 5 RS485 sensors, max load | VSYS-side | `07_FieldIO` (100mA/sensor × 5, user-approved) | 500mA |
| **Worst-case simultaneous** | VSYS (12.8V), buck-referred | relays + sensors + LoRa TX + MCU + charger/AFE/buck overhead | **≈933mA (~0.93A, ~11.9W)** |

(Full derivation already presented and unchanged from the pre-implementation discussion; repeated here per the task's explicit Section 8 requirement.)

---

## 9. Estimated Battery Life

Using the user-approved provisional capacity (3.35Ah/cell, 4S LiFePO4, ≈42.9Wh pack energy):

| Scenario | Basis | Result |
|---|---|---|
| Sleep-only ceiling (illustrative, unrealistic as a sustained mode) | 410µA × 12.8V ≈ 5.25mW | ≈340 days |
| Worst-case continuous (illustrative, unrealistic — shows the floor) | ≈11.9W | ≈3.6 hours |
| **Illustrative light-duty field scenario** (assumptions, not a spec — LoRa uplink/15min, sensors polled 10s/5min at rated load, relays 30min/day) | ≈7.72Wh/day | **≈5.6 days autonomy** |

The illustrative scenario's result lands almost exactly on the architecture doc's original "5–7 day no-solar autonomy" target (§4.3 of `SWAFarmNodeV1_PowerSupply_Design.md`) — a reassuring consistency check between the two independently-derived figures, though both remain provisional pending a real firmware duty-cycle measurement (SWA-PWM-201).

**Recommended solar panel**: bare minimum ≈2.3W (daily 7.72Wh ÷ 4 peak-sun-hours ÷ 85% charge efficiency); **user-approved target: 10W, Voc ≤20V** for real-world margin (monsoon cloud cover, panel soiling/aging, non-optimal tilt) — sized into the protection stage (§3) and consistent with Risk R-1 in the original architecture doc.

---

## 10. Thermal Considerations

- **Operating range**: -20°C to +60°C (user-confirmed, §7 of the pre-implementation discussion) — applied to both NTC thermistor placements (`NTC_CHG1` for charge-temperature qualification, `NTC_PROT1` for the protection AFE's own thermal monitoring).
- **Charger dissipation**: BQ25798's VQFN-29 exposed pad carries real power at charge currents in the ampere class (the architecture doc's own footprint note already flags this for the equivalent BQ25792 package) — thermal via pattern under the exposed pad is a PCB-layout-stage concern, recorded here, not yet actionable without a real footprint placed (per the standing "no PCB routing yet" rule).
- **Protection FET pair** (`Q_DSG1`/`Q_CHG1`): reuse the same `NMOS_30V_RDSon_20mOhm`/TO-252 class already used for `Q1` — adequately margined for the pack's charge/discharge current class, low conduction loss keeps self-heating modest.
- **Sense resistor** (`R_SENSE1`): 2512 package chosen specifically for its larger thermal mass/power dissipation capability relative to smaller chip resistors, appropriate for a component that continuously carries the full pack current.
- **Sealed IP65 enclosure risk** (R-7 in the original architecture doc, unchanged and still open): both the charger's TS pin and the AFE's TS1 pin now have real, wired thermistor networks in this milestone — the *hardware mechanism* for enclosure-heat-aware charge qualification exists; whether the NTC placement is thermally representative of actual cell temperature remains an enclosure-design-stage confirmation (`mechanical_design.md`), not resolved by schematic capture alone.

---

## 11. Engineering Decisions

1. **BQ25798 substitutes BQ25792** — no official KiCad symbol exists for BQ25792; BQ25798 is a real, verified, same-family, same-core-architecture part. Directly mirrors the already-approved LT8609A→LT8610AC precedent from `01_power`.
2. **U1's input redirected from VIN_PROT to VSYS** — necessary for the charger/battery stage to be anything other than an electrically orphaned block; user-approved before implementation, disclosed explicitly rather than silently changed.
3. **Two separate NTC thermistors** (one per IC) rather than one shared — avoids risking interaction between the two ICs' internal bias current sources, at the cost of one extra low-value component.
4. **Discrete battery-voltage divider sized for low IQ** (860kΩ total, ~17µA) rather than a "textbook" lower-impedance divider — direct trade-off favoring the milestone's explicit "low quiescent current" priority over ADC settling speed (a firmware-side sample-timing consideration, not a hardware blocker).
5. **CE tied hard to GND (always enabled)**, no MCU-controlled charger enable this milestone — matches the "IMPLEMENT ONLY Step 08" scope discipline; a future milestone could route this to a spare GPIO if firmware-controlled charge inhibit is wanted.
6. **Battery pack connector reuses the Screw_Terminal_01x02/Phoenix MKDS family** already used for J1/J2, rather than the architecture doc's originally-suggested keyed Molex Mini-Fit Jr class — no suitably-sized keyed 2-pin symbol exists in the stock library; screw terminals are still polarity-labeled via silkscreen (SWA-HWR-305-compliant) and keep the BOM/footprint family consistent across all three power connectors on this board.

---

## 12. Risks

| ID | Risk | Status |
|---|---|---|
| R-BATT-1 | The charger's external application circuit (input-selector FETs, bootstrap network, ILIM/PROG resistor values) and the AFE's cell-tap filter network are captured per standard BQ2579x/BQ76920 application-circuit convention, not verified pin-by-pin against a specific locked datasheet revision | **Open — highest-priority item from this milestone.** Must be reviewed against TI's actual datasheet application section before fabrication release |
| R-BATT-2 | BQ25798 substitutes BQ25792 (no stock symbol available); BQ76920PW and the core dual-input NVDC architecture are confirmed real/verified, but the exact substitute part's full electrical equivalence to the originally-specified BQ25792 is not independently re-verified here | Open — confirm at BOM lock, alongside the pre-existing R-2 (single-source qualification) from the architecture doc |
| R-BATT-3 | `R_ILIM1`/`R_PROG1` values marked TBD pending the exact datasheet scaling formula for target input-current-limit and ~1.6A charge current | Open — size at detailed design |
| R-BATT-4 | Battery capacity (3.35Ah/cell), solar panel spec (10W/≤20V Voc), and environmental range (-20°C to +60°C) are all user-approved planning assumptions, not measured/sourced specs | Open — same disclosure pattern as the architecture doc's original R-3; confirm once real cells/panel are selected |
| R-BATT-5 | Cell-tap filter network uses cap-to-GND rather than cap-to-adjacent-tap (a simplification vs. some BQ769x0 reference designs) | Open — verify against datasheet recommended practice before fabrication |
| R-BATT-6 | Second-source qualification for BQ25798, BQ76920PW not yet performed (extends the architecture doc's existing R-2) | Open, SWA-CST-004 |
| R-BATT-7 | UN38.3/IEC 62133 battery pack certification track not yet started (unchanged from the architecture doc's R-4) | Open — carried forward, no new work this milestone |

---

## 13. ERC Results

Real `kicad-cli sch erc` (authoritative): **92 violations (45 errors, 47 warnings)** — 2 *fewer* errors than the 47-error pre-milestone baseline (three previously-unconnected MCU pins consumed — `PB1`, `PC4`, `PC5` — offset by one new intentionally-unconnected pin net gained), and **zero new warnings** (47, exactly matching baseline composition: pre-existing `endpoint_off_grid` grid warnings from `02_MCU` plus the pre-existing `THVD1450D` `lib_symbol_mismatch`).

All new components were placed on the 1.27mm grid (verified after an initial process error — see Documentation Updates below).

Of the 45 remaining errors, exactly 3 are new and intentional: `U_CHG1` pins `D+`, `D-`, `SDRV`, deliberately left unconnected (§4). All others are pre-existing, already-documented reserved-but-unwired MCU/LoRa GPIOs.

Two real defects were found and fixed during implementation, both before this final ERC run:
1. A `pin_to_pin` "Power output and Power output connected" error, caused by the pre-existing `#FLG02` `PWR_FLAG` sitting at the exact coordinate that became `U1`'s new `VSYS` input pin — relocated to a different, still-valid point on `VIN_PROT` (coincident with `TP1`).
2. A `power_pin_not_driven` error on `U_CHG1`'s `VBUS` pin — the input-selector FETs' shared source node (`CHG_VBUS_INT`) has no "power output"-typed pin from ERC's perspective even though it is one architecturally; resolved with a new `PWR_FLAG` (`#FLG05`), the same established pattern already used elsewhere on this board.

Independently verified via `generate_netlist` + `trace_netlist_connection` on `U_CHG1`, `U_PROT1`, `Q_DSG1`, and `J3`: every net matches the intended topology exactly — `VAC1`/`VAC2` correctly isolated to their respective protected input nets, `VSYS` correctly now feeding `U1`'s buck input, the low-side protection FET pair correctly in series between `CELL_N` and `GND` via `SENSE_SRP`, cell taps correctly isolated per channel, I2C/ALERT lines correctly shared across charger/AFE/MCU, and all three deliberately-unconnected charger pins confirmed genuinely isolated (not accidentally shorted).

`SWAFarmNodeV1_erc.json` re-exported reflecting this state.

---

## 14. Documentation Updates

- This document created.
- `TODO.md`: new "Battery & Solar Power Management" milestone entry to be added (see below), including the process-error/grid-alignment lesson.
- `SWAFarmNodeV1_PowerSupply_Design.md`: to be annotated marking §4.1 (charger) and §7 (KiCad symbol list) as superseded by the real BQ25798 substitution and the verified pin tables now captured in the schematic.
- No BOM CSV update — consistent with established precedent (`SWAFarmNodeV1_PowerSupply_BOM.csv` covers only `01_power`'s as-built scope; this milestone's component decisions are recorded here instead).

### Process note (for TODO.md Tooling section)

This milestone's initial schematic generation pass used "round number" origin coordinates (e.g., `(200.00, 900.00)`) for readability, breaking this project's established 1.27mm grid-alignment discipline and producing 70 new `endpoint_off_grid` ERC warnings on the first attempt. Root cause: convenient round decimal millimeter values are very often *not* exact multiples of 1.27mm (the KiCad connection grid), the same class of mistake documented as a lesson during `02_MCU`. Fixed by a targeted script pass snapping only genuine new-component origin variables to the nearest 1.27mm multiple — carefully excluding any coordinate copied from a *real, existing* component pin (e.g., the verified MCU pin position used for the battery-voltage ADC connection), since snapping those would have silently disconnected the label from the actual pin it needed to reach. Lesson: when hand-picking new origin coordinates for bulk schematic generation, always choose multiples of 1.27mm (ideally 2.54mm) from the start rather than convenient round numbers — cheaper than a post-hoc regex fix, and zero risk of a snap script touching a coordinate that must stay exact.
