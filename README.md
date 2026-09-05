# Resource-Aware Care Option Comparer

> [!CAUTION]
> ### SYNTHETIC DATA NOTICE & CLINICAL GOVERNANCE DISCLAIMER
> - **SYNTHETIC DATA — FOR DEMONSTRATION ONLY**
>   All patient cases, facility registries, clinical protocols, and operational records in this prototype are strictly synthetic. No real patient data is used or accepted.
> - **Decision-support prototype — clinician sign-off required.**
>   This system is an assistive clinical decision-support prototype for research, evaluation, and demonstration. It does **not** provide validated diagnostic guidance, autonomous triage, or autonomous prescribing. Every generated care recommendation, ladder adaptation, and escalation order must be reviewed and authorized by a licensed healthcare professional.
> - **Pre-Deployment Operational Notice:**
>   *"This prototype is intended for demonstration and evaluation and requires clinical, regulatory, security, and operational validation before real-world deployment."*

---

## 1. Project Title & Overview

**Resource-Aware Care Option Comparer** is an end-to-end clinical decision-support and operational coordination system designed for multilingual teleconsultation networks. It bridges the critical divide between standard textbook clinical guidelines and the ground-level resource realities of peripheral healthcare outposts (sub-centers, primary clinics, and rural kiosks) across Tamil Nadu and South India in English and Tamil (தமிழ்).

---

## 2. Problem Statement

Teleconsultation dramatically expands specialized medical access to remote geographies. However, conventional teleconsultation models suffer from two systemic vulnerabilities:

1. **The Resource Blindness Gap**: Remote clinicians routinely formulate care plans assuming tertiary medical capabilities—such as unbroken cold-chain refrigeration, CT/Doppler imaging, and on-site specialists. When patients present at peripheral sub-centers that lack these resources, the prescribed care plan is completely unexecutable. Patients are forced to make arduous 90+ minute journeys or silently abandon treatment.
2. **The Follow-Up Disappearance Gap**: Post-consultation instructions (e.g., "repeat capillary glucose in 48 hours" or "monitor wound for cellulitis spread") are traditionally logged as unstructured free-text notes. Without named ownership, calculated SLA due dates, or automated escalation triggers, these critical actions frequently vanish, leading to preventable clinical deterioration.

---

## 3. Why This Matters

- **Healthcare Equity**: Rural and peripheral patients should not be penalized by unexecutable orders that cause treatment drop-out or catastrophic out-of-pocket travel costs.
- **Patient Safety**: Transparent communication matching in the patient's native tongue (Tamil) eliminates dangerous diagnostic misunderstandings.
- **Care Continuity**: Deterministic follow-up tracking with supervisory escalations ensures that high-urgency and chronic patients receive closed-loop care.
- **Clinical Confidence**: Providing remote teleconsultants with real-time visibility into local facility equipment, drug stocks, and transfer times prevents clinical misjudgments.

---

## 4. The Solution: Resource-Aware Care Option Comparer

The system delivers a dual-engine architecture:
1. **Unconstrained Textbook Baseline**: Retrieves the gold-standard protocol recommendation assuming ideal hospital conditions.
2. **Resource-Aware Constraint Engine**: Evaluates the patient against a 4-tier clinical safety ladder (*preferred*, *resource-adapted alternative*, *minimum-safe fallback*, and *escalate-only*), checking local equipment, medication stocks, cold chain, specialists, transport, and network bandwidth.
3. **Multilingual Language Layer**: Resolves patient language against clinician fluency and on-site interpreter rosters, enforcing `LANGUAGE_ESCALATION_REQUIRED` whenever communication safety cannot be guaranteed.
4. **Accountable Follow-Up & Escalation**: Generates structured work orders with named owners, deterministic due dates, and automated multi-tier supervisory escalations.

---

## 5. Architectural Rationale: Why Rules & Constraint Engines Instead of Black-Box ML?

A foundational architectural decision of this project is the use of a **deterministic, rule-based constraint engine** rather than a black-box machine learning (ML) or large language model (LLM) decision agent:

