# Section B completion — RS-485 direction control

The user approved section B, and it has been applied only in `../project/`. Original design sources are unchanged, verified against the pre-section-A snapshot. A recoverable pre-section-B snapshot is in `../before-section-b/`.

## Applied changes

- MCU IO41 (U_MCU1 pin 34) now connects to U_ISO1 pin 3 (INB) through global RS485_DE labels on the MCU and RS-485 sheets.
- Removed both redundant RS485_RE labels. Removed the IO42 wire and placed an explicit no-connect marker at U_MCU1 pin 35, schematic coordinate (132.08, 97.79) mm.
- Updated the PCB nets of U_MCU1 pads 34 and 35 and U_ISO1 pad 3. No other PCB content changed, including placement, footprint geometry or routing.
- The isolated-side connection from U_ISO1 pin 14 to transceiver U_RS485_TX1 pins 2 and 3 remains intact.

Firmware must use IO41 as the sole RS-485 direction GPIO. IO42 is reserved and has no external connection. Firmware files were not changed in this schematic/PCB task.

## Verification

KiCad 10.0.5 exported a fresh netlist and reran ERC and DRC with all severities and schematic parity. `section_b.py verify` independently confirms the only net merge is IO41 to INB, IO42 remains an isolated singleton with an explicit no-connect marker, all section-A connectivity is preserved, and every one of 691 netlisted PCB pads matches the schematic.

| Check | After A | After B |
|---|---:|---:|
| ERC errors | 9 | 8 |
| ERC warnings | 19 | 15 |
| Schematic-parity findings | 0 | 0 |
| Physical DRC errors | 33 | 33 |
| Physical DRC warnings | 1 | 1 |
| Unconnected PCB items | 421 | 422 |

The added unconnected PCB item is the newly established IO41-to-isolator connection, which still needs routing. The RS-485 undriven direction input, redundant-net-name warning and direction-label isolation warnings are resolved.

Evidence: `netlist-section-b.xml`, `erc-section-b.rpt`, `drc-section-b.rpt`, `section-b-verification.json`. The PCB comparison permits only the three specified pad-net changes and passes. Original source hashes still match the pre-section-A snapshot.

## Remaining release blockers

Eight ERC errors remain: three unused J2 pins and five undriven-power reports. Physical DRC still reports 33 thermal-drill constraint errors and one MCU footprint-library mismatch. The board is unrouted.

Sections C-E remain unapplied: the missing U2 catch diode and unresolved power-component sizing, J2/power-flag cleanup after circuit validation, and sourcing/package discrepancies. Manufacturer capabilities, mechanical/connector requirements, supply/load specifications and assembly/sourcing choices still need resolution. This checkpoint is not manufacturing or assembly sign-off.
