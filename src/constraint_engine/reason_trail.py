"""Reason trail builder generating human-readable clinical and logistical explanations.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from typing import Dict, List, Optional
from src.constraint_engine.models import LanguageEvaluation, LanguageStatus, OptionEvaluation


class ReasonTrailBuilder:
    """Constructs an inspectable, chronological reason trail for decision-support transparency."""

    def __init__(self) -> None:
        self._trail: List[str] = []

    def add_step(self, message: str) -> None:
        """Append a step or evaluation checkpoint to the trail."""
        self._trail.append(message)

    def log_language_evaluation(self, lang_eval: LanguageEvaluation) -> None:
        """Record the linguistic safety evaluation."""
        if lang_eval.status == LanguageStatus.SUPPORTED:
            self.add_step(
                f"Language Safety: Patient language '{lang_eval.patient_language}' is directly supported without translation barriers."
            )
        elif lang_eval.status == LanguageStatus.REQUIRES_INTERPRETER:
            self.add_step(
                f"Language Safety: Patient language '{lang_eval.patient_language}' requires an interpreter; translator is confirmed available."
            )
        else:
            self.add_step(
                f"Language Safety ALERT: Patient language '{lang_eval.patient_language}' is unsupported by available clinicians and interpreters. Language escalation triggered."
            )

    def log_option_evaluation(self, opt_eval: OptionEvaluation) -> None:
        """Record the feasibility assessment of a specific ladder rung."""
        tier_title = opt_eval.ladder_level.replace("_", " ").title()
        if opt_eval.feasible:
            self.add_step(f"Evaluated '{tier_title}': FEASIBLE. All required resources and constraints are satisfied.")
        else:
            reasons = "; ".join(opt_eval.blocking_reasons)
            self.add_step(f"Evaluated '{tier_title}': BLOCKED. Constraints not met: {reasons}.")

    def log_final_decision(
        self,
        decision: str,
        selected_level: Optional[str],
        escalation_required: bool,
        escalation_reason: Optional[str],
    ) -> None:
        """Record the final decision synthesis."""
        if decision == "ESCALATE_IMMEDIATELY":
            self.add_step(
                f"FINAL DECISION: ESCALATE_IMMEDIATELY. All local treatment rungs (preferred, adapted, fallback) are infeasible. Reason: {escalation_reason}."
            )
        else:
            tier_title = selected_level.replace("_", " ").title() if selected_level else "Unknown"
            self.add_step(
                f"FINAL DECISION: Selected '{tier_title}' as the highest feasible care pathway for this patient's clinical and site constraints."
            )
            if escalation_required:
                self.add_step(f"Escalation Flag: Immediate operational escalation active. Reason: {escalation_reason}.")

    def build(self) -> List[str]:
        """Return the compiled list of reason trail strings."""
        return list(self._trail)