- **Protocols Are Explicit**: Clinical practice guidelines (such as ICMR, WHO, and state health protocols) are explicitly codified as hierarchical recommendation ladders with defined inclusion and exclusion criteria.
- **Resources Are Explicit**: Facility capabilities (equipment lists, pharmaceutical formularies, cold-chain status, specialist schedules) are binary or quantified operational facts, not probabilistic estimations.
- **Decisions Require Medicolegal Auditability**: In healthcare, clinicians must understand the exact causal rationale behind every care recommendation. A machine-learned vector representation cannot provide the legal defensibility of an explicit rule trail.
- **Human-Readable Reason Trails**: The engine produces transparent, step-by-step audit steps (e.g., `✓ captopril available`, `✗ doppler_ultrasound missing -> blocked [preferred] -> adapted to [alternative]`), empowering frontline clinicians to verify logic in seconds.
- **Safety Rules Demand Deterministic Behavior**: Emergency containment, red-flag detection, and fail-safe transfer logic must execute with 100% mathematical certainty. Hallucinations or probabilistic shifts in emergency routing are unacceptable.
- **Escalation Logic Must Be Predictable**: Follow-up SLA timers and hierarchical supervisor handoffs require deterministic state-machine transitions, not statistical guesswork.
- **Small Dataset Does Not Justify ML**: Clinical protocols across target conditions number in the dozens, not millions. Training ML models on small synthetic cohorts risks severe overfitting, spurious correlations, and demographic bias.
- **Governance & Version Control Are Superior**: Rule files and protocol catalogs are stored in transparent JSON/YAML schemas under version control, enabling clinical committees to audit, diff, test, and approve guideline modifications with standard software engineering practices.

---

## 6. End-to-End Architecture & Data Flow

```
                      ┌────────────────────────────────────────┐
                      │         Synthetic Patient Case         │
                      │ (Condition, Urgency, Site, Lang, Travel)│
                      └───────────────────┬────────────────────┘
                                          │
                      ┌───────────────────▼────────────────────┐
                      │            Protocol Engine             │
                      │  (Retrieves 4-Tier Guideline Ladder)   │
                      └─────────────┬──────────────────────────┘
                                    │
            ┌───────────────────────┴───────────────────────┐
            │                                               │
            ▼                                               ▼
┌───────────────────────┐                       ┌───────────────────────┐
│   Textbook Baseline   │                       │   Resource-Aware      │
│  (Unconstrained Rec)  │                       │   Constraint Engine   │
└───────────────────────┘                       │  (Equipment, Drugs,   │
                                                │   Cold Chain, Travel) │
                                                └───────────┬───────────┘
                                                            │
                                                ┌───────────▼───────────┐
                                                │  Language Resolution  │
                                                │   (English / Tamil    │
                                                │    Interpreter Check) │
                                                └───────────┬───────────┘
                                                            │
                                                ┌───────────▼───────────┐
                                                │   Follow-Up Tracker   │
                                                │  (Named Owner, SLA,   │
                                                │   Escalation Path)    │
                                                └───────────┬───────────┘
                                                            │
                                                ┌───────────▼───────────┐
                                                │  Escalation Scheduler │
                                                │   (Overdue Breaches)  │
                                                └───────────┬───────────┘
                                                            │
                                                ┌───────────▼───────────┐
                                                │   User Interfaces     │
                                                │ (Clinician, Follow-Up,│
                                                │  Comparison Screens)  │
                                                └───────────┬───────────┘
                                                            │
                                                ┌───────────▼───────────┐
                                                │ Evaluation & Auditing │
                                                │   (Bias Evaluation,   │
                                                │  Clinician Simulation)│
                                                └───────────────────────┘
```

---

## 7. Technology Stack

