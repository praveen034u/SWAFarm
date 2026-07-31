# SWAFarm Node V1 — "02_MCU" Milestone: Design Review Package

Author: Hardware Architect (AI-assisted)
Status: **ERC clean of unexpected defects (43 errors = intentionally reserved pins, 46 warnings = cosmetic grid alignment only), verified via live netlist trace**
Scope: The discrete MCU foundation subsystem — STM32L462RETx + power/decoupling/reset/boot/clock support, SWD programming interface, UART debug console, status LED. No LoRaWAN, RS485, relay, sensor, battery-monitor, or expansion circuitry is connected — those GPIOs are reserved (named, unwired) for future milestones per explicit instruction.
Source of truth verified live against `Hardware/SWAFarmNodeV1/SWAFarmNodeV1.kicad_sch` via the real `kicad-cli.exe sch erc` binary (not only the MCP server's internal tooling) and `generate_netlist()` + `trace_netlist_connection()` on 2026-07-30/31.

---

## 1. Scope and Architecture Decision

`.ai/knowledge/swafarm_overview.md` §"Example 2: Trade-off Evaluation Snapshot" explicitly recommends **discrete MCU + certified LoRaWAN module** over a single integrated MCU+RF module, citing "lower certification risk, better modularity" vs. "vendor lock-in and migration risk." This is why the milestone is architected as a standalone MCU with a *reserved* UART for a future certified LoRaWAN module (e.g., RAK3172-class), rather than treating a combo module's own MCU as "the platform MCU."

| Task Requirement | Design Element | Status |
|---|---|---|
| Industrial MCU, long-term availability | STM32L462RETx (LQFP64) | Captured, verified |
| Power connections | VDD/VSS/VDDA/VSSA/VBAT/VDDUSB tied to existing 3V3_RAIL/GND | Captured, verified |
| Decoupling | Per-pin 100nF + bulk 4.7uF + filtered VDDA | Captured, verified |
| Reset circuit | RC pull-up/filter on NRST + test point | Captured, verified |
| Boot configuration | Pull-down on PH3/BOOT0 + test point | Captured, verified |
| Clock | LSE 32.768kHz crystal for RTC; HSI16 internal (no HSE) | Captured, verified |
| Programming interface | ARM 10-pin SWD header | Captured, verified |
| Debug interface | USART1 console UART header | Captured, verified |
| Status LED | GPIO-driven, PC13 | Captured, verified |
| Test points | NRST, BOOT0 | Captured, verified |
| GPIO reservation for future subsystems | 27 pins named via netlist labels only, zero wiring | Reserved, not connected |
| LoRaWAN RF, RS485, Relay, Solar, Battery Mgmt, Sensors, Buttons, Expansion | — | **Explicitly out of scope, not implemented** |

---

## 2. MCU Selection Rationale

**TI/ST STM32L462RETx**, LQFP64, 512KB Flash / 160KB RAM, Arm Cortex-M4F @ up to 80MHz.

| Requirement | How STM32L462RETx satisfies it |
|---|---|
| SWA-HWR-301 (30% CPU/memory headroom) | 512KB/160KB gives wide margin over a typical LoRaWAN+RS485+RTOS footprint (commonly well under 200KB flash / 40KB RAM in mature builds) |
| SWA-SEC (hardware root of trust, secure boot, crypto) | L462 is the **AES-256 hardware crypto + TRNG variant** of the STM32L4 family — chosen specifically over the plain STM32L452 for this reason (identical pinout/package, so this cost no manufacturability penalty) |
| SWA-SWO-304 / SWA-HWR-101 (ultra-low-power) | STM32L4 series Stop 2 mode (~1µA class) with RTC-alive via LSE; industry-standard choice for solar/battery LoRaWAN nodes |
| SWA-CST (industrial grade, distributor availability) | Broad DigiKey/Mouser/Arrow stock, ST's long-lifecycle industrial catalog |
| Stock KiCad symbol availability | Confirmed present in `MCU_ST_STM32L4.kicad_sym` (`STM32L462RETx`) — avoided the custom-symbol burden that BQ25792/BQ76920/LT8610AC required in the Power subsystem |

**Second-source risk (SWA-CST-004 / SWA-SWO-001):** MCUs are inherently a single-silicon-vendor architecture; no pin-and-firmware-compatible cross-vendor part exists. Mitigation, consistent with how BQ25792/BQ76920/LT8610AC were handled in the Power subsystem: STM32L4 is a wide, pin-compatible family (L451/L452/L462/L433 etc. share the LQFP64 'R' footprint), so a same-board-revision part swap is possible without a redesign if ST supply is disrupted. Tracked as a risk (§9), not a blocker.

---

## 3. Existing Design Review (Power Subsystem)

Reviewed `01_power` before extending it. **No changes were made to any existing Power-subsystem component, wire, or net** — the MCU subsystem only *adds* new elements that reference the Power subsystem's already-exposed `3V3_RAIL` and `GND` net labels by name (the file is a single flat sheet, so matching label text is what joins nets — no hierarchical or cross-sheet linkage was needed). Verified via netlist trace that `3V3_RAIL` and `GND` now correctly span both subsystems' members with no unintended merges.

No critical issue was found in the Power subsystem during this review, so no modification was proposed or made.

---

## 4. Changes Made

**23 new components placed** (STM32L462RETx + 22 supporting parts), all via the documented `add_component_from_library` MCP tool, each followed by the same manual `instances`-block injection the Power-subsystem milestone documented as necessary (confirmed still required — the tool has not been fixed since).

| Group | Components |
|---|---|
| MCU | U_MCU1 (STM32L462RETx) |
| Power decoupling | C_MCU_VBAT1, C_MCU_VDD1/2/3, C_MCU_BULK1, FB_MCU1, C_MCU_VDDA1/2, C_MCU_VDDUSB1 |
| Reset | R_NRST1, C_NRST1, TP_NRST1 |
| Boot config | R_BOOT0_1, TP_BOOT0_1 |
| Clock | Y_LSE1, C_LSE1, C_LSE2 |
| Status indicator | D_STATUS1, R_STATUS1 |
| Programming/debug | J_SWD1 (ARM 10-pin), J_DBG_UART1 (3-pin) |
| Power symbols | #PWR16–23 (GND ×8), #FLG03/#FLG04 (PWR_FLAG on 3V3_RAIL/VDDA) |

**44 net labels** and **16 wires** added to connect this milestone's populated signals only. **2 no-connect flags** added on J_SWD1 pins 7 (KEY) and 8 (reserved-NC per the ARM standard connector spec — these two are never populated on a real ARM debug probe cable).

---

## 5. SWD Programming Interface Design

**Connector: generic 2×5, 1.27mm pitch header (`Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical`), wired to the ARM CoreSight standard 10-pin SWD pinout.**

| Pin | Signal | Connects to |
|---|---|---|
| 1 | VTref (3.3V reference) | 3V3_RAIL |
| 2 | SWDIO | MCU PA13 |
| 3 | GND | GND |
| 4 | SWCLK | MCU PA14 |
| 5 | GND | GND |
| 6 | SWO (trace) | MCU PB3 |
| 7 | KEY | No-connect (mechanical key position on a real connector; meaningless on this generic header, flagged NC) |
| 8 | Reserved | No-connect (per ARM standard) |
| 9 | GND | GND |
| 10 | nRESET | MCU NRST |

**Why this connector:** the ARM 10-pin 1.27mm layout is the de facto industry standard for Cortex-M debug (ST-Link, J-Link, and most third-party probes ship this cable natively) — no adapter needed in production test or field service. A stock KiCad footprint/generic-header combination was used rather than a proprietary/exotic footprint, keeping sourcing simple (SWA-CST recommended practice: prefer broadly available parts). PA13/PA14 are STM32's **dedicated** SWD pins (not general-purpose-first pins repurposed), so debug access is available even if firmware later misconfigures other GPIOs — a standard safety property of the ARM debug architecture.

**Trade-off considered and deferred:** a Tag-Connect (TC2030-class) pogo-pin footprint would eliminate a stuffed connector's per-unit BOM cost, which is attractive for the "not a prototype" cost-target philosophy — but its footprint isn't in KiCad's stock libraries (same class of problem as the Power subsystem's custom-symbol ICs), and would need a vendor footprint import. Recorded as a Recommended Improvement (§10) rather than blocking this milestone on a sourcing side-quest.

