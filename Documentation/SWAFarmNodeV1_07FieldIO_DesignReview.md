# SWAFarm Node V1 — Step 07: Field I/O & Sensor Interface Subsystem — Design Review

**Status:** Captured, ERC-clean against baseline (no new violations). Awaiting approval before Step 08.
**Date:** 2026-07-31

---

## 1. Executive Summary

This milestone reviewed the five RS485 sensor field connectors already captured in `04_RS485` and found they already satisfy the connector/topology requirement (one shared bus, five field-wiring access points, each exposing RS485 A/B, Sensor Power, and Ground) — **no new or duplicate connectors were created**. What was missing, and is the real deliverable of this milestone, is protection on the Sensor Power line: today each connector's Sensor Power pin sits directly on the shared `VSYS_RAW_OUT` trunk with zero fusing or transient protection, meaning a short on any single sensor's power wiring would pull down the rail for all five sensors and offer no clamping against field-induced surge/ESD. This milestone closes that gap: a PTC fuse per connector (isolating individual field-wiring faults, mirroring the existing RS485 A/B fusing pattern exactly) plus one shared unidirectional TVS on the trunk (surge/ESD/crude reverse-polarity clamping). The sensor current budget needed to size the fuse (100mA/sensor, 500mA total worst-case) was confirmed with the user before implementation, since no such figure exists anywhere in the requirements documentation — flagged explicitly rather than guessed (§6). No changes were made to RS485 topology, MCU GPIO allocation, or any other previously-approved circuitry.

---

## 2. Field Interface Architecture

```
                         VSYS_RAW_OUT (shared trunk, unsourced — see §6)
                                │
                   D_SENSOR_PWR_TVS1 (shared, once)
                                │
        ┌───────────┬───────────┼───────────┬───────────┐
   F_RS485_PWR1  F_RS485_PWR2  F_RS485_PWR3  F_RS485_PWR4  F_RS485_PWR5
        │              │              │              │              │
  VSYS_RAW_OUT1  VSYS_RAW_OUT2  VSYS_RAW_OUT3  VSYS_RAW_OUT4  VSYS_RAW_OUT5
        │              │              │              │              │
  J_RS485_SENSOR1  ...SENSOR2...  ...SENSOR3...  ...SENSOR4...  ...SENSOR5

  (RS485 A/B: unchanged from 04_RS485 — same shared bus, same per-drop
   F_RS485_A/Bn fusing, same shared D_RS485_TVS_A1/B1, one THVD1450D transceiver)
```

This directly mirrors the RS485 A/B protection topology already established in `04_RS485`: one shared protective element (TVS) placed once upstream, per-drop fuses isolating individual field-cable faults, and per-connector net segments (`VSYS_RAW_OUTn`) analogous to `RS485_A_RAWn`/`RS485_B_RAWn`. Extending an already-proven pattern to the one pin type that lacked it, rather than inventing a new protection philosophy, was a deliberate consistency choice.

---

## 3. Connector Selection

**No new connectors were added.** The five field connectors from `04_RS485` (`J_RS485_SENSOR1`–`5`, `Connector_Generic:Conn_01x04`, footprint `TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-4-5.08_1x04_P5.08mm_Horizontal`) already satisfy Section 1 of this milestone's requirements in full: industrial screw-terminal connectors, all five wired to the one shared RS485 bus (confirmed no second transceiver exists — `U_RS485_1` remains the only `THVD1450D` on the board), each exposing RS485 A / RS485 B / Sensor Power / Ground. Re-implementing them here would have violated "never duplicate documentation" and "reuse existing conventions" — this milestone instead reviews, protects, and formally documents what already exists.

---

## 4. Pinout Tables

| Pin | Function | Net (per connector `n`, 1–5) |
|---|---|---|
| 1 | RS485 A | `RS485_A_RAWn` → `F_RS485_An` → shared `RS485_A` |
| 2 | RS485 B | `RS485_B_RAWn` → `F_RS485_Bn` → shared `RS485_B` |
| 3 | Sensor Power | `VSYS_RAW_OUTn` → `F_RS485_PWRn` → shared `VSYS_RAW_OUT` **(new this milestone)** |
| 4 | Ground | `GND` (direct, unprotected — see §7) |

