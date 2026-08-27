const STORAGE_KEYS = {
  users: "ax_users",
  currentUser: "ax_current_user"
};

const SELLER_API_BASE_URL = "http://localhost:8001";
const sellerState = { supplierId: "supplier_a", catalog: null, orders: [] };

const partCatalog = {
  Hydraulics: [
    { name: "Hydraulic Pump", id: "HYD-PMP-001" },
    { name: "Control Valve", id: "HYD-VLV-014" },
    { name: "Actuator Cylinder", id: "HYD-ACT-022" }
  ],
  Electronics: [
    { name: "Sensor Module", id: "ELE-SNS-104" },
    { name: "Control Board", id: "ELE-CTL-118" },
    { name: "Power Relay", id: "ELE-RLY-133" }
  ],
  Fasteners: [
    { name: "Hex Bolt Set", id: "FST-BLT-212" },
    { name: "Lock Nut Pack", id: "FST-NUT-225" },
    { name: "Washer Kit", id: "FST-WSR-231" }
  ],
  Filtration: [
    { name: "Air Filter Cartridge", id: "FIL-AIR-309" },
    { name: "Oil Filter Unit", id: "FIL-OIL-317" },
    { name: "Dust Separator", id: "FIL-DST-324" }
  ]
};

const demoUsers = [
  {
    role: "Buyer",
    name: "Ava Buyer",
    email: "buyer@demo.com",
    password: "buyer123",
    company: "Northline Procurement",
    customerId: "CUST-BUY-1001",
    phone: "+1 555 0101",
    location: "Chicago, USA",
    preferredCategory: "Hydraulics"
  },
  {
    role: "Seller",
    name: "Noah Seller",
    email: "seller@demo.com",
    password: "seller123",
    company: "Prime Parts Supply",
    customerId: "CUST-SEL-2001",
    phone: "+1 555 0202",
    location: "Austin, USA",
    preferredCategory: "Electronics"
  }
];

function seedUsers() {
  if (!localStorage.getItem(STORAGE_KEYS.users)) {
    localStorage.setItem(STORAGE_KEYS.users, JSON.stringify(demoUsers));
  }
}

function getUsers() {
  return JSON.parse(localStorage.getItem(STORAGE_KEYS.users) || "[]");
}

function saveUsers(users) {
  localStorage.setItem(STORAGE_KEYS.users, JSON.stringify(users));
}

function getCurrentUser() {
  return JSON.parse(localStorage.getItem(STORAGE_KEYS.currentUser) || "null");
}

function saveCurrentUser(user) {
  localStorage.setItem(STORAGE_KEYS.currentUser, JSON.stringify(user));
}

seedUsers();

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
const buyerDashboardContent = document.getElementById("buyerDashboardContent");
const sellerCommandCenter = document.getElementById("sellerCommandCenter");
const connectionStatus = document.getElementById("connectionStatus");
const connectionStatusText = document.getElementById("connectionStatusText");
const connectionWarning = document.getElementById("connectionWarning");
const sellerApiMessage = document.getElementById("sellerApiMessage");
const sellerInventoryBody = document.getElementById("sellerInventoryBody");
const sellerCatalogMeta = document.getElementById("sellerCatalogMeta");
const sellerOrdersBody = document.getElementById("sellerOrdersBody");
const sellerDetailsPanel = document.getElementById("sellerDetailsPanel");
const sellerDetailsTitle = document.getElementById("sellerDetailsTitle");
const sellerDetailsContent = document.getElementById("sellerDetailsContent");
const sellerRiskPanel = document.getElementById("sellerRiskPanel");
const sellerRiskContent = document.getElementById("sellerRiskContent");
const accountTypeLabel = document.getElementById("accountTypeLabel");
const accountSubtitle = document.getElementById("accountSubtitle");
const sellerViewEyebrow = document.getElementById("sellerViewEyebrow");
const agentExecution = document.getElementById("agentExecution");
const agentStateLabel = document.getElementById("agentStateLabel");
const supplierFindings = document.getElementById("supplierFindings");
const supplierFindingsContent = document.getElementById("supplierFindingsContent");
const strategyResults = document.getElementById("strategyResults");
const agentRecommendation = document.getElementById("agentRecommendation");
const recommendationContent = document.getElementById("recommendationContent");
const approvalGate = document.getElementById("approvalGate");
const agentRejection = document.getElementById("agentRejection");

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

