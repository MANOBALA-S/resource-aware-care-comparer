# Resource Constraint Engine Specification

> [!CAUTION]
> **GOVERNANCE & SYNTHETIC DATA NOTICE**
> - **Decision-support prototype — clinician sign-off required.**
> - **Synthetic data only — no real patient data.**
> - All cases, facility registries, protocols, and operational records described herein are synthetic.

---

## 1. Engine Architecture

The **Resource Constraint Engine** (`src/constraint_engine/`) is the central decision-support module of the Resource-Aware Care Option Comparer. While the textbook baseline provides an unconstrained standard-of-care recommendation, the constraint engine evaluates the real-world operational feasibility of each care pathway at the patient's specific location.

```
┌───────────────────────────────┐     ┌────────────────────────────────┐
│      PATIENT CASE PROFILE     │     │   CLINICAL PROTOCOL LADDER     │
│ (Condition, Site, Travel, Lang)│    │ (Preferred, Adapted, Fallback) │
└───────────────┬───────────────┘     └───────────────┬────────────────┘
                │                                     │
                ▼                                     ▼
        ┌─────────────────────────────────────────────────────┐
        │              RESOURCE CONSTRAINT ENGINE             │
        │                                                     │
        │   1. Language Safety Verification                   │
        │   2. Registry Conflict Resolution (Safety-First)    │
        │   3. Deterministic Option Feasibility Testing       │
        │   4. Highest-Tier Ladder Selection                  │
        │   5. Reason Trail Assembly & Audit Logging          │
        └──────────────────────────┬──────────────────────────┘
                                   │
                                   ▼
        ┌─────────────────────────────────────────────────────┐
        │            CONSTRAINT ENGINE RESULT                 │
        │  - Selected Option & Ladder Tier                    │
        │  - Inspectable Reason Trail                         │
        │  - Blocked Options Breakdown                        │
        │  - Escalation & Fallback Owner Requirement          │
        └─────────────────────────────────────────────────────┘
```

The engine employs purely **deterministic, inspectable rules**—no machine learning or black-box heuristics are used.

---

## 2. Deterministic Decision Flow

The engine evaluates recommendations strictly in order of clinical preference:

```
[Start Evaluation]
       │
       ▼
[Check Language Safety]
       │
       ▼
[Evaluate 'Preferred' Option]
   ├── Feasible? ──► [SELECT 'preferred'] ─────────────────────────┐
   └── Blocked? (Record blocking reasons in trail)                  │
             │                                                     │
             ▼                                                     │
      [Evaluate 'Resource-Adapted Alternative']                    │
         ├── Feasible? ──► [SELECT 'resource_adapted_alternative'] ┼──► [Build Reason Trail]
         └── Blocked? (Record blocking reasons in trail)           │            │
                   │                                               │            ▼
                   ▼                                               │   [Emit Final Result]
            [Evaluate 'Minimum-Safe Fallback']                     │
               ├── Feasible? ──► [SELECT 'minimum_safe_fallback'] ─┘
               └── Blocked? (Record blocking reasons in trail)
                         │
                         ▼
             [ALL LOCAL TIERS BLOCKED]
                         │
                         ▼
             [Trigger: ESCALATE_IMMEDIATELY]
             (feasible = false, escalation_required = true,
              fallback_owner_required = true)
```

### Safety Invariants:
1. **Never Silently Downgrade:** If the preferred option cannot be delivered, the engine explicitly logs every blocking resource deficit before evaluating the resource-adapted alternative.
2. **Never Return Null or Inappropriate Fallbacks:** If the minimum safe fallback is also blocked, the engine refuses to invent ad-hoc alternatives or emit empty results. It transitions to immediate operational escalation (`ESCALATE_IMMEDIATELY`).

---

## 3. Feasibility Rules

Every option declares a list of `required_resources` and clinical instructions that are tested against the ground-truth environment:

| Resource Dimension | Evaluation Rule | Failure / Blocking Rationale |
| :--- | :--- | :--- |
| **Diagnostic Imaging** | Checked against `site.equipment`. Requires confirmed hardware (e.g. Doppler ultrasound, CT, digital X-ray). | `"Same-day diagnostic imaging is unavailable at the current site."` |
| **Cold Chain** | Checked against `site.cold_chain_available`. | `"Cold-chain storage is unavailable or currently non-functional at this site."` |
| **Medications** | Checked against `site.medication_stock`. Verified for essential categories (antibiotics, hypoglycemics, antihypertensives, inhalers). | `"Medication stockout: required pharmaceuticals are unavailable in the local dispensary."` |
| **Specialists (48h)** | Checked against `site.specialists` and `site.specialist_availability_hours`. | `"Specialist unavailable within the required 48-hour clinical window."` |
| **Transport** | Checked against `site.transport_available` and `travel_constraints.transport_available`. | `"Transport unavailable: Neither facility ambulance nor viable patient conveyance is available."` |
| **Connectivity** | Checked against `travel_constraints.connectivity_quality` and `teleconsult_bandwidth`. High-loss/2G links (128 kbps) cannot support virtual teleconsultation. | `"Remote review or teleconsultation is infeasible due to insufficient connectivity (POOR quality or high loss)."` |
| **Travel Friction** | Transfer options are checked against transit duration and vehicle availability. | `"Transfer required, but transport to next-tier facility is unavailable."` |

---

## 4. The Recommendation Substitution Ladder

Each synthetic clinical protocol in `data/protocols/protocols.json` provides a structured 4-tier ladder:

1. **`preferred` (Tier 1):** The unconstrained gold standard (e.g., IV cephalosporin + Doppler imaging + surgical specialist review).
2. **`resource_adapted_alternative` (Tier 2):** A safe adaptation that substitutes unavailable equipment or cold-chain items with verified local alternatives (e.g., oral fluoroquinolones + digital wound margin photography).
3. **`minimum_safe_fallback` (Tier 3):** The lowest acceptable clinical standard of care that prevents immediate decompensation or death in austere settings (e.g., basic oral broad-spectrum antibiotics + bedside vital sign monitoring).
4. **`escalate_only` (Tier 4):** Mandatory physical evacuation or senior supervisor mobilization when local care is impossible.

---

## 5. Inspectable Reason Trail

Every evaluation generates an audit log detailing why each ladder level succeeded or failed. This enables full clinical transparency before clinician sign-off:

### Example Reason Trail Output:
```
1. Initiating evaluation for Case 'SYNTH-CASE-002' (Condition: 'condition_alpha', Site: 'SITE-002').
2. Language Safety: Patient language 'ta' is directly supported without translation barriers.
3. Evaluated 'Preferred': BLOCKED. Constraints not met: same_day_imaging: Same-day diagnostic imaging is unavailable at the current site; cold_chain: Cold-chain storage is unavailable or currently non-functional at this site.
4. Evaluated 'Resource Adapted Alternative': FEASIBLE. All required resources and constraints are satisfied.
5. FINAL DECISION: Selected 'Resource Adapted Alternative' as the highest feasible care pathway for this patient's clinical and site constraints.
```

---

## 6. Safety Behaviors

### A. Registry Conflict Resolution (Safety-First Principle)
Real-world facility registries occasionally contain contradictory or out-of-date records (e.g. an equipment inventory declaring `specialist_available: true` alongside an operational note declaring `specialist_unavailable: true`).

**Engine Safety Policy:**
- When conflicting records are detected, the engine **refuses to guess** and **refuses to average** values.
- It applies the **safer clinical assumption**: the resource is treated as **unavailable**.
- The conflict is logged explicitly in the reason trail:
  > *"Conflicting specialist availability records detected. Safer assumption applied: specialist treated as unavailable."*

### B. Language Safety & Escalation
Effective teleconsultation is impossible without clear communication.
- Patient language is evaluated against remote clinician languages, local site staff languages, and available interpreter rosters.
- If the patient speaks a language unsupported by both clinician and translators:
  1. The engine sets `language_status = "LANGUAGE_ESCALATION_REQUIRED"`.
  2. The engine forces `escalation_required = true`.
  3. The reason trail records the communication barrier.
  4. The engine refuses to authorize silent unmonitored discharge.

### C. Immediate Escalation on Total Rung Exhaustion
When a patient presents at an austere facility where `preferred`, `adapted`, and `fallback` rungs are all blocked by severe resource stockouts:
1. `decision = "ESCALATE_IMMEDIATELY"`
2. `feasible = false`
3. `escalation_required = true`
4. `fallback_owner_required = true` (an accountable coordinator must be assigned to manage evacuation)
5. `selected_option` defaults to the protocol's emergency transfer directive (`escalate_only`).
