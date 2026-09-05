# Resource-Aware Care Option Comparer

> [!CAUTION]
> ### CLINICAL DECISION-SUPPORT & SYNTHETIC DATA GOVERNANCE
> - **Decision-support prototype — clinician sign-off required.**
>   This system is an illustrative software prototype for research and evaluation. It does **not** provide validated clinical guidance, diagnostic determinations, or autonomous prescribing. Every comparison and recommendation generated requires explicit review and sign-off by a qualified, licensed clinician.
> - **Synthetic data only — no real patient data.**
>   All patient cases, facility registries, medical histories, and operational records in this repository are synthetic. No real patient data is used or accepted.

---

## 1. Project Purpose

The **Resource-Aware Care Option Comparer** is an end-to-end web application prototype engineered for multilingual teleconsultation services. It bridges the critical divide between standard clinical protocol recommendations and the operational realities of peripheral healthcare settings (such as primary health sub-centers, rural clinics, and home-based triage).

The system serves two complementary functions:
1. **Option Comparison:** Contrasting an ideal "textbook/protocol recommendation" against a realistic "resource-aware recommendation" constrained by actual local inventories, diagnostic availability, travel friction, and language needs.
2. **Accountable Follow-up Orchestration:** Preventing critical follow-up actions from vanishing into operational voids through ownership assignment, deadline monitoring, and automated multi-tier escalations.

---

## 2. Problem Statement

Teleconsultation services expand medical access to underserved geographies. However, conventional teleconsultations frequently suffer from two systemic failures:

1. **The Resource Blindness Gap:** Remote clinicians issue care plans assuming the immediate availability of advanced diagnostics (e.g., MRI, ultrasound), specialty physicians, continuous cold-chain refrigeration, and prompt pharmaceutical dispensing. When patients cannot access these resources locally, treatment is delayed or abandoned, often leading to acute deterioration.
2. **The Follow-up Disappearance Gap:** Post-consultation tasks (e.g., "repeat capillary blood glucose in 24 hours," "dispatch oral antibiotics," "schedule taluk hospital transport") are routinely recorded as unassigned text notes. Without explicit task owners, deadline tracking, or escalation triggers, these critical milestones are dropped.

---

## 3. Architecture Overview

Phase 1 & Phase 2 established the extensible modular backend, protocol library, protocol engine, and textbook baseline:

