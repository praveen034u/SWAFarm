# SWAFarm — TODO / Milestone Tracker

## Node V1 Hardware

### Power Supply Subsystem
- [x] Architecture designed (logical, full solar+battery scope) — 2026-07-29. See [`Documentation/SWAFarmNodeV1_PowerSupply_Design.md`](Documentation/SWAFarmNodeV1_PowerSupply_Design.md) and [`BOM/SWAFarmNodeV1_PowerSupply_BOM.csv`](BOM/SWAFarmNodeV1_PowerSupply_BOM.csv).
- [x] `01_power` schematic captured — 2026-07-30, narrower scope than the full architecture above: 12V DC input, fuse + TVS + low-side N-MOSFET reverse-polarity protection, LT8610AC buck to 3.3V (feedback divider, RT, EN/UV UVLO divider, soft-start, BST/INTVCC decoupling), power-good LED, 4 test points (VIN_PROT, 3V3_RAIL, GND, PG), net labels. Solar input, battery charging (BQ25792), and battery protection (BQ76920) from the architecture doc are **not yet captured in KiCad** — deferred to a follow-on milestone. ERC clean (0 violations) — see `Hardware/SWAFarmNodeV1/SWAFarmNodeV1_erc.json`.
- [ ] Capture solar input + battery charge/protection stage (BQ25792, BQ76920, LiFePO4 pack) in KiCad once scheduled
- [ ] Confirm solar panel Voc spec against BQ25792 22V VINDPM ceiling (Risk R-1)
- [ ] Second-source qualification for LT8610AC (used in place of LT8609A-3.3, which has no official KiCad library symbol), BQ25792, BQ76920 (Risk R-2, SWA-CST-004)
- [ ] Formal power budget (SWA-PWM-201) to lock battery capacity (Risk R-3) and confirm F1's 1.1A PTC sizing against real load current
- [ ] Start LiFePO4 pack UN38.3 / IEC 62133 certification track (Risk R-4)
- [ ] Define surge test level (IEC 61000-4-5 class) and finalize GDT/TVS coordination (Risk R-5)
- [ ] Footprint placement and routing in KiCad GUI (MCP tooling has no placement/routing capability — see Tooling note below) — handoff to schematic_designer/pcb_layout_reviewer roles
- [ ] Schematic review (pcb_layout_reviewer role) — reverse-polarity MOSFET part number, EN/UV UVLO threshold, and RT switching-frequency choice should be reconfirmed against the LT8610AC datasheet before release

### Other Subsystems (not started)
- [ ] MCU / core architecture
- [ ] LoRaWAN module integration
- [ ] RS485 Modbus interface
- [ ] Sensor front-end (5+ channels)
- [ ] Relay output driver (5 channels)
- [ ] Enclosure / mechanical design

## Tooling
- [x] KiCad MCP server configured — 2026-07-30. Seeed-Studio/kicad-mcp-server installed into KiCad 10.0's bundled Python (`C:\Program Files\KiCad\10.0\bin\python.exe`), registered with Claude Code (`claude mcp add kicad -s user`) at `C:\Users\prave\mcp-servers\kicad-mcp-server`, scoped to this project via `KICAD_PROJECT_PATHS`. Enables AI-assisted schematic/PCB analysis, netlist tracing, and ERC/DRC directly against `pcbnew` — unblocks the schematic capture and ERC steps above. Editing tools are experimental (manual S-expression manipulation); schematic capture itself should still be done in the KiCad GUI per this file's existing guidance.
- [x] KiCad MCP editing-tool defects found and worked around — 2026-07-30, during `01_power` capture:
  - `add_component_from_library`/`create_kicad_project` stamp a fictional schema `(version 20260306)`/`(generator_version "10.0")` that the installed KiCad 10.0.5 `kicad-cli` refuses to load ("Failed to load schematic" with no further detail). Fix: use a real, backward-compatible schema (`20250114`/`"9.0"`) — confirmed working. Both `SWAFarmNodeV1.kicad_sch` and `.kicad_pcb` had this bad stamp pre-existing from an earlier session and were corrected as part of this milestone.
  - `add_component_from_library` never writes the `(instances (project "..." (path "/<sheet-uuid>" (reference "...") (unit N))))` sub-block that modern KiCad schematic format requires per symbol instance. Without it, `kicad-cli sch erc` reports every pin on that symbol as "not connected" even when wires/labels are geometrically exact — this was the dominant source of false ERC errors this session, not bad coordinates. Fix: inject the block manually after placement.
  - `add_wire` silently accepts more than 2 points and writes an invalid multi-point `(wire (pts ...))` element that fails to load entirely. Always call it with exactly 2 points per segment; use multiple calls for bends.
  - Pin absolute position = `(symbol_origin_x + pin_local_x, symbol_origin_y − pin_local_y)` — the Y offset from a symbol's own library definition is negated when placed on a sheet (library Y-up vs. sheet Y-down). Getting this backwards silently swaps which physical pin a wire lands on (caught via `kicad-cli sch export netlist`, not ERC).
  - `setup_pcb_layout` fills the new `.kicad_pcb` with an unrelated placeholder footprint/nets and an invalid `title_block` field (`ki_producers`) that also fails to load — both were stripped out; only the board outline was kept.
  - No footprint-placement or routing tool exists in this MCP server's toolset — DRC is only meaningful after that's done in the KiCad GUI.

## Notes
- Milestones are appended here per CLAUDE.md instruction; this file tracks completion status only. Design rationale lives in `Documentation/`, normative engineering rules live in `.ai/knowledge/`.
