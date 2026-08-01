# SWAFarm NODE_CORE — Step 1: Power Input, Protection & Power Chain — Design Review

**Date:** 2026-07-31
**Milestone:** Step 1 of the ESP32-S3 NODE_CORE rebuild (see `C:\Users\prave\.claude\plans\moonlit-napping-snowglobe.md`)
**Status:** Schematic captured, ERC-clean (0 errors, 1 expected/documented warning), netlist-verified.

## 1. Scope

This is the first milestone of the full NODE_CORE rebuild that replaces the archived STM32L462-based "SWAFarm Node V1" design (see `Documentation/archive_stm32/`). It implements the field power entry, protection, and two-stage regulation chain specified by the `NodeForRefrence.csv` reference spec's `NODE_CORE` rows:

12V field power in → PTC fuse + TVS surge clamp → self-biased low-side NMOS reverse-polarity protection → daisy-chain pass-through to the next node → `TPS26600PWP` eFuse (UVLO/OVP/current-limit) → `TPS54561`-class 12V→5V buck → `TPS563201` 5V→3.3V buck.

Not in scope (later milestones per the plan): MCU, RS485, LoRa, sensor front-end, valve drivers, PCB placement/routing.

## 2. Architecture

```
J1 (M12 4P, power in)
  Pin1 +12V ---> F1 (PTC fuse) ---> V12_PROT ---+--> D1 (TVS, to GND)
  Pin2 GND(field) ------------------------------|--> Q1 Drain
  Pin3 SHIELD -----------------------------------> GND

Q1 (low-side self-biased NMOS, reverse-polarity protection)
  Gate  <- R_gate1 <- V12_PROT   (self-bias, same topology as archived 01_power's Q1)
  Source -> GND (system reference — isolated from field return until Q1 conducts)
  Drain  <- DC_IN_RAW_N (J1 pin 2)

J_OUT (M12 4P, power out / daisy-chain)
  Pin1 <- V12_PROT   Pin2/3 <- GND      (passes this node's fused+surge-clamped rail
                                          downstream; each node's own Q1 handles its
                                          own local reverse-polarity risk)

U1 TPS26600PWP (eFuse: UVLO ~9.1V, OVP ~16V, auto-retry on fault)
  IN <- V12_PROT        OUT -> V12_SW (feeds both bucks)
  UVLO/OVP <- resistor dividers from V12_PROT
  MODE -> GND (auto-retry, not latch-off — unattended field operation)
  ~SHDN <- pulled up to V12_PROT (always-enabled, no MCU control reserved in spec)
  ILIM/dVdT -> sizing resistor/cap to GND (reasoned defaults, TBD-flagged)
  IMON -> burden resistor + TP (diagnostic only, not wired to MCU — no GPIO reserved)
  ~FLT -> pulled up to V5_RAIL + TP (diagnostic only, not wired to MCU)

U2 TPS54561 (12V->5V buck, substitutes TPS54531)
  VIN <- V12_SW   SW -> L1 -> V5_RAIL   EN <- UVLO divider from V12_SW (~10V threshold)
  FB <- divider from V5_RAIL (0.8V ref)   PWRGD -> LED + pull-up + TP

U3 TPS563201 (5V->3.3V buck, exact stock part)
  VIN <- V5_RAIL   SW -> L2 -> V3V3_RAIL   EN <- pull-up to V5_RAIL (always-on)
  VFB <- divider from V3V3_RAIL (~0.768V ref)   status LED on V3V3_RAIL (no PG pin on this part)
```

## 3. Component substitutions (disclosed, same precedent as LT8609A→LT8610AC / BQ25792→BQ25798 in the archived build)

| Spec part | Used part | Why |
|---|---|---|
| TPS54531DDAR | **TPS54561** (WSON-10) | No exact TPS54531 stock KiCad symbol exists. TPS54561 is the same TI SWIFT integrated-FET family, 5A vs. the spec's 3.5A (headroom, not a downgrade). Package differs (WSON-10 vs. SO-8 PowerPAD) — flagged for BOM/footprint confirmation. |
| NXE1S0505MC, ISO1410 | *(not yet needed — Step 4)* | Deferred; noted here only because both were verified available during planning (`MEE1S0505SC`, `ISO776x`-class). |

