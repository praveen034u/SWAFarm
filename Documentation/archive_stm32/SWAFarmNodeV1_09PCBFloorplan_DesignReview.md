# SWAFarm Node V1 — Step 09: PCB Floor Planning and Component Placement — Design Review

**Status:** Placement complete, DRC clean of all physical/electrical placement violations (0 courtyard overlaps, 0 shorts, 0 co-located holes). Awaiting approval before Step 10 (routing).
**Date:** 2026-07-31

---

## 1. Executive Summary

This milestone imported all 199 approved schematic components into a fresh 4-layer `.kicad_pcb`, established the board outline and layer stack, and placed every component into functional zones per the `SWAFarmNodeV1_PCB_FloorPlan_and_LayerStrategy.md` planning document written back in `05_LoRaWAN`. No routing, copper pours, or trace widths were touched, per explicit scope.

The existing `.kicad_pcb` was found to contain corrupted placeholder geometry from initial project setup (an "Edge.Cuts" outline with coordinates at `INT32_MAX/1e6` — a ~2147mm × 2147mm board, clearly a tool artifact never cleaned up) and only 27 of the schematic's 199 components. It was rebuilt from scratch rather than patched. Since no MCP tool exists for PCB footprint placement (a gap already documented in `TODO.md`'s Tooling section), this milestone used KiCad's own bundled Python (`pcbnew` scripting API) rather than hand-editing raw `.kicad_pcb` S-expressions — a deliberate departure from this project's usual direct-file-editing technique, justified in §9 (Manufacturing Considerations) and the new Tooling note (§13).

A real, previously-undetected schematic defect was found and fixed during this milestone: `J2` (Solar-IN connector, added in `08_BatterySolar`) had an empty `Footprint` property — it would not have been manufacturable. Caught by a footprint-resolution verification pass before any placement was attempted, not by chance.

---

## 2. Board Dimensions

**300mm × 220mm, 4-layer.**

**Why this size:** driven bottom-up by real connector counts and courtyard-verified component footprints, not chosen arbitrarily or minimized for area:
- 5× RS485 field connectors + 5× relay field connectors (10 industrial screw-terminal connectors total) each need real clearance for cable approach, tool access, and — for the relay row specifically — a genuine 29.55mm × 12.95mm relay body (Finder 40.51, courtyard-measured, not estimated) between adjacent channels.
- 3 power-related connectors (DC-IN, Solar-IN, Battery) plus an RF antenna connector, a SWD header, and a UART debug header all need edge placement per the task's explicit "connectors define the board perimeter" requirement.
- An initial 220×200mm attempt (first placement pass) produced real courtyard collisions and one relay's silkscreen extending past the board edge — confirming the smaller size was undersized for this connector count, not just tight. Board size was increased to 300×220mm specifically to resolve those, not chosen first and justified after.

**Mechanical assumptions:** 1.6mm board thickness (KiCad default, unchanged — no fabricator/stack-up selected yet per the standing global constraint); 4× M3 mounting holes at the corners (10mm inset), matching the M3 corner pattern already specified in `03_HMI` §7.

**Future enclosure considerations:** this size is large enough to need a purpose-built enclosure (not an off-the-shelf small project box) — consistent with `mechanical_design.md`'s IP65 industrial enclosure objective. No enclosure design exists yet (per `TODO.md`, still "not started"); this board size should be treated as an *input* to that future milestone, not adjusted to fit a box chosen without reference to it — the same principle the floor-plan document already established for board outline generally.

---

## 3. Functional Floorplan

| Zone | Location | Contents |
|---|---|---|
| **Power** | Top-left (X10-130, Y10-85) | DC-IN (`J1`) + Solar-IN (`J2`) protection stages (mirrored topology), buck converter `U1`, charger `U_CHG1` + support |
| **Battery** | Top-middle (X138-200, Y10-85) | Battery pack connector `J3`, protection AFE `U_PROT1`, low-side FET pair, sense shunt, cell-tap network |
| **RF** | Top-right (X210-290, Y10-70) | LoRa module `U_LORA1`, antenna connector `J_LORA_ANT1` — farthest zone from every switching/noisy block |
| **RS485** | Left column (X10-100, Y80-215) | Transceiver `U_RS485_1`, protection/bias/termination, all 5 sensor field connectors on the left board edge |
| **MCU** | Center (X95-160, Y75-135) | `U_MCU1` as the hub, decoupling capacitors tightly ringed around it (§8) |
| **Debug** | Right, upper (X165-210, Y75-115) | SWD header `J_SWD1`, UART debug header `J_DBG_UART1` |
| **HMI** | Right, middle (X165-210, Y118-138) | Activity LED, user button, reset button |
| **Relay** | Bottom (X95-210, Y140-195) | 5 identical relay driver channels, all 5 relay field connectors on the bottom board edge |