---

## 6. UART Debug Interface Design

**UART used: USART1 (PA9 = TX, PA10 = RX).**

| Header pin | Signal |
|---|---|
| 1 | GND |
| 2 | MCU_TX (board's USART1 TX → adapter's RX) |
| 3 | MCU_RX (board's USART1 RX ← adapter's TX) |

**Why USART1:** it's the STM32's first/default UART with no alternate-function remapping required (AF7 on PA9/PA10, the most standard mapping on this family), keeping firmware bring-up simple. **Why no 3.3V pin on the header:** the board is always powered from its own regulated rail (from the Power subsystem); a second unprotected power injection point from a USB-serial adapter was deliberately omitted to avoid a backfeed/dual-supply hazard — consistent with the reverse-polarity/surge protection discipline already established on the Power subsystem's external ports.

**Future firmware usage:** this is a general **printf-style debug/log console**, deliberately kept separate from the UARTs reserved for RS485 (USART3) and the future LoRaWAN module (USART2) — so debug logging never contends with a field-protocol UART, and can remain active in production builds if desired (gated per SWA-SEC-003's "no debug interface exposure in production without approved controls" — a firmware-level policy decision for a later milestone, not a hardware constraint).

---

## 7. GPIO Allocation Table

### Used this milestone
| Pin | Function | Connects to |
|---|---|---|
| PC13 | GPIO out | Status LED (via R_STATUS1) |
| PC14 | OSC32_IN | LSE crystal |
| PC15 | OSC32_OUT | LSE crystal |
| PH3 (BOOT0) | Boot select | Pull-down + test point |
| PA9 | USART1_TX | Debug UART header |
| PA10 | USART1_RX | Debug UART header |
| PA13 | SWDIO | SWD header (dedicated debug pin) |
| PA14 | SWCLK | SWD header (dedicated debug pin) |
| PB3 | SWO | SWD header |

### Reserved for future subsystems (named, NOT wired)
| Subsystem | Pins | Notes |
|---|---|---|
| LoRaWAN module UART | PA2 (USART2_TX), PA3 (USART2_RX), PA0 (LORA_RESET_N), PA1 (LORA_BUSY) | Module itself out of scope; UART peripheral choice avoids USART1/3 to prevent future conflicts |
| RS485 | PB10 (USART3_TX), PB11 (USART3_RX), PB2 (driver-enable) | — |
| Battery monitor / charger telemetry I2C | PB8 (I2C1_SCL), PB9 (I2C1_SDA), PC4 (CHG_ALERT_N), PC5 (PROT_ALERT_N) | Matches the original Power architecture doc's "I2C + ALERT to MCU" concept — no charger/protection ICs exist in KiCad yet |
| Relay driver ×5 | PB12, PB13, PB14, PB15, PA15 | Chosen on TIM1-capable pins where practical for future PWM flexibility |
| Sensor front-end ×5 | PC0, PC1, PC2, PC3, PA4 | All ADC1-capable |
| SPI / expansion header | PA5 (SCK), PA6 (MISO), PA7 (MOSI), PA8 (CS) | General-purpose expansion bus |
| User button(s) ×2 | PC6, PC7 | EXTI-capable |

27 pins reserved. **Exact alternate-function pin choices (PA2/PA3 for USART2 etc.) are the standard/default AF7 mappings for this family; final confirmation against the STM32L462 datasheet AF table is a firmware GPIO-init task, not a hardware risk** — no wiring depends on this being off by one AF.

### Spare / unallocated headroom
PH0, PH1, PC8, PC9, PC10, PC11, PC12, PD2, PB0, PB1, PB4, PB5, PB6, PB7, PA11, PA12 (16 pins) — intentionally left uncommitted as margin beyond the currently-known future subsystems.

**43 reserved+spare pins = 27 + 16, exactly matching the ERC "pin_not_connected" error count**, confirming the allocation was implemented with no drift between plan and schematic.

---

## 8. Engineering Decisions

1. **STM32L462 over STM32L452**: AES-256/TRNG variant chosen for SWA-SEC compliance at zero footprint/pinout cost.
2. **Discrete MCU, not an integrated MCU+RF module**: matches `swafarm_overview.md`'s explicit recommendation; keeps LoRaWAN module swap/certification-risk isolated from the platform MCU.
3. **VBAT tied to 3V3_RAIL**: no RTC backup battery/coin-cell domain in this design; ST datasheet-recommended simplification when no backup supply exists.
4. **VDDUSB tied to 3V3_RAIL**: USB peripheral unused, but ST recommends not floating this pin even when idle.
5. **VDDA filtered via ferrite bead, not tied directly to 3V3_RAIL**: standard ADC noise-isolation practice; kept on a single project-wide GND (no separate AGND net) since the rest of the design (Power subsystem) already uses one unified GND — introducing an AGND split now would be inconsistent with established precedent and is more of a PCB-layout floor-planning concern than a schematic-net concern at this stage.
6. **LSE crystal populated, HSE crystal not populated**: RTC/low-power timekeeping needs LSE's accuracy-during-sleep property that HSI16 cannot provide; HSI16's internal ±1%-trimmed accuracy is sufficient for UART/general timing, avoiding 2 extra components for no measured benefit.
7. **No physical reset button**: reset is available via SWD (debugger-controlled NRST) and firmware; a manual button was excluded because "User Buttons" are an explicitly deferred future subsystem.
8. **PG (PowerGood) from the Power subsystem's buck regulator was *not* wired to the MCU this milestone**, despite being a natural, low-risk connection — deliberately deferred to respect "implement ONLY the requested subsystem." Flagged as a recommendation (§10) for explicit approval.

---

## 9. Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R-MCU-1 | MCU is single-vendor silicon (no cross-vendor second source) | Low–Medium | High if ST supply disrupted | Pin-compatible STM32L4 family alternates (L451/L452/L433) exist for a same-footprint swap; tracked per SWA-CST-004 |
| R-MCU-2 | Exact AF (alternate-function) pin mapping for reserved peripherals (USART2/3, I2C1, SPI1, TIM1) not yet cross-checked against the datasheet's AF table | Low | Low (firmware config only, no rewiring risk) | Confirm during firmware GPIO-init development, before those subsystems are wired in hardware |
| R-MCU-3 | 46 ERC "endpoint_off_grid" warnings — new components placed on round-mm coordinates instead of the 1.27mm grid the rest of the design uses | High (known) | None electrically; cosmetic/GUI-editing friction only | See §11 — classified Minor, fix path identified but not applied to avoid risking the verified zero-length pin/label/GND-symbol joins |
| R-MCU-4 | No manual reset button or user button populated | N/A (by design) | None — SWD provides reset control | Add in a future milestone if field service without a debugger probe is required |

---

## 10. Recommendations

1. Approve wiring the Power subsystem's existing `PG` (power-good) signal to a spare MCU GPIO — low-risk, high-value (lets firmware detect buck regulator faults), uses an already-exposed net, needs no new components.
2. Consider a Tag-Connect-class pogo-pin SWD footprint for a cost-down respin once volume justifies importing that vendor footprint.
3. Run a snap-to-grid pass on the 23 new components in the KiCad GUI (Edit → Select newly-added items → grid-align) before this milestone is considered final for layout — see §11.
4. When the LoRaWAN module milestone begins, confirm the module's actual control-line needs (reset/busy/wake) against the 2 spare pins reserved for it (PA0/PA1) — some certified modules need more or fewer control lines than assumed here.

---

## 11. ERC Results — Classified

Verified independently via the real `kicad-cli.exe sch erc` binary (not only the MCP server's internal ERC), per the discipline established after the Power-subsystem review found the MCP tool's version-stamp writes untrustworthy without cross-checking.

**Total: 89 violations (43 errors, 46 warnings)**

| Classification | Count | Detail |
|---|---|---|
| **Critical** | 0 | None |
| **Major** | 0 | None |
| **Minor** | 46 | `endpoint_off_grid` warnings on every new label/wire/component this milestone added. Root cause: new components were placed at round decimal-mm coordinates (e.g., 90, 225, 251.74) instead of exact multiples of KiCad's 1.27mm connection grid, unlike the Power subsystem's coordinates (all clean multiples of 2.54mm). **Zero electrical impact** — confirmed via netlist trace that every intended connection is correct regardless of grid alignment. Not auto-fixed in this pass because doing so risks silently breaking the zero-length pin/label/GND-symbol coincidences deliberately engineered throughout this milestone; the safe fix is a GUI-side "move to grid" pass (KiCad preserves connectivity through that operation) or a follow-up scripted pass with full re-verification. |
| **Informational** | 43 | `pin_not_connected` on U_MCU1. **Every single one is an intentionally reserved-for-future or spare GPIO pin** (§7) — verified by exact count match (27 reserved + 16 spare = 43) and by netlist trace confirming zero unexpected unconnected pins among the pins this milestone was supposed to wire. KiCad's ERC severity model has no "intentionally deferred" category, so these surface as "errors" in the raw tool count; they are not defects. |

No floating pin that *should* be connected this milestone was found unconnected. No missing symbols or missing footprints — every placed component resolved to a real stock KiCad symbol and footprint (confirmed via direct inspection of `MCU_ST_STM32L4.kicad_sym`, `Device.kicad_sym`, `Connector_Generic.kicad_sym` before use, not assumed).

---

## 12. Documentation Updates

- This document created.
- `TODO.md` updated with the `02_MCU` milestone entry.
- Fresh `SWAFarmNodeV1_erc.json` exported (2026-07-31), reflecting the current 89-violation (43 informational + 46 minor) state — **do not mistake this nonzero count for a regression**; see §11 before assuming the design is broken.

---

## 13. Items Intentionally Deferred to Later Milestones

Per explicit instruction, **not implemented, only GPIO-reserved**:
- LoRaWAN RF module and antenna path
- RS485 transceiver and bus protection
- Relay driver stage
- Solar charging (BQ25792) and battery protection (BQ76920) — already deferred from the Power subsystem, unchanged
- Sensor front-end circuitry
- User button(s)
- Expansion header
- PG (power-good) monitoring by the MCU (ready to wire, awaiting approval — §10)
- Grid-alignment cleanup pass (§11, Minor, zero electrical impact)
- Tag-Connect SWD cost-down evaluation

## Cross References
- [SWAFarmNodeV1_01Power_DesignReview.md](SWAFarmNodeV1_01Power_DesignReview.md) — Power subsystem review (unchanged by this milestone)
- [SWAFarmNodeV1_PowerSupply_Design.md](SWAFarmNodeV1_PowerSupply_Design.md) — full target architecture
- [../TODO.md](../TODO.md) — milestone tracker
- [../Hardware/SWAFarmNodeV1/SWAFarmNodeV1.kicad_sch](../Hardware/SWAFarmNodeV1/SWAFarmNodeV1.kicad_sch) — source schematic
- [../Hardware/SWAFarmNodeV1/SWAFarmNodeV1_erc.json](../Hardware/SWAFarmNodeV1/SWAFarmNodeV1_erc.json) — fresh ERC report
- [../.ai/knowledge/swafarm_overview.md](../.ai/knowledge/swafarm_overview.md) — discrete-MCU-vs-integrated-module architecture decision basis
- [../.ai/knowledge/security_standards.md](../.ai/knowledge/security_standards.md) — basis for STM32L462 (crypto variant) selection
- [../.ai/knowledge/hardware_requirements.md](../.ai/knowledge/hardware_requirements.md) — SWA-HWR-301 headroom, SWA-HWR-204 test point requirements
