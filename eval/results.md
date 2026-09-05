# Empirical Evaluation Results: Population Cohorts & Disparity Analysis

> [!NOTE]
> **Synthetic Data Notice**: Synthetic data only — no real patient data.  
> **Clinical Governance**: Decision-support prototype — clinician sign-off required.  
> **Evaluation Scope**: Phase 12 evaluation module analyzing paired Baseline vs. Resource-Aware engine behaviors across 40 deterministic synthetic cases.

---

## 1. Baseline (Textbook Protocol Lookup)

The Textbook Baseline operates under unconstrained assumptions, selecting the clinical gold-standard recommendation regardless of local facility tier, medication stock, equipment, cold-chain refrigeration, transport feasibility, or clinician language matching.

- **Rural Baseline Feasibility**: 55.0% (11/20 cases)
- **Urban Baseline Feasibility**: 75.0% (15/20 cases)
- **English Baseline Feasibility**: 72.7% (8/11 cases)
- **Tamil Baseline Feasibility**: 62.1% (18/29 cases)
- **Overall Baseline Feasibility**: 65.0% (26/40 cases)
- **Baseline High-Priority Follow-Up Accountability**: **0.0%** across all cohorts (disposition noted only as generic untracked interval; zero assigned named owners, zero computed SLA due dates, zero escalation hierarchies).
- **Baseline Language Safety Verification**: **0.0%** across all cohorts (language compatibility unexamined; zero interpreter checks).

---

## 2. Target (Operational Standard)

The operational targets define the required safety and accountability standards for real-world teleconsultation deployment:

| Dimension | Target Standard | Rationale |
| :--- | :--- | :--- |
| **Recommendation Feasibility** | **100.0%** | When local constraints block the preferred tier, safely adapt down the clinical ladder or trigger structured escalation. |
| **Follow-Up Accountability** | **100.0%** | Every HIGH and CRITICAL case must have a named owner, deterministic due date, and structured escalation path. |
| **Language Safety Verification** | **100.0%** | Patient-clinician language compatibility must be explicitly verified for every consultation; no silent translation failure. |
| **Immediate Clinical Escalation** | Context-Dependent | Appropriate identification of unresolvable red-flag barriers without unneeded hospital transfers. |
| **Logistical Disparity Minimization** | Transparent Monitoring | Actively quantify transit time and distance burdens to inform service planning and dispatch. |

---

## 3. Measured (Empirical Prototype Results)

Measured empirical outcomes for the Resource-Aware Care Option Comparer across all synthetic cohorts:

### Cohort Summary Table

| Population Cohort | Total Cases | Baseline Feasible % | Resource-Aware Feasible % | Immediate Escalation % | Language Escalation % | High-Priority Follow-Up Coverage % | Avg Travel Distance (km) | Avg Travel Time (min) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Rural** | 20 | 55.0% (11) | **100.0%** (20) | 0.0% (0) | 55.0% (11) | **100.0%** (4/4) | 23.70 | 94.60 |
| **Urban** | 20 | 75.0% (15) | **100.0%** (20) | 0.0% (0) | 5.0% (1) | **100.0%** (12/12) | 11.22 | 35.15 |
| **English** | 11 | 72.7% (8) | **100.0%** (11) | 0.0% (0) | 0.0% (0) | **100.0%** (5/5) | 14.32 | 49.00 |
| **Tamil** | 29 | 62.1% (18) | **100.0%** (29) | 0.0% (0) | 41.4% (12) | **100.0%** (11/11) | 18.66 | 70.90 |
| **Age 18-35** | 13 | 53.9% (7) | **100.0%** (13) | 0.0% | 23.1% | **100.0%** | 14.81 | 39.46 |
| **Age 36-50** | 7 | 57.1% (4) | **100.0%** (7) | 0.0% | 28.6% | **100.0%** | 18.00 | 80.43 |
| **Age 51-65** | 11 | 72.7% (8) | **100.0%** (11) | 0.0% | 45.5% | **100.0%** | 22.23 | 93.91 |
| **Age 65+** | 9 | 77.8% (7) | **100.0%** (9) | 0.0% | 22.2% | **100.0%** | 15.06 | 54.00 |
| **Overall** | **40** | **65.0%** (26) | **100.0%** (40) | **0.0%** (0) | **30.0%** (12) | **100.0%** (16/16) | **17.46** | **64.88** |

---

## 4. Difference (Deltas & Cohort Gaps)

### A. System Improvement: Resource-Aware vs. Baseline

