# Textbook Baseline Engine

> [!CAUTION]
> **GOVERNANCE & SYNTHETIC DATA NOTICE**
> - **Decision-support prototype — clinician sign-off required.**
> - **Synthetic data only — no real patient data.**

---

## 1. Baseline Purpose

The **Textbook Baseline Engine** (`TextbookBaselineEngine`) acts as the unconstrained clinical benchmark comparator in the Resource-Aware Care Option Comparer system.

In real-world teleconsultations, clinicians often consult national or international disease treatment guidelines that reflect the **gold standard of care**. These standard-of-care guidelines presuppose modern clinical infrastructure:
- Continuous tertiary specialist coverage
- Round-the-clock advanced imaging (CT, MRI, Doppler ultrasound)
- Unbroken pharmaceutical cold chains
- Rapid emergency transport systems
- Fluid multilingual interpretation services

The Baseline Engine replicates this textbook paradigm: it receives a patient condition and returns the official textbook recommendation directly from the approved protocol catalog.

---

## 2. Baseline Workflow

```
[Synthetic Patient Case]
         │
         ▼
[Textbook Baseline Engine]
         │
         ├── Step 1: Extract condition ('condition_alpha', 'condition_beta', etc.)
         │
         ├── Step 2: Query Protocol Engine for matching protocol
         │
         ├── Step 3: Extract gold-standard textbook_recommendation
         │
         └── Step 4: Emit unconstrained baseline result
                     (resource_checked = false, follow_up_checked = false)
```

---

## 3. What the Baseline Checks

- **Case Condition:** Identifies the primary condition specified in the synthetic patient case.
- **Protocol Catalog:** Verifies that an approved protocol definition exists for the condition.
- **Textbook Recommendation:** Retrieves the official standard-of-care guidance.
- **Urgency & Required Resources:** Passes through the theoretical resources specified by the protocol.

---

## 4. What the Baseline Deliberately Ignores

The Baseline Engine is strictly forbidden from inspecting or filtering by ground-truth logistical realities:

| Ground-Truth Resource | Baseline Behavior |
| :--- | :--- |
| **Site Diagnostics & Imaging** | **IGNORED.** Recommends MRI/ultrasound even if the patient's facility has no imaging equipment. |
| **Medication Stockouts** | **IGNORED.** Recommends second-line drugs even if the dispensary shelf is bare. |
| **Cold-Chain Refrigeration** | **IGNORED.** Prescribes refrigerated biologics even in areas with zero domestic refrigeration. |
| **Transportation Road Closures** | **IGNORED.** Assumes immediate referral transit even if roads are impassable. |
| **Specialist Availability** | **IGNORED.** Recommends immediate specialist review even if wait times are 6 weeks. |
| **Language & Literacy** | **IGNORED.** Assumes English comprehension by default. |
| **Follow-Up Ownership** | **IGNORED.** Does not assign an accountable owner or monitor milestones. |
| **Escalation Feasibility** | **IGNORED.** Does not configure operational escalation tiers. |

---

## 5. Why the Baseline is Essential for Evaluation

Without an explicit textbook baseline, evaluating a resource-aware system is impossible. The baseline serves as:
1. **The Ground Anchor:** Demonstrating what an unconstrained clinician would prescribe according to standard guidelines.
2. **The Contrast Surface:** Highlighting the exact "delta" or gap between ideal clinical advice and realistic field execution.
3. **The Counterfactual Benchmark:** In Phase 3 and Phase 4, the Resource-Aware Engine will contrast against this baseline to prove why and where resource-adapted modifications prevent treatment abandonment.

---

## 6. Contractual Output Specification

```json
{
  "method": "baseline",
  "case_id": "SYNTH-CASE-001",
  "status": "success",
  "protocol_id": "PROTO-001",
  "condition": "condition_alpha",
  "protocol_title": "Condition Alpha: Acute Progressive Soft-Tissue & Peripheral Infection Protocol",
  "urgency": "HIGH",
  "recommendation": "Immediate parenteral broad-spectrum antimicrobial administration...",
  "textbook_required_resources": ["same_day_imaging", "specialist_48h", "medication_stock", "cold_chain", "transport", "local_clinician"],
  "follow_up_interval": "6h",
  "resource_checked": false,
  "follow_up_checked": false,
  "governance_notice": "Decision-support prototype — clinician sign-off required.",
  "synthetic_data_notice": "Synthetic data only — no real patient data."
}
```
