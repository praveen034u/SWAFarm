# SWAFarm Requirement Traceability Index

## Executive Summary
This index is the consolidated registry of normative SWAFarm requirement IDs across the AI knowledge base. It supports requirement-to-test mapping, release reviews, and change impact analysis.

## Purpose
Provide a single lookup table for all SWA-PREFIX-NNN requirement IDs and their source documents.

## Scope
Applies to all Markdown standards files in AI/knowledge except this index file.

## ID Range Legend
- 0xx: Engineering Rules
- 1xx: Performance Targets
- 2xx: Required Practices
- 3xx: Design Constraints

## Summary by Document
| Document | Total IDs | 0xx Rules | 1xx Performance | 2xx Practices | 3xx Constraints |
|---|---:|---:|---:|---:|---:|
| certification_requirements.md | 12 | 3 | 3 | 3 | 3 |
| cloud_integration.md | 12 | 3 | 3 | 3 | 3 |
| coding_standards.md | 13 | 4 | 3 | 3 | 3 |
| component_standards.md | 14 | 4 | 3 | 3 | 4 |
| cost_targets.md | 12 | 3 | 3 | 3 | 3 |
| firmware_architecture.md | 13 | 4 | 3 | 3 | 3 |
| hardware_requirements.md | 17 | 4 | 4 | 4 | 5 |
| manufacturing_rules.md | 13 | 4 | 3 | 3 | 3 |
| mechanical_design.md | 12 | 3 | 3 | 3 | 3 |
| pcb_design_rules.md | 15 | 5 | 3 | 3 | 4 |
| power_management.md | 12 | 3 | 3 | 3 | 3 |
| project_glossary.md | 10 | 3 | 2 | 2 | 3 |
| rf_lorawan_standards.md | 12 | 3 | 3 | 3 | 3 |
| security_standards.md | 13 | 4 | 3 | 3 | 3 |
| swafarm_overview.md | 26 | 6 | 7 | 6 | 7 |
| testing_standards.md | 12 | 3 | 3 | 3 | 3 |