| Connector | Field label | Reference |
|---|---|---|
| Sensor 1 | "Sensor 1" | `J_RS485_SENSOR1` |
| Sensor 2 | "Sensor 2" | `J_RS485_SENSOR2` |
| Sensor 3 | "Sensor 3" | `J_RS485_SENSOR3` |
| Sensor 4 | "Sensor 4" | `J_RS485_SENSOR4` |
| Sensor 5 | "Sensor 5" | `J_RS485_SENSOR5` |

Numbering matches physical left-to-right board position (X = 50.8, 101.6, 152.4, 203.2, 254.0mm — 50.8mm pitch, unchanged from `04_RS485`).

---

## 5. Power Distribution

**Sensor Supply Voltage:** `VSYS_RAW_OUT`, the raw ~9–15V battery-tracking rail defined at the architecture level (`SWAFarmNodeV1_PowerSupply_Design.md`) and already reused verbatim for this exact purpose since `04_RS485`. This is **not yet a physically sourced rail** — the charger/VSYS stage (BQ25792) that would actually drive it remains an unbuilt, deferred milestone (tracked in `TODO.md` since `01_power`). This subsystem continues that same, previously-disclosed scoping: the net, its protection, and its per-drop segmentation are fully built out now so no rework is needed once the source exists.

**Missing requirement, resolved with the user before implementation:** neither `hardware_requirements.md`, `power_management.md`, nor any other `.ai/knowledge` document specifies a per-sensor current draw, expected sensor count, or total sensor power budget — and no real sensor models have been selected yet. Rather than guess, this was raised explicitly; the user approved a planning ceiling of **100mA per sensor, 500mA total worst-case (all 5 sensors simultaneously active)**. This figure is used below to size the fuse and is documented as an assumption, not a measured or datasheet-derived value — flagged again in §10 (Risks) for confirmation once real sensors are selected.

**Filtering:** none added at this distribution point beyond the new TVS (§7). Bulk filtering for the shared `VSYS_RAW_OUT` trunk was already addressed at its other major consumer (`FB_RELAY_PWR1` + `C_RELAY_BULK1`, `06_Relay`); duplicating a second filter stage here for the same shared net would be redundant. If per-sensor supply noise proves an issue in the field, local decoupling at each sensor is the sensor manufacturer's/installer's responsibility, consistent with how a distribution trunk is normally treated.

---

## 6. Current Calculations

Using the approved 100mA/sensor planning figure:

```
I_per_sensor (planning ceiling)     = 100 mA
I_total_worst_case (5 sensors)      = 5 × 100 mA = 500 mA
```

**Connector current rating:** the Phoenix MKDS-1,5 series terminal block accepts up to 1.5mm² (16AWG) wire and is rated in the 10–17.5A class per contact (family datasheet) — several orders of magnitude above the 100mA/sensor planning figure. The connector's mechanical/contact rating is not a limiting factor for this application; it was originally selected in `04_RS485` for RS485 signal-level use and, incidentally, has enormous margin for DC power distribution too.

**Fuse sizing:** `F_RS485_PWR{n}` reuses the exact same PTC part class already qualified for `F_RS485_A/Bn` (0.2A / 200mA hold current, `Fuse:Fuse_1206_3216Metric`). At a 100mA/sensor planning load this gives ~2× margin between normal operating current and the fuse's hold rating (typical PTC trip current ≈ 2× hold, so trip ≈ 400mA) — enough margin to avoid nuisance tripping under normal load while still isolating a genuinely faulted drop well below the point it could damage the shared trunk or starve the other four sensors.

**Voltage drop:** not calculated in absolute terms since `VSYS_RAW_OUT` has no real source impedance yet (no charger stage built). Qualitatively: PTC fuses in their un-tripped state add a small series resistance (typically 0.5–1.5Ω for this fuse class) — at 100mA that is ≤150mV per drop, negligible against a 9–15V rail (<2%). This should be re-verified against the actual selected PTC part's datasheet resistance once the charger/VSYS milestone locks a real source and cable-run lengths are known (Risk R-FIO-2).