This is a direct, coordinate-level realization of the zone-adjacency diagram already approved in `SWAFarmNodeV1_PCB_FloorPlan_and_LayerStrategy.md` §3 — that document's relative-adjacency rules (RF farthest from switching, external connectors clustered at edges by real-world cable entry point, MCU as central hub, relay/sensor zones kept apart) were followed, not re-derived from scratch.

*(See `Documentation/images/SWAFarmNodeV1_09PCB_TopView_Placement.png` for a rendered top-down view of the final placement.)*

---

## 4. Placement Strategy

Each of the 199 schematic components was categorized into one of the 8 zones above by reference-designator pattern (verified to cover all 199 components with zero unassigned), then placed using:
1. **Hand-placed anchors** for the ~20 major parts (ICs, connectors, the relay bank) — precise, deliberate positions matching the zone-adjacency plan.
2. **A generic grid-fill helper** for the remaining small passives within each zone's leftover space.

**A real lesson learned mid-milestone:** the first placement pass used footprint-size *assumptions* (e.g., estimating relay connector pitch from the schematic's own visual spacing) rather than measured data, and produced 38 courtyard overlaps, 32 net-shorting collisions, and 4 co-located mounting holes on the first DRC pass. This was corrected by querying every unique footprint's **real courtyard geometry** directly via the `pcbnew` API (not the misleading full bounding box, which includes silkscreen reference text and can overstate a small connector's footprint by 3×) before re-placing — the same "verify against real data, don't guess" discipline this project has applied to library symbols throughout, now applied to physical footprint geometry. Iterating against real `kicad-cli pcb drc` output (not just visual inspection) caught every remaining collision precisely.

---

## 5. RF Region

- `U_LORA1` (RAK3172) and `J_LORA_ANT1` occupy the top-right corner (X210-290, Y10-70) — the single farthest zone on the board from both the power stage's switching loop (top-left) and the relay bank (bottom), directly implementing SWA-PDR-003 and the floor-plan doc's own RF-isolation rule.
- No power, relay, or battery components were placed anywhere in or adjacent to this zone.
- **Ground clearance / stitching**: not yet applicable at the placement stage — no copper pours or ground plane exist yet (explicitly out of scope this milestone). The floor-plan doc's requirement ("L2 ground plane must remain fully continuous and unslotted directly under the RF zone") is carried forward unchanged as a routing-stage constraint — recorded here, not yet actionable.
- **Antenna clearance**: `J_LORA_ANT1` sits at the board's outer edge with no other component within its immediate footprint radius, preserving room for a coax pigtail bend and keeping tall/shielded components (none currently exist in this design) out of the near-field region above the module, per `05_LoRaWAN` §6.
- **No noisy circuitry nearby**: confirmed by construction — the nearest zone boundary (Battery, ending at X200) is 10mm clear of the RF zone's start (X210), and the nearest high-current zone (Relay, Y140+) is over 70mm away vertically.

---

## 6. High Current Region

- **Relay outputs** (bottom zone, Y140-195): physically the farthest functional zone from RF (diagonal opposite corner of the board), consistent with SWA-PDR-002 ("keep relay and inductive switching currents away from sensor reference paths") and the floor-plan doc's pre-existing relay/RF separation rule.
- **Power input / Battery** (top-left and top-middle): kept together per the floor-plan doc's rationale (both are DC power-path stages that belong in one thermal/electrical neighborhood), physically separated from RF (top-right) by the Battery zone's own width (~65mm) and from the Relay zone by the MCU/RS485 zones (~55-70mm).
- **Solar** input protection is co-located with the Power zone (mirrors DC-IN exactly, same reasoning as `08_BatterySolar`), not a separate physical region — consistent with both being external DC sources feeding the same charger IC.
- No high-current zone is adjacent to the RF zone or to the RS485 zone's differential-pair region.

---

## 7. Connector Placement

Every connector required by the task is placed on the board perimeter:

| Connector | Reference | Edge |
|---|---|---|
| Power input | `J1` | Top |
| Solar input | `J2` | Top |
| Battery | `J3` | Top |
| RF antenna | `J_LORA_ANT1` | Top-right corner |
| SWD programming header | `J_SWD1` | Right |
| UART debug header | `J_DBG_UART1` | Right |
| RS485 sensor ×5 | `J_RS485_SENSOR1`–`5` | Left |
| Relay output ×5 | `J_RELAY11`–`J_RELAY51` | Bottom |

Mounting holes (`MH1`–`MH4`) sit at all four corners, clear of every connector and zone. Debug/programming headers are grouped on the right edge specifically for technician tool access without disturbing the field-wiring connectors on the other three edges — matching `mechanical_design.md`'s "physical access to debug/program ports must be controlled" requirement and this project's own established SWD/UART accessibility precedent.

---

## 8. Decoupling Strategy

Every IC with a schematic-defined decoupling/filter network was reviewed:

- **`U_MCU1`**: initial placement put its 8 decoupling capacitors (`C_MCU_VBAT1`, `C_MCU_VDD1-3`, `C_MCU_VDDA1-2`, `C_MCU_VDDUSB1`, `C_MCU_BULK1`) 20-32mm away in a distant row — reviewed against this milestone's own explicit "verify decoupling placement" requirement and found inadequate. **Corrected**: all 8 now sit in a tight ring within ~12mm of the MCU package on both sides, with `FB_MCU1` (the VDDA ferrite-bead filter already established in `02_MCU`) directly below it.
- **`U_CHG1`** (charger): `C_PMID1`, `C_REGN1`, `C_SYS1` — the three filter/decoupling caps most sensitive to trace length for switching-noise suppression — were similarly found at 30-46mm and pulled in to ~14mm.
- **`U_RS485_1`**: `C_RS485_VCC1` and the TVS/bias network were already placed within ~15mm during the initial pass — no correction needed.
- **`U_PROT1`, `U1`, `U_LORA1`**: local decoupling/filter passives (`C_CAP1_1`/`C_REGOUT1`; `Cin1/2`, `Cout1/2`, `C_BST1`, `C_INTVCC1`, `C_SS1`; `C_LORA_VDD1`) are all placed within their respective IC's immediate zone cluster.

**Ground return**: not yet routable (no copper exists), but every decoupling cap's GND pad was net-assigned during placement (§9) to the shared `GND` net, so the upcoming routing milestone can verify short-return-path compliance directly via ratsnest rather than needing to re-derive net membership.

---

## 9. Manufacturing Considerations

- **Tooling gap and workaround (new this milestone)**: no MCP tool exists for PCB footprint placement, board-outline creation, or layer-stack configuration (confirmed by searching the full available tool list before starting). This milestone used KiCad 10's own bundled Python (`C:\Program Files\KiCad\10.0\bin\python.exe`, `pcbnew` module) — the same interpreter this project's MCP server itself runs on — via `pcbnew.FootprintLoad()` to pull real, verified footprint geometry directly from the system footprint libraries, rather than hand-authoring or guessing footprint S-expressions. This is more reliable than the direct-file-splice technique used for schematic work in Steps 06/08, since `pcbnew` guarantees geometrically-correct pad/courtyard data straight from the library rather than requiring manual extraction.
- **Real footprint verification**: all 34 unique footprint strings used across the 199 schematic components were confirmed to resolve to real files in the stock KiCad footprint libraries before any placement was attempted (one gap found and fixed — see §1).
- **Net-aware placement**: every pad was assigned its correct net from the schematic netlist during placement (188 nets total) — not just positioned. This means the next milestone's ratsnest and DRC connectivity checks will work correctly from the first load, rather than needing a separate "import netlist" pass.
- **Design rule adjustment**: the default board (freshly created) had a minimum-hole-size rule (0.3mm) that falsely flagged `U1`'s legitimate 0.25mm thermal-via pattern (an existing, already-approved `01_power` footprint detail). Relaxed to 0.2mm, matching common PCB fabricator capability — a board-setup correction, not a routing decision.
- **Assembly/AOI access**: zone separation (Power/Battery/RF along the top, RS485/Relay along the left/bottom, MCU/Debug/HMI in the middle-right) keeps no zone's components stacked against another's, preserving pick-and-place and AOI camera access per `pcb_layout_reviewer.md`'s mandatory checks.

---

## 10. Thermal Considerations

- Carried forward unchanged from `SWAFarmNodeV1_PCB_FloorPlan_and_LayerStrategy.md` §8 (Power/Battery zones flagged for thermal-via strategy under `U1`/`U_CHG1`, Relay zone flagged for coil/contact dissipation) — this milestone's placement satisfies the *physical separation* half of that plan (heat sources are not stacked against thermally-sensitive neighbors) but does not yet implement thermal vias or copper pour heat-spreading, which are routing-stage work explicitly out of scope here.
- The charger (`U_CHG1`, VQFN-29 with exposed thermal pad) and buck converter (`U1`) sit adjacent to each other in the Power zone rather than against the RF or MCU zones — confirmed via the rendered placement, not just intended.

---

## 11. Risks

| ID | Risk | Status |
|---|---|---|
| R-PCB-1 | 41 `silk_overlap`/`silk_over_copper` DRC warnings remain — reference-designator text collisions in densely-populated sub-areas (Power zone, Relay driver stacks). Purely cosmetic (no physical/electrical collision); normal for a placement-stage pass | Open — resolve in a dedicated silkscreen cleanup pass, typically done alongside or after routing when final component orientation is locked |
| R-PCB-2 | Board size (300×220mm) was sized from courtyard-verified connector/component geometry, not validated against any real enclosure — no enclosure design exists yet | Open — carried forward from the floor-plan doc's own open item; revisit once enclosure milestone begins |
| R-PCB-3 | Ground plane continuity, RF keepout copper exclusion, and thermal via strategy are all *planned* (floor-plan doc) but not yet *implemented* — this milestone is placement-only by explicit scope | Open by design — Step 10 (routing) scope |
| R-PCB-4 | Mounting hole positions (10mm corner inset) are a placement-stage estimate, not validated against real enclosure boss/standoff geometry | Open — same dependency as R-PCB-2 |

---

## 12. Recommendations

1. Proceed to routing (Step 10) using this placement as the input — do not re-floorplan without cause; the zone structure has been visually and DRC-verified.
2. Address the 41 remaining silk-overlap warnings during routing, when final orientations are locked (many will resolve naturally as components are nudged for trace access).
3. When the enclosure milestone begins, treat this board's 300×220mm outline and corner mounting-hole positions as an input to enclosure design, consistent with the floor-plan doc's stated principle for board outline generally.
4. Confirm decoupling cap placement for `U_MCU1` and `U_CHG1` remains within ~12-15mm after any routing-stage nudges — don't let trace-length optimization silently regress the proximity fixed in this milestone.

---

## 13. PCB Screenshots

Top-down rendered view (`kicad-cli pcb render`) saved to [`Documentation/images/SWAFarmNodeV1_09PCB_TopView_Placement.png`](images/SWAFarmNodeV1_09PCB_TopView_Placement.png) — shows all 8 functional zones, the 4-layer board outline, and all 199 placed components plus 4 mounting holes.

---

## 14. Documentation Updates

- This document created.
- `TODO.md`: new "PCB Floor Planning and Component Placement" milestone entry (see below), plus a new Tooling entry documenting the `pcbnew`-scripting technique and the real-vs-assumed-footprint-size lesson.
- `SWAFarmNodeV1_PCB_FloorPlan_and_LayerStrategy.md` §11 (Per-Subsystem Region Reservation Summary): to be updated marking every row "Captured" in placement, not just schematic — see below.
- `J2`'s empty `Footprint` property fixed in `SWAFarmNodeV1.kicad_sch` (§1) — a real defect fix to already-approved `08_BatterySolar` circuitry, disclosed explicitly per this project's established practice, not a silent change.
- **Note on `NodeForRefrence.csv`**: reviewed at the user's request mid-milestone; confirmed to describe an unrelated parallel product specification (different MCU, different power architecture, different product family: `HUB_CORE`/`NODE_CORE`/`MOTOR_CONTROLLER`) rather than a refinement of this board. Per explicit user direction, not incorporated into this design. No further action taken on it.
