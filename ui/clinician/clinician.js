/**
 * Resource-Aware Care Option Comparer — Clinician Screen Logic
 * Real-time Bilingual Decision Support (English & தமிழ்)
 * 
 * Synthetic data only — no real patient data.
 * Decision-support prototype — clinician sign-off required.
 */

// State
let currentLang = 'en';
let currentCaseId = 'SYNTH-CASE-001';
let simulateExhaustion = false;
let casesCache = [];

// Bilingual UI Text Dictionary
const UI_STRINGS = {
  en: {
    appTitle: "Resource-Aware Care Option Comparer",
    appSubtitle: "Clinician Teleconsultation Decision-Support Screen",
    governanceDisclaimer: "Decision-support prototype — clinician sign-off required.",
    selectCaseLabel: "Select Synthetic Patient Case:",
    btnEvaluate: "Evaluate Recommendations",
    btnSimExhaustion: "Simulate Option Exhaustion",
    btnRevertExhaustion: "Revert Simulation",
    
    // Headings
    headingPatient: "Patient Case Profile",
    headingResources: "Local Facility Resources",
    headingRecommendation: "Resource-Aware Recommendation",
    headingFollowup: "Accountable Follow-up & Escalation",
    
    // Patient Fields
    labelCaseId: "Case ID",
    labelCondition: "Condition",
    labelAgeBand: "Age Band",
    labelPopGroup: "Population Group",
    labelPatientLang: "Patient Language",
    labelSite: "Facility Site",
    
    // Resource Fields
    labelEquipment: "Diagnostic Equipment Available",
    labelMedications: "In-Stock Formulary & Medications",
    labelSpecialists: "Specialists On-Call",
    labelTransport: "Emergency Transport",
    labelConnectivity: "Teleconsult Connectivity",
    labelColdChain: "Cold Chain Storage",
    labelInterpreter: "Interpreter & Language Support",
    
    // Recommendation Fields
    labelTransparentTrail: "Transparent Clinical Reason Trail",
    trailHelpText: "Inspectable step-by-step verification comparing requirements against actual site capabilities:",
    labelBlockedOptions: "Blocked Higher Ladder Tiers & Reasons:",
    statusFeasible: "FEASIBLE LOCAL OPTION",
    statusInfeasible: "LOCAL TIERS BLOCKED",
    noEscalation: "NO EMERGENCY ESCALATION",
    escalationMandatory: "EMERGENCY ESCALATION MANDATORY",
    
    // Follow-up Fields
    labelFollowupOwner: "Named Task Owner",
    labelFollowupDue: "SLA Due Date & Time",
    labelFollowupPath: "Escalation Ladder Hierarchy",
    labelFollowupDesc: "Action Item Instructions",
    
    // Safety Banners
    bannerEscalateTitle: "ESCALATE IMMEDIATELY",
    bannerLanguageTitle: "LANGUAGE ESCALATION REQUIRED",
    bannerEscalateMsg: "All local care pathways blocked. Immediate transfer and specialist escalation required.",
    bannerLanguageMsg: "Patient language is unsupported by available clinicians and interpreters. Proceeding is unsafe.",
    
    // Footers
    footerGovernance: "⚠️ <strong>Decision-Support Prototype:</strong> Clinician sign-off required before implementing any recommendation.",
    footerSynthetic: "🔒 <strong>Synthetic Operational Data:</strong> No real patient data is used. All clinical cases, sites, and protocols are synthetic."
  },
  ta: {
    appTitle: "வள-அறிவாற்றல் சிகிச்சை ஒப்பீட்டாளர்",
    appSubtitle: "மருத்துவர் தொலைத்தொடர்பு மருத்துவ முடிவு ஆதரவு திரை",
    governanceDisclaimer: "முடிவு ஆதரவு முன்மாதிரி — மருத்துவர் ஒப்புதல் தேவை.",
    selectCaseLabel: "செயற்கை நோயாளி வழக்கை தேர்ந்தெடுக்கவும்:",
    btnEvaluate: "பரிந்துரைகளை மதிப்பிடு",
    btnSimExhaustion: "சிகிச்சை தீர்வு தடையை உருவகப்படுத்து",
    btnRevertExhaustion: "இயல்பு நிலைக்கு திரும்பு",
    
    // Headings
    headingPatient: "நோயாளி விவரங்கள்",
    headingResources: "உள்ளூர் மருத்துவமனை வளங்கள்",
    headingRecommendation: "வள-தழுவிய மருத்துவ பரிந்துரை",
    headingFollowup: "பொறுப்பான பின்தொடர்தல் மற்றும் அதிகரிப்பு",
    
    // Patient Fields
    labelCaseId: "வழக்கு எண் (Case ID)",
    labelCondition: "மருத்துவ நிலை",
    labelAgeBand: "வயது வரம்பு",
    labelPopGroup: "மக்கள் தொகை குழு",
    labelPatientLang: "நோயாளி பேசும் மொழி",
    labelSite: "சிகிச்சை மையம்",
    
    // Resource Fields
    labelEquipment: "கிடைக்கக்கூடிய பரிசோதனை கருவிகள்",
    labelMedications: "கையிருப்பில் உள்ள மருந்துகள்",
    labelSpecialists: "சிறப்பு மருத்துவர்கள்",
    labelTransport: "அவசர ஆம்புலன்ஸ் போக்குவரத்து",
    labelConnectivity: "தொலைத்தொடர்பு இணைய வசதி",
    labelColdChain: "குளிர்பதன சேமிப்பு வசதி",
    labelInterpreter: "மொழிபெயர்ப்பாளர் & மொழி ஆதரவு",
    
    // Recommendation Fields
    labelTransparentTrail: "வெளிப்படையான மருத்துவ காரணப் பாதை",
    trailHelpText: "உள்ளூர் வளங்களுடன் மருத்துவ நெறிமுறை தேவைகளை ஒப்பிடும் வெளிப்படையான சரிபார்ப்பு:",
    labelBlockedOptions: "தடைசெய்யப்பட்ட சிகிச்சை நிலைகளும் காரணங்களும்:",
    statusFeasible: "உள்ளூரில் சாத்தியமான தேர்வு",
    statusInfeasible: "உள்ளூர் தேர்வுகள் கிடைக்கவில்லை",
    noEscalation: "அவசர அதிகரிப்பு தேவையில்லை",
    escalationMandatory: "உடனடி அவசர அதிகரிப்பு கட்டாயம்",
    
    // Follow-up Fields
    labelFollowupOwner: "பொறுப்பான அலுவலர் / பணியாளர்",
    labelFollowupDue: "காலக்கெடு தேதி & நேரம் (SLA)",
    labelFollowupPath: "படிநிலை மேலனுப்பல் திட்டம்",
    labelFollowupDesc: "செயல்படுத்த வேண்டிய அறிவுறுத்தல்கள்",
    
    // Safety Banners
    bannerEscalateTitle: "உடனடி தீவிர மேலனுப்பல் தேவை",
    bannerLanguageTitle: "மொழி அதிகரிப்பு தேவை",
    bannerEscalateMsg: "அனைத்து உள்ளூர் சிகிச்சை வழிகளும் தடைபட்டுள்ளன. உடனடி இடமாற்றம் மற்றும் நிபுணர் மேலனுப்பல் தேவை.",
    bannerLanguageMsg: "நோயாளியின் மொழி மருத்துவ ஊழியர்கள் மற்றும் மொழிபெயர்ப்பாளர்களால் ஆதரிக்கப்படவில்லை. உரையாடலை தொடர்வது பாதுகாப்பற்றது.",
    
    // Footers
    footerGovernance: "⚠️ <strong>முடிவு ஆதரவு முன்மாதிரி:</strong> எந்தவொரு பரிந்துரையையும் செயல்படுத்தும் முன் தகுதிவாய்ந்த மருத்துவர் ஒப்புதல் கட்டாயம்.",
    footerSynthetic: "🔒 <strong>செயற்கை செயல்பாட்டு தரவு:</strong> உண்மையான நோயாளி தரவு எதுவும் பயன்படுத்தப்படவில்லை. அனைத்தும் செயற்கையானவை."
  }
};

