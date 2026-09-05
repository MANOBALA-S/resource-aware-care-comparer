/**
 * Resource-Aware Care Option Comparer — Follow-Up Queue UI Logic
 * Health Worker / Clinical Coordinator Dashboard
 * 
 * Invariants:
 * - No silent disappearance: Tasks remain in Active Queue until COMPLETED.
 * - Completed tasks disappear from Active Queue but remain in Historical Records.
 * - Visually obvious OVERDUE, ESCALATED, and ESCALATION CONFIGURATION ERROR badges.
 * 
 * Synthetic data only — no real patient data.
 * Decision-support prototype — clinician sign-off required.
 */

// State
let allTasks = [];
let casesMap = {}; // case_id -> { site_id, patient_language, condition }
let activeTaskId = null;

document.addEventListener('DOMContentLoaded', () => {
  initDashboard();
});

async function initDashboard() {
  await loadCasesMetadata();
  await loadFollowups();
}

/**
 * Fetch cases metadata to associate site_id and patient_language with each follow-up.
 */
async function loadCasesMetadata() {
  try {
    const res = await fetch('/cases');
    if (res.ok) {
      const cases = await res.json();
      cases.forEach((c) => {
        casesMap[c.case_id] = {
          site_id: c.site_id,
          patient_language: c.patient_language,
          condition: c.condition,
          urgency: c.urgency,
        };
      });
    }
  } catch (err) {
    console.warn("Could not load cases metadata for enrichment:", err);
  }
}

/**
 * Load all follow-up tasks from backend and update summary and queue table.
 */
async function loadFollowups() {
  try {
    const res = await fetch('/followups');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    allTasks = await res.json();

    updateKPISummaries();
    applyFilters();
  } catch (err) {
    console.error("Failed to load follow-up tasks:", err);
    document.getElementById('queue-table-body').innerHTML = `
      <tr><td colspan="8" class="table-loading" style="color: #f87171;">Failed to load follow-ups from backend server.</td></tr>
    `;
  }
}

/**
 * Update the 5 KPI summary metric counters.
 */
function updateKPISummaries() {
  const total = allTasks.length;
  const pending = allTasks.filter(t => t.status === 'PENDING' || t.status === 'IN_PROGRESS').length;
  const overdue = allTasks.filter(t => t.status === 'OVERDUE' || isOverdue(t.due_at, t.status)).length;
  const escalated = allTasks.filter(t => t.status === 'ESCALATED' || t.escalation_status === 'ESCALATED').length;
  const completed = allTasks.filter(t => t.status === 'COMPLETED').length;

  document.getElementById('kpi-total-val').textContent = total;
  document.getElementById('kpi-pending-val').textContent = pending;
  document.getElementById('kpi-overdue-val').textContent = overdue;
  document.getElementById('kpi-escalated-val').textContent = escalated;
  document.getElementById('kpi-completed-val').textContent = completed;
}

/**
 * Filter tasks according to toolbar selections and render table rows.
 */
function applyFilters() {
  const scope = document.getElementById('filter-scope').value;
  const urgency = document.getElementById('filter-urgency').value;
  const statusFilter = document.getElementById('filter-status').value;
  const site = document.getElementById('filter-site').value;
  const lang = document.getElementById('filter-language').value;
  const overdueOnly = document.getElementById('toggle-overdue-only').checked;
  const escalatedOnly = document.getElementById('toggle-escalated-only').checked;
  const searchText = document.getElementById('search-input').value.trim().toLowerCase();

  const filtered = allTasks.filter((task) => {
    // 1. Scope filter: "No Silent Disappearance" invariant
    // Active Queue hides COMPLETED tasks.
    if (scope === 'active' && task.status === 'COMPLETED') {
      return false;
    }
    if (scope === 'completed' && task.status !== 'COMPLETED') {
      return false;
    }

    // 2. Urgency filter
    if (urgency !== 'ALL' && task.urgency !== urgency) {
      return false;
    }

    // 3. Status filter
    if (statusFilter !== 'ALL' && task.status !== statusFilter) {
      return false;
    }

    // 4. Site filter
    const caseMeta = casesMap[task.case_id] || {};
    if (site !== 'ALL' && caseMeta.site_id !== site) {
      return false;
    }

    // 5. Language filter
    if (lang !== 'ALL' && caseMeta.patient_language !== lang) {
      return false;
    }

    // 6. Overdue toggle
    if (overdueOnly && task.status !== 'OVERDUE' && !isOverdue(task.due_at, task.status)) {
      return false;
    }

    // 7. Escalated toggle
    if (escalatedOnly && task.status !== 'ESCALATED' && task.escalation_status !== 'ESCALATED') {
      return false;
    }

    // 8. Text search
    if (searchText) {
      const matchCase = task.case_id.toLowerCase().includes(searchText);
      const matchOwner = task.owner.toLowerCase().includes(searchText);
      const matchDesc = task.description.toLowerCase().includes(searchText);
      const matchType = task.task_type.toLowerCase().includes(searchText);
      if (!matchCase && !matchOwner && !matchDesc && !matchType) {
        return false;
      }
    }

    return true;
  });

  renderQueueTable(filtered);
}