let authState = {
  role: "Buyer",
  mode: "login"
};

let executionState = "IDLE";

const fieldConfig = [
  {
    id: "category",
    validate: (value) => value.trim() !== "",
    message: "Please select a category."
  },
  {
    id: "partName",
    validate: (value) => value.trim() !== "",
    message: "Please select a part name."
  },
  {
    id: "partId",
    validate: (value) => value.trim() !== "",
    message: "A matching part ID is required."
  },
  {
    id: "requestedQuantity",
    validate: (value) => Number.isInteger(Number(value)) && Number(value) > 0,
    message: "Requested quantity must be a positive whole number."
  },
  {
    id: "maximumBudgetRange",
    validate: (value) => value.trim() !== "",
    message: "Please select a maximum budget range."
  },
  {
    id: "leadTime",
    validate: (value) => Number.isInteger(Number(value)) && Number(value) > 0,
    message: "Lead time must be a positive whole number of days."
  },
  {
    id: "priorityLevel",
    validate: (value) => ["Low", "Medium", "Critical"].includes(value),
    message: "Please select a priority level."
  }
];

function setFieldError(fieldId, message) {
  const input = document.getElementById(fieldId);
  const errorElement = document.getElementById(`${fieldId}Error`);

  if (input) {
    input.classList.toggle("input-error", Boolean(message));
  }

  if (errorElement) {
    errorElement.textContent = message;
  }
}

function clearErrors() {
  fieldConfig.forEach((field) => setFieldError(field.id, ""));
}

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

  parts.forEach((part) => {
    const option = document.createElement("option");
    option.value = part.name;
    option.textContent = part.name;
    option.dataset.partId = part.id;
    partNameSelect.appendChild(option);
  });
}

function syncPartId() {
  const selectedOption = partNameSelect.options[partNameSelect.selectedIndex];
  partIdInput.value = selectedOption?.dataset?.partId || "";
}

function updateCustomerIdFromSession() {
  const currentUser = getCurrentUser();
  customerIdInput.value = currentUser?.customerId || "CUST-GUEST-0001";
}

function updateDashboardForRole() {
  const currentUser = getCurrentUser();
  const isSeller = currentUser?.role === "Seller";

  accountTypeLabel.textContent = isSeller ? "Seller Account" : "Buyer Account";
  document.getElementById("order-ingestion-title").textContent = isSeller
    ? "Seller Command Center"
    : "Autonomous Fulfillment Console";
  accountSubtitle.textContent = isSeller
    ? "Monitor inventory, incoming orders, fulfillment decisions, and supply-chain impact."
    : "Submit a spare-parts request and let the autonomous agent evaluate inventory, suppliers, logistics, cost, and lead-time constraints.";
  sellerViewEyebrow.textContent = isSeller ? "Seller Operations" : "Buyer Workspace";

  orderForm.hidden = isSeller;
  sellerWorkspace.hidden = !isSeller;
  requestPanel.classList.toggle("panel--seller", isSeller);
  formTitle.textContent = isSeller ? "Seller Workspace" : "New Spare Parts Request";
  formDescription.textContent = isSeller
    ? "Your account is ready for seller-side fulfillment activity."
    : "Tell the agent what you need. It will evaluate available fulfillment options against your quantity, budget, urgency, and lead-time requirements.";
  buyerDashboardContent.hidden = isSeller;
  sellerCommandCenter.hidden = !isSeller;
  if (isSeller) refreshSellerData();
}

