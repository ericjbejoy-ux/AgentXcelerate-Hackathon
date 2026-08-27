/* ============================================================
   AgentXcelerate — Order Ingestion + Backend API Integration
   ============================================================ */

const API_BASE = "http://localhost:8000";

// ── Storage helpers ──────────────────────────────────────────
const STORAGE_KEYS = { users: "ax_users", currentUser: "ax_current_user" };

const partCatalog = {
  Hydraulics: [
    { name: "Hydraulic Pump", id: "HYD-PMP-001" },
    { name: "Control Valve", id: "HYD-VLV-014" },
    { name: "Actuator Cylinder", id: "HYD-ACT-022" },
  ],
  Electronics: [
    { name: "Sensor Module", id: "ELE-SNS-104" },
    { name: "Control Board", id: "ELE-CTL-118" },
    { name: "Power Relay", id: "ELE-RLY-133" },
  ],
  Fasteners: [
    { name: "Hex Bolt Set", id: "FST-BLT-212" },
    { name: "Lock Nut Pack", id: "FST-NUT-225" },
    { name: "Washer Kit", id: "FST-WSR-231" },
  ],
  Filtration: [
    { name: "Air Filter Cartridge", id: "FIL-AIR-309" },
    { name: "Oil Filter Unit", id: "FIL-OIL-317" },
    { name: "Dust Separator", id: "FIL-DST-324" },
  ],
};

const demoUsers = [
  { role: "Buyer", name: "Ava Buyer", email: "buyer@demo.com", password: "buyer123", company: "Northline Procurement", customerId: "CUST-BUY-1001", phone: "+1 555 0101", location: "Chicago, USA", preferredCategory: "Hydraulics" },
  { role: "Seller", name: "Noah Seller", email: "seller@demo.com", password: "seller123", company: "Prime Parts Supply", customerId: "CUST-SEL-2001", phone: "+1 555 0202", location: "Austin, USA", preferredCategory: "Electronics" },
];

function seedUsers() { if (!localStorage.getItem(STORAGE_KEYS.users)) localStorage.setItem(STORAGE_KEYS.users, JSON.stringify(demoUsers)); }
function getUsers() { return JSON.parse(localStorage.getItem(STORAGE_KEYS.users) || "[]"); }
function saveUsers(u) { localStorage.setItem(STORAGE_KEYS.users, JSON.stringify(u)); }
function getCurrentUser() { return JSON.parse(localStorage.getItem(STORAGE_KEYS.currentUser) || "null"); }
function saveCurrentUser(u) { localStorage.setItem(STORAGE_KEYS.currentUser, JSON.stringify(u)); }

seedUsers();

// ── DOM refs ─────────────────────────────────────────────────
const form = document.getElementById("order-form");
const categorySelect = document.getElementById("category");
const partNameSelect = document.getElementById("partName");
const partIdInput = document.getElementById("partId");
const customerIdInput = document.getElementById("customerId");
const statusMessage = document.getElementById("statusMessage");
const resultTableBody = document.getElementById("resultTableBody");
const requestPanel = document.getElementById("requestPanel");
const orderForm = document.getElementById("order-form");
const sellerWorkspace = document.getElementById("sellerWorkspace");
const formTitle = document.getElementById("form-title");
const formDescription = document.getElementById("form-description");
const welcomeScreen = document.getElementById("welcomeScreen");
const welcomeTitle = document.getElementById("welcomeTitle");
const welcomeContinue = document.getElementById("welcomeContinue");
const dashboardPage = document.getElementById("dashboardPage");
const connectionStatus = document.getElementById("connectionStatus");
const connectionLabel = document.getElementById("connectionLabel");
const submitBtn = document.getElementById("submitBtn");
const submitBtnText = document.getElementById("submitBtnText");
const submitSpinner = document.getElementById("submitSpinner");
const winnerCard = document.getElementById("winnerCard");
const explanationBlock = document.getElementById("explanationBlock");
const explanationText = document.getElementById("explanationText");
const candidatesSection = document.getElementById("candidatesSection");
const candidatesTableBody = document.getElementById("candidatesTableBody");
const inventoryDashboard = document.getElementById("inventoryDashboard");
const inventoryTableBody = document.getElementById("inventoryTableBody");
const inventoryStats = document.getElementById("inventoryStats");