**Total demand vs. supply:** this milestone establishes the *demand-side* budget (500mA worst-case) that the future VSYS/charger milestone must supply alongside the ~385mA worst-case already disclosed by `06_Relay` for relay coils. Combined disclosed `VSYS_RAW_OUT` demand to date: **≈885mA worst-case** (500mA sensors + 385mA relays). This running total is the single most important number to carry into the charger/VSYS sizing milestone and is repeated in `TODO.md`.

---

## 7. Protection Strategy

- **Over-current (new this milestone):** `F_RS485_PWR{n}` ×5, PTC resettable, 0.2A hold — one per connector, in series between the shared trunk and that connector's Sensor Power pin. Isolates a single faulted field drop (e.g., a pinched or shorted sensor cable) without taking down power to the other four sensors, and is field-resettable by the technician who caused or discovers the fault — directly serving "field maintenance" per the same reasoning already applied to RS485 A/B in `04_RS485`.
- **Surge/ESD (new this milestone):** `D_SENSOR_PWR_TVS1`, one shared TVS on the trunk upstream of all five fuses (mirrors the RS485 A/B shared-TVS-once placement — one part protects the whole distribution point since per-drop fusing already isolates individual faults, avoiding 5× redundant parts).
- **Reverse polarity:** evaluated and deliberately handled via the same TVS rather than a dedicated series diode or MOSFET switch. `D_SENSOR_PWR_TVS1`'s selected part class (`SMBJ18A`, the "A" suffix denoting a genuinely **unidirectional** device, as opposed to the bidirectional `SMBJ_class_RS485` used on the differential A/B lines) is oriented cathode-toward-`VSYS_RAW_OUT`, anode-toward-GND: in normal operation it blocks up to its 18V standoff (comfortable margin above the 15V top of `VSYS_RAW_OUT`'s range) and does nothing; if a field technician miswires a connector such that reverse voltage appears on the Sensor Power pin, the same part conducts near-immediately in the forward direction (like an ordinary diode), clamping the fault and letting the in-series PTC fuse clear it. This is a deliberately lighter-weight approach than Q1's active MOSFET reverse-polarity switch in `01_power` — appropriate given Q1 protects the board's single main input, while these are five much lower-power field *outputs* where a passive clamp-and-fuse pair is the standard, proportionate industrial practice. The KiCad schematic symbol used (`Device:D_TVS_Filled`) is the same generic part already used for the bidirectional RS485 TVS, per this project's symbol-reuse convention — polarity is a selected-part and orientation property, not a distinct symbol, and is called out explicitly here since it matters for this instance unlike the symmetric RS485 case.
- **Ground pin:** deliberately left unprotected — pin 4 is the common return reference; adding a fuse or clamp in series with a ground return would be actively wrong (defeats its purpose, no precedent anywhere on this board).
- **RS485 A/B protection:** unchanged from `04_RS485` — reviewed and reconfirmed correct, not modified.

---

## 8. Mechanical Considerations

Per the explicit direction to reserve physical space around each field connector for terminal blocks, cable strain relief, and labeling — recorded here as **PCB-layout-stage constraints** (no `.kicad_pcb` placement or routing has been touched, consistent with the standing "do not begin PCB routing" rule):

- **Connector pitch:** 50.8mm between adjacent sensor connectors (unchanged from `04_RS485`). The Phoenix MKDS-1,5-4-5.08 body is ≈20.3mm wide (4 positions × 5.08mm) plus mounting flanges; at 50.8mm pitch this leaves ≈25–28mm of clear gap between adjacent connector bodies — enough for wire dressing and a silkscreen label between them without crowding.
- **Cable approach clearance:** reserve a minimum ≈20mm of unobstructed board area beyond each connector's wire-entry face for cable bend radius (typical minimum bend radius for 16–18AWG stranded industrial cable is 4–6× cable OD) — no other component or the board edge should be placed inside this zone.
- **Tool access clearance:** reserve ≈15mm of clear vertical access above each terminal position for flat-blade screwdriver insertion/removal (standard for screw-actuated terminal blocks of this class) — do not stack taller components directly above the connector row.
- **Strain relief:** if the enclosure design (future milestone) uses cable glands at the wall, the connector-to-gland cable run must be included in the enclosure's own cable-length budget; this board-level reservation only guarantees the board doesn't itself obstruct strain relief at the connector.
- **Labeling:** reserve ≈5×2mm of silkscreen area per connector for its "Sensor N" text, positioned so it remains legible after the connector and any strain-relief hardware are mated (typically above or below the connector body, not on it).
- **Same reservations apply to the relay field connectors** (`J_RELAY1`–`5`, `06_Relay`) for consistency — both connector families are field-wired, serviced, and labeled the same way.

