/**
 * Resource-Aware Care Option Comparer — Comparison Screen Client
 * Phase 10: ui/comparer/comparer.js
 *
 * Invariant:
 * Left panel (Baseline) and Right panel (Resource-Aware) ALWAYS evaluate the exact same case_id.
 */

let allCases = [];
let filteredCases = [];
let activeCaseId = null;

document.addEventListener("DOMContentLoaded", () => {
  initComparer();
});

async function initComparer() {
  await loadSummaryMetrics();
  await loadCaseList();
  setupEventListeners();

  // Check URL params for case_id or default to first
  const urlParams = new URLSearchParams(window.location.search);
  const initialCaseId = urlParams.get("case_id") || (allCases.length > 0 ? allCases[0].case_id : "SYNTH-CASE-001");

  if (initialCaseId) {
    loadCaseComparison(initialCaseId);
  }
}

/**
 * Fetch and render aggregate evaluation metrics (All 40 cases)
 */
async function loadSummaryMetrics() {
  try {
    const res = await fetch("/comparer/summary");
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const metrics = await res.json();

    const baselineFeasEl = document.getElementById("val-baseline-feas");
    const subBaselineFeasEl = document.getElementById("sub-baseline-feas");
    if (baselineFeasEl) baselineFeasEl.textContent = `${metrics.metric_1_baseline_feasible_pct.toFixed(1)}%`;
    if (subBaselineFeasEl) {
      subBaselineFeasEl.textContent = `${metrics.metric_1_baseline_feasible_count}/${metrics.total_cases_evaluated} feasible at local site`;
    }

    const raFeasEl = document.getElementById("val-ra-feas");
    const subRaFeasEl = document.getElementById("sub-ra-feas");
    if (raFeasEl) raFeasEl.textContent = `${metrics.metric_1_resource_aware_feasible_pct.toFixed(1)}%`;
    if (subRaFeasEl) {
      subRaFeasEl.textContent = `${metrics.metric_1_resource_aware_feasible_count}/${metrics.total_cases_evaluated} verified feasible`;
    }

    const langEl = document.getElementById("val-lang-mismatch");
    const subLangEl = document.getElementById("sub-lang-mismatch");
    if (langEl) langEl.textContent = `${metrics.metric_4_language_mismatches_pct.toFixed(1)}%`;
    if (subLangEl) {
      subLangEl.textContent = `${metrics.metric_4_language_mismatches_detected_count} cases required interpreter/safety`;
    }

    const escEl = document.getElementById("val-escalations");
    if (escEl) escEl.textContent = `${metrics.metric_5_immediate_escalations_count}`;
  } catch (err) {
    console.error("Failed to load summary metrics:", err);
  }
}

/**
 * Fetch all 40 cases and populate dropdown
 */
async function loadCaseList() {
  try {
    const res = await fetch("/comparer/cases");
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    allCases = await res.json();
    filteredCases = [...allCases];
    renderDropdown(filteredCases);
  } catch (err) {
    console.error("Failed to load cases:", err);
    const selectEl = document.getElementById("case-select");
    if (selectEl) selectEl.innerHTML = '<option value="">Error loading cases</option>';
  }
}

function renderDropdown(casesToRender) {
  const selectEl = document.getElementById("case-select");
  if (!selectEl) return;

  selectEl.innerHTML = "";
  if (casesToRender.length === 0) {
    selectEl.innerHTML = '<option value="">No cases match filter</option>';
    return;
  }

  casesToRender.forEach((c) => {
    const opt = document.createElement("option");
    opt.value = c.case_id;
    const changedMarker = c.changed ? "🔄 [Adapted]" : "✓ [Preserved]";
    opt.textContent = `${c.case_id} — ${c.condition} (${c.site_name}) ${changedMarker}`;
    selectEl.appendChild(opt);
  });

  if (activeCaseId && casesToRender.some((c) => c.case_id === activeCaseId)) {
    selectEl.value = activeCaseId;
  }
}

function setupEventListeners() {
  const selectEl = document.getElementById("case-select");
  if (selectEl) {
    selectEl.addEventListener("change", (e) => {
      if (e.target.value) {
        loadCaseComparison(e.target.value);
      }
    });
  }

  const prevBtn = document.getElementById("btn-prev-case");
  if (prevBtn) {
    prevBtn.addEventListener("click", () => navigateCase(-1));
  }

  const nextBtn = document.getElementById("btn-next-case");
  if (nextBtn) {
    nextBtn.addEventListener("click", () => navigateCase(1));
  }

  // Keyboard navigation (Left / Right arrow keys)
  document.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;
    if (e.key === "ArrowLeft") navigateCase(-1);
    if (e.key === "ArrowRight") navigateCase(1);
  });

  // Filter chips
  const chips = document.querySelectorAll(".filter-chip");
  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      chips.forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      const filterType = chip.getAttribute("data-filter");
      applyCaseFilter(filterType);
    });
  });
}