- **Core Backend**: Python 3.12, FastAPI, Starlette, Pydantic v2, SQLite (via pure Python standard library `sqlite3`), PyYAML.
- **Frontend / UI**: Vanilla HTML5, Modern CSS3 (Dark mode, glassmorphism, responsive grid), Vanilla JavaScript (ES6+), Google Fonts (*Outfit*, *Inter*, *Noto Sans Tamil*). No heavy frontend framework dependencies.
- **Testing & Quality Assurance**: pytest, pytest-asyncio, FastAPI TestClient, httpx.
- **Data & Evaluation**: JSON / YAML schema standards, custom deterministic statistical evaluators.

---

## 8. Repository Structure

```
resource-aware-care-comparer/
├── baseline/                        # Phase 1 & 7: Textbook baseline comparator engine
│   ├── baseline_engine.py
│   └── README.md
├── config/                          # System configurations (urgency, languages, escalation)
│   ├── default_config.yaml
│   ├── followup_rules.json
│   └── languages.yaml
├── data/                            # Verified synthetic datasets & generated outputs
│   ├── cases/synthetic_cases.json   # 40 diverse synthetic patient cases
│   ├── generated/                   # Comparison results & summary exports
│   ├── languages/messages_*.json    # Bilingual message catalogs (en, ta)
│   ├── protocols/protocols.json     # 5 clinical protocols with 4-tier ladders
│   └── services/service_registry.json # 6 stratified healthcare facilities
├── docs/                            # Comprehensive engineering & governance documentation
│   ├── 01_scenario_definition.md
│   ├── 02_baseline_method.md
│   ├── 03_ethics_note.md            # Phase 14: 14-point ethics & clinical governance note
│   ├── 04_deployment_checklist.md   # Phase 14: 7-domain pre-deployment readiness checklist
│   ├── comparison_method.md
│   ├── constraint_engine.md
│   ├── followup_and_escalation.md
│   └── multilingual_language_layer.md
├── eval/                            # Evaluation and auditing suite
│   ├── bias_eval.py                 # Phase 12: Demographic & geographic disparity evaluator
│   ├── bias_report.md               # Phase 12: 9-section bias evaluation report
│   ├── clinician_validation.md      # Phase 13: 5-persona simulated validation report
│   ├── results.json / results.md    # Phase 12: Empirical baseline vs prototype results
│   ├── run_validation.py            # Phase 13: Clinician validation runner
│   └── validation_cases.json        # Phase 13: 10 curated validation cases
├── scripts/                         # Operational CLI scripts
│   ├── demo.py                      # Phase 15: Master 4-scenario automated demo
│   ├── generate_cases.py            # Synthetic case cohort generator
│   ├── run_comparison.py            # Batch 40-case paired comparison pipeline
│   ├── run_server.py                # Local web server runner
│   └── run_tests.py                 # Test runner utility
├── src/                             # Core application source code
│   ├── api/                         # FastAPI route modules (health, cases, followup, etc.)
│   ├── comparer/                    # Paired comparison models & runner
│   ├── constraint_engine/           # Feasibility filter & reason trail builder
│   ├── followup/                    # State machine, repository, scheduler & escalation
│   ├── language/                    # Language resolver, translator, & message catalog
│   ├── models/                      # Pydantic domain models (operational & config)
│   └── protocol_engine/             # Protocol loader & query engine
├── tests/                           # Complete automated test suite (159 tests)
│   ├── comparer/                    # Comparer output & metric tests
│   ├── edge_cases/                  # Failure states, broken chains, conflict tests
│   ├── followup/                    # Due date, overdue, and escalation tests
│   ├── language/                    # English & Tamil message & escalation tests
│   ├── test_bias_eval.py            # Phase 12 bias evaluation tests
│   ├── test_clinician_validation.py # Phase 13 simulated clinician validation tests
│   └── test_ethics_and_deployment.py# Phase 14 ethics & deployment tests
├── ui/                              # User Interface Screens
│   ├── clinician/                   # Phase 8: Clinician Teleconsult Screen
│   ├── followup/                    # Phase 9: Follow-up Coordinator Screen
│   ├── comparer/                    # Phase 10: Care Option Comparison Screen
│   ├── index.html                   # Phase 15: Master Navigation Landing Page
│   └── style.css                    # Unified design tokens & styling
└── README.md                        # Master repository documentation
```

