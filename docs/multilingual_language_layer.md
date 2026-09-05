# Multilingual Language Layer Specification (English & Tamil)

> [!CAUTION]
> **CLINICAL DECISION-SUPPORT & SYNTHETIC DATA NOTICE**
> - **Decision-support prototype — clinician sign-off required.**
> - **Synthetic data only — no real patient data.**
> - All cases, facility registries, protocols, and operational records described herein are synthetic.

---

## 1. Executive Summary & Problem Statement

In distributed teleconsultation and peripheral clinical triage, linguistic discordance between patients, local field workers, and remote clinicians is a primary driver of misdiagnosis, non-adherence, and preventable deterioration. When care options are presented without confirming safe verbal and written comprehension, health systems experience **silent communication failures**.

The **Multilingual Language Layer** (`src/language/`) introduces deterministic language resolution, human-curated message catalogs in English (`en`) and Tamil (`ta`), presentation-layer reason trail localization, and a strict safety gate that prohibits silent clinical delivery when language communication cannot be supported.

---

## 2. Supported Languages

| Code | Name | Native Script | Direction | Default | Target Audience |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `en` | English | English | LTR | Yes | Primary clinical, administrative, and supervision teams |
| `ta` | Tamil | தமிழ் | LTR | No | Patients, ASHA/Local Health Workers, and rural clinics |

*No external or automatic translation APIs are used. All translations are human-curated and deterministically mapped.*

---

## 3. Architecture & Data Flow

```
                     ┌──────────────────────────────────────────────┐
                     │          PATIENT CASE / REQUEST              │
                     │  (patient_language, preferred_language)      │
                     └──────────────────────┬───────────────────────┘
                                            │
                                            ▼
                     ┌──────────────────────────────────────────────┐
                     │          LANGUAGE RESOLUTION ENGINE          │
                     │          (src/language/resolver.py)          │
                     │                                              │
                     │  1. Clinician Speaks Language?               │
                     │     - Yes ──► SUPPORTED                      │
                     │  2. Certified Interpreter Available?         │
                     │     - Yes ──► REQUIRES_INTERPRETER           │
                     │  3. Neither Available?                       │
                     │     - ──────► LANGUAGE_ESCALATION_REQUIRED   │
                     └──────────────────────┬───────────────────────┘
                                            │
                       ┌────────────────────┴────────────────────┐
                       │                                         │
                       ▼                                         ▼
        ┌─────────────────────────────┐           ┌─────────────────────────────┐
        │   MESSAGE CATALOGS          │           │   REASON TRAIL TRANSLATOR   │
        │   (data/languages/en.json)  │           │   (src/language/            │
        │   (data/languages/ta.json)  │           │    translator.py)           │
        │                             │           │                             │
        │ - UI Labels & Notifications │           │ - Presentation-layer        │
        │ - Disclaimers in EN / TA    │           │   translation for Reason    │
        │ - Severity & Ladder terms   │           │   Trails into English & TA  │
        └──────────────┬──────────────┘           └──────────────┬──────────────┘
                       │                                         │
                       └────────────────────┬────────────────────┘
                                            │
                                            ▼
        ┌───────────────────────────────────────────────────────────────────────┐
        │                         API & UI CONSUMPTION                          │
        │  - GET /languages: Catalog metadata                                  │
        │  - GET /languages/{code}/messages: Full dictionary for code           │
        │  - POST /evaluate: Multilingual care option comparison                │
        │  - UI: Interactive Language Selector (English / தமிழ்)                │
        │  - Safety Gate: Block silent display on LANGUAGE_ESCALATION_REQUIRED  │
        └───────────────────────────────────────────────────────────────────────┘
```

---

## 4. Language Resolution Algorithm (`resolver.py`)

The language resolver evaluates compatibility strictly via three deterministic rules:

1. **Rule 1 — Direct Provider Support:**
   If the patient's primary (or preferred) language is in the clinician's spoken languages:
   $$\text{status} = \mathbf{SUPPORTED}$$
   $$\text{selected\_language} = \text{target\_language}$$

2. **Rule 2 — Interpreter Requirement:**
   If the clinician does not speak the language, but an on-duty interpreter is available who speaks the patient's language:
   $$\text{status} = \mathbf{REQUIRES\_INTERPRETER}$$
   $$\text{selected\_language} = \text{target\_language}$$

3. **Rule 3 — Language Escalation Required:**
   If neither clinician nor interpreter speaks the patient's language, or if an interpreter is required but unavailable:
   $$\text{status} = \mathbf{LANGUAGE\_ESCALATION\_REQUIRED}$$
   $$\text{selected\_language} = \text{None}$$

---

