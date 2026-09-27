# SWAFarm eight-relay POC: two-unit manufacturing candidate

2026-09-26. Technically checked fabrication and assembly package; **conditional RFQ / vendor DFM release, not unconditional production sign-off**. Do not start fabrication until the vendor confirms the process items in `fab/FAB-NOTES.md`. Do not substitute parts without approval. No order or payment has been placed.

The former 370 unrouted connections and 24 thermal-hole DRC errors are resolved. Native KiCad checks: ERC 0, DRC 0, unconnected 0, schematic parity 0. Independent output validation PASS: see `review/output-validation.json`. Original project sources were preserved. The revised project is included in the full handoff archive.

- `fab/`: 11 Gerber layers, job, plated/nonplated drills and maps, normalized IPC-356 electrical-test netlist, fabrication instructions.
- `assembly/`: per-board exact-MPN BOM, native KiCad component positions, schematic and top/bottom assembly drawings, sourcing and assembly instructions.
- `review/index.html`: offline interactive layer and component inspection; keep its companion folders. Browser interaction self-test passed.
- `TEST-PLAN.md`: unperformed two-unit acceptance tests and safety restrictions.
- `review/`: strict reports, independent Gerber renders, source-to-output checks, and documented IPC export compatibility correction. The unprocessed native IPC is evidence only; use the normalized file in `fab/`.

Current board: 200 x 160 mm, four layers, 176 total footprints, 153 fitted components, 1276 tracks, 116 vias, four filled reference zones. All fitted components have manufacturer and MPN; stock and assembler rotation-library acceptance remain unconfirmed. BOM quantities are per board, not per two-unit order.

Release gates: vendor accepts thermal-hole filling/stencil, stackup/impedance and fine geometry; confirms exact sourcing and placement orientation; then purchaser authorizes fabrication. Post-build electrical/firmware/load tests are mandatory before field use, not represented as completed here. No global sale, EMC, surge, radio or safety certification is claimed.

Low-voltage supervised POC only. No mains or pump motors on this PCB. Relay outputs can remain on through an MCU software reset; provide manual water shutoff and do not operate unattended.
