# SWAFarm Node V1 — Step 06: Industrial Relay Output Subsystem — Design Review

**Status:** Captured, ERC-clean against baseline (no new violations). Awaiting approval before Step 07.
**Date:** 2026-07-31

---

## 1. Executive Summary

Five identical, independently-controlled relay output channels (`RELAY1`–`RELAY5`) were added to the schematic, each capable of switching an external field load (water pump, solenoid valve, contactor coil, lighting circuit, or irrigation controller) under MCU control. Each channel is a standard low-side N-MOSFET relay driver: MCU GPIO → gate resistor → logic-level N-MOSFET → relay coil, with a flyback diode across the coil and a pull-down resistor holding the channel safely OFF by default (including during MCU reset/boot before firmware configures the GPIO). A shared, locally-filtered coil-power rail (`RELAY_PWR`) is derived from the already-reserved `VSYS_RAW_OUT` net via a power ferrite bead and bulk capacitor, isolating relay-switching noise from other consumers of that same rail (notably RS485 sensor power, `04_RS485`). Each channel exposes a 3-position screw-terminal field connector with clearly assigned COM/NO/NC contacts, a control-signal test point, and a status LED tapped directly off the control net (zero incremental GPIO cost). Relay contacts are deliberately **not** tied to board GND, preserving the relay's built-in galvanic isolation between the control circuit and whatever the contacts switch.

All five channels consume exactly the five GPIOs (`PB12`, `PB13`, `PB14`, `PB15`, `PA15`) reserved for "Relay driver ×5" in `02_MCU`'s GPIO allocation table — no other subsystem's pins were touched, and no previously-approved circuitry (`01_power` through `05_LoRaWAN`) was modified.

---

## 2. Relay Architecture

Each of the 5 channels is topologically identical:

```
RELAY_PWR ──┬── Relay coil (A1) ──── Relay coil (A2) ──┬── MOSFET Drain
            │                                          │
      Flyback diode (K)                          Flyback diode (A)
            │                                          │
            └──────────────────────────────────────────┘
                                                         │
MCU GPIO ── R_GATE(100Ω) ──┬── MOSFET Gate              MOSFET Source ── GND
                           │
                     R_PD(10k)
                           │
                          GND

MCU GPIO net also feeds: R_STATUS(1k) ── Status LED (anode) ── GND (cathode)

Relay contacts: COM(11) / NC(12) / NO(14) ──→ 3-pin field connector (isolated from GND)
```

