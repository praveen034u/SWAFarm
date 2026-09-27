# Assembly and procurement - two units

BOM.csv is native KiCad CSV: 59 grouped rows, 153 fitted components per board, 306 placements across two units before attrition. Quantity is **per board**. Multiple value groups may share an MPN; combine only identical manufacturer/MPN while preserving all references. Every fitted item has exact MPN and manufacturer; no stock reservation, quote or supplier approval is implied.

CPL-KiCad.csv contains all 153 fitted SMT and THT parts. All are on top. Coordinates and rotations were checked against the PCB; KiCad native origin/sign convention and negative rotations are intentional. HOLD: assembler must map to its component-library zero orientation and confirm pin 1/polarity in a first-article drawing. Do not apply a blanket 90/180-degree correction. Mechanical holes, fiducials and test pads are intentionally excluded from procurement.

Critical no-substitution items: G5Q-14 DC12 relay coil voltage; ISO7761FDWR default-low F variant; regulated TMR 1-0511 isolated converter (not the earlier unregulated converter); RAK3172-T-8-SM-NI India/868 variant; R-78B5.0-2.0 and R-78B3.3-2.0 regulator modules; TPS26600PWP; ESP32-S3-WROOM-1-N16R8. Confirm all full orderable suffixes in BOM, not just this abbreviated list. No unapproved relay coil, RF-region, regulator, pin-compatible or passive dielectric substitutions.

Inspect LED pin 1 cathode / pin 2 anode, diodes, electrolytic polarity, IC pin 1, module orientation and connector pin labels. Relay connector pins 1/2/3 are COM/NO/NC; DC power pins 1/2 are positive/GND. Do not short TPS26600 RTN thermal island to GND. Fit sensor mode headers but leave shunts open for initial voltage-mode tests.

## Off-board equipment (not PCB BOM)

- Regulated external 12 VDC, 3 A controller supply with locally appropriate certified mains adapter. Board's nominal eFuse limit is 1.489 A; normal total input target <=1.2 A. Auxiliary output shares this limit.
- Separate isolated 24 VAC, 120 VA / 5 A valve supply; appropriately fused secondary branches and enclosure/strain relief. No mains on PCB.
- Reference valve Hunter PGV-101-G-B, 24 VAC, BSP flow control. Qualify up to eight simultaneous valves; software initially limits to one and staggers starts. Plumbing and hydraulic suitability require field engineering.
- Matching removable Phoenix plugs: obtain vendor-confirmed mates for PCB headers 1755736 (2-position), 1755749 (3-position), 1755765 (5-position), and sensor headers 1710726 (6-position). Candidate MSTB plug numbers 1757019/1757022/1757048 require final mating confirmation; do not purchase solely by pitch. Include all power, relay, bus and sensor plugs for both boards.
- Region-appropriate 50-ohm SMA antenna, USB data cable, insulated enclosure, 2.54 mm sensor-mode shunts, harnesses and branch protection. SMA jack 132134 is board-mounted, not an enclosure bulkhead part. PCB terminals are not M12 connectors.

These accessory choices are requirements/candidates, not a completed accessory purchase list. Request vendor quote, stock/lead times, traceability and component attrition allowance before ordering. Document approved substitutions and recheck affected footprints/electrical ratings. Firmware programming is not included in the fabrication files.