/**
 * Initialize application on DOM ready.
 */
document.addEventListener('DOMContentLoaded', () => {
  loadCasesList();
  setupEventListeners();
});

/**
 * Fetch list of all 40 synthetic cases and populate dropdown.
 */
async function loadCasesList() {
  const selector = document.getElementById('case-selector');
  try {
    const response = await fetch('/cases');
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    
    const cases = await response.json();
    casesCache = cases;

    selector.innerHTML = '';
    cases.forEach((c) => {
      const opt = document.createElement('option');
      opt.value = c.case_id;
      const condClean = c.condition.replace('condition_', '').toUpperCase();
      opt.textContent = `[${c.case_id}] Condition ${condClean} • ${c.site_id} • ${c.urgency} (${c.patient_language.toUpperCase()})`;
      selector.appendChild(opt);
    });

    if (cases.length > 0) {
      currentCaseId = cases[0].case_id;
      selector.value = currentCaseId;
      evaluateSelectedCase();
    }
  } catch (err) {
    console.error("Failed to load synthetic cases:", err);
    selector.innerHTML = '<option value="">Error loading cases from server</option>';
  }
}

/**
 * Setup UI event listeners.
 */
function setupEventListeners() {
  const selector = document.getElementById('case-selector');
  selector.addEventListener('change', (e) => {
    currentCaseId = e.target.value;
    simulateExhaustion = false;
    updateSimulationButtonState();
    evaluateSelectedCase();
  });
}

