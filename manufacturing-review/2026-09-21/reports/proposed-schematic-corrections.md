# Schematic corrections — sections A and B approved and applied

Evidence: freshly exported `netlist.xml`, `connectivity-trace.json`, and `erc.rpt`. All investigation used the project copy. Quantity: two assembled POC units.

Sections A and B were explicitly approved and applied. The subsequent request to address open items authorized the further corrections recorded in `open-items-completion.md`, which is now the current status report. The text below retains the original proposals and rationale. Section C's catch diode, section D's J2 cleanup, and section E's choke/capacitor/clamp corrections are now applied and verified; power qualification, Q1 and release requirements remain open. Section-A/B reports are historical checkpoints.

## A. Restore intended cross-sheet signals and the 3.3 V test point

Convert only the following local labels into global labels, retaining their existing attachment points and names. This joins the currently separate /MCU/ and peripheral-sheet nets. Each row specifies the resulting connection; sensor rows include the complete existing sensor-channel net, not just the diode pin.

| Signal | MCU symbol pin | Peripheral endpoint |
|---|---|---|
| SENSOR_CH1 | U_MCU1.39 / IO1 | D_CLHI1.3 and existing channel-1 RC/jumper network |
| SENSOR_CH2 | U_MCU1.38 / IO2 | D_CLHI2.3 and existing channel-2 RC/jumper network |
| SENSOR_CH3 | U_MCU1.4 / IO4 | D_CLHI3.3 and existing channel-3 RC/jumper network |
| SENSOR_CH4 | U_MCU1.5 / IO5 | D_CLHI4.3 and existing channel-4 RC/jumper network |
| SENSOR_CH5 | U_MCU1.6 / IO6 | D_CLHI5.3 and existing channel-5 RC/jumper network |
| SENSOR_CH6 | U_MCU1.7 / IO7 | D_CLHI6.3 and existing channel-6 RC/jumper network |
| VALVE_SPI_CS | U_MCU1.18 / IO10 | U_VALVEEXP1.11 / CS |
| VALVE_SPI_MOSI | U_MCU1.19 / IO11 | U_VALVEEXP1.13 / SI |
| VALVE_SPI_SCLK | U_MCU1.20 / IO12 | U_VALVEEXP1.12 / SCK |
| VALVE_SPI_MISO | U_MCU1.21 / IO13 | U_VALVEEXP1.14 / SO |
| LORA_UART_TX | U_MCU1.10 / IO17 | U_LORA1.5 / UART1_RX |
| LORA_UART_RX | U_MCU1.11 / IO18 | U_LORA1.4 / UART1_TX |
| net_USB_DM | U_MCU1.13 / USB_D- | J_USB1.A7 and J_USB1.B7 |
| net_USB_DP | U_MCU1.14 / USB_D+ | J_USB1.A6 and J_USB1.B6 |
| RS485_TX | U_MCU1.8 / IO15 | U_ISO1.2 / INA |
| RS485_RX | U_MCU1.9 / IO16 | U_ISO1.7 / OUTF |

Connect TP_3V3.1 to the existing +3V3 net using a correctly attached +3V3 power symbol or wire. Its current exported net contains only TP_3V3.1. Remove only the associated dangling wire stub if it becomes redundant.

These 16 cross-sheet signal connections match the documented MCU mapping in the existing design review. They are presently absent in the actual netlist. After approval, re-export the netlist and verify every endpoint above, rerun ERC, and synchronize the PCB copy. This batch does not resolve all release blockers.

## B. RS-485 direction — approved and applied

The user approved the single-direction policy below. IO41 now drives U_ISO1.3 on the global RS485_DE net. IO42 has an explicit no-connect marker; its wire and label were removed. Both RS485_RE labels were removed. PCB pad nets were synchronized and independently verified. The following paragraphs record the original finding and proposal.

The RS-485 sheet currently joins its local RS485_DE and RS485_RE labels at U_ISO1.3. The MCU sheet has separate IO41 and IO42 nets. Making both names global would short those two MCU pins. Do not do that automatically.

