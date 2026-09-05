# 01. Scenario Definition: Resource-Aware Care Option Comparer

> [!CAUTION]
> **SYNTHETIC DATA NOTICE & CLINICAL DISCLAIMER**
> **All patient cases, service registries, protocols, and operational records in this prototype are synthetic. No real patient data is used.**
> This software is an illustrative decision-support prototype and does **not** provide validated clinical guidance.
> **Decision-support prototype — clinician sign-off required.** Every generated comparison, referral pathway, and recommendation must be evaluated and authorized by a licensed healthcare professional.

---

## 1. Problem Statement

Teleconsultation services expand healthcare access across remote and underserved regions by connecting patients with remote medical specialists. However, conventional teleconsultation models operate under an implicit, dangerous assumption: **that ideal clinical resources exist and are immediately accessible at the patient's actual point of care.**

In practice, standard protocols recommend interventions such as:
- Immediate advanced diagnostic imaging (e.g., MRI, Doppler ultrasound, CT angiogram)
- Specialized physician evaluation (e.g., pediatric neurologist, endocrinologist, vascular surgeon)
- Specific pharmaceutical regimens requiring unbroken cold-chain storage or specialized dispensing
- Frequent in-clinic monitoring and scheduled laboratory panels

When a remote clinician issues textbook guidelines without visibility into local infrastructure, patients receive care plans that are logistically impossible to follow. Consequently, treatment is delayed, patients incur catastrophic out-of-pocket transportation costs searching for unavailable resources, or patients silently drop out of care.

A compounding failure occurs in **care coordination and follow-up**. When a teleconsultation concludes with multi-step follow-up instructions (e.g., "obtain liver function test in 72 hours and report back"), these actions frequently vanish into an operational void. Without clear task assignment, deadline tracking, and automatic escalation pathways, pending actions disappear, leading to preventable clinical deterioration.

The **Resource-Aware Care Option Comparer** addresses these twin challenges by contrasting the unconstrained "textbook protocol" against a "resource-aware recommendation" calibrated to local facilities, travel friction, language needs, and verified follow-up capabilities.

---

## 2. Current Teleconsultation Workflow

The current baseline teleconsultation workflow typically follows a linear, non-adaptive path:

```
[Patient / Village Kiosk]
          │
          ▼
1. Triage & Intake (Basic vital signs collected by local health worker)
          │
          ▼
2. Remote Teleconsultation Session (Video or audio call with remote clinician)
          │
          ▼
3. Textbook Clinical Assessment (Clinician applies standard national/disease protocol)
          │
          ▼
4. Prescription & Advice Issued (Assuming regional laboratory, pharmacy, & referral capacity)
          │
          ▼
5. Patient Discharged to Community (Patient left to locate diagnostics and medications independently)
          │
          ▼
[FAIL POINT]: Follow-up untracked; Stockouts unmitigated; Silent drop-out
```

### Key Breakpoints in the Current Workflow:
1. **Intake Blindness:** The remote clinician receives vital signs and symptoms but zero telemetry regarding current local medicine stockouts, technician staffing, or road washouts.
2. **Abstract Protocolizing:** Prescriptions are generated from static clinical handbooks that assume a tertiary hospital environment.
3. **Operational Orphanhood:** Instructions to "repeat blood glucose in 48 hours" are logged in consultation notes as free text rather than tracked as accountable work orders with deadlines and assigned owners.

---

## 3. Operational Gap

The operational gap represents the organizational and logistical friction between centralized clinical decision-makers and peripheral healthcare delivery.

* **Siloed Responsibilities:** Remote clinicians provide medical advice in an episodic bubble; local health workers (e.g., ASHAs, ANMs, community health nurses) handle community execution without real-time feedback loops.
* **Coordination Deficit:** Care coordinators lack an integrated operational dashboard that maps which patient requires transportation subsidies, local appointment slots, or home specimen collection.
* **Language and Literacy Asymmetries:** Clinical discharge summaries generated in English are poorly understood by vernacular-speaking patients and local caregivers, creating compliance failure.

---

## 4. Resource Gap

The resource gap consists of physical, logistical, and infrastructural shortages at the patient's geographic location:

| Resource Dimension | Textbook Assumption | Local Reality in Peripheral Areas |
| :--- | :--- | :--- |
| **Diagnostic Imaging & Labs** | Immediate CBC, ultrasound, or HbA1c testing within 24 hours. | Nearest ultrasound is 45 km away; blood sample courier operates twice weekly; reagent stockouts. |
| **Medications & Cold Chain** | Daily refrigerated insulin, specialized second-line antimicrobials. | Unreliable electricity grid; local sub-center lacks cold-chain storage; stockouts of oral third-generation cephalosporins. |
| **Specialist Availability** | Rapid in-person consultation with an endocrinologist or cardiologist. | Specialists visit the district headquarters once a month; waitlists exceed 6 weeks. |
| **Patient Mobility & Transit** | Patient can travel to the district hospital independently. | Seasonal monsoon cuts off unpaved access roads; public transit bus runs once daily; transit costs exceed daily income. |
| **Connectivity & Power** | High-bandwidth video link for virtual reviews. | Intermittent 2G/EDGE cellular data; prolonged power outages requiring asynchronous or SMS/audio fallbacks. |

