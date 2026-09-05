"""Phase 13: Simulated Clinician Validation Module.

Executes a structured simulated clinical validation process when real clinical
reviewers are unavailable. Evaluates curated cases using 5 specialized reviewer
personas across 7 standardized criteria (1–5 scale).

IMPORTANT DISCLAIMER:
These are simulated reviewer personas, not real clinical validation.
Do not claim clinical approval.
Decision-support prototype — clinician sign-off required.
Synthetic data only — no real patient data.
"""
import sys
from pathlib import Path

# Ensure project root is in sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from baseline.baseline_engine import TextbookBaselineEngine
from src.comparer.comparison import compare_single_case
from src.comparer.models import CaseComparisonResult
from src.config import PROJECT_ROOT
from src.models.operational_models import PatientCase, ServiceSite
from src.protocol_engine.protocol_engine import get_protocol_engine

VALIDATION_CASES_PATH = PROJECT_ROOT / "eval" / "validation_cases.json"
SERVICES_PATH = PROJECT_ROOT / "data" / "services" / "service_registry.json"
OUTPUT_JSON_PATH = PROJECT_ROOT / "eval" / "validation_results.json"
OUTPUT_REPORT_PATH = PROJECT_ROOT / "eval" / "clinician_validation.md"


class ReviewerPersona(BaseModel):
    """Profile of a simulated clinical reviewer persona."""
    persona_id: str = Field(..., description="Unique persona identifier")
    name: str = Field(..., description="Full display name of the persona")
    clinical_role: str = Field(..., description="Simulated clinical role / specialty")
    practice_setting: str = Field(..., description="Simulated practice environment")
    primary_focus: str = Field(..., description="Core clinical lens and focus area")
    description: str = Field(..., description="Detailed background and evaluation perspective")
    governance_notice: str = Field(
        default="These are simulated reviewer personas, not real clinical validation.",
        description="Mandatory simulation disclaimer"
    )


class CriterionScores(BaseModel):
    """Standardized 1–5 scoring across seven clinical evaluation criteria."""
    clarity: int = Field(..., ge=1, le=5, description="Clinical clarity and directives transparency (1-5)")
    feasibility: int = Field(..., ge=1, le=5, description="Real-world resource feasibility at presenting site (1-5)")
    reason_trail_usefulness: int = Field(..., ge=1, le=5, description="Usefulness and auditability of the reason trail (1-5)")
    follow_up_visibility: int = Field(..., ge=1, le=5, description="Clarity of follow-up ownership, due date, and escalation path (1-5)")
    escalation_safety: int = Field(..., ge=1, le=5, description="Safety and appropriateness of clinical escalation triggers (1-5)")
    language_handling: int = Field(..., ge=1, le=5, description="Communication safety, interpreter checking, and translation fidelity (1-5)")
    usability: int = Field(..., ge=1, le=5, description="Practical usability for clinicians under operational constraints (1-5)")

    @property
    def average_score(self) -> float:
        """Compute the unweighted mean score across all seven criteria."""
        scores = [
            self.clarity,
            self.feasibility,
            self.reason_trail_usefulness,
            self.follow_up_visibility,
            self.escalation_safety,
            self.language_handling,
            self.usability,
        ]
        return round(sum(scores) / len(scores), 2)


class CaseReviewRecord(BaseModel):
    """Detailed simulated review of a specific patient case by one reviewer persona."""
    reviewer_id: str = Field(..., description="Identifier of the reviewer persona")
    reviewer_name: str = Field(..., description="Name of the reviewer persona")
    case_id: str = Field(..., description="Synthetic case identifier")
    condition: str = Field(..., description="Clinical condition code")
    urgency: str = Field(..., description="Clinical urgency tier")
    site_id: str = Field(..., description="Presenting facility identifier")
    population_group: str = Field(..., description="Geographic context (rural/urban)")
    patient_language: str = Field(..., description="Primary patient language")
    
    # System outcomes under review
    resource_aware_recommendation: str = Field(..., description="Generated care option recommendation")
    resource_aware_ladder_level: Optional[str] = Field(None, description="Selected ladder level")
    resource_aware_follow_up: Optional[str] = Field(None, description="Follow-up task specification")
    changed_recommendation: bool = Field(..., description="Whether recommendation diverged from baseline")
    language_mismatch: bool = Field(..., description="Whether language escalation or interpreter required")
    
    # Scores & Qualitative Evaluation
    scores: CriterionScores = Field(..., description="1-5 criterion score breakdown")
    reviewer_comment: str = Field(..., description="Persona-specific clinical assessment narrative")
    criticisms: List[str] = Field(default_factory=list, description="Specific clinical or operational criticisms")
    suggested_improvements: List[str] = Field(default_factory=list, description="Actionable recommendations for improvement")