const authModal = document.getElementById("authModal");
const closeAuthModalButton = document.getElementById("closeAuthModal");
const roleSelection = document.getElementById("roleSelection");
const authPanel = document.getElementById("authPanel");
const authForm = document.getElementById("authForm");
const authSubmitButton = document.getElementById("authSubmitButton");
const toggleAuthModeButton = document.getElementById("toggleAuthMode");
const authError = document.getElementById("authError");
const authRoleBadge = document.getElementById("authRoleBadge");
const authModalTitle = document.getElementById("authModalTitle");
const authModalText = document.getElementById("authModalText");
const demoCredentials = document.getElementById("demoCredentials");
const authEmailInput = document.getElementById("authEmail");
const authPasswordInput = document.getElementById("authPassword");
const authNameInput = document.getElementById("authName");
const authCompanyInput = document.getElementById("authCompany");
const nameField = document.getElementById("nameField");
const companyField = document.getElementById("companyField");
const roleSelectionButtons = document.querySelectorAll("[data-role-select]");

let authState = { role: "Buyer", mode: "login" };

// ── Validation config ────────────────────────────────────────
const fieldConfig = [
  { id: "category", validate: v => v.trim() !== "", message: "Please select a category." },
  { id: "partName", validate: v => v.trim() !== "", message: "Please select a part name." },
  { id: "partId", validate: v => v.trim() !== "", message: "A part ID is required." },
  { id: "requestedQuantity", validate: v => Number.isInteger(Number(v)) && Number(v) > 0, message: "Requested quantity must be a positive whole number." },
  { id: "leadTime", validate: v => Number.isInteger(Number(v)) && Number(v) > 0, message: "Lead time must be a positive whole number of days." },
  { id: "priorityLevel", validate: v => ["Low", "Medium", "Critical"].includes(v), message: "Please select a priority level." },
];

function setFieldError(fieldId, message) {
  const input = document.getElementById(fieldId);
  const err = document.getElementById(`${fieldId}Error`);
  if (input) input.classList.toggle("input-error", Boolean(message));
  if (err) err.textContent = message;
}
function clearErrors() { fieldConfig.forEach(f => setFieldError(f.id, "")); }

// ── Backend health check ──────────────────────────────────────
async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/health`, { signal: AbortSignal.timeout(3000) });
    if (res.ok) {
      connectionStatus.classList.add("connection-status--online");
      connectionStatus.classList.remove("connection-status--offline");
      connectionLabel.textContent = "BACKEND ONLINE";
      return true;
    }
  } catch (_) { }
  connectionStatus.classList.add("connection-status--offline");
  connectionStatus.classList.remove("connection-status--online");
  connectionLabel.textContent = "BACKEND OFFLINE";
  return false;
}

// ── Part catalog helpers ──────────────────────────────────────
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

// ── Order summary table ───────────────────────────────────────
function renderSummaryTable(payload) {
  const rows = [
    ["Category", payload.category],
    ["Part Name", payload.partName],
    ["Part ID", payload.partId],
    ["Requested Quantity", String(payload.requestedQuantity)],
    ["Lead Time", `${payload.maximumAcceptableLeadTimeDays} day(s)`],
    ["Priority Level", payload.priorityLevel],
    ["Special Instructions", payload.specialInstructions || "None"],
  ];
  resultTableBody.innerHTML = rows.map(([l, v]) =>
    `<tr><th scope="row">${l}</th><td>${v}</td></tr>`
  ).join("");
}

// ── Winner card ────────────────────────────────────────────────
function renderWinnerCard(selected) {
  document.getElementById("winnerScore").textContent = `Score: ${(selected.topsis_score || 0).toFixed(4)}`;
  document.getElementById("winnerSource").textContent = selected.source || selected.warehouse_id || "—";
  document.getElementById("winnerLeadTime").textContent = `${selected.lead_time_days ?? "—"} day(s)`;
  document.getElementById("winnerCost").textContent = selected.unit_cost != null ? `$${selected.unit_cost.toFixed(2)}` : "—";
  document.getElementById("winnerTotalCost").textContent = selected.total_cost != null ? `$${selected.total_cost.toFixed(2)}` : "—";
  document.getElementById("winnerFulfill").textContent = selected.can_fulfill ? "✅ Yes" : "⚠️ Partial";
  document.getElementById("winnerStrategy").textContent = selected.fulfillment_type || "—";
  winnerCard.hidden = false;
}

// ── Ranked candidates table ───────────────────────────────────
function renderCandidates(candidates) {
  if (!candidates || !candidates.length) {
    candidatesSection.hidden = true;
    return;
  }
  candidatesTableBody.innerHTML = candidates.map((c, i) => {
    const rankCell = i === 0 ? `<td class="rank rank--first">🥇 #1</td>` : `<td class="rank">#${i + 1}</td>`;
    const scoreBar = `<div class="score-bar"><div class="score-bar__fill" style="width:${Math.min((c.topsis_score || 0) * 500, 100)}%"></div></div>`;
    const statusBadge = c.can_fulfill
      ? `<span class="badge badge--ok">In Stock</span>`
      : `<span class="badge badge--warn">Partial</span>`;
    return `<tr ${i === 0 ? 'class="winner-row"' : ""}>
      ${rankCell}
      <td>${c.candidate_id || "—"}</td>
      <td>${c.source || c.warehouse_id || "—"}</td>
      <td><code>${c.sku || c.item_sku || "—"}</code></td>
      <td>$${(c.unit_cost || 0).toFixed(2)}</td>
      <td>${c.lead_time_days ?? "—"} days</td>
      <td>${(c.available_stock || 0).toLocaleString()} units</td>
      <td>${((c.reliability_score || 0) * 100).toFixed(0)}%</td>
      <td>${scoreBar}<span class="score-label">${(c.topsis_score || 0).toFixed(4)}</span></td>
      <td>${statusBadge}</td>
    </tr>`;
  }).join("");
  candidatesSection.hidden = false;
}

