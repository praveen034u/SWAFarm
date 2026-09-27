# Eight-relay POC: manufacturing candidate

Updated 2026-09-26. **CAD/export checks passed; vendor DFM and sourcing acceptance pending.** Two assembled POC units. Working project: ../project/SWAFarmNodeV1.kicad_pro. Original Hardware/SWAFarmNodeV1 sources match the pre-manufacturing snapshot; prior user changes were preserved.

## Approved implementation

- Eight G5Q-14 DC12 SPDT low-voltage dry-contact outputs, TBD62083AFWG,EL sink driver, MCP23S17 GPA0-GPA7 control and eight 47k pull-downs. Relay coil pins 1/5; contact pins 2/3/4 COM/NO/NC. Phoenix 1755749 connector pins 1/2/3 COM/NO/NC. No mains or pump motors.
- External regulated 12 V / 3 A controller supply; separate isolated 24 VAC / 120 VA / 5 A valve supply. Reference Hunter PGV-101-G-B. Qualify eight simultaneous valves; firmware initially limits to one and staggers starts. Hydraulic suitability remains untested.
- Approved RECOM R-78B5.0-2.0 and R-78B3.3-2.0 replace unfinished discrete bucks and take protected 12V_SW directly. Individual module ratings do not override combined input budget.
- Approved TPS26600 correction removes switched-ground Q1/gate resistor. GND returns directly; RTN pins 8/17, MODE and protection support returns use separate EF_RTN. Never short RTN to GND. R_ILIM 8.06k 1% gives nominal 1.489 A, approximately 1.40-1.58 A with stated tolerances. Normal total input target <=1.2 A; J_OUT shares this limit. Nominal UVLO 8.913 V, OVP 15.946 V, DVDT 100 nF / 9.6 ms ramp. Support components now have exact MPNs.
- F1 0451002.MRL 2 A; F2 0451001.MRL 1 A for relay coils. SMBJ18CA TVS; GRM32ER71J106KA12L 10 uF / 63 V input capacitor. Fuse/TVS coordination, effective capacitance and thermal/transient behavior require physical qualification.
- Regulated TRACO TMR 1-0511 replaces unregulated isolated converter; ISO7761FDWR default-low isolator, THVD1450DR and separate ISO_GND planes implement functional RS485 isolation. Hardwired 120-ohm termination / 680-ohm bias require endpoint use.
- RAK3172-T-8-SM-NI India/868 variant on corrected UART2 host pins; Amphenol 132134 board SMA. ESP32-S3-WROOM-1-N16R8 PSRAM-reserved pins remain NC. USB VBUS is not a board supply. Six sensor networks have sourced divider/burden/clamp parts.
- Implemented 200 x 160 mm four-layer outline, four mounting holes, three global/two local fiducials, top-side placement, complete routing, split reference planes, antenna exclusion, USB return vias and connector legends.
- MCU and eFuse thermal footprints each use twelve finished 0.30 mm holes / 0.70 mm lands. Drill minimum was not relaxed. Local USB ground-land adjustment clears mounting pegs. Local footprints are included.

## Verification

KiCad 10.0.5 CLI/pcbnew checked this copy because the project-specific MCP connector targets the original.

| Check | Result |
|---|---:|
| Strict ERC | 0 violations |
| Physical DRC | 0 violations |
| Unconnected items | 0 |
| Schematic parity | 0 |
| Footprints | 176 |
| Fitted BOM/CPL components | 153, all with manufacturer/MPN |
| Tracks / vias / filled zones | 1276 / 116 / 4 |
| Corrected thermal holes | 24 |
| Independent output validation | PASS |

Strict ERC/DRC exit 0. Existing ignored DRC categories remain: missing_courtyard, track_not_centered_on_via, tuning_profile_track_geometries, footprint_filters_mismatch, footprint_type_mismatch. No new exclusions; zero violations is scoped to configured checks.