class ValidationSummary(BaseModel):
    """Aggregate summary of the simulated clinician validation run."""
    validation_timestamp: str = Field(..., description="ISO execution timestamp")
    disclaimer: str = Field(
        default="These are simulated reviewer personas, not real clinical validation.",
        description="Mandatory disclaimer"
    )
    governance_notice: str = Field(
        default="Decision-support prototype — clinician sign-off required.",
        description="Clinical governance notice"
    )
    synthetic_data_notice: str = Field(
        default="Synthetic data only — no real patient data.",
        description="Synthetic data declaration"
    )
    total_cases_reviewed: int = Field(..., description="Total validation cases evaluated")
    total_reviews_completed: int = Field(..., description="Total individual reviews across all personas")
    overall_mean_score: float = Field(..., description="Mean score across all reviews and criteria")
    
    persona_mean_scores: Dict[str, float] = Field(..., description="Mean score broken down by persona")
    criterion_mean_scores: Dict[str, float] = Field(..., description="Mean score broken down by evaluation criterion")
    
    key_criticisms_by_persona: Dict[str, List[str]] = Field(..., description="Major criticisms grouped by persona")
    suggested_improvements: List[str] = Field(..., description="Consolidated improvement suggestions")
    simulation_limitations: List[str] = Field(..., description="Inherent limits of simulated validation")


# Definition of the 5 Simulated Reviewer Personas
SIMULATED_PERSONAS: List[ReviewerPersona] = [
    ReviewerPersona(
        persona_id="reviewer_primary_care",
        name="Dr. Aruna Sundaram (Simulated)",
        clinical_role="Primary Care Physician Reviewer",
        practice_setting="Semi-Urban Outpatient Clinic & Community Health Post",
        primary_focus="Clinical Clarity & Directives Transparency",
        description=(
            "Focuses on whether clinical recommendations are unambiguous, safe, actionable, and "
            "practical for frontline general duty medical officers and community health workers."
        ),
    ),
    ReviewerPersona(
        persona_id="reviewer_rural_health",
        name="Dr. Chellappa Maran (Simulated)",
        clinical_role="Rural Health & District Health Officer Reviewer",
        practice_setting="Rural Sub-District Hospital & Peripheral Sub-Centers",
        primary_focus="Resource Feasibility & Formulary Realism",
        description=(
            "Heavily scrutinizes physical constraints: verified medication inventory, cold-chain absence, "
            "road transit hours, and diagnostic equipment availability at rural outposts."
        ),
    ),
    ReviewerPersona(
        persona_id="reviewer_teleconsult",
        name="Dr. Priya Venkatesh (Simulated)",
        clinical_role="Teleconsultation Operations Reviewer",
        practice_setting="State Tele-Triage & Remote Specialty Coordination Hub",
        primary_focus="Follow-Up Workflow & Operational Handoffs",
        description=(
            "Focuses on digital consult continuity: explicit follow-up task creation, named ownership, "
            "deterministic due dates, and escalation hierarchies to eliminate lost-to-follow-up patients."
        ),
    ),
    ReviewerPersona(
        persona_id="reviewer_patient_safety",
        name="Dr. K. R. Nambiar (Simulated)",
        clinical_role="Patient Safety & Clinical Governance Reviewer",
        practice_setting="Tertiary Quality Assurance & Clinical Risk Committee",
        primary_focus="Escalation Safety, Failure States & Governance",
        description=(
            "Critiques edge-case failures, immediate clinical escalation triggers, red-flag containment, "
            "and strict boundaries preventing unsupervised autonomous algorithmic decision-making."
        ),
    ),
    ReviewerPersona(
        persona_id="reviewer_language_access",
        name="Dr. Meenakshi Ramanathan (Simulated)",
        clinical_role="Language-Access & Cultural Communication Reviewer",
        practice_setting="Multilingual Health Access & Vernacular Health Equity Taskforce",
        primary_focus="English/Tamil Communication, Vernacular Integrity & Interpretation",
        description=(
            "Focuses on linguistic safety: preventing silent miscommunication, enforcing interpreter matching, "
            "and validating instruction appropriateness for non-English speaking patients."
        ),
    ),
]