function applyCaseFilter(filterType) {
  if (filterType === "all") {
    filteredCases = [...allCases];
  } else if (filterType === "changed") {
    filteredCases = allCases.filter((c) => c.changed);
  } else if (filterType === "unchanged") {
    filteredCases = allCases.filter((c) => !c.changed);
  } else if (filterType === "high") {
    filteredCases = allCases.filter((c) => c.urgency === "HIGH" || c.urgency === "CRITICAL");
  }

  renderDropdown(filteredCases);

  // If current active case is in filtered set, stay on it; otherwise switch to first filtered
  if (!filteredCases.some((c) => c.case_id === activeCaseId) && filteredCases.length > 0) {
    loadCaseComparison(filteredCases[0].case_id);
  }
}

function navigateCase(delta) {
  if (!filteredCases.length) return;
  const currentIndex = filteredCases.findIndex((c) => c.case_id === activeCaseId);
  let newIndex = currentIndex + delta;
  if (newIndex < 0) newIndex = filteredCases.length - 1;
  if (newIndex >= filteredCases.length) newIndex = 0;

  const nextCase = filteredCases[newIndex];
  if (nextCase) {
    loadCaseComparison(nextCase.case_id);
  }
}

/**
 * Fetch and render comparison for the SAME synthetic case
 */