/**
 * Set active language ('en' or 'ta').
 */
function setLanguage(lang) {
  if (currentLang === lang) return;
  currentLang = lang;
  document.body.setAttribute('data-lang', lang);

  // Update button active state
  document.getElementById('lang-btn-en').classList.toggle('active', lang === 'en');
  document.getElementById('lang-btn-en').setAttribute('aria-pressed', lang === 'en');
  document.getElementById('lang-btn-ta').classList.toggle('active', lang === 'ta');
  document.getElementById('lang-btn-ta').setAttribute('aria-pressed', lang === 'ta');

  // Update static UI dictionary text
  applyLocalizationText();

  // Re-evaluate current case in new language
  evaluateSelectedCase();
}

/**
 * Apply localized strings across DOM elements.
 */
function applyLocalizationText() {
  const t = UI_STRINGS[currentLang];

  document.getElementById('header-app-title').textContent = t.appTitle;
  document.getElementById('header-subtitle-text').textContent = t.appSubtitle;
  document.getElementById('governance-text').textContent = t.governanceDisclaimer;
  document.getElementById('label-select-case').textContent = t.selectCaseLabel;
  document.getElementById('btn-re-evaluate-text').textContent = t.btnEvaluate;
  
  updateSimulationButtonState();

  // Headings
  document.getElementById('heading-patient-section').textContent = t.headingPatient;
  document.getElementById('heading-resource-section').textContent = t.headingResources;
  document.getElementById('heading-recommendation-section').textContent = t.headingRecommendation;
  document.getElementById('heading-followup-section').textContent = t.headingFollowup;

  // Patient Labels
  document.getElementById('label-case-id').textContent = t.labelCaseId;
  document.getElementById('label-condition').textContent = t.labelCondition;
  document.getElementById('label-age-band').textContent = t.labelAgeBand;
  document.getElementById('label-pop-group').textContent = t.labelPopGroup;
  document.getElementById('label-patient-lang').textContent = t.labelPatientLang;
  document.getElementById('label-site').textContent = t.labelSite;

  // Resource Labels
  document.getElementById('label-equipment').textContent = t.labelEquipment;
  document.getElementById('label-medications').textContent = t.labelMedications;
  document.getElementById('label-specialists').textContent = t.labelSpecialists;
  document.getElementById('label-transport').textContent = t.labelTransport;
  document.getElementById('label-connectivity').textContent = t.labelConnectivity;
  document.getElementById('label-cold-chain').textContent = t.labelColdChain;
  document.getElementById('label-interpreter').textContent = t.labelInterpreter;

  // Recommendation Labels
  document.getElementById('label-transparent-trail').textContent = t.labelTransparentTrail;
  document.getElementById('trail-help-text').textContent = t.trailHelpText;
  document.getElementById('label-blocked-options-title').textContent = t.labelBlockedOptions;

  // Follow-up Labels
  document.getElementById('label-followup-owner').textContent = t.labelFollowupOwner;
  document.getElementById('label-followup-due').textContent = t.labelFollowupDue;
  document.getElementById('label-followup-path').textContent = t.labelFollowupPath;
  document.getElementById('label-followup-desc').textContent = t.labelFollowupDesc;

  // Footers
  document.getElementById('footer-governance').innerHTML = t.footerGovernance;
  document.getElementById('footer-synthetic').innerHTML = t.footerSynthetic;
}

