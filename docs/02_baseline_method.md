# 02. Baseline Method: The Unconstrained Textbook Comparator

> [!CAUTION]
> **SYNTHETIC DATA NOTICE & CLINICAL DISCLAIMER**
> **All patient cases, service registries, protocols, and operational records in this prototype are synthetic. No real patient data is used.**
> This document describes an illustrative software benchmark methodology. It does **not** provide validated clinical guidance.
> **Decision-support prototype — clinician sign-off required.**

---

## 1. Baseline Purpose

In medical informatics and teleconsultation systems, evaluating the added value of "resource awareness" requires a rigorous control method. The **Textbook Baseline Method** serves as this standardized, unconstrained control anchor.

In conventional teleconsultation models, remote physicians consult national protocols, institutional guidelines, or clinical compendia that describe best-practice treatment assuming ideal conditions. These recommendations are medically sound in theory, but they are geographically and operationally agnostic.

The baseline method encapsulates this standard practice:
- It processes a patient presentation (represented by a synthetic condition).
- It retrieves the corresponding textbook standard of care.
- It produces a clinical recommendation without modifying it for local constraints.

By freezing this standard-of-care logic into an explicit software component, the system creates a stable foundation against which resource-aware, constraint-filtered recommendations can be systematically compared.

---

## 2. Baseline Workflow

The baseline method follows a direct lookup workflow:

```
┌────────────────────────────────────────────────────────┐
│               SYNTHETIC PATIENT CASE                   │
│   (e.g., condition: "condition_alpha", location_id)    │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│               CONDITION EXTRACTION LAYER               │
│   Extracts primary condition identifier from payload   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│               PROTOCOL LIBRARY LOOKUP                  │
│       Matches condition against protocols.json         │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│             TEXTBOOK RECOMMENDATION EMISSION           │
│   - Extracts textbook_recommendation                   │
│   - Retains theoretical required_resources             │
│   - Explicitly bypasses resource availability checks   │
│   - Explicitly bypasses follow-up assignment checks    │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│              UNCONSTRAINED BASELINE OUTPUT             │
│   { method: "baseline", resource_checked: false, ... } │
└────────────────────────────────────────────────────────┘
```

### Operational Steps:
1. **Case Ingestion:** The baseline engine receives a case representation containing a clinical condition identifier.
2. **Catalog Matching:** The engine indexes the approved synthetic protocol library (`data/protocols/protocols.json`) to locate the relevant protocol definition.
3. **Guideline Extraction:** The primary `textbook_recommendation` field is extracted directly from the protocol.
4. **Constraint Bypass:** The engine deliberately does **not** evaluate whether the patient's local site actually possesses the required drugs, imaging suites, or transport links.
5. **Contract Emission:** The result is formatted with explicit audit flags confirming that resource and follow-up checks were bypassed (`resource_checked: false`, `follow_up_checked: false`).

---

## 3. What the Baseline Checks

The baseline engine limits its scope to pure clinical matching:

1. **Condition Validity:** Verifies that the case specifies a recognized condition code (e.g., `condition_alpha`, `condition_beta`).
2. **Protocol Availability:** Confirms that an approved, versioned clinical protocol exists for that condition.
3. **Textbook Standard of Care:** Retrieves the exact guideline-defined intervention.
4. **Declared Theoretical Requirements:** Reports the list of resources theoretically necessary for the textbook recommendation (e.g., `same_day_imaging`, `cold_chain`), without asserting their local existence.

---

## 4. What the Baseline Deliberately Ignores

To serve as a faithful reproduction of unconstrained clinical practice, the baseline engine deliberately ignores all operational, logistical, and infrastructural variables:

| Operational Dimension | Ground-Truth Reality in Peripheral Settings | Baseline Behavior |
| :--- | :--- | :--- |
| **Medication Stock** | Peripheral dispensaries frequently experience stockouts of first-line second-generation or specialized antibiotics. | **Ignored.** Prescribes the textbook drug regardless of local shelf stock. |
| **Cold-Chain Continuity** | Unreliable power grids or broken refrigerators prevent storage of refrigerated insulins or biologics. | **Ignored.** Recommends cold-chain items without checking cold-chain telemetry. |
| **Diagnostic Equipment** | Ultrasound, CT scanners, and automated biochemistry analyzers are absent or offline. | **Ignored.** Mandates same-day imaging and complex panels. |
| **Specialist Staffing** | Visiting specialists arrive once monthly or are located hours away. | **Ignored.** Recommends immediate 48-hour specialist evaluation. |
| **Patient Transportation** | Monsoon road flooding, lack of private vehicles, or high transit fares prevent hospital transit. | **Ignored.** Directs patient to attend distant regional referral centers. |
| **Language & Literacy** | Patients may speak only vernacular languages (e.g., Tamil) and have limited literacy. | **Ignored.** Produces uniform administrative guidance without translation adaptation. |
| **Follow-up Ownership** | Follow-up instructions lack designated human owners (Local Health Worker vs. Care Coordinator). | **Ignored.** Issues instructions into consultation notes without an assigned task owner. |
| **Escalation Feasibility** | No escalation pathways exist if a patient misses a scheduled milestone. | **Ignored.** Assumes spontaneous patient return if symptoms worsen. |

---

## 5. Why the Baseline is Needed for Evaluation

The baseline is not an arbitrary dummy implementation; it is the **scientific anchor** for comparative evaluation:

1. **Quantifying the Feasibility Delta:**
   By comparing the baseline against the resource-aware recommendation, researchers and clinicians can measure the exact proportion of textbook recommendations that are physically unimplementable at peripheral facilities.
2. **Preventing Counterfactual Drift:**
   Without a textbook baseline, a resource-aware engine might quietly lower standards of care without documenting the clinical trade-offs. The baseline guarantees that the gold standard is always preserved as an explicit reference point.
3. **Evaluating Decision-Support Safety:**
   In clinical governance reviews, the remote clinician can inspect both the ideal recommendation and the locally feasible alternative side-by-side, ensuring full transparency in clinical sign-off.

---

## 6. Limitations of the Baseline Method

1. **Synthetic Clinical Scope:** The baseline uses synthetic condition identifiers and generic protocol templates. It does not replace clinical judgment or certified medical guidelines.
2. **Static Lookup:** The baseline does not perform dynamic multi-morbidity reasoning or pharmacokinetic modeling; it performs a direct, deterministic protocol lookup.
3. **Presumption of Frictionless Care:** The baseline represents the upper theoretical bound of care delivery—a scenario where resources and compliance are friction-free.