// ── AI Explanation ─────────────────────────────────────────────
function renderExplanation(text) {
  if (!text) { explanationBlock.hidden = true; return; }
  explanationText.textContent = text;
  explanationBlock.hidden = false;
}

// ── Inventory dashboard (Seller) ──────────────────────────────
async function loadInventoryDashboard() {
  inventoryDashboard.hidden = false;
  inventoryTableBody.innerHTML = `<tr><td colspan="12" class="loading-cell">⏳ Loading inventory from backend…</td></tr>`;
  try {
    const res = await fetch(`${API_BASE}/api/v1/inventory`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const inv = data.inventory || [];
    const stats = data.stats || {};

    // Stats row
    inventoryStats.innerHTML = `
      <div class="inv-stat"><span class="inv-stat__val">${stats.total_skus ?? inv.length}</span><span>Total SKUs</span></div>
      <div class="inv-stat inv-stat--warn"><span class="inv-stat__val">${stats.low_stock_count ?? 0}</span><span>Low Stock</span></div>
      <div class="inv-stat inv-stat--crit"><span class="inv-stat__val">${stats.critical_parts_count ?? 0}</span><span>Critical Parts</span></div>
      <div class="inv-stat"><span class="inv-stat__val">$${(stats.total_inventory_value_usd ?? 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}</span><span>Inventory Value</span></div>
    `;

    inventoryTableBody.innerHTML = inv.map(item => {
      const needsReorder = item.needs_reorder;
      const statusBadge = needsReorder
        ? `<span class="badge badge--warn">⚠ Reorder</span>`
        : `<span class="badge badge--ok">✓ OK</span>`;
      const stockPct = item.stock_pct ?? 0;
      const fillBar = `<div class="score-bar"><div class="score-bar__fill ${stockPct < 30 ? 'score-bar__fill--low' : ''}" style="width:${Math.min(stockPct, 100)}%"></div></div><span class="score-label">${stockPct}%</span>`;
      return `<tr class="${needsReorder ? "row--warn" : ""}">
        <td><code>${item.sku}</code></td>
        <td>${item.description}</td>
        <td>${item.category}</td>
        <td>${item.warehouse_loc}</td>
        <td>${(item.on_hand_qty ?? 0).toLocaleString()}</td>
        <td>${(item.reserved_qty ?? 0).toLocaleString()}</td>
        <td><strong>${(item.available_qty ?? 0).toLocaleString()}</strong></td>
        <td>${(item.reorder_point ?? 0).toLocaleString()}</td>
        <td>${fillBar}</td>
        <td>$${(item.base_unit_price ?? 0).toFixed(2)}</td>
        <td>${item.is_critical ? "🔴 Yes" : "—"}</td>
        <td>${statusBadge}</td>
      </tr>`;
    }).join("");

    if (!inv.length) {
      inventoryTableBody.innerHTML = `<tr><td colspan="12" class="loading-cell">No inventory data returned.</td></tr>`;
    }
  } catch (err) {
    inventoryTableBody.innerHTML = `<tr><td colspan="12" class="loading-cell error-cell">❌ Failed to load: ${err.message}. Is the backend running on port 8000?</td></tr>`;
  }
}

// ── Dashboard role setup ──────────────────────────────────────
function updateDashboardForRole() {
  const user = getCurrentUser();
  const isSeller = user?.role === "Seller";

  orderForm.hidden = isSeller;
  sellerWorkspace.hidden = !isSeller;
  requestPanel.classList.toggle("panel--seller", isSeller);
  candidatesSection.hidden = true;
  winnerCard.hidden = true;
  explanationBlock.hidden = true;

  formTitle.textContent = isSeller ? "Seller Workspace" : "New Fulfillment Request";
  formDescription.textContent = isSeller
    ? "Your account is ready for seller-side fulfillment activity."
    : "Choose a category and part name. The matching part ID is filled in automatically.";

  if (isSeller) {
    loadInventoryDashboard();
  } else {
    inventoryDashboard.hidden = true;
  }
}

function showDashboard() {
  welcomeScreen.hidden = true;
  dashboardPage.hidden = false;
  updateDashboardForRole();
  checkBackendHealth();
}

// ── Welcome animation ─────────────────────────────────────────
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

// ── Auth helpers ──────────────────────────────────────────────
function setAuthMode(mode) {
  authState.mode = mode;
  const s = mode === "signup";
  authModalTitle.textContent = s ? `${authState.role} Sign Up` : `${authState.role} Login`;
  authModalText.textContent = s ? "Create a local demo account (stored in browser)." : "Use the demo credentials below or sign up locally.";
  authSubmitButton.textContent = s ? "Create Account" : "Login";
  toggleAuthModeButton.textContent = s ? "Already registered? Login" : "New here? Sign up";
  nameField.hidden = !s;
  companyField.hidden = !s;
  demoCredentials.hidden = s;
  authError.textContent = "";
}

function showRoleSelection() {
  authState.role = "Buyer";
  authState.mode = "login";
  roleSelection.hidden = false;
  authPanel.hidden = true;
  authRoleBadge.textContent = "Account Access";
  authModalTitle.textContent = "Choose your role";
  authModalText.textContent = "Select how you want to continue to the demo portal.";
  authForm.reset();
  authError.textContent = "";
}

function openAuthModal(role) {
  authState.role = role;
  authRoleBadge.textContent = `${role} Access`;
  authModal.dataset.role = role.toLowerCase();
  setAuthMode("login");
  roleSelection.hidden = true;
  authPanel.hidden = false;
  authModal.hidden = false;
  document.documentElement.classList.add("modal-open");
  document.body.classList.add("modal-open");
}

function openRoleSelectionModal() {
  showRoleSelection();
  authModal.hidden = false;
  document.documentElement.classList.add("modal-open");
  document.body.classList.add("modal-open");
}

function closeAuthModal() {
  authModal.hidden = true;
  document.documentElement.classList.remove("modal-open");
  document.body.classList.remove("modal-open");
  showRoleSelection();
}

function buildProfileFromAuth(role, email, name, company) {
  const code = role === "Buyer" ? "BUY" : "SEL";
  return { role, name, email, password: authPasswordInput.value, company, customerId: `CUST-${code}-${Date.now().toString().slice(-4)}`, phone: "", location: "", preferredCategory: "" };
}

function handleLogin() {
  const email = authEmailInput.value.trim().toLowerCase();
  const pw = authPasswordInput.value;
  const match = getUsers().find(u => u.email.toLowerCase() === email && u.password === pw && u.role === authState.role);
  if (!match) { authError.textContent = "Invalid login details for the selected role."; return; }
  saveCurrentUser(match);
  updateCustomerIdFromSession();
  closeAuthModal();
  showDashboard();
  statusMessage.textContent = `${match.role} logged in as ${match.name}.`;
  statusMessage.classList.add("status-message--success");
}

function handleSignup() {
  const name = authNameInput.value.trim(), email = authEmailInput.value.trim().toLowerCase();
  const co = authCompanyInput.value.trim(), pw = authPasswordInput.value;
  if (!name || !email || !co || !pw) { authError.textContent = "Please complete all sign-up fields."; return; }
  const users = getUsers();
  if (users.find(u => u.email.toLowerCase() === email && u.role === authState.role)) {
    authError.textContent = "An account with this email already exists for that role."; return;
  }
  const nu = buildProfileFromAuth(authState.role, email, name, co);
  users.push(nu);
  saveUsers(users);
  saveCurrentUser(nu);
  updateCustomerIdFromSession();
  closeAuthModal();
  showDashboard();
  statusMessage.textContent = `${nu.role} account created for ${nu.name}.`;
  statusMessage.classList.add("status-message--success");
}

// ── Form submit → backend API ─────────────────────────────────
function buildOrderPayload(formData) {
  return {
    customer_id: customerIdInput.value,
    customerId: customerIdInput.value,
    category: formData.get("category").trim(),
    partName: formData.get("partName").trim(),
    part_id: formData.get("partId").trim(),
    partId: formData.get("partId").trim(),
    requestedQuantity: Number(formData.get("requestedQuantity")),
    requested_qty: Number(formData.get("requestedQuantity")),
    maximumAcceptableLeadTimeDays: Number(formData.get("leadTime")),
    max_lead_time_days: Number(formData.get("leadTime")),
    priorityLevel: formData.get("priorityLevel"),
    priority: formData.get("priorityLevel"),
    special_instructions: formData.get("specialInstructions").trim() || "None provided",
    specialInstructions: formData.get("specialInstructions").trim() || "None provided",
  };
}

function validateForm(formData) {
  let ok = true;
  fieldConfig.forEach(f => {
    const v = formData.get(f.id) || "";
    if (!f.validate(v)) { ok = false; setFieldError(f.id, f.message); }
  });
  return ok;
}

function setSubmitting(loading) {
  submitBtn.disabled = loading;
  submitBtnText.textContent = loading ? "Analyzing…" : "Analyze Fulfillment";
  submitSpinner.hidden = !loading;
}

function setStatus(msg, ok = null) {
  statusMessage.textContent = msg;
  if (ok === true) statusMessage.classList.add("status-message--success");
  if (ok === false) statusMessage.classList.remove("status-message--success");
}

form.addEventListener("submit", async event => {
  event.preventDefault();
  clearErrors();
  updateCustomerIdFromSession();

  const formData = new FormData(form);
  if (!validateForm(formData)) {
    setStatus("Please fix the highlighted fields and try again.", false);
    return;
  }

  const payload = buildOrderPayload(formData);
  renderSummaryTable({
    category: payload.category,
    partName: payload.partName,
    partId: payload.part_id,
    requestedQuantity: payload.requested_qty,
    maximumAcceptableLeadTimeDays: payload.max_lead_time_days,
    priorityLevel: payload.priorityLevel,
    specialInstructions: payload.specialInstructions,
  });

  // Reset result panels
  winnerCard.hidden = true;
  explanationBlock.hidden = true;
  candidatesSection.hidden = true;

  setSubmitting(true);
  setStatus("⏳ Calling backend AI optimization pipeline…");

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

    if (data.status === "success") {
      renderWinnerCard(data.selected_option || {});
      renderCandidates(data.all_candidates || []);
      renderExplanation(data.explanation || "");
      setStatus(
        `✅ AI pipeline complete — ${data.total_candidates} candidates evaluated, ${data.feasible_count ?? 0} meet lead-time constraint.`,
        true
      );
    } else {
      throw new Error(data.detail || "Unknown error");
    }
  } catch (err) {
    setStatus(`❌ Backend error: ${err.message}. Ensure the backend is running: uvicorn main:app --reload`, false);
  } finally {
    setSubmitting(false);
  }
});

// ── Event listeners ───────────────────────────────────────────
welcomeContinue.addEventListener("click", () => openRoleSelectionModal());
roleSelectionButtons.forEach(b => b.addEventListener("click", () => openAuthModal(b.dataset.roleSelect)));
closeAuthModalButton.addEventListener("click", closeAuthModal);
authModal.addEventListener("click", e => { if (e.target === authModal) closeAuthModal(); });
toggleAuthModeButton.addEventListener("click", () => setAuthMode(authState.mode === "login" ? "signup" : "login"));
authForm.addEventListener("submit", e => {
  e.preventDefault();
  authError.textContent = "";
  authState.mode === "login" ? handleLogin() : handleSignup();
});

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

// ── Init ──────────────────────────────────────────────────────
updateCustomerIdFromSession();
renderPartOptions("");

if (getCurrentUser()) {
  showDashboard();
} else {
  showWelcomeScreen();
}