/**
 * Render table rows into tbody.
 */
function renderQueueTable(tasks) {
  const tbody = document.getElementById('queue-table-body');
  document.getElementById('queue-count-badge').textContent = `${tasks.length} Tasks`;

  if (tasks.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" class="table-loading">No follow-up tasks match the selected filters.</td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = '';
  tasks.forEach((task) => {
    const tr = document.createElement('tr');
    
    // Row classes
    const overdue = task.status === 'OVERDUE' || isOverdue(task.due_at, task.status);
    if (overdue && task.status !== 'COMPLETED') {
      tr.classList.add('row-overdue');
    } else if (task.status === 'ESCALATED' || task.escalation_status === 'ESCALATED') {
      tr.classList.add('row-escalated');
    } else if (task.status === 'COMPLETED') {
      tr.classList.add('row-completed');
    }

    const caseMeta = casesMap[task.case_id] || { site_id: 'SITE-UNKNOWN', patient_language: '—' };

    // 1. Case ID Cell
    const tdCase = document.createElement('td');
    tdCase.innerHTML = `
      <div class="case-cell">
        <span class="case-id-text">${task.case_id}</span>
        <span class="case-subtext">${caseMeta.site_id} • ${caseMeta.patient_language.toUpperCase()}</span>
      </div>
    `;
    tr.appendChild(tdCase);

    // 2. Task Cell
    const tdTask = document.createElement('td');
    tdTask.innerHTML = `
      <div class="task-cell">
        <span class="task-type-badge">${formatTaskType(task.task_type)}</span>
        <div class="task-desc-text" title="${escapeHtml(task.description)}">${escapeHtml(task.description)}</div>
      </div>
    `;
    tr.appendChild(tdTask);

    // 3. Urgency Cell
    const tdUrg = document.createElement('td');
    const urgClass = `badge-urg-${task.urgency.toLowerCase()}`;
    tdUrg.innerHTML = `<span class="badge ${urgClass}">${task.urgency}</span>`;
    tr.appendChild(tdUrg);

    // 4. Owner Cell
    const tdOwner = document.createElement('td');
    tdOwner.innerHTML = `<strong>${escapeHtml(task.owner)}</strong>`;
    tr.appendChild(tdOwner);

    // 5. Due Date Cell
    const tdDue = document.createElement('td');
    const relDue = getRelativeTimeString(task.due_at, task.status);
    tdDue.innerHTML = `
      <div class="due-cell">
        <span class="due-time-text">${formatShortDate(task.due_at)}</span>
        <span class="due-relative-badge ${relDue.isBreached ? 'breached' : 'active'}">${relDue.text}</span>
      </div>
    `;
    tr.appendChild(tdDue);

    // 6. Status Cell
    const tdStatus = document.createElement('td');
    tdStatus.appendChild(renderStatusBadge(task.status, overdue));
    tr.appendChild(tdStatus);

    // 7. Escalation Cell
    const tdEsc = document.createElement('td');
    tdEsc.appendChild(renderEscalationBadge(task));
    tr.appendChild(tdEsc);

    // 8. Actions Cell
    const tdActions = document.createElement('td');
    tdActions.className = 'actions-cell';

    // View Button
    const btnView = document.createElement('button');
    btnView.className = 'btn-action btn-act-view';
    btnView.textContent = 'View';
    btnView.onclick = () => openTaskModal(task);
    tdActions.appendChild(btnView);

    // Start Button (if PENDING)
    if (task.status === 'PENDING') {
      const btnStart = document.createElement('button');
      btnStart.className = 'btn-action btn-act-start';
      btnStart.textContent = 'Start';
      btnStart.onclick = () => startTask(task.follow_up_id);
      tdActions.appendChild(btnStart);
    }

    // Complete Button (if not COMPLETED)
    if (task.status !== 'COMPLETED') {
      const btnComplete = document.createElement('button');
      btnComplete.className = 'btn-action btn-act-complete';
      btnComplete.textContent = 'Complete';
      btnComplete.onclick = () => completeTask(task.follow_up_id);
      tdActions.appendChild(btnComplete);
    }

    // Escalate Button (if not COMPLETED)
    if (task.status !== 'COMPLETED') {
      const btnEscalate = document.createElement('button');
      btnEscalate.className = 'btn-action btn-act-escalate';
      btnEscalate.textContent = 'Escalate';
      btnEscalate.onclick = () => escalateTask(task.follow_up_id);
      tdActions.appendChild(btnEscalate);
    }

    tr.appendChild(tdActions);
    tbody.appendChild(tr);
  });
}

/**
 * Render visual status badge.
 */
function renderStatusBadge(status, isOverdue) {
  const span = document.createElement('span');
  span.className = 'badge';

  if (status === 'OVERDUE' || (isOverdue && status !== 'COMPLETED')) {
    span.classList.add('badge-status-overdue');
    span.textContent = 'OVERDUE';
  } else if (status === 'ESCALATED') {
    span.classList.add('badge-status-escalated');
    span.textContent = 'ESCALATED';
  } else if (status === 'COMPLETED') {
    span.classList.add('badge-status-completed');
    span.textContent = 'COMPLETED';
  } else if (status === 'IN_PROGRESS') {
    span.classList.add('badge-status-inprogress');
    span.textContent = 'IN PROGRESS';
  } else {
    span.classList.add('badge-status-pending');
    span.textContent = 'PENDING';
  }

  return span;
}

/**
 * Render visual escalation badge: ESCALATED / ESCALATION CONFIGURATION ERROR / NOT_REQUIRED.
 */
function renderEscalationBadge(task) {
  const span = document.createElement('span');
  span.className = 'badge';

  if (task.escalation_status === 'ESCALATION_FAILED') {
    span.classList.add('badge-esc-failed');
    span.textContent = '⚠️ ESCALATION CONFIGURATION ERROR';
    span.title = 'Escalation path is missing or contact could not be resolved.';
  } else if (task.escalation_status === 'ESCALATED' || task.status === 'ESCALATED') {
    span.classList.add('badge-esc-active');
    span.textContent = 'ESCALATED';
    span.title = task.escalation_reason || 'Active escalation';
  } else {
    span.classList.add('badge-esc-none');
    span.textContent = 'Not Required';
  }

  return span;
}

/* ==========================================================================
   Task Actions (Start, Complete, Escalate) calling Phase 5 Backend APIs
   ========================================================================== */

/**
 * Start task: update status to IN_PROGRESS.
 */
async function startTask(followUpId) {
  try {
    const res = await fetch(`/followups/${followUpId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'IN_PROGRESS' }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    await loadFollowups();
  } catch (err) {
    alert(`Failed to start task: ${err.message}`);
  }
}

/**
 * Complete task: calls POST /followups/{id}/complete.
 */
async function completeTask(followUpId) {
  try {
    const res = await fetch(`/followups/${followUpId}/complete`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    await loadFollowups();
  } catch (err) {
    alert(`Failed to complete task: ${err.message}`);
  }
}

/**
 * Escalate task: calls POST /followups/{id}/escalate.
 */
async function escalateTask(followUpId) {
  const reason = prompt("Enter escalation rationale:", "Manual clinical/operational escalation initiated by coordinator.");
  if (reason === null) return; // cancelled

  try {
    const res = await fetch(`/followups/${followUpId}/escalate?reason=${encodeURIComponent(reason)}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    await loadFollowups();
  } catch (err) {
    alert(`Escalation request failed: ${err.message}`);
  }
}

/**
 * Run scheduler overdue check: calls POST /followups/check-overdue.
 */
async function triggerOverdueCheck() {
  const btn = document.getElementById('btn-run-scheduler');
  const origText = btn.innerHTML;
  btn.innerHTML = 'Checking SLAs...';
  btn.disabled = true;

  try {
    const res = await fetch('/followups/check-overdue', { method: 'POST' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const summary = await res.json();
    
    await loadFollowups();
    alert(`SLA Check Complete:\n- Tasks Checked: ${summary.total_checked || 0}\n- Newly Overdue: ${summary.overdue_count || 0}\n- Newly Escalated: ${summary.escalated_count || 0}`);
  } catch (err) {
    alert(`SLA check failed: ${err.message}`);
  } finally {
    btn.innerHTML = origText;
    btn.disabled = false;
  }
}

/* ==========================================================================
   Detail Modal & Audit Log Timeline
   ========================================================================== */
async function openTaskModal(task) {
  activeTaskId = task.follow_up_id;
  const modal = document.getElementById('task-modal');
  modal.classList.remove('hidden');

  document.getElementById('modal-task-id').textContent = task.follow_up_id;
  document.getElementById('modal-case-id').textContent = task.case_id;
  document.getElementById('modal-urgency').textContent = task.urgency;
  document.getElementById('modal-owner').textContent = task.owner;
  document.getElementById('modal-status').textContent = task.status;
  document.getElementById('modal-due-at').textContent = new Date(task.due_at).toLocaleString();
  document.getElementById('modal-esc-due-at').textContent = new Date(task.escalation_due_at).toLocaleString();
  document.getElementById('modal-instructions').textContent = task.description;

  // Render Ladder
  const ladderContainer = document.getElementById('modal-escalation-ladder');
  ladderContainer.innerHTML = '';
  if (task.escalation_path && task.escalation_path.length > 0) {
    task.escalation_path.forEach((role, idx) => {
      const node = document.createElement('span');
      node.className = 'escalation-node';
      node.textContent = `${idx + 1}. ${role}`;
      ladderContainer.appendChild(node);
      if (idx < task.escalation_path.length - 1) {
        const arrow = document.createElement('span');
        arrow.className = 'escalation-arrow';
        arrow.textContent = ' → ';
        ladderContainer.appendChild(arrow);
      }
    });
  } else {
    ladderContainer.innerHTML = '<span class="empty-state">No escalation ladder configured</span>';
  }

  // Fetch and Render Audit Log
  const timeline = document.getElementById('modal-audit-timeline');
  timeline.innerHTML = '<span class="empty-state">Loading chronological audit events...</span>';

  try {
    const res = await fetch(`/followups/${task.follow_up_id}/escalations`);
    if (res.ok) {
      const events = await res.json();
      if (events.length === 0) {
        timeline.innerHTML = '<span class="empty-state">No audit events recorded yet.</span>';
      } else {
        timeline.innerHTML = '';
        events.forEach((ev) => {
          const item = document.createElement('div');
          item.className = 'audit-event-item';
          item.innerHTML = `
            <div class="audit-timestamp">${new Date(ev.event_timestamp).toLocaleTimeString()}</div>
            <div class="audit-desc">
              <strong>${ev.event_type}</strong>: ${escapeHtml(ev.reason)} (Owner: ${escapeHtml(ev.owner)})
            </div>
          `;
          timeline.appendChild(item);
        });
      }
    }
  } catch (err) {
    timeline.innerHTML = '<span class="empty-state">Could not retrieve audit history.</span>';
  }
}

function closeModal() {
  document.getElementById('task-modal').classList.add('hidden');
  activeTaskId = null;
}

function clearFilters() {
  document.getElementById('filter-scope').value = 'active';
  document.getElementById('filter-urgency').value = 'ALL';
  document.getElementById('filter-status').value = 'ALL';
  document.getElementById('filter-site').value = 'ALL';
  document.getElementById('filter-language').value = 'ALL';
  document.getElementById('toggle-overdue-only').checked = false;
  document.getElementById('toggle-escalated-only').checked = false;
  document.getElementById('search-input').value = '';
  applyFilters();
}

/* ==========================================================================
   Utility Helpers
   ========================================================================== */
function isOverdue(dueAtStr, status) {
  if (status === 'COMPLETED') return false;
  try {
    return new Date(dueAtStr) < new Date();
  } catch {
    return false;
  }
}

function getRelativeTimeString(dueAtStr, status) {
  if (status === 'COMPLETED') return { text: 'Completed', isBreached: false };
  try {
    const diffMs = new Date(dueAtStr) - new Date();
    const diffHours = Math.round(diffMs / (1000 * 60 * 60));
    if (diffMs < 0) {
      return { text: `${Math.abs(diffHours)}h Overdue`, isBreached: true };
    } else {
      return { text: `In ${diffHours}h`, isBreached: false };
    }
  } catch {
    return { text: '—', isBreached: false };
  }
}

function formatShortDate(isoStr) {
  try {
    const d = new Date(isoStr);
    return `${d.getMonth() + 1}/${d.getDate()} ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
  } catch {
    return isoStr;
  }
}

function formatTaskType(t) {
  return t ? t.replace(/_/g, ' ').toUpperCase() : 'TASK';
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