| Population Group | Baseline Feasibility | Resource-Aware Feasibility | Feasibility Improvement | Baseline Follow-Up Coverage | Resource-Aware Follow-Up Coverage | Accountability Gain |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Rural** | 55.0% | 100.0% | **+45.0%** | 0.0% | 100.0% | **+100.0%** |
| **Urban** | 75.0% | 100.0% | **+25.0%** | 0.0% | 100.0% | **+100.0%** |
| **English** | 72.7% | 100.0% | **+27.3%** | 0.0% | 100.0% | **+100.0%** |
| **Tamil** | 62.1% | 100.0% | **+37.9%** | 0.0% | 100.0% | **+100.0%** |
| **Overall Population** | 65.0% | 100.0% | **+35.0%** | 0.0% | 100.0% | **+100.0%** |

### B. Demographic Disparity Gaps

- **Rural vs. Urban Disparity Gaps**:
  - *Baseline Feasibility Deficit*: **-20.0%** (Rural 55.0% vs. Urban 75.0%). Baseline disproportionately failed rural patients by prescribing unstocked medications or unavailable diagnostic equipment.
  - *Resource-Aware Feasibility Gap*: **+0.0%** (Rural 100.0% vs. Urban 100.0%). The constraint engine eliminated the feasibility deficit by selecting verified local ladder rungs.
  - *Language Escalation Gap*: **+50.0%** (Rural 55.0% vs. Urban 5.0%). Driven by the absence of on-site interpreters at rural Sub-Centers (`SITE-002`) and remote posts (`SITE-004`).
  - *Travel Distance Gap*: **+12.48 km** (Rural 23.70 km vs. Urban 11.22 km; more than double the transit distance).
  - *Travel Time Gap*: **+59.45 minutes** (Rural 94.60 min vs. Urban 35.15 min; nearly triple the transit time).

- **Tamil vs. English Disparity Gaps**:
  - *Baseline Feasibility Deficit*: **-10.7%** (Tamil 62.1% vs. English 72.7%).
  - *Resource-Aware Feasibility Gap*: **+0.0%** (Both 100.0%).
  - *Language Escalation Gap*: **+41.4%** (Tamil 41.4% vs. English 0.0%). Reflects clinician staffing assumptions (English-speaking teleconsultants) paired with unstaffed interpreter rosters at peripheral sites.
  - *Travel Burden Gap*: Tamil patients face +4.34 km distance and +21.90 minutes transit time due to geographic concentration of Tamil cases in peripheral rural regions.

---

## 5. Error Analysis

### Root Cause Breakdown of Baseline Failures

1. **Why Baseline Feasibility Collapsed in Rural Settings (55.0% vs. 75.0%)**:
   - In 9 out of 20 rural cases, the textbook protocol prescribed interventions requiring resources completely absent at peripheral facilities:
     - Prescribed Doppler ultrasound or CT imaging at `SITE-002` (Sub-Center possessing only basic capillary glucometer and BP cuff).
     - Prescribed refrigerated insulin or IV cephalosporins at facilities lacking cold-chain infrastructure.
     - Mandated immediate specialist physical review where no specialist is stationed.
   - In contrast, the resource-aware system adapted 45.0% of rural recommendations down the safety ladder (e.g. to oral metformin + lifestyle review, or oral ampicillin/clavulanate), preserving 100.0% local feasibility.

2. **Why Language Escalation Clustered in Rural Tamil Cases (55.0%)**:
   - The teleconsultation simulation models English-speaking remote clinicians (`clinician_languages=["en"]`).
   - `SITE-002` (Agastheeswaram Sub-Center) and `SITE-004` (Upper Kodayar Primary Health Post) have local staff speaking Tamil but have **zero dedicated interpreters** (`interpreter_languages: []`).
   - When a Tamil-speaking patient presents at these facilities, the language engine deterministically executes the safety rule: *Never proceed blindly without communication verification*. It safely flags `LANGUAGE_ESCALATION_REQUIRED`.
   - In urban centers (`SITE-001`, `SITE-003`, `SITE-006`), interpreters for Tamil, Malayalam, and Hindi are staffed on site, allowing seamless matching (`REQUIRES_INTERPRETER`) without operational escalation.

3. **Transit and Physical Accessibility Bottlenecks**:
   - Rural elderly patients (`Age 51-65` and `65+`) experience average referral transit times of 80 to 94 minutes over 18 to 24 km of difficult terrain.
   - For cases where baseline blindly dictates referral to a tertiary hospital, rural patients face a severe transit barrier, whereas the resource-aware engine prioritizes community-level stabilization.
