# Open-item corrections and manufacturing hold

Status: **NOT ready for manufacture or assembly.** Quantity requested: two assembled POC units. Work is confined to `../project/`; the original design is unchanged against the pre-manufacturing snapshot. Sections A and B remain intact.

## Applied in this batch

1. Added `D_BUCK1`, candidate MPN **PDS760-13**, using the installed `Diode_SMD:D_PowerDI-5` footprint. Cathode/pad 1 connects to U2.9, L1.1 and C_BOOT1.2; both anode/pad-2 lands connect to GND. This fixes the missing catch-diode topology, **not** the complete power-stage qualification. The device is the reference-design choice in [TI TPS54561 section 8.2.1.2.5](https://www.ti.com/lit/ds/symlink/tps54561.pdf); the [manufacturer drawing](https://www.diodes.com/datasheet/download/PDS760.pdf) establishes polarity and lands. Both anode lands must be connected by PCB copper during routing.
2. Replaced both RS-485 choke footprints with `Inductor_SMD:L_CommonMode_Wurth_WE-CNSW-1206`. Also corrected the schematic pin map: upper winding 1-to-2, lower winding 4-to-3, with pins 1 and 4 on the same incoming side. Old pins 3/4 exchanged net assignments on both components. This follows the [744232090 manufacturer drawing](https://www.we-online.com/components/products/datasheet/744232090.pdf), including 1.1 x 0.6 mm lands. A footprint-only replacement would have reversed one winding.
3. Assigned **EEUFR1E102** and the stock 10 mm diameter / 5 mm pitch footprint to `C_VALVEBULK1-6`. Polarity is unchanged: pad 1 to +12V, pad 2 to GND. [Panasonic specifies a 20 mm body height](https://industrial.panasonic.com/ww/products/pt/aluminum-cap-lead/models/EEUFR1E102). The stock footprint's generic 16 mm-high 3D model was omitted to avoid a misleading height review. The 2D footprint is library geometry; exact manufacturer 3D models, enclosure clearance, finished-hole allowance and assembler acceptance are still required.
4. Corrected the cached BAV99 clamp pin names to 1=A1, 2=K2, 3=K1/A2, and assigned **BAV99LT1G** to all six clamps. Preserved all numbered-pin connections: GND, +3V3, and the corresponding sensor channel. The [onsemi datasheet](https://www.onsemi.com/pdf/datasheet/bav99lt1-d.pdf) is the pinout authority. Clamp performance and surge qualification remain open.
5. Added project-local `SWAFarm_Review.kicad_sym` and `sym-lib-table` for the two verified, geometry-preserving symbol definitions. System libraries were not changed.
6. Kept unused J2 as a schematic placeholder, excluded it from BOM/position files, and marked all three pins intentionally unconnected. It remains excluded from the board.
7. Removed the obsolete upper RS-485 direction wire stub and made the surviving join explicit. Verified that IO41 still connects only to isolator INB for direction control; the section-B pin partition is unchanged.
8. Synchronized PCB nets and sourcing fields. Added explicit Manufacturer, MPN, Datasheet and qualification status for 15 component instances (four distinct MPNs). No assembler identifiers or stock availability were invented.

## Verification evidence

All checks used KiCad 10.0.5 CLI and its bundled pcbnew, on the working copy. The project-specific MCP connector targets the original project, so it was not used for copy validation.

| Check | Before this batch | Current |
|---|---:|---:|
| ERC errors | 8 | 5 |
| ERC warnings | 15 | 6 |
| Physical DRC errors | 33 | 33 |
| Physical DRC warnings | 1 | 1 |
| Unconnected items | 422 | 425 |
| Schematic parity issues | 0 | 0 |
| PCB footprints | 184 | 185 |

The additional three unconnected items arise with the new three-land diode; they are not routed. There are still **zero tracks and zero copper zones**. Diode placement is provisional, not an approved power-loop layout.

- `erc-open-items.rpt`: five undriven-power errors (+12V, VIN_12V, +5V, +3V3, GND); six symbol-library warnings (USB connector, U3, isolated converter, RS-485 transceiver and two SM712 instances).
- `drc-open-items.rpt`: 33 existing 0.2 mm thermal-hole violations against the current 0.3 mm minimum, one MCU footprint-library mismatch, 425 unconnected items and zero parity issues. The strict DRC invocation returns exit code 1; release verification has **not** passed.
- `open-items-verification.json`: 694 pad/net assignments checked; catch-diode polarity checked; both choke remaps checked; every other component-pin net partition preserved. Existing footprint positions, orientations and UUIDs preserved. Original schematic/PCB/project hashes and working-copy project rules unchanged.
- `netlist-open-items.xml`: current exported electrical connectivity.
- `sourcing-open-items.json`: 182 exported components, of which J2 is BOM-excluded; **15/181** BOM-included instances have explicit MPN fields. **166** still lack those fields. An explicit MPN here is not an assertion of stock availability or assembler acceptance.
- `schematic-open-items.pdf` and its rendered PNGs: internal visual QA of the changed power, RS-485, sensor and valve pages. Existing schematic layout limitations are not a manufacturing sign-off.

Reversible checkpoint: `../before-open-items/` contains the design as it stood after section B. Scripts generate selective patches and check actual exported connectivity; do not rerun initial patch-generation modes against an already modified project.

## Highest-priority remaining release blockers

1. **Supply and load envelope not specified.** Need actual input source voltage range/current rating, transients, valve model, simultaneous valve count and sensor loads. The reference workbook's power-budget currents remain TBD.
2. **Q1 reverse-polarity stage unresolved.** The value `IPD50N06S4L-16` is not backed by a verified exact datasheet/order code and its SOT-23 assignment is not justified. Select an exact device and validate pinout, package, VGS stress, losses and the low-side return topology.
3. **Buck/eFuse design not qualified.** L1, compensation, switching frequency, current limit, startup and other `_TBD` values cannot be finalized from the available load data. Adding the diode does not validate them. Verify peak/ripple current, DC-biased capacitance, stability, current limits and thermal dissipation for both converters and the input protection.
4. **Placement and all routing incomplete.** The current array-like placement separates power-loop components widely. Complete functional placement, thermal copper, ground/reference planes, isolation/RF exclusions, critical routing and remaining connections only after rules and mechanics are agreed.
5. **Fab/assembler and process rules unspecified.** Resolve the 33 thermal drill violations against a chosen process, including annular ring, via filling/tenting and paste-wicking requirements. No rules have been relaxed.
6. **Connector sourcing/pin counts unresolved.** Replace or formally approve the header stand-ins for the field M12 interfaces; resolve the four-pin versus five-pin value conflict at J_OUT1 and validate valve/sensor terminal-block order codes against real drawings. Do not order historical BOM suggestions without verification.
7. **BOM still incomplete.** Qualify the remaining 166 explicit-MPN gaps, exact LoRa variant, passive ratings/tolerances, assembly side, DNP/consigned policies and all assembler part numbers. Verify quantities and availability for two assemblies; current source assignments alone do not close procurement.
8. **ERC still fails.** Resolve source/return validation before adding truthful power-output flags. Audit the remaining six cached-symbol differences against exact packages and pinouts; do not blindly replace cached definitions or suppress warnings.
9. **MCU footprint/RF review incomplete.** Investigate the remaining ESP32 footprint mismatch and verify antenna keepout, thermal pad treatment, USB routing and enclosure effects before accepting it.
10. **Mechanical and output-validation gates open.** Confirm whether 420 x 361.6 mm is required or may be reduced, mounting/connector positions, height limits, stackup, thickness, finish and assembly access. Then complete strict ERC/DRC, independent output checks, BOM/CPL alignment and human review. No orderable manufacturing ZIP was generated.

## Inputs needed to continue

- Supply model or voltage/current limits; valve model and maximum simultaneous activation; sensor supply/loading information.
- Fab/assembler target and required stackup/process, or permission to propose a two-unit POC specification for approval before routing.
- Whether the present outline may shrink, fixed connector/mounting positions and enclosure height; whether M12 interfaces must remain.

The reference workbook mentions approximately 2.5 A / 150 ms valve pulses, but leaves the usable power budget open. A 1000 uF capacitor cannot supply that entire pulse by itself: idealized I*t/C is 375 V of droop; even six in parallel imply 62.5 V. These capacitors are transient decoupling, not a substitute for a supply capable of delivering the actuation pulse. This is an engineering calculation from the reference pulse, not a verified requirement for the user's actual valve.

## Human review before ordering

- [ ] Approve actual requirements, schematic power design and exact connector parts.
- [ ] Confirm fully routed placement, heat paths, return paths, antenna/isolation keepouts and mechanics.
- [ ] Close all ERC/DRC errors and individually justify any remaining warnings.
- [ ] Complete sourcing, assembly DNP/consigned decisions, BOM and placement validation.
- [ ] Review validated Gerbers/drills, stackup, assembly drawings and final two-unit order with the selected manufacturer.
