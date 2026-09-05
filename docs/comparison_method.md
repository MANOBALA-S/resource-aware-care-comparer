# Comparison Methodology: Baseline vs Resource-Aware Care Option Comparer

> [!IMPORTANT]
> **Decision-Support Prototype — Clinician Sign-Off Required.**  
> **Synthetic Data Only — No Real Patient Data.**  
> All patient cases, facility service registries, clinical protocols, and operational records are purely synthetic and designed exclusively for software validation and decision-support simulation.

---

## 1. Objective and Core Philosophy

In low-resource and remote teleconsultation networks, textbook clinical protocols frequently recommend interventions (e.g., immediate specialist consults, advanced imaging, cold-chain parenterals) that are unavailable at peripheral primary health centers. When standard decision-support systems blindly prescribe unconstrained textbook guidelines, local health workers face operational deadlocks, unmonitored drop-offs, and clinical risks.

**Phase 7** introduces an empirical, reproducible comparative evaluation framework that runs identical synthetic patient cases through:
1. **The Textbook Baseline Method** (Phase 2): Direct unconstrained protocol lookup ignoring site resource realities, travel barriers, connectivity limits, language barriers, and follow-up accountability.
2. **The Resource-Aware System** (Phases 4–6): Deterministic 4-tier recommendation ladder evaluation (`preferred` &rarr; `resource_adapted_alternative` &rarr; `minimum_safe_fallback` &rarr; `escalate_only`), paired with persistent follow-up tracking (Phase 5) and multilingual safety enforcement (Phase 6).

---

## 2. Why the Comparison is Methodologically Fair

A comparative trial between clinical decision-support methods is only valid if external variables are strictly controlled. The evaluation architecture enforces the following invariants:

```
                  ┌───────────────────────────────┐
                  │     SYNTHETIC PATIENT CASE    │
                  │  (Exact same 40 cases, Seed 42)│
                  └──────────────┬────────────────┘
                                 │
                 Identical Case Snapshot Feed
                                 │
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
┌───────────────────────────────┐       ┌───────────────────────────────┐
│       TEXTBOOK BASELINE       │       │     RESOURCE-AWARE SYSTEM     │
│   • Same condition            │       │   • Same condition            │
│   • Same facility site        │       │   • Same facility site        │
│   • Same clinical urgency     │       │   • Same clinical urgency     │
│   • Same travel constraints   │       │   • Same travel constraints   │
│   • Same language profile     │       │   • Same language profile     │
│   • Site resources ignored    │       │   • Site resources evaluated  │
│   • Follow-up untracked       │       │   • SLA follow-up tracked     │
│   • Language ignored          │       │   • Language safety enforced  │
└───────────────────────────────┘       └───────────────────────────────┘
```

### Fairness Guarantees:
1. **Paired In-Subject Design:** Every synthetic case ($N = 40$) acts as its own control. The baseline and resource-aware systems evaluate the exact same clinical scenario.
2. **Input Immutability Guarantee:** The case entity is snapshot-verified before and after execution (`tests/comparer/test_same_input.py`). Neither system alters patient vitals, site IDs, or constraint parameters.
3. **Controlled Protocol Truth:** Both systems draw from the exact same protocol definition library (`data/protocols/protocols.json`). The baseline outputs the protocol's declared `textbook_recommendation` (matching the `preferred` ladder rung), while the resource-aware engine evaluates the protocol's 4-tier ladder against the site registry.
4. **No Machine Learning Confounders:** Both engines are 100% deterministic and rule-based. Results are fully inspectable, reproducible, and explainable.

---

## 3. The Five Core Comparative Metrics

The framework deterministically evaluates five quantitative metrics across all 40 cases:

### Metric 1: % Recommendations Feasible Given Site Resources
- **Formula:**
  $$\text{Feasibility Rate} = \frac{\sum \text{Feasible Recommendations}}{\text{Total Cases Evaluated}} \times 100$$
- **Baseline Behavior:** Baseline always prescribes the gold-standard textbook option without checking whether the facility has the required diagnostic machines, specialist physicians, or cold-chain medication stock.
- **Resource-Aware Behavior:** If the preferred rung cannot be fulfilled locally, the engine traverses down the ladder to identify a safe, adapted alternative or minimum-safe fallback. If all local tiers are blocked, it triggers immediate escalation rather than prescribing infeasible local care.
- **Observed Result:**
  - **Baseline:** **65.0%** (26/40 cases feasible; 14 cases blindly prescribed care that peripheral clinics could not deliver).
  - **Resource-Aware:** **100.0%** (40/40 cases feasible; all selected options matched verified local facility capabilities).