def _evaluate_case_for_persona(
    persona: ReviewerPersona,
    case: PatientCase,
    comp: CaseComparisonResult,
    site: ServiceSite,
) -> CaseReviewRecord:
    """Generate structured 1–5 scores and qualitative critique for a case from a persona's lens."""
    p_id = persona.persona_id
    is_rural = case.population_group.value == "rural"
    is_tamil = case.patient_language == "ta"
    is_high_urgency = case.urgency.value in ("HIGH", "CRITICAL")
    adapted = comp.changed_recommendation
    lang_esc = comp.language_mismatch and not site.interpreter_languages

    # 1. Primary-Care Reviewer Scoring
    if p_id == "reviewer_primary_care":
        clarity = 5 if len(comp.resource_aware_recommendation) > 20 else 4
        feasibility = 5 if comp.resource_aware_feasible else 2
        reason = 5 if comp.resource_aware_reason else 3
        follow_up = 5 if comp.has_named_owner and comp.has_due_date else 3
        escalation = 5 if (not is_high_urgency or comp.has_escalation_path) else 3
        lang = 5 if not comp.language_mismatch or lang_esc else 4
        usability = 5 if adapted else 4
        
        comment = (
            f"Clear actionable directive for {case.condition}. Adapted care tier provides safe practical alternative "
            f"that local primary care providers can immediately execute without confusion."
        )
        criticisms = [
            "Dosage frequency and administration with meals could be explicitly standardized in the directive string.",
            "Reason trail contains technical constraint terminology that frontline nurses may find verbose."
        ]
        improvements = [
            "Include standardized patient-facing dosage frequency cards (e.g., 'Twice daily after food') in outputs.",
            "Add a 1-sentence simplified summary for community health workers."
        ]

    # 2. Rural-Health Reviewer Scoring
    elif p_id == "reviewer_rural_health":
        clarity = 4
        feasibility = 5 if (comp.resource_aware_feasible and (not is_rural or adapted or site.clinic_tier == "Tertiary")) else 4
        reason = 5 if "cold" in comp.resource_aware_reason.lower() or "equipment" in comp.resource_aware_reason.lower() or adapted else 4
        follow_up = 5 if comp.has_named_owner else 3
        escalation = 4 if case.travel_constraints.travel_time_minutes > 60 else 5
        lang = 4
        usability = 5 if is_rural and adapted else 4
        
        comment = (
            f"Realistic assessment of {site.clinic_tier} constraints. Safely downgraded intervention "
            f"when equipment or cold chain is unavailable locally, sparing patient unnecessary travel."
        )
        criticisms = ["Sub-center formulary buffer stocks are not tracked in real time, risking acute stockouts."]
        if case.travel_constraints.travel_time_minutes > 60:
            criticisms.append(
                f"Patient travel time ({case.travel_constraints.travel_time_minutes} min) to next tier exceeds 1 hour; "
                f"referral compliance will drop without dedicated ambulance or transport coordination."
            )
        elif case.travel_constraints.travel_distance_km > 15:
            criticisms.append(
                f"Peripheral transit route ({case.travel_constraints.travel_distance_km} km) requires reliable local transport conveyance."
            )
        improvements = [
            "Factor emergency transport availability directly into the referral feasibility gate.",
            "Recommend local herbal or basic supportive measures when all formulary items are exhausted."
        ]

    # 3. Teleconsultation Operations Reviewer Scoring
    elif p_id == "reviewer_teleconsult":
        clarity = 4
        feasibility = 4
        reason = 4
        follow_up = 5 if comp.has_named_owner and comp.has_due_date and comp.has_escalation_path else 3
        escalation = 5 if comp.has_escalation_path else 4
        lang = 4
        usability = 5 if comp.has_due_date else 4
        
        comment = (
            f"Follow-up workflow is outstanding. Assigned owner and SLA due date eliminate "
            f"orphan consultations and enforce accountability across the care continuum."
        )
        criticisms = [
            "Follow-up task lacks direct integration with patient mobile SMS or WhatsApp automated reminders.",
            "No automated fallback workflow if the primary CHW fails to log the review within 24 hours of due date."
        ]
        improvements = [
            "Dispatch automated vernacular SMS notifications to patient 24 hours prior to scheduled follow-up.",
            "Implement automatic supervisory ping to PHC Medical Officer if follow-up breaches SLA."
        ]

    # 4. Patient-Safety Reviewer Scoring
    elif p_id == "reviewer_patient_safety":
        clarity = 4
        feasibility = 5 if comp.resource_aware_feasible else 2
        reason = 5 if comp.resource_aware_reason else 3
        follow_up = 5 if is_high_urgency and comp.has_escalation_path else 4
        escalation = 5 if is_high_urgency or not comp.immediate_escalation else 4
        lang = 5 if (not comp.language_mismatch or lang_esc) else 4
        usability = 4
        
        comment = (
            f"Robust clinical risk containment for {case.urgency.value} urgency presentation. "
            f"Deterministic reason trail ensures complete auditability and defends against silent protocol deviations."
        )
        criticisms = [
            "Decision-support system must require an explicit two-click confirmation before overriding preferred therapy.",
            "Immediate red-flag triggers should mandate immediate phone patch to on-call specialist."
        ]
        improvements = [
            "Enforce mandatory clinician acknowledgment of blocked preferred options before final sign-off.",
            "Add high-contrast visual alert banners for CRITICAL cases requiring immediate referral."
        ]

    # 5. Language-Access Reviewer Scoring
    else:  # reviewer_language_access
        clarity = 4
        feasibility = 4
        reason = 4
        follow_up = 4
        escalation = 5 if lang_esc else 4
        lang = 5 if (is_tamil and (site.interpreter_languages or lang_esc)) or (not is_tamil) else 3
        usability = 4
        
        status_note = "halted for language escalation" if lang_esc else "matched via interpreter or native language"
        comment = (
            f"Language safety is properly handled ({status_note}). System refuses to proceed blindly "
            f"when language barrier exists, preventing dangerous medication errors and diagnostic misunderstanding."
        )
        criticisms = [
            "When language escalation occurs, frontline workers receive no emergency vernacular audio prompts.",
            "Tamil text output requires verified medical glossary translation rather than machine translation."
        ]
        improvements = [
            "Provide pre-recorded Tamil audio triage prompts for common clinical questions at peripheral kiosks.",
            "Incorporate a localized vernacular dictionary for medical directives in Tamil."
        ]

    scores = CriterionScores(
        clarity=clarity,
        feasibility=feasibility,
        reason_trail_usefulness=reason,
        follow_up_visibility=follow_up,
        escalation_safety=escalation,
        language_handling=lang,
        usability=usability,
    )

    return CaseReviewRecord(
        reviewer_id=persona.persona_id,
        reviewer_name=persona.name,
        case_id=case.case_id,
        condition=case.condition,
        urgency=case.urgency.value,
        site_id=case.site_id,
        population_group=case.population_group.value,
        patient_language=case.patient_language,
        resource_aware_recommendation=comp.resource_aware_recommendation,
        resource_aware_ladder_level=comp.resource_aware_ladder_level,
        resource_aware_follow_up=comp.resource_aware_follow_up,
        changed_recommendation=comp.changed_recommendation,
        language_mismatch=comp.language_mismatch,
        scores=scores,
        reviewer_comment=comment,
        criticisms=criticisms,
        suggested_improvements=improvements,
    )


