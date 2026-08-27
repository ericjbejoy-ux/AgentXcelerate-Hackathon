/* ============================================================
   AutoSCM — Autonomous SCM Frontend
   ============================================================ */

const API_BASE = "http://localhost:5555";

const STORAGE_KEYS = { users: "ax_users", currentUser: "ax_current_user" };

const partCatalog = {
  Hydraulics: [
    { name: "Hydraulic Pump", id: "HYD-1001" },
    { name: "Hydraulic Cylinder", id: "HYD-1002" },
    { name: "Hydraulic Hose", id: "HYD-1003" },
    { name: "Hydraulic Valve", id: "HYD-1004" },
    { name: "Pressure Relief Valve", id: "HYD-1005" },
  ],
  Electronic: [
    { name: "Control Module", id: "ELE-2001" },
    { name: "Electronic Sensor", id: "ELE-2002" },
    { name: "Relay Module", id: "ELE-2003" },
    { name: "Ignition Controller", id: "ELE-2004" },
    { name: "Voltage Regulator", id: "ELE-2005" },
  ],
  Fasteners: [
    { name: "Hex Bolt Set", id: "FAS-3001" },
    { name: "Lock Nut Set", id: "FAS-3002" },
    { name: "Mounting Screw Set", id: "FAS-3003" },
    { name: "Threaded Rod", id: "FAS-3004" },
    { name: "Retaining Ring Set", id: "FAS-3005" },
  ],
  Filters: [
    { name: "Hydraulic Filter", id: "FIL-4001" },
    { name: "Oil Filter", id: "FIL-4002" },
    { name: "Air Filter", id: "FIL-4003" },
    { name: "Fuel Filter", id: "FIL-4004" },
    { name: "Return Line Filter", id: "FIL-4005" },
  ],
};

const demoUsers = [
  { role: "Buyer", name: "Arjun Mehta", email: "buyer@demo.com", password: "buyer123", company: "Mumbai Industrial Corp", customerId: "CUST-101" },
  { role: "Seller", name: "Priya Sharma", email: "seller@demo.com", password: "seller123", company: "Hyderabad Parts Supply", customerId: "CUST-SELLER-001" },
];

function seedUsers() { if (!localStorage.getItem(STORAGE_KEYS.users)) localStorage.setItem(STORAGE_KEYS.users, JSON.stringify(demoUsers)); }
function getUsers() { return JSON.parse(localStorage.getItem(STORAGE_KEYS.users) || "[]"); }
function saveUsers(u) { localStorage.setItem(STORAGE_KEYS.users, JSON.stringify(u)); }
function getCurrentUser() { return JSON.parse(localStorage.getItem(STORAGE_KEYS.currentUser) || "null"); }
function saveCurrentUser(u) { localStorage.setItem(STORAGE_KEYS.currentUser, JSON.stringify(u)); }
seedUsers();

let currentOrderId = null;
let currentTraceId = null;

// ── DOM ────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const form = $("order-form");
const categorySelect = $("category");
const partNameSelect = $("partName");
const partIdInput = $("partId");
const customerIdInput = $("customerId");
const welcomeScreen = $("welcomeScreen");
const welcomeTitle = $("welcomeTitle");
const welcomeContinue = $("welcomeContinue");
const dashboardPage = $("dashboardPage");
const connectionStatus = $("connectionStatus");
const connectionLabel = $("connectionLabel");
const submitBtn = $("submitBtn");
const submitBtnText = $("submitBtnText");
const submitSpinner = $("submitSpinner");
const winnerCard = $("winnerCard");
const explanationBlock = $("explanationBlock");
const explanationText = $("explanationText");
const candidatesSection = $("candidatesSection");
const candidatesTableBody = $("candidatesTableBody");
const candidatesTableWrap = $("candidatesSection");
const inventoryStats = $("inventoryStats");
const inventoryTableBody = $("inventoryTableBody");
const historyTableBody = $("historyTableBody");
const analyticsSummary = $("analyticsSummary");
const priorityChart = $("priorityChart");
const categoryChart = $("categoryChart");
const strategyChart = $("strategyChart");
const warehouseChart = $("warehouseChart");
const recentOrders = $("recentOrders");
const authModal = $("authModal");
const orderLayout = $("orderLayout");
const pipeline = $("pipeline");
const pipelineAgents = $("pipelineAgents");
const resultsPanel = $("resultsPanel");
const closeAuthModalButton = $("closeAuthModal");
const authPanel = $("authPanel");
const authForm = $("authForm");
const authSubmitButton = $("authSubmitButton");
const toggleAuthModeButton = $("toggleAuthMode");
const authError = $("authError");
const authRoleBadge = $("authRoleBadge");
const authModalTitle = $("authModalTitle");
const authModalText = $("authModalText");
const demoCredentials = $("demoCredentials");
const authEmailInput = $("authEmail");
const authPasswordInput = $("authPassword");
const authNameInput = $("authName");
const authCompanyInput = $("authCompany");
const nameField = $("nameField");
const companyField = $("companyField");
const roleTabs = document.querySelectorAll("[data-role-select]");
const navTabs = document.querySelectorAll(".nav-tab");
const userAvatar = $("userAvatar");
const userName = $("userName");
const logoutBtn = $("logoutBtn");
const demoAutofillButtons = document.querySelectorAll(".demo-autofill");