---

## 5. Follow-Up Gap

Follow-up failure is the primary mechanism through which minor health conditions escalate into life-threatening emergencies.

* **Absence of Accountability:** Follow-up tasks are rarely assigned to a named individual. A recommendation like "monitor blood pressure twice daily" belongs to neither the patient nor the local worker formally.
* **Unmonitored Deadlines:** Without automated due-date calculation (relative to clinical urgency), deadlines lapse unnoticed.
* **Missing Escalation Channels:** If a patient with severe hypertension fails to report vital signs within 24 hours, the system fails to alert the local health worker, care coordinator, or supervising clinician.
* **No Closed-Loop Verification:** There is no mechanism confirming whether prescribed medications were actually dispensed or diagnostic tests actually conducted.

---

## 6. Actors

The system defines four distinct, collaborative human actors:

```
┌─────────────────────────────────────────────────────────────┐
│                       REMOTE CLINICIAN                      │
│             (Diagnostic review & clinical sign-off)         │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────┴──────────────────────────────┐
│                       CARE COORDINATOR                      │
│            (Resource orchestration & escalation triage)     │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────┴──────────────────────────────┐
│                     LOCAL HEALTH WORKER                     │
│         (Direct patient contact, vitals, field execution)   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                           PATIENT                           │
│        (Recipient of care, localized action instructions)   │
└─────────────────────────────────────────────────────────────┘
```

1. **Patient:** The individual seeking care or management for an acute or chronic condition. May have limited functional literacy, digital access, or travel resources.
2. **Remote Clinician:** A licensed physician conducting teleconsultation from a tertiary or centralized hub, responsible for medical diagnosis and clinical validation.
3. **Local Health Worker (LHW):** An accredited social health activist (ASHA), auxiliary nurse midwife (ANM), or community health worker situated physically near the patient. Acts as the primary human touchpoint for physical assessment and regimen administration.
4. **Care Coordinator:** An operational manager responsible for tracking follow-up task queues, scheduling transfers, reconciling supply/resource registries, and managing escalations.

---

## 7. Responsibilities of Each Actor

### A. Patient
- Provide accurate symptom descriptions (assisted by LHW if needed).
- Adhere to localized care instructions delivered in their preferred language.
- Report adverse reactions or lack of improvement to the local health worker.

### B. Remote Clinician
- Conduct teleconsultation assessment.
- Review comparative options: standard protocol vs. resource-aware adaptation.
- Authorize and sign off on the final clinical regimen (**mandatory clinical sign-off**).
- Address high-tier clinical escalations triggered by follow-up deviations.

### C. Local Health Worker (LHW)
- Collect and verify vital signs and patient history.
- Inspect and report local resource constraints (e.g., current clinic stock, transport road conditions).
- Execute field actions: dispense verified in-stock medications, explain instructions in vernacular language, observe therapy.
- Complete assigned follow-up checklists before deadlines expire.

### D. Care Coordinator
- Monitor the operational dashboard for overdue follow-up milestones.
- Intervene on resource constraints (e.g., dispatch alternative delivery, authorize travel stipends).
- Escalate missed critical checkpoints from Level 0 to Level 3.
- Maintain accurate service, facility, and supply registries.

---

## 8. Languages in Scope

The system features an internationalized architecture capable of seamless multilingual interaction across clinical and field actors.

### Phase 1 Languages:
1. **English (`en`):** Primary administrative and clinical interface language for medical documentation, audit logging, and coordinator interfaces.
2. **Tamil (`ta` - தமிழ்):** Vernacular language for local health worker instructions, patient care summaries, follow-up notifications, and alert messages.

### Architectural Language Extensibility:
- Languages are defined through dynamic configuration files (`languages.yaml`).
- Translation keys decouple interface components and protocol templates from display strings.
- Directionality (LTR/RTL), regional script encodings (UTF-8), and localized date-time formatting are integrated into model schemas.
- Future languages (e.g., Hindi `hi`, Telugu `te`, Kannada `kn`, Bengali `bn`) can be incorporated via declarative configuration without application recompilation.

---

## 9. Example Patient Journey

### Scenario: Synthetic Patient Case — "Meenakshi", 54-Year-Old Female, Rural Kanyakumari District
*(Synthetic Case Identifier: `SYNTH-CASE-2026-081`)*

#### Initial Presentation:
- **Chief Complaint:** 5-day history of non-healing ulcer on right plantar foot, elevated random blood sugar (310 mg/dL), mild surrounding erythema.
- **Location:** Peripheral village sub-center (18 km from secondary taluk hospital; 65 km from tertiary medical college).
- **Language:** Tamil only (`ta`).