`TPS26600PWP` and `TPS563201` are exact/functionally-exact stock parts (TPS563201 is `extends "TPS562200"` in the stock library; per the same fix used for `THVD1450D` in the archived `04_RS485` milestone, the schematic carries a self-contained flattened copy rather than relying on the inheritance chain, which the MCP/KiCad symbol-cache tooling doesn't resolve reliably).

## 4. Reasoned-default / TBD component values (disclosed, not blocking)

`Layout_Rules` and most passive sizing are not specified numerically anywhere in the reference spec. The following are planning-level defaults, explicitly flagged for datasheet/simulation confirmation before fabrication (same discipline as the archived build's RT/ILIM/PROG resistor values):

- `R_UVLO1`/`R_UVLO2` (64.9k/10k): eFuse UVLO ≈ 9.1V trip point (rising), assuming a 1.2V reference — **confirm against TPS2660x datasheet formula**.
- `R_OVP1`/`R_OVP2` (124k/10k): eFuse OVP ≈ 16V trip point — **confirm against datasheet formula**.
- `R_ILIM1` (20k, `_TBD` suffix in Value): eFuse current limit — sized for an assumed ~3A-class limit, **not calculated from the real TPS2660x ILIM formula (not available offline)**.
- `C_DVDT1` (1nF, `_TBD`): eFuse inrush slew-rate cap — placeholder.
- `R_RT1` (100k, `_TBD`): buck1 switching-frequency-set resistor — placeholder for a ~500kHz-class default.
- `R_COMP1`/`C_COMP1` (10k/2.2nF, `_TBD`): buck1 Type-II compensation — **requires a real loop-stability calculation against the final L1/C_OUT2 values**, not just a component-count placeholder.
- `C_SS1` (10nF, `_TBD`): buck1 soft-start timing cap.
- `R_EN1A1` (73.2k, `_TBD`): buck1 UVLO-style enable divider, ~10V threshold on V12_SW.
- `L1` (3.3µH, `_TBD`), `L2` (2.2µH, `_TBD`): power inductor values sized by rule-of-thumb buck formula, not a verified ripple-current calc. Footprints (`L_Bourns-SRN6028`, `L_Bourns-SRN4018`) are real, stocked KiCad footprints chosen for approximate current class — **exact part number pending real load-current confirmation**.

None of these block schematic capture or ERC; all are flagged the same way the archived project flagged LT8610AC's RT resistor and BQ25798's ILIM/PROG resistors — as pre-fabrication datasheet-confirmation items.

## 5. ERC results

Real `kicad-cli sch erc` (not just the MCP tool): **0 errors, 1 warning.**

The one warning — `lib_symbol_mismatch` on U3 (`TPS563201` doesn't match the library's copy) — is **expected and documented**, for the same reason as `04_RS485`'s `THVD1450D` warning: the schematic carries a self-contained, flattened copy of the symbol (see §3) rather than depending on KiCad's `extends` inheritance chain, which existing tooling does not reliably resolve. The schematic's copy is authoritative and pin-verified.

Independently verified via `generate_netlist` (real `kicad-cli sch export netlist --format kicadxml`) + `trace_netlist_connection` on `Q1` (confirms the low-side self-biased reverse-polarity topology matches the archived, proven `01_power` pattern exactly: gate self-biased from `V12_PROT` through `R_gate1`, source on system `GND`, drain on the raw field return `DC_IN_RAW_N`), `U1` (confirms eFuse IN/OUT/UVLO/OVP/MODE/SHDN/ILIM/dVdT/IMON/FLT all land on the intended nets, NC pins 4/13 correctly isolated), and `U2` (confirms buck1's BOOT-SW bootstrap, FB/EN dividers, COMP/SS/RT networks, and PWRGD-LED path all match the intended topology).

## 6. Reference designators, test points, and power flags

New scheme (no prior precedent from the spec — `Final_Component_RefDes`/`Test_Point_Map` are placeholder-only, per the earlier extraction): component prefixes follow the archived project's own convention (`U`=IC, `Q`=MOSFET, `D`=diode/LED, `F`=fuse, `J`=connector, `R`/`C`/`L`=passives), disambiguated by function suffix (`_gate`, `_UVLO`, `_FB`, etc.) where more than one instance of a prefix exists in the same net role.

Test points: `TP_12V_SW1`, `TP_IMON1`, `TP_FLT1`, `TP_5V1`, `TP_PG1`, `TP_3V3`, `TP_GND1` — one per key rail/diagnostic signal, matching the archived project's per-rail test point convention.

Power flags: 5 `PWR_FLAG`s (`DC_IN_RAW_P`, `GND`, `V12_PROT`, `V5_RAIL`, `V3V3_RAIL`) — required because KiCad's ERC `power_pin_not_driven` check is per-exact-net and does not trace through passive components (fuses, inductors); a rail on the *far side* of a fuse or inductor from its true source needs its own flag even though it's obviously "the same power," electrically. Exactly the same requirement the archived `01_power` hit on `GND`/`VIN_PROT` (`#FLG01`/`#FLG02`).

## 7. Known gaps / open items for later milestones or pre-fabrication review

- eFuse `ILIM`/`dVdT`/buck compensation values are placeholders (§4) — need real datasheet-formula/loop-stability confirmation before BOM release.
- `IMON` and `~FLT` diagnostic outputs are test-point-only, not wired to the MCU — the spec's `Final_MCU_Pin_Map` (NODE_CORE rows) does not reserve a GPIO for either. Revisit once Step 2 (MCU) is captured, in case a spare ADC/GPIO makes sense to add.
- M12 connector footprints are intentionally left blank (schematic-level connectivity only) — the reference spec's own `Footprint_Library_Map` marks M12 footprints `PENDING_PCB_ENGINEER`. **This must be resolved before Step 8 (PCB placement)** — leaving it blank silently caused a real defect once already in this project (`J2`'s empty footprint in the archived build, caught only during Step 09's pre-placement verification pass).
- `.kicad_pcb` still contains the Arduino_Mega template's 13 placeholder footprints (from `create_kicad_project`'s template-copy mechanism) — harmless at this stage since Step 1 is schematic-only, but must be stripped before Step 8, same as `setup_pcb_layout`'s placeholder content was stripped for the archived build.
- Reverse-polarity/eFuse/buck part numbers (`IPD50N06S4L-16`, `TPS26600PWP`, `TPS54561`, `TPS563201`) are real, sourceable parts but not yet second-source-qualified — same open item class as the archived build's Risk R-2/SWA-CST-004.

## 8. Files changed

- `Hardware/SWAFarmNodeV1/SWAFarmNodeV1.kicad_sch` — new, from scratch (fresh project; the STM32-based original is archived, see `TODO.md`'s "Architecture pivot" note).
- `Hardware/SWAFarmNodeV1/SWAFarmNodeV1_erc.json`, `SWAFarmNodeV1_netlist.xml` — fresh exports for this milestone.
- `Hardware/SWAFarmNodeV1/SWAFarmNodeV1.kicad_pcb` — untouched (still template placeholder; Step 8 scope).

## 9. Next step

Per the approved plan: **Step 2 — MCU Core (ESP32-S3-WROOM-1)**, then STOP for approval, matching this milestone's own cadence.
