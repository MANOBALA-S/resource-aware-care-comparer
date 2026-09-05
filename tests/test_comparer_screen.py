"""Tests for Phase 10: Care Option Comparison Screen.

Verifies:
1. Exact same case_id evaluated in both panels.
2. Baseline panel fields: recommendation, resources ignored, follow-up, language, feasibility.
3. Resource-aware panel fields: selected option, ladder level, feasibility, reason trail, blocked options, follow-up, escalation, language status.
4. Bottom section: "What changed and why?" accurately captures divergence rationale.
5. Aggregate metrics endpoint: baseline vs resource-aware feasibility, follow-up coverage, language mismatches.
6. Static file serving for ui/comparer/ (HTML, CSS, JS).

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from fastapi.testclient import TestClient
import pytest

from src.main import app

client = TestClient(app)


def test_compare_endpoint_same_case_id():
    """Verify that GET /comparer/compare/{case_id} evaluates the EXACT SAME case in both panels."""
    case_id = "SYNTH-CASE-001"
    response = client.get(f"/comparer/compare/{case_id}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()

    # Exact same case_id guarantee
    assert data["case_id"] == case_id
    assert data["condition"] is not None
    assert data["site_id"] is not None
    assert data["urgency"] is not None

    # Mandatory disclaimers
    assert "Decision-support prototype — clinician sign-off required." in data["governance_notice"]
    assert "Synthetic data only — no real patient data." in data["synthetic_data_notice"]


def test_compare_all_40_cases_immutability():
    """Verify that all 40 cases can be compared without error and maintain case_id consistency."""
    cases_resp = client.get("/comparer/cases")
    assert cases_resp.status_code == 200
    cases_list = cases_resp.json()
    assert len(cases_list) == 40, f"Expected 40 cases, got {len(cases_list)}"

    for case_item in cases_list:
        cid = case_item["case_id"]
        resp = client.get(f"/comparer/compare/{cid}")
        assert resp.status_code == 200, f"Failed for case {cid}"
        data = resp.json()
        assert data["case_id"] == cid
        assert data["baseline"]["label"] == "TEXTBOOK / BASELINE METHOD"
        assert data["resource_aware"]["label"] == "RESOURCE-AWARE METHOD"


def test_baseline_panel_fields():
    """Verify baseline panel displays recommendation, resources ignored, follow-up, language, and feasibility."""
    case_id = "SYNTH-CASE-002"
    response = client.get(f"/comparer/compare/{case_id}")
    assert response.status_code == 200
    baseline = response.json()["baseline"]

    assert baseline["label"] == "TEXTBOOK / BASELINE METHOD"
    assert isinstance(baseline["recommendation"], str) and len(baseline["recommendation"]) > 0
    assert isinstance(baseline["resources_ignored"], list) and len(baseline["resources_ignored"]) >= 5
    assert "Untracked" in baseline["follow_up"]
    assert "no named human owner assigned" in baseline["follow_up"]
    assert "Ignored" in baseline["language"]
    assert isinstance(baseline["feasibility"], bool)
    assert baseline["feasibility_status"] in ("FEASIBLE", "NOT FEASIBLE")
    assert isinstance(baseline["feasibility_reason"], str) and len(baseline["feasibility_reason"]) > 0


def test_resource_aware_panel_fields():
    """Verify resource-aware panel displays selected option, ladder level, feasibility, reason trail, blocked options, follow-up, escalation, language status."""
    case_id = "SYNTH-CASE-003"
    response = client.get(f"/comparer/compare/{case_id}")
    assert response.status_code == 200
    ra = response.json()["resource_aware"]

    assert ra["label"] == "RESOURCE-AWARE METHOD"
    assert isinstance(ra["selected_option"], str) and len(ra["selected_option"]) > 0
    assert ra["ladder_level"] in ("preferred", "resource_adapted_alternative", "minimum_safe_fallback", "escalate_only")
    assert ra["feasibility"] is True
    assert ra["feasibility_status"] == "FEASIBLE"
    assert isinstance(ra["reason_trail"], list) and len(ra["reason_trail"]) > 0
    assert isinstance(ra["blocked_options"], dict)
    assert "Tracked task" in ra["follow_up"]
    assert ra["follow_up_details"]["owner"] is not None
    assert ra["follow_up_details"]["due_at"] is not None
    assert isinstance(ra["follow_up_details"]["escalation_path"], list)
    assert isinstance(ra["escalation"], str)
    assert isinstance(ra["language_status"], str)


def test_what_changed_and_why():
    """Verify 'What changed and why?' correctly describes divergence when constraints force adaptation."""
    # SYNTH-CASE-002 is at SITE-002 (Remote Primary Clinic), which lacks cold-chain storage and specialist coverage
    case_id = "SYNTH-CASE-002"
    response = client.get(f"/comparer/compare/{case_id}")
    assert response.status_code == 200
    data = response.json()
    wc = data["what_changed_and_why"]

    # This case diverged from textbook guideline due to peripheral site constraints
    assert wc["changed"] is True
    assert wc["baseline_rec"] != wc["resource_aware_rec"]
    assert isinstance(wc["reason_summary"], str) and len(wc["reason_summary"]) > 0
    assert len(wc["constraint_factors"]) > 0

    # SYNTH-CASE-001 is at SITE-001 (Tertiary Hospital), where textbook care is feasible
    case_id_unchanged = "SYNTH-CASE-001"
    response_unchanged = client.get(f"/comparer/compare/{case_id_unchanged}")
    assert response_unchanged.status_code == 200
    wc_unchanged = response_unchanged.json()["what_changed_and_why"]

    assert wc_unchanged["changed"] is False
    assert len(wc_unchanged["baseline_rec"]) > 0
    assert len(wc_unchanged["resource_aware_rec"]) > 0
    assert "No change required" in wc_unchanged["reason_summary"]


def test_comparer_summary_metrics_endpoint():
    """Verify /comparer/summary returns aggregate metrics matching Phase 7 benchmark."""
    response = client.get("/comparer/summary")
    assert response.status_code == 200
    metrics = response.json()

    assert metrics["total_cases_evaluated"] == 40
    assert metrics["metric_1_baseline_feasible_pct"] == 65.0
    assert metrics["metric_1_resource_aware_feasible_pct"] == 100.0
    assert metrics["metric_1_baseline_feasible_count"] == 26
    assert metrics["metric_1_resource_aware_feasible_count"] == 40
    assert metrics["metric_2_total_high_priority_cases"] == 16
    assert metrics["metric_2_baseline_high_priority_tracked_pct"] == 0.0
    assert metrics["metric_2_resource_aware_high_priority_tracked_pct"] == 100.0
    assert metrics["metric_3_recommendations_changed_count"] == 14
    assert metrics["metric_3_recommendations_changed_pct"] == 35.0
    assert metrics["metric_4_language_mismatches_detected_count"] == 29
    assert metrics["metric_4_language_mismatches_pct"] == 72.5
    assert metrics["metric_5_immediate_escalations_count"] == 0


def test_ui_comparer_static_files_served():
    """Verify that ui/comparer/ static files (index.html, comparer.css, comparer.js) are properly served."""
    html_resp = client.get("/ui/comparer/index.html")
    assert html_resp.status_code == 200
    assert "TEXTBOOK / BASELINE METHOD" in html_resp.text
    assert "RESOURCE-AWARE METHOD" in html_resp.text
    assert "What changed and why?" in html_resp.text
    assert "Decision-support prototype — clinician sign-off required." in html_resp.text
    assert "SYNTHETIC DATA" in html_resp.text

    css_resp = client.get("/ui/comparer/comparer.css")
    assert css_resp.status_code == 200
    assert "--color-baseline" in css_resp.text

    js_resp = client.get("/ui/comparer/comparer.js")
    assert js_resp.status_code == 200
    assert "loadCaseComparison" in js_resp.text
    assert "/comparer/compare" in js_resp.text