## Master Index
| Requirement ID | Section Class | Source Document | Source Heading | Requirement Label |
|---|---|---|---|---|
| SWA-CER-001 | Engineering Rules | certification_requirements.md | Engineering Rules | No regional shipment without approved compliance package. |
| SWA-CER-002 | Engineering Rules | certification_requirements.md | Engineering Rules | No RF path change without recertification impact review. |
| SWA-CER-003 | Engineering Rules | certification_requirements.md | Engineering Rules | No uncontrolled BOM substitutions in certified assemblies. |
| SWA-CER-101 | Performance Targets | certification_requirements.md | Performance Targets | Certification pass rate |
| SWA-CER-102 | Performance Targets | certification_requirements.md | Performance Targets | Recertification lead time |
| SWA-CER-103 | Performance Targets | certification_requirements.md | Performance Targets | Compliance escapes |
| SWA-CER-201 | Required Practices | certification_requirements.md | Required Practices | Maintain region-by-region compliance matrix. |
| SWA-CER-202 | Required Practices | certification_requirements.md | Required Practices | Perform pre-compliance testing before formal lab booking. |
| SWA-CER-203 | Required Practices | certification_requirements.md | Required Practices | Keep certification artifacts linked to hardware and firmware revision identifiers. |
| SWA-CER-301 | Design Constraints | certification_requirements.md | Design Constraints | RF parameters |
| SWA-CER-302 | Design Constraints | certification_requirements.md | Design Constraints | EMC margin |
| SWA-CER-303 | Design Constraints | certification_requirements.md | Design Constraints | Documentation |
| SWA-CLD-001 | Engineering Rules | cloud_integration.md | Engineering Rules | No breaking API change without migration path. |
| SWA-CLD-002 | Engineering Rules | cloud_integration.md | Engineering Rules | No command execution without authorization and audit. |
| SWA-CLD-003 | Engineering Rules | cloud_integration.md | Engineering Rules | No OTA campaign without segmentation and rollback controls. |
| SWA-CLD-101 | Performance Targets | cloud_integration.md | Performance Targets | Telemetry ingest success |
| SWA-CLD-102 | Performance Targets | cloud_integration.md | Performance Targets | Command delivery reliability |
| SWA-CLD-103 | Performance Targets | cloud_integration.md | Performance Targets | OTA orchestration integrity |
| SWA-CLD-201 | Required Practices | cloud_integration.md | Required Practices | Maintain schema registry with compatibility checks. |
| SWA-CLD-202 | Required Practices | cloud_integration.md | Required Practices | Implement idempotency in critical write paths. |
| SWA-CLD-203 | Required Practices | cloud_integration.md | Required Practices | Define SLOs and error budgets for core services. |
| SWA-CLD-301 | Design Constraints | cloud_integration.md | Design Constraints | Mixed fleet support |
| SWA-CLD-302 | Design Constraints | cloud_integration.md | Design Constraints | Latency critical commands |
| SWA-CLD-303 | Design Constraints | cloud_integration.md | Design Constraints | Data retention |
| SWA-CDS-001 | Engineering Rules | coding_standards.md | Engineering Rules | No merge without passing CI quality gates. |
| SWA-CDS-002 | Engineering Rules | coding_standards.md | Engineering Rules | No silent error swallowing. |
| SWA-CDS-003 | Engineering Rules | coding_standards.md | Engineering Rules | No undefined ownership semantics in memory/resource management. |
| SWA-CDS-004 | Engineering Rules | coding_standards.md | Engineering Rules | No hard-coded credentials or environment secrets. |
| SWA-CDS-101 | Performance Targets | coding_standards.md | Performance Targets | Build reproducibility |
| SWA-CDS-102 | Performance Targets | coding_standards.md | Performance Targets | Defect leakage |
| SWA-CDS-103 | Performance Targets | coding_standards.md | Performance Targets | Mean review turnaround |
| SWA-CDS-201 | Required Practices | coding_standards.md | Required Practices | Use strict compiler warnings and treat critical warnings as errors. |
| SWA-CDS-202 | Required Practices | coding_standards.md | Required Practices | Write unit tests for all non-trivial logic. |
| SWA-CDS-203 | Required Practices | coding_standards.md | Required Practices | Use code reviews with at least one domain reviewer. |
| SWA-CDS-301 | Design Constraints | coding_standards.md | Design Constraints | Cyclomatic complexity |
| SWA-CDS-302 | Design Constraints | coding_standards.md | Design Constraints | Test coverage |
| SWA-CDS-303 | Design Constraints | coding_standards.md | Design Constraints | Dependency policy |
| SWA-CST-001 | Engineering Rules | component_standards.md | Engineering Rules | No NRND components in new designs. |
| SWA-CST-002 | Engineering Rules | component_standards.md | Engineering Rules | No components lacking traceable manufacturer data. |
| SWA-CST-003 | Engineering Rules | component_standards.md | Engineering Rules | No custom-only parts without business-approved risk case. |
| SWA-CST-004 | Engineering Rules | component_standards.md | Engineering Rules | Critical parts shall have approved alternates before MP ramp. |
| SWA-CST-101 | Performance Targets | component_standards.md | Performance Targets | Approved alternate coverage |
| SWA-CST-102 | Performance Targets | component_standards.md | Performance Targets | EOL exposure |
| SWA-CST-103 | Performance Targets | component_standards.md | Performance Targets | Qualification cycle time |
| SWA-CST-201 | Required Practices | component_standards.md | Required Practices | Maintain AVL with manufacturer part number, alternates, and qualification status. |
| SWA-CST-202 | Required Practices | component_standards.md | Required Practices | Perform fit-form-function evaluation before substitutions. |
| SWA-CST-203 | Required Practices | component_standards.md | Required Practices | Use derating policy for voltage, current, power, and temperature stress. |
| SWA-CST-301 | Design Constraints | component_standards.md | Design Constraints | Electrolytic capacitors |
| SWA-CST-302 | Design Constraints | component_standards.md | Design Constraints | Relays |
| SWA-CST-303 | Design Constraints | component_standards.md | Design Constraints | Connectors |
| SWA-CST-304 | Design Constraints | component_standards.md | Design Constraints | TVS/protection parts |
| SWA-CTT-001 | Engineering Rules | cost_targets.md | Engineering Rules | No cost-down change without validation against reliability and quality KPIs. |
| SWA-CTT-002 | Engineering Rules | cost_targets.md | Engineering Rules | No single-source dependency accepted solely for short-term cost gain. |
| SWA-CTT-003 | Engineering Rules | cost_targets.md | Engineering Rules | No change that increases field service frequency without executive approval. |
| SWA-CTT-101 | Performance Targets | cost_targets.md | Performance Targets | BOM reduction trajectory |
| SWA-CTT-102 | Performance Targets | cost_targets.md | Performance Targets | Cost of poor quality |
| SWA-CTT-103 | Performance Targets | cost_targets.md | Performance Targets | Warranty cost per device |
| SWA-CTT-201 | Required Practices | cost_targets.md | Required Practices | Maintain costed BOM by revision and volume band. |
| SWA-CTT-202 | Required Practices | cost_targets.md | Required Practices | Track yield-adjusted cost, not nominal BOM alone. |
| SWA-CTT-203 | Required Practices | cost_targets.md | Required Practices | Run formal engineering change review for all cost-down proposals. |
| SWA-CTT-301 | Design Constraints | cost_targets.md | Design Constraints | Reliability floor |
| SWA-CTT-302 | Design Constraints | cost_targets.md | Design Constraints | Certification impact |
| SWA-CTT-303 | Design Constraints | cost_targets.md | Design Constraints | Firmware impact |
| SWA-FWA-001 | Engineering Rules | firmware_architecture.md | Engineering Rules | No blocking calls in timing-critical task contexts without bounded timeout. |
| SWA-FWA-002 | Engineering Rules | firmware_architecture.md | Engineering Rules | No direct hardware register access from business logic layers. |
| SWA-FWA-003 | Engineering Rules | firmware_architecture.md | Engineering Rules | No production build with disabled watchdog strategy. |
| SWA-FWA-004 | Engineering Rules | firmware_architecture.md | Engineering Rules | All externally visible payloads and commands must be versioned. |
| SWA-FWA-101 | Performance Targets | firmware_architecture.md | Performance Targets | Boot-to-operational readiness |
| SWA-FWA-102 | Performance Targets | firmware_architecture.md | Performance Targets | OTA completion reliability |
| SWA-FWA-103 | Performance Targets | firmware_architecture.md | Performance Targets | Protocol command timeout handling |
| SWA-FWA-201 | Required Practices | firmware_architecture.md | Required Practices | Maintain state diagrams for critical control flows. |
| SWA-FWA-202 | Required Practices | firmware_architecture.md | Required Practices | Enforce static analysis and MISRA-inspired safe coding constraints. |
| SWA-FWA-203 | Required Practices | firmware_architecture.md | Required Practices | Execute regression suite for each release candidate. |
| SWA-FWA-301 | Design Constraints | firmware_architecture.md | Design Constraints | Memory headroom |
| SWA-FWA-302 | Design Constraints | firmware_architecture.md | Design Constraints | Power budget |
| SWA-FWA-303 | Design Constraints | firmware_architecture.md | Design Constraints | OTA robustness |
| SWA-HWR-001 | Engineering Rules | hardware_requirements.md | Engineering Rules | Do not use hobby-grade connectors, relays, or regulator families. |
| SWA-HWR-002 | Engineering Rules | hardware_requirements.md | Engineering Rules | All critical components require second-source or approved mitigation. |
| SWA-HWR-003 | Engineering Rules | hardware_requirements.md | Engineering Rules | Every external line shall include protection against ESD and surge classes defined by system test plans. |
| SWA-HWR-004 | Engineering Rules | hardware_requirements.md | Engineering Rules | Board interfaces shall be revisioned and documented before layout release. |
| SWA-HWR-101 | Performance Targets | hardware_requirements.md | Performance Targets | Sleep current |
| SWA-HWR-102 | Performance Targets | hardware_requirements.md | Performance Targets | Relay actuation reliability |
| SWA-HWR-103 | Performance Targets | hardware_requirements.md | Performance Targets | Sensor data acquisition validity |
| SWA-HWR-104 | Performance Targets | hardware_requirements.md | Performance Targets | Field uptime |
| SWA-HWR-201 | Required Practices | hardware_requirements.md | Required Practices | Assign requirement IDs to all electrical and mechanical constraints. |
| SWA-HWR-202 | Required Practices | hardware_requirements.md | Required Practices | Validate sensor and relay channels under worst-case temperature and supply variation. |
| SWA-HWR-203 | Required Practices | hardware_requirements.md | Required Practices | Verify sleep current using production-representative hardware. |
| SWA-HWR-204 | Required Practices | hardware_requirements.md | Required Practices | Include production test points for major power rails and communication interfaces. |
| SWA-HWR-301 | Design Constraints | hardware_requirements.md | Design Constraints | MCU headroom |
| SWA-HWR-302 | Design Constraints | hardware_requirements.md | Design Constraints | RS485 network tolerance |
| SWA-HWR-303 | Design Constraints | hardware_requirements.md | Design Constraints | Relay subsystem |
| SWA-HWR-304 | Design Constraints | hardware_requirements.md | Design Constraints | Charging subsystem |
| SWA-HWR-305 | Design Constraints | hardware_requirements.md | Design Constraints | Connector strategy |
| SWA-MFR-001 | Engineering Rules | manufacturing_rules.md | Engineering Rules | No production release without validated test coverage report. |
| SWA-MFR-002 | Engineering Rules | manufacturing_rules.md | Engineering Rules | No unmanaged process parameter changes on active lines. |
| SWA-MFR-003 | Engineering Rules | manufacturing_rules.md | Engineering Rules | No shipment from lots with unresolved critical defects. |
| SWA-MFR-004 | Engineering Rules | manufacturing_rules.md | Engineering Rules | Every unit must carry traceable identity and firmware manifest. |
| SWA-MFR-101 | Performance Targets | manufacturing_rules.md | Performance Targets | First Pass Yield |
| SWA-MFR-102 | Performance Targets | manufacturing_rules.md | Performance Targets | Defect escape rate |
| SWA-MFR-103 | Performance Targets | manufacturing_rules.md | Performance Targets | Rework rate |
| SWA-MFR-201 | Required Practices | manufacturing_rules.md | Required Practices | Maintain control plan and PFMEA per product family. |
| SWA-MFR-202 | Required Practices | manufacturing_rules.md | Required Practices | Enforce golden sample and fixture calibration schedule. |
| SWA-MFR-203 | Required Practices | manufacturing_rules.md | Required Practices | Record per-unit test results with timestamp and station ID. |
| SWA-MFR-301 | Design Constraints | manufacturing_rules.md | Design Constraints | Fixture cycle time |
| SWA-MFR-302 | Design Constraints | manufacturing_rules.md | Design Constraints | Station downtime |
| SWA-MFR-303 | Design Constraints | manufacturing_rules.md | Design Constraints | Rework policy |
| SWA-MEC-001 | Engineering Rules | mechanical_design.md | Engineering Rules | No enclosure change without environmental regression review. |
| SWA-MEC-002 | Engineering Rules | mechanical_design.md | Engineering Rules | Cable entry paths must preserve ingress and strain relief integrity. |
| SWA-MEC-003 | Engineering Rules | mechanical_design.md | Engineering Rules | Mounting design must tolerate installation variability. |
| SWA-MEC-101 | Performance Targets | mechanical_design.md | Performance Targets | Enclosure leak failures |
| SWA-MEC-102 | Performance Targets | mechanical_design.md | Performance Targets | Mounting-related field returns |
| SWA-MEC-103 | Performance Targets | mechanical_design.md | Performance Targets | Connector mechanical failures |
| SWA-MEC-201 | Required Practices | mechanical_design.md | Required Practices | Conduct tolerance stack analysis for all sealed interfaces. |
| SWA-MEC-202 | Required Practices | mechanical_design.md | Required Practices | Validate assembly torque windows and fastener retention. |
| SWA-MEC-203 | Required Practices | mechanical_design.md | Required Practices | Verify connector access under field installation constraints. |
| SWA-MEC-301 | Design Constraints | mechanical_design.md | Design Constraints | Thermal rise |
| SWA-MEC-302 | Design Constraints | mechanical_design.md | Design Constraints | UV exposure |
| SWA-MEC-303 | Design Constraints | mechanical_design.md | Design Constraints | Vibration and shock |
| SWA-PDR-001 | Engineering Rules | pcb_design_rules.md | Engineering Rules | Place power conversion and switching loops compactly. |
| SWA-PDR-002 | Engineering Rules | pcb_design_rules.md | Engineering Rules | Keep relay and inductive switching currents away from sensor reference paths. |
| SWA-PDR-003 | Engineering Rules | pcb_design_rules.md | Engineering Rules | Maintain explicit RF keepout regions and validated antenna placement. |
| SWA-PDR-004 | Engineering Rules | pcb_design_rules.md | Engineering Rules | Route RS485 differential pairs with controlled topology and protection proximity. |
| SWA-PDR-005 | Engineering Rules | pcb_design_rules.md | Engineering Rules | No unrouted or unreviewed net exceptions at release. |
| SWA-PDR-101 | Performance Targets | pcb_design_rules.md | Performance Targets | Manufacturing first-pass PCB yield |
| SWA-PDR-102 | Performance Targets | pcb_design_rules.md | Performance Targets | EMI/EMC pre-compliance pass rate |
| SWA-PDR-103 | Performance Targets | pcb_design_rules.md | Performance Targets | Field noise-related sensor defects |
| SWA-PDR-201 | Required Practices | pcb_design_rules.md | Required Practices | Use pre-layout floorplan review. |
| SWA-PDR-202 | Required Practices | pcb_design_rules.md | Required Practices | Run ERC/DRC with project-specific rule deck before each review gate. |
| SWA-PDR-203 | Required Practices | pcb_design_rules.md | Required Practices | Perform return-current path review for every high-speed or switching net class. |
| SWA-PDR-301 | Design Constraints | pcb_design_rules.md | Design Constraints | Copper balancing |
| SWA-PDR-302 | Design Constraints | pcb_design_rules.md | Design Constraints | Thermal |
| SWA-PDR-303 | Design Constraints | pcb_design_rules.md | Design Constraints | Creepage/clearance |
| SWA-PDR-304 | Design Constraints | pcb_design_rules.md | Design Constraints | Connector edge placement |
| SWA-PWM-001 | Engineering Rules | power_management.md | Engineering Rules | Never exceed battery chemistry limits in charge profile configuration. |
| SWA-PWM-002 | Engineering Rules | power_management.md | Engineering Rules | No release without validated low-voltage behavior and graceful degradation. |
| SWA-PWM-003 | Engineering Rules | power_management.md | Engineering Rules | All high-risk fault modes must map to protective hardware or firmware response. |
| SWA-PWM-101 | Performance Targets | power_management.md | Performance Targets | Sleep-mode current |
| SWA-PWM-102 | Performance Targets | power_management.md | Performance Targets | Brownout recovery |
| SWA-PWM-103 | Performance Targets | power_management.md | Performance Targets | Battery service interval |
| SWA-PWM-201 | Required Practices | power_management.md | Required Practices | Build a measured power budget for each firmware operating mode. |
| SWA-PWM-202 | Required Practices | power_management.md | Required Practices | Validate charging and discharge behavior across thermal extremes. |
| SWA-PWM-203 | Required Practices | power_management.md | Required Practices | Include brownout and recovery behavior tests in release gating. |
| SWA-PWM-301 | Design Constraints | power_management.md | Design Constraints | Sleep current |
| SWA-PWM-302 | Design Constraints | power_management.md | Design Constraints | Charge safety |
| SWA-PWM-303 | Design Constraints | power_management.md | Design Constraints | Thermal margin |
| SWA-GLS-001 | Engineering Rules | project_glossary.md | Engineering Rules | Use glossary terms in all formal engineering artifacts. |
| SWA-GLS-002 | Engineering Rules | project_glossary.md | Engineering Rules | Do not introduce conflicting synonyms in requirements or interfaces. |
| SWA-GLS-003 | Engineering Rules | project_glossary.md | Engineering Rules | Update glossary before adopting new platform-wide terminology. |
| SWA-GLS-101 | Performance Targets | project_glossary.md | Performance Targets | Terminology inconsistencies in reviews |
| SWA-GLS-102 | Performance Targets | project_glossary.md | Performance Targets | Glossary update turnaround |
| SWA-GLS-201 | Required Practices | project_glossary.md | Required Practices | Cross-check new standards documents against glossary terms. |
| SWA-GLS-202 | Required Practices | project_glossary.md | Required Practices | Include glossary references in onboarding and design review templates. |
| SWA-GLS-301 | Design Constraints | project_glossary.md | Design Constraints | Clarity |
| SWA-GLS-302 | Design Constraints | project_glossary.md | Design Constraints | Stability |
| SWA-GLS-303 | Design Constraints | project_glossary.md | Design Constraints | Traceability |
| SWA-RFL-001 | Engineering Rules | rf_lorawan_standards.md | Engineering Rules | No antenna or enclosure material changes without RF revalidation. |
| SWA-RFL-002 | Engineering Rules | rf_lorawan_standards.md | Engineering Rules | No region deployment without approved channel plan and duty-cycle policy. |
| SWA-RFL-003 | Engineering Rules | rf_lorawan_standards.md | Engineering Rules | No firmware release that changes MAC behavior without field A/B validation. |
| SWA-RFL-101 | Performance Targets | rf_lorawan_standards.md | Performance Targets | Uplink success in baseline deployment |
| SWA-RFL-102 | Performance Targets | rf_lorawan_standards.md | Performance Targets | Downlink command reliability |
| SWA-RFL-103 | Performance Targets | rf_lorawan_standards.md | Performance Targets | Regional compliance escapes |
| SWA-RFL-201 | Required Practices | rf_lorawan_standards.md | Required Practices | Maintain link budget analysis with margin assumptions. |
| SWA-RFL-202 | Required Practices | rf_lorawan_standards.md | Required Practices | Validate radiated behavior in representative enclosure states. |
| SWA-RFL-203 | Required Practices | rf_lorawan_standards.md | Required Practices | Track packet success metrics by region and environment profile. |
| SWA-RFL-301 | Design Constraints | rf_lorawan_standards.md | Design Constraints | Enclosure coupling |
| SWA-RFL-302 | Design Constraints | rf_lorawan_standards.md | Design Constraints | RF coexistence |
| SWA-RFL-303 | Design Constraints | rf_lorawan_standards.md | Design Constraints | Certification |
| SWA-SEC-001 | Engineering Rules | security_standards.md | Engineering Rules | No plaintext storage of production secrets. |
| SWA-SEC-002 | Engineering Rules | security_standards.md | Engineering Rules | No unsigned firmware execution path. |
| SWA-SEC-003 | Engineering Rules | security_standards.md | Engineering Rules | No debug interface exposure in production without approved controls. |
| SWA-SEC-004 | Engineering Rules | security_standards.md | Engineering Rules | No security exception without owner, expiry, and mitigation. |
| SWA-SEC-101 | Performance Targets | security_standards.md | Performance Targets | Critical vulnerability remediation |
| SWA-SEC-102 | Performance Targets | security_standards.md | Performance Targets | Unauthorized access attempts detected |
| SWA-SEC-103 | Performance Targets | security_standards.md | Performance Targets | Signed firmware enforcement |
| SWA-SEC-201 | Required Practices | security_standards.md | Required Practices | Threat modeling for all major features and interfaces. |
| SWA-SEC-202 | Required Practices | security_standards.md | Required Practices | Security test cases integrated into regression suites. |
| SWA-SEC-203 | Required Practices | security_standards.md | Required Practices | Credential provisioning with audited, least-privilege access. |
| SWA-SEC-301 | Design Constraints | security_standards.md | Design Constraints | Compute overhead |
| SWA-SEC-302 | Design Constraints | security_standards.md | Design Constraints | Provisioning throughput |
| SWA-SEC-303 | Design Constraints | security_standards.md | Design Constraints | Compatibility |
| SWA-SWO-001 | Engineering Rules | swafarm_overview.md | Engineering Rules | Never introduce single-source critical components without approved risk mitigation. |
| SWA-SWO-002 | Engineering Rules | swafarm_overview.md | Engineering Rules | No unversioned protocol or payload changes in production paths. |
| SWA-SWO-003 | Engineering Rules | swafarm_overview.md | Engineering Rules | No firmware release without rollback strategy and staged deployment controls. |
| SWA-SWO-004 | Engineering Rules | swafarm_overview.md | Engineering Rules | No hardware revision release without DFM review, test coverage review, and supply risk review. |
| SWA-SWO-005 | Engineering Rules | swafarm_overview.md | Engineering Rules | No cloud API change without compatibility validation for deployed firmware and mobile clients. |
| SWA-SWO-006 | Engineering Rules | swafarm_overview.md | Engineering Rules | No security exception without documented expiry and owner. |
| SWA-SWO-101 | Performance Targets | swafarm_overview.md | Performance Targets | Node Availability |
| SWA-SWO-102 | Performance Targets | swafarm_overview.md | Performance Targets | OTA Success Rate |
| SWA-SWO-103 | Performance Targets | swafarm_overview.md | Performance Targets | Fleet Telemetry Integrity |
| SWA-SWO-104 | Performance Targets | swafarm_overview.md | Performance Targets | Relay Command Reliability |
| SWA-SWO-105 | Performance Targets | swafarm_overview.md | Performance Targets | Manufacturing First Pass Yield |
| SWA-SWO-106 | Performance Targets | swafarm_overview.md | Performance Targets | Early Life Failure Rate |
| SWA-SWO-107 | Performance Targets | swafarm_overview.md | Performance Targets | Battery Service Life Objective |
| SWA-SWO-201 | Required Practices | swafarm_overview.md | Required Practices | Requirements Traceability |
| SWA-SWO-202 | Required Practices | swafarm_overview.md | Required Practices | Design Reviews |
| SWA-SWO-203 | Required Practices | swafarm_overview.md | Required Practices | Version Control Discipline |
| SWA-SWO-204 | Required Practices | swafarm_overview.md | Required Practices | Manufacturing Traceability |
| SWA-SWO-205 | Required Practices | swafarm_overview.md | Required Practices | Incident Response |
| SWA-SWO-206 | Required Practices | swafarm_overview.md | Required Practices | Field Feedback Loop |
| SWA-SWO-301 | Design Constraints | swafarm_overview.md | Design Constraints | Sensor Capacity |
| SWA-SWO-302 | Design Constraints | swafarm_overview.md | Design Constraints | Outputs |
| SWA-SWO-303 | Design Constraints | swafarm_overview.md | Design Constraints | Power Inputs |
| SWA-SWO-304 | Design Constraints | swafarm_overview.md | Design Constraints | Power Behavior |
| SWA-SWO-305 | Design Constraints | swafarm_overview.md | Design Constraints | Environmental |
| SWA-SWO-306 | Design Constraints | swafarm_overview.md | Design Constraints | Protocols |
| SWA-SWO-307 | Design Constraints | swafarm_overview.md | Design Constraints | Future Expansion |
| SWA-TST-001 | Engineering Rules | testing_standards.md | Engineering Rules | No release without passing all critical test gates. |
| SWA-TST-002 | Engineering Rules | testing_standards.md | Engineering Rules | No unresolved critical defects at release authorization. |
| SWA-TST-003 | Engineering Rules | testing_standards.md | Engineering Rules | Every defect fix requires regression proof in related domains. |
| SWA-TST-101 | Performance Targets | testing_standards.md | Performance Targets | Requirement coverage completeness |
| SWA-TST-102 | Performance Targets | testing_standards.md | Performance Targets | Regression pass stability |
| SWA-TST-103 | Performance Targets | testing_standards.md | Performance Targets | Defect escape rate |
| SWA-TST-201 | Required Practices | testing_standards.md | Required Practices | Maintain test plans with objective pass/fail criteria. |
| SWA-TST-202 | Required Practices | testing_standards.md | Required Practices | Run environmental and power-stress tests on production-representative hardware. |
| SWA-TST-203 | Required Practices | testing_standards.md | Required Practices | Capture test artifacts in version-controlled repositories. |
| SWA-TST-301 | Design Constraints | testing_standards.md | Design Constraints | Test duration |
| SWA-TST-302 | Design Constraints | testing_standards.md | Design Constraints | Fixture availability |
| SWA-TST-303 | Design Constraints | testing_standards.md | Design Constraints | Data integrity |

## Usage Notes
- Use this index during design reviews to confirm all new normative statements receive an SWA ID.
- Use this index in test planning to map validation artifacts to requirement IDs.
- Keep this file updated whenever IDs are added, removed, or renamed in source standards.