/**
 * Toggle simulation of option exhaustion to verify immediate escalation alert.
 */
function toggleSimulatedExhaustion() {
  simulateExhaustion = !simulateExhaustion;
  updateSimulationButtonState();
  evaluateSelectedCase();
}

function updateSimulationButtonState() {
  const t = UI_STRINGS[currentLang];
  const btnText = document.getElementById('btn-sim-escalation-text');
  const btn = document.getElementById('btn-test-escalation');
  
  if (simulateExhaustion) {
    btnText.textContent = t.btnRevertExhaustion;
    btn.classList.add('active-sim');
  } else {
    btnText.textContent = t.btnSimExhaustion;
    btn.classList.remove('active-sim');
  }
}

/**
 * Execute evaluation for selected case via POST /recommendations/{case_id}.
 */
async function evaluateSelectedCase() {
  if (!currentCaseId) return;

  const url = `/recommendations/${currentCaseId}?lang=${currentLang}&simulate_exhaustion=${simulateExhaustion}`;

  try {
    const res = await fetch(url, { method: 'POST' });
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    const data = await res.json();

    renderDashboard(data);
  } catch (err) {
    console.error("Evaluation request failed:", err);
  }
}

/**
 * Render all dashboard sections from evaluation response.
 */
function renderDashboard(data) {
  renderPatientSection(data.patient_summary, data.urgency);
  renderResourceSection(data.site_resources);
  renderRecommendationSection(data);
  renderFollowupSection(data.follow_up);
  renderSafetyAlerts(data);
}

/**
 * 1. Render Patient Profile Card
 */
function renderPatientSection(patient, urgency) {
  document.getElementById('patient-case-id').textContent = patient.case_id;
  document.getElementById('patient-condition').textContent = formatConditionName(patient.condition);
  document.getElementById('patient-age-band').textContent = patient.age_band;
  document.getElementById('patient-population-group').textContent = capitalize(patient.population_group);
  
  const langDisplay = patient.patient_language.toLowerCase() === 'ta' ? 'Tamil (ta / தமிழ்)' : 'English (en)';
  document.getElementById('patient-language-val').textContent = langDisplay;
  document.getElementById('patient-site-name').textContent = `${patient.site_name} (${patient.site_id})`;

  // Urgency Badge
  const urgencyBadge = document.getElementById('patient-urgency-badge');
  urgencyBadge.textContent = urgency.toUpperCase();
  urgencyBadge.className = 'badge badge-urgency';
  
  const urgLower = urgency.toLowerCase();
  if (urgLower === 'critical') urgencyBadge.classList.add('badge-urgency-critical');
  else if (urgLower === 'high') urgencyBadge.classList.add('badge-urgency-high');
  else if (urgLower === 'medium') urgencyBadge.classList.add('badge-urgency-medium');
  else urgencyBadge.classList.add('badge-urgency-low');
}

/**
 * 2. Render Facility Resources Card
 */
