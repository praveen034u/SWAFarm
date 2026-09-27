# SWAFarmNodeV1 POC manufacturing review

Status: NOT READY FOR MANUFACTURE OR ASSEMBLY. Target: two assembled POC units.

Current checkpoint: sections A and B are approved and applied in the project copy. `section-b-completion.md` records the latest results: ERC 8 errors / 15 warnings; zero schematic-parity findings; 34 physical DRC findings and 422 unconnected items. The baseline findings below are historical.

Follow-up audit: `proposed-schematic-corrections.md` gives exact endpoints for 16 cross-sheet signal connections and TP_3V3, documents the missing mandatory U2 catch diode, and flags additional package/sourcing discrepancies. Section A was subsequently approved, applied and verified in the project copy; see `section-a-completion.md` for current results. Other proposed edits remain pending. The baseline findings below describe the pre-correction state.

Work copy: `../project/`. Original design sources have not been edited in this audit. KiCad 10.0.5 is installed, and its bundled Python provides pcbnew, DSN export and SES import. Java and Freerouting were not found on PATH; no router JAR was found in the repository. Routing has not been attempted. If using an externally installed router, check `java -version` and run `java -jar "C:\path\to\freerouting.jar" -de "board.dsn" -do "board.ses"` with the actual installed JAR path. Installation/version selection remains pending.

## Verified baseline

Fresh CLI ERC: 58 findings, comprising 14 errors and 44 warnings. Fresh CLI DRC with schematic parity: 34 physical violations (33 drill errors and one footprint-library mismatch), 404 unconnected items, zero schematic-parity findings. Reports: `erc.rpt`, `drc_before.rpt`. These are baseline checks, not release checks.

The board has four copper layers, a 1.6 mm configured thickness, 184 footprints, zero track/via objects, and zero copper zones. The rectangular Edge.Cuts centerline is 420 x 361.5795 mm; its stroked bounding box is 420.15 x 361.7295 mm. These dimensions are inherited layout data, not an approved enclosure specification. No full placement, footprint polarity or datasheet sign-off has been completed.

## Functional overview

The design comprises input protection and 12 V distribution, 5 V and 3.3 V conversion, ESP32-S3 MCU and programming interfaces, RAK3172 LoRa, isolated RS-485, six analog sensor channels, and six DRV8871 valve drivers controlled through an SPI expander. Critical routing includes regulator switching/feedback loops, valve supply and output currents, USB D+/D-, RF, analog inputs, SPI, and RS-485. Isolated power/ground separation must be established from the circuit before assigning reference planes.

## Highest-priority blockers

1. Valve expander U_VALVEEXP1 CS, SCK and SI inputs are reported undriven. Connectivity and hierarchy intent require review before routing.
2. RS-485 isolator U_ISO1 INA/INB inputs are reported undriven. RS485_DE and RS485_RE also share one net according to ERC; intended control behavior needs confirmation.
3. Five power-input findings remain across Power, MCU, RS-485 and Motor Valve. Verify actual supply paths before proposing power flags; flags alone do not establish a connection.
4. TP_3V3 is unconnected. J2 remains board-excluded but has three unconnected schematic pins. Any connection, removal or no-connect mark needs the user's prior schematic-edit approval.
5. Five connector footprints are identified in the historical BOM as pin-header placeholders for M12 parts. J_OUT1 is labelled M12_5P but currently has a four-position footprint. Confirm exact connectors, pinouts and mechanical drawings, or explicitly choose a different POC connector arrangement.
6. L1 and compensation values contain TBD selections. Fuse entries describe families/current classes rather than locked orderable parts. Load current, simultaneous valve operation and supply conditions must be specified before calculation and part selection.
7. The historical U2 entry TPS54561DDAR must not be treated as verified sourcing. TI lists TPS54561 in the DPR 10-pin 4 x 4 mm WSON package and TPS54561DPRR as an orderable variant. This identifies a BOM correction candidate, not a full footprint/pinout approval. Source: https://www.ti.com/product/TPS54561/part-details/TPS54561DPRR .
8. All 181 netlisted components lack explicit MPN/assembler identifiers in the fields inspected. Historical BOM MPN text exists for 55 references, but includes families and unresolved selections. `sourcing-audit.csv` separates historical text from verified schematic fields. J2 is the only netlisted component without a footprint and is excluded from the board; the four additional PCB items are mounting holes.
9. The 33 thermal drill errors are 0.20 mm holes against a 0.30 mm project minimum on U1, U2 and U_MCU1. The manufacturer must support the selected drill and assembly process, or the footprints require engineering changes. Do not lower constraints merely to silence DRC. U_MCU1 also differs from its footprint library copy.
10. No fab/assembler, approved outline, connector locations, loading, stackup dielectric data or sourcing policy is selected. The project references a missing local Arduino_MountingHole.pretty library. Library portability and every selected component's pad geometry, pin 1 and polarity remain audit gates.

## Approval and specification gates

Quantity is confirmed as two assembled POC units. Still needed: fab/assembler (or authority to propose one), allowable dimensions and fixed mechanical locations, connector choice, input supply and valve currents/pulse durations/concurrency, assembly side and treatment of through-hole parts, and sourcing/DNP/consignment requirements.

Sections A and B are the approved and applied schematic change batches. Before additional schematic edits, provide the exact proposed net/pin/field changes for approval, as requested in the supplied workflow. The remaining findings are investigations and correction candidates, not approved electrical changes.

Phase 0 is incomplete pending sourcing and datasheet validation. Phases 1-6 are not complete. No routing rules, stackup, impedance widths, final placements, manufacturing ZIP, ordering BOM or CPL have been released. Numeric rules must follow the selected fab and actual current/impedance requirements. Before ordering: approve circuit corrections, verify the BOM and all packages, complete placement/routing and zone fill, pass final ERC/DRC gates, validate manufacturing layers/drills and BOM/CPL rotations, and review assembled renders.