- **Low-side switching** was chosen (MOSFET between coil return and GND, coil supply tied directly to `RELAY_PWR`) — consistent with the low-side reverse-polarity MOSFET topology already used for Q1 in `01_power`, and the simplest, most common topology for driving a relay coil from a 3.3V logic GPIO.
- **Default-OFF safety**: the 10kΩ pull-down (`R_RELAY{n}_PD1`) holds the MOSFET gate at 0V whenever the GPIO is floating or tri-stated (MCU in reset, or before firmware initializes the pin as an output), guaranteeing every relay is de-energized at power-up and during MCU reset — this is the primary safety mechanism requested for this subsystem.
- **Status LED at zero GPIO cost**: rather than consuming a 6th GPIO per channel, each status LED (`D_RELAY{n}_STATUS1`) is tapped directly off the same control net that drives the gate, through its own 1kΩ resistor (matching `R_ACT1`'s value/footprint convention from `03_HMI`). Steady-state current draw when a channel is ON is dominated by the LED (~2mA) plus the pull-down's bleed current (~0.33mA) — the MOSFET gate itself draws negligible steady-state current since it's a capacitive load, not a continuous-current one. This is comfortably within a single STM32L4 GPIO's standard drive capability.

---

## 3. GPIO Allocation

| Channel | GPIO | Net | Consumed from |
|---|---|---|---|
| RELAY1 | PB12 | `RELAY1_CTRL` | `02_MCU` GPIO table, "Relay driver ×5" reservation |
| RELAY2 | PB13 | `RELAY2_CTRL` | ″ |
| RELAY3 | PB14 | `RELAY3_CTRL` | ″ |
| RELAY4 | PB15 | `RELAY4_CTRL` | ″ |
| RELAY5 | PA15 | `RELAY5_CTRL` | ″ |

These are exactly the five pins `02_MCU` named for this purpose ("Chosen on TIM1-capable pins where practical for future PWM flexibility") and were confirmed still floating (ERC `pin_not_connected`) immediately before this milestone. No pins reserved for any other subsystem (LoRaWAN UART, RS485, battery-monitor I2C, sensor front-end, SPI/expansion, user buttons) were touched. Per this project's established convention (see `04_RS485`/`05_LoRaWAN`), `02_MCU`'s own GPIO table is treated as an immutable planning snapshot and is not retroactively edited by each consuming milestone — consumption is authoritatively recorded here and in `TODO.md`.

---

## 4. Driver Selection: N-MOSFET vs. NPN BJT

**N-MOSFET (logic-level, low-RDS(on)) was selected.** Evaluation:

| Criterion | NPN BJT | N-MOSFET (selected) |
|---|---|---|
| Static MCU/GPIO loading | Continuous base current required (~mA-scale) to hold saturation for as long as the relay is energized | Gate is capacitive — draws current only during the switching transition, ~0 steady-state. Directly satisfies the "low MCU loading" requirement. |
| Conduction loss | V_CE(sat) ≈ 0.2–0.3V at the relay coil's current — real power dissipated in the driver, worse ×5 channels | R_DS(on) in the tens of mΩ at 3.3V V_GS — an order of magnitude lower conduction loss |
| Drive predictability over temperature | h_FE varies significantly with temperature; requires conservative base-current overdrive margin to guarantee saturation across conditions | V_GS(th) is far more stable; a simple series gate resistor + pull-down is sufficient, no gain-margin calculation needed |
| Project precedent | Not used elsewhere on this board | Matches the N-MOSFET already selected for Q1 (reverse-polarity protection, `01_power`) — reuses an established, proven part class |

Given the explicit "low MCU loading," "industrial reliability," and "EMC-friendly" requirements, plus this project's own precedent, N-MOSFET is the clear choice with no meaningful downside for this application.

**Selected device:** generic logic-level N-MOSFET, SOT-23, Value `NMOS_30V_RDSon_100mOhm_SOT23` (`Transistor_FET:Q_NMOS_GSD` generic symbol — same symbol family as Q1, footprint `Package_TO_SOT_SMD:SOT-23`). SOT-23 was chosen over Q1's TO-252 package because relay coil current (tens of mA per channel, §6) is roughly two orders of magnitude below what TO-252 was sized for in `01_power` (full board input current) — a small-signal SOT-23 part is the correctly-sized, lower-cost choice for this role. As with other "class" designations used throughout this project's BOM (e.g., `01_power`'s `NMOS_30V_RDSon_20mOhm`), a specific orderable part number (e.g. AO3400/2N7002-class) is a manufacturing-release task, not a schematic-capture blocker.

**Gate resistor** (`R_RELAY{n}_GATE1`, 100Ω): limits gate-charge inrush current and damps ringing on the gate node — an EMC measure, not a saturation-margin calculation (unlike the BJT case).

---

## 5. Relay Selection

**Selected:** Finder 40.51 series, SPDT (1 Form C), 12VDC coil, 10A contact rating — KiCad stock symbol `Relay:FINDER-40.51`, footprint `Relay_THT:Relay_SPDT_Finder_40.51`, BOM designation `FINDER-40.51.9.012.0000` (12VDC coil, flux-proof/washable "9" variant).

Rationale:
- **Industrial-grade, not hobby-grade.** Finder is a recognized industrial relay manufacturer; the 40-series is a general-purpose power relay family used widely in real automation/control-panel products, not a consumer PCB-relay-module part. This directly satisfies the "never use hobby components" instruction.
- **Coil voltage (12VDC) matches `VSYS_RAW_OUT`.** `VSYS_RAW_OUT` is the net reserved in the original architecture doc and already reused for RS485 sensor power (`04_RS485`) — its description ("feeds relay/other-subsystem rails") makes it the architecturally intended source for relay coil power, and its expected ~9–15V range (from the future 4S LiFePO4 charger stage) matches a 12V coil well. See §6 for the explicit power-source decision.
- **Contact rating (10A @ 250VAC / 30VDC)** comfortably covers the stated load classes (pumps, solenoid valves, contactors, lighting, irrigation controllers), including mains-adjacent loads plausible in an Indian agricultural (230VAC) context.
- **Standard IEC/Finder contact numbering** (11 = common, 12 = normally closed, 14 = normally open) is used as-is from the library symbol — a real, unambiguous industrial numbering convention, reused directly on the field-wiring connector silkscreen (§8).
- **THT package** is normal and expected for a relay of this contact rating (mechanical robustness under switching stress), consistent with how RS485's field connectors also use THT terminal blocks.

---

## 6. Power Calculations

**Coil power source:** `RELAY_PWR`, a locally-filtered branch of `VSYS_RAW_OUT` (ferrite bead `FB_RELAY_PWR1` + bulk capacitor `C_RELAY_BULK1`, see §7). `VSYS_RAW_OUT` itself remains unsourced pending the future battery-charger/VSYS milestone — this is the same, previously-disclosed state left by `04_RS485`, now with a second, larger consumer. This is flagged explicitly in §10 (Risks) as a requirement on that future rail's design.

**Per-channel coil current** (Finder 40.51.9, 12VDC coil, ~0.9W nominal sealed-coil power, representative figure — verify against the manufacturer datasheet at manufacturing release, per this project's established "class" component treatment):

```
I_coil = P_coil / V_coil = 0.9 W / 12 V ≈ 75 mA
```

**Worst-case simultaneous draw (all 5 channels energized at once):**

```
I_coils_total = 5 × 75 mA = 375 mA
I_LEDs_total  = 5 × ~2 mA = 10 mA
I_pulldowns   = 5 × (3.3V / 10kΩ) ≈ 1.65 mA   (only while GPIO drives HIGH; negligible)
─────────────────────────────────────────────
I_RELAY_PWR_worst_case ≈ 385 mA (steady-state) + coil inrush transient at turn-on
```

This ~385mA steady-state figure (plus inrush) is the **additional load this subsystem places on `VSYS_RAW_OUT`**, on top of whatever RS485 sensor power (`04_RS485`) already draws from the same net. Both draws must be accounted for when the VSYS/charger stage is finally sized — flagged as a cross-milestone note in §10.

**Voltage drop / dissipation in the driver path:** MOSFET R_DS(on) ≈ 100mΩ at I_coil = 75mA gives V_DS ≈ 7.5mV and P_MOSFET ≈ 0.56mW per channel — negligible, confirming the N-MOSFET choice imposes no meaningful voltage drop on the coil supply (unlike a BJT's ~0.2–0.3V V_CE(sat), which alone would be ~2–4% of the 12V rail per channel).

---

## 7. Protection Strategy

- **Flyback protection:** one diode per channel (`D_RELAY{n}_FLYBACK1`, Value `S1M_1A_1000V_SMA`, footprint `Diode_SMD:D_SMA`), cathode to `RELAY_PWR`, anode to the MOSFET-drain/coil-return node. Reverse-biased (and thus non-conducting, zero loss) during normal ON operation; conducts only during the turn-off inductive-kick transient, clamping the voltage spike and protecting the MOSFET's V_DS rating. A 1A-class rectifier is comfortably oversized relative to the ~75mA coil current it must carry during that transient.
- **Power filtering / noise suppression:** `RELAY_PWR` is derived from the shared `VSYS_RAW_OUT` trunk through a power-rated ferrite bead (`FB_RELAY_PWR1`, Value "Power Ferrite, 1A class", footprint `Inductor_SMD:L_1206_3216Metric` — a larger, higher-current-rated part than `FB_MCU1`'s small-signal 0603 bead used for VDDA filtering in `02_MCU`, sized for this subsystem's ~385mA worst-case draw) plus a local bulk capacitor (`C_RELAY_BULK1`, 22µF, `Capacitor_SMD:C_1210_3225Metric`) at the relay bank. This is a deliberate, explained deviation from `FB_MCU1`'s class: this ferrite/cap stage isolates relay coil switching transients (5 channels' worth of inrush/flyback activity) from the shared `VSYS_RAW_OUT` trunk, protecting the other subsystem that already depends on that same net for clean power — RS485 sensor supply (`04_RS485`). This mirrors the pattern already established for `VDDA` (isolated from `3V3_RAIL` via ferrite bead in `02_MCU`) and for `VIN_PROT` (derived from `DC_IN_RAW_P` via fusing in `01_power`): a named, filtered branch net rather than a bare tap.
- **Grounding strategy:** all coil-side circuitry (MOSFET source, pull-down resistor, status LED cathode, bulk capacitor return) shares the board's single unified GND plane, consistent with the whole design's one-GND-net philosophy (no AGND split, matching the reasoning already recorded in `02_MCU` §8). **Relay contacts (COM/NO/NC) are intentionally NOT connected to board GND** — the relay itself provides galvanic isolation between the low-voltage control circuit and whatever external circuit the contacts switch, which may be a completely different voltage domain (including mains). Tying the contact side to board GND would defeat this isolation and is a potential safety hazard if any channel switches a mains-referenced load; verified via netlist trace that no such connection exists (§9/§12).

---

## 8. Connector Pinout

Each channel gets its own 3-position screw terminal (`J_RELAY{n}1`, `Connector_Generic:Conn_01x03`, footprint `TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3-5.08_1x03_P5.08mm_Horizontal` — same Phoenix MKDS-1,5 family already used for RS485's field connectors in `04_RS485`, rated well above the relay's 10A contacts):

| Pin | Function | Relay pin |
|---|---|---|
| 1 | **COM** (common/pole) | 11 |
| 2 | **NO** (normally open) | 14 |
| 3 | **NC** (normally closed) | 12 |

Silkscreen labeling should print "COM / NO / NC" directly above pins 1/2/3 respectively (layout-stage artifact, specified here per this project's established documentation-first pattern for connector labeling — see `04_RS485`'s equivalent A/B/PWR/GND treatment).

---

## 9. Test Points

| Test point | Net | Purpose |
|---|---|---|
| `TP_RELAY{n}_CTRL1` (×5) | `RELAY{n}_CTRL` | Per-channel control-signal probe point, placed before the gate resistor so probing doesn't load the gate-drive timing |
| `TP_RELAY_PWR1` | `RELAY_PWR` | Local probe for the filtered relay coil supply, near the relay bank (production convenience — this bank sits far from `04_RS485`'s own `VSYS_RAW_OUT` connectors, so a local tap avoids requiring a technician to probe across the board) |
| `TP_RELAY_GND1` | `GND` | Local ground reference near the relay bank |

Production test coverage: with these three test-point classes, a functional test fixture can (a) drive each `RELAY{n}_CTRL` test point directly to verify independent channel switching without needing firmware, (b) confirm `RELAY_PWR` is present and within tolerance, and (c) verify local ground continuity — sufficient for a basic go/no-go production test of the relay driver stage independent of the MCU.

---

## 10. Risks

| ID | Risk | Status |
|---|---|---|
| R-RELAY-1 | `RELAY_PWR`/`VSYS_RAW_OUT` has no real source yet (same open item `04_RS485` already flagged) — this milestone adds a second, larger consumer (~385mA worst-case vs. RS485 sensor power's smaller draw) | Open — must be accounted for when the battery-charger/VSYS milestone is sized |
| R-RELAY-2 | Coil current (75mA/channel) is a representative figure for the Finder 40.51.9 12VDC "class"; not yet confirmed against a locked, purchased datasheet | Open — confirm at manufacturing release, same treatment as other "class" BOM entries on this board |
| R-RELAY-3 | Second-source qualification for the Finder 40.51 family not yet performed | Open (SWA-CST-004 pattern, consistent with other subsystems' Risk entries) |
| R-RELAY-4 | Relay driver zone thermal loading (5× coil dissipation + contact I²R at rated load) not yet assessed against real enclosure airflow | Open — flagged in the PCB floor-plan doc's relay-zone row; to be revisited at PCB layout |
| R-RELAY-5 | Physical spacing/creepage between the 5 relay channels (especially if any channel switches mains-referenced loads) has not been analyzed against IEC clearance requirements | Open — a PCB-layout-stage concern, not resolved by this schematic-capture milestone |

---

## 11. Recommendations

1. Confirm the Finder 40.51.9.012 datasheet's exact coil power/current figures before locking the BOM part number (R-RELAY-2).
2. When the VSYS/charger milestone is captured, size it against the combined `VSYS_RAW_OUT` draw of RS485 sensor power **and** this subsystem's ~385mA worst-case relay coil draw (R-RELAY-1).
3. At PCB layout, keep the relay bank in the Relay Driver Zone reserved by the floor-plan document, physically separated from the RF zone and the future sensor front-end zone (already reserved, see updated floor-plan §11), and give contact-side traces/pads appropriate creepage/clearance if any channel is expected to switch mains voltage (R-RELAY-5).
4. Treat contact-to-GND isolation as a hard constraint during any future layout or rework — do not add a "convenience" ground connection to COM/NO/NC pads.

---

## 12. ERC Results

Real `kicad-cli sch erc` (authoritative) and MCP `run_erc` (cross-check) agree: **94 total violations (47 errors, 47 warnings)**, down from the 99-violation baseline immediately before this milestone — a net reduction of 5, exactly matching the 5 previously-unconnected MCU pins (`PB12`, `PB13`, `PB14`, `PB15`, `PA15`) now wired. **Zero new violations were introduced by this milestone.**

| Class | Count | Disposition |
|---|---|---|
| Critical | 0 | — |
| Major | 0 | — |
| Minor | 47 errors (`pin_not_connected`) | 100% pre-existing: unconsumed MCU/LoRa-module GPIOs already reserved-but-unwired for other future subsystems (sensor front-end, SPI/expansion, user buttons ×2, LoRa module's unused GPIOs). None reference any relay-subsystem component. |
| Informational | 46 warnings (`endpoint_off_grid`) + 1 warning (`lib_symbol_mismatch`) | 100% pre-existing: the `endpoint_off_grid` set is the `02_MCU`-era grid-alignment item already explicitly deferred (see that milestone's §11); the `lib_symbol_mismatch` is the already-documented `THVD1450D` cosmetic warning from `04_RS485`. All 66 newly-placed relay-subsystem components (5× each of MOSFET, gate resistor, pull-down resistor, flyback diode, status LED, status resistor, control test point, relay, field connector, plus shared ferrite, bulk cap, and 2 shared test points, plus 17 new GND symbols) were placed on the established 1.27mm grid discipline used since `03_HMI` — **zero new grid warnings.** |

Independently verified via `generate_netlist` + `trace_netlist_connection` on every new node class (relay coil/contact pins, MOSFET all 3 pins, MCU control pins for channels 1 and 5, status LED branch, shared `RELAY_PWR`): every net matches the intended topology exactly, with no shorts, no cross-channel bleed, and confirmed contact-to-GND isolation (COM/NO/NC nets contain only the relay and its own field connector — never a GND symbol).

`SWAFarmNodeV1_erc.json` re-exported at 2026-07-31T02:29 reflecting this state.

---

## 13. Documentation Updates

- This document created.
- `Documentation/SWAFarmNodeV1_PCB_FloorPlan_and_LayerStrategy.md`: relay-driver row in the §11 region-reservation table updated from "Not started / Reserved (Future)" to "Captured" with real constraints; open-items count corrected from four to three not-yet-captured subsystems; top-of-document scope line updated to "six completed subsystems."
- `TODO.md`: new "Industrial Relay Output Subsystem" milestone entry added; "Relay output driver (5 channels)" line removed from the "Other Subsystems (not started)" list; new Tooling entry documenting a schematic-file-structure gotcha found during this milestone (see below).
- `02_MCU`'s GPIO allocation table (§7 of that document) intentionally **not** edited, per the same precedent already set by `04_RS485` and `05_LoRaWAN` when they consumed their own reserved pins — that table is treated as an immutable planning snapshot; as-built consumption is authoritatively recorded in each consuming subsystem's own design review document (this one, for the relay row).

### New tooling note (for TODO.md Tooling section)

This milestone's scale (66 new components, 104 net labels) made per-component MCP tool calls impractical, so the additions were generated by a script and spliced directly into the `.kicad_sch` file — a technique already used for targeted defect fixes in prior milestones, extended here to bulk capture. This surfaced a new, non-obvious file-structure fact: **`(lib_symbols ...)` closes far earlier in this file than the top-level `(sheet_instances ...)` block appears** — a large run of legacy verbose-format placed symbols (from early `01_power`/`02_MCU` capture) sits between the two. A splice keyed off the text immediately preceding `(sheet_instances ...)` lands inside the placed-symbol region, not inside `(lib_symbols ...)` — a bare `(symbol "Name" ...)` template inserted there is invalid as a direct child of `(kicad_sch ...)` and real `kicad-cli` rejects the whole file with an unhelpful "Failed to load schematic" (no line/reason given), while the MCP server's own lenient parser accepts it silently. A second, independent mistake compounded this during debugging: even once the correct splice point (the point where a string-aware, quote-respecting paren-depth counter confirms `lib_symbols`' true closing paren, found here at the first bare `)` immediately before the first placed `(junction ...)` element) was located, new content must be inserted **before** that closing paren, not after it — inserting after silently places the new symbol templates outside `lib_symbols` entirely. Both mistakes produced syntactically-balanced, MCP-tool-readable files that real `kicad-cli` still refused to load. Lesson for future bulk direct-file edits: (1) locate `lib_symbols`' true end via a string-aware paren-depth counter, never a text-adjacency guess; (2) always verify with real `kicad-cli sch erc`, never the MCP tool's own parser alone, before trusting a splice; (3) when in doubt, bisect with a minimal, known-good, self-sourced test insertion before debugging library-sourced content.
