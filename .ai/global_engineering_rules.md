====================================================================
PCB ARCHITECTURE CONSTRAINT
====================================================================

The final SWAFarm Node V1 PCB is planned as a four-layer PCB.

Design all schematic subsystems and component selections with this final
four-layer implementation in mind.

The intended preliminary layer strategy is:

- Layer 1: Components and signal routing
- Layer 2: Continuous solid ground plane
- Layer 3: Power distribution and selected low-speed signals
- Layer 4: Components and signal routing

During the current schematic milestone:

- Do not begin PCB routing.
- Do not finalize impedance values without the selected manufacturer's stack-up.
- Record placement, grounding, isolation, RF, thermal, and high-current constraints.
- Reserve adequate physical regions for RF, power, RS485, relays, connectors,
  battery, solar, and mechanical mounting.
- Do not assume that every schematic block can be placed anywhere on the PCB.

The final stack-up, dielectric thicknesses, copper weights, controlled-impedance
geometry, and manufacturing constraints will be confirmed before PCB routing.