async function loadCaseComparison(caseId) {
  activeCaseId = caseId;
  const selectEl = document.getElementById("case-select");
  if (selectEl && selectEl.value !== caseId) {
    selectEl.value = caseId;
  }

  // Update browser URL query param cleanly without reload
  const newUrl = new URL(window.location);
  newUrl.searchParams.set("case_id", caseId);
  window.history.replaceState({}, "", newUrl);

  try {
    const res = await fetch(`/comparer/compare/${caseId}`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const data = await res.json();

    // STRICT INVARIANT CHECK: Both panels must use the exact same case_id
    if (data.case_id !== caseId) {
      console.error(`Case ID mismatch! Requested: ${caseId}, Received: ${data.case_id}`);
      return;
    }

    renderCaseDetails(data);
  } catch (err) {
    console.error(`Failed to load comparison for case ${caseId}:`, err);
  }
}

/**
 * Render all panels with the received comparison payload
 */
function renderCaseDetails(data) {
  // 1. Meta Bar
  const activeCaseIdEl = document.getElementById("active-case-id");
  if (activeCaseIdEl) activeCaseIdEl.textContent = data.case_id;

  const condEl = document.getElementById("active-condition");
  if (condEl) condEl.textContent = data.condition;

  const urgEl = document.getElementById("active-urgency");
  if (urgEl) {
    urgEl.textContent = data.urgency;
    urgEl.className = `urgency-pill ${data.urgency}`;
  }

  const siteEl = document.getElementById("active-site");
  if (siteEl) siteEl.textContent = `${data.site_name} (${data.site_id})`;

  const langEl = document.getElementById("active-language");
  if (langEl) langEl.textContent = data.patient_language.toUpperCase();

  // 2. Left Panel: TEXTBOOK / BASELINE METHOD
  const baseline = data.baseline;
  const bRecEl = document.getElementById("baseline-rec-text");
  if (bRecEl) bRecEl.textContent = baseline.recommendation;

  const bFeasBadge = document.getElementById("baseline-feasibility-badge");
  if (bFeasBadge) {
    bFeasBadge.textContent = baseline.feasibility_status;
    bFeasBadge.className = `feasibility-badge ${baseline.feasibility ? "feasible" : "not-feasible"}`;
  }

  const bIgnoredList = document.getElementById("baseline-resources-ignored");
  if (bIgnoredList && baseline.resources_ignored) {
    bIgnoredList.innerHTML = "";
    baseline.resources_ignored.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      bIgnoredList.appendChild(li);
    });
  }

  const bFollowupEl = document.getElementById("baseline-followup-text");
  if (bFollowupEl) bFollowupEl.textContent = baseline.follow_up;

  const bLangEl = document.getElementById("baseline-language-text");
  if (bLangEl) bLangEl.textContent = baseline.language;

  const bFeasReasonEl = document.getElementById("baseline-feasibility-reason");
  if (bFeasReasonEl) bFeasReasonEl.textContent = baseline.feasibility_reason;

  // 3. Right Panel: RESOURCE-AWARE METHOD
  const ra = data.resource_aware;
  const raRecEl = document.getElementById("ra-rec-text");
  if (raRecEl) raRecEl.textContent = ra.selected_option;

  const raLadderPill = document.getElementById("ra-ladder-pill");
  if (raLadderPill) {
    const formattedLadder = ra.ladder_level.replace(/_/g, " ").toUpperCase();
    raLadderPill.textContent = `Ladder Tier: ${formattedLadder}`;
  }

  const raFeasBadge = document.getElementById("ra-feasibility-badge");
  if (raFeasBadge) {
    raFeasBadge.textContent = ra.feasibility_status;
    raFeasBadge.className = `feasibility-badge ${ra.feasibility ? "feasible" : "not-feasible"}`;
  }

  const raReasonTrailEl = document.getElementById("ra-reason-trail");
  if (raReasonTrailEl && ra.reason_trail) {
    raReasonTrailEl.innerHTML = "";
    ra.reason_trail.forEach((step) => {
      const div = document.createElement("div");
      div.className = "trail-item";
      div.textContent = step;
      raReasonTrailEl.appendChild(div);
    });
  }

  const raBlockedListEl = document.getElementById("ra-blocked-list");
  if (raBlockedListEl) {
    raBlockedListEl.innerHTML = "";
    const blockedEntries = Object.entries(ra.blocked_options || {});
    if (blockedEntries.length === 0) {
      raBlockedListEl.innerHTML = '<span class="text-muted">None (Preferred option is feasible locally)</span>';
    } else {
      blockedEntries.forEach(([tier, reasons]) => {
        const div = document.createElement("div");
        div.style.marginBottom = "0.35rem";
        div.innerHTML = `<strong>Tier [${tier.replace(/_/g, " ")}]:</strong> ${reasons.join("; ")}`;
        raBlockedListEl.appendChild(div);
      });
    }
  }

  const raFollowupEl = document.getElementById("ra-followup-text");
  if (raFollowupEl) raFollowupEl.textContent = ra.follow_up;

  const raEscalationEl = document.getElementById("ra-escalation-val");
  if (raEscalationEl) raEscalationEl.textContent = ra.escalation;

  const raLangEl = document.getElementById("ra-language-val");
  if (raLangEl) raLangEl.textContent = `${ra.language_status} — ${ra.language_details}`;

  const raFeasDetailsEl = document.getElementById("ra-feasibility-details");
  if (raFeasDetailsEl) raFeasDetailsEl.textContent = ra.feasibility_details;

  // 4. Bottom Section: What changed and why?
  const whatChanged = data.what_changed_and_why;
  const diffBadgeEl = document.getElementById("divergence-status-badge");
  if (diffBadgeEl) {
    if (whatChanged.changed) {
      diffBadgeEl.textContent = "RECOMMENDATION ADAPTED";
      diffBadgeEl.className = "divergence-status-badge";
    } else {
      diffBadgeEl.textContent = "CARE PRESERVED / EQUIVALENT";
      diffBadgeEl.className = "divergence-status-badge";
      diffBadgeEl.classList.add("identical");
    }
  }

  const diffBaselineEl = document.getElementById("diff-baseline-rec");
  if (diffBaselineEl) diffBaselineEl.textContent = whatChanged.baseline_rec;

  const diffRaEl = document.getElementById("diff-ra-rec");
  if (diffRaEl) diffRaEl.textContent = whatChanged.resource_aware_rec;

  const diffReasonEl = document.getElementById("diff-reason-box");
  if (diffReasonEl) diffReasonEl.textContent = whatChanged.reason_summary;

  const diffTagsEl = document.getElementById("diff-factor-tags");
  if (diffTagsEl) {
    diffTagsEl.innerHTML = "";
    if (whatChanged.constraint_factors && whatChanged.constraint_factors.length > 0) {
      whatChanged.constraint_factors.forEach((factor) => {
        const tag = document.createElement("span");
        tag.className = "factor-tag";
        tag.textContent = factor;
        diffTagsEl.appendChild(tag);
      });
    } else {
      const tag = document.createElement("span");
      tag.className = "factor-tag";
      tag.style.background = "var(--color-ra-bg)";
      tag.style.borderColor = "var(--color-ra)";
      tag.style.color = "#6ee7b7";
      tag.textContent = "No resource deficit — full protocol feasibility";
      diffTagsEl.appendChild(tag);
    }
  }
}
