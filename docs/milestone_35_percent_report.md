# Milestone Progress Report: First 35% Review
**Project Title**: Resource-Aware Care Option Comparer for Teleconsultation Services  
**Project Repository**: [https://github.com/MANOBALA-S/resource-aware-care-comparer](https://github.com/MANOBALA-S/resource-aware-care-comparer)  
**Milestone Target**: 35% Progress Gate (Foundational Architecture, Protocol Engine, Operational Data, & Constraint Filtering)  
**Date**: September 2026  
**Status**: Completed & Verified  

---

## Executive Summary

Teleconsultation services in resource-constrained environments frequently face a major operational failure mode: **clinical recommendations issued by remote specialists assume standard-of-care resources that are physically unavailable at the patient's local primary health facility**. This disconnect leads to unfulfilled prescriptions, delayed referrals, dangerous care omissions, and loss of patient trust.

The **Resource-Aware Care Option Comparer** addresses this gap by creating an auditable, deterministic clinical decision-support engine. The first **35% milestone** focuses on establishing the core system foundation: codifying evidence-based clinical protocols, modeling physical health post resources, generating a diverse synthetic patient cohort, and implementing the deterministic constraint evaluation engine that matches care options to real-world resource capacities.

---

## 1. What Has Been Completed So Far

During this initial 35% phase, the team has delivered the complete core logic required to ingest a clinical case, cross-reference it against verified protocols, inspect local health center capabilities, and determine whether a care option can be safely executed:

### A. Architectural & Data Foundation (Phase 1)
- **Deterministic Domain Architecture**: Designed the end-to-end data pipeline separating idealized clinical guidelines from physical resource constraints.
- **Pydantic v2 Type System**: Implemented data contracts in `src/models/` defining clinical cases, operational inventories, protocol specifications, and evaluation outputs.
- **Central Configuration Architecture**: Built a centralized configuration manager (`config/default_config.yaml`) defining operational thresholds, fallback policies, and service limits.
- **API Backbone**: Built a FastAPI-based server with health monitoring (`GET /health`) and lifecycle management.

### B. Codified Clinical Protocol Library (Phase 2)
- Codified standard-of-care guidelines into structured JSON protocols across **5 high-burden conditions**:
  1. **Type 2 Diabetes Mellitus (T2D)**: Management of glycemic control, lifestyle adaptation, and specialist referral triggers.
  2. **Essential Hypertension (HTN)**: Staged pharmacological management and cardiovascular risk screening.
  3. **Pediatric Asthma**: Bronchodilator therapy, inhaler spacer availability, and acute exacerbation protocols.
  4. **Antenatal Care (ANC)**: High-risk pregnancy screening, ultrasound access, iron-folic acid supplementation, and delivery planning.
  5. **Chronic Heart Failure (CHF)**: Fluid management, diuretic optimization, electrolyte monitoring, and specialist co-management.
- Each protocol defines **tiered options** (*Preferred Option*, *Acceptable Alternative*, *Minimum Safe Option*) and lists mandatory requirements across 5 resource dimensions:
  - Required medical staff / specialist roles
  - Mandatory point-of-care or laboratory diagnostics
  - Essential pharmaceuticals and formulation types
  - Cold-chain refrigeration dependencies
  - Clinical transport / emergency transit availability

### C. Operational Service Registry & Synthetic Patient Cohort (Phase 3)
- **Service Registry (`data/services/service_registry.json`)**: Codified real-world capacities for 6 distinct healthcare delivery facilities:
  - Urban General Hospital (Comprehensive capabilities, round-the-clock labs, cold-chain, specialists)
  - District Hospital (Intermediate specialty access, standard labs)
  - Community Health Centre (CHC) (General medical officer, basic labs)
  - Rural Primary Health Centre (PHC) (Constrained staffing, intermittent cold-chain, basic medications)
  - Rural Sub-Centre (Health & Wellness Centre) (Nurse/community worker led, point-of-care tests only)
  - Mobile Medical Unit (MMU) (Highly mobile, transit-constrained, limited formulary)
- **Synthetic Patient Cohort (`data/cases/synthetic_cases.json`)**: Built a fully stratified dataset of **40 synthetic patient profiles**:
  - Geographic distribution: 20 Rural (50%) and 20 Urban (50%) cases
  - Linguistic distribution: English (11 cases) and Tamil (29 cases)
  - Urgency levels: Routine (16), Moderate (12), Urgent (8), Emergency (4)
  - All 40 cases are strictly synthetic constructs containing zero protected health information (PHI).

### D. Resource Constraint Engine (Phase 4)
- Developed the deterministic filtering pipeline (`src/constraint_engine/resource_filter.py`) that tests every protocol tier against the target facility's inventory.
- Implemented **Human-Readable Reason Trails**: When an option is disqualified, the engine logs the exact physical deficit (e.g., *"Disqualified: Facility lacks cold-chain refrigeration for Insulin glargine; HbA1c analyzer out of service"*).
- Implemented **Safety Fallback (`ESCALATE_IMMEDIATELY`)**: When all local protocol tiers are rendered infeasible by severe stockouts or staffing absences, the system immediately flags the case for emergency transfer rather than recommending substandard or dangerous care.

---

## 2. Key Features, Modules, and Components Completed

| Component / Module | Type | File Location | Key Responsibility |
|---|---|---|---|
| **Data Models** | Software / Schema | `src/models/` | Type-safe Pydantic contracts for cases, resources, options, and reason trails. |
| **Configuration Engine** | Software / Config | `src/config.py`, `config/default_config.yaml` | System-wide thresholds, facility capacities, and operational rules. |
| **Protocol Engine** | Software / Clinical | `src/protocol_engine/` | Loads, parses, and resolves clinical guideline hierarchies for active cases. |
| **Clinical Protocols** | Data / Knowledge Base | `data/protocols/*.json` | Codified rules and tiered alternatives for T2D, HTN, Asthma, ANC, and CHF. |
| **Service Registry** | Operational Data | `data/services/service_registry.json` | Real-time simulation of medical staff, diagnostic equipment, and drug inventories. |
| **Synthetic Cases** | Dataset | `data/cases/synthetic_cases.json` | 40 clinically diverse synthetic test cases across rural/urban domains. |
| **Resource Constraint Filter** | Core Engine | `src/constraint_engine/resource_filter.py` | Deterministic verification of clinical requirements against physical resources. |
| **Audit Reason Trail** | Core Feature | Integrated in Constraint Engine | Generates step-by-step transparency into why alternatives were chosen or rejected. |
| **Unit Test Suite** | Quality Assurance | `tests/test_protocol_engine.py`, `tests/test_constraint_engine.py`, etc. | Automated test coverage verifying data integrity and constraint resolution. |

---

## 3. What Is Currently Working

The following capabilities are operational and verified through automated test suites:

1. **Ingestion & Validation**:
   - Ingesting synthetic patient case files and parsing clinical parameters, urgency, and facility IDs with strict validation.
2. **Clinical Protocol Resolution**:
   - Matching patient symptoms and conditions to the appropriate clinical protocol guidelines.
   - Extracting tiered options (Preferred vs. Alternative vs. Minimum Safe Option).
3. **Resource Constraint Checking**:
   - Querying the local facility's operational profile for diagnostic availability, medication stock, staffing, and cold-chain status.
   - Determining exact feasibility of each tiered option.
4. **Transparent Reason Trail Generation**:
   - Formatting clear clinical explanations of why the preferred option was selected or why an alternative was substituted due to local shortages.
5. **Deterministic Escalation Triggering**:
   - Detecting when a case cannot be safely treated locally (e.g., severe hypertension with absent parenteral anti-hypertensives and no physician on duty) and triggering an immediate emergency escalation output.
6. **Core API Health Endpoints**:
   - FastAPI server responding with system status, versioning, and operational health metrics.

---

## 4. Pending Work & Next Steps (Remaining 65% Roadmap)

To bring the project from this 35% foundational stage to full completion, the remaining 65% of the development plan is structured into two sequential execution blocks:

```
[Completed: 35%]                      [Pending Block 1: 35% -> 70%]                       [Pending Block 2: 70% -> 100%]
Foundation & Core Engine   ──►   Workflows, Multilingual & Interfaces    ──►    Evaluation, Safety & Integration
• Pydantic Data Models           • Follow-up Tracking & Escalation              • Edge-case & Bias Evaluation
• 5 Codified Protocols           • Multilingual Layer (English/Tamil)           • Simulated Clinician Review
• 40 Synthetic Cases             • Baseline vs Resource-Aware Comparer          • Ethics & Deployment Gate
• Constraint Engine              • Clinician Decision & Queue UI                • Interactive Demonstration Hub
```

### Next Steps (Immediate Priorities - Milestone 35% &rarr; 70%):
1. **Dynamic Follow-Up & Escalation Module (Phase 5)**:
   - Implement scheduled follow-up tracking with urgency-based intervals.
   - Build overdue detection and supervisor escalation triggers for missed reviews.
2. **Multilingual Localization Layer (Phase 6)**:
   - Integrate Tamil (`தமிழ்`) and English clinical message resolution.
   - Implement language barrier detection and automated medical interpreter assignment.
3. **Comparative Baseline Engine (Phase 7)**:
   - Implement side-by-side gap analysis comparing idealized standard-of-care recommendations against resource-adapted recommendations.
   - Compute quantifiable divergence metrics (feasibility rate, resource cost delta, delay factors).
4. **Interactive Web User Interfaces (Phases 8–10)**:
   - Build the Clinician Decision Support screen with live reason trail inspection.
   - Build the Follow-up Breach Management Queue screen.
   - Build the Baseline vs. Resource-Aware Care Option Comparer dashboard.

### Subsequent Priorities (Milestone 70% &rarr; 100%):
5. **Safety, Edge-Cases, and Bias Audits (Phases 11–12)**:
   - Test adversarial scenarios (simulated network blackouts, simultaneous resource collapses).
   - Perform demographic and geographic disparity analysis between rural and urban synthetic cohorts.
6. **Simulated Clinician Review & Governance (Phases 13–14)**:
   - Run multi-persona simulated validation across 5 distinct reviewer perspectives.
   - Document the clinical AI ethics note and multi-stage deployment checklist.
7. **Final Presentation Package (Phase 15)**:
   - Package the automated CLI demo script and launch the unified demonstration hub.

---

## 5. Milestone Verification Metrics

- **Unit Tests Passed for Foundation**: 100% passing rate across protocol, data, and constraint test modules.
- **Protocol Coverage**: 5 major non-communicable and primary care conditions codified with complete tiered alternatives.
- **Facility Diversity**: 6 distinct healthcare delivery profiles modeled (from tertiary urban hospital to rural sub-centre).
- **Dataset Size**: Exactly 40 diverse synthetic cases verified with zero real patient data.
- **Determinism**: 100% rule-based predictability with zero black-box stochastic hallucination.