#### 1. Baseline Textbook Protocol Recommendation:
- Immediate surgical debridement consultation by vascular/orthopedic surgeon.
- Non-contrast MRI of the right foot to exclude osteomyelitis within 24 hours.
- Initiate subcutaneous basal-bolus insulin regimen (requires continuous 2°C–8°C refrigeration).
- Daily dressing change with hydrocolloid dressings.
- Follow-up in specialist outpatient clinic in 48 hours.

#### 2. Ground-Truth Resource Constraints Identified:
- **Imaging:** No MRI or radiography available within 40 km; road travel limited by monsoon rains.
- **Medication:** Patient has no domestic refrigerator; local sub-center refrigerator compressor is out of order. Secondary facility has oral hypoglycemic agents (Metformin, Glimepiride) and broad-spectrum oral antibiotics in stock.
- **Specialists:** Next visiting physician arrives at taluk hospital in 5 days.

#### 3. Resource-Aware Recommendation Generated:
- **Immediate Local Care:** Aggressive local wound irrigation with sterile normal saline and povidone-iodine; offloading padding using locally fabricated pressure relief splint.
- **Oral Pharmacotherapy:** Transition to high-dose oral antimicrobial regimen matching verified local dispensary stock; optimize oral hypoglycemic therapy with tight local capillary blood glucose monitoring.
- **Tele-imaging Alternative:** High-resolution photographic wound inspection taken by LHW transmitted asynchronously for remote wound-care specialist review every 48 hours.
- **Follow-up Plan with Escalation:**
  - *Action 1:* LHW home visit at 24 hours to measure fasting capillary glucose and photograph wound margin. (Owner: Local Health Worker, Deadline: T+24h, Escalation Level: L1).
  - *Action 2:* If erythema advances >1 cm or patient develops systemic fever (>38°C), initiate Level 3 emergency transport to district hospital.

#### 4. Clinician Sign-Off & Vernacular Delivery:
- Remote clinician reviews both options on screen, evaluates trade-offs, and signs off on the resource-aware plan.
- The system generates:
  - Clinical English summary for medical records.
  - Tamil (`தமிழ்`) instruction checklist for the Local Health Worker and patient caregiver with clear pictorial care steps.

---

## 10. System Boundary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SYSTEM BOUNDARY (IN SCOPE)                         │
│                                                                             │
│  [Synthetic Case Ingestion] ──► [Resource Registry & Constraint Filter]    │
│                                              │                              │
│                                              ▼                              │
│  [Textbook Protocol Library] ──► [Care Option Comparer Engine]              │
│                                              │                              │
│                                              ▼                              │
│  [Multilingual Localization] ◄── [Clinician Sign-off & Audit Logging]      │
│               │                                                             │
│               ▼                                                             │
│  [Follow-up & Escalation Tracker (Task Deadlines & Ownership)]             │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                      OUT OF SCOPE / EXTERNAL BOUNDARIES
                                       ▼
 ┌──────────────────────────────┬──────────────────────────────┐
 │  Direct Telemetry / EHR write│  Automated AI Diagnostics    │
 │  Payment / Billing Gateways  │  Real-time Hardware Monitors │
 └──────────────────────────────┴──────────────────────────────┘
```

### In Scope:
- Ingestion and management of synthetic patient profiles and clinical case scenarios.
- Declarative catalog of clinical protocols (textbook guidelines).
- Declarative facility and resource inventory (diagnostics, cold chain, drug availability, transit times).
- Comparative analysis highlighting delta between ideal protocol vs. locally feasible options.
- Mandatory clinician authorization and sign-off interface mechanisms.
- Internationalized communication generation (English / Tamil).
- Time-bounded follow-up task tracking with multi-tier escalation triggers.

### Out of Scope:
- Direct integration with proprietary hospital billing systems or national EHR databases.
- Autonomous algorithmic prescribing without human-in-the-loop clinician sign-off.
- Real-time IoT biometric device streaming.
- Emergency 911/108 ambulance automated dispatch hardware.

---

## 11. Prototype Limitations

1. **Illustrative Decision-Support Only:** The comparative recommendations generated by the system are designed to structure decision-making; they do not constitute validated clinical practice guidelines.
2. **Deterministic Constraint Rules:** The initial prototype employs explicit rule-based constraints and deterministic logic rather than probabilistic clinical AI/ML models.
3. **Synthetic Environment:** All operational data, network latencies, travel times, and drug stocks are simulated for development, demonstration, and evaluation purposes.
4. **Human Verification Obligation:** The system refuses to publish or transmit care plans to patients or field workers without cryptographically verifiable clinician sign-off.

---

## 12. Synthetic-Data Policy

> [!IMPORTANT]
> **SYNTHETIC DATA MANDATE**
> - **All patient cases, service registries, protocols, and operational records in this prototype are synthetic. No real patient data is used.**
> - Under no circumstances should real Protected Health Information (PHI), Personally Identifiable Information (PII), or confidential clinical records be imported, processed, or stored in this repository.
> - All synthetic test cases use fabricated names, artificial locations, randomized timestamps, and simulated medical parameters.
> - Any correlation between synthetic profiles and real individuals is entirely coincidental.
> - Datasets generated or utilized within the `data/` directory must maintain clear metadata headers affirming synthetic origin.