Inherited ERC ignores are single-occurrence global labels, four-way junctions, SPICE model issues and footprint-filter mismatch. See native reports for full scope.

Independent checks cover BOM/CPL reference sets, quantities, positions and rotations; all pad centers within outline; 289 distinct drill features; four-layer order; closed outline; mask/paste pad centers; 705 IPC records; original-source and current-board hashes. Native IPC mask-field defects were corrected only in the fab export, with raw evidence/full mapping retained. Gerbers were independently parsed/rendered. Offline browser interaction self-test passed. These checks do not establish solderability, physical performance or compliance.

Evidence: drc-final.json, drc-release.rpt, erc-release.rpt and [output validation](../release-candidate/review/output-validation.json). Earlier 370-unrouted/24-drill-error reports are historical and superseded. [Package instructions](../release-candidate/README.md) link manufacturing notes, sourcing, review and test plan.

The PDF skill guided visual drawing checks; native KiCad PDF and local rasterization replaced its unavailable preferred runtime. User approved native KiCad CSV BOM when the spreadsheet export runtime was unavailable.

## Applied rules

Ordinary width/clearance 0.25/0.20 mm; power 0.8/0.2; contacts 1.0/0.5; coils 0.5/0.2; USB 0.13/0.12; RF 0.15/0.2. Minimum track 0.125, hole 0.30, annular ring 0.15, hole clearances 0.25, copper-edge 0.50 mm. Ordinary via 0.80/0.30 mm. Mask expansion 0.06, web 0.08, mask-to-copper 0.10 mm. Internal THT connections have thermal relief; ground domains remain separate.

Published PCB Power starting stack: 35 um copper / 0.105 mm prepreg / 35 um / 1.2 mm core / 35 um / 0.105 mm prepreg / 35 um. Outer copper must start at 0.5 oz and plate to nominal 1 oz to support fine geometry. USB 90-ohm and RF 50-ohm targets require vendor acceptance; not measured impedance claims.

## Remaining gates, in priority order

1. Vendor accepts thermal-hole fill/plug/tent, stencil/hidden-joint inspection, local USB lands, fine geometry and stackup/impedance. Explicit HOLD items are in fab notes.
2. Vendor confirms exact-MPN stock, placement-library rotations, mating plugs/accessories and panel process. Board BOM is specified; off-board procurement and stock allocation remain incomplete.
3. Purchaser approves quote/vendor dispositions and authorizes fabrication. No submission, payment or order has been made.
4. Firmware clears OLATA before IODIRA, implements concurrency/timeouts/watchdog and passes reset/hang tests. MCU software reset does not independently clear expander outputs. Supervised POC only, with manual water shutoff; not safety-rated.
5. Execute physical two-unit power, relay, sensor, USB, radio, RS485 and thermal/load acceptance plan. No bench tests performed. Global radio/EMC/environmental qualification is separate.

## Primary references

- [PCB Power capabilities](https://www.pcbpower.com/technology/technical-capabilities-rigid-pcb) and [stackups](https://www.pcbpower.com/impedance-controlled-standard-build-ups)
- [TI TPS2660](https://www.ti.com/lit/ds/symlink/tps2660.pdf), [ISO7761](https://www.ti.com/lit/ds/symlink/iso7761.pdf), [THVD1450](https://www.ti.com/lit/ds/symlink/thvd1450.pdf)
- [Omron G5Q](https://omronfs.omron.com/en_US/ecb/products/pdf/en-g5q.pdf), [Toshiba driver](https://toshiba.semicon-storage.com/info/docget.jsp?did=29893), [RECOM](https://recom-power.com/pdf/Innoline/R-78B-2.0.pdf)
- [RAK3172](https://docs.rakwireless.com/product-categories/wisduo/rak3172-module/datasheet/), [Espressif USB layout](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html), [GCT USB4105](https://gct.co/files/drawings/usb4105.pdf)