async function sellerRequest(path, options = {}) {
  const response = await fetch(`${SELLER_API_BASE_URL}${path}`, {
    headers: { Accept: "application/json" },
    ...options
  });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try { message = (await response.json()).detail || message; } catch (error) {}
    throw new Error(message);
  }
  return response.json();
}

function formatSellerCurrency(value) {
  return Number.isFinite(Number(value)) ? `$${Number(value).toFixed(2)}` : "--";
}

function sellerValue(value) {
  return value === null || value === undefined || value === "" ? "--" : value;
}

function showSellerMessage(message, type = "error") {
  sellerApiMessage.textContent = message;
  sellerApiMessage.dataset.type = type;
}

function setConnectionStatus(isOnline) {
  connectionStatus.dataset.status = isOnline ? "online" : "offline";
  connectionStatusText.textContent = isOnline ? "SYSTEM ONLINE" : "SYSTEM OFFLINE";
  connectionWarning.hidden = isOnline;
}

function renderSellerCatalog(catalog) {
  const items = catalog.items || [];
  sellerCatalogMeta.textContent = `${catalog.supplier_name} / ${items.length} SKUs`;
  document.getElementById("sellerCatalogCount").textContent = items.length;
  document.getElementById("sellerStockCount").textContent = items.reduce((total, item) => total + Number(item.available_qty || 0), 0).toLocaleString();
  sellerInventoryBody.innerHTML = items.length ? items.map(item => {
    const stock = Number(item.available_qty || 0);
    const stockState = stock === 0 ? "out" : stock < 50 ? "low" : "healthy";
    const stockLabel = stockState === "out" ? "Out of stock" : stockState === "low" ? "Low stock" : "Healthy stock";
    return `<tr><td class="seller-mono">${item.sku}</td><td>${item.description}</td><td>${formatSellerCurrency(item.unit_price)}</td><td class="seller-stock"><span class="stock-indicator stock-indicator--${stockState}"></span>${item.available_qty}<small>${stockLabel}</small></td></tr>`;
  }).join("") : '<tr><td colspan="4">No catalog items returned.</td></tr>';
}

function renderSellerOrders(orders) {
  sellerState.orders = orders;
  document.getElementById("sellerOrderCount").textContent = orders.length;
  document.getElementById("sellerMarginTotal").textContent = formatSellerCurrency(orders.reduce((total, order) => total + Number(order.net_margin || 0), 0));
  sellerOrdersBody.innerHTML = orders.length ? orders.map(order => `<tr><td class="seller-mono">${order.incoming_order_id}</td><td>${order.buyer_id}</td><td><span class="seller-mono">${order.part_id}</span><br>${order.requested_qty} requested</td><td>${order.allocated_stock}</td><td><span class="seller-priority seller-priority--${String(order.priority).toLowerCase()}">${order.priority}</span></td><td>${order.fulfillment_type}</td><td>${order.automated_approval_status}</td><td class="seller-actions"><button type="button" class="button-secondary" data-seller-action="details" data-order-id="${order.incoming_order_id}">View Details</button><button type="button" class="seller-cancel" data-seller-action="cancel" data-order-id="${order.incoming_order_id}">Cancel / Restock Order</button></td></tr>`).join("") : '<tr><td colspan="8">No active orders for this supplier.</td></tr>';
}