---

## 9. Installation & Getting Started

### Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- `pip` package manager

### 1. Clone & Set Up Environment
```bash
# Navigate to project directory
cd resource-aware-care-comparer

# Create and activate virtual environment (optional but recommended)
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 10. How to Run

### Run the Web Application
```bash
python scripts/run_server.py
```
*The web server will start at `http://127.0.0.1:8000`.*

### UI Screen URLs
- **Main Landing Page**: [http://127.0.0.1:8000/ui/index.html](http://127.0.0.1:8000/ui/index.html)
- **Clinician Screen**: [http://127.0.0.1:8000/ui/clinician/index.html](http://127.0.0.1:8000/ui/clinician/index.html)
- **Follow-up Queue**: [http://127.0.0.1:8000/ui/followup/index.html](http://127.0.0.1:8000/ui/followup/index.html)
- **Option Comparer**: [http://127.0.0.1:8000/ui/comparer/index.html](http://127.0.0.1:8000/ui/comparer/index.html)
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 11. How to Run the Automated Demonstration

To run the complete automated scenario demonstration directly in your terminal:
```bash
python scripts/demo.py
```
This script automatically executes:
1. **Scenario 1**: Full resource availability -> Preferred option confirmed feasible.
2. **Scenario 2**: Specialist & cold-chain missing -> Resource-adapted ladder rung selected.
3. **Scenario 3**: Total formulary exhaustion -> `ESCALATE_IMMEDIATELY` fail-safe transfer triggered.
4. **Scenario 4**: Follow-up SLA breached -> Automated escalation to supervisory health officer.
5. **Multilingual Demo**: Reason trail rendered in Tamil (`ta`) + Language safety gate demonstration.

---

## 12. How to Run Tests

Run the complete 159-test suite with coverage across all modules:
```bash
pytest
```
Run specific module test suites:
```bash
# Edge case tests
pytest tests/edge_cases/ -v

# Phase 12 Bias evaluation tests
pytest tests/test_bias_eval.py -v

# Phase 13 Simulated clinician validation tests
pytest tests/test_clinician_validation.py -v

# Phase 14 Ethics & deployment checklist tests
pytest tests/test_ethics_and_deployment.py -v
```

---

## 13. How to Run Comparisons & Evaluations

### Batch Paired Comparison Pipeline
```bash
python scripts/run_comparison.py
```
*Generates `data/generated/comparison_results.json` and `comparison_summary.json`.*

### Phase 12 Bias & Disparity Evaluation
```bash
python eval/bias_eval.py
```
*Generates `eval/results.json`, `eval/results.md`, and `eval/bias_report.md`.*

### Phase 13 Clinician Validation Simulation
```bash
python eval/run_validation.py
```
*Generates `eval/validation_results.json` and `eval/clinician_validation.md`.*

---

## 14. Multilingual English & Tamil Support

The system incorporates full bilingual parity:
- **Language Resolver**: Resolves patient primary/preferred language against clinician fluency and site interpreter staffing.
- **Language Safety Gate**: If an English-only clinician treats a Tamil-speaking patient at a facility without an interpreter, the consultation is halted with `LANGUAGE_ESCALATION_REQUIRED`. No silent translations are permitted.
- **Vernacular Translations**: Localized message catalogs (`data/languages/messages_ta.json`) provide native Tamil rendering for reason trails, UI labels, governance notices, and safety banners.

---

## 15. Empirical Evaluation Results

### Phase 12 Bias & Disparity Findings (All 40 Cases)

| Population Group | Total Cases | Baseline Feasible % | Resource-Aware Feasible % | Immediate Escalation % | Language Escalation % | High-Priority Follow-Up Coverage % | Avg Travel Distance | Avg Travel Time |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Rural** | 20 | 55.0% (11/20) | **100.0%** (20/20) | 0.0% | 55.0% | **100.0%** (4/4) | 23.70 km | 94.60 min |
| **Urban** | 20 | 75.0% (15/20) | **100.0%** (20/20) | 0.0% | 5.0% | **100.0%** (12/12) | 11.22 km | 35.15 min |
| **English** | 11 | 72.7% (8/11) | **100.0%** (11/11) | 0.0% | 0.0% | **100.0%** (5/5) | 14.32 km | 49.00 min |
| **Tamil** | 29 | 62.1% (18/29) | **100.0%** (29/29) | 0.0% | 41.4% | **100.0%** (11/11) | 18.66 km | 70.90 min |
| **Overall** | **40** | **65.0%** (26/40) | **100.0%** (40/40) | **0.0%** | **30.0%** | **100.0%** (16/16) | **17.46 km** | **64.88 min** |

- **Deficit Elimination**: Unconstrained baseline had a **-20.0% feasibility penalty in rural settings** (55% vs 75% urban) due to assuming unavailable specialists and cold chain. The Resource-Aware Comparer closed this deficit entirely (**100.0% vs 100.0%**).
- **Causal Disparities**: Rural language escalations (55.0%) clustered exclusively due to lack of interpreter staffing at peripheral Sub-Centers (`SITE-002`) and health posts (`SITE-004`), proving disparities stem from physical infrastructure rather than algorithmic bias.

### Phase 13 Simulated Clinician Validation

Five simulated clinician personas evaluated 10 representative cases across 7 standardized criteria on a 1–5 scale:
- **Overall System Validation Score**: **4.51 / 5.0** (*Exemplary Decision-Support Grade*)
- **Dr. Aruna Sundaram (Primary Care Reviewer)**: **4.86 / 5.0**
- **Dr. Chellappa Maran (Rural Health Reviewer)**: **4.51 / 5.0**
- **Dr. Priya Venkatesh (Teleconsult Operations Reviewer)**: **4.43 / 5.0**
- **Dr. K. R. Nambiar (Patient Safety Reviewer)**: **4.58 / 5.0**
- **Dr. Meenakshi Ramanathan (Language Access Reviewer)**: **4.18 / 5.0**

---

## 16. Edge Cases Handled

The system is fortified against critical operational edge cases:
1. **Total Option Exhaustion**: When all ladder tiers are blocked, system triggers `ESCALATE_IMMEDIATELY` and routes to referral center.
2. **Missing Escalation Contact**: Automatically reassigns to default regional supervisor (`district_health_officer`) if contact is unlisted.
3. **Idempotent Escalations**: Repeated overdue checks do not trigger duplicate escalation loops.
4. **Registry Conflicts**: Detects overlapping or contradictory capability records.
5. **Zero Travel Friction**: Handles collocated patients presenting directly at tertiary centers without divide-by-zero errors.

---

## 17. Ethics & Deployment Limitations

### Ethical Principles
- **Decision-Support Only**: strictly non-diagnostic; assists licensed practitioners.
- **Clinician Sign-Off Required**: human-in-the-loop authorization required for all directives.
- **No Real Patient Data**: 100% synthetic data pipeline eliminates privacy risks.
- **Explainability**: deterministic, step-by-step reason trails.
- **Human Override**: clinicians retain full authority to override recommendations.

### Known Limitations
- **Heuristic Simulation**: Simulated personas and synthetic cases do not replace prospective randomized clinical trials.
- **Static Registry Snapshots**: Registries reflect point-in-time audits and do not track intraday power cuts or unexpected batch stockouts.
- **Nominal Travel Estimates**: Nominal transit models do not account for extreme monsoon flooding or localized road closures.
- **Regulatory Status**: Prototype has not been submitted for FDA, CE-MDR, or CDSCO medical device clearance.

---

## 18. Hackathon Demonstration Quickstart

To launch a complete live demonstration for hackathon evaluators in one command:
```bash
# Terminal 1: Start backend server
python scripts/run_server.py

# Terminal 2: Run automated end-to-end demo
python scripts/demo.py
```
Open [http://127.0.0.1:8000/ui/index.html](http://127.0.0.1:8000/ui/index.html) in your browser to explore the interactive visual interface!
