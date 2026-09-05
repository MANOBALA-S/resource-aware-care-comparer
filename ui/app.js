/**
 * Resource-Aware Care Option Comparer - Frontend Application
 * Supports English & Tamil with real-time UI translation and communication safety gates.
 *
 * Synthetic data only — no real patient data.
 * Decision-support prototype — clinician sign-off required.
 */

let currentLang = 'en';
let loadedMessages = {};
let allCases = [];
let currentCase = null;
let currentEvaluation = null;

// DOM Elements
const langBtnEn = document.getElementById('lang-btn-en');
const langBtnTa = document.getElementById('lang-btn-ta');
const caseSelect = document.getElementById('case-select');
const caseDetailsPanel = document.getElementById('case-details-panel');
const evaluateBtn = document.getElementById('evaluate-btn');
const commWarningBanner = document.getElementById('comm-warning-banner');
const commWarningTitle = document.getElementById('comm-warning-title');
const commWarningText = document.getElementById('comm-warning-text');
const evalDecisionBadge = document.getElementById('eval-decision-badge');
const textbookText = document.getElementById('textbook-recommendation-text');
const resourceText = document.getElementById('resource-adapted-text');
const resourceTitle = document.getElementById('resource-adapted-title');
const reasonTrailList = document.getElementById('reason-trail-list');
const trailLangIndicator = document.getElementById('trail-lang-indicator');
const followupTbody = document.getElementById('followup-tbody');
const refreshFollowupsBtn = document.getElementById('refresh-followups-btn');

// Initialize application
document.addEventListener('DOMContentLoaded', async () => {
  setupEventListeners();
  await switchLanguage('en');
  await loadCases();
  await loadFollowups();
});

function setupEventListeners() {
  langBtnEn.addEventListener('click', () => switchLanguage('en'));
  langBtnTa.addEventListener('click', () => switchLanguage('ta'));

  caseSelect.addEventListener('change', (e) => {
    const caseId = e.target.value;
    onCaseSelected(caseId);
  });

  evaluateBtn.addEventListener('click', async () => {
    if (currentCase) {
      await runEvaluation(currentCase.case_id);
    }
  });

  if (refreshFollowupsBtn) {
    refreshFollowupsBtn.addEventListener('click', loadFollowups);
  }
}

/**
 * Switch active application display language.
 */
async function switchLanguage(lang) {
  currentLang = lang;

  // Toggle active button states
  if (lang === 'en') {
    langBtnEn.classList.add('active');
    langBtnTa.classList.remove('active');
  } else {
    langBtnTa.classList.add('active');
    langBtnEn.classList.remove('active');
  }

  // Fetch messages dictionary
  try {
    const res = await fetch(`/languages/${lang}/messages`);
    if (res.ok) {
      loadedMessages = await res.json();
      applyTranslations();
    }
  } catch (err) {
    console.warn('Failed to load language catalog:', err);
  }

  // Re-evaluate or update reason trail in new language if an evaluation is active
  if (currentCase && currentEvaluation) {
    await runEvaluation(currentCase.case_id);
  }
}

/**
 * Apply localized strings to static UI elements.
 */