This is recorded as a floor-plan-level constraint (§13, `SWAFarmNodeV1_PCB_FloorPlan_and_LayerStrategy.md` updated accordingly) rather than an enforced dimension, since no board outline exists yet — per that document's own stated purpose, it is the input to a future outline decision, not fit to one chosen arbitrarily.

---

## 9. Manufacturing Considerations

- All new components (5× PTC fuse, 1× TVS) reuse **already-qualified part classes** already present in the BOM from `04_RS485` — zero new footprints or unique part numbers introduced, minimizing AVL/procurement impact.
- Pluggable screw-terminal connectors (unchanged from `04_RS485`) support blind mating and tool-free field replacement of the mating plug, consistent with `SWA-HWR-305` ("field-serviceable and polarity-safe").
- No new SMT placement complexity: fuses and TVS are standard 1206/SMB packages already used elsewhere on this board.

---

## 10. Risks

| ID | Risk | Status |
|---|---|---|
| R-FIO-1 | Sensor current budget (100mA/sensor, 500mA total) is a planning assumption approved by the user, not a measured or datasheet-derived figure — no real sensors selected yet | Open — confirm against actual sensor models once selected; revisit fuse sizing if materially different |
| R-FIO-2 | `VSYS_RAW_OUT` remains unsourced; combined disclosed demand from this milestone + `06_Relay` is now ≈885mA worst-case — this is the number the future charger/VSYS milestone must be sized against | Open — carried forward in `TODO.md`, same disclosure pattern as `04_RS485`'s original flag |
| R-FIO-3 | PTC fuse resistance/trip-current tolerance not yet verified against a locked datasheet for real voltage-drop calculation | Open — same "class" component treatment as other fuses/passives on this board |
| R-FIO-4 | Field-connector mechanical clearances (§8) are recorded constraints, not yet validated against a real enclosure or cable gland selection | Open — revisit once enclosure/mechanical milestone begins |

---

## 11. ERC Results

Real `kicad-cli sch erc` and MCP `run_erc` agree: **94 violations (47 errors, 47 warnings) — identical to the pre-milestone baseline. Zero new violations.** None of the 7 new components (`F_RS485_PWR1`–`5`, `D_SENSOR_PWR_TVS1`, `#PWR59`) appear anywhere in the violation list. All new pin positions were placed on the established 1.27mm grid (verified: fuse row at Y=482.6, TVS at X=147.32/Y=495.3, all values exact multiples of the grid step) — zero new grid warnings.

Independently verified via `generate_netlist` + `trace_netlist_connection`: `J_RS485_SENSOR1`'s Sensor Power pin now sits on its own isolated `VSYS_RAW_OUT1` net joined only to `F_RS485_PWR1` (confirmed the same construction applies identically to connectors 2–5); `D_SENSOR_PWR_TVS1` correctly bridges the shared `VSYS_RAW_OUT` trunk (joined with all 5 fuses' bus-side pins and the existing `FB_RELAY_PWR1` tap from `06_Relay`) to `GND`. No shorts, no cross-connector bleed, RS485 A/B and the transceiver confirmed untouched.

`SWAFarmNodeV1_erc.json` re-exported reflecting this state.

---

## 12. Documentation Updates

- This document created.
- `TODO.md`: new "Field I/O & Sensor Interface Subsystem" milestone entry added, including the running `VSYS_RAW_OUT` combined-demand total.
- `Documentation/SWAFarmNodeV1_PCB_FloorPlan_and_LayerStrategy.md`: RS485 zone row and connector/mechanical placement section (§9) updated with the field-connector clearance reservations from §8 above (approach clearance, tool access, strain relief, labeling), applied to both the RS485 sensor and relay connector families.
- No BOM CSV update — consistent with established precedent that `SWAFarmNodeV1_PowerSupply_BOM.csv` covers only `01_power`; subsystems `02`–`07` record their own component/part decisions in their respective design review documents, not in that file.
