# Fabrication / DFM acceptance - two POC boards

Preferred vendor: PCB Power India. Quote two assembled units and suitable panel/attrition costs. Obtain written acceptance of every HOLD below before CAM release. These instructions accompany, and do not replace, the Gerbers/drills.

## Board and process

- Finished outline 200.00 x 160.00 mm, four copper layers, FR4 nominal 1.6 mm +/-10%, ENIG, green solder mask, white legends. Edge.Cuts centerline defines the outline; rendered stroke bounds are not board dimensions.
- Layer order: F.Cu / In1.Cu / In2.Cu / B.Cu. Inner layers contain separate GND and ISO_GND reference planes. **Never merge GND, ISO_GND or EF_RTN.** No copper additions under antenna keepout or relay contact isolation region.
- Proposed finished copper 35 um on all layers; outer copper starts at 17.5 um (0.5 oz), then plates to nominal 1 oz. HOLD: confirm this process supports the 0.13 mm USB tracks and 0.12 mm spacing; a starting-1-oz process requiring 0.15 mm is not acceptable without redesign.
- Proposed dielectric: 0.105 mm prepreg / 1.200 mm core / 0.105 mm prepreg; nominal Dk 4.3. This is a published starting stack, not a vendor-approved impedance solution. HOLD: solve and approve 90 ohm +/-10% differential USB (nominal 0.13 width / 0.12 gap) and 50 ohm +/-10% RF (0.15 width), with coupons if offered. Return any geometry changes for review; do not silently change copper.
- Ordinary track/clearance 0.25/0.20 mm, ordinary vias 0.80/0.30 mm; minimum track rule 0.125 mm; finished hole minimum 0.30 mm; annular ring rule 0.15 mm; hole-to-copper and hole-to-hole rules 0.25 mm; copper-to-edge 0.50 mm. Special RF/USB rules are recorded in project.
- Mask expansion 0.06 mm, minimum web 0.08 mm, mask-to-unrelated-copper 0.10 mm. Legend minimum height 1.0 mm. Preserve existing mask apertures and polarity.

## Mandatory thermal-pad process acceptance

There are 24 finished 0.30 mm thermal holes with 0.70 mm lands: 12 each at U1 and U_MCU1. Do not reduce them to 0.20 mm. They overlap exposed-pad solder regions. HOLD: assembler/fab must approve a filled/plugged/tented process that prevents solder loss and provides acceptable pad planarity; simply leaving holes open under paste is not approved. PCB Power publishes nonconductive solder-mask ink fill up to 0.35 mm, but suitability here must be confirmed, not assumed equivalent to resin-filled/capped via-in-pad.

U1 TPS26600 thermal copper is 3.4 x 5.0 mm, with 3.3 x 3.3 mm mask/paste window based on TI's package example for a nominal 0.125 mm stencil. MCU retains nine paste windows. HOLD: approve stencil thickness/apertures and thermal-pad inspection method against the chosen fill process. Request X-ray/process evidence for hidden joints.

## Assembly interfaces and inspection

Four M3 nonplated mounting holes; three global and two local fiducials. Components fit on top, mixed SMT/THT. Panel rails/tab locations must preserve USB access, antenna edge keepout and mounting holes; submit proposed panel drawing. No unapproved board resizing or hole moves.

The local USB4105 footprint uses slightly shortened/repositioned outer ground lands to satisfy the 0.25 mm peg-hole copper clearance. HOLD: assembler reviews solderability against GCT drawing. Mechanical peg, shell and signal positions are retained. Local MCU/eFuse footprints intentionally differ from stock thermal-hole patterns.

Perform 100% bare-board shorts/opens test using the normalized `SWAFarmNodeV1.ipc` plus Gerber X2 data. Review IPC normalization evidence if importing into CAM; it corrects KiCad 10.0.5 mask-field formatting only. Inspect drill plating, slots, mask registration and isolation gaps. All 289 distinct drill features were independently matched to source geometry (283 plated, 6 nonplated).

Sources: [capabilities](https://www.pcbpower.com/technology/technical-capabilities-rigid-pcb), [stackups](https://www.pcbpower.com/impedance-controlled-standard-build-ups), [assembly guidance](https://www.pcbpower.com/design-guideline-pcba), [TI TPS2660](https://www.ti.com/lit/ds/symlink/tps2660.pdf), [GCT USB4105](https://gct.co/files/drawings/usb4105.pdf).