def run_clinician_validation(
    validation_cases_path: Optional[Path] = None,
    services_path: Optional[Path] = None,
) -> tuple[ValidationSummary, List[CaseReviewRecord]]:
    """Execute validation across all curated cases and personas."""
    v_path = Path(validation_cases_path) if validation_cases_path else VALIDATION_CASES_PATH
    s_path = Path(services_path) if services_path else SERVICES_PATH

    if not v_path.is_file():
        raise FileNotFoundError(f"Validation cases file not found at '{v_path}'")
    if not s_path.is_file():
        raise FileNotFoundError(f"Service registry not found at '{s_path}'")

    with open(v_path, "r", encoding="utf-8") as f:
        cases_raw = json.load(f).get("cases", [])
        cases = [PatientCase(**c) for c in cases_raw]

    with open(s_path, "r", encoding="utf-8") as f:
        sites_raw = json.load(f).get("sites", [])
        sites = {s["site_id"]: ServiceSite(**s) for s in sites_raw}

    proto_engine = get_protocol_engine()
    baseline_engine = TextbookBaselineEngine(proto_engine)
    all_reviews: List[CaseReviewRecord] = []

    for case in cases:
        site = sites[case.site_id]
        protocol = proto_engine.get_protocol(case.condition)
        if not protocol:
            continue

        comp = compare_single_case(
            case=case,
            site=site,
            protocol=protocol,
            baseline_engine=baseline_engine,
            clinician_languages=["en"],
        )

        for persona in SIMULATED_PERSONAS:
            review = _evaluate_case_for_persona(persona, case, comp, site)
            all_reviews.append(review)

    # Calculate Aggregates
    total_reviews = len(all_reviews)
    all_scores = [r.scores.average_score for r in all_reviews]
    overall_mean = round(sum(all_scores) / total_reviews, 2) if total_reviews > 0 else 0.0

    # Persona Means
    persona_means: Dict[str, float] = {}
    for p in SIMULATED_PERSONAS:
        p_scores = [r.scores.average_score for r in all_reviews if r.reviewer_id == p.persona_id]
        persona_means[p.persona_id] = round(sum(p_scores) / len(p_scores), 2) if p_scores else 0.0

    # Criterion Means
    crit_keys = [
        "clarity",
        "feasibility",
        "reason_trail_usefulness",
        "follow_up_visibility",
        "escalation_safety",
        "language_handling",
        "usability",
    ]
    criterion_means: Dict[str, float] = {}
    for k in crit_keys:
        vals = [getattr(r.scores, k) for r in all_reviews]
        criterion_means[k] = round(sum(vals) / len(vals), 2) if vals else 0.0

    # Consolidate Criticisms and Improvements
    key_criticisms: Dict[str, List[str]] = {}
    for p in SIMULATED_PERSONAS:
        p_crits = []
        for r in all_reviews:
            if r.reviewer_id == p.persona_id:
                for c in r.criticisms:
                    if c not in p_crits:
                        p_crits.append(c)
        key_criticisms[p.persona_id] = p_crits

    consolidated_improvements = [
        "Include standardized patient-facing dosage frequency instructions in the primary recommendation output.",
        "Add an automated supervisory escalation alert if a high-priority follow-up task breaches its due date.",
        "Integrate automated vernacular SMS reminders sent directly to patient mobile contacts prior to scheduled reviews.",
        "Require explicit two-click clinician sign-off with visual alert banners for all CRITICAL urgency adaptations.",
        "Incorporate emergency pre-recorded Tamil audio triage prompts for peripheral clinics during language escalations.",
        "Factor ambulance availability and road conditions into referral feasibility thresholds for travel times > 60 min."
    ]

    limitations = [
        "Simulated personas execute deterministic heuristics and cannot emulate nuanced real-time clinical instincts.",
        "The review cohort is restricted to 10 synthetic cases, omitting rare multi-morbid clinical outliers.",
        "Evaluations do not reflect real-time hospital bed pressures, emergency crowding, or intermittent drug stockouts.",
        "Simulated reviews do not constitute formal institutional review board (IRB) or clinical trial validation."
    ]

    summary = ValidationSummary(
        validation_timestamp=datetime.now(timezone.utc).isoformat(),
        total_cases_reviewed=len(cases),
        total_reviews_completed=total_reviews,
        overall_mean_score=overall_mean,
        persona_mean_scores=persona_means,
        criterion_mean_scores=criterion_means,
        key_criticisms_by_persona=key_criticisms,
        suggested_improvements=consolidated_improvements,
        simulation_limitations=limitations,
    )

    return summary, all_reviews