function renderSellerDetails(order) {
  sellerDetailsTitle.textContent = order.incoming_order_id;
  const groups = [["Demand", [["Buyer ID", order.buyer_id], ["Part ID", order.part_id], ["Requested Quantity", order.requested_qty], ["Priority", order.priority]]], ["Inventory / Fulfillment", [["Current Stock", order.current_stock], ["Allocated Stock", order.allocated_stock], ["Remaining Stock", order.remaining_stock], ["Warehouse Location", order.warehouse_loc], ["Fulfillment Type", order.fulfillment_type]]], ["Financial", [["Gross Revenue", formatSellerCurrency(order.gross_revenue)], ["Fulfillment Cost", formatSellerCurrency(order.fulfillment_cost)], ["Expedited Freight Cost", formatSellerCurrency(order.expedited_freight_cost)], ["Net Margin", formatSellerCurrency(order.net_margin)]]], ["Operational", [["Recommended Action", order.recommended_action], ["Automated Approval Status", order.automated_approval_status], ["Created At", order.created_at]]]];
  sellerDetailsContent.innerHTML = groups.map(([title, fields]) => `<div class="seller-detail-group"><h4>${title}</h4>${fields.map(([label, value]) => `<div><span>${label}</span><strong>${sellerValue(value)}</strong></div>`).join("")}</div>`).join("");
  sellerDetailsPanel.hidden = false;
  renderSellerRisk(order);
  sellerDetailsPanel.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderSellerRisk(order) {
  const hasRisk = order.deprioritized_order_id || order.affected_customer || Number(order.sla_penalty || 0) > 0;
  sellerRiskPanel.hidden = !hasRisk;
  if (hasRisk) sellerRiskContent.innerHTML = [["Deprioritized Order ID", order.deprioritized_order_id], ["Affected Customer", order.affected_customer], ["SLA Penalty", formatSellerCurrency(order.sla_penalty)]].map(([label, value]) => `<div><span>${label}</span><strong>${sellerValue(value)}</strong></div>`).join("");
}

async function loadSellerHealth() {
  try {
    await sellerRequest("/health");
    setConnectionStatus(true);
    showSellerMessage("Live supplier data connected.", "success");
  } catch (error) {
    setConnectionStatus(false);
    showSellerMessage("Unable to retrieve live supplier data.");
    console.error("Seller backend health check failed:", error);
  }
}

async function loadSellerCatalog() {
  sellerInventoryBody.innerHTML = '<tr><td colspan="4">Loading catalog...</td></tr>';
  try { sellerState.catalog = await sellerRequest("/supplier_a/catalog"); renderSellerCatalog(sellerState.catalog); } catch (error) { sellerCatalogMeta.textContent = "Unavailable"; sellerInventoryBody.innerHTML = '<tr><td colspan="4">Unable to retrieve inventory.</td></tr>'; console.error("Seller catalog request failed:", error); }
}

async function loadSellerOrders() {
  sellerOrdersBody.innerHTML = '<tr><td colspan="8">Loading orders...</td></tr>';
  try {
    const orders = await sellerRequest("/seller/orders");
    const supplierOrders = orders.filter((order) => !order.recommended_action || order.recommended_action.toLowerCase().includes("[supplier_a]"));
    renderSellerOrders(supplierOrders);
  } catch (error) { sellerState.orders = []; sellerOrdersBody.innerHTML = '<tr><td colspan="8">Unable to retrieve incoming orders.</td></tr>'; document.getElementById("sellerOrderCount").textContent = "--"; document.getElementById("sellerMarginTotal").textContent = "--"; console.error("Seller orders request failed:", error); }
}

async function refreshSellerData() {
  sellerDetailsPanel.hidden = true;
  sellerRiskPanel.hidden = true;
  await Promise.all([loadSellerHealth(), loadSellerCatalog(), loadSellerOrders()]);
}

async function cancelSellerOrder(orderId, button) {
  const shouldCancel = window.confirm("Cancel this order?\n\nThis will cancel the fulfillment request and restore allocated inventory.");
  if (!shouldCancel) return;

  button.disabled = true;
  button.textContent = "Cancelling...";
  try { const result = await sellerRequest(`/seller/orders/${encodeURIComponent(orderId)}/cancel`, { method: "POST" }); showSellerMessage(`${result.message} Restored ${result.restored_stock} unit(s).`, "success"); await refreshSellerData(); } catch (error) { showSellerMessage(`Could not cancel ${orderId}: ${error.message}`); button.disabled = false; button.textContent = "Cancel / Restock Order"; }
}

function showDashboard() {
  welcomeScreen.hidden = true;
  dashboardPage.hidden = false;
  updateDashboardForRole();
}

function startWelcomeAnimation() {
  const welcomeMessage = "Welcome to Parts Investigation System";
  let messageIndex = 0;

  welcomeTitle.textContent = "Welcome!";

  const typeNextCharacter = () => {
    if (messageIndex < welcomeMessage.length) {
      welcomeTitle.textContent = welcomeMessage.slice(0, messageIndex + 1);
      messageIndex += 1;
      window.setTimeout(typeNextCharacter, messageIndex < 9 ? 95 : 62);
      return;
    }

    welcomeTitle.classList.add("welcome-screen__title--complete");
    welcomeContinue.hidden = false;
  };

  window.setTimeout(typeNextCharacter, 700);
}

function showWelcomeScreen() {
  dashboardPage.hidden = true;
  welcomeScreen.hidden = false;
  welcomeContinue.hidden = true;
  welcomeTitle.classList.remove("welcome-screen__title--complete");
  startWelcomeAnimation();
}

function buildOrderPayload(formData) {
  return {
    customerId: customerIdInput.value,
    category: formData.get("category").trim(),
    partName: formData.get("partName").trim(),
    partId: formData.get("partId").trim(),
    requestedQuantity: Number(formData.get("requestedQuantity")),
    maximumBudgetRange: formData.get("maximumBudgetRange"),
    maximumAcceptableLeadTimeDays: Number(formData.get("leadTime")),
    priorityLevel: formData.get("priorityLevel"),
    specialInstructions: formData.get("specialInstructions").trim() || "None provided"
  };
}

function validateForm(formData) {
  let isValid = true;

  fieldConfig.forEach((field) => {
    const value = formData.get(field.id) || "";
    const fieldIsValid = field.validate(value);

    if (!fieldIsValid) {
      isValid = false;
      setFieldError(field.id, field.message);
    }
  });

  return isValid;
}

function renderSummaryTable(payload) {
  const rows = [
    ["Category", payload.category],
    ["Part Name", payload.partName],
    ["Part ID", payload.partId],
    ["Requested Quantity", String(payload.requestedQuantity)],
    ["Maximum Budget Range", payload.maximumBudgetRange],
    ["Lead Time", `${payload.maximumAcceptableLeadTimeDays} day(s)`],
    ["Priority Level", payload.priorityLevel],
    ["Special Instructions", payload.specialInstructions]
  ];

  resultTableBody.innerHTML = rows
    .map(([label, value]) => `<tr><th scope="row">${label}</th><td>${value}</td></tr>`)
    .join("");
}

function resetAgentExecution() {
  executionState = "IDLE";
  agentExecution.hidden = true;
  supplierFindings.hidden = true;
  strategyResults.hidden = true;
  agentRecommendation.hidden = true;
  approvalGate.hidden = true;
  agentRejection.hidden = true;
  document.querySelectorAll("#agentPipeline li").forEach((step, index) => {
    step.dataset.status = index === 0 ? "completed" : "waiting";
    step.querySelector(".pipeline-symbol").textContent = index === 0 ? "✓" : "○";
  });
}

function renderExecutionConstraints(payload) {
  document.getElementById("executionQuantity").textContent = payload.requestedQuantity;
  document.getElementById("executionBudget").textContent = payload.maximumBudgetRange;
  document.getElementById("executionLeadTime").textContent = `${payload.maximumAcceptableLeadTimeDays} day(s)`;
  document.getElementById("executionPriority").textContent = payload.priorityLevel;
}

function updatePipelineStage(stageName, status, message = "") {
  const step = document.querySelector(`#agentPipeline li[data-stage="${stageName}"]`);
  if (!step) return;
  step.dataset.status = status;
  step.querySelector(".pipeline-symbol").textContent = status === "completed" ? "✓" : status === "running" ? "●" : status === "failed" ? "✕" : "○";
  if (message) step.querySelector("small").textContent = message;
}

function handleAgentEvent(event) {
  if (!event || !event.stage || !event.status) return;
  updatePipelineStage(event.stage, event.status, event.message || "");
  if (event.status === "running") executionState = "ANALYZING";
  if (event.status === "completed" && event.stage === "final_recommendation" && event.data) {
    executionState = "WAITING_FOR_APPROVAL";
    renderAgentRecommendation(event.data);
  }
  agentStateLabel.textContent = executionState.replaceAll("_", " ");
}

function renderAgentRecommendation(data) {
  recommendationContent.innerHTML = `<div class="recommendation-grid"><p>Recommended Strategy<strong>${data.strategy_name || "--"}</strong></p><p>Fulfillment Allocation<strong>${data.fulfillment_allocation || "--"}</strong></p><p>Total Cost<strong>${data.total_cost ?? "--"}</strong></p><p>Estimated Lead Time<strong>${data.estimated_lead_time ?? "--"} days</strong></p><p>TOPSIS Score<strong>${data.topsis_score ?? "--"}</strong></p></div><p>${data.explanation || "No explanation provided."}</p>`;
  agentRecommendation.hidden = false;
  approvalGate.hidden = false;
}

function startAgentExecution(payload) {
  resetAgentExecution();
  executionState = "ANALYZING";
  agentExecution.hidden = false;
  agentStateLabel.textContent = "ANALYZING";
  renderExecutionConstraints(payload);
}

async function approveStrategy(strategy) {
  console.warn("Approval API is not connected yet. No supplier order was placed.", strategy);
}

function setAuthMode(mode) {
  authState.mode = mode;
  const isSignup = mode === "signup";

  authModalTitle.textContent = isSignup ? `${authState.role} Sign Up` : `${authState.role} Login`;
  authModalText.textContent = isSignup
    ? "Create a local demo account. This is stored only in the browser."
    : "Use the demo credentials below or sign up for a local account.";
  authSubmitButton.textContent = isSignup ? "Create Account" : "Login";
  toggleAuthModeButton.textContent = isSignup ? "Already registered? Login" : "New here? Sign up";
  nameField.hidden = !isSignup;
  companyField.hidden = !isSignup;
  demoCredentials.hidden = isSignup;
  authError.textContent = "";
}

function showRoleSelection() {
  authState.role = "Buyer";
  authState.mode = "login";
  roleSelection.hidden = false;
  authPanel.hidden = true;
  authRoleBadge.textContent = "Account Access";
  authModalTitle.textContent = "Choose your role";
  authModalText.textContent = "Select how you want to continue to the local demo portal.";
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
  const roleCode = role === "Buyer" ? "BUY" : "SEL";
  return {
    role,
    name,
    email,
    password: authPasswordInput.value,
    company,
    customerId: `CUST-${roleCode}-${Date.now().toString().slice(-4)}`,
    phone: "",
    location: "",
    preferredCategory: ""
  };
}

function handleLogin() {
  const email = authEmailInput.value.trim().toLowerCase();
  const password = authPasswordInput.value;
  const users = getUsers();

  const matchedUser = users.find(
    (user) => user.email.toLowerCase() === email && user.password === password && user.role === authState.role
  );

  if (!matchedUser) {
    authError.textContent = "Invalid login details for the selected role.";
    return;
  }

  saveCurrentUser(matchedUser);
  updateCustomerIdFromSession();
  closeAuthModal();
  showDashboard();
  statusMessage.textContent = `${matchedUser.role} logged in as ${matchedUser.name}. Customer ID is kept hidden but ready for backend payloads.`;
  statusMessage.classList.add("status-message--success");
}

function handleSignup() {
  const name = authNameInput.value.trim();
  const email = authEmailInput.value.trim().toLowerCase();
  const company = authCompanyInput.value.trim();
  const password = authPasswordInput.value;
  const users = getUsers();

  if (!name || !email || !company || !password) {
    authError.textContent = "Please complete all sign-up fields.";
    return;
  }

  const existingUser = users.find((user) => user.email.toLowerCase() === email && user.role === authState.role);

  if (existingUser) {
    authError.textContent = "An account with this email already exists for that role.";
    return;
  }

  const newUser = buildProfileFromAuth(authState.role, email, name, company);
  users.push(newUser);
  saveUsers(users);
  saveCurrentUser(newUser);
  updateCustomerIdFromSession();
  closeAuthModal();
  showDashboard();
  statusMessage.textContent = `${newUser.role} account created for ${newUser.name}. You can edit the full profile on the profile page.`;
  statusMessage.classList.add("status-message--success");
}

welcomeContinue.addEventListener("click", () => {
  openRoleSelectionModal();
});

roleSelectionButtons.forEach((button) => {
  button.addEventListener("click", () => openAuthModal(button.dataset.roleSelect));
});

closeAuthModalButton.addEventListener("click", closeAuthModal);

authModal.addEventListener("click", (event) => {
  if (event.target === authModal) {
    closeAuthModal();
  }
});

toggleAuthModeButton.addEventListener("click", () => {
  setAuthMode(authState.mode === "login" ? "signup" : "login");
});

authForm.addEventListener("submit", (event) => {
  event.preventDefault();
  authError.textContent = "";

  if (authState.mode === "login") {
    handleLogin();
    return;
  }

  handleSignup();
});

categorySelect.addEventListener("change", () => {
  renderPartOptions(categorySelect.value);
  partNameSelect.value = "";
  partIdInput.value = "";
  setFieldError("category", "");
  setFieldError("partName", "");
  setFieldError("partId", "");
});

partNameSelect.addEventListener("change", () => {
  syncPartId();
  setFieldError("partName", "");
  setFieldError("partId", "");
});

document.getElementById("refreshSellerData").addEventListener("click", refreshSellerData);
document.getElementById("closeSellerDetails").addEventListener("click", () => {
  sellerDetailsPanel.hidden = true;
  sellerRiskPanel.hidden = true;
});

sellerOrdersBody.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-seller-action]");
  if (!button) return;

  const order = sellerState.orders.find((item) => item.incoming_order_id === button.dataset.orderId);
  if (button.dataset.sellerAction === "details" && order) {
    renderSellerDetails(order);
  }
  if (button.dataset.sellerAction === "cancel") {
    cancelSellerOrder(button.dataset.orderId, button);
  }
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  clearErrors();
  updateCustomerIdFromSession();

  const formData = new FormData(form);
  const isValid = validateForm(formData);

  if (!isValid) {
    statusMessage.textContent = "Please fix the highlighted fields and try again.";
    statusMessage.classList.remove("status-message--success");
    return;
  }

  const orderPayload = buildOrderPayload(formData);

  console.log("Order ingestion payload:", orderPayload);
  renderSummaryTable(orderPayload);
  startAgentExecution(orderPayload);

  statusMessage.textContent = "Order validated successfully. Visible table stays clean, while customer ID remains hidden inside the payload.";
  statusMessage.classList.add("status-message--success");
});

document.getElementById("returnToRequest").addEventListener("click", () => {
  resetAgentExecution();
  form.scrollIntoView({ behavior: "smooth", block: "start" });
});

document.getElementById("approveStrategy").addEventListener("click", () => {
  approveStrategy(null);
});

document.getElementById("rejectStrategy").addEventListener("click", () => {
  executionState = "REJECTED";
  agentRecommendation.hidden = true;
  approvalGate.hidden = true;
  agentRejection.hidden = false;
  agentStateLabel.textContent = "REJECTED";
});

updateCustomerIdFromSession();
renderPartOptions("");
resetAgentExecution();

if (getCurrentUser()) {
  showDashboard();
} else {
  showWelcomeScreen();
}

  loadSellerHealth();
