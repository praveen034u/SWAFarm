# SWAFarm NODE_CORE — BOM Notes

**BOM file:** `SWAFarmNodeV1_NodeCore_BOM.csv`
**Generated:** 2026-08-01, from the live schematic (`Hardware/SWAFarmNodeV1/SWAFarmNodeV1.kicad_sch`, 181 components, Steps 1-8 of the ESP32-S3 NODE_CORE rebuild + the 2026-08-01 design audit fixes below).
**Source of truth for part numbers:** `NodeForRefrence.csv` (actual `.xlsx`), `BOM` sheet, `NODE_CORE` rows — 38 line items with real manufacturer/MPN data, cross-referenced by function against this project's actual schematic components.

**Scope note (LoRaWAN):** the LoRaWAN module bay went through 3 revisions on 2026-08-01 — captured DNP (optional), fully removed per user decision, then re-added **fully populated** per a follow-up request for an India-region module with ~5km+ theoretical range. `U_LORA1` is the `RAK3172-xx-8-SM-xI` variant (its own stock-symbol Description field reads "RU864/**IN865**/EU868" — IN865 is India's LoRaWAN band). Link-budget calculation and ESP32-S3 compatibility confirmation are in the `U_LORA1` BOM row below and in the Step 5 design review. See `TODO.md` for the full revision history.

**2026-08-01 design audit fixes (2 critical findings, both resolved):** a full 11-category engineering audit (datasheet verification, power rail audit, connectivity review, connector/pull-up/protection/RF/test-point checks, BOM validation) surfaced two real defects, both now fixed and re-verified (0 ERC errors, 0 DRC violations):
1. **Valve rail overcurrent risk (power rail audit).** `V12_SW`, the TPS26600PWP eFuse's 2A-rated output, fed both the 5V buck regulator AND all 6 `DRV8871` valve drivers (each capable of 2.5-3.6A pulses for latching solenoids) — a single valve pulse could exceed the eFuse's silicon current limit. Fixed by giving the valve rail its own branch, `V12_VALVE`, tapped from `V12_PROT` upstream of the eFuse through a new dedicated fuse `F2`; `F1` (input fuse) resized 1.5A → 5A to cover the new worst-case local draw. See `F1`/`F2`/`U_DRV`/`C_VMDEC`/`C_VALVEBULK1` BOM rows below.
2. **Sensor front-end 0-10V divider math (datasheet/connectivity review).** The shared `R_SER`(100k)+`R_BURDEN`(150R) network gave only ~15mV at the ADC for a 10V input (unusable), and also made the 4-20mA loop's compliance voltage physically impossible (100k+150R in series needs >2000V at 20mA). Fixed with a jumper-selectable dual network per channel (industry-standard universal analog input practice): `R_SER` revalued to 232k (paired with new `R_VBOT`, 100k) for a proper 0-10V→3.01V divider, gated in/out of circuit by new jumpers `JP_VBYP`/`JP_IGND` per channel. See `R_SER`/`R_VBOT`/`R_BURDEN`/`JP_VBYP`/`JP_IGND` BOM rows below.

## How to read the BOM

- **RefDes / Qty**: grouped by identical Value + Footprint, so e.g. all twenty 100nF/0603 decoupling caps are one line with 20 reference designators, not 20 separate rows.
- **Manufacturer / MPN**: filled in wherever a component matches a real `NodeForRefrence.csv` BOM row (by function, not just by ref name). Left blank for genuinely generic passives (pull-ups, decoupling, gate resistors) that the spec doesn't itemize individually — these were never spec'd to a specific MPN and shouldn't be assigned a fabricated one.
- **Spec_Component_ID**: the matching `CMP_*` identifier from the reference spec, for traceability back to `NodeForRefrence.csv`.
- **Notes**: flags every disclosed substitution, package variant, value mismatch, or placeholder — same disclosure discipline used throughout this project's design reviews. Nothing in this BOM is silently different from the spec without a note explaining why.

## Real MPN matches (17 lines, exact)

Q1, U1, U3, U_MCU1, D_RS485PROT1/2, CMC_RS485_1/2, R_BIASA1/B1, J_SENSOR_SIG1/RET1, J_VALVE_OUT1_1/OUT2_1, C_VALVEBULK1, U_DRV1-6, D_PWR1, D_LINK1, R_PWR1/LINK1, R_BURDEN1-6, J_LORASMA1, U_LORA1 (part number matches; not itemized with a spec `CMP_*` ID since NODE_CORE's LoRa was originally PROVISIONAL/optional in the reference spec).

**F1 and the new F2** are cited by real PTC *family/class* (Bourns MF-RG1812 series / Littelfuse 1812L series) rather than a single exact MPN, pending final hold-current selection against the M12 connector's real current rating (see the footprint-placeholder note below) — moved out of the exact-match list during the 2026-08-01 resize.

## Disclosed substitutions (carried over from the design reviews)

| Component | Spec part | Used part | Why |
|---|---|---|---|
| U2 (12V→5V buck) | TPS54531DDAR | TPS54561DDAR | No exact stock KiCad symbol for TPS54531; same TI SWIFT family, 5A vs 3.5A (headroom) |
| U_ISO1 (RS485 isolator) | ISO1410BDWR | ISO7761DW | Real stock 6-channel TI isolator, more headroom than the 2fwd+1rev actually used |
| U_ISODCDC1 (isolated DC-DC) | NXE1S0505MC | MEE1S0505SC | Real, stock, function-identical Murata part (5V/5V/1W/SIP) |
| U_RS485_TX1 (transceiver) | THVD1450DR ×2 | THVD1450DR ×1 | A 2-transceiver design hit a real ERC `pin_to_pin` conflict (2 active RO outputs on 1 isolator channel); resolved to 1 shared transceiver fanned out to all 3 M12 connectors |
| D_CLHI/D_CLLO (sensor clamp) | BAV99LT1G ×6 (dual-diode) | 2× discrete diode ×6 channels (12 total) | Same bipolar-clamp function, implemented as 2 discrete parts instead of fighting BAV99's common-anode pinout for this specific topology |
| U_VALVEEXP1 (SPI expander) | MCP23S17-E/SS (SSOP-28) | MCP23S17-E/SO (SOIC-28W) | Same die/function, different package — no functional difference, confirm preferred package before BOM lock |

## Value mismatches to resolve before BOM lock

- **L1** (12V→5V buck inductor): schematic placeholder is 3.3µH (sized by rule-of-thumb buck formula); the spec's recommended real part (Wurth 74437368100) is a 10µH-class inductor. These need to be reconciled together with the compensation network — not yet done, flagged in the Step 1 design review too.
- **D1** (input TVS): schematic uses SMBJ18CA (18V clamp); the spec has two BOM rows that appear to describe the same physical protection diode differently (`CMP_INPUT_TVS` = SMBJ24A, `CMP_SURGE_PROTECTOR` = SMAJ24A) — worth resolving with the spec's own author which is authoritative, and reconfirming the target clamp voltage against the real 12V rail transient spec.

## Not itemized in the spec BOM (this project's own additions)

- **J_USB1**: native USB-C programming port (per `Final_MCU_Pin_Map`'s `USB_DM`/`USB_DP` GPIO rows, but no BOM line item existed for the connector itself).
- **J_PROG1**: optional external debug UART header.
- **D_FLT1** + its resistor: FAULT LED (per `Final_MCU_Pin_Map`'s `LED_FAULT`/GPIO40 row — the spec's BOM only priced PWR+LINK LEDs, 2 of them, not 3).

## Intentionally NOT populated (resolved DNP contradiction — not a gap)

Per the Step 7 design review: `NodeForRefrence.csv`'s `BOM`/`Device_Allocation` sheets list these as mandatory (qty 6 each), but `DNP_Optional_Parts` explicitly marks all three **DNP** with dated rationale (superseded by the `DRV8871`'s integrated freewheeling diodes, internal current limit, and thermal shutdown). `DNP_Optional_Parts` was treated as authoritative, so **none of these appear in the schematic or this BOM at all**:

- `CMP_VALVE_FLYBACK_DIODE_CH` (onsemi ES1D, qty 6)
- `CMP_VALVE_GATE_NETWORK_CH` (Yageo RC0603FR-07100RL, qty 6)
- `CMP_VALVE_CURRENT_SENSE_CH` (Bourns CSS2H-2512R-L100F, qty 6)

## Spec BOM lines with no corresponding schematic component (open gap, not yet actioned)

- **`CMP_ESD_ARRAY`** (Nexperia PESD2CANFD24VTQ, qty 4) — a general multi-channel ESD array the spec calls for at unspecified port(s). Not implemented; this design's protection is per-subsystem instead (SM712 on RS485, discrete diode clamps on sensors, TVS on power input). Worth a follow-up review to decide whether additional ESD hardening is needed at any specific connector before production.
- **`CMP_VALVE_LINE_CLAMP`** (Littelfuse SMBJ33A, qty 6) — a per-channel valve line clamp, separate from the 3 DNP items above. Not currently in the schematic. Given the DRV8871's own internal protection already covers switching transients, this may also be a candidate for DNP, but it wasn't explicitly addressed in the DNP resolution — flagged for team review, not assumed.

## Footprint placeholders (must resolve before Gerber export)

All 5 M12 connectors (`J1`, `J_OUT1`, `J_RS485_IN1/OUT1/LOC1`) currently use generic THT pin-header footprints as placeholders for schematic/PCB floor-planning purposes — the reference spec's own `Footprint_Library_Map` marks real M12 footprints `PENDING_PCB_ENGINEER`. These must be swapped to real M12 A/5P-coded panel-mount footprints before fabrication.
