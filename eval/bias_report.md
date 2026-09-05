# Bias Evaluation & Demographic Disparity Report

> [!NOTE]
> **Synthetic Data Notice**: Synthetic data only — no real patient data.  
> **Clinical Governance**: Decision-support prototype — clinician sign-off required.  
> **Operational Scope**: Phase 12 evaluation module analyzing paired Baseline vs. Resource-Aware recommendation behaviors across synthetic population groups.

---

## 1. Purpose

The objective of this evaluation is to determine whether clinical recommendation feasibility, follow-up accountability, or operational escalation behaviors systematically differ across synthetic population groups. Specifically, this analysis compares:
- **Rural vs. Urban** populations
- **English vs. Tamil** language speakers
- **Age cohorts** (`18-35`, `36-50`, `51-65`, `65+`)

This is an **analytical evaluation module and reporting suite, NOT a machine learning model**. It uses deterministic, rule-based clinical constraint logic. Any observed divergences between demographic groups reflect underlying physical resource availability, logistical transit infrastructure, cellular network connectivity, language translation staffing, and healthcare service distribution, rather than algorithmic prejudice or model bias.

---

## 2. Synthetic Dataset

The evaluation was executed across the standardized synthetic dataset comprising:
- **40 Synthetic Patient Cases** (`data/cases/synthetic_cases.json`): Diverse clinical presentations across diabetes, hypertension, asthma, infectious disease, and wound care. Each case defines clinical history, urgency level, geographic population group, language profile, and travel constraints.
- **6 Synthetic Healthcare Facility Sites** (`data/services/service_registry.json`): Stratified facility tiers ranging from peripheral Sub-Centers (`SITE-002`) and remote Primary Health Centers (`SITE-004`) to Community Health Centers (`SITE-003`), Sub-District Hospitals (`SITE-005`), and Tertiary Medical Centers (`SITE-001`).
- **Clinician Staffing Model**: Teleconsultation clinicians operating remotely with primary communication language set to English (`["en"]`).

---

## 3. Group Definitions

Cases were segmented into mutually exclusive demographic and geographic cohorts:

1. **Geographic Cohorts**:
   - **Rural** ($N = 20$): Patients presenting at peripheral Sub-Centers (`SITE-002`) and remote mountain posts (`SITE-004`) in Coastal South Rural and Central Highland Remote regions.
   - **Urban** ($N = 20$): Patients presenting at Tertiary Centers (`SITE-001`), Community Health Centers (`SITE-003`), Taluk Hospitals (`SITE-005`), and Municipal Kiosks (`SITE-006`).

2. **Linguistic Cohorts**:
   - **English** ($N = 11$): Patients whose primary spoken and preferred communication language is English.
   - **Tamil** ($N = 29$): Patients whose primary spoken and preferred communication language is Tamil.

3. **Age Band Cohorts**:
   - **Age 18-35** ($N = 13$): Young adult cohort.
   - **Age 36-50** ($N = 7$): Middle-age adult cohort.
   - **Age 51-65** ($N = 11$): Older adult cohort.
   - **Age 65+** ($N = 9$): Geriatric cohort.

---

## 4. Metrics

For each cohort, the following 7 core operational metrics were computed deterministically:

1. **Total Cases**: Number of synthetic patient cases in the cohort.
2. **Feasible Recommendation %**: Percentage of generated recommendations that are executable given the equipment, pharmaceuticals, cold chain, and specialists physically available at the presenting site. Evaluated for both Baseline and Resource-Aware systems.
3. **Immediate Escalation %**: Percentage of cases where the decision engine triggered immediate clinical escalation (`ESCALATE_IMMEDIATELY`) due to critical unresolvable barriers.
4. **Language Escalation %**: Percentage of consultations where patient language could not be directly matched with the clinician or resolved via on-site interpreters, triggering `LANGUAGE_ESCALATION_REQUIRED`.
5. **High-Priority Follow-Up Coverage %**: Percentage of HIGH and CRITICAL urgency cases with complete accountability: an assigned named owner, a calculated due date, and a defined escalation hierarchy. Evaluated for both Baseline and Resource-Aware systems.
6. **Average Travel Distance (km)**: Mean transit distance from patient presentation site to the nearest referral tier.
7. **Average Travel Time (minutes)**: Mean travel time in minutes to the nearest referral tier under standard local transit conditions.

---

## 5. Results

### Complete Cohort Evaluation Results

| Demographic Cohort | Total Cases | Baseline Feasible % | Resource-Aware Feasible % | Immediate Escalation % | Language Escalation % | High-Priority Follow-Up Coverage % | Avg Travel Distance (km) | Avg Travel Time (min) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Rural** | 20 | 55.0% | **100.0%** | 0.0% | 55.0% | **100.0%** | 23.70 | 94.60 |
| **Urban** | 20 | 75.0% | **100.0%** | 0.0% | 5.0% | **100.0%** | 11.22 | 35.15 |
| **English** | 11 | 72.7% | **100.0%** | 0.0% | 0.0% | **100.0%** | 14.32 | 49.00 |
| **Tamil** | 29 | 62.1% | **100.0%** | 0.0% | 41.4% | **100.0%** | 18.66 | 70.90 |
| **Age 18-35** | 13 | 53.9% | **100.0%** | 0.0% | 23.1% | **100.0%** | 14.81 | 39.46 |
| **Age 36-50** | 7 | 57.1% | **100.0%** | 0.0% | 28.6% | **100.0%** | 18.00 | 80.43 |
| **Age 51-65** | 11 | 72.7% | **100.0%** | 0.0% | 45.5% | **100.0%** | 22.23 | 93.91 |
| **Age 65+** | 9 | 77.8% | **100.0%** | 0.0% | 22.2% | **100.0%** | 15.06 | 54.00 |
| **Overall** | **40** | **65.0%** | **100.0%** | **0.0%** | **30.0%** | **100.0%** | **17.46** | **64.88** |