### Metric 2: % High-Priority Follow-ups with Owner, Due Date & Escalation Path
- **Scope:** Cases with `HIGH` or `CRITICAL` clinical urgency ($N = 16$).
- **Requirements:**
  1. A named human owner/role (e.g., `"Local Health Worker"`).
  2. A deterministic SLA deadline timestamp (`due_at`).
  3. A defined multi-tier escalation hierarchy (`escalation_path`).
- **Baseline Behavior:** Follow-up is represented merely as an unassigned, untracked time interval (e.g., `"6h"`). No owner, due date, or escalation ladder exists (**0.0%**).
- **Resource-Aware Behavior:** Phase 5 follow-up tracker registers a persistent SQLite record with an assigned owner, calculated ISO timestamp, and escalation path (**100.0%**).

### Metric 3: Number of Recommendations Changed Because of Constraints
- **Definition:** The number of cases where the resource-aware system diverted from the textbook preferred tier to an adapted alternative, minimum-safe fallback, or emergency escalation due to verified local resource deficits.
- **Observed Result:** **14 / 40 cases (35.0%)**.
  - 10 cases adapted to `resource_adapted_alternative`.
  - 4 cases adapted to `minimum_safe_fallback`.
  - 26 cases retained `preferred` because facility resources were confirmed available (e.g. at Tertiary Medical Center `SITE-001` or Secondary Hospital `SITE-005`).

### Metric 4: Number of Language Mismatches Detected
- **Definition:** Cases where patient mother tongue or preferred language is not directly spoken by the treating remote clinician.
- **Safety Rule:** Never proceed with silent miscommunication. The system must verify certified interpreter availability (`REQUIRES_INTERPRETER`) or mandate language escalation (`LANGUAGE_ESCALATION_REQUIRED`).
- **Observed Result:** **29 / 40 cases (72.5%)** detected and safely resolved through interpreter coverage.

### Metric 5: Number of Immediate Escalations Triggered
- **Definition:** Cases where the resource-aware engine triggered immediate human clinical escalation (`decision == "ESCALATE_IMMEDIATELY"`) due to total local care pathway exhaustion or severe communication barrier without interpreter coverage.
- **Observed Result:** **0 / 40 cases (0.0%)** (all 40 synthetic cohort cases had at least one safe alternative tier available or accessible interpreter coverage).

---

## 4. Facility Tier Breakdown

The comparative metrics demonstrate how real-world healthcare disparities impact care delivery:

| Site ID | Clinic Tier | Total Cases | Baseline Feasible | Resource-Aware Feasible | Changed Recommendations |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **SITE-001** | Regional Tertiary Medical Center | 7 | 7 (100%) | 7 (100%) | 0 (0%) |
| **SITE-002** | Remote Primary Health Center | 7 | 1 (14%) | 7 (100%) | 6 (86%) |
| **SITE-003** | Rural Community Health Clinic | 7 | 5 (71%) | 7 (100%) | 2 (29%) |
| **SITE-004** | Sub-District Taluk Hospital | 7 | 6 (86%) | 7 (100%) | 1 (14%) |
| **SITE-005** | Urban Secondary Hospital | 6 | 6 (100%) | 6 (100%) | 0 (0%) |
| **SITE-006** | Tribal Mobile Health Clinic | 6 | 1 (17%) | 6 (100%) | 5 (83%) |
| **TOTAL** | **All Facilities** | **40** | **26 (65%)** | **40 (100%)** | **14 (35%)** |

> [!NOTE]
> At well-resourced tertiary and secondary hospitals (`SITE-001` and `SITE-005`), both systems agree 100% of the time. However, at peripheral facilities (`SITE-002` and `SITE-006`), textbook baseline fails up to 86% of the time by recommending unavailable specialists, doppler imaging, or cold-chain therapies, whereas the resource-aware comparer safely adapts care.

---

## 5. Summary and Next Steps

Phase 7 proves the central hypothesis: **unconstrained clinical protocols produce frequent operational failures at peripheral facilities, whereas deterministic resource-aware adaptation guarantees 100% site-feasible care options, 100% follow-up accountability for high-priority patients, and safe multilingual communication.**