function renderResourceSection(site) {
  document.getElementById('site-tier-badge').textContent = site.clinic_tier;

  // Equipment Chips
  const eqContainer = document.getElementById('equipment-list');
  eqContainer.innerHTML = '';
  if (site.equipment && site.equipment.length > 0) {
    site.equipment.forEach((item) => {
      const chip = document.createElement('span');
      chip.className = 'res-chip';
      chip.textContent = formatResourceName(item);
      eqContainer.appendChild(chip);
    });
  } else {
    eqContainer.innerHTML = '<span class="empty-state">No specialized equipment present</span>';
  }

  // Medication Chips
  const medContainer = document.getElementById('medication-list');
  medContainer.innerHTML = '';
  if (site.medication_stock && site.medication_stock.length > 0) {
    site.medication_stock.forEach((item) => {
      const chip = document.createElement('span');
      chip.className = 'res-chip';
      chip.textContent = formatResourceName(item);
      medContainer.appendChild(chip);
    });
  } else {
    medContainer.innerHTML = '<span class="empty-state">Dispensary stock empty</span>';
  }

  // Logistics
  document.getElementById('specialists-val').textContent =
    site.specialists && site.specialists.length > 0
      ? site.specialists.map(formatResourceName).join(', ')
      : (currentLang === 'ta' ? 'கிடைக்கவில்லை' : 'None on site');

  document.getElementById('transport-val').textContent = site.transport_available
    ? (currentLang === 'ta' ? 'அவசர ஆம்புலன்ஸ் உள்ளது' : 'Ambulance On-Duty')
    : (currentLang === 'ta' ? 'கிடைக்கவில்லை' : 'Unavailable locally');

  document.getElementById('connectivity-val').textContent = site.connectivity;

  document.getElementById('cold-chain-val').textContent = site.cold_chain_available
    ? (currentLang === 'ta' ? 'குளிர்பதன வசதி இயங்குகிறது (2°C - 8°C)' : 'Operational (2°C - 8°C)')
    : (currentLang === 'ta' ? 'கிடைக்கவில்லை' : 'Unavailable');

  const interpLangs = site.interpreter_languages && site.interpreter_languages.length > 0
    ? site.interpreter_languages.join(', ').toUpperCase()
    : 'None';
  document.getElementById('interpreter-val').textContent =
    `${site.supported_languages.join(', ').toUpperCase()} (Interpreters: ${interpLangs})`;
}

/**
 * 3. Render Recommendation Card & Transparent Reason Trail
 */
function renderRecommendationSection(data) {
  const t = UI_STRINGS[currentLang];

  // Hero Care Option
  document.getElementById('selected-care-option-text').textContent = data.selected_care_option;

  // Feasibility and Escalation tags
  const feasTag = document.getElementById('feasibility-status-tag');
  feasTag.textContent = data.feasible ? t.statusFeasible : t.statusInfeasible;
  feasTag.style.color = data.feasible ? 'var(--accent-emerald)' : 'var(--accent-rose)';

  const escTag = document.getElementById('escalation-requirement-tag');
  escTag.textContent = data.escalation_required ? t.escalationMandatory : t.noEscalation;
  escTag.style.color = data.escalation_required ? 'var(--accent-rose)' : 'var(--text-secondary)';

  // Ladder Level Pill
  const pill = document.getElementById('ladder-level-pill');
  pill.className = 'ladder-pill';
  
  const level = (data.ladder_level || 'escalate_only').toLowerCase();
  if (level.includes('preferred')) {
    pill.classList.add('ladder-preferred');
    pill.textContent = currentLang === 'ta' ? 'விருப்பமான தேர்வு' : 'Preferred (Gold Standard)';
  } else if (level.includes('adapted')) {
    pill.classList.add('ladder-adapted');
    pill.textContent = currentLang === 'ta' ? 'வள-தழுவிய மாற்று' : 'Resource-Adapted Alternative';
  } else if (level.includes('fallback')) {
    pill.classList.add('ladder-fallback');
    pill.textContent = currentLang === 'ta' ? 'பாதுகாப்பான வழி' : 'Minimum-Safe Fallback';
  } else {
    pill.classList.add('ladder-escalate');
    pill.textContent = currentLang === 'ta' ? 'அவசர மேலனுப்பல்' : 'Immediate Escalation Only';
  }

  // Render Transparent Reason Trail with ✓ / ✗ / ★
  const stepsContainer = document.getElementById('reason-steps-container');
  stepsContainer.innerHTML = '';

  if (data.reason_steps && data.reason_steps.length > 0) {
    data.reason_steps.forEach((step) => {
      const stepRow = document.createElement('div');
      stepRow.className = 'reason-step-item';

      const iconSpan = document.createElement('span');
      iconSpan.className = 'step-icon';

      if (step.status === 'available') {
        iconSpan.classList.add('step-icon-available');
        iconSpan.textContent = '✓';
      } else if (step.status === 'unavailable' || step.status === 'blocked') {
        iconSpan.classList.add('step-icon-unavailable');
        iconSpan.textContent = '✗';
      } else {
        iconSpan.classList.add('step-icon-selected');
        iconSpan.textContent = '★';
      }

      const textSpan = document.createElement('span');
      textSpan.className = 'step-text';
      if (step.status === 'selected') {
        textSpan.classList.add('step-decision');
      }
      textSpan.textContent = step.text;

      stepRow.appendChild(iconSpan);
      stepRow.appendChild(textSpan);
      stepsContainer.appendChild(stepRow);
    });
  }

  // Blocked Tiers Callout
  const blockedCallout = document.getElementById('blocked-options-callout');
  const blockedList = document.getElementById('blocked-options-list');
  blockedList.innerHTML = '';

  const blockedKeys = Object.keys(data.blocked_options || {});
  if (blockedKeys.length > 0) {
    blockedCallout.classList.remove('hidden');
    blockedKeys.forEach((key) => {
      const li = document.createElement('li');
      const reasons = data.blocked_options[key].join('; ');
      li.textContent = `[${key.toUpperCase()}]: ${reasons}`;
      blockedList.appendChild(li);
    });
  } else {
    blockedCallout.classList.add('hidden');
  }
}

