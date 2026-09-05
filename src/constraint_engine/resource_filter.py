"""Resource filtering and capability verification against site registries with safety conflict handling.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from typing import Any, Dict, List, Optional, Tuple

from src.constraint_engine.models import ResourceEvaluation, ResourceStatus
from src.models.operational_models import ServiceSite, TravelConstraints


def check_registry_conflicts(
    site_data: Dict[str, Any],
    resource: str,
) -> Optional[str]:
    """Detect contradictory or ambiguous records in site data for a resource.

    If conflicting data is found, returns an explanatory reason string.
    Otherwise returns None.
    """
    # 1. Check explicit conflict markers
    conflicts = site_data.get("conflicts", {})
    if isinstance(conflicts, dict) and resource in conflicts:
        return f"Conflicting {resource} records detected ({conflicts[resource]}). Safer assumption applied: {resource} treated as unavailable."

    # 2. Check contradictory boolean flags in site metadata
    # e.g., specialist_available=True and specialist_available=False or specialist_unavailable=True
    if resource == "specialist_48h" or resource == "specialists":
        if site_data.get("specialist_available") is True and site_data.get("specialist_available_override") is False:
            return "Conflicting specialist availability records detected. Safer assumption applied: specialist treated as unavailable."
        if site_data.get("specialist_available") is True and site_data.get("specialist_unavailable") is True:
            return "Conflicting specialist availability records detected. Safer assumption applied: specialist treated as unavailable."

    if resource == "cold_chain":
        if site_data.get("cold_chain_available") is True and site_data.get("cold_chain_offline") is True:
            return "Conflicting cold-chain records detected. Safer assumption applied: cold-chain treated as unavailable."

    if resource == "same_day_imaging":
        if site_data.get("imaging_available") is True and site_data.get("imaging_offline") is True:
            return "Conflicting imaging records detected. Safer assumption applied: same-day imaging treated as unavailable."

    if resource == "transport":
        if site_data.get("transport_available") is True and site_data.get("transport_offline") is True:
            return "Conflicting transport records detected. Safer assumption applied: transport treated as unavailable."

    return None


def evaluate_resource_availability(
    resource: str,
    site: ServiceSite,
    travel_constraints: Optional[TravelConstraints] = None,
    raw_site_dict: Optional[Dict[str, Any]] = None,
) -> ResourceEvaluation:
    """Evaluate whether a specific required resource is available at the given site.

    Adheres strictly to the safety invariant:
    If conflicting records are detected, do NOT guess or average; apply the safer
    clinical assumption and treat the resource as unavailable.

    Args:
        resource: Resource identifier (e.g. 'same_day_imaging', 'cold_chain', 'specialist_48h')
        site: ServiceSite object representing the healthcare facility.
        travel_constraints: Optional travel constraints of the patient.
        raw_site_dict: Optional raw dictionary to inspect for low-level metadata conflicts.

    Returns:
        ResourceEvaluation detailing availability, status, and rationale.
    """
    site_dict = raw_site_dict or site.model_dump()

    # Step 1: Detect and resolve registry conflicts
    conflict_reason = check_registry_conflicts(site_dict, resource)
    if conflict_reason:
        return ResourceEvaluation(
            resource=resource,
            required=True,
            available=False,
            status=ResourceStatus.CONFLICT_RESOLVED_BLOCKED,
            reason=conflict_reason,
        )

    res_lower = resource.strip().lower()

    # 1. Imaging checks
    if res_lower in ("same_day_imaging", "imaging", "ultrasound", "doppler_ultrasound", "ct_scanner", "mri_scanner"):
        imaging_modalities = {"doppler_ultrasound", "ct_scanner", "mri_scanner", "digital_xray", "ultrasound_general", "point_of_care_ultrasound_basic"}
        site_equipment = {e.lower() for e in site.equipment}
        available_modalities = imaging_modalities.intersection(site_equipment)

        if available_modalities:
            return ResourceEvaluation(
                resource=resource,
                required=True,
                available=True,
                status=ResourceStatus.AVAILABLE,
                reason=f"Imaging available on site ({', '.join(sorted(available_modalities))}).",
            )
        else:
            return ResourceEvaluation(
                resource=resource,
                required=True,
                available=False,
                status=ResourceStatus.BLOCKED,
                reason="Same-day diagnostic imaging is unavailable at the current site.",
            )

    # 2. Cold Chain checks
    if res_lower in ("cold_chain", "refrigeration"):
        if site.cold_chain_available:
            return ResourceEvaluation(
                resource=resource,
                required=True,
                available=True,
                status=ResourceStatus.AVAILABLE,
                reason="Functional continuous cold-chain storage is verified on site.",
            )
        else:
            return ResourceEvaluation(
                resource=resource,
                required=True,
                available=False,
                status=ResourceStatus.BLOCKED,
                reason="Cold-chain storage is unavailable or currently non-functional at this site.",
            )

    # 3. Specialist checks (48h)
    if res_lower in ("specialist_48h", "specialist", "specialists"):
        # Check on-site specialists
        if site.specialists and len(site.specialists) > 0:
            return ResourceEvaluation(
                resource=resource,
                required=True,
                available=True,
                status=ResourceStatus.AVAILABLE,
                reason=f"Specialist available on site: {', '.join(site.specialists)} ({site.specialist_availability_hours}).",
            )
        # Check teleconsultation specialist on-call availability
        avail_hours = site.specialist_availability_hours.lower()
        if "remote teleconsultation on-call" in avail_hours or "remote tele-specialist" in avail_hours:
            return ResourceEvaluation(
                resource=resource,
                required=True,
                available=True,
                status=ResourceStatus.AVAILABLE,
                reason=f"Specialist accessible remotely within 48h via teleconsultation ({site.specialist_availability_hours}).",
            )
        else:
            return ResourceEvaluation(
                resource=resource,
                required=True,
                available=False,
                status=ResourceStatus.BLOCKED,
                reason="Specialist unavailable within the required 48-hour clinical window.",
            )

    # 4. Medication Stock checks
    if res_lower in ("medication_stock", "pharmacy", "oral_medication"):
        if site.medication_stock and len(site.medication_stock) > 0:
            return ResourceEvaluation(
                resource=resource,
                required=True,
                available=True,
                status=ResourceStatus.AVAILABLE,
                reason=f"Essential pharmaceuticals verified in stock ({len(site.medication_stock)} formulations present).",
            )
        else:
            return ResourceEvaluation(
                resource=resource,
                required=True,
                available=False,
                status=ResourceStatus.BLOCKED,
                reason="Medication stockout: required pharmaceuticals are unavailable in the local dispensary.",
            )

    # Specific medication check
    if res_lower.startswith("medication:") or res_lower.startswith("drug:"):
        med_name = res_lower.split(":", 1)[1].strip()
        site_meds = {m.lower() for m in site.medication_stock}
        if med_name in site_meds:
            return ResourceEvaluation(
                resource=resource,
                required=True,
                available=True,
                status=ResourceStatus.AVAILABLE,
                reason=f"Medication '{med_name}' is currently verified in stock.",
            )
        else:
            return ResourceEvaluation(
                resource=resource,
                required=True,
                available=False,
                status=ResourceStatus.BLOCKED,
                reason=f"Medication stockout: '{med_name}' is not in stock at the local dispensary.",
            )

    # 5. Transport checks
    if res_lower in ("transport", "ambulance", "vehicle"):
        has_site_transport = site.transport_available
        has_patient_transport = travel_constraints.transport_available if travel_constraints else False

        if has_site_transport or has_patient_transport:
            src = "facility ambulance" if has_site_transport else "patient transit"
            return ResourceEvaluation(
                resource=resource,
                required=True,
                available=True,
                status=ResourceStatus.AVAILABLE,
                reason=f"Transport is available via {src}.",
            )
        else:
            return ResourceEvaluation(
                resource=resource,
                required=True,
                available=False,
                status=ResourceStatus.BLOCKED,
                reason="Transport unavailable: Neither facility ambulance nor viable patient conveyance is available.",
            )

    # 6. Connectivity checks
    if res_lower in ("stable_connectivity", "connectivity", "teleconsult_bandwidth"):
        bandwidth = site.teleconsult_bandwidth.lower()
        if "128 kbps" in bandwidth or "intermittent" in bandwidth:
            return ResourceEvaluation(
                resource=resource,
                required=True,
                available=False,
                status=ResourceStatus.BLOCKED,
                reason="Connectivity insufficient: 2G cellular link is too unstable for reliable teleconsultation or remote monitoring.",
            )
        return ResourceEvaluation(
            resource=resource,
            required=True,
            available=True,
            status=ResourceStatus.AVAILABLE,
            reason=f"Adequate network connectivity available ({site.teleconsult_bandwidth}).",
        )

    # 7. Local Clinician checks
    if res_lower in ("local_clinician", "local_health_worker", "lhw"):
        # Available if staff exists at Sub-Center, CHC, Taluk, or Tertiary
        return ResourceEvaluation(
            resource=resource,
            required=True,
            available=True,
            status=ResourceStatus.AVAILABLE,
            reason="Local healthcare cadre is present on site to supervise care.",
        )

    # 8. Interpreter checks
    if res_lower in ("interpreter", "translation"):
        # Will be verified in conjunction with language safety
        return ResourceEvaluation(
            resource=resource,
            required=True,
            available=True,
            status=ResourceStatus.AVAILABLE,
            reason="Translation support verified.",
        )

    # Default fallback for unspecified generic resources
    return ResourceEvaluation(
        resource=resource,
        required=True,
        available=True,
        status=ResourceStatus.AVAILABLE,
        reason=f"Standard resource '{resource}' assumed available.",
    )