function applyTranslations() {
  const m = (key, fallback) => loadedMessages[key] || fallback;

  // Header and disclaimers
  setText('ui-app-title', m('app_title', 'Resource-Aware Care Option Comparer'));
  setText('ui-app-subtitle', m('app_subtitle', 'Multilingual Teleconsultation Decision-Support Prototype'));
  setText('ui-lang-label', m('language_selector', 'Language') + ':');
  setText('ui-prototype-disclaimer', m('prototype_disclaimer', 'Decision-support prototype — clinician sign-off required.'));
  setText('ui-synthetic-data-policy', m('synthetic_data_policy', 'Synthetic data only — no real patient data.'));

  // Case card labels
  setText('ui-case-header', m('patient_case', 'Patient Case Profile'));
  setText('ui-select-case-label', m('select_case', 'Select Synthetic Patient Case') + ':');
  setText('ui-key-condition', m('clinical_condition', 'Condition') + ':');
  setText('ui-key-site', m('facility_site', 'Facility Site') + ':');
  setText('ui-key-urgency', m('urgency', 'Urgency Tier') + ':');
  setText('ui-key-language', m('language_selector', 'Patient Language') + ':');
  setText('ui-key-safety', m('feasibility_status', 'Communication Safety') + ':');
  setText('ui-eval-btn-text', m('evaluate_button', 'Compare Care Options'));

  // Results panel
  setText('ui-comparison-header', m('app_title', 'Care Option Comparison'));
  setText('ui-tag-textbook', m('textbook_baseline', 'TEXTBOOK GUIDELINE'));
  setText('ui-title-textbook', m('preferred_option', 'Gold-Standard Recommendation'));
  setText('ui-tag-resource', m('resource_adapted_plan', 'RESOURCE-AWARE PLAN'));
  setText('ui-reason-trail-title', m('reason_trail_title', 'Inspectable Reason Trail'));
  setText('trail-lang-indicator', `Language / மொழி: ${currentLang === 'ta' ? 'தமிழ்' : 'English'}`);

  // Follow-up card
  setText('ui-followup-header', m('active_followups', 'Operational Follow-Up & Escalation Tracker'));
  setText('ui-refresh-btn-text', m('actions', 'Refresh Tasks'));

  // Update table headers
  setText('th-case', m('patient_case', 'Case ID'));
  setText('th-urgency', m('urgency', 'Urgency'));
  setText('th-owner', m('owner', 'Owner'));
  setText('th-due', m('due_at', 'Due Deadline'));
  setText('th-status', m('status', 'Status'));
  setText('th-actions', m('actions', 'Action'));

  // Update details panel if case is active
  if (currentCase) {
    updateCaseDetails(currentCase);
  }
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

/**
 * Fetch and populate synthetic cases into dropdown.
 */
async function loadCases() {
  try {
    const res = await fetch('/cases');
    if (!res.ok) throw new Error('Could not load cases');
    allCases = await res.json();

    caseSelect.innerHTML = '<option value="">-- Choose a patient case --</option>';
    allCases.forEach((c) => {
      const opt = document.createElement('option');
      opt.value = c.case_id;
      opt.textContent = `${c.case_id} — ${c.condition} (${c.patient_language.toUpperCase()}, ${c.urgency})`;
      caseSelect.appendChild(opt);
    });
  } catch (err) {
    console.error(err);
    caseSelect.innerHTML = '<option value="">Error loading cases</option>';
  }
}

/**
 * Handle selection of a patient case.
 */
function onCaseSelected(caseId) {
  currentCase = allCases.find((c) => c.case_id === caseId);
  currentEvaluation = null;

  if (!currentCase) {
    caseDetailsPanel.classList.add('hidden');
    evaluateBtn.disabled = true;
    commWarningBanner.classList.add('hidden');
    return;
  }

  caseDetailsPanel.classList.remove('hidden');
  evaluateBtn.disabled = false;
  updateCaseDetails(currentCase);

  // Reset comparison cards
  textbookText.textContent = 'Click "Compare Care Options" to evaluate this case.';
  resourceText.textContent = 'Evaluation required.';
  resourceTitle.textContent = 'Selected Feasible Pathway';
  evalDecisionBadge.textContent = 'READY TO EVALUATE';
  evalDecisionBadge.className = 'badge badge-synthetic';
  reasonTrailList.innerHTML = '<li class="trail-placeholder">Click "Compare Care Options" to generate the audit trail.</li>';
  commWarningBanner.classList.add('hidden');
}

/**
 * Update case detail fields.
 */
function updateCaseDetails(c) {
  setText('case-val-condition', c.condition);
  setText('case-val-site', `${c.site_id} (${c.population_group})`);
  setText('case-val-urgency', c.urgency);
  setText('case-val-language', c.patient_language.toUpperCase());
  setText('case-val-connectivity', c.connectivity || c.travel_constraints?.connectivity_quality || 'MODERATE');

  // Preliminary language badge
  const badge = document.getElementById('case-val-lang-status');
  if (c.patient_language.toLowerCase() === 'en') {
    badge.textContent = loadedMessages['status_supported'] || 'Directly Supported';
    badge.className = 'badge badge-supported';
  } else if (c.travel_constraints?.interpreter_required) {
    badge.textContent = loadedMessages['status_requires_interpreter'] || 'Requires Interpreter';
    badge.className = 'badge badge-interpreter';
  } else {
    badge.textContent = loadedMessages['status_supported'] || 'Directly Supported';
    badge.className = 'badge badge-supported';
  }
}

/**
 * Execute option evaluation via POST /evaluate with active display language.
 */
async function runEvaluation(caseId) {
  evaluateBtn.disabled = true;
  setText('ui-eval-btn-text', loadedMessages['evaluating'] || 'Evaluating Constraints...');

  try {
    const res = await fetch('/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        case_id: caseId,
        lang: currentLang,
        clinician_languages: ['en'], // Teleconsultation clinician default
      }),
    });

    if (!res.ok) {
      throw new Error(`Evaluation failed with status ${res.status}`);
    }

    currentEvaluation = await res.json();
    renderEvaluationResults(currentEvaluation);
  } catch (err) {
    console.error('Evaluation error:', err);
    alert('Failed to evaluate case. See console for details.');
  } finally {
    evaluateBtn.disabled = false;
    setText('ui-eval-btn-text', loadedMessages['evaluate_button'] || 'Compare Care Options');
  }
}