Proposed single-direction policy: U_MCU1.34 / IO41 drives U_ISO1.3 through RS485_DE; remove the redundant RS485_RE label from the RS-485 sheet; reserve MCU IO42, remove its unused direction label, and mark it unconnected. This matches the existing transceiver's combined DE/RE arrangement but changes the GPIO/firmware contract and therefore needs explicit approval. Independent receive control would instead need another isolator channel and separate transceiver wiring, which is a different change.

## C. Power-stage circuit defect — part selection pending

The actual U2 SW net contains only U2.9, C_BOOT1.2 and L1.1. There is no catch diode. TI's TPS54561 datasheet section 8.2.1.2.5 requires an external catch diode between SW and GND. Proposed topology: add a Schottky diode with cathode at U2.9/SW and anode at GND, then select its exact MPN, footprint and ratings from the specified input range, transient envelope, load, ripple current and thermal budget. This is not yet a ready-to-apply parts change.

Source: https://www.ti.com/lit/ds/symlink/tps54561.pdf .

## D. Remaining power/ERC work

Power flags are absent from the current parsed schematics. ERC reports GND, VIN_12V, +3V3, +5V and +12V as undriven. The netlist confirms +12V reaches F2.2 and all valve-driver VM pins, +5V reaches L1.2, and +3V3 reaches L2.2. Power flags may represent these passive-fed rails after source, return-path and power-stage validation; flags must not conceal the missing U2 catch diode or unresolved reverse-polarity topology.

J2 is board-excluded but remains a BOM item with three unconnected pins. Proposed cleanup, separately approved: keep it as a documented unused schematic placeholder, exclude it from BOM and position files, and mark its three pins intentionally unconnected. Alternatively delete it if the user confirms it serves no documentation purpose.

## E. Additional sourcing/package findings

- CMC_RS485_1 and CMC_RS485_2 have value 744232090 but use L_CommonModeChoke_Bourns_SRF1260. The Würth datasheet specifies a 3.2 x 1.6 mm 1206 part. KiCad has Inductor_SMD:L_CommonMode_Wurth_WE-CNSW-1206 available. Validate pad dimensions and winding pin mapping against the datasheet before proposing the exact symbol/footprint substitution. Merely having four pads is insufficient. Source: https://www.we-online.com/components/products/datasheet/744232090.pdf .
- Q1 is labelled IPD50N06S4L-16 but uses SOT-23. An authoritative datasheet for that exact suffix has not been located. Related IPD50N06S4L-08/-12 parts use DPAK; that does not validate or authorize substituting them. Q1 needs an exact orderable MPN, pin mapping, package and voltage/current/gate-drive check before assembly.
- BAV99LT1G pin numbering is 1=anode, 2=cathode, 3=series midpoint. Actual D_CLHI1-6 nets are 1=GND, 2=+3V3, 3=sensor channel, consistent with that clamp topology. The custom cached Device:D pin names incorrectly describe pins 1/2 as K/A. Proposed later symbol cleanup must preserve these verified pad-number connections. This is a pin-connectivity check, not complete clamp-performance qualification. Source: https://www.onsemi.com/pdf/datasheet/bav99lt1-d.pdf .
- Panasonic EEUFR1E102 is 1000 uF / 25 V, 10 mm diameter, 20 mm high, with 5 mm lead pitch. The current 12.5 mm diameter / 5 mm pitch footprint has matching pitch but an oversized body outline. Lead drill, polarity, height clearance, and the selections for all six capacitors remain to be verified. Source: https://industrial.panasonic.com/ww/products/pt/aluminum-cap-lead/models/EEUFR1E102 .

Sections A and B are complete; the authorized subset of C-E is now applied as detailed in `open-items-completion.md`. Fab/assembler, allowed outline, connector choice, supply/load envelope and assembly requirements remain necessary before final rules and placement. Use `erc-open-items.rpt`, `drc-open-items.rpt`, `netlist-open-items.xml` and `open-items-verification.json` for current evidence.