let authState = { role: "Buyer", mode: "login" };

// ── Validation ─────────────────────────────────────────────
const fieldConfig = [
  { id: "category", validate: v => v.trim() !== "", message: "Select a category." },
  { id: "partName", validate: v => v.trim() !== "", message: "Select a part." },
  { id: "partId", validate: v => v.trim() !== "", message: "Part ID required." },
  { id: "requestedQuantity", validate: v => Number.isInteger(Number(v)) && Number(v) > 0, message: "Must be a positive whole number." },
  { id: "leadTime", validate: v => Number.isInteger(Number(v)) && Number(v) > 0, message: "Must be a positive whole number." },
  { id: "priorityLevel", validate: v => ["Low", "Medium", "High", "Critical"].includes(v), message: "Select a priority." },
];

function setFieldError(fieldId, message) {
  const input = $(fieldId);
  const err = $(`${fieldId}Error`);
  if (input) input.classList.toggle("input-error", Boolean(message));
  if (err) err.textContent = message;
}
function clearErrors() { fieldConfig.forEach(f => setFieldError(f.id, "")); }
function validateForm(formData) {
  let ok = true;
  fieldConfig.forEach(f => {
    const v = formData.get(f.id) || "";
    if (!f.validate(v)) { ok = false; setFieldError(f.id, f.message); }
  });
  return ok;
}