## 5. Communication Safety Invariant

> [!IMPORTANT]
> **THE SILENT COMMUNICATION PREVENTION RULE**
> If:
> $$\text{patient\_language} \neq \text{supported\_language} \quad \text{AND} \quad \text{interpreter\_available} == \text{False}$$
> Then:
> **The system NEVER silently displays the clinical recommendation as if communication were safe.**
>
> Instead, it:
> 1. Triggers `LANGUAGE_ESCALATION_REQUIRED`.
> 2. Displays the critical alert banner: `LANGUAGE ESCALATION REQUIRED / மொழி அதிகரிப்பு தேவை`.
> 3. Refuses treatment discharge until a qualified human interpreter or language-competent clinician is assigned.

---

## 6. Reason Trail Localization (`translator.py`)

While internal machine-readable codes and protocol identifiers remain in standard English, presentation reason trails are translated into natural, authentic Tamil when requested:

| Context | English Display | Tamil Display |
| :--- | :--- | :--- |
| **Specialist Deficit** | Preferred option blocked because specialist is unavailable. | நிபுணர் கிடைக்காததால் விருப்பமான சிகிச்சைத் தேர்வு பயன்படுத்த முடியாது. |
| **Transport Deficit** | Resource-adapted alternative blocked because transport is unavailable. | போக்குவரத்து வசதி இல்லாததால் வள-தழுவிய மாற்று சிகிச்சை பயன்படுத்த முடியாது. |
| **Feasible Assessment** | Evaluated 'Preferred': FEASIBLE. All required resources and constraints are satisfied. | மதிப்பீடு 'விருப்பமான சிகிச்சைத் தேர்வு': சாத்தியமானது. தேவையான அனைத்து வளங்களும் நிபந்தனைகளும் பூர்த்தி செய்யப்பட்டுள்ளன. |
| **Direct Language Support** | Language Safety: Patient language 'ta' is directly supported without translation barriers. | மொழி பாதுகாப்பு: நோயாளியின் மொழி 'ta' மொழிபெயர்ப்பு தடைகள் இன்றி நேரடியாக ஆதரிக்கப்படுகிறது. |
| **Language Escalation** | Language Safety ALERT: Patient language 'kn' is unsupported by available clinicians and interpreters. Language escalation triggered. | மொழி பாதுகாப்பு எச்சரிக்கை: நோயாளியின் மொழி 'kn' மருத்துவர் அல்லது மொழிபெயர்ப்பாளரால் ஆதரிக்கப்படவில்லை. மொழி அதிகரிப்பு தொடங்கப்பட்டது. |
| **Immediate Escalation** | FINAL DECISION: ESCALATE_IMMEDIATELY. All local treatment rungs are infeasible. | இறுதி முடிவு: உடனடியாக அவசர மேலனுப்பல் செய்க. உள்ளூர் சிகிச்சை முறைகள் எதுவும் சாத்தியமில்லை. |

---

## 7. REST API Endpoints

| Method | Path | Summary | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/languages` | Supported Languages | Returns supported language metadata (`en`, `ta`) |
| `GET` | `/languages/{code}/messages` | Message Dictionary | Returns flat key-value translation catalog (`404` for unsupported codes) |
| `POST`| `/evaluate` | Localized Evaluation | Evaluates case constraints with localized reason trails and language safety overlay |
| `GET` | `/cases` | Synthetic Case Catalog | Returns synthetic cases for UI dropdown and testing |

---

## 8. Web User Interface (`/ui`)

The web dashboard is served directly at `/ui` and features:
- **Interactive Language Toggle:** Switch between `English` and `தமிழ்` in real time.
- **Dynamic Catalog Translation:** Translates UI labels, status descriptions, disclaimers, and reason trails.
- **Visual Safety Gate:** When a patient case triggers `LANGUAGE_ESCALATION_REQUIRED`, the UI displays a glowing crimson alert banner and prevents treatment confirmation.
- **Care Option Comparison:** Side-by-side display of Textbook Baseline vs. Resource-Aware Recommendation.
- **Live Follow-Up Tracking:** Displays SQLite-persisted follow-up tasks with completion actions.

---

## 9. Operational Limitations

1. **Dialectal Variation:** While standard formal Tamil (`ta_IN`) is supported, hyper-localized rural colloquialisms or slang are not dynamically parsed.
2. **Deterministic Catalog Scope:** Dictionaries cover teleconsultation clinical, operational, and reason-trail phrases. Dynamic free-text notes outside catalog patterns fall back to structured English terms.
3. **Clinical Sign-Off Invariant:** Even when communication is directly supported in Tamil or English, all recommendations require explicit clinician sign-off.
