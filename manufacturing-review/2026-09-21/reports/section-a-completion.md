# Section A completion — two-unit POC

Historical checkpoint: section B has since been approved and applied. See `section-b-completion.md` for current results and direction-control status.

Status: approved correction batch completed; design NOT READY FOR MANUFACTURE OR ASSEMBLY.

## Applied changes

Changed 34 local-label instances into global labels for the 16 approved signal names: SENSOR_CH1-6, VALVE_SPI_CS/MOSI/SCLK/MISO, LORA_UART_TX/RX, net_USB_DM/DP and RS485_TX/RX. Existing label attachment points and identifiers were retained. Each USB label has three instances; each other signal has two.

Reconnected TP_3V3.1 to +3V3 by ending its existing wire at (240.03, 109.22) mm, splitting the rail wire at that point, and adding an explicit junction. The wire previously crossed the rail without a connection.

Updated PCB pad net assignments to match the fresh schematic netlist. No parts were added or removed. All 184 footprint references, UUIDs, positions, rotations, footprint identities, pad positions and pad sizes remained unchanged. No routing was performed.

Modified five subsheets and the PCB under `../project/`. The original `Hardware/SWAFarmNodeV1` design sources still match the saved pre-edit hashes. The project copy's pre-edit snapshot is in `../before-section-a/`.

## Tool-verified results

| Check | Before | After section A |
|---|---:|---:|
| ERC errors | 14 | 9 |
| ERC warnings | 44 | 19 |
| Schematic-parity findings | 0 | 0 |
| Physical DRC errors | 33 | 33 |
| Physical DRC warnings | 1 | 1 |
| Unconnected PCB items | 404 | 421 |

The 17 additional unconnected items represent the 16 restored signal connections and the test-point connection that now need PCB routing. The board still has no tracks or zones; the increased count reflects corrected connectivity, not completed routing.

`section_a.py verify`, run with KiCad's bundled Python, independently checked every approved endpoint and the entire netlist connectivity partition against the baseline. The only net merges are the 17 authorized merges. The set of symbol pins is unchanged. All 691 netlisted physical PCB pads, including repeated pad numbers, match the new schematic nets. MCU pins 34 and 35 and isolator pin 3 remain on three separate nets; the unresolved direction-control problem has not been converted into a GPIO short.

KiCad 10.0.5 CLI reruns produced `erc-section-a.rpt` and `drc-section-a.rpt`; machine-readable endpoint and invariant results are in `section-a-verification.json`. DRC ran with all severities and schematic parity. These are intermediate checks, not the clean final release gate.

## Remaining blockers

The nine ERC errors are three unused J2 pins, five undriven power-net reports, and the RS-485 direction input. Warnings also include cached/library symbol differences and the redundant RS485_DE/RE labels. Section B proposes using MCU IO41 as the single direction control and reserving IO42; that GPIO/firmware decision is not yet approved.

The missing U2 catch diode, unresolved regulator/fuse sizing, Q1 sourcing/package discrepancy, choke and connector footprints, and remaining datasheet/assembly checks must be resolved before placement and routing can be finalized. No power flags, catch diode, package substitutions or RS-485 direction edits were added in section A.

The confirmed order target is two POC assemblies. Fab/assembler, acceptable board dimensions, connector/mechanical requirements, supply and valve specifications, concurrency, and assembly/sourcing requirements remain unanswered. No fabrication or assembly files have been released.