```
resource-aware-care-comparer/
├── docs/
│   ├── 01_scenario_definition.md    # Comprehensive operational & clinical scenario
│   ├── 02_baseline_method.md        # Textbook baseline methodology & evaluation design
│   └── constraint_engine.md         # Resource constraint engine & reason trail specification
├── baseline/
│   ├── __init__.py
│   ├── baseline_engine.py           # Unconstrained textbook protocol baseline comparator
│   └── README.md                    # Baseline documentation & contract
├── src/
│   ├── __init__.py
│   ├── main.py                      # FastAPI application factory & middleware
│   ├── config.py                    # YAML loader with environment-variable overrides
│   ├── models/
│   │   ├── __init__.py
│   │   ├── config_models.py         # Pydantic schemas (urgency, escalation, languages)
│   │   └── operational_models.py    # Operational schemas (sites, travel, cases)
│   ├── protocol_engine/
│   │   ├── __init__.py
│   │   ├── models.py                # Protocol & 4-tier recommendation ladder models
│   │   ├── protocol_loader.py       # JSON catalog parser with uniqueness validation
│   │   └── protocol_engine.py       # Protocol query, indexing, & ladder retrieval
│   ├── constraint_engine/
│   │   ├── __init__.py
│   │   ├── models.py                # Constraint engine results & evaluation models
│   │   ├── resource_filter.py       # Resource capability matcher & conflict safety
│   │   ├── feasibility.py           # Deterministic ladder traversal & safety rules
│   │   └── reason_trail.py          # Human-readable chronological reason trail
│   ├── data_generation/
│   │   ├── __init__.py
│   │   └── case_generator.py        # Deterministic 40-case synthetic generator
│   └── api/
│       ├── __init__.py
│       └── routes_health.py         # GET /health and GET /health/detail endpoints
├── ui/                              # Web frontend assets (HTML/CSS/JS)
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures and TestClient initialization
│   ├── test_health.py               # Healthcheck & header tests
│   ├── test_config.py               # Configuration & domain model tests
│   ├── test_protocol_engine.py      # Protocol loading, query, & ladder tests
│   ├── test_baseline.py             # Baseline unconstrained lookup tests
│   ├── test_operational_data.py     # 40-case distribution & registry tests
│   ├── test_constraint_engine.py    # Feasibility evaluation & ladder traversal tests
│   └── edge_cases/
│       ├── __init__.py
│       ├── test_config_edge_cases.py  # Configuration boundary tests
│       ├── test_no_feasible_option.py # Option exhaustion & immediate escalation tests
│       ├── test_registry_conflict.py  # Safety-first registry conflict tests
│       └── test_language_mismatch.py  # Language barrier & translator safety tests
├── eval/                            # Evaluation frameworks & metric benchmarks
├── data/
│   ├── protocols/
│   │   └── protocols.json           # Approved synthetic protocol catalog (5 conditions)
│   ├── services/
│   │   └── service_registry.json    # Synthetic healthcare facilities (6 sites)
│   ├── cases/
│   │   └── synthetic_cases.json     # Exactly 40 diverse synthetic patient cases
│   └── generated/                   # Simulated comparative runs & logs
├── config/
│   ├── default_config.yaml          # App, urgency, and escalation rules
│   └── languages.yaml               # Extensible multilingual language registry
├── scripts/
│   ├── run_server.py                # Server execution script
│   ├── run_tests.py                 # Test execution runner
│   └── generate_cases.py            # Case generation CLI (seed=42)
├── requirements.txt
├── README.md
└── .gitignore
```
│   └── generated/                   # Simulated comparative runs & logs
├── config/
│   ├── default_config.yaml          # App, urgency, and escalation rules
│   └── languages.yaml               # Extensible multilingual language registry
├── scripts/
│   ├── run_server.py                # Server execution script
│   └── run_tests.py                 # Test execution runner
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 4. Phase 2 Status: Synthetic Protocol Library + Baseline

Phase 2 introduces the core clinical protocol data structures, the protocol retrieval engine, and the textbook baseline engine:

### A. Synthetic Protocol Library (`data/protocols/protocols.json`)
Contains 5 generic, illustrative clinical protocols:
- `PROTO-001` (`condition_alpha` - High urgency: acute progressive soft-tissue infection)
- `PROTO-002` (`condition_beta` - Medium urgency: sub-acute decompensated metabolic/glycemic risk)
- `PROTO-003` (`condition_gamma` - Critical urgency: acute hemodynamic & neurologic vulnerability)
- `PROTO-004` (`condition_delta` - Low urgency: primary chronic cardiovascular & hypertension)
- `PROTO-005` (`condition_epsilon` - Medium urgency: reactive airway bronchospasm & respiratory distress)

Each protocol defines:
- Standard identifiers, version, urgency tier, and full textbook recommendation
- Theoretical resource requirements (`same_day_imaging`, `specialist_48h`, `medication_stock`, `cold_chain`, `transport`, `stable_connectivity`, `interpreter`, `local_clinician`)
- Structured **4-Tier Recommendation Ladder**:
  1. `preferred`: Unconstrained gold standard
  2. `resource_adapted_alternative`: Feasible alternative when key diagnostics/cold-chain are missing
  3. `minimum_safe_fallback`: Basic maintenance or stabilization option in austere settings
  4. `escalate_only`: Mandatory transfer/escalation trigger

### B. Protocol Engine (`src/protocol_engine/`)
- `get_protocol(condition: str)`: Fast indexed lookup by condition code (case-insensitive)
- `get_protocol_by_id(protocol_id: str)`: Lookup by protocol ID
- `get_recommendation_ladder(condition: str)`: Retrieves the 4-tier recommendation ladder
- `validate_protocols()`: Structural and semantic integrity validation across all catalog entries

### C. Textbook Baseline Engine (`baseline/baseline_engine.py`)
- Accepts a synthetic case (e.g. `{"case_id": "...", "condition": "condition_alpha"}`)
- Returns the official unconstrained textbook recommendation
- **Strict Invariant:** Deliberately ignores site diagnostics, drug stockouts, transport limits, cold-chain absence, and language constraints (`resource_checked=False`, `follow_up_checked=False`)
- Serves as the comparison anchor for subsequent resource-aware evaluation