/**
 * Render evaluation results and enforce communication safety gate.
 */
function renderEvaluationResults(evalData) {
  // 1. Safety Invariant Check: If language is unsupported, DO NOT silently display recommendation
  if (!evalData.communication_supported || evalData.language_status === 'LANGUAGE_ESCALATION_REQUIRED') {
    commWarningBanner.classList.remove('hidden');
    commWarningTitle.textContent = loadedMessages['language_escalation_required'] || 'LANGUAGE ESCALATION REQUIRED';
    commWarningText.textContent =
      evalData.communication_warning ||
      'Communication cannot be safely supported: Clinician and interpreter do not support patient language.';

    evalDecisionBadge.textContent = 'COMMUNICATION UNSUPPORTED';
    evalDecisionBadge.className = 'badge badge-escalation';

    resourceTitle.textContent = 'COMMUNICATION BLOCKED';
    resourceText.textContent =
      'WARNING: Patient language cannot be understood by available staff or interpreters. Immediate language escalation is mandatory before treatment delivery.';
  } else {
    commWarningBanner.classList.add('hidden');
    evalDecisionBadge.textContent = evalData.decision;
    evalDecisionBadge.className = evalData.feasible ? 'badge badge-supported' : 'badge badge-escalation';

    // Rung title & selected option
    const tierName = evalData.selected_ladder_level ? evalData.selected_ladder_level.replace(/_/g, ' ').toUpperCase() : 'ESCALATE';
    resourceTitle.textContent = tierName;
    resourceText.textContent = evalData.selected_option || 'Immediate clinical escalation required.';
  }

  // Textbook baseline note
  textbookText.textContent =
    'Standard textbook guideline assumes unrestricted access to tertiary diagnostics, specialists, and continuous cold chain.';

  // Render Reason Trail (in requested language: English or Tamil)
  reasonTrailList.innerHTML = '';
  if (evalData.reason_trail && evalData.reason_trail.length > 0) {
    evalData.reason_trail.forEach((step) => {
      const li = document.createElement('li');
      li.textContent = step;
      reasonTrailList.appendChild(li);
    });
  } else {
    reasonTrailList.innerHTML = '<li class="trail-placeholder">No reason trail recorded.</li>';
  }
}

/**
 * Load and render follow-up tasks from SQLite backend.
 */
async function loadFollowups() {
  try {
    const res = await fetch('/followups');
    if (!res.ok) throw new Error('Could not fetch follow-ups');
    const tasks = await res.json();

    if (tasks.length === 0) {
      followupTbody.innerHTML = '<tr><td colspan="8" class="text-center">No active follow-up tasks tracked.</td></tr>';
      return;
    }

    followupTbody.innerHTML = '';
    tasks.slice(0, 8).forEach((t) => {
      const tr = document.createElement('tr');

      const badgeClass =
        t.status === 'COMPLETED'
          ? 'badge-supported'
          : t.status === 'ESCALATED' || t.status === 'OVERDUE'
          ? 'badge-escalation'
          : 'badge-synthetic';

      tr.innerHTML = `
        <td><strong>${t.follow_up_id}</strong></td>
        <td>${t.case_id}</td>
        <td>${t.task_type}</td>
        <td><span class="badge badge-synthetic">${t.urgency}</span></td>
        <td>${t.owner}</td>
        <td>${new Date(t.due_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', month: 'short', day: 'numeric' })}</td>
        <td><span class="badge ${badgeClass}">${t.status}</span></td>
        <td>
          ${
            t.status !== 'COMPLETED'
              ? `<button class="btn btn-sm btn-secondary" onclick="completeTask('${t.follow_up_id}')">Done</button>`
              : '<span class="text-muted">Completed</span>'
          }
        </td>
      `;
      followupTbody.appendChild(tr);
    });
  } catch (err) {
    console.error('Failed to load follow-ups:', err);
    followupTbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">Error loading follow-up tasks.</td></tr>';
  }
}

async function completeTask(id) {
  try {
    const res = await fetch(`/followups/${id}/complete`, { method: 'POST' });
    if (res.ok) {
      await loadFollowups();
    }
  } catch (err) {
    console.error('Error completing task:', err);
  }
}
window.completeTask = completeTask;