---

## 6. Observed Differences

1. **Elimination of the Rural Feasibility Penalty**:
   - In the unconstrained Baseline, rural patients faced a **20.0% feasibility deficit** (55.0% vs. 75.0% in urban clinics).
   - In the Resource-Aware prototype, feasibility reached **100.0% in both rural and urban cohorts**, successfully closing the geographic deficit. The system achieved this by adapting 45.0% of rural recommendations down the safety ladder (compared to 25.0% in urban clinics) to match verified local supplies.

2. **Substantial Language Escalation Disparity**:
   - Rural patients experienced a **55.0% language escalation rate**, compared to just **5.0%** in urban clinics (representing a **+50.0%** disparity gap).
   - Similarly, Tamil-speaking patients had a **41.4% escalation rate**, while English-speaking patients had **0.0%** (a **+41.4%** disparity gap).
   - This difference occurred because remote teleconsultation clinicians spoke English, and peripheral rural clinics lacked on-site interpreters, triggering safety escalations rather than unverified communication.

3. **Pronounced Physical Logistics and Travel Disparity**:
   - Rural patients had an average travel distance to referral facilities of **23.70 km** and transit time of **94.60 minutes**, compared to **11.22 km** and **35.15 minutes** for urban patients.
   - This constitutes an excess burden of **+12.48 km** and **+59.45 minutes** for rural patients.

4. **Age Cohort Variations**:
   - The older adult cohort (`Age 51-65`) faced the highest travel burden (**22.23 km**, **93.91 minutes**) and highest language escalation rate (**45.5%**), reflecting the geographic clustering of chronic conditions in peripheral rural communities.

---

## 7. Possible Causes

All observed differences are directly attributable to operational, physical, and infrastructural factors rather than model prejudice:

1. **Resource Availability (Equipment, Medications, Cold Chain)**:
   - Primary Health Centers and Sub-Centers have basic formulary lists (oral amoxicillin, paracetamol, metformin) and lack cold-chain refrigeration. Baseline protocols failed because they assumed tertiary hospital capabilities (Doppler ultrasound, IV cephalosporins, refrigerated insulin).
2. **Transport and Road Infrastructure**:
   - Rural facilities are physically separated from secondary and tertiary referral hospitals by rugged terrain, lack of paved highways, and limited public transport, increasing transit times up to 94+ minutes.
3. **Cellular and Network Connectivity**:
   - Rural facilities (`SITE-002`) operate on intermittent 2G/EDGE connectivity (128 kbps), making real-time video teleconsultation difficult and requiring store-and-forward or asynchronous follow-up workflows.
4. **Language Support and Interpreter Staffing**:
   - Dedicated medical interpreters are staffed exclusively at higher-tier facilities (`SITE-001`, `SITE-003`, `SITE-005`, `SITE-006`). Peripheral sub-centers have only local frontline workers who may not speak English, creating a communication barrier when matched with English-only remote clinicians.
5. **Healthcare Service Distribution**:
   - Specialized medical personnel (endocrinologists, cardiologists, vascular surgeons) and diagnostic imaging are concentrated in regional hubs, requiring peripheral patients to rely on adapted primary care alternatives.

---

## 8. Limitations of Synthetic Evaluation

While providing rigorous verification of constraint logic, this evaluation has inherent limitations:

1. **Deterministic Synthetic Cases**: The 40 synthetic patient cases are generated from fixed probability distributions and clinical archetypes, which may not capture the full heterogeneity of complex multi-morbid real-world populations.
2. **Uniform Clinician Language Assumption**: The evaluation assumed all teleconsultation clinicians speak only English (`["en"]`). In actual operational deployment, regional teleconsultation networks frequently staff bilingual or multilingual physicians.
3. **Static Facility Snapshots**: Service registries represent a static point-in-time snapshot. Real-world clinics experience dynamic pharmaceutical stockouts, intermittent generator failures, and fluctuating staffing rosters.
4. **Simplified Transit Models**: Travel distances and times represent nominal estimates and do not account for weather conditions (e.g., monsoon flooding), road closures, or time-of-day traffic congestion.

---

## 9. Mitigation Ideas

To mitigate the observed disparities in actual teleconsultation deployments:

1. **Centralized Multilingual Interpreter Tele-Pool**:
   - Establish a centralized on-demand phone/video medical interpretation pool accessible from all peripheral Sub-Centers (`SITE-002`, `SITE-004`). This would eliminate the 55.0% rural language escalation bottleneck without requiring on-site translator staffing at every village outpost.
2. **Language-Aware Dynamic Clinician Dispatch**:
   - Update the teleconsultation triage queue to route Tamil-speaking patient cases directly to Tamil-fluent clinicians before falling back to English-speaking clinicians.
3. **Decentralized Cold Chain and Essential Supply Caches**:
   - Deploy solar-powered micro-refrigerators to Sub-Centers to enable local stocking of insulin and emergency injectables, reducing the need for clinical downgrading.
4. **Mobile Outreach and Diagnostic Clinics**:
   - Deploy mobile diagnostic vans (equipped with portable ultrasound, ECG, and point-of-care biochemistry) on rotating schedules to peripheral communities to reduce the 94-minute travel burden for elderly patients.
5. **Asynchronous Low-Bandwidth Consultation Protocols**:
   - Implement structured offline store-and-forward workflows for clinics with poor cellular connectivity, allowing auxiliary nurse midwives to record patient data and photos for specialist review when connectivity resumes.