### Core Stakeholders (Actors):
- **Patient:** Care recipient receiving instructions in their preferred vernacular language.
- **Remote Clinician:** Teleconsultation physician reviewing options and providing mandatory sign-off.
- **Local Health Worker (LHW):** Field caregiver (ASHA/ANM) conducting in-person assessments and administering regimens.
- **Care Coordinator:** Operational controller monitoring task queues, supply stocks, and escalations.

### Supported Languages (Phase 1):
- **English (`en`):** Clinical documentation and administrative control.
- **Tamil (`ta` - தமிழ்):** Patient communication and field worker instructions.
*(Designed for seamless configuration-driven expansion to Hindi, Telugu, Kannada, etc.)*

### Urgency & Escalation Framework:
- **Urgency Levels:** `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
- **Escalation Levels:**
  - `L0`: Local Health Worker acknowledgment (60 min timeout)
  - `L1`: Care Coordinator logistical intervention (180 min timeout)
  - `L2`: Remote Clinician teleconsultation review (360 min timeout)
  - `L3`: Emergency Facility Transfer dispatch (30 min timeout)

---

## 5. Phase 3 Status: Synthetic Operational Data

Phase 3 introduces the synthetic operational environment required by the resource-aware engine:

### A. Synthetic Service Registry (`data/services/service_registry.json`)
Catalogues 6 diverse healthcare sites with realistic infrastructural and staffing variations:
- **`SITE-001` (Tertiary Medical Center - Urban):** Comprehensive imaging (Doppler US, CT, MRI), complete medication stock with cold chain, 24/7 on-site specialists, emergency transport, 100 Mbps fiber broadband, English & Tamil staff with multilingual interpreters.
- **`SITE-002` (Village Sub-Center - Rural):** No imaging, basic oral generic stock only, no cold chain, visiting doctor once monthly, no transport, 128 kbps 2G link, Tamil only.
- **`SITE-003` (Community Health Center - Semi-Urban):** Basic X-ray, oral antibiotics and hypoglycemics, no cold chain, general medical officer, shared ambulance, 10 Mbps 4G LTE.
- **`SITE-004` (Primary Health Post - Remote/Island):** Point-of-care ultrasound, solar-backed cold chain, no on-site specialists, no road transport, 50 Mbps satellite uplink, Tamil only.
- **`SITE-005` (Taluk Sub-District Hospital - Taluk):** Radiography, ultrasound, functional cold chain, general surgeon, ambulance transfer to Tertiary, 20 Mbps DSL.
- **`SITE-006` (Urban Dispensary Kiosk - Urban):** No imaging, essential oral medicines, high-speed teleconsultation booth (50 Mbps fiber), commercial transit accessible, English & Tamil.

### B. Why Resource Variation Exists
Standard clinical protocols assume frictionless availability of specialists, tertiary diagnostics, and cold-chain supply. The synthetic operational environment models realistic peripheral constraints to evaluate whether decision-support systems can adapt recommendations rather than issuing unimplementable advice.

### C. Deterministic Synthetic Case Generation (`scripts/generate_cases.py`)
Generates exactly **40 synthetic patient cases** stored in `data/cases/synthetic_cases.json`:
- **Deterministic Reproducibility:** Uses fixed random seed (`seed=42`). Running `python scripts/generate_cases.py` always reproduces the identical dataset.
- **Variation Dimensions:**
  - **Languages:** English (`en`) and Tamil (`ta`)
  - **Population Groups:** `rural` (20 cases) and `urban` (20 cases)
  - **Age Bands:** `18-35`, `36-50`, `51-65`, `65+`
  - **Urgency Levels:** `LOW` (7), `MEDIUM` (17), `HIGH` (8), `CRITICAL` (8)
  - **Conditions:** `condition_alpha` through `condition_epsilon` (8 cases each)
  - **Sites:** Distributed across all 6 synthetic facilities
- **Logical Data Quality:**
  - Cases lacking transport reflect realistic travel delays to next-tier sites.
  - Tamil-speaking patients presenting at English-predominant facilities automatically declare `interpreter_required=true`.
  - Connectivity quality mirrors site telemetry (e.g. 2G sites flag virtual follow-up as constrained).

### D. How to Regenerate Cases
```bash
python scripts/generate_cases.py
```

---

## 6. Phase 4 Status: Resource Constraint Engine

Phase 4 implements the core deterministic decision engine (`src/constraint_engine/`):

### A. Core Architecture & Inputs
The engine compares protocol requirements against:
- Ground-truth site equipment and pharmaceutical stocks
- Patient travel and transportation constraints
- Local network bandwidth and teleconsultation feasibility
- Patient language vs. staff and interpreter availability

### B. Substitution Ladder Decision Flow
Evaluates recommendations strictly in hierarchical order:
1. `preferred`: Gold-standard clinical guidance
2. `resource_adapted_alternative`: Safe adaptation for austere settings
3. `minimum_safe_fallback`: Basic maintenance or stabilization option
4. `escalate_only`: Emergency transfer directive when local care is impossible

The engine selects the **highest feasible option** and **never silently downgrades**.

### C. Safety Invariants & Edge Case Handling
1. **Never Silently Downgrade:** Every blocking resource deficit is recorded with clear rationale.
2. **Registry Conflict Safety:** If conflicting records exist in facility data, the engine applies the **safer clinical assumption** (treats resource as unavailable) and documents the conflict in the reason trail.
3. **Language Barrier Safety:** If patient language cannot be supported by clinicians, on-site staff, or interpreters, the engine triggers `LANGUAGE_ESCALATION_REQUIRED` and refuses unmonitored discharge.
4. **Immediate Escalation on Exhaustion:** If all three local care rungs are blocked by severe resource deficits, the engine emits `decision = "ESCALATE_IMMEDIATELY"`, `feasible = false`, `escalation_required = true`, and mandates assignment of an accountable fallback owner (`fallback_owner_required = true`).

### D. Inspectable Reason Trail
Every evaluation returns an audit trail detailing why each ladder rung was accepted or rejected, enabling transparent clinician sign-off before regimen dispatch.

---

## 4. Technology Stack

- **Backend Framework:** Python 3.11+ / FastAPI
- **Data Validation & Typing:** Pydantic v2
- **Configuration:** YAML (`pyyaml`) with Pydantic runtime validation
- **Database Engine:** SQLite (prepared for structured storage in later phases)
- **Testing Suite:** Pytest, pytest-asyncio, HTTPX
- **Frontend Stack (Phase 2+):** Vanilla HTML, CSS, JavaScript (no complex node builds required)
- **Machine Learning:** None in Phase 1 (deterministic, rule-based architecture)

---

## 5. Installation

### Prerequisites:
- Python 3.11 or higher installed on your system.
- Git (optional, for version control).

### Setup Instructions:
1. Clone or navigate to the repository directory:
   ```bash
   cd resource-aware-care-comparer
   ```

2. (Optional) Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   # On Windows PowerShell:
   .venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## 6. How to Run the Application

### Option A: Using the Runner Script (Recommended)
```bash
python scripts/run_server.py
```

### Option B: Using Uvicorn Directly
```bash
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

### Accessing Endpoints:
- **Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
  - Expected JSON Response: `{"status": "ok"}`
- **Detailed System Introspection:** [http://127.0.0.1:8000/health/detail](http://127.0.0.1:8000/health/detail)
- **Interactive Swagger Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Alternative UI:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 7. How to Run Tests

### Option A: Using the Test Runner Script
```bash
python scripts/run_tests.py
```

### Option B: Using Pytest Directly
```bash
pytest tests/ -v
```

To run only edge case tests:
```bash
pytest tests/edge_cases/ -v
```

---

## 8. Governance & Disclaimers

### Synthetic-Data Policy
```
Synthetic data only — no real patient data.
```
All patient cases, service registries, protocols, and operational records in this prototype are strictly synthetic. No Protected Health Information (PHI) or Personally Identifiable Information (PII) is included or accepted.

### Clinical Sign-Off Policy
```
Decision-support prototype — clinician sign-off required.
```
Outputs from this system are illustrative decision aids intended to highlight resource constraints and logistical options. All clinical care plans require validation and formal authorization by a licensed physician before delivery to any patient or field healthcare worker.