/**
 * 4. Render Accountable Follow-Up Card
 */
function renderFollowupSection(fup) {
  document.getElementById('followup-owner-val').textContent = fup.owner;
  
  // Format due date nicely
  try {
    const d = new Date(fup.due_at);
    document.getElementById('followup-due-val').textContent = `${d.toLocaleString()} (${fup.due_at})`;
  } catch {
    document.getElementById('followup-due-val').textContent = fup.due_at;
  }

  // Status Badge
  const statusBadge = document.getElementById('followup-status-badge');
  statusBadge.textContent = fup.status;

  // Escalation Path Steps
  const pathContainer = document.getElementById('followup-path-steps');
  pathContainer.innerHTML = '';

  if (fup.escalation_path && fup.escalation_path.length > 0) {
    fup.escalation_path.forEach((node, idx) => {
      const nodeSpan = document.createElement('span');
      nodeSpan.className = 'escalation-node';
      nodeSpan.textContent = `${idx + 1}. ${node}`;
      pathContainer.appendChild(nodeSpan);

      if (idx < fup.escalation_path.length - 1) {
        const arrow = document.createElement('span');
        arrow.className = 'escalation-arrow';
        arrow.textContent = '→';
        pathContainer.appendChild(arrow);
      }
    });
  } else {
    pathContainer.innerHTML = '<span class="empty-state">No escalation ladder assigned</span>';
  }

  document.getElementById('followup-description-val').textContent = fup.description;
}

/**
 * 5. Render High-Contrast Safety Alert Banners
 */
function renderSafetyAlerts(data) {
  const container = document.getElementById('safety-alerts-container');
  container.innerHTML = '';
  const t = UI_STRINGS[currentLang];

  // Check condition 1: ESCALATE IMMEDIATELY (no feasible local option or simulated exhaustion)
  if (data.escalate_immediately) {
    const banner = document.createElement('div');
    banner.className = 'safety-banner safety-banner-escalate';
    banner.innerHTML = `
      <div class="safety-banner-icon">🚨</div>
      <div>
        <div class="banner-title">${t.bannerEscalateTitle}</div>
        <div class="banner-msg">${data.safety_banner_message || t.bannerEscalateMsg}</div>
      </div>
    `;
    container.appendChild(banner);
  }

  // Check condition 2: LANGUAGE ESCALATION REQUIRED (patient language cannot be communicated)
  if (data.language_escalation_required) {
    const banner = document.createElement('div');
    banner.className = 'safety-banner safety-banner-language';
    banner.innerHTML = `
      <div class="safety-banner-icon">🗣️</div>
      <div>
        <div class="banner-title">${t.bannerLanguageTitle}</div>
        <div class="banner-msg">${data.safety_banner_message || t.bannerLanguageMsg}</div>
      </div>
    `;
    container.appendChild(banner);
  }
}

// Helpers
function capitalize(str) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

function formatConditionName(cond) {
  if (!cond) return '—';
  return cond.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function formatResourceName(item) {
  if (!item) return '';
  return item.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}