// ── Health check ───────────────────────────────────────────
async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/health`, { signal: AbortSignal.timeout(3000) });
    if (res.ok) {
      connectionStatus.className = "status-pill status-pill--online";
      connectionLabel.textContent = "ONLINE";
      return true;
    }
  } catch (_) {}
  connectionStatus.className = "status-pill status-pill--offline";
  connectionLabel.textContent = "OFFLINE";
  return false;
}

// ── Part catalog ───────────────────────────────────────────
function renderPartOptions(category) {
  const parts = partCatalog[category] || [];
  partNameSelect.innerHTML = "";
  if (!parts.length) {
    partNameSelect.disabled = true;
    partNameSelect.innerHTML = '<option value="">Select category first</option>';
    partIdInput.value = "";
    return;
  }
  partNameSelect.disabled = false;
  partNameSelect.innerHTML = '<option value="">Select part name</option>';
  parts.forEach(part => {
    const opt = document.createElement("option");
    opt.value = part.name;
    opt.textContent = part.name;
    opt.dataset.partId = part.id;
    partNameSelect.appendChild(opt);
  });
}
function syncPartId() {
  const sel = partNameSelect.options[partNameSelect.selectedIndex];
  partIdInput.value = sel?.dataset?.partId || "";
}
function updateCustomerIdFromSession() {
  const u = getCurrentUser();
  customerIdInput.value = u?.customerId || "CUST-GUEST-0001";
}

// ── View switching ─────────────────────────────────────────
function switchView(viewName) {
  document.querySelectorAll(".view").forEach(v => v.classList.remove("view--active"));
  document.querySelectorAll(".nav-tab").forEach(t => t.classList.remove("nav-tab--active"));
  const view = $(`${viewName}View`);
  if (view) view.classList.add("view--active");
  const tab = document.querySelector(`[data-view="${viewName}"]`);
  if (tab) tab.classList.add("nav-tab--active");
  if (viewName === "inventory") loadInventoryDashboard();
  if (viewName === "history") loadHistory();
  if (viewName === "analytics") loadAnalytics();
}

// ── Pipeline animation ─────────────────────────────────────
const PIPELINE_STEPS = [
  { id: "step-orchestrator", agent: "Orchestrator", desc: "Receiving order..." },
  { id: "step-demand", agent: "DemandAgent", desc: "Scanning warehouses & suppliers..." },
  { id: "step-ranking", agent: "RankingEngine", desc: "Multi-criteria scoring..." },
  { id: "step-explanation", agent: "ExplanationAgent", desc: "Generating reasoning via LLM..." },
];

function resetPipeline() {
  PIPELINE_STEPS.forEach(s => {
    const el = $(s.id);
    el.classList.remove("is-active", "is-done", "is-error");
    el.querySelector(".step-desc").textContent = s.desc;
  });
}

function activateStep(index) {
  if (index > 0) {
    const prev = $(PIPELINE_STEPS[index - 1].id);
    prev.classList.remove("is-active");
    prev.classList.add("is-done");
  }
  if (index < PIPELINE_STEPS.length) {
    const cur = $(PIPELINE_STEPS[index].id);
    cur.classList.add("is-active");
  }
}

function completeStep(index) {
  const el = $(PIPELINE_STEPS[index].id);
  el.classList.remove("is-active");
  el.classList.add("is-done");
}

function finishPipeline() {
  const last = $(PIPELINE_STEPS[PIPELINE_STEPS.length - 1].id);
  last.classList.remove("is-active");
  last.classList.add("is-done");
}

// Animate through events
function animatePipeline(events, callback) {
  resetPipeline();
  pipeline.hidden = false;
  resultsPanel.hidden = true;
  orderLayout.classList.add("is-processing");

  // Map event types to step indices
  const eventToStep = {
    ORDER_RECEIVED: 0,
    CANDIDATES_GENERATED: 1,
    TOPSIS_COMPLETED: 2,
    EXPLANATION_GENERATED: 3,
  };

  // Filter to key events (skip AGENT_STATUS)
  const keyEvents = events.filter(e => eventToStep[e.event_type] !== undefined);
  // Deduplicate by event_type
  const seen = new Set();
  const uniqueEvents = keyEvents.filter(e => {
    if (seen.has(e.event_type)) return false;
    seen.add(e.event_type);
    return true;
  });

  let i = 0;
  const step = () => {
    if (i >= uniqueEvents.length) {
      finishPipeline();
      setTimeout(() => {
        resultsPanel.hidden = false;
        if (callback) callback();
      }, 400);
      return;
    }
    const ev = uniqueEvents[i];
    const stepIdx = eventToStep[ev.event_type];
    activateStep(stepIdx);

    // Update description with data from event
    const desc = ev.data?.message || ev.event_type.replace(/_/g, " ").toLowerCase();
    $(PIPELINE_STEPS[stepIdx].id).querySelector(".step-desc").textContent = desc;

    // Complete this step and move to next
    setTimeout(() => {
      completeStep(stepIdx);
      i++;
      setTimeout(step, 200);
    }, 600);
  };

  // Start after a brief delay for the slide animation
  setTimeout(step, 500);
}

// ── Winner card ────────────────────────────────────────────
function renderWinnerCard(selected) {
  $("winnerScore").textContent = (selected.topsis_score || 0).toFixed(4);
  $("winnerSource").textContent = selected.source || selected.warehouse_id || "--";
  $("winnerLeadTime").textContent = `${selected.lead_time_days ?? "--"}d`;
  $("winnerCost").textContent = selected.unit_cost != null ? `$${selected.unit_cost.toFixed(2)}` : "--";
  $("winnerTotalCost").textContent = selected.total_cost != null ? `$${selected.total_cost.toFixed(2)}` : "--";
  $("winnerFulfill").textContent = selected.can_fulfill ? "Yes" : "Partial";
  $("winnerStrategy").textContent = selected.strategy_name || "--";
  winnerCard.hidden = false;
}

// ── Candidates table ───────────────────────────────────────
function renderCandidates(candidates) {
  if (!candidates?.length) { candidatesSection.hidden = true; return; }
  const shown = candidates.slice(0, 5);
  candidatesTableBody.innerHTML = shown.map((c, i) => {
    const rank = i === 0 ? `<td class="rank rank--first">1</td>` : `<td class="rank">${i + 1}</td>`;
    const bar = `<div class="score-bar"><div class="score-bar__fill" style="width:${Math.min((c.topsis_score || 0) * 500, 100)}%"></div></div><span style="font-size:0.78rem;color:var(--text-muted)">${(c.topsis_score || 0).toFixed(4)}</span>`;
    const rowClass = i === 0 ? 'class="row--winner"' : "";
    return `<tr ${rowClass}>
      ${rank}
      <td style="font-weight:500">${c.strategy_name || "--"}</td>
      <td>${c.source || c.warehouse_id || "--"}</td>
      <td>$${(c.total_cost || 0).toLocaleString()}</td>
      <td>${c.lead_time_days ?? "--"}d</td>
      <td>${((c.reliability_score || 0) * 100).toFixed(0)}%</td>
      <td>${bar}</td>
    </tr>`;
  }).join("");
  candidatesSection.hidden = false;
}

// ── Explanation ────────────────────────────────────────────
function renderExplanation(text) {
  if (!text) { explanationBlock.hidden = true; return; }
  explanationText.textContent = text;
  explanationBlock.hidden = false;
}

// ── Inventory ──────────────────────────────────────────────
async function loadInventoryDashboard() {
  inventoryTableBody.innerHTML = '<tr><td colspan="12" class="loading-cell">Loading inventory...</td></tr>';
  try {
    const res = await fetch(`${API_BASE}/api/v1/inventory`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const inv = data.inventory || [];
    const stats = data.stats || {};
    inventoryStats.innerHTML = `
      <div class="inv-stat"><span class="inv-stat__val">${stats.total_skus ?? inv.length}</span><span>Total SKUs</span></div>
      <div class="inv-stat inv-stat--warn"><span class="inv-stat__val">${stats.low_stock_count ?? 0}</span><span>Low Stock</span></div>
      <div class="inv-stat inv-stat--crit"><span class="inv-stat__val">${stats.critical_parts_count ?? 0}</span><span>Critical</span></div>
      <div class="inv-stat"><span class="inv-stat__val">$${(stats.total_inventory_value_usd ?? 0).toLocaleString(undefined, {maximumFractionDigits:0})}</span><span>Value</span></div>`;
    inventoryTableBody.innerHTML = inv.map(item => {
      const warn = item.needs_reorder;
      const badge = warn ? '<span class="badge badge--warn">Reorder</span>' : '<span class="badge badge--ok">OK</span>';
      const pct = item.stock_pct ?? 0;
      const bar = `<div class="score-bar"><div class="score-bar__fill ${pct < 30 ? 'score-bar__fill--low' : ''}" style="width:${Math.min(pct,100)}%"></div></div><span style="font-size:0.78rem">${pct}%</span>`;
      return `<tr class="${warn ? 'row--warn' : ''}">
        <td><code style="font-size:0.8rem">${item.sku}</code></td>
        <td>${item.description}</td>
        <td>${item.category}</td>
        <td>${item.warehouse_loc}</td>
        <td>${(item.on_hand_qty ?? 0).toLocaleString()}</td>
        <td>${(item.reserved_qty ?? 0).toLocaleString()}</td>
        <td style="font-weight:600">${(item.available_qty ?? 0).toLocaleString()}</td>
        <td>${(item.reorder_point ?? 0).toLocaleString()}</td>
        <td>${bar}</td>
        <td>$${(item.base_unit_price ?? 0).toFixed(2)}</td>
        <td>${item.is_critical ? "Yes" : "--"}</td>
        <td>${badge}</td>
      </tr>`;
    }).join("");
    if (!inv.length) inventoryTableBody.innerHTML = '<tr><td colspan="12" class="loading-cell">No inventory data.</td></tr>';
  } catch (err) {
    inventoryTableBody.innerHTML = `<tr><td colspan="12" class="loading-cell error-cell">Failed to load: ${err.message}</td></tr>`;
  }
}

// ── History ────────────────────────────────────────────────
async function loadHistory() {
  historyTableBody.innerHTML = '<tr><td colspan="6" class="loading-cell">Loading...</td></tr>';
  try {
    const res = await fetch(`${API_BASE}/orders`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const orders = await res.json();
    if (!orders.length) {
      historyTableBody.innerHTML = '<tr><td colspan="6" class="loading-cell">No orders yet.</td></tr>';
      return;
    }
    historyTableBody.innerHTML = orders.map(o => {
      const statusBadge = o.status === "EXECUTED"
        ? '<span class="badge badge--ok">Executed</span>'
        : o.status === "REJECTED"
        ? '<span class="badge badge--warn">Rejected</span>'
        : '<span class="badge" style="background:var(--accent-light);color:var(--accent)">Pending</span>';
      return `<tr>
        <td><code>${o.order_id}</code></td>
        <td>${statusBadge}</td>
        <td>${o.approval_status || "--"}</td>
        <td>${o.customer_id || "--"}</td>
        <td>${o.part_id || "--"}</td>
        <td style="color:var(--text-muted);font-size:0.8rem">${o.created_at ? new Date(o.created_at).toLocaleString() : "--"}</td>
      </tr>`;
    }).join("");
  } catch (err) {
    historyTableBody.innerHTML = `<tr><td colspan="6" class="loading-cell error-cell">${err.message}</td></tr>`;
  }
}

// ── Analytics ──────────────────────────────────────────────
function statCard(label, value, extra = "", tone = "") {
  const toneClass = tone === "green" ? "text-green-600" : tone === "red" ? "text-red-500" : tone === "amber" ? "text-amber-500" : "text-brand-600";
  return `<div class="bg-white border border-gray-200/80 rounded-2xl p-5 shadow-sm">
    <div class="text-[11px] font-semibold uppercase tracking-wider text-gray-400 mb-1.5">${label}</div>
    <div class="text-3xl font-extrabold ${toneClass} tracking-tight">${value}</div>
    ${extra ? `<div class="text-xs text-gray-400 mt-1">${extra}</div>` : ""}
  </div>`;
}

function distributionBars(container, data, color = "#315cda") {
  const entries = Object.entries(data || {});
  if (!entries.length) {
    container.innerHTML = '<p class="text-sm text-gray-400">No data yet.</p>';
    return;
  }
  const max = Math.max(...entries.map(([, v]) => v), 1);
  container.innerHTML = entries.map(([key, val]) => {
    const pct = Math.round((val / max) * 100);
    return `<div>
      <div class="flex items-center justify-between mb-1">
        <span class="text-sm font-medium text-gray-700 truncate">${key}</span>
        <span class="text-sm font-semibold text-gray-500">${val}</span>
      </div>
      <div class="h-2 rounded-full bg-gray-100 overflow-hidden">
        <div class="h-full rounded-full" style="width:${pct}%;background:${color};transition:width 0.6s ease"></div>
      </div>
    </div>`;
  }).join("");
}

const STATUS_BADGE = {
  EXECUTED: '<span class="inline-flex px-2 py-0.5 rounded-full bg-green-50 text-green-600 text-[11px] font-semibold">Executed</span>',
  REJECTED: '<span class="inline-flex px-2 py-0.5 rounded-full bg-red-50 text-red-500 text-[11px] font-semibold">Rejected</span>',
  PENDING_APPROVAL: '<span class="inline-flex px-2 py-0.5 rounded-full bg-amber-50 text-amber-600 text-[11px] font-semibold">Pending</span>',
};

async function loadAnalytics() {
  analyticsSummary.innerHTML = '<div class="col-span-full text-sm text-gray-400 p-4">Loading analytics...</div>';
  try {
    const res = await fetch(`${API_BASE}/api/v1/analytics`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const s = data.summary || {};
    analyticsSummary.innerHTML =
      statCard("Total Orders", s.total_orders ?? 0) +
      statCard("Executed", s.executed ?? 0, `${s.execution_rate ?? 0}% execution rate`, "green") +
      statCard("Pending", s.pending ?? 0, "", "amber") +
      statCard("Avg Cost", `$${(s.avg_cost ?? 0).toFixed(2)}`, `${s.avg_lead_time ?? 0}d avg lead`, "");

    distributionBars(priorityChart, data.by_priority, "#315cda");
    distributionBars(categoryChart, data.by_category, "#7c3aed");
    distributionBars(strategyChart, data.by_strategy, "#0891b2");

    // Warehouse utilization — stacked on_hand / reserved / available
    const wh = data.warehouse_utilization || {};
    const whEntries = Object.entries(wh);
    if (!whEntries.length) {
      warehouseChart.innerHTML = '<p class="text-sm text-gray-400">No warehouse data.</p>';
    } else {
      const whMax = Math.max(...whEntries.map(([, v]) => v.on_hand || 0), 1);
      warehouseChart.innerHTML = whEntries.map(([name, v]) => {
        const onHand = v.on_hand || 0;
        const pct = Math.round((onHand / whMax) * 100);
        return `<div>
          <div class="flex items-center justify-between mb-1">
            <span class="text-xs font-medium text-gray-700 truncate">${name}</span>
            <span class="text-xs text-gray-400">${onHand.toLocaleString()} on hand</span>
          </div>
          <div class="h-2 rounded-full bg-gray-100 overflow-hidden">
            <div class="h-full rounded-full" style="width:${pct}%;background:#16a34a;transition:width 0.6s ease"></div>
          </div>
          <div class="text-[10px] text-gray-400 mt-0.5">${(v.reserved || 0).toLocaleString()} reserved · ${(v.available || 0).toLocaleString()} available</div>
        </div>`;
      }).join("");
    }

    const recent = data.recent_orders || [];
    if (!recent.length) {
      recentOrders.innerHTML = '<p class="text-sm text-gray-400">No recent orders.</p>';
    } else {
      recentOrders.innerHTML = recent.map(o => {
        const badge = STATUS_BADGE[o.status] || `<span class="inline-flex px-2 py-0.5 rounded-full bg-gray-100 text-gray-500 text-[11px] font-semibold">${o.status || "--"}</span>`;
        const when = o.created_at ? new Date(o.created_at).toLocaleString() : "--";
        return `<div class="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
          <div class="flex items-center gap-3 min-w-0">
            <code class="text-xs text-gray-500">${o.order_id}</code>
            <span class="text-sm text-gray-700 truncate">${o.part_id || "--"}</span>
          </div>
          <div class="flex items-center gap-3 flex-shrink-0">
            <span class="text-[11px] text-gray-400">${o.priority || "--"}</span>
            ${badge}
            <span class="text-[11px] text-gray-400 hidden md:inline">${when}</span>
          </div>
        </div>`;
      }).join("");
    }
  } catch (err) {
    analyticsSummary.innerHTML = `<div class="col-span-full text-sm text-red-500 p-4">Failed to load: ${err.message}</div>`;
  }
}

// ── Role / Dashboard ───────────────────────────────────────
function updateDashboardForRole() {
  const user = getCurrentUser();
  if (user) {
    userAvatar.textContent = user.name?.[0] || user.role?.[0] || "?";
    userName.textContent = user.name || "Guest";
  }
  const isSeller = user?.role === "Seller";
  if (isSeller) {
    switchView("inventory");
    document.querySelector('[data-view="order"]').style.display = "none";
  } else {
    switchView("order");
    document.querySelector('[data-view="order"]').style.display = "";
  }
}
function showDashboard() {
  welcomeScreen.hidden = true;
  dashboardPage.hidden = false;
  updateDashboardForRole();
  checkBackendHealth();
}

// ── Welcome animation ──────────────────────────────────────
function startWelcomeAnimation() {
  const msg = "Welcome to Autonomous SCM";
  let i = 0;
  welcomeTitle.textContent = "Welcome!";
  const tick = () => {
    if (i < msg.length) {
      welcomeTitle.textContent = msg.slice(0, i + 1);
      i++;
      window.setTimeout(tick, i < 9 ? 95 : 62);
      return;
    }
    welcomeTitle.classList.add("welcome-screen__title--complete");
    welcomeContinue.hidden = false;
  };
  window.setTimeout(tick, 700);
}
function showWelcomeScreen() {
  dashboardPage.hidden = true;
  welcomeScreen.hidden = false;
  welcomeContinue.hidden = true;
  welcomeTitle.classList.remove("welcome-screen__title--complete");
  startWelcomeAnimation();
}

// ── Auth ───────────────────────────────────────────────────
function setAuthMode(mode) {
  authState.mode = mode;
  const s = mode === "signup";
  authModalTitle.textContent = s ? "Create Account" : "Welcome back";
  authModalText.textContent = s ? "Create a local demo account." : "Sign in to your account.";
  authSubmitButton.textContent = s ? "Create Account" : "Login";
  toggleAuthModeButton.textContent = s ? "Already registered? Login" : "New here? Sign up";
  nameField.hidden = !s;
  companyField.hidden = !s;
  demoCredentials.hidden = s;
  authError.textContent = "";
  syncRoleTab();
}
function syncRoleTab() {
  roleTabs.forEach(t => { t.classList.toggle("auth-role-tab--active", t.dataset.roleSelect === authState.role); });
}
function setActiveRole(role) { authState.role = role; syncRoleTab(); authError.textContent = ""; }
function openRoleSelectionModal() {
  authRoleBadge.textContent = "Sign In";
  setAuthMode("login");
  authPanel.hidden = false;
  authModal.hidden = false;
  syncRoleTab();
}
function closeAuthModal() { authModal.hidden = true; authForm.reset(); authError.textContent = ""; }
function handleLogin() {
  const email = authEmailInput.value.trim().toLowerCase();
  const pw = authPasswordInput.value;
  const match = getUsers().find(u => u.email.toLowerCase() === email && u.password === pw && u.role === authState.role);
  if (!match) { authError.textContent = "Invalid login details."; return; }
  saveCurrentUser(match);
  updateCustomerIdFromSession();
  closeAuthModal();
  showDashboard();
}
function handleSignup() {
  const name = authNameInput.value.trim(), email = authEmailInput.value.trim().toLowerCase();
  const co = authCompanyInput.value.trim(), pw = authPasswordInput.value;
  if (!name || !email || !co || !pw) { authError.textContent = "Please complete all fields."; return; }
  const users = getUsers();
  if (users.find(u => u.email.toLowerCase() === email && u.role === authState.role)) {
    authError.textContent = "Account already exists for that role."; return;
  }
  const code = authState.role === "Buyer" ? "BUY" : "SEL";
  const nu = { role: authState.role, name, email, password: pw, company: co, customerId: `CUST-${code}-${Date.now().toString().slice(-4)}` };
  users.push(nu);
  saveUsers(users);
  saveCurrentUser(nu);
  updateCustomerIdFromSession();
  closeAuthModal();
  showDashboard();
}
function logout() { localStorage.removeItem(STORAGE_KEYS.currentUser); showWelcomeScreen(); }

// ── Form submit ────────────────────────────────────────────
function buildOrderPayload(formData) {
  return {
    customer_id: customerIdInput.value,
    part_id: formData.get("partId").trim(),
    requested_qty: Number(formData.get("requestedQuantity")),
    max_lead_time_days: Number(formData.get("leadTime")),
    priority: formData.get("priorityLevel"),
    notes: formData.get("specialInstructions").trim() || "None provided",
  };
}

form.addEventListener("submit", async event => {
  event.preventDefault();
  clearErrors();
  updateCustomerIdFromSession();
  const formData = new FormData(form);
  if (!validateForm(formData)) return;
  const payload = buildOrderPayload(formData);

  // Reset UI
  winnerCard.hidden = true;
  explanationBlock.hidden = true;
  candidatesSection.hidden = true;
  resultsPanel.hidden = true;
  setSubmitting(true);

  try {
    const res = await fetch(`${API_BASE}/api/v1/process-order`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      throw new Error(errBody.detail || `HTTP ${res.status}`);
    }
    const data = await res.json();
    if (data.status !== "success") throw new Error(data.detail || "Unknown error");

    currentOrderId = data.order_id || null;
    currentTraceId = data.trace_id || null;

    // Animate the pipeline, then show results
    animatePipeline(data.agent_events || [], () => {
      renderWinnerCard(data.selected_option || {});
      renderCandidates(data.all_candidates || []);
      renderExplanation(data.explanation || "");
      const actions = $("winnerActions");
      const status = $("winnerStatus");
      if (actions) actions.hidden = false;
      if (status) status.hidden = true;
    });
  } catch (err) {
    // Show error in pipeline
    pipeline.hidden = false;
    resultsPanel.hidden = true;
    orderLayout.classList.add("is-processing");
    finishPipeline();
    const errStep = $(PIPELINE_STEPS[PIPELINE_STEPS.length - 1].id);
    errStep.classList.remove("is-done");
    errStep.classList.add("is-error");
    errStep.querySelector(".step-desc").textContent = `Error: ${err.message}`;
  } finally {
    setSubmitting(false);
  }
});

function setSubmitting(loading) {
  submitBtn.disabled = loading;
  submitBtnText.textContent = loading ? "Analyzing..." : "Run AI Analysis";
  submitSpinner.hidden = !loading;
}

// ── Approve / Reject ───────────────────────────────────────
function setWinnerStatus(status, message) {
  const el = $("winnerStatus");
  const txt = $("winnerStatusText");
  if (!el || !txt) return;
  el.hidden = false;
  el.dataset.status = status;
  txt.textContent = message;
  $("winnerActions").hidden = true;
}

$("approveBtn")?.addEventListener("click", async () => {
  if (!currentOrderId) return;
  try {
    const res = await fetch(`${API_BASE}/approve-execution`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ order_id: currentOrderId, action: "APPROVE" })
    });
    const data = await res.json();
    if (!data.error) {
      setWinnerStatus("success", data.message || "Order executed successfully.");
    } else {
      setWinnerStatus("cancelled", `Error: ${data.error}`);
    }
  } catch (e) {
    setWinnerStatus("cancelled", `Error: ${e.message}`);
  }
});

$("rejectBtn")?.addEventListener("click", async () => {
  if (!currentOrderId) return;
  try {
    const res = await fetch(`${API_BASE}/approve-execution`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ order_id: currentOrderId, action: "REJECT" })
    });
    const data = await res.json();
    if (!data.error) {
      setWinnerStatus("cancelled", data.message || "Order rejected.");
    } else {
      setWinnerStatus("cancelled", `Error: ${data.error}`);
    }
  } catch (e) {
    setWinnerStatus("cancelled", `Error: ${e.message}`);
  }
});

// ── Event listeners ────────────────────────────────────────
welcomeContinue.addEventListener("click", () => openRoleSelectionModal());
roleTabs.forEach(b => b.addEventListener("click", () => setActiveRole(b.dataset.roleSelect)));
closeAuthModalButton.addEventListener("click", closeAuthModal);
authModal.addEventListener("click", e => { if (e.target === authModal) closeAuthModal(); });
toggleAuthModeButton.addEventListener("click", () => setAuthMode(authState.mode === "login" ? "signup" : "login"));
authForm.addEventListener("submit", e => { e.preventDefault(); authError.textContent = ""; authState.mode === "login" ? handleLogin() : handleSignup(); });
logoutBtn.addEventListener("click", logout);

demoAutofillButtons.forEach(btn => {
  btn.addEventListener("click", () => {
    const role = btn.dataset.demoRole;
    const demo = demoUsers.find(u => u.role === role);
    if (!demo) return;
    authEmailInput.value = demo.email;
    authPasswordInput.value = demo.password;
    setActiveRole(role);
    authEmailInput.focus();
  });
});

navTabs.forEach(tab => { tab.addEventListener("click", () => switchView(tab.dataset.view)); });

categorySelect.addEventListener("change", () => {
  renderPartOptions(categorySelect.value);
  partNameSelect.value = "";
  partIdInput.value = "";
  ["category", "partName", "partId"].forEach(id => setFieldError(id, ""));
});

partNameSelect.addEventListener("change", () => {
  syncPartId();
  ["partName", "partId"].forEach(id => setFieldError(id, ""));
});

// ── Init ───────────────────────────────────────────────────
updateCustomerIdFromSession();
renderPartOptions("");
if (getCurrentUser()) { showDashboard(); } else { showWelcomeScreen(); }