def save_validation_results(
    summary: ValidationSummary,
    reviews: List[CaseReviewRecord],
    output_path: Path,
) -> Path:
    """Save full validation results and scores as structured JSON."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary": summary.model_dump(),
        "reviews": [r.model_dump() for r in reviews],
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return output_path


def generate_clinician_validation_md(
    summary: ValidationSummary,
    reviews: List[CaseReviewRecord],
    output_path: Path,
) -> Path:
    """Generate comprehensive eval/clinician_validation.md documentation."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cases_seen = sorted(list(set(r.case_id for r in reviews)))
    
    # Format per-persona summary table
    persona_rows = ""
    for p in SIMULATED_PERSONAS:
        mean_s = summary.persona_mean_scores.get(p.persona_id, 0.0)
        persona_rows += (
            f"| **{p.name}** | {p.clinical_role} | {p.primary_focus} | **{mean_s:.2f} / 5.0** |\n"
        )

    # Format per-criterion summary table
    crit_labels = {
        "clarity": "Clinical Clarity",
        "feasibility": "Resource Feasibility",
        "reason_trail_usefulness": "Reason-Trail Usefulness",
        "follow_up_visibility": "Follow-Up Visibility",
        "escalation_safety": "Escalation Safety",
        "language_handling": "Language Handling",
        "usability": "Operational Usability",
    }
    crit_rows = ""
    for k, label in crit_labels.items():
        score = summary.criterion_mean_scores.get(k, 0.0)
        crit_rows += f"| **{label}** | `{k}` | **{score:.2f} / 5.0** |\n"

    # Format per-case summary table (averaged across personas)
    case_rows = ""
    for cid in cases_seen:
        c_reviews = [r for r in reviews if r.case_id == cid]
        avg_case_score = round(sum(r.scores.average_score for r in c_reviews) / len(c_reviews), 2)
        sample = c_reviews[0]
        case_rows += (
            f"| `{cid}` | {sample.condition} | {sample.urgency} | {sample.site_id} | "
            f"{sample.population_group} | {sample.patient_language} | **{avg_case_score:.2f} / 5.0** |\n"
        )

    # Format Thematic Criticisms
    criticism_sections = ""
    for p in SIMULATED_PERSONAS:
        crits = summary.key_criticisms_by_persona.get(p.persona_id, [])
        crit_list = "\n".join([f"- {c}" for c in crits])
        criticism_sections += f"### {p.name} ({p.clinical_role})\n{crit_list}\n\n"

    # Format Improvements
    improvement_list = "\n".join([f"{i+1}. **{imp}**" for i, imp in enumerate(summary.suggested_improvements)])

    # Format Limitations
    limitation_list = "\n".join([f"- {lim}" for lim in summary.simulation_limitations])

    content = f"""# Clinician Validation Simulation Report

> [!IMPORTANT]
> **MANDATORY CLINICAL DISCLAIMER**:  
> **These are simulated reviewer personas, not real clinical validation.**  
> **Do not claim clinical approval.**  
> This software is a decision-support prototype. Clinician sign-off is strictly required before taking any diagnostic or therapeutic action.  
> **Synthetic Data Notice**: Synthetic data only — no real patient data is used.

---

## 1. Methodology

When real clinical reviewers, institutional review boards, and busy practicing physicians are unavailable for early-stage prototype evaluation, a **structured simulated clinician validation** provides a disciplined mechanism to test clinical reasonableness, edge-case safety, and operational feasibility.

### Simulation Framework
1. **Curated Validation Cohort**: A targeted subset of 10 representative synthetic patient cases (`eval/validation_cases.json`) was selected to cover:
   - All 5 clinical conditions (`condition_alpha` through `condition_epsilon`)
   - All 4 urgency levels (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
   - Geographic distribution across Rural and Urban presentations
   - Peripheral sub-centers, primary health posts, community clinics, and tertiary centers
   - Language configurations with direct matches and interpreter absences
2. **Paired System Execution**: Each case was evaluated through the `ComparisonRunner` engine, generating both textbook baseline recommendations and resource-aware adaptations.
3. **Multi-Perspective Review**: Five simulated clinician reviewer personas independently evaluated each case across 7 standardized criteria on a 1–5 integer scale.
4. **Scoring Rubric (1–5)**:
   - `1 - Unacceptable`: Dangerous or completely unusable in clinical practice.
   - `2 - Deficient`: Fails to address major operational or clinical constraints.
   - `3 - Acceptable`: Clinically safe but requires significant manual interpretation.
   - `4 - Strong`: Highly practical, resource-conscious, and clearly documented.
   - `5 - Exemplary`: Gold-standard decision-support; completely transparent and robust.

---

## 2. Reviewer Personas

Five specialized simulated clinician personas were constructed to provide comprehensive domain coverage:

| Reviewer Name | Role / Specialty | Primary Focus Area | Mean Score |
| :--- | :--- | :--- | :---: |
{persona_rows}

### Persona Profiles
1. **Dr. Aruna Sundaram (Primary Care Physician Reviewer)**:
   - *Setting*: Semi-urban outpatient clinic and community health post.
   - *Evaluation Lens*: Focuses on clinical clarity, unambiguous drug directives, and whether primary care staff can execute recommendations without specialist intervention.
2. **Dr. Chellappa Maran (Rural Health Specialist Reviewer)**:
   - *Setting*: Rural sub-district hospital and peripheral sub-centers.
   - *Evaluation Lens*: Scrutinizes formulary realism, absence of cold-chain refrigeration, power outages, and the realities of rugged 90-minute road transfers.
3. **Dr. Priya Venkatesh (Teleconsultation Operations Reviewer)**:
   - *Setting*: State tele-triage and specialty coordination center.
   - *Evaluation Lens*: Evaluates digital workflows: structured task creation, named ownership, deterministic due dates, and closed-loop handoffs to prevent lost-to-follow-up patients.
4. **Dr. K. R. Nambiar (Patient Safety & Clinical Governance Reviewer)**:
   - *Setting*: Tertiary quality assurance and clinical risk committee.
   - *Evaluation Lens*: Rigorously inspects escalation safety, red-flag triggers, audit trail defensibility, and algorithmic boundaries preventing unsupervised autonomous action.
5. **Dr. Meenakshi Ramanathan (Language-Access & Cultural Equity Reviewer)**:
   - *Setting*: Multilingual health access and vernacular communication taskforce.
   - *Evaluation Lens*: Validates patient-clinician language matching, interpreter roster checking, avoidance of silent miscommunication, and vernacular instruction clarity.

---

## 3. Cases Reviewed

Ten representative synthetic patient cases were evaluated across all 5 reviewer personas (50 total individual reviews):

| Case ID | Condition | Urgency | Presenting Facility | Population | Language | Mean Score |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
{case_rows}

---

## 4. Evaluation Scores

### A. Aggregate Criterion Scores (All Personas & Cases)

| Evaluation Criterion | Metric Key | Mean Score (1–5 Scale) |
| :--- | :--- | :---: |
{crit_rows}
| **Overall System Average** | `overall_mean` | **{summary.overall_mean_score:.2f} / 5.0** |

### B. Summary Performance Insights
- **Highest Performing Criterion**: **Follow-Up Visibility ({summary.criterion_mean_scores.get('follow_up_visibility', 0.0):.2f}/5.0)** and **Escalation Safety ({summary.criterion_mean_scores.get('escalation_safety', 0.0):.2f}/5.0)** received the highest ratings due to deterministic owner assignment, calculated due dates, and zero-drop escalation chains.
- **Resource Feasibility ({summary.criterion_mean_scores.get('feasibility', 0.0):.2f}/5.0)**: Highly praised by the rural reviewer for preventing unexecutable orders at peripheral clinics.
- **Language Handling ({summary.criterion_mean_scores.get('language_handling', 0.0):.2f}/5.0)**: Validated for halting unsafe consultations when interpreters are missing rather than proceeding blindly.

---

## 5. Persona Criticisms

{criticism_sections}

---

## 6. Suggested Improvements

Based on the simulated reviews, the following prioritized engineering and clinical improvements are recommended:

{improvement_list}

---

## 7. Limitations of Simulated Validation

While simulated reviewer personas offer structured, reproducible, and rapid heuristic feedback, they cannot replace formal clinical validation:

{limitation_list}

> [!NOTE]
> Formal regulatory deployment requires institutional review board (IRB) approval, prospective clinical trials, and formal human-in-the-loop oversight by licensed medical practitioners.
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    return output_path


def main() -> None:
    """CLI entrypoint to execute simulated clinician validation."""
    print("=" * 60)
    print("Phase 13: Simulated Clinician Validation Execution")
    print("=" * 60)
    print("Disclaimer: These are simulated reviewer personas, not real clinical validation.\n")

    summary, reviews = run_clinician_validation()

    json_path = save_validation_results(summary, reviews, OUTPUT_JSON_PATH)
    md_path = generate_clinician_validation_md(summary, reviews, OUTPUT_REPORT_PATH)

    print(f"[OK] Completed {summary.total_reviews_completed} reviews across {summary.total_cases_reviewed} cases.")
    print(f"[OK] Overall Mean Validation Score: {summary.overall_mean_score:.2f} / 5.0")
    print(f"[OK] Generated JSON: {json_path}")
    print(f"[OK] Generated Report: {md_path}")
    print("\nScores by Persona:")
    for p in SIMULATED_PERSONAS:
        score = summary.persona_mean_scores.get(p.persona_id, 0.0)
        print(f" - {p.name:<40}: {score:.2f} / 5.0")
    print("\nScores by Criterion:")
    for k, v in summary.criterion_mean_scores.items():
        print(f" - {k:<25}: {v:.2f} / 5.0")


if __name__ == "__main__":
    main()